"""Centralized SQL Query Catalog & Database Execution Engine.

Member 3: SQL Analytics & Business Intelligence Specialist
Provides structured access to advanced SQL queries (CTEs, Window Functions,
Correlated Subqueries, HAVING clauses, Stored Procedures, and Views).
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from core.database import db
from core.logger import logger, log_error

class SQLQueryManager:
    """Executes analytical SQL statements, stored procedures, and views."""

    @staticmethod
    def run_query(sql_statement: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Executes a raw SQL SELECT query and returns rows as dictionaries."""
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text(sql_statement), params or {})
                return [dict(row) for row in result.mappings().all()]
        except Exception as e:
            log_error(f"SQLQueryManager execution error: {sql_statement[:80]}...", e)
            logger.warning(f"Falling back or returning empty result on error: {str(e)}")
            return []

    @staticmethod
    def run_query_df(sql_statement: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Executes an SQL query and returns results directly as a Pandas DataFrame."""
        try:
            with db.engine.connect() as conn:
                df = pd.read_sql_query(text(sql_statement), conn, params=params or {})
                return df
        except Exception as e:
            log_error("Failed to execute query to DataFrame", e)
            return pd.DataFrame()

    @staticmethod
    def call_procedure_df(procedure_name: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
        """Calls a MySQL Stored Procedure and returns the first resultset as a DataFrame."""
        try:
            # If MySQL connection via raw DBAPI cursor
            raw_conn = db.engine.raw_connection()
            try:
                cursor = raw_conn.cursor(dictionary=True)
                cursor.callproc(procedure_name, params or [])
                # Read stored results
                for res in getattr(cursor, 'stored_results', lambda: [])():
                    rows = res.fetchall()
                    return pd.DataFrame(rows)
                return pd.DataFrame()
            finally:
                raw_conn.close()
        except Exception as e:
            logger.warning(f"Stored procedure {procedure_name} call via raw cursor failed: {e}. Attempting standard query fallback.")
            # Fallback to direct view query based on procedure name
            fallback_map = {
                "get_department_summary": "SELECT * FROM department_ticket_view ORDER BY total_tickets DESC",
                "get_agent_performance": "SELECT * FROM agent_performance_view ORDER BY resolved_tickets DESC",
                "get_sla_breaches": "SELECT * FROM sla_breach_view WHERE sla_status IN ('Resolved Past SLA', 'Currently Breached') ORDER BY breach_minutes DESC",
                "get_workload_analysis": "SELECT * FROM open_ticket_workload_view ORDER BY open_ticket_count DESC",
                "get_monthly_ticket_report": "SELECT * FROM monthly_ticket_summary_view ORDER BY ticket_month DESC, ticket_count DESC",
                "get_recurring_issues": "SELECT * FROM recurring_issue_view ORDER BY occurrence_count DESC",
                "get_reopened_ticket_analysis": "SELECT * FROM reopened_ticket_view ORDER BY reopened_count DESC"
            }
            if procedure_name in fallback_map:
                return SQLQueryManager.run_query_df(fallback_map[procedure_name])
            return pd.DataFrame()


# ==========================================================
# SQL QUERY CATALOG
# ==========================================================

# 1. Department Summary & Health
QUERY_DEPARTMENT_SUMMARY = """
SELECT 
    d.department_id,
    d.name AS department_name,
    d.code AS department_code,
    COUNT(t.ticket_id) AS total_tickets,
    SUM(CASE WHEN t.status IN ('OPEN', 'ASSIGNED', 'IN PROGRESS', 'REOPENED') THEN 1 ELSE 0 END) AS active_backlog,
    SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) AS resolved_count,
    SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_count,
    ROUND(AVG(
        CASE 
            WHEN t.resolved_at IS NOT NULL 
            THEN TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0 
            ELSE NULL 
        END
    ), 2) AS avg_resolution_hours,
    ROUND(
        (SUM(CASE 
            WHEN (t.resolved_at IS NOT NULL AND t.resolved_at <= t.resolution_deadline)
                 OR (t.resolved_at IS NULL AND NOW() <= t.resolution_deadline)
                 OR t.resolution_deadline IS NULL 
            THEN 1 ELSE 0 END) / 
         NULLIF(COUNT(t.ticket_id), 0)
        ) * 100, 
    1) AS sla_compliance_pct
