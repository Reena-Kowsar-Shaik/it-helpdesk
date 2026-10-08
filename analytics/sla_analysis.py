"""SLA Compliance, Deadline Breach & Risk Intelligence Module.

Member 3: SQL Analytics & Business Intelligence Specialist
Provides analysis of response SLAs, resolution SLAs, deadlines,
imminent breach risks, and priority-tier compliance tracking.
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from analytics.sql_queries import SQLQueryManager, QUERY_SLA_BREACH_DRILLDOWN

class SLAAnalytics:
    """Monitors SLA targets, breaches, and performance deadlines across the organization."""

    def __init__(self):
        self.query_mgr = SQLQueryManager()

    def get_sla_kpi_summary(self) -> Dict[str, Any]:
        """Calculates global SLA compliance statistics using aggregate SQL or ORM fallback."""
        default_summary = {
            "total_tracked_tickets": 0,
            "total_resolved": 0,
            "compliant_count": 0,
            "breached_count": 0,
            "at_risk_count": 0,
            "compliance_pct": 100.0,
            "avg_response_minutes": 0.0,
            "avg_resolution_hours": 0.0
        }
        
        sql = """
        SELECT 
            COUNT(ticket_id) AS total_tracked_tickets,
            SUM(CASE WHEN status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) AS total_resolved,
            SUM(CASE 
                WHEN status IN ('RESOLVED', 'CLOSED') AND (resolved_at <= resolution_deadline OR resolution_deadline IS NULL) THEN 1
                WHEN status NOT IN ('RESOLVED', 'CLOSED') AND (datetime('now') <= resolution_deadline OR resolution_deadline IS NULL) THEN 1
                ELSE 0 
            END) AS compliant_count,
            SUM(CASE 
                WHEN status IN ('RESOLVED', 'CLOSED') AND resolved_at > resolution_deadline THEN 1
                WHEN status NOT IN ('RESOLVED', 'CLOSED') AND datetime('now') > resolution_deadline THEN 1
                ELSE 0 
            END) AS breached_count
        FROM tickets;
        """
        rows = self.query_mgr.run_query(sql)
        if not rows or not rows[0].get("total_tracked_tickets"):
            # Fallback to direct Python/ORM query
            from core.database import db
            from core.models import Ticket
            try:
                with db.get_session() as session:
                    all_t = session.query(Ticket).all()
                    if not all_t:
                        return default_summary
                    total = len(all_t)
                    total_res = sum(1 for t in all_t if t.status in ("RESOLVED", "CLOSED"))
                    breached = sum(1 for t in all_t if t.is_breached())
                    compliant = total - breached
                    compliance_pct = round((compliant / total * 100.0), 1) if total > 0 else 100.0

                    # Calculate avg response / resolution
                    res_durations = [(t.resolved_at - t.created_at).total_seconds() / 3600.0 for t in all_t if t.resolved_at and t.created_at]
                    avg_res = round(sum(res_durations) / len(res_durations), 2) if res_durations else 0.0

                    resp_durations = [(t.first_responded_at - t.created_at).total_seconds() / 60.0 for t in all_t if t.first_responded_at and t.created_at]
                    avg_resp = round(sum(resp_durations) / len(resp_durations), 1) if resp_durations else 0.0

                    return {
                        "total_tracked_tickets": total,
                        "total_resolved": total_res,
                        "compliant_count": compliant,
                        "breached_count": breached,
                        "at_risk_count": 0,
                        "compliance_pct": compliance_pct,
                        "avg_response_minutes": avg_resp,
                        "avg_resolution_hours": avg_res
                    }
            except Exception:
                return default_summary

        r = rows[0]
        total = int(r.get("total_tracked_tickets") or 0)
        total_res = int(r.get("total_resolved") or 0)
        breached = int(r.get("breached_count") or 0)
        compliant = int(r.get("compliant_count") or (total - breached))
        compliance_pct = round(((total - breached) / total * 100.0), 1) if total > 0 else 100.0

        return {
            "total_tracked_tickets": total,
            "total_resolved": total_res,
            "compliant_count": compliant,
            "breached_count": breached,
            "at_risk_count": int(r.get("at_risk_count") or 0),
            "compliance_pct": compliance_pct,
            "avg_response_minutes": float(r.get("avg_response_minutes") or 0.0),
            "avg_resolution_hours": float(r.get("avg_resolution_hours") or 0.0)
        }

    def get_breached_tickets_list(self) -> pd.DataFrame:
        """Retrieves detailed log of tickets that exceeded their SLA resolution deadline."""
        df = self.query_mgr.run_query_df(QUERY_SLA_BREACH_DRILLDOWN)
        if df.empty:
            df = self.query_mgr.call_procedure_df("get_sla_breaches")

        if df.empty:
            from core.database import db
            from core.models import Ticket
            try:
                with db.get_session() as session:
                    all_t = session.query(Ticket).all()
                    data = []
                    for t in all_t:
                        if t.is_breached():
                            end_time = t.resolved_at or datetime.utcnow()
                            diff_min = int((end_time - t.resolution_deadline).total_seconds() / 60.0) if t.resolution_deadline else 0
                            status_str = "Resolved Past SLA" if t.status in ("RESOLVED", "CLOSED") else "Currently Breached"
                            data.append({
                                "ticket_id": t.ticket_id,
                                "ticket_number": t.ticket_number,
                                "title": t.title,
                                "priority": t.priority,
                                "status": t.status,
                                "department_name": t.department.name if t.department else "N/A",
                                "assigned_agent": t.assigned_agent.full_name if t.assigned_agent else "Unassigned",
                                "created_at": t.created_at,
                                "resolution_deadline": t.resolution_deadline,
                                "resolved_at": t.resolved_at,
                                "sla_status": status_str,
                                "breach_minutes": diff_min,
                                "breach_hours": round(diff_min / 60.0, 1)
                            })
                    data.sort(key=lambda x: x["breach_minutes"], reverse=True)
                    df = pd.DataFrame(data)
            except Exception:
                df = pd.DataFrame()

        if not df.empty:
            df = df[df["sla_status"].isin(["Resolved Past SLA", "Currently Breached"])]
            if "breach_minutes" in df.columns and "breach_hours" not in df.columns:
                df["breach_hours"] = (df["breach_minutes"] / 60.0).round(1)
        return df

    def get_at_risk_tickets(self) -> pd.DataFrame:
        """Identifies active tickets within 60 minutes of exceeding resolution deadlines."""
        sql = """
        SELECT 
            t.ticket_number,
            t.title,
            t.priority,
            d.name AS department_name,
            COALESCE(sa.full_name, 'Unassigned') AS assigned_agent,
            t.resolution_deadline,
            TIMESTAMPDIFF(MINUTE, NOW(), t.resolution_deadline) AS minutes_remaining
        FROM tickets t
        JOIN departments d ON t.department_id = d.department_id
        LEFT JOIN support_agents sa ON t.assigned_agent_id = sa.agent_id
        WHERE t.status NOT IN ('RESOLVED', 'CLOSED')
          AND t.resolution_deadline IS NOT NULL
          AND TIMESTAMPDIFF(MINUTE, NOW(), t.resolution_deadline) BETWEEN 0 AND 60
        ORDER BY minutes_remaining ASC;
        """
        return self.query_mgr.run_query_df(sql)

    def get_sla_compliance_by_priority(self) -> pd.DataFrame:
        """Computes SLA compliance breakdown partitioned by incident priority tier."""
        sql = """
        SELECT 
            priority,
            COUNT(ticket_id) AS total_tickets,
            SUM(CASE 
                WHEN status IN ('RESOLVED', 'CLOSED') AND (resolved_at <= resolution_deadline OR resolution_deadline IS NULL) THEN 1
                WHEN status NOT IN ('RESOLVED', 'CLOSED') AND (NOW() <= resolution_deadline OR resolution_deadline IS NULL) THEN 1
                ELSE 0 
            END) AS compliant_tickets,
            SUM(CASE 
                WHEN status IN ('RESOLVED', 'CLOSED') AND resolved_at > resolution_deadline THEN 1
                WHEN status NOT IN ('RESOLVED', 'CLOSED') AND NOW() > resolution_deadline THEN 1
                ELSE 0 
            END) AS breached_tickets,
            ROUND(
                (SUM(CASE 
                    WHEN (resolved_at IS NOT NULL AND resolved_at <= resolution_deadline)
                         OR (resolved_at IS NULL AND NOW() <= resolution_deadline)
                         OR resolution_deadline IS NULL 
                    THEN 1 ELSE 0 END) / 
                 NULLIF(COUNT(ticket_id), 0)) * 100, 
            1) AS compliance_pct
        FROM tickets
        GROUP BY priority
        ORDER BY FIELD(priority, 'Critical', 'High', 'Medium', 'Low');
        """
        return self.query_mgr.run_query_df(sql)
