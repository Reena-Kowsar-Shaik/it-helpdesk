"""Object-Oriented Database Models for IT Helpdesk System."""

from datetime import datetime, timedelta
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint
)
from sqlalchemy.orm import relationship
from core.database import Base

class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(20), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    employees = relationship("Employee", back_populates="department")
    tickets = relationship("Ticket", back_populates="department")

    def __repr__(self):
        return f"<Department(id={self.department_id}, code='{self.code}', name='{self.name}')>"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        SQLEnum('Employee', 'Support Agent', 'Team Lead', 'Admin', name='user_roles'),
        nullable=False,
        default='Employee',
        index=True
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employee = relationship("Employee", back_populates="user", uselist=False, cascade="all, delete-orphan")
    agent = relationship("SupportAgent", back_populates="user", uselist=False, cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user")
    history_records = relationship("TicketHistory", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.user_id}, username='{self.username}', role='{self.role}')>"

    def is_admin(self) -> bool:
        return self.role == 'Admin'

    def is_agent(self) -> bool:
        return self.role in ('Support Agent', 'Team Lead')

    def is_employee(self) -> bool:
        return self.role == 'Employee'


class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    department_id = Column(Integer, ForeignKey("departments.department_id", ondelete="RESTRICT"), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(25), nullable=True)
    job_title = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="employee")
    department = relationship("Department", back_populates="employees")
    tickets = relationship("Ticket", back_populates="employee")

    def __repr__(self):
        return f"<Employee(id={self.employee_id}, name='{self.full_name}', dept_id={self.department_id})>"


class SupportTeam(Base):
    __tablename__ = "support_teams"

    team_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    agents = relationship("SupportAgent", back_populates="team")
    tickets = relationship("Ticket", back_populates="team")

    def __repr__(self):
        return f"<SupportTeam(id={self.team_id}, name='{self.name}')>"


class SupportAgent(Base):
    __tablename__ = "support_agents"

    agent_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    team_id = Column(Integer, ForeignKey("support_teams.team_id", ondelete="RESTRICT"), nullable=False)
    full_name = Column(String(100), nullable=False)
    specialization = Column(String(100), default="General IT")
    is_available = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="agent")
    team = relationship("SupportTeam", back_populates="agents")
    assigned_tickets = relationship("Ticket", back_populates="assigned_agent")
    resolutions = relationship("TicketResolution", back_populates="agent")

    def __repr__(self):
        return f"<SupportAgent(id={self.agent_id}, name='{self.full_name}', team_id={self.team_id})>"


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    default_priority = Column(
        SQLEnum('Critical', 'High', 'Medium', 'Low', name='priority_enum'),
        nullable=False,
        default='Medium'
    )
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tickets = relationship("Ticket", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.category_id}, name='{self.name}')>"


class SLARule(Base):
    __tablename__ = "sla_rules"

    sla_id = Column(Integer, primary_key=True, autoincrement=True)
    priority = Column(
        SQLEnum('Critical', 'High', 'Medium', 'Low', name='sla_priority_enum'),
        nullable=False,
        unique=True
    )
    response_time_minutes = Column(Integer, nullable=False)
    resolution_time_minutes = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('response_time_minutes > 0', name='chk_sla_resp_pos'),
        CheckConstraint('resolution_time_minutes > 0', name='chk_sla_res_pos'),
    )

    tickets = relationship("Ticket", back_populates="sla")

    def __repr__(self):
        return f"<SLARule(priority='{self.priority}', resp_min={self.response_time_minutes}, res_min={self.resolution_time_minutes})>"


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_number = Column(String(30), nullable=False, unique=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete="RESTRICT"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.department_id", ondelete="RESTRICT"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(
        SQLEnum('Critical', 'High', 'Medium', 'Low', name='ticket_priority_enum'),
        nullable=False,
        default='Medium',
        index=True
    )
    status = Column(
        SQLEnum('OPEN', 'ASSIGNED', 'IN PROGRESS', 'RESOLVED', 'CLOSED', 'REOPENED', name='ticket_status_enum'),
        nullable=False,
        default='OPEN',
        index=True
    )
    assigned_team_id = Column(Integer, ForeignKey("support_teams.team_id", ondelete="SET NULL"), nullable=True)
    assigned_agent_id = Column(Integer, ForeignKey("support_agents.agent_id", ondelete="SET NULL"), nullable=True, index=True)
    sla_id = Column(Integer, ForeignKey("sla_rules.sla_id", ondelete="SET NULL"), nullable=True)
    response_deadline = Column(DateTime, nullable=True)
    resolution_deadline = Column(DateTime, nullable=True)
    first_responded_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    reopened_count = Column(Integer, nullable=False, default=0)
    csat_rating = Column(Integer, nullable=True)  # 1 to 5 stars
    csat_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employee = relationship("Employee", back_populates="tickets")
    department = relationship("Department", back_populates="tickets")
    category = relationship("Category", back_populates="tickets")
    team = relationship("SupportTeam", back_populates="tickets")
    assigned_agent = relationship("SupportAgent", back_populates="assigned_tickets")
    sla = relationship("SLARule", back_populates="tickets")
    history = relationship("TicketHistory", back_populates="ticket", cascade="all, delete-orphan", order_by="desc(TicketHistory.changed_at)")
    comments = relationship("Comment", back_populates="ticket", cascade="all, delete-orphan", order_by="Comment.created_at")
    resolution = relationship("TicketResolution", back_populates="ticket", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ticket(id={self.ticket_id}, number='{self.ticket_number}', status='{self.status}', priority='{self.priority}')>"

    def is_breached(self) -> bool:
        """Check if resolution deadline has been breached."""
        if not self.resolution_deadline:
            return False
        comparison_time = self.resolved_at or datetime.utcnow()
        return comparison_time > self.resolution_deadline


class TicketHistory(Base):
    __tablename__ = "ticket_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=False)
    changed_by_user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    comment = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="history")
    user = relationship("User", back_populates="history_records")

    def __repr__(self):
        return f"<TicketHistory(id={self.history_id}, ticket_id={self.ticket_id}, '{self.old_status}'->'{self.new_status}')>"


class Comment(Base):
    __tablename__ = "comments"

    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    comment_text = Column(Text, nullable=False)
    is_internal = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship("Ticket", back_populates="comments")
    user = relationship("User", back_populates="comments")

    def __repr__(self):
        return f"<Comment(id={self.comment_id}, ticket_id={self.ticket_id}, user_id={self.user_id})>"


class TicketResolution(Base):
    __tablename__ = "ticket_resolutions"

    resolution_id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    agent_id = Column(Integer, ForeignKey("support_agents.agent_id", ondelete="RESTRICT"), nullable=False)
    root_cause = Column(Text, nullable=False)
    resolution_steps = Column(Text, nullable=False)
    resolution_category = Column(String(100), default="Technical Fix")
    resolved_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship("Ticket", back_populates="resolution")
    agent = relationship("SupportAgent", back_populates="resolutions")

    def __repr__(self):
        return f"<TicketResolution(id={self.resolution_id}, ticket_id={self.ticket_id})>"


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    article_id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False)
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    tags = Column(String(255), nullable=True)
    views_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category")

    def __repr__(self):
        return f"<KnowledgeArticle(id={self.article_id}, title='{self.title}')>"
