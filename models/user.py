from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Department:
    department_id: int
    name: str
    code: str
    head_name: Optional[str] = None
    contact_email: Optional[str] = None
    budget_code: Optional[str] = None

@dataclass
class SupportTeam:
    team_id: int
    name: str
    specialization: str
    lead_name: Optional[str] = None
    operating_hours: str = "24x7"

@dataclass
class User:
    user_id: int
    full_name: str
    email: str
    role: str  # 'Employee', 'Support Agent', 'Team Lead', 'IT Admin', 'Executive'
    department_id: Optional[int] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    @property
    def is_admin(self) -> bool:
        return self.role in ["IT Admin", "Executive"]

    @property
    def is_agent(self) -> bool:
        return self.role in ["Support Agent", "Team Lead", "IT Admin"]

@dataclass
class Agent:
    agent_id: int
    user_id: int
    team_id: Optional[int]
    tier: str  # L1, L2, L3, Specialist
    max_active_tickets: int = 10
    status: str = "Available"
    skills: Optional[str] = None
    user: Optional[User] = None
