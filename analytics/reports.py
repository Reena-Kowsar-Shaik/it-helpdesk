"""Enterprise Report Generation Engine (PDF & CSV).

Member 3: SQL Analytics & Business Intelligence Specialist
Generates executive PDF summaries and data exports for:
1. Monthly Ticket Summary Report
2. Agent Performance Leaderboard Report
3. Department Operational Health Report
4. SLA Compliance & Breach Incident Report
5. Recurring Technical Issues & Root Cause Report
"""

import io
from datetime import datetime
import pandas as pd
from typing import Dict, Any, List, Optional
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from analytics.agent_analysis import AgentAnalytics
from analytics.department_analysis import DepartmentAnalytics
from analytics.sla_analysis import SLAAnalytics
from analytics.workload_analysis import WorkloadAnalytics
from analytics.recurring_issues import RecurringIssueAnalytics

class HelpdeskPDFReport(FPDF):
    """Custom styled PDF document for enterprise reporting."""

    def __init__(self, report_title: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.report_title = report_title
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Header banner
        self.set_fill_color(30, 41, 59)  # Dark slate #1E293B
        self.rect(0, 0, 210, 24, "F")

        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 6)
        self.cell(0, 8, "IT HELPDESK & TICKET INTELLIGENCE", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font("Helvetica", "", 9)
        self.set_text_color(203, 213, 225)
        self.set_xy(10, 14)
        self.cell(0, 5, f"Report: {self.report_title}  |  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(12)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}  |  Confidential & Internal Operations", align="C")

    def chapter_title(self, label: str):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(79, 70, 229)  # Indigo
        self.cell(0, 8, label, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(226, 232, 240)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def render_table(self, df: pd.DataFrame, col_widths: List[float], max_rows: int = 15):
        if df.empty:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(100, 116, 139)
            self.cell(0, 8, "No records found.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            return

        # Header
        self.set_fill_color(241, 245, 249)
        self.set_text_color(15, 23, 42)
        self.set_font("Helvetica", "B", 8)
        
        cols = list(df.columns)
        for i, col in enumerate(cols):
            w = col_widths[i] if i < len(col_widths) else 25
            self.cell(w, 7, str(col)[:18], border=1, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("Helvetica", "", 8)
        self.set_text_color(51, 65, 85)
        for idx, row in df.head(max_rows).iterrows():
            fill = (idx % 2 == 1)
            if fill:
                self.set_fill_color(248, 250, 252)
            else:
                self.set_fill_color(255, 255, 255)

            for i, col in enumerate(cols):
                w = col_widths[i] if i < len(col_widths) else 25
                val = str(row[col]) if pd.notnull(row[col]) else "-"
                self.cell(w, 6, val[:22], border=1, fill=True, align="L" if i < 2 else "C")
            self.ln()
        self.ln(4)


class ReportGenerator:
    """Orchestrates CSV and PDF reporting pipelines."""

    def __init__(self):
        self.agent_analytics = AgentAnalytics()
        self.dept_analytics = DepartmentAnalytics()
        self.sla_analytics = SLAAnalytics()
        self.workload_analytics = WorkloadAnalytics()
        self.recurring_analytics = RecurringIssueAnalytics()

    # ==========================================================
    # CSV GENERATORS
    # ==========================================================
    def get_agent_performance_csv(self) -> str:
        """Returns CSV text for agent ranking leaderboard."""
        df = self.agent_analytics.get_agent_leaderboard()
        return df.to_csv(index=False)

    def get_department_summary_csv(self) -> str:
        """Returns CSV text for department operational statistics."""
        df = self.dept_analytics.get_department_summary()
        return df.to_csv(index=False)

    def get_sla_breaches_csv(self) -> str:
        """Returns CSV text for SLA breach incident register."""
        df = self.sla_analytics.get_breached_tickets_list()
        return df.to_csv(index=False)

    def get_workload_csv(self) -> str:
        """Returns CSV text for active agent workload distribution."""
        df = self.workload_analytics.get_agent_workload()
        return df.to_csv(index=False)

    def get_recurring_issues_csv(self) -> str:
        """Returns CSV text for recurring technical issues."""
        df = self.recurring_analytics.get_top_recurring_categories()
        return df.to_csv(index=False)

    # ==========================================================
    # PDF EXECUTIVE REPORTS
    # ==========================================================
    def generate_executive_bi_pdf(self) -> bytes:
        """Generates a comprehensive multi-section Business Intelligence PDF report."""
        pdf = HelpdeskPDFReport("Executive Business Intelligence & SLA Audit")
        pdf.alias_nb_pages()
        pdf.add_page()

        # 1. Executive Summary KPIs
        pdf.chapter_title("1. System Operational Health & SLA Scorecard")
        sla_kpis = self.sla_analytics.get_sla_kpi_summary()
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(238, 242, 255)
        pdf.rect(10, pdf.get_y(), 190, 20, "F")
        pdf.set_xy(12, pdf.get_y() + 3)
        pdf.set_text_color(67, 56, 202)
        pdf.cell(45, 6, f"Total Tracked: {sla_kpis['total_tracked_tickets']}")
        pdf.cell(45, 6, f"Resolved: {sla_kpis['total_resolved']}")
        pdf.cell(50, 6, f"SLA Compliance: {sla_kpis['compliance_pct']}%")
        pdf.cell(45, 6, f"Active Breaches: {sla_kpis['breached_count']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_xy(12, pdf.get_y() + 2)
        pdf.set_text_color(100, 116, 139)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(60, 6, f"Avg Response: {sla_kpis['avg_response_minutes']} mins")
        pdf.cell(65, 6, f"Avg Resolution: {sla_kpis['avg_resolution_hours']} hrs")
        pdf.cell(60, 6, f"At-Risk (<1h): {sla_kpis['at_risk_count']}")
        pdf.ln(12)

        # 2. Agent Performance Leaderboard
        pdf.chapter_title("2. Support Agent Performance Leaderboard (SQL DENSE_RANK)")
        df_agents = self.agent_analytics.get_agent_leaderboard()
        if not df_agents.empty:
            cols = ["Rank", "Agent Name", "Team", "Assigned", "Resolved", "Active Queue", "Avg Resolution (hrs)", "SLA Compliance %"]
            avail_cols = [c for c in cols if c in df_agents.columns]
            widths = [15, 35, 30, 20, 20, 25, 25, 20]
            pdf.render_table(df_agents[avail_cols], widths[:len(avail_cols)])

        # 3. Department Health
        pdf.chapter_title("3. Department Volume & Resolution Velocity")
        df_dept = self.dept_analytics.get_department_summary()
        if not df_dept.empty:
            dept_cols = ["department_name", "total_tickets", "active_backlog", "resolved_count", "avg_resolution_hours", "sla_compliance_pct"]
            avail_dept = [c for c in dept_cols if c in df_dept.columns]
            widths_d = [45, 25, 25, 25, 35, 35]
            pdf.render_table(df_dept[avail_dept], widths_d[:len(avail_dept)])

        # New Page for Risk and Recurring
        pdf.add_page()

        # 4. Workload Capacity
        pdf.chapter_title("4. Workload Capacity & Queue Distribution")
        df_workload = self.workload_analytics.get_agent_workload()
        if not df_workload.empty:
            w_cols = ["agent_name", "team_name", "active_tickets", "critical_load", "high_load", "workload_status"]
            avail_w = [c for c in w_cols if c in df_workload.columns]
            widths_w = [40, 35, 25, 25, 25, 40]
            pdf.render_table(df_workload[avail_w], widths_w[:len(avail_w)])

        # 5. SLA Breaches Register
        pdf.chapter_title("5. SLA Deadline Breach Incident Log")
        df_breaches = self.sla_analytics.get_breached_tickets_list()
        if not df_breaches.empty:
            b_cols = ["ticket_number", "title", "department_name", "priority", "assigned_agent", "sla_status"]
            avail_b = [c for c in b_cols if c in df_breaches.columns]
            widths_b = [28, 55, 30, 20, 30, 27]
            pdf.render_table(df_breaches[avail_b], widths_b[:len(avail_b)])
        else:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 8, "No active SLA breaches recorded.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # 6. Recurring Issues
        pdf.chapter_title("6. Recurring Technical Problems & Hotspots")
        df_recur = self.recurring_analytics.get_top_recurring_categories()
        if not df_recur.empty:
            r_cols = ["category_name", "total_occurrences", "critical_count", "high_count", "total_reopenings", "avg_resolution_hours"]
            avail_r = [c for c in r_cols if c in df_recur.columns]
            widths_r = [45, 28, 28, 28, 30, 31]
            pdf.render_table(df_recur[avail_r], widths_r[:len(avail_r)])

        # Output bytes
        return bytes(pdf.output())
