"""Department-Wise Analytics & Organizational Health Intelligence.

Member 3: SQL Analytics & Business Intelligence Specialist
Provides operational visibility into ticket load, active backlogs,
most problematic business units, SLA compliance rates, and resolution speed.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from analytics.sql_queries import (
    SQLQueryManager, 
    QUERY_DEPARTMENT_SUMMARY, 
    QUERY_PROBLEMATIC_DEPARTMENTS_HAVING,
    QUERY_CORRELATED_SUBQUERY_LONGER_THAN_DEPT
)

class DepartmentAnalytics:
    """Computes departmental metrics and isolates chronic ticket-generating units."""

    def __init__(self):
        self.query_mgr = SQLQueryManager()

    def get_department_summary(self) -> pd.DataFrame:
        """Retrieves comprehensive operational KPIs across all corporate departments.

        Returns DataFrame containing:
        - department_name
        - total_tickets
        - active_backlog
        - resolved_count
        - critical_count
        - avg_resolution_hours
        - sla_compliance_pct
        - department_health_status
        """
        df = self.query_mgr.run_query_df(QUERY_DEPARTMENT_SUMMARY)
        if df.empty:
            df = self.query_mgr.call_procedure_df("get_department_summary")

        if df.empty:
            from core.database import db
            from core.models import Department, Ticket
            try:
                with db.get_session() as session:
                    depts = session.query(Department).all()
                    data = []
                    for d in depts:
                        d_tickets = d.tickets or []
                        total = len(d_tickets)
                        resolved = sum(1 for t in d_tickets if t.status in ("RESOLVED", "CLOSED"))
                        backlog = total - resolved
                        critical = sum(1 for t in d_tickets if t.priority == "Critical")
                        breached = sum(1 for t in d_tickets if t.is_breached())
                        comp = round(((total - breached) / total * 100), 1) if total > 0 else 100.0
                        durations = [(t.resolved_at - t.created_at).total_seconds() / 3600.0 for t in d_tickets if t.resolved_at and t.created_at]
                        avg_res = round(sum(durations) / len(durations), 2) if durations else 0.0
                        data.append({
                            "department_id": d.department_id,
                            "department_name": d.name,
                            "department_code": d.code,
                            "total_tickets": total,
                            "active_backlog": backlog,
                            "resolved_count": resolved,
                            "critical_count": critical,
                            "avg_resolution_hours": avg_res,
                            "sla_compliance_pct": comp
                        })
                    df = pd.DataFrame(data)
            except Exception:
                df = pd.DataFrame()

        if not df.empty and "department_health_status" not in df.columns:
            def compute_health(row):
                compliance = row.get("sla_compliance_pct")
                if pd.notnull(compliance) and float(compliance) < 75.0:
                    return "At Risk"
                if int(row.get("critical_count", 0)) >= 3:
                    return "Critical Focus"
                if int(row.get("active_backlog", 0)) >= 5:
                    return "High Load"
                return "Healthy"

            df["department_health_status"] = df.apply(compute_health, axis=1)

        return df

    def get_problematic_departments(self, min_tickets: int = 2, min_hours: float = 2.0) -> pd.DataFrame:
        """Identifies departments with high incident volume and prolonged resolution times.

        Executes SQL query using GROUP BY and HAVING clauses.
        """
        return self.query_mgr.run_query_df(
            QUERY_PROBLEMATIC_DEPARTMENTS_HAVING, 
            {"min_count": min_tickets, "min_hours": min_hours}
        )

    def get_tickets_exceeding_dept_average(self) -> pd.DataFrame:
        """Executes Correlated Subquery to find tickets whose resolution took longer

        than the average resolution time for their department.
        """
        return self.query_mgr.run_query_df(QUERY_CORRELATED_SUBQUERY_LONGER_THAN_DEPT)

    def get_department_priority_breakdown(self) -> pd.DataFrame:
        """Breaks down departmental volume by priority level (Critical, High, Medium, Low)."""
        sql = """
        SELECT 
            d.name AS department_name,
            SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_tickets,
            SUM(CASE WHEN t.priority = 'High' THEN 1 ELSE 0 END) AS high_tickets,
            SUM(CASE WHEN t.priority = 'Medium' THEN 1 ELSE 0 END) AS medium_tickets,
            SUM(CASE WHEN t.priority = 'Low' THEN 1 ELSE 0 END) AS low_tickets,
            COUNT(t.ticket_id) AS total_tickets
        FROM departments d
        LEFT JOIN tickets t ON d.department_id = t.department_id
        GROUP BY d.department_id, d.name
        ORDER BY total_tickets DESC;
        """
        return self.query_mgr.run_query_df(sql)
