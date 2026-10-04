"""Analytics Package Initialization.

Member 3: SQL Analytics, Reports & Performance Intelligence
Exports analytics modules for department health, agent ranking,
SLA tracking, workload management, recurring problems, and report generation.
"""

from analytics.sql_queries import SQLQueryManager
from analytics.agent_analysis import AgentAnalytics
from analytics.department_analysis import DepartmentAnalytics
from analytics.sla_analysis import SLAAnalytics
from analytics.workload_analysis import WorkloadAnalytics
from analytics.recurring_issues import RecurringIssueAnalytics
from analytics.reports import ReportGenerator

__all__ = [
    "SQLQueryManager",
    "AgentAnalytics",
    "DepartmentAnalytics",
    "SLAAnalytics",
    "WorkloadAnalytics",
    "RecurringIssueAnalytics",
    "ReportGenerator",
]
