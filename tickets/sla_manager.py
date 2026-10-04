"""SLA Management & Compliance Engine.

Member 2: Ticket Management, SLA & Support Operations.
Handles SLA rules, deadline calculations, breach detection, countdowns, and compliance analysis.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import db
from core.models import SLARule, Ticket
from core.exceptions import SLAConfigurationError
from core.logger import log_audit, log_error


# Default standard industry SLAs (in minutes)
DEFAULT_SLA_CONFIG = {
    "Critical": {"response_minutes": 15, "resolution_minutes": 120},    # 15m resp, 2h res
    "High":     {"response_minutes": 30, "resolution_minutes": 240},    # 30m resp, 4h res
    "Medium":   {"response_minutes": 120, "resolution_minutes": 480},   # 2h resp, 8h res
    "Low":      {"response_minutes": 240, "resolution_minutes": 1440}   # 4h resp, 24h res
}


class SLAManager:
    """Core SLA Manager for calculating deadlines, monitoring breaches, and tracking SLA performance."""

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    def get_session(self) -> Session:
        """Helper to get db session."""
        if self._external_session:
            return self._external_session
        return db.Session()

    def get_sla_rule(self, priority: str) -> Optional[SLARule]:
        """Fetch active SLA rule for a specific priority."""
        session = self.get_session()
        try:
            rule = session.query(SLARule).filter(
                SLARule.priority == priority,
                SLARule.is_active == True
            ).first()
            return rule
        finally:
            if not self._external_session:
                session.close()

    def get_all_rules(self) -> List[SLARule]:
        """Retrieve all active and inactive SLA rules."""
        session = self.get_session()
        try:
            return session.query(SLARule).all()
        finally:
            if not self._external_session:
                session.close()

    def calculate_deadlines(
        self,
        priority: str,
        start_time: Optional[datetime] = None
    ) -> Tuple[datetime, datetime, Optional[int]]:
        """Calculate response and resolution deadlines from creation timestamp.
        
        Returns:
            Tuple of (response_deadline, resolution_deadline, sla_id)
        """
        now = start_time or datetime.utcnow()
        rule = self.get_sla_rule(priority)

        if rule:
            resp_delta = timedelta(minutes=rule.response_time_minutes)
            res_delta = timedelta(minutes=rule.resolution_time_minutes)
            sla_id = rule.sla_id
        else:
            # Fallback to default config
            fallback = DEFAULT_SLA_CONFIG.get(priority, DEFAULT_SLA_CONFIG["Medium"])
            resp_delta = timedelta(minutes=fallback["response_minutes"])
            res_delta = timedelta(minutes=fallback["resolution_minutes"])
            sla_id = None

        response_deadline = now + resp_delta
        resolution_deadline = now + res_delta

        return response_deadline, resolution_deadline, sla_id

    def check_ticket_sla_status(self, ticket: Ticket, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Evaluate real-time SLA status for a given ticket.
        
        Returns:
            Dict containing:
                - is_response_breached (bool)
                - is_resolution_breached (bool)
                - is_breached (bool)
                - response_status ('Compliant', 'Warning', 'Breached', 'Met')
                - resolution_status ('Compliant', 'Warning', 'Breached', 'Met')
                - time_remaining_seconds (float)
                - time_remaining_formatted (str)
                - percentage_consumed (float: 0.0 to 100.0+)
        """
        now = current_time or datetime.utcnow()
        result = {
            "is_response_breached": False,
            "is_resolution_breached": False,
            "is_breached": False,
            "response_status": "Compliant",
            "resolution_status": "Compliant",
            "time_remaining_seconds": 0,
            "time_remaining_formatted": "N/A",
            "percentage_consumed": 0.0
        }

        # 1. Response SLA Check
        if ticket.response_deadline:
            if ticket.first_responded_at:
                if ticket.first_responded_at > ticket.response_deadline:
                    result["is_response_breached"] = True
                    result["response_status"] = "Breached"
                else:
                    result["response_status"] = "Met"
            else:
                if now > ticket.response_deadline:
                    result["is_response_breached"] = True
                    result["response_status"] = "Breached"
                elif (ticket.response_deadline - now).total_seconds() < 15 * 60: # <15 min warning
                    result["response_status"] = "Warning"

        # 2. Resolution SLA Check
        if ticket.resolution_deadline:
            created_at = ticket.created_at or now
            total_duration = (ticket.resolution_deadline - created_at).total_seconds()

            if ticket.status in ("RESOLVED", "CLOSED") and ticket.resolved_at:
                if ticket.resolved_at > ticket.resolution_deadline:
                    result["is_resolution_breached"] = True
                    result["resolution_status"] = "Breached"
                    result["time_remaining_formatted"] = "Resolved Late (Breached)"
                else:
                    result["resolution_status"] = "Met"
                    result["time_remaining_formatted"] = "Resolved on Time"

                consumed_secs = (ticket.resolved_at - created_at).total_seconds()
                result["percentage_consumed"] = round(min(100.0, (consumed_secs / total_duration * 100.0)) if total_duration > 0 else 100.0, 1)
            else:
                # Still open/active
                remaining_secs = (ticket.resolution_deadline - now).total_seconds()
                result["time_remaining_seconds"] = remaining_secs

                if remaining_secs < 0:
                    result["is_resolution_breached"] = True
                    result["resolution_status"] = "Breached"
                    overdue_minutes = int(abs(remaining_secs) // 60)
                    if overdue_minutes < 60:
                        result["time_remaining_formatted"] = f"Overdue by {overdue_minutes}m"
                    else:
                        hours = overdue_minutes // 60
                        mins = overdue_minutes % 60
                        result["time_remaining_formatted"] = f"Overdue by {hours}h {mins}m"
                    result["percentage_consumed"] = 100.0
                else:
                    elapsed_secs = (now - created_at).total_seconds()
                    pct = (elapsed_secs / total_duration * 100.0) if total_duration > 0 else 0.0
                    result["percentage_consumed"] = round(min(100.0, pct), 1)

                    rem_minutes = int(remaining_secs // 60)
                    if rem_minutes < 60:
                        result["time_remaining_formatted"] = f"{rem_minutes}m remaining"
                    else:
                        hours = rem_minutes // 60
                        mins = rem_minutes % 60
                        result["time_remaining_formatted"] = f"{hours}h {mins}m remaining"

                    # Warning if less than 25% time remains
                    if (remaining_secs / total_duration) < 0.25 if total_duration > 0 else False:
                        result["resolution_status"] = "Warning"

        result["is_breached"] = result["is_response_breached"] or result["is_resolution_breached"]
        return result

    def get_sla_metrics_summary(self) -> Dict[str, Any]:
        """Calculate overall SLA compliance statistics across all tickets."""
        session = self.get_session()
        try:
            tickets = session.query(Ticket).all()
            total_tickets = len(tickets)
            if total_tickets == 0:
                return {
                    "total_tickets": 0,
                    "compliant_tickets": 0,
                    "breached_tickets": 0,
                    "compliance_rate": 100.0,
                    "avg_response_time_min": 0.0,
                    "avg_resolution_time_min": 0.0,
                    "approaching_breach_count": 0
                }

            breached_count = 0
            approaching_count = 0
            response_times = []
            resolution_times = []

            for t in tickets:
                status_info = self.check_ticket_sla_status(t)
                if status_info["is_breached"]:
                    breached_count += 1
                elif status_info["resolution_status"] == "Warning" and t.status not in ("RESOLVED", "CLOSED"):
                    approaching_count += 1

                # Response duration
                if t.first_responded_at and t.created_at:
                    r_mins = (t.first_responded_at - t.created_at).total_seconds() / 60.0
                    response_times.append(r_mins)

                # Resolution duration
                if t.resolved_at and t.created_at:
                    res_mins = (t.resolved_at - t.created_at).total_seconds() / 60.0
                    resolution_times.append(res_mins)

            compliant_count = total_tickets - breached_count
            compliance_rate = round((compliant_count / total_tickets) * 100.0, 2)
            avg_resp = round(sum(response_times) / len(response_times), 1) if response_times else 0.0
            avg_res = round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else 0.0

            return {
                "total_tickets": total_tickets,
                "compliant_tickets": compliant_count,
                "breached_tickets": breached_count,
                "compliance_rate": compliance_rate,
                "avg_response_time_min": avg_resp,
                "avg_resolution_time_min": avg_res,
                "approaching_breach_count": approaching_count
            }
        finally:
            if not self._external_session:
                session.close()

    def update_sla_rule(
        self,
        priority: str,
        response_time_minutes: int,
        resolution_time_minutes: int,
        user_id: Optional[int] = None
    ) -> SLARule:
        """Update or create SLA thresholds for a given priority level."""
        if response_time_minutes <= 0 or resolution_time_minutes <= 0:
            raise SLAConfigurationError("SLA response and resolution times must be positive non-zero minutes.")

        with db.get_session() as session:
            rule = session.query(SLARule).filter(SLARule.priority == priority).first()
            if rule:
                rule.response_time_minutes = response_time_minutes
                rule.resolution_time_minutes = resolution_time_minutes
            else:
                rule = SLARule(
                    priority=priority,
                    response_time_minutes=response_time_minutes,
                    resolution_time_minutes=resolution_time_minutes,
                    is_active=True
                )
                session.add(rule)

            session.flush()
            session.refresh(rule)
            log_audit("SLA_RULE_UPDATED", f"User {user_id}", f"Priority: {priority} (Resp: {response_time_minutes}m, Res: {resolution_time_minutes}m)")
            return rule
