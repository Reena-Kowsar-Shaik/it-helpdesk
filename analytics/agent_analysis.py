"""Agent Performance & Ranking Intelligence Module.

Member 3: SQL Analytics & Business Intelligence Specialist
Computes assigned, resolved, active backlog, average resolution times,
SLA compliance percentages, reopened ticket metrics, and competitive rankings.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from analytics.sql_queries import SQLQueryManager, QUERY_AGENT_PERFORMANCE_WINDOW

class AgentAnalytics:
    """Provides SQL-backed analytical insights on support agent efficiency."""

    def __init__(self):
        self.query_mgr = SQLQueryManager()

    def get_agent_leaderboard(self) -> pd.DataFrame:
        """Retrieves agent performance rankings powered by SQL Window Functions (DENSE_RANK).

        Returns:
            DataFrame containing ranks, agent names, assigned, resolved, active queue,
            average resolution hours, and SLA compliance percentages.
        """
        df = self.query_mgr.run_query_df(QUERY_AGENT_PERFORMANCE_WINDOW)
        if df.empty:
            # Fallback to stored procedure or view
            df = self.query_mgr.call_procedure_df("get_agent_performance", [0])

        if not df.empty:
            # Normalize column names if needed
            rename_map = {
                "performance_rank": "Rank",
                "agent_name": "Agent Name",
                "team_name": "Team",
                "total_assigned": "Assigned",
                "total_assigned_tickets": "Assigned",
                "resolved_count": "Resolved",
                "resolved_tickets": "Resolved",
                "active_queue": "Active Queue",
                "active_tickets": "Active Queue",
                "avg_res_hours": "Avg Resolution (hrs)",
                "avg_resolution_hours": "Avg Resolution (hrs)",
                "sla_compliance_pct": "SLA Compliance %",
                "total_reopened": "Reopened Count",
                "total_reopened_count": "Reopened Count"
            }
            df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
            
            # Format SLA Compliance
            if "SLA Compliance %" in df.columns:
                df["SLA Compliance %"] = df["SLA Compliance %"].apply(
                    lambda x: f"{float(x):.1f}%" if pd.notnull(x) else "N/A"
                )
        return df

    def get_agent_detail_kpis(self, agent_id: int) -> Dict[str, Any]:
        """Fetches individual scorecard metrics for a specific agent."""
        df = self.query_mgr.call_procedure_df("get_agent_performance", [agent_id])
        if df.empty:
            return {}
        row = df.iloc[0].to_dict()
        return {
            "agent_id": row.get("agent_id"),
            "agent_name": row.get("agent_name"),
            "team_name": row.get("team_name"),
            "total_assigned": int(row.get("total_assigned_tickets", 0)),
            "resolved_tickets": int(row.get("resolved_tickets", 0)),
            "active_tickets": int(row.get("active_tickets", 0)),
            "avg_resolution_hours": float(row.get("avg_resolution_hours", 0.0) or 0.0),
            "sla_compliance_pct": float(row.get("sla_compliance_pct", 0.0) or 0.0),
            "reopened_count": int(row.get("total_reopened_count", 0)),
            "rank": int(row.get("performance_rank", 1))
        }

    def get_agent_resolution_comparison(self) -> pd.DataFrame:
        """Compares agent average resolution speed against team & organization benchmarks."""
        sql = """
        SELECT 
            sa.full_name AS agent_name,
            ROUND(AVG(TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0), 2) AS agent_avg_hours,
            ROUND((
                SELECT AVG(TIMESTAMPDIFF(MINUTE, t_all.created_at, t_all.resolved_at) / 60.0)
                FROM tickets t_all
                WHERE t_all.resolved_at IS NOT NULL
            ), 2) AS org_avg_hours
        FROM support_agents sa
        JOIN tickets t ON sa.agent_id = t.assigned_agent_id
        WHERE t.resolved_at IS NOT NULL
        GROUP BY sa.agent_id, sa.full_name
        ORDER BY agent_avg_hours ASC;
        """
        return self.query_mgr.run_query_df(sql)
