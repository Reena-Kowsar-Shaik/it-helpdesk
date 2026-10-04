"""Recurring Problem & Reopened Ticket Intelligence Module.

Member 3: SQL Analytics & Business Intelligence Specialist
Isolates chronic technical problem hotspots, analyzes root causes from resolutions,
and performs audit tracking on reopened tickets to detect incomplete fixes.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from analytics.sql_queries import (
    SQLQueryManager, 
    QUERY_RECURRING_PROBLEMS, 
    QUERY_REOPENED_TICKETS_AUDIT
)

class RecurringIssueAnalytics:
    """Analyzes chronic infrastructure problems and resolution defect rates."""

    def __init__(self):
        self.query_mgr = SQLQueryManager()

    def get_top_recurring_categories(self, min_count: int = 1) -> pd.DataFrame:
        """Retrieves incident volume by category to identify systematic problems."""
        df = self.query_mgr.run_query_df(QUERY_RECURRING_PROBLEMS)
        if df.empty:
            df = self.query_mgr.call_procedure_df("get_recurring_issues", [min_count])
        return df

    def get_problem_keyword_frequency(self) -> pd.DataFrame:
        """Categorizes frequent recurring problem themes across ticket titles.

        Uses SQL CASE and LIKE expressions to cluster recurring pain points:
        - Network / VPN
        - Password / Authentication
        - Hardware & Displays
        - Software & Applications
        - Security Incidents
        - Cloud Infrastructure
        """
        sql = """
        SELECT 
            CASE 
                WHEN LOWER(title) LIKE '%vpn%' OR LOWER(title) LIKE '%network%' OR LOWER(title) LIKE '%wi-fi%' OR LOWER(title) LIKE '%dns%' THEN 'Network & VPN'
                WHEN LOWER(title) LIKE '%password%' OR LOWER(title) LIKE '%login%' OR LOWER(title) LIKE '%auth%' OR LOWER(title) LIKE '%token%' OR LOWER(title) LIKE '%mfa%' THEN 'Password & Authentication'
                WHEN LOWER(title) LIKE '%printer%' OR LOWER(title) LIKE '%monitor%' OR LOWER(title) LIKE '%dock%' OR LOWER(title) LIKE '%battery%' OR LOWER(title) LIKE '%laptop%' THEN 'Hardware & Peripherals'
                WHEN LOWER(title) LIKE '%license%' OR LOWER(title) LIKE '%install%' OR LOWER(title) LIKE '%excel%' OR LOWER(title) LIKE '%docker%' THEN 'Software & Applications'
                WHEN LOWER(title) LIKE '%phish%' OR LOWER(title) LIKE '%malware%' OR LOWER(title) LIKE '%security%' OR LOWER(title) LIKE '%ssl%' THEN 'Security & Vulnerabilities'
                ELSE 'Other General Support'
            END AS problem_cluster,
            COUNT(ticket_id) AS incident_count,
            SUM(CASE WHEN priority = 'Critical' THEN 1 ELSE 0 END) AS critical_count,
            ROUND(AVG(
                CASE 
                    WHEN resolved_at IS NOT NULL 
                    THEN TIMESTAMPDIFF(MINUTE, created_at, resolved_at) / 60.0 
                    ELSE NULL 
                END
            ), 2) AS avg_resolution_hours
        FROM tickets
        GROUP BY problem_cluster
        ORDER BY incident_count DESC;
        """
        return self.query_mgr.run_query_df(sql)

    def get_reopened_ticket_analysis(self) -> pd.DataFrame:
        """Extracts reopened tickets, associated categories, departments, and agents."""
        df = self.query_mgr.run_query_df(QUERY_REOPENED_TICKETS_AUDIT)
        if df.empty:
            df = self.query_mgr.call_procedure_df("get_reopened_ticket_analysis")
        return df

    def get_reopened_summary_by_agent(self) -> pd.DataFrame:
        """Correlates reopened incidents with assigned agents to detect incomplete fixes."""
        sql = """
        SELECT 
            COALESCE(sa.full_name, 'Unassigned') AS agent_name,
            COUNT(t.ticket_id) AS total_reopened_tickets,
            SUM(t.reopened_count) AS total_reopen_events,
            ROUND(AVG(t.reopened_count), 1) AS avg_reopen_per_ticket
        FROM tickets t
        LEFT JOIN support_agents sa ON t.assigned_agent_id = sa.agent_id
        WHERE t.reopened_count > 0
        GROUP BY sa.agent_id, sa.full_name
        ORDER BY total_reopen_events DESC;
        """
        return self.query_mgr.run_query_df(sql)

    def get_root_cause_breakdown(self) -> pd.DataFrame:
        """Analyzes documented root causes from the ticket_resolutions table."""
        sql = """
        SELECT 
            resolution_category,
            COUNT(resolution_id) AS resolution_count,
            COUNT(DISTINCT agent_id) AS resolving_agents
        FROM ticket_resolutions
        GROUP BY resolution_category
        ORDER BY resolution_count DESC;
        """
        return self.query_mgr.run_query_df(sql)
