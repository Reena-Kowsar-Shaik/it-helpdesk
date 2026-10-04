"""SLA Compliance, Deadline Breach & Risk Intelligence Module.

Member 3: SQL Analytics & Business Intelligence Specialist
Provides analysis of response SLAs, resolution SLAs, deadlines,
imminent breach risks, and priority-tier compliance tracking.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from analytics.sql_queries import SQLQueryManager, QUERY_SLA_BREACH_DRILLDOWN

class SLAAnalytics:
    """Monitors SLA targets, breaches, and performance deadlines across the organization."""

    def __init__(self):
        self.query_mgr = SQLQueryManager()

    def get_sla_kpi_summary(self) -> Dict[str, Any]:
        """Calculates global SLA compliance statistics using aggregate SQL expressions."""
        sql = """
        SELECT 
            COUNT(ticket_id) AS total_tracked_tickets,
            SUM(CASE WHEN status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) AS total_resolved,
            SUM(CASE 
                WHEN status IN ('RESOLVED', 'CLOSED') AND (resolved_at <= resolution_deadline OR resolution_deadline IS NULL) THEN 1
                WHEN status NOT IN ('RESOLVED', 'CLOSED') AND (NOW() <= resolution_deadline OR resolution_deadline IS NULL) THEN 1
                ELSE 0 
            END) AS compliant_count,
            SUM(CASE 
                WHEN status IN ('RESOLVED', 'CLOSED') AND resolved_at > resolution_deadline THEN 1
                WHEN status NOT IN ('RESOLVED', 'CLOSED') AND NOW() > resolution_deadline THEN 1
                ELSE 0 
            END) AS breached_count,
            SUM(CASE 
                WHEN status NOT IN ('RESOLVED', 'CLOSED') 
                     AND TIMESTAMPDIFF(MINUTE, NOW(), resolution_deadline) BETWEEN 0 AND 60 
                THEN 1 ELSE 0 
            END) AS at_risk_count,
            ROUND(AVG(
                CASE 
                    WHEN first_responded_at IS NOT NULL 
                    THEN TIMESTAMPDIFF(MINUTE, created_at, first_responded_at) 
                    ELSE NULL 
                END
            ), 1) AS avg_response_minutes,
            ROUND(AVG(
                CASE 
                    WHEN resolved_at IS NOT NULL 
                    THEN TIMESTAMPDIFF(MINUTE, created_at, resolved_at) / 60.0 
                    ELSE NULL 
                END
            ), 2) AS avg_resolution_hours
        FROM tickets;
        """
        rows = self.query_mgr.run_query(sql)
        if not rows:
            return {
                "total_tracked_tickets": 0, "compliant_count": 0, "breached_count": 0,
                "at_risk_count": 0, "compliance_pct": 100.0, "avg_response_minutes": 0, "avg_resolution_hours": 0.0
            }
        r = rows[0]
        total = int(r.get("total_tracked_tickets") or 0)
        breached = int(r.get("breached_count") or 0)
        compliant = int(r.get("compliant_count") or 0)
        compliance_pct = round(((total - breached) / total * 100.0), 1) if total > 0 else 100.0

        return {
            "total_tracked_tickets": total,
            "total_resolved": int(r.get("total_resolved") or 0),
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

        if not df.empty:
            # Filter specifically for breached statuses
            df = df[df["sla_status"].isin(["Resolved Past SLA", "Currently Breached"])]
            if "breach_minutes" in df.columns:
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
