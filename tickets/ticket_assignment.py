"""Ticket Assignment & Workload Distribution Engine.

Member 2: Ticket Management, SLA & Support Operations.
Handles manual assignment, team routing, workload-aware round-robin/least-loaded auto assignment,
and agent workload tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_

from core.database import db
from core.models import Ticket, SupportAgent, SupportTeam, Category, TicketHistory, User
from core.exceptions import TicketNotFoundError, EntityNotFoundError, ValidationError
from core.logger import log_audit, log_error
from tickets.ticket_history import TicketHistoryManager


# Default Category to Team mappings for intelligent auto-routing
CATEGORY_TEAM_ROUTING = {
    "Hardware & Devices": "Hardware Support",
    "Hardware": "Hardware Support",
    "Network & Connectivity": "Network Operations",
    "Network": "Network Operations",
    "Software & Applications": "Application Support",
    "Software": "Application Support",
    "Account & Access": "Identity & Access",
    "Security": "Identity & Access",
    "Email & Communication": "Application Support",
    "Database & Storage": "Database Support"
}


class TicketAssignmentManager:
    """Manages ticket routing, agent workload calculation, and smart automated assignment."""

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session
        self.history_mgr = TicketHistoryManager(session)

    def get_session(self) -> Session:
        """Helper to get db session."""
        if self._external_session:
            return self._external_session
        return db.Session()

    def get_agent_workloads(self, team_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Calculate active ticket workload and capacity for support agents.
        
        Active statuses: ASSIGNED, IN PROGRESS, REOPENED.
        """
        session = self.get_session()
        try:
            q = session.query(SupportAgent).options(
                joinedload(SupportAgent.team),
                joinedload(SupportAgent.user)
            )
            if team_id:
                q = q.filter(SupportAgent.team_id == team_id)

            agents = q.all()
            workload_list = []

            for agent in agents:
                active_count = session.query(func.count(Ticket.ticket_id)).filter(
                    Ticket.assigned_agent_id == agent.agent_id,
                    Ticket.status.in_(["ASSIGNED", "IN PROGRESS", "REOPENED"])
                ).scalar() or 0

                resolved_count = session.query(func.count(Ticket.ticket_id)).filter(
                    Ticket.assigned_agent_id == agent.agent_id,
                    Ticket.status.in_(["RESOLVED", "CLOSED"])
                ).scalar() or 0

                # Workload status evaluation
                if not agent.is_available:
                    status_label = "Unavailable"
                elif active_count >= 10:
                    status_label = "Overloaded"
                elif active_count >= 5:
                    status_label = "Moderate"
                else:
                    status_label = "Light"

                workload_list.append({
                    "agent_id": agent.agent_id,
                    "user_id": agent.user_id,
                    "full_name": agent.full_name,
                    "team_id": agent.team_id,
                    "team_name": agent.team.name if agent.team else "Unassigned",
                    "specialization": agent.specialization,
                    "is_available": agent.is_available,
                    "active_tickets": active_count,
                    "resolved_tickets": resolved_count,
                    "workload_status": status_label
                })

            # Sort by active tickets ascending
            workload_list.sort(key=lambda x: (not x["is_available"], x["active_tickets"]))
            return workload_list
        finally:
            if not self._external_session:
                session.close()

    def assign_ticket_manual(
        self,
        ticket_id: int,
        agent_id: Optional[int],
        team_id: Optional[int] = None,
        assigned_by_user_id: Optional[int] = None,
        comment: Optional[str] = None
    ) -> Ticket:
        """Assign ticket to a specific agent and/or support team."""
        with db.get_session() as session:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if not ticket:
                raise TicketNotFoundError(ticket_id)

            old_agent_id = ticket.assigned_agent_id
            old_status = ticket.status

            if agent_id:
                agent = session.query(SupportAgent).filter(SupportAgent.agent_id == agent_id).first()
                if not agent:
                    raise EntityNotFoundError("Support Agent", agent_id)
                ticket.assigned_agent_id = agent.agent_id
                ticket.assigned_team_id = agent.team_id if not team_id else team_id
                agent_name = agent.full_name
            else:
                ticket.assigned_agent_id = None
                if team_id:
                    ticket.assigned_team_id = team_id
                agent_name = "Unassigned"

            # Transition status from OPEN to ASSIGNED if currently OPEN
            if ticket.status == "OPEN":
                ticket.status = "ASSIGNED"

            now = datetime.utcnow()
            ticket.updated_at = now

            log_msg = comment or f"Ticket assigned to {agent_name}"
            history_record = TicketHistory(
                ticket_id=ticket.ticket_id,
                old_status=old_status,
                new_status=ticket.status,
                changed_by_user_id=assigned_by_user_id,
                comment=log_msg,
                changed_at=now
            )
            session.add(history_record)
            session.flush()
            session.refresh(ticket)

            log_audit(
                "TICKET_ASSIGNMENT",
                f"User {assigned_by_user_id or 'System'}",
                f"Ticket #{ticket.ticket_number} assigned to {agent_name} (Team: {ticket.assigned_team_id})"
            )
            return ticket

    def auto_assign_ticket(
        self,
        ticket_id: int,
        assigned_by_user_id: Optional[int] = None
    ) -> Tuple[Ticket, SupportAgent]:
        """Intelligently auto-route and assign a ticket to the least-loaded available agent.
        
        Routing algorithm:
        1. Match Category to appropriate Support Team.
        2. Filter active & available agents in that team.
        3. Pick agent with fewest active tickets.
        4. Fallback to any available agent across all teams if team is fully occupied or empty.
        """
        with db.get_session() as session:
            ticket = session.query(Ticket).options(
                joinedload(Ticket.category),
                joinedload(Ticket.department)
            ).filter(Ticket.ticket_id == ticket_id).first()

            if not ticket:
                raise TicketNotFoundError(ticket_id)

            category_name = ticket.category.name if ticket.category else ""
            target_team_name = None

            # 1. Match category to team
            for cat_key, team_val in CATEGORY_TEAM_ROUTING.items():
                if cat_key.lower() in category_name.lower():
                    target_team_name = team_val
                    break

            # Find matching team
            target_team = None
            if target_team_name:
                target_team = session.query(SupportTeam).filter(
                    SupportTeam.name.ilike(f"%{target_team_name}%")
                ).first()

            # 2. Get available agents
            agent_query = session.query(SupportAgent).filter(SupportAgent.is_available == True)
            if target_team:
                team_agents = agent_query.filter(SupportAgent.team_id == target_team.team_id).all()
                candidates = team_agents if team_agents else agent_query.all()
            else:
                candidates = agent_query.all()

            if not candidates:
                # No agents available; keep unassigned
                ticket.status = "OPEN"
                session.flush()
                raise ValidationError("No available support agents found for automatic assignment.")

            # 3. Calculate workload for each candidate to find least loaded
            best_agent = None
            min_workload = float("inf")

            for agent in candidates:
                active_count = session.query(func.count(Ticket.ticket_id)).filter(
                    Ticket.assigned_agent_id == agent.agent_id,
                    Ticket.status.in_(["ASSIGNED", "IN PROGRESS", "REOPENED"])
                ).scalar() or 0

                if active_count < min_workload:
                    min_workload = active_count
                    best_agent = agent

            # 4. Assign
            old_status = ticket.status
            ticket.assigned_agent_id = best_agent.agent_id
            ticket.assigned_team_id = best_agent.team_id
            if ticket.status == "OPEN":
                ticket.status = "ASSIGNED"

            now = datetime.utcnow()
            ticket.updated_at = now

            history = TicketHistory(
                ticket_id=ticket.ticket_id,
                old_status=old_status,
                new_status=ticket.status,
                changed_by_user_id=assigned_by_user_id,
                comment=f"Smart Auto-Assigned to {best_agent.full_name} (Workload: {min_workload} active tickets)",
                changed_at=now
            )
            session.add(history)
            session.flush()
            session.refresh(ticket)

            log_audit(
                "SMART_AUTO_ASSIGNMENT",
                f"User {assigned_by_user_id or 'System'}",
                f"Ticket #{ticket.ticket_number} auto-assigned to {best_agent.full_name}"
            )
            return ticket, best_agent

    def claim_ticket(
        self,
        ticket_id: int,
        agent_id: int,
        user_id: int
    ) -> Ticket:
        """Allow a support agent to self-claim a ticket from the pool and start progress."""
        with db.get_session() as session:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if not ticket:
                raise TicketNotFoundError(ticket_id)

            agent = session.query(SupportAgent).filter(SupportAgent.agent_id == agent_id).first()
            if not agent:
                raise EntityNotFoundError("Support Agent", agent_id)

            old_status = ticket.status
            ticket.assigned_agent_id = agent.agent_id
            ticket.assigned_team_id = agent.team_id
            ticket.status = "IN PROGRESS"

            now = datetime.utcnow()
            if not ticket.first_responded_at:
                ticket.first_responded_at = now
            ticket.updated_at = now

            history = TicketHistory(
                ticket_id=ticket.ticket_id,
                old_status=old_status,
                new_status="IN PROGRESS",
                changed_by_user_id=user_id,
                comment=f"Self-claimed by agent {agent.full_name} and moved to IN PROGRESS",
                changed_at=now
            )
            session.add(history)
            session.flush()
            session.refresh(ticket)

            log_audit("TICKET_CLAIMED", f"User {user_id}", f"Ticket #{ticket.ticket_number} claimed by {agent.full_name}")
            return ticket
