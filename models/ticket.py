from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Ticket:
    ticket_id: int
    ticket_number: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    requester_id: int
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    assigned_agent_id: Optional[int] = None
    created_at: Optional[datetime] = None
    first_response_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    sla_due_date: Optional[datetime] = None
    sla_breached: bool = False
    reopen_count: int = 0
    satisfaction_rating: Optional[int] = None
    feedback_comments: Optional[str] = None
    resolution_notes: Optional[str] = None
    root_cause: Optional[str] = None
    actual_hours: Optional[float] = None

@dataclass
class TicketComment:
    comment_id: int
    ticket_id: int
    user_id: int
    comment_type: str  # 'Public', 'Internal Note'
    message: str
    created_at: Optional[datetime] = None
    author_name: Optional[str] = None

@dataclass
class TicketAuditHistory:
    history_id: int
    ticket_id: int
    changed_by: Optional[int]
    action_type: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    changed_by_name: Optional[str] = None
