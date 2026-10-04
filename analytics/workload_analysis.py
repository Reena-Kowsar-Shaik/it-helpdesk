"""Support Agent & Team Workload Intelligence Module.

Member 3: SQL Analytics & Business Intelligence Specialist
Provides real-time visibility into open ticket volumes, identifies
overloaded personnel, and balances queue assignments using CTEs and SQL aggregation.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from analytics.sql_queries import SQLQueryManager, QUERY_WORKLOAD_ANALYSIS_CTE

class WorkloadAnalytics:
    """Calculates operational workload, backlog density, and capacity thresholds."""

    def __init__(self):
        self.query_mgr = SQLQueryManager()

    def get_agent_workload(self) -> pd.DataFrame:
        """Retrieves active ticket load per agent categorized by capacity state.

        Categories:
        - Overloaded (>= 10 active tickets)
        - Moderate (5 to 9 active tickets)
        - Optimal (< 5 active tickets)
        """
        df = self.query_mgr.run_query_df(QUERY_WORKLOAD_ANALYSIS_CTE)
        if df.empty:
            df = self.query_mgr.call_procedure_df("get_workload_analysis")

        if not df.empty and "workload_status" not in df.columns:
            def calc_status(row):
                cnt = int(row.get("open_ticket_count", 0) or row.get("active_tickets", 0))
                if cnt >= 10:
                    return "Overloaded"
                elif cnt >= 5:
                    return "Moderate"
                return "Optimal"
            df["workload_status"] = df.apply(calc_status, axis=1)

        return df

    def get_team_workload_distribution(self) -> pd.DataFrame:
        """Aggregates workload across functional support teams."""
        sql = """
        SELECT 
            st.team_id,
            st.name AS team_name,
            COUNT(DISTINCT sa.agent_id) AS total_agents,
            COUNT(t.ticket_id) AS active_tickets,
            SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_load,
            SUM(CASE WHEN t.priority = 'High' THEN 1 ELSE 0 END) AS high_load,
            ROUND(COUNT(t.ticket_id) / NULLIF(COUNT(DISTINCT sa.agent_id), 0), 1) AS tickets_per_agent
        FROM support_teams st
        LEFT JOIN support_agents sa ON st.team_id = sa.team_id
        LEFT JOIN tickets t ON sa.agent_id = t.assigned_agent_id 
            AND t.status IN ('OPEN', 'ASSIGNED', 'IN PROGRESS', 'REOPENED')
        GROUP BY st.team_id, st.name
        ORDER BY active_tickets DESC;
        """
        return self.query_mgr.run_query_df(sql)

    def get_unassigned_tickets_queue(self) -> pd.DataFrame:
        """Extracts tickets currently sitting in the unassigned backlog."""
        sql = """
        SELECT 
            t.ticket_id,
            t.ticket_number,
            t.title,
            d.name AS department_name,
            c.name AS category_name,
            t.priority,
            t.status,
            t.created_at,
            TIMESTAMPDIFF(MINUTE, t.created_at, NOW()) AS waiting_minutes
        FROM tickets t
        JOIN departments d ON t.department_id = d.department_id
        JOIN categories c ON t.category_id = c.category_id
        WHERE t.assigned_agent_id IS NULL
          AND t.status IN ('OPEN', 'REOPENED')
        ORDER BY FIELD(t.priority, 'Critical', 'High', 'Medium', 'Low'), t.created_at ASC;
        """
        return self.query_mgr.run_query_df(sql)
