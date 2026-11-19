from datetime import datetime
from database.connection import db_manager
import pandas as pd
from utils.logger import get_logger

logger = get_logger("sla_service")

class SLAService:
    @staticmethod
    def get_all_policies():
        """Returns all configured SLA policies."""
        sql = "SELECT * FROM sla_policies ORDER BY resolution_time_hours ASC;"
        return db_manager.fetch_dataframe(sql)

    @staticmethod
    def update_policy(sla_id: int, response_hrs: float, resolution_hrs: float, escalation_hrs: float, desc: str):
        """Updates SLA policy thresholds."""
        sql = """
            UPDATE sla_policies 
            SET response_time_hours = :resp, resolution_time_hours = :res, 
                escalation_time_hours = :esc, description = :desc
            WHERE sla_id = :sla_id
        """
        db_manager.execute_non_query(sql, {
            "sla_id": sla_id, "resp": response_hrs, "res": resolution_hrs,
            "esc": escalation_hrs, "desc": desc
        })
        return True

    @staticmethod
    def get_sla_status(ticket: dict) -> dict:
        """Calculates real-time SLA countdown, breach status, and alert state."""
        status = ticket.get("status")
        created_at = ticket.get("created_at")
        sla_due = ticket.get("sla_due_date")
        breached = bool(ticket.get("sla_breached"))

        if not sla_due:
            return {"label": "No SLA", "color": "gray", "hours_left": None, "is_breached": False}

        if isinstance(sla_due, str):
            sla_due_dt = datetime.strptime(sla_due[:19], "%Y-%m-%d %H:%M:%S")
        else:
            sla_due_dt = sla_due

        now = datetime.now()

        if status in ["Resolved", "Closed"]:
            if breached:
                return {"label": "Breached (Resolved Late)", "color": "#ef4444", "hours_left": 0, "is_breached": True}
            return {"label": "SLA Met", "color": "#10b981", "hours_left": None, "is_breached": False}

        # Active ticket
        time_diff = (sla_due_dt - now).total_seconds() / 3600.0

        if time_diff < 0 or breached:
            return {
                "label": f"BREACHED ({abs(time_diff):.1f}h overdue)",
                "color": "#ef4444",
                "hours_left": time_diff,
                "is_breached": True,
                "urgency": "critical"
            }
        elif time_diff <= 2.0:
            return {
                "label": f"APPROACHING BREACH ({time_diff:.1f}h left)",
                "color": "#f59e0b",
                "hours_left": time_diff,
                "is_breached": False,
                "urgency": "high"
            }
        else:
            return {
                "label": f"{time_diff:.1f}h remaining",
                "color": "#3b82f6",
                "hours_left": time_diff,
                "is_breached": False,
                "urgency": "normal"
            }

    @staticmethod
    def get_at_risk_tickets() -> pd.DataFrame:
        """Fetches active tickets that are either breached or approaching SLA breach within 4 hours."""
        sql = """
            SELECT 
                t.ticket_id, t.ticket_number, t.title, t.priority, t.status,
                t.sla_due_date, t.sla_breached,
                req.full_name AS requester_name,
                ag_u.full_name AS assigned_agent,
                st.name AS team_name
            FROM tickets t
            JOIN users req ON t.requester_id = req.user_id
            LEFT JOIN support_teams st ON t.team_id = st.team_id
            LEFT JOIN agents ag ON t.assigned_agent_id = ag.agent_id
            LEFT JOIN users ag_u ON ag.user_id = ag_u.user_id
            WHERE t.status NOT IN ('Resolved', 'Closed')
            ORDER BY t.sla_due_date ASC;
        """
        return db_manager.fetch_dataframe(sql)
