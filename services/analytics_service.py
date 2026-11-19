import pandas as pd
from database.connection import db_manager
from database import queries
from utils.logger import get_logger

logger = get_logger("analytics_service")

class AnalyticsService:
    @staticmethod
    def get_kpi_summary() -> dict:
        """Calculates executive dashboard KPI metrics using SQL aggregation."""
        df = db_manager.fetch_dataframe(queries.QUERY_KPI_SUMMARY)
        if not df.empty:
            return df.iloc[0].to_dict()
        return {
            "total_tickets": 0, "open_tickets": 0, "assigned_tickets": 0,
            "in_progress_tickets": 0, "pending_customer_tickets": 0,
            "resolved_tickets": 0, "reopened_tickets": 0, "active_critical": 0,
            "sla_breached_count": 0, "avg_csat_score": 0.0, "sla_compliance_pct": 100.0
        }

    @staticmethod
    def get_agent_rankings() -> pd.DataFrame:
        """
        Executes SQL CTE + Window Functions (RANK, DENSE_RANK) to score & rank support agents.
        """
        db_type = db_manager.get_db_info()["type"]
        query = queries.QUERY_AGENT_RANKINGS_MYSQL if db_type == "MYSQL" else queries.QUERY_AGENT_RANKINGS
        df = db_manager.fetch_dataframe(query)
        if df.empty:
            # Fallback if window function query has dialect variance
            fallback_sql = """
                SELECT 
                    a.agent_id, u.full_name AS agent_name, st.name AS team_name, a.tier, a.status AS current_status,
                    COUNT(t.ticket_id) AS total_assigned,
                    SUM(CASE WHEN t.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS tickets_resolved,
                    SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS active_tickets,
                    SUM(CASE WHEN t.sla_breached = 1 THEN 1 ELSE 0 END) AS breached_tickets,
                    SUM(CASE WHEN t.reopen_count > 0 THEN 1 ELSE 0 END) AS reopened_tickets,
                    ROUND(AVG(t.satisfaction_rating), 2) AS avg_csat,
                    ROUND((SUM(CASE WHEN t.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) * 100.0) / NULLIF(COUNT(t.ticket_id), 0), 1) AS resolution_rate_pct,
                    ROUND(((SUM(CASE WHEN t.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) - SUM(CASE WHEN t.sla_breached = 1 THEN 1 ELSE 0 END)) * 100.0) / NULLIF(SUM(CASE WHEN t.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END), 0), 1) AS sla_compliance_pct
                FROM agents a
                JOIN users u ON a.user_id = u.user_id
                LEFT JOIN support_teams st ON a.team_id = st.team_id
                LEFT JOIN tickets t ON a.agent_id = t.assigned_agent_id
                GROUP BY a.agent_id, u.full_name, st.name, a.tier, a.status
                ORDER BY tickets_resolved DESC;
            """
            df = db_manager.fetch_dataframe(fallback_sql)
            if not df.empty:
                df["performance_rank"] = df["tickets_resolved"].rank(ascending=False, method="min").astype(int)
        return df

    @staticmethod
    def get_department_load() -> pd.DataFrame:
        """Analyzes department-wise ticket demand and company share."""
        return db_manager.fetch_dataframe(queries.QUERY_DEPARTMENT_LOAD)

    @staticmethod
    def get_recurring_problems() -> pd.DataFrame:
        """Analyzes recurring IT incident categories and severity."""
        return db_manager.fetch_dataframe(queries.QUERY_RECURRING_PROBLEMS)

    @staticmethod
    def get_team_workload() -> pd.DataFrame:
        """Identifies overloaded teams and capacity bottlenecks."""
        return db_manager.fetch_dataframe(queries.QUERY_TEAM_WORKLOAD)

    @staticmethod
    def get_sla_compliance_breakdown() -> pd.DataFrame:
        """Returns SLA compliance and breach statistics per priority tier."""
        return db_manager.fetch_dataframe(queries.QUERY_SLA_ANALYSIS)

    @staticmethod
    def get_reopened_tickets() -> pd.DataFrame:
        """Fetches reopened tickets with resolution defect analysis."""
        return db_manager.fetch_dataframe(queries.QUERY_REOPENED_ANALYSIS)

    @staticmethod
    def get_monthly_trends() -> pd.DataFrame:
        """Calculates month-over-month ticket volume, resolution rates, and breaches."""
        sql = """
            SELECT 
                SUBSTR(created_at, 1, 7) AS month_year,
                COUNT(*) AS total_created,
                SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS total_resolved,
                SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END) AS sla_breaches,
                SUM(CASE WHEN reopen_count > 0 THEN 1 ELSE 0 END) AS total_reopens,
                ROUND(AVG(CASE WHEN satisfaction_rating IS NOT NULL THEN satisfaction_rating END), 2) AS monthly_csat
            FROM tickets
            GROUP BY SUBSTR(created_at, 1, 7)
            ORDER BY month_year ASC;
        """
        return db_manager.fetch_dataframe(sql)

    @staticmethod
    def execute_custom_query(sql_query: str) -> pd.DataFrame:
        """Executes arbitrary user SQL query for the SQL Explorer tool."""
        return db_manager.fetch_dataframe(sql_query)
