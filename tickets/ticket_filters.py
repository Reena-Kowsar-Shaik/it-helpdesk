"""Advanced Search & Multi-Dimensional Ticket Filtering Engine.

Member 2: Ticket Management, SLA & Support Operations.
Provides flexible filtering across employee, department, category, priority, status,
assigned agent/team, date ranges, SLA breach flags, and keyword search.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import pandas as pd
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc, asc

from core.database import db
from core.models import Ticket, Employee, Department, Category, SupportAgent, SupportTeam, SLARule, Comment
from tickets.sla_manager import SLAManager


@dataclass
class TicketFilterCriteria:
    """Encapsulates all multi-criteria query parameters for searching tickets."""
    employee_id: Optional[int] = None
    department_id: Optional[int] = None
    category_id: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    agent_id: Optional[int] = None
    team_id: Optional[int] = None
    unassigned_only: bool = False
    search_query: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sla_breached_only: bool = False
    approaching_sla_only: bool = False
    sort_by: str = "created_at"
    sort_desc: bool = True
    limit: Optional[int] = None


class TicketFilterService:
    """Service to execute fast, indexed database queries with multi-faceted filtering."""

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session
        self.sla_mgr = SLAManager(session)

    def get_session(self) -> Session:
        """Helper to get db session."""
        if self._external_session:
            return self._external_session
        return db.Session()

    def filter_tickets(self, criteria: TicketFilterCriteria) -> List[Ticket]:
        """Apply all specified criteria filters and return joined ticket models."""
        session = self.get_session()
        try:
            q = session.query(Ticket).options(
                joinedload(Ticket.employee).joinedload(Employee.department),
                joinedload(Ticket.department),
                joinedload(Ticket.category),
                joinedload(Ticket.assigned_agent).joinedload(SupportAgent.team),
                joinedload(Ticket.team),
                joinedload(Ticket.sla),
                joinedload(Ticket.resolution)
            )

            # Department filter
            if criteria.department_id:
                q = q.filter(Ticket.department_id == criteria.department_id)

            # Employee filter
            if criteria.employee_id:
                q = q.filter(Ticket.employee_id == criteria.employee_id)

            # Category filter
            if criteria.category_id:
                q = q.filter(Ticket.category_id == criteria.category_id)

            # Priority filter
            if criteria.priority and criteria.priority not in ("All", ""):
                q = q.filter(Ticket.priority == criteria.priority)

            # Status filter
            if criteria.status and criteria.status not in ("All", ""):
                q = q.filter(Ticket.status == criteria.status)

            # Agent / Team filter
            if criteria.unassigned_only:
                q = q.filter(Ticket.assigned_agent_id.is_(None))
            else:
                if criteria.agent_id:
                    q = q.filter(Ticket.assigned_agent_id == criteria.agent_id)
                if criteria.team_id:
                    q = q.filter(Ticket.assigned_team_id == criteria.team_id)

            # Date range filter
            if criteria.start_date:
                q = q.filter(Ticket.created_at >= criteria.start_date)
            if criteria.end_date:
                q = q.filter(Ticket.created_at <= criteria.end_date)

            # Keyword Search across Ticket Number, Title, and Description
            if criteria.search_query and criteria.search_query.strip():
                kw = f"%{criteria.search_query.strip()}%"
                q = q.filter(
                    or_(
                        Ticket.ticket_number.ilike(kw),
                        Ticket.title.ilike(kw),
                        Ticket.description.ilike(kw)
                    )
                )

            # Sorting
            sort_column = getattr(Ticket, criteria.sort_by, Ticket.created_at)
            if criteria.sort_desc:
                q = q.order_by(desc(sort_column))
            else:
                q = q.order_by(asc(sort_column))

            if criteria.limit:
                q = q.limit(criteria.limit)

            results = q.all()

            # Post-filter for dynamic SLA flags if requested
            if criteria.sla_breached_only or criteria.approaching_sla_only:
                now = datetime.utcnow()
                filtered_sla_results = []
                for t in results:
                    sla_info = self.sla_mgr.check_ticket_sla_status(t, now)
                    if criteria.sla_breached_only and sla_info["is_breached"]:
                        filtered_sla_results.append(t)
                    elif criteria.approaching_sla_only and sla_info["resolution_status"] == "Warning" and t.status not in ("RESOLVED", "CLOSED"):
                        filtered_sla_results.append(t)
                return filtered_sla_results

            return results
        finally:
            if not self._external_session:
                session.close()

    def get_filter_dropdown_options(self) -> Dict[str, Any]:
        """Fetch all distinct filter options for UI controls."""
        session = self.get_session()
        try:
            departments = session.query(Department).order_by(Department.name).all()
            categories = session.query(Category).order_by(Category.name).all()
            agents = session.query(SupportAgent).order_by(SupportAgent.full_name).all()
            teams = session.query(SupportTeam).order_by(SupportTeam.name).all()

            return {
                "departments": {d.name: d.department_id for d in departments},
                "categories": {c.name: c.category_id for c in categories},
                "agents": {a.full_name: a.agent_id for a in agents},
                "teams": {t.name: t.team_id for t in teams},
                "priorities": ["All", "Critical", "High", "Medium", "Low"],
                "statuses": ["All", "OPEN", "ASSIGNED", "IN PROGRESS", "RESOLVED", "CLOSED", "REOPENED"]
            }
        finally:
            if not self._external_session:
                session.close()

    def tickets_to_dataframe(self, tickets: List[Ticket]) -> pd.DataFrame:
        """Convert a list of Ticket models into a clean Pandas DataFrame for table display or CSV export."""
        data = []
        now = datetime.utcnow()

        for t in tickets:
            sla_info = self.sla_mgr.check_ticket_sla_status(t, now)
            data.append({
                "Ticket ID": t.ticket_id,
                "Ticket Number": t.ticket_number,
                "Title": t.title,
                "Employee": t.employee.full_name if t.employee else "N/A",
                "Department": t.department.name if t.department else (t.employee.department.name if t.employee and t.employee.department else "N/A"),
                "Category": t.category.name if t.category else "N/A",
                "Priority": t.priority,
                "Status": t.status,
                "Assigned Agent": t.assigned_agent.full_name if t.assigned_agent else "Unassigned",
                "Assigned Team": t.team.name if t.team else "Unassigned",
                "Created At": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "N/A",
                "Resolution Target": t.resolution_deadline.strftime("%Y-%m-%d %H:%M") if t.resolution_deadline else "N/A",
                "SLA Status": "Breached" if sla_info["is_breached"] else ("Warning" if sla_info["resolution_status"] == "Warning" else "Compliant"),
                "SLA Time Remaining": sla_info["time_remaining_formatted"],
                "Reopened Count": t.reopened_count
            })

        return pd.DataFrame(data)
