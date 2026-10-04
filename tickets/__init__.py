"""Tickets Module Package.

Member 2: Ticket Management, SLA & Support Operations.
Exposes core ticket lifecycle management, assignment engine, SLA calculations,
audit histories, and multi-dimensional search filters.
"""

from tickets.sla_manager import SLAManager, DEFAULT_SLA_CONFIG
from tickets.ticket_history import TicketHistoryManager
from tickets.ticket_assignment import TicketAssignmentManager, CATEGORY_TEAM_ROUTING
from tickets.ticket_filters import TicketFilterService, TicketFilterCriteria
from tickets.ticket_manager import TicketManager, ALLOWED_TRANSITIONS

__all__ = [
    "SLAManager",
    "DEFAULT_SLA_CONFIG",
    "TicketHistoryManager",
    "TicketAssignmentManager",
    "CATEGORY_TEAM_ROUTING",
    "TicketFilterService",
    "TicketFilterCriteria",
    "TicketManager",
    "ALLOWED_TRANSITIONS"
]
