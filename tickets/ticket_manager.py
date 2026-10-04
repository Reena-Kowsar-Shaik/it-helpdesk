"""Core Ticket Management & Lifecycle Workflow Engine.

Member 2: Ticket Management, SLA & Support Operations.
Orchestrates ticket creation, editing, status lifecycle transitions, resolution records,
reopening operations, and commenting threads.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_

from core.database import db
from core.models import (
    Ticket, TicketHistory, Comment, TicketResolution,
    Employee, Department, Category, SupportAgent, SupportTeam, SLARule, User
)
from core.exceptions import (
    TicketNotFoundError, EntityNotFoundError, ValidationError, UnauthorizedAccessError
)
from core.logger import log_audit, log_error
from tickets.sla_manager import SLAManager
from tickets.ticket_history import TicketHistoryManager


# Valid lifecycle state transitions
ALLOWED_TRANSITIONS = {
    "OPEN": ["ASSIGNED", "IN PROGRESS", "CLOSED"],
    "ASSIGNED": ["IN PROGRESS", "OPEN", "RESOLVED", "CLOSED"],
    "IN PROGRESS": ["RESOLVED", "ASSIGNED", "CLOSED"],
    "RESOLVED": ["CLOSED", "REOPENED", "IN PROGRESS"],
    "CLOSED": ["REOPENED"],
    "REOPENED": ["IN PROGRESS", "ASSIGNED", "RESOLVED", "CLOSED"]
}


class TicketManager:
    """Primary operational manager for ticket lifecycle, modifications, and resolutions."""

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session
        self.sla_mgr = SLAManager(session)
        self.history_mgr = TicketHistoryManager(session)

    def get_session(self) -> Session:
        """Helper to get db session."""
        if self._external_session:
            return self._external_session
        return db.Session()

    def _generate_ticket_number(self, session: Session) -> str:
        """Generate unique ticket identifier: TCK-YYYY-XXXX."""
        year = datetime.utcnow().year
        count = session.query(func.count(Ticket.ticket_id)).scalar() or 0
        return f"TCK-{year}-{count + 1:04d}"

    def create_ticket(
        self,
        employee_id: int,
        department_id: int,
        category_id: int,
        title: str,
        description: str,
        priority: str = "Medium",
        user_id: Optional[int] = None
    ) -> Ticket:
        """Create a new ticket with automatic SLA deadline calculation and audit trail."""
        if not title or not title.strip():
            raise ValidationError("Ticket title cannot be empty.")
        if not description or not description.strip():
            raise ValidationError("Ticket description cannot be empty.")

        now = datetime.utcnow()
        resp_deadline, res_deadline, sla_id = self.sla_mgr.calculate_deadlines(priority, now)

        with db.get_session() as session:
            # Validate employee
            emp = session.query(Employee).filter(Employee.employee_id == employee_id).first()
            if not emp:
                raise EntityNotFoundError("Employee", employee_id)

            ticket_num = self._generate_ticket_number(session)

            ticket = Ticket(
                ticket_number=ticket_num,
                employee_id=employee_id,
                department_id=department_id,
                category_id=category_id,
                title=title.strip(),
                description=description.strip(),
                priority=priority,
                status="OPEN",
                sla_id=sla_id,
                response_deadline=resp_deadline,
                resolution_deadline=res_deadline,
                created_at=now,
                updated_at=now
            )
            session.add(ticket)
            session.flush()

            # Record initial history
            history = TicketHistory(
                ticket_id=ticket.ticket_id,
                old_status=None,
                new_status="OPEN",
                changed_by_user_id=user_id,
                comment=f"Ticket created with priority '{priority}' and SLA target {res_deadline.strftime('%Y-%m-%d %H:%M')}",
                changed_at=now
            )
            session.add(history)
            session.flush()
            session.refresh(ticket)

            log_audit(
                "TICKET_CREATED",
                f"User {user_id or emp.full_name}",
                f"Ticket #{ticket.ticket_number} created (Priority: {priority}, Dept ID: {department_id})"
            )
            return ticket

    def get_ticket_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """Fetch ticket by ID with full entity relationships."""
        session = self.get_session()
        try:
            return session.query(Ticket).options(
                joinedload(Ticket.employee).joinedload(Employee.department),
                joinedload(Ticket.department),
                joinedload(Ticket.category),
                joinedload(Ticket.assigned_agent).joinedload(SupportAgent.team),
                joinedload(Ticket.team),
                joinedload(Ticket.sla),
                joinedload(Ticket.comments).joinedload(Comment.user),
                joinedload(Ticket.history).joinedload(TicketHistory.user),
                joinedload(Ticket.resolution).joinedload(TicketResolution.agent)
            ).filter(Ticket.ticket_id == ticket_id).first()
        finally:
            if not self._external_session:
                session.close()

    def get_ticket_by_number(self, ticket_number: str) -> Optional[Ticket]:
        """Fetch ticket by formatted ticket number."""
        session = self.get_session()
        try:
            return session.query(Ticket).options(
                joinedload(Ticket.employee),
                joinedload(Ticket.department),
                joinedload(Ticket.category),
                joinedload(Ticket.assigned_agent),
                joinedload(Ticket.sla),
                joinedload(Ticket.resolution)
            ).filter(Ticket.ticket_number == ticket_number).first()
        finally:
            if not self._external_session:
                session.close()

    def update_ticket_details(
        self,
        ticket_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        category_id: Optional[int] = None,
        department_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Ticket:
        """Update ticket metadata and recalculate SLA if priority changed."""
        with db.get_session() as session:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if not ticket:
                raise TicketNotFoundError(ticket_id)

            changes = []
            if title and title.strip() != ticket.title:
                changes.append(f"Title updated")
                ticket.title = title.strip()

            if description and description.strip() != ticket.description:
                changes.append(f"Description updated")
                ticket.description = description.strip()

            if category_id and category_id != ticket.category_id:
                changes.append(f"Category changed to {category_id}")
                ticket.category_id = category_id

            if department_id and department_id != ticket.department_id:
                changes.append(f"Department changed to {department_id}")
                ticket.department_id = department_id

            if priority and priority != ticket.priority:
                old_prio = ticket.priority
                ticket.priority = priority
                changes.append(f"Priority changed from {old_prio} to {priority}")
                
                # Recalculate SLA
                resp_deadline, res_deadline, sla_id = self.sla_mgr.calculate_deadlines(priority, ticket.created_at)
                ticket.response_deadline = resp_deadline
                ticket.resolution_deadline = res_deadline
                ticket.sla_id = sla_id

            now = datetime.utcnow()
            ticket.updated_at = now

            if changes:
                history = TicketHistory(
                    ticket_id=ticket.ticket_id,
                    old_status=ticket.status,
                    new_status=ticket.status,
                    changed_by_user_id=user_id,
                    comment="; ".join(changes),
                    changed_at=now
                )
                session.add(history)

            session.flush()
            session.refresh(ticket)
            log_audit("TICKET_UPDATED", f"User {user_id}", f"Ticket #{ticket.ticket_number} updated: {', '.join(changes)}")
            return ticket

    def transition_status(
        self,
        ticket_id: int,
        new_status: str,
        user_id: Optional[int] = None,
        comment: Optional[str] = None
    ) -> Ticket:
        """Transition ticket through its lifecycle state machine."""
        with db.get_session() as session:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if not ticket:
                raise TicketNotFoundError(ticket_id)

            old_status = ticket.status
            if old_status == new_status:
                return ticket

            # Validate lifecycle transition
            valid_next_states = ALLOWED_TRANSITIONS.get(old_status, [])
            if new_status not in valid_next_states and new_status != "CLOSED":
                raise ValidationError(f"Invalid status transition from '{old_status}' to '{new_status}'. Allowed: {valid_next_states}")

            now = datetime.utcnow()
            ticket.status = new_status
            ticket.updated_at = now

            # Manage lifecycle timestamps
            if new_status in ("IN PROGRESS", "ASSIGNED") and not ticket.first_responded_at:
                ticket.first_responded_at = now
            elif new_status == "RESOLVED":
                ticket.resolved_at = now
            elif new_status == "CLOSED":
                ticket.closed_at = now
            elif new_status == "REOPENED":
                ticket.reopened_count += 1
                ticket.resolved_at = None
                ticket.closed_at = None

            history = TicketHistory(
                ticket_id=ticket.ticket_id,
                old_status=old_status,
                new_status=new_status,
                changed_by_user_id=user_id,
                comment=comment or f"Status transitioned from {old_status} to {new_status}",
                changed_at=now
            )
            session.add(history)
            session.flush()
            session.refresh(ticket)

            log_audit(
                "STATUS_TRANSITION",
                f"User {user_id}",
                f"Ticket #{ticket.ticket_number}: {old_status} -> {new_status}"
            )
            return ticket

    def reopen_ticket(
        self,
        ticket_id: int,
        user_id: int,
        reason: str
    ) -> Ticket:
        """Reopen a resolved or closed ticket when an issue persists."""
        if not reason or not reason.strip():
            raise ValidationError("A clear reason is required to reopen a ticket.")

        return self.transition_status(
            ticket_id=ticket_id,
            new_status="REOPENED",
            user_id=user_id,
            comment=f"Ticket Reopened: {reason.strip()}"
        )

    def resolve_ticket(
        self,
        ticket_id: int,
        agent_id: int,
        root_cause: str,
        resolution_steps: str,
        resolution_category: str = "Technical Fix",
        user_id: Optional[int] = None
    ) -> TicketResolution:
        """Record formal resolution details and transition ticket to RESOLVED."""
        if not root_cause or not root_cause.strip():
            raise ValidationError("Root cause diagnosis is required to resolve a ticket.")
        if not resolution_steps or not resolution_steps.strip():
            raise ValidationError("Resolution steps are required to resolve a ticket.")

        with db.get_session() as session:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if not ticket:
                raise TicketNotFoundError(ticket_id)

            now = datetime.utcnow()

            resolution = TicketResolution(
                ticket_id=ticket_id,
                agent_id=agent_id,
                root_cause=root_cause.strip(),
                resolution_steps=resolution_steps.strip(),
                resolution_category=resolution_category,
                resolved_at=now
            )
            session.merge(resolution)

            old_status = ticket.status
            ticket.status = "RESOLVED"
            ticket.resolved_at = now
            ticket.updated_at = now

            history = TicketHistory(
                ticket_id=ticket.ticket_id,
                old_status=old_status,
                new_status="RESOLVED",
                changed_by_user_id=user_id,
                comment=f"Resolved by agent: {root_cause[:60]}...",
                changed_at=now
            )
            session.add(history)
            session.flush()

            log_audit("TICKET_RESOLVED", f"User {user_id}", f"Ticket #{ticket.ticket_number} resolved (Category: {resolution_category})")
            return resolution

    def close_ticket(
        self,
        ticket_id: int,
        user_id: Optional[int] = None,
        comment: Optional[str] = None
    ) -> Ticket:
        """Permanently close a resolved ticket."""
        return self.transition_status(
            ticket_id=ticket_id,
            new_status="CLOSED",
            user_id=user_id,
            comment=comment or "Ticket officially closed and verified by user/staff."
        )

    def add_comment(
        self,
        ticket_id: int,
        user_id: int,
        comment_text: str,
        is_internal: bool = False
    ) -> Comment:
        """Post a public reply or internal staff note to a ticket."""
        if not comment_text or not comment_text.strip():
            raise ValidationError("Comment text cannot be empty.")

        with db.get_session() as session:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if not ticket:
                raise TicketNotFoundError(ticket_id)

            now = datetime.utcnow()
            comment = Comment(
                ticket_id=ticket_id,
                user_id=user_id,
                comment_text=comment_text.strip(),
                is_internal=is_internal,
                created_at=now
            )
            session.add(comment)

            # Touch ticket updated_at
            ticket.updated_at = now

            session.flush()
            session.refresh(comment)

            log_audit(
                "COMMENT_POSTED",
                f"User {user_id}",
                f"Comment on Ticket #{ticket.ticket_number} (Internal: {is_internal})"
            )
            return comment
