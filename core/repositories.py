"""Data Access Layer & OOP Repositories for Database Operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_, and_

from core.database import db
from core.models import (
    User, Employee, SupportAgent, SupportTeam, Department, 
    Category, SLARule, Ticket, TicketHistory, Comment, TicketResolution, KnowledgeArticle
)
from core.exceptions import (
    TicketNotFoundError, EntityNotFoundError, UserAlreadyExistsError, ValidationError
)
from core.logger import log_audit, log_error

class BaseRepository:
    """Base repository with shared session utilities."""
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    def get_session(self):
        if self._external_session:
            return self._external_session
        return db.Session()


class UserRepository(BaseRepository):
    """User repository for authentication and account management."""

    def get_by_id(self, user_id: int) -> Optional[User]:
        session = self.get_session()
        try:
            return session.query(User).filter(User.user_id == user_id).first()
        finally:
            if not self._external_session:
                session.close()

    def get_by_username(self, username: str) -> Optional[User]:
        session = self.get_session()
        try:
            return session.query(User).filter(User.username == username).first()
        finally:
            if not self._external_session:
                session.close()

    def get_by_email(self, email: str) -> Optional[User]:
        session = self.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            if not self._external_session:
                session.close()

    def create(self, username: str, email: str, password_hash: str, role: str = 'Employee') -> User:
        with db.get_session() as session:
            # Check unique constraint
            if session.query(User).filter(or_(User.username == username, User.email == email)).first():
                raise UserAlreadyExistsError(username)

            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                is_active=True
            )
            session.add(user)
            session.flush()
            session.refresh(user)
            log_audit("USER_CREATED", username, f"Role: {role}, ID: {user.user_id}")
            return user

    def get_all(self) -> List[User]:
        session = self.get_session()
        try:
            return session.query(User).all()
        finally:
            if not self._external_session:
                session.close()


class DepartmentRepository(BaseRepository):
    """Department repository for listing and fetching departments."""

    def get_all(self) -> List[Department]:
        session = self.get_session()
        try:
            return session.query(Department).order_by(Department.name).all()
        finally:
            if not self._external_session:
                session.close()

    def get_by_id(self, dept_id: int) -> Optional[Department]:
        session = self.get_session()
        try:
            return session.query(Department).filter(Department.department_id == dept_id).first()
        finally:
            if not self._external_session:
                session.close()

    def create(self, name: str, code: str, description: str = "") -> Department:
        with db.get_session() as session:
            dept = Department(name=name, code=code, description=description)
            session.add(dept)
            session.flush()
            session.refresh(dept)
            log_audit("DEPARTMENT_CREATED", "system", f"Dept: {name} ({code})")
            return dept


class CategoryRepository(BaseRepository):
    """Category repository for helpdesk issue categories."""

    def get_all(self) -> List[Category]:
        session = self.get_session()
        try:
            return session.query(Category).order_by(Category.name).all()
        finally:
            if not self._external_session:
                session.close()

    def get_by_id(self, category_id: int) -> Optional[Category]:
        session = self.get_session()
        try:
            return session.query(Category).filter(Category.category_id == category_id).first()
        finally:
            if not self._external_session:
                session.close()


class SLARepository(BaseRepository):
    """SLA rules management repository."""

    def get_by_priority(self, priority: str) -> Optional[SLARule]:
        session = self.get_session()
        try:
            return session.query(SLARule).filter(SLARule.priority == priority, SLARule.is_active == True).first()
        finally:
            if not self._external_session:
                session.close()

    def get_all(self) -> List[SLARule]:
        session = self.get_session()
        try:
            return session.query(SLARule).all()
        finally:
            if not self._external_session:
                session.close()


class EmployeeRepository(BaseRepository):
    """Employee repository."""

    def get_by_user_id(self, user_id: int) -> Optional[Employee]:
        session = self.get_session()
        try:
            return session.query(Employee).options(joinedload(Employee.department)).filter(Employee.user_id == user_id).first()
        finally:
            if not self._external_session:
                session.close()

    def get_all(self) -> List[Employee]:
        session = self.get_session()
        try:
            return session.query(Employee).options(joinedload(Employee.department)).all()
        finally:
            if not self._external_session:
                session.close()

    def create_or_link_employee(
        self,
        user_id: int,
        department_id: Optional[int] = None,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        job_title: Optional[str] = None
    ) -> Employee:
        """Create or auto-link an Employee profile for a user if one does not exist."""
        with db.get_session() as session:
            existing = session.query(Employee).options(joinedload(Employee.department)).filter(Employee.user_id == user_id).first()
            if existing:
                return existing

            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise EntityNotFoundError("User", user_id)

            if not department_id:
                # Prefer IT Infrastructure or Information Technology, else first department
                it_dept = session.query(Department).filter(
                    (Department.name.ilike("%Information Technology%")) | (Department.name.ilike("%IT%"))
                ).first()
                if it_dept:
                    department_id = it_dept.department_id
                else:
                    first_dept = session.query(Department).first()
                    department_id = first_dept.department_id if first_dept else 1

            name = full_name or user.username.replace("_", " ").title()
            emp = Employee(
                user_id=user_id,
                department_id=department_id,
                full_name=name,
                phone=phone or "+1-555-0100",
                job_title=job_title or (user.role if user.role != "Employee" else "Staff Specialist")
            )
            session.add(emp)
            session.flush()
            session.refresh(emp)
            if emp.department:
                _ = emp.department.name
            log_audit("EMPLOYEE_PROFILE_LINKED", user.username, f"Auto-created employee profile for user ID {user_id}")
            return emp



class AgentRepository(BaseRepository):
    """Support Agent repository."""

    def get_by_user_id(self, user_id: int) -> Optional[SupportAgent]:
        session = self.get_session()
        try:
            return session.query(SupportAgent).options(joinedload(SupportAgent.team)).filter(SupportAgent.user_id == user_id).first()
        finally:
            if not self._external_session:
                session.close()

    def get_by_id(self, agent_id: int) -> Optional[SupportAgent]:
        session = self.get_session()
        try:
            return session.query(SupportAgent).options(joinedload(SupportAgent.team)).filter(SupportAgent.agent_id == agent_id).first()
        finally:
            if not self._external_session:
                session.close()

    def get_all(self) -> List[SupportAgent]:
        session = self.get_session()
        try:
            return session.query(SupportAgent).options(joinedload(SupportAgent.team)).all()
        finally:
            if not self._external_session:
                session.close()

    def get_all_teams(self) -> List[SupportTeam]:
        session = self.get_session()
        try:
            return session.query(SupportTeam).all()
        finally:
            if not self._external_session:
                session.close()

    def update_availability(self, agent_id: int, is_available: bool) -> bool:
        """Update active availability status for an agent."""
        with db.get_session() as session:
            agent = session.query(SupportAgent).filter(SupportAgent.agent_id == agent_id).first()
            if agent:
                agent.is_available = is_available
                session.flush()
                log_audit("AGENT_AVAILABILITY_CHANGED", str(agent.full_name), f"Available: {is_available}")
                return True
            return False


class TicketRepository(BaseRepository):
    """Ticket operations repository with full CRUD, SLA calculations and filtering."""

    def _generate_ticket_number(self, session: Session) -> str:
        """Generate unique ticket identifier format: TCK-YYYY-XXXX."""
        year = datetime.utcnow().year
        prefix = f"TCK-{year}-"
        latest_ticket = (
            session.query(Ticket.ticket_number)
            .filter(Ticket.ticket_number.like(f"{prefix}%"))
            .order_by(Ticket.ticket_number.desc())
            .first()
        )
        if latest_ticket and latest_ticket[0]:
            try:
                last_seq = int(latest_ticket[0].split("-")[-1])
                return f"{prefix}{last_seq + 1:04d}"
            except (ValueError, IndexError):
                pass
        count = session.query(func.count(Ticket.ticket_id)).scalar() or 0
        return f"{prefix}{count + 1:04d}"

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
        """Create a new ticket with automatic SLA deadline calculation."""
        with db.get_session() as session:
            # Query SLA rule
            sla = session.query(SLARule).filter(SLARule.priority == priority).first()
            now = datetime.utcnow()

            resp_deadline = now + timedelta(minutes=sla.response_time_minutes) if sla else now + timedelta(hours=2)
            res_deadline = now + timedelta(minutes=sla.resolution_time_minutes) if sla else now + timedelta(hours=8)

            ticket_num = self._generate_ticket_number(session)

            ticket = Ticket(
                ticket_number=ticket_num,
                employee_id=employee_id,
                department_id=department_id,
                category_id=category_id,
                title=title,
                description=description,
                priority=priority,
                status="OPEN",
                sla_id=sla.sla_id if sla else None,
                response_deadline=resp_deadline,
                resolution_deadline=res_deadline,
                created_at=now
            )
            session.add(ticket)
            session.flush()

            # Record initial history
            history = TicketHistory(
                ticket_id=ticket.ticket_id,
                old_status=None,
                new_status="OPEN",
                changed_by_user_id=user_id,
                comment=f"Ticket created with priority '{priority}'",
                changed_at=now
            )
            session.add(history)
            session.flush()
            session.refresh(ticket)

            log_audit("TICKET_CREATED", f"User {user_id}", f"Ticket #{ticket.ticket_number} (ID: {ticket.ticket_id})")
            return ticket

    def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
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
                joinedload(Ticket.resolution)
            ).filter(Ticket.ticket_id == ticket_id).first()
        finally:
            if not self._external_session:
                session.close()

    def get_filtered_tickets(
        self,
        employee_id: Optional[int] = None,
        agent_id: Optional[int] = None,
        department_id: Optional[int] = None,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Ticket]:
        """Query tickets with multi-dimensional filtering."""
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

            if employee_id:
                q = q.filter(Ticket.employee_id == employee_id)
            if agent_id:
                q = q.filter(Ticket.assigned_agent_id == agent_id)
            if department_id:
                q = q.filter(Ticket.department_id == department_id)
            if category_id:
                q = q.filter(Ticket.category_id == category_id)
            if status and status != "All":
                q = q.filter(Ticket.status == status)
            if priority and priority != "All":
                q = q.filter(Ticket.priority == priority)
            if search_query:
                term = f"%{search_query}%"
                q = q.filter(or_(Ticket.title.ilike(term), Ticket.description.ilike(term), Ticket.ticket_number.ilike(term)))

            return q.order_by(desc(Ticket.created_at)).all()
        finally:
            if not self._external_session:
                session.close()

    def update_status(
        self,
        ticket_id: int,
        new_status: str,
        user_id: Optional[int] = None,
        comment: Optional[str] = None
    ) -> Ticket:
        """Update ticket lifecycle status with audit logging."""
        with db.get_session() as session:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if not ticket:
                raise TicketNotFoundError(ticket_id)

            old_status = ticket.status
            if old_status == new_status:
                return ticket

            ticket.status = new_status
            now = datetime.utcnow()

            # Lifecycle timestamps
            if new_status in ("IN PROGRESS", "ASSIGNED") and not ticket.first_responded_at:
                ticket.first_responded_at = now
            if new_status == "RESOLVED":
                ticket.resolved_at = now
            elif new_status == "CLOSED":
                ticket.closed_at = now
            elif new_status == "REOPENED":
                ticket.reopened_count += 1
                ticket.resolved_at = None
                ticket.closed_at = None

            # Audit record
            history = TicketHistory(
                ticket_id=ticket.ticket_id,
                old_status=old_status,
                new_status=new_status,
                changed_by_user_id=user_id,
                comment=comment or f"Status changed from {old_status} to {new_status}",
                changed_at=now
            )
            session.add(history)
            session.flush()
            session.refresh(ticket)

            log_audit("TICKET_STATUS_UPDATED", f"User {user_id}", f"Ticket #{ticket.ticket_number}: {old_status} -> {new_status}")
            return ticket

    def assign_ticket(
        self,
        ticket_id: int,
        agent_id: Optional[int],
        team_id: Optional[int],
        user_id: Optional[int] = None,
        comment: Optional[str] = None
    ) -> Ticket:
        """Assign ticket to support team and/or agent."""
        with db.get_session() as session:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if not ticket:
                raise TicketNotFoundError(ticket_id)

            ticket.assigned_agent_id = agent_id
            if team_id:
                ticket.assigned_team_id = team_id

            if ticket.status == "OPEN":
                ticket.status = "ASSIGNED"

            # History log
            agent_obj = session.query(SupportAgent).filter(SupportAgent.agent_id == agent_id).first() if agent_id else None
            agent_name = agent_obj.full_name if agent_obj else "Unassigned"

            history = TicketHistory(
                ticket_id=ticket.ticket_id,
                old_status=ticket.status,
                new_status=ticket.status,
                changed_by_user_id=user_id,
                comment=comment or f"Assigned to agent {agent_name}",
                changed_at=datetime.utcnow()
            )
            session.add(history)
            session.flush()
            session.refresh(ticket)

            log_audit("TICKET_ASSIGNED", f"User {user_id}", f"Ticket #{ticket.ticket_number} assigned to {agent_name}")
            return ticket

    def add_comment(
        self,
        ticket_id: int,
        user_id: int,
        comment_text: str,
        is_internal: bool = False
    ) -> Comment:
        """Add public or internal comment to ticket."""
        with db.get_session() as session:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if not ticket:
                raise TicketNotFoundError(ticket_id)

            comment = Comment(
                ticket_id=ticket_id,
                user_id=user_id,
                comment_text=comment_text,
                is_internal=is_internal,
                created_at=datetime.utcnow()
            )
            session.add(comment)
            session.flush()
            session.refresh(comment)

            log_audit("COMMENT_ADDED", f"User {user_id}", f"Ticket #{ticket.ticket_number} ({'Internal' if is_internal else 'Public'})")
            return comment

    def resolve_ticket(
        self,
        ticket_id: int,
        agent_id: int,
        root_cause: str,
        resolution_steps: str,
        resolution_category: str = "Technical Fix",
        user_id: Optional[int] = None
    ) -> TicketResolution:
        """Record ticket resolution and transition status to RESOLVED."""
        with db.get_session() as session:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if not ticket:
                raise TicketNotFoundError(ticket_id)

            resolution = TicketResolution(
                ticket_id=ticket_id,
                agent_id=agent_id,
                root_cause=root_cause,
                resolution_steps=resolution_steps,
                resolution_category=resolution_category,
                resolved_at=datetime.utcnow()
            )
            session.merge(resolution)

            # Update ticket status
            ticket.status = "RESOLVED"
            ticket.resolved_at = datetime.utcnow()

            history = TicketHistory(
                ticket_id=ticket.ticket_id,
                old_status=ticket.status,
                new_status="RESOLVED",
                changed_by_user_id=user_id,
                comment=f"Resolved: {root_cause[:50]}...",
                changed_at=datetime.utcnow()
            )
            session.add(history)
            session.flush()

            log_audit("TICKET_RESOLVED", f"User {user_id}", f"Ticket #{ticket.ticket_number}")
            return resolution

    def submit_csat(self, ticket_id: int, rating: int, feedback: Optional[str] = None, user_id: Optional[int] = None) -> bool:
        """Submit Customer Satisfaction (CSAT) rating (1-5) and feedback."""
        with db.get_session() as session:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if not ticket:
                raise TicketNotFoundError(ticket_id)
            ticket.csat_rating = max(1, min(5, rating))
            ticket.csat_feedback = feedback.strip() if feedback else None
            log_audit("CSAT_SUBMITTED", f"User {user_id}", f"Ticket #{ticket.ticket_number}: {ticket.csat_rating} Stars")
            return True


class KnowledgeRepository(BaseRepository):
    """Knowledge base articles repository for self-service help & ticket deflection."""

    def get_all(self) -> List[KnowledgeArticle]:
        """Fetch all knowledge base articles with their categories."""
        with db.get_session() as session:
            return session.query(KnowledgeArticle).options(joinedload(KnowledgeArticle.category)).all()

    def get_by_id(self, article_id: int) -> Optional[KnowledgeArticle]:
        """Fetch article by ID."""
        with db.get_session() as session:
            return session.query(KnowledgeArticle).options(joinedload(KnowledgeArticle.category)).filter(KnowledgeArticle.article_id == article_id).first()

    def get_by_category(self, category_id: int) -> List[KnowledgeArticle]:
        """Fetch articles for a specific category."""
        with db.get_session() as session:
            return session.query(KnowledgeArticle).filter(KnowledgeArticle.category_id == category_id).all()

    def search_articles(self, query: str) -> List[KnowledgeArticle]:
        """Search knowledge articles by title, content, or tags."""
        if not query or not query.strip():
            return self.get_all()
        q_term = f"%{query.strip().lower()}%"
        with db.get_session() as session:
            return session.query(KnowledgeArticle).options(joinedload(KnowledgeArticle.category)).filter(
                or_(
                    func.lower(KnowledgeArticle.title).like(q_term),
                    func.lower(KnowledgeArticle.content).like(q_term),
                    func.lower(KnowledgeArticle.tags).like(q_term)
                )
            ).all()

    def mark_helpful(self, article_id: int) -> int:
        """Increment helpful count for an article."""
        with db.get_session() as session:
            art = session.query(KnowledgeArticle).filter(KnowledgeArticle.article_id == article_id).first()
            if art:
                art.helpful_count = (art.helpful_count or 0) + 1
                return art.helpful_count
            return 0

    def increment_view(self, article_id: int) -> int:
        """Increment view count for an article."""
        with db.get_session() as session:
            art = session.query(KnowledgeArticle).filter(KnowledgeArticle.article_id == article_id).first()
            if art:
                art.views_count = (art.views_count or 0) + 1
                return art.views_count
            return 0

