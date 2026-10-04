"""Ticket History & Audit Trail Engine.

Member 2: Ticket Management, SLA & Support Operations.
Maintains comprehensive audit logs, status transition tracking, chronological timelines,
and lifecycle metrics for IT helpdesk tickets.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from core.database import db
from core.models import TicketHistory, Ticket, User
from core.logger import log_audit, log_error


class TicketHistoryManager:
    """Manages recording, retrieving, and analyzing ticket lifecycle audit logs."""

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    def get_session(self) -> Session:
        """Helper to get db session."""
        if self._external_session:
            return self._external_session
        return db.Session()

    def record_history(
        self,
        ticket_id: int,
        old_status: Optional[str],
        new_status: str,
        changed_by_user_id: Optional[int] = None,
        comment: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> TicketHistory:
        """Log a new status transition or event into ticket_history."""
        with db.get_session() as session:
            record = TicketHistory(
                ticket_id=ticket_id,
                old_status=old_status,
                new_status=new_status,
                changed_by_user_id=changed_by_user_id,
                comment=comment,
                changed_at=timestamp or datetime.utcnow()
            )
            session.add(record)
            session.flush()
            session.refresh(record)

            log_audit(
                "TICKET_HISTORY_RECORDED",
                f"User {changed_by_user_id or 'System'}",
                f"Ticket ID {ticket_id}: '{old_status}' -> '{new_status}' - {comment or ''}"
            )
            return record

    def get_ticket_timeline(self, ticket_id: int) -> List[Dict[str, Any]]:
        """Retrieve complete chronological audit trail with parsed display metadata."""
        session = self.get_session()
        try:
            records = session.query(TicketHistory).options(
                joinedload(TicketHistory.user)
            ).filter(
                TicketHistory.ticket_id == ticket_id
            ).order_by(TicketHistory.changed_at.asc()).all()

            timeline = []
            for idx, r in enumerate(records):
                # Calculate time elapsed since previous event
                time_delta_str = ""
                if idx > 0:
                    delta = r.changed_at - records[idx - 1].changed_at
                    total_minutes = int(delta.total_seconds() // 60)
                    if total_minutes < 60:
                        time_delta_str = f"+{total_minutes}m"
                    else:
                        hours = total_minutes // 60
                        mins = total_minutes % 60
                        time_delta_str = f"+{hours}h {mins}m"

                user_name = r.user.username if r.user else "System / Automated Rule"
                user_role = r.user.role if r.user else "System"

                timeline.append({
                    "history_id": r.history_id,
                    "ticket_id": r.ticket_id,
                    "old_status": r.old_status,
                    "new_status": r.new_status,
                    "changed_by": user_name,
                    "changed_by_role": user_role,
                    "changed_by_user_id": r.changed_by_user_id,
                    "comment": r.comment or "",
                    "timestamp": r.changed_at,
                    "timestamp_formatted": r.changed_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "time_since_previous": time_delta_str
                })

            return timeline
        finally:
            if not self._external_session:
                session.close()

    def get_lifecycle_stage_durations(self, ticket_id: int) -> Dict[str, float]:
        """Compute the total duration (in minutes) a ticket spent in each status stage."""
        timeline = self.get_ticket_timeline(ticket_id)
        if not timeline:
            return {}

        durations: Dict[str, float] = {}
        for i in range(len(timeline) - 1):
            curr_event = timeline[i]
            next_event = timeline[i + 1]
            status = curr_event["new_status"]
            elapsed = (next_event["timestamp"] - curr_event["timestamp"]).total_seconds() / 60.0
            durations[status] = durations.get(status, 0.0) + round(elapsed, 2)

        # For the active / final status:
        last_event = timeline[-1]
        active_status = last_event["new_status"]
        if active_status not in ("CLOSED", "RESOLVED"):
            now = datetime.utcnow()
            elapsed = (now - last_event["timestamp"]).total_seconds() / 60.0
            durations[active_status] = durations.get(active_status, 0.0) + round(elapsed, 2)

        return durations

    def get_ticket_audit_metrics(self, ticket_id: int) -> Dict[str, Any]:
        """Extract high-level audit summary metrics for a ticket."""
        timeline = self.get_ticket_timeline(ticket_id)
        reassignments = sum(1 for e in timeline if "Assigned to" in (e.get("comment") or ""))
        status_transitions = len(timeline)
        durations = self.get_lifecycle_stage_durations(ticket_id)

        return {
            "ticket_id": ticket_id,
            "total_events": status_transitions,
            "reassignments_count": reassignments,
            "stage_durations_minutes": durations,
            "first_event_time": timeline[0]["timestamp"] if timeline else None,
            "last_event_time": timeline[-1]["timestamp"] if timeline else None
        }