FROM departments d
LEFT JOIN tickets t ON d.department_id = t.department_id
GROUP BY d.department_id, d.name, d.code
ORDER BY total_tickets DESC;
"""

# 2. GROUP BY & HAVING - Identify Problematic Departments
QUERY_PROBLEMATIC_DEPARTMENTS_HAVING = """
SELECT 
    d.name AS department_name,
    d.code AS department_code,
    COUNT(t.ticket_id) AS total_incidents,
    ROUND(AVG(TIMESTAMPDIFF(MINUTE, t.created_at, COALESCE(t.resolved_at, NOW())) / 60.0), 2) AS avg_duration_hours,
    SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_incidents,
    ROUND(
        (SUM(CASE WHEN t.resolved_at > t.resolution_deadline OR (t.resolved_at IS NULL AND NOW() > t.resolution_deadline) THEN 1 ELSE 0 END) / 
         NULLIF(COUNT(t.ticket_id), 0)) * 100, 1
    ) AS breach_rate_pct
FROM departments d
JOIN tickets t ON d.department_id = t.department_id
GROUP BY d.department_id, d.name, d.code
HAVING COUNT(t.ticket_id) >= :min_count 
   AND avg_duration_hours > :min_hours
ORDER BY avg_duration_hours DESC;
"""

# 3. Window Function - Agent Performance Leaderboard with DENSE_RANK
QUERY_AGENT_PERFORMANCE_WINDOW = """
SELECT 
    sa.agent_id,
    sa.full_name AS agent_name,
    COALESCE(st.name, 'General Support') AS team_name,
    COUNT(t.ticket_id) AS total_assigned,
    SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) AS resolved_count,
    SUM(CASE WHEN t.status IN ('OPEN', 'ASSIGNED', 'IN PROGRESS', 'REOPENED') THEN 1 ELSE 0 END) AS active_queue,
    ROUND(AVG(
        CASE 
            WHEN t.resolved_at IS NOT NULL 
            THEN TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0 
            ELSE NULL 
        END
    ), 2) AS avg_res_hours,
    ROUND(
        (SUM(CASE 
            WHEN t.status IN ('RESOLVED', 'CLOSED') 
                 AND (t.resolved_at <= t.resolution_deadline OR t.resolution_deadline IS NULL) 
            THEN 1 ELSE 0 END) / 
         NULLIF(SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END), 0)
        ) * 100, 
    1) AS sla_compliance_pct,
    COALESCE(SUM(t.reopened_count), 0) AS total_reopened,
    DENSE_RANK() OVER (
        ORDER BY 
            SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) DESC,
            ROUND(
                (SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') AND (t.resolved_at <= t.resolution_deadline OR t.resolution_deadline IS NULL) THEN 1 ELSE 0 END) / 
                 NULLIF(SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END), 0)) * 100, 1) DESC
    ) AS performance_rank
FROM support_agents sa
LEFT JOIN support_teams st ON sa.team_id = st.team_id
LEFT JOIN tickets t ON sa.agent_id = t.assigned_agent_id
GROUP BY sa.agent_id, sa.full_name, st.name
ORDER BY performance_rank;
"""

# 4. Multi-Stage CTE - Workload Analysis vs Team Benchmarks
QUERY_WORKLOAD_ANALYSIS_CTE = """
WITH AgentWorkloadCTE AS (
    SELECT 
        sa.agent_id,
        sa.full_name AS agent_name,
        sa.team_id,
        COUNT(t.ticket_id) AS active_tickets,
        SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_load,
        SUM(CASE WHEN t.priority = 'High' THEN 1 ELSE 0 END) AS high_load
    FROM support_agents sa
    LEFT JOIN tickets t ON sa.agent_id = t.assigned_agent_id 
        AND t.status IN ('OPEN', 'ASSIGNED', 'IN PROGRESS', 'REOPENED')
    GROUP BY sa.agent_id, sa.full_name, sa.team_id
),
TeamAverageCTE AS (
    SELECT 
        team_id,
        ROUND(AVG(active_tickets), 1) AS team_avg_active
    FROM AgentWorkloadCTE
    GROUP BY team_id
)
SELECT 
    aw.agent_id,
    aw.agent_name,
    COALESCE(st.name, 'General Support') AS team_name,
    aw.active_tickets,
    aw.critical_load,
    aw.high_load,
    ta.team_avg_active,
    CASE 
        WHEN aw.active_tickets >= 10 THEN 'Overloaded'
        WHEN aw.active_tickets >= 5 THEN 'Moderate'
        ELSE 'Optimal'
    END AS workload_status
FROM AgentWorkloadCTE aw
LEFT JOIN support_teams st ON aw.team_id = st.team_id
LEFT JOIN TeamAverageCTE ta ON aw.team_id = ta.team_id
ORDER BY aw.active_tickets DESC;
"""

# 5. Correlated Subquery - Tickets taking longer than Department Average
QUERY_CORRELATED_SUBQUERY_LONGER_THAN_DEPT = """
SELECT 
    t.ticket_id,
    t.ticket_number,
    t.title,
    d.name AS department_name,
    ROUND(TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0, 2) AS ticket_resolution_hours,
    ROUND((
        SELECT AVG(TIMESTAMPDIFF(MINUTE, t_inner.created_at, t_inner.resolved_at) / 60.0)
        FROM tickets t_inner
        WHERE t_inner.department_id = t.department_id 
          AND t_inner.resolved_at IS NOT NULL
    ), 2) AS dept_avg_resolution_hours
