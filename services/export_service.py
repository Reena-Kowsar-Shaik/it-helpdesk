import io
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from services.analytics_service import AnalyticsService
from database.connection import db_manager

class ExportService:
    @staticmethod
    def generate_excel_report() -> bytes:
        """Generates a professional multi-sheet Excel report with styling."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book

            # Styles
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#1E293B',
                'font_color': '#FFFFFF',
                'border': 1
            })

            # Sheet 1: Executive KPI Summary
            kpi_data = AnalyticsService.get_kpi_summary()
            kpi_df = pd.DataFrame(list(kpi_data.items()), columns=["Metric", "Value"])
            kpi_df.to_excel(writer, sheet_name='Executive Summary', index=False)

            # Sheet 2: All Tickets
            tickets_df = db_manager.fetch_dataframe("""
                SELECT ticket_number, title, category, priority, status, created_at,
                       resolved_at, sla_breached, reopen_count, satisfaction_rating, resolution_notes
                FROM tickets ORDER BY ticket_id DESC;
            """)
            tickets_df.to_excel(writer, sheet_name='Tickets Master', index=False)

            # Sheet 3: Agent Rankings
            agent_df = AnalyticsService.get_agent_rankings()
            if not agent_df.empty:
                agent_df.to_excel(writer, sheet_name='Agent Rankings', index=False)

            # Sheet 4: Department Load
            dept_df = AnalyticsService.get_department_load()
            if not dept_df.empty:
                dept_df.to_excel(writer, sheet_name='Department Load', index=False)

            # Sheet 5: SLA Compliance
            sla_df = AnalyticsService.get_sla_compliance_breakdown()
            if not sla_df.empty:
                sla_df.to_excel(writer, sheet_name='SLA Compliance', index=False)

        output.seek(0)
        return output.getvalue()

    @staticmethod
    def generate_pdf_report() -> bytes:
        """Generates an executive PDF report using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=6
        )

        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=15
        )

        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=12,
            spaceAfter=8
        )

        # Header
        elements.append(Paragraph("Enterprise IT Helpdesk & SLA Executive Report", title_style))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Antigravity IT Operations", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3B82F6'), spaceAfter=15))

        # KPI Summary Table
        kpis = AnalyticsService.get_kpi_summary()
        elements.append(Paragraph("1. Executive KPI Overview", section_style))

        kpi_table_data = [
            ["Metric", "Value", "Metric", "Value"],
            ["Total Tickets", str(kpis.get("total_tickets", 0)), "Open Backlog", str(kpis.get("open_tickets", 0) + kpis.get("assigned_tickets", 0))],
            ["In Progress", str(kpis.get("in_progress_tickets", 0)), "Resolved / Closed", str(kpis.get("resolved_tickets", 0))],
            ["SLA Compliance", f"{kpis.get('sla_compliance_pct', 100)}%", "SLA Breaches", str(kpis.get("sla_breached_count", 0))],
            ["Avg CSAT Score", f"{kpis.get('avg_csat_score', 0)} / 5.0", "Reopened Tickets", str(kpis.get("reopened_tickets", 0))],
        ]

        t_kpi = Table(kpi_table_data, colWidths=[130, 130, 130, 130])
        t_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        elements.append(t_kpi)
        elements.append(Spacer(1, 15))

        # Department Breakdown Table
        elements.append(Paragraph("2. Department-wise Demand & Workload", section_style))
        dept_df = AnalyticsService.get_department_load()
        if not dept_df.empty:
            dept_table_data = [["Department", "Total Requests", "Critical", "Pending", "Breached", "% Share"]]
            for _, row in dept_df.iterrows():
                dept_table_data.append([
                    str(row["department_name"]),
                    str(row["total_requests"]),
                    str(row["critical_tickets"]),
                    str(row["pending_tickets"]),
                    str(row["breached_tickets"]),
                    f"{row['pct_of_total_company_load']}%"
                ])
            t_dept = Table(dept_table_data, colWidths=[170, 75, 65, 65, 65, 80])
            t_dept.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284C7')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F5F9')])
            ]))
            elements.append(t_dept)

        elements.append(Spacer(1, 15))

        # Top Agents Table
        elements.append(Paragraph("3. Top Ranked Support Agents", section_style))
        agent_df = AnalyticsService.get_agent_rankings()
        if not agent_df.empty:
            agent_table_data = [["Rank", "Agent Name", "Team", "Resolved", "Active", "SLA %", "CSAT"]]
            for _, row in agent_df.head(6).iterrows():
                agent_table_data.append([
                    f"#{row.get('performance_rank', '-')}",
                    str(row["agent_name"]),
                    str(row["team_name"]),
                    str(row["tickets_resolved"]),
                    str(row["active_tickets"]),
                    f"{row['sla_compliance_pct']}%",
                    f"{row['avg_csat']}★" if row['avg_csat'] else "N/A"
                ])
            t_agent = Table(agent_table_data, colWidths=[45, 140, 135, 55, 45, 50, 50])
            t_agent.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F5F9')])
            ]))
            elements.append(t_agent)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
