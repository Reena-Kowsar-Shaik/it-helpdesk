from dataclasses import dataclass
from typing import Optional

@dataclass
class SLAPolicy:
    sla_id: int
    priority: str
    response_time_hours: float
    resolution_time_hours: float
    escalation_time_hours: float
    description: Optional[str] = None