FROM tickets t
JOIN departments d ON t.department_id = d.department_id
WHERE t.resolved_at IS NOT NULL
  AND (TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0) > (
      SELECT AVG(TIMESTAMPDIFF(MINUTE, t_sub.created_at, t_sub.resolved_at) / 60.0)
      FROM tickets t_sub
      WHERE t_sub.department_id = t.department_id 
        AND t_sub.resolved_at IS NOT NULL
  )
ORDER BY (ticket_resolution_hours - dept_avg_resolution_hours) DESC;
"""

# 6. Cumulative Monthly Ticket Trend with Window Function
QUERY_MONTHLY_CUMULATIVE_WINDOW = """
WITH MonthlyTotals AS (
    SELECT 
        DATE_FORMAT(created_at, '%Y-%m') AS report_month,
        COUNT(ticket_id) AS monthly_count,
        SUM(CASE WHEN status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) AS monthly_resolved
    FROM tickets
    GROUP BY DATE_FORMAT(created_at, '%Y-%m')
)
SELECT 
    report_month,
    monthly_count,
    monthly_resolved,
    SUM(monthly_count) OVER (ORDER BY report_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_tickets,
    ROUND((monthly_resolved * 100.0) / NULLIF(monthly_count, 0), 1) AS resolution_rate_pct
FROM MonthlyTotals
ORDER BY report_month ASC;
"""

# 7. Recurring Problems & Root Cause Categorization
QUERY_RECURRING_PROBLEMS = """
SELECT 
    c.category_id,
    c.name AS category_name,
    COUNT(t.ticket_id) AS total_occurrences,
    SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_count,
    SUM(CASE WHEN t.priority = 'High' THEN 1 ELSE 0 END) AS high_count,
    SUM(t.reopened_count) AS total_reopenings,
    ROUND(AVG(
        CASE 
            WHEN t.resolved_at IS NOT NULL 
            THEN TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0 
            ELSE NULL 
        END
    ), 2) AS avg_resolution_hours
FROM categories c
LEFT JOIN tickets t ON c.category_id = t.category_id
GROUP BY c.category_id, c.name
ORDER BY total_occurrences DESC;
"""

# 8. Reopened Tickets Audit
QUERY_REOPENED_TICKETS_AUDIT = """
SELECT 
    t.ticket_id,
    t.ticket_number,
    t.title,
    c.name AS category_name,
    d.name AS department_name,
    COALESCE(sa.full_name, 'Unassigned') AS assigned_agent,
    t.reopened_count,
    t.status AS current_status,
    t.created_at,
    t.resolved_at,
    TIMESTAMPDIFF(HOUR, t.created_at, COALESCE(t.resolved_at, NOW())) AS total_lifecycle_hours
FROM tickets t
JOIN categories c ON t.category_id = c.category_id
JOIN departments d ON t.department_id = d.department_id
LEFT JOIN support_agents sa ON t.assigned_agent_id = sa.agent_id
WHERE t.reopened_count > 0
ORDER BY t.reopened_count DESC, total_lifecycle_hours DESC;
"""

# 9. SLA Breach Drilldown
QUERY_SLA_BREACH_DRILLDOWN = """
SELECT 
    t.ticket_id,
    t.ticket_number,
    t.title,
    t.priority,
    t.status,
    d.name AS department_name,
    COALESCE(sa.full_name, 'Unassigned') AS assigned_agent,
    t.created_at,
    t.resolution_deadline,
    t.resolved_at,
    CASE 
        WHEN t.status IN ('RESOLVED', 'CLOSED') AND t.resolved_at > t.resolution_deadline THEN 'Resolved Past SLA'
        WHEN t.status NOT IN ('RESOLVED', 'CLOSED') AND NOW() > t.resolution_deadline THEN 'Currently Breached'
        WHEN t.status NOT IN ('RESOLVED', 'CLOSED') AND TIMESTAMPDIFF(MINUTE, NOW(), t.resolution_deadline) BETWEEN 0 AND 60 THEN 'At Risk (<1 hr)'
        ELSE 'Within SLA'
    END AS sla_status,
    TIMESTAMPDIFF(MINUTE, t.resolution_deadline, COALESCE(t.resolved_at, NOW())) AS breach_minutes
FROM tickets t
JOIN departments d ON t.department_id = d.department_id
LEFT JOIN support_agents sa ON t.assigned_agent_id = sa.agent_id
WHERE t.resolution_deadline IS NOT NULL
ORDER BY breach_minutes DESC;
"""
