"""Executive Management & Admin Analytics Dashboard."""

import streamlit as st
import pandas as pd
from datetime import datetime
from core.repositories import TicketRepository, DepartmentRepository, AgentRepository, SLARepository
from core.database import db
from core.auth import SessionManager
from core.logger import log_error
from dashboard.ui_components import render_kpi_card, get_status_badge, get_priority_badge, get_sla_status_badge
from dashboard.charts import (
    create_status_donut, create_priority_chart, create_department_bar,
    create_sla_compliance_gauge, create_agent_performance_bar, create_category_bar
)
from analytics.reports import ReportGenerator
from analytics.sql_queries import (
    SQLQueryManager,
    QUERY_DEPARTMENT_SUMMARY,
    QUERY_PROBLEMATIC_DEPARTMENTS_HAVING,
    QUERY_AGENT_PERFORMANCE_WINDOW,
    QUERY_WORKLOAD_ANALYSIS_CTE,
    QUERY_CORRELATED_SUBQUERY_LONGER_THAN_DEPT,
    QUERY_MONTHLY_CUMULATIVE_WINDOW,
    QUERY_RECURRING_PROBLEMS,
    QUERY_REOPENED_TICKETS_AUDIT,
    QUERY_SLA_BREACH_DRILLDOWN
)
from tickets.ticket_assignment import TicketAssignmentManager

def render_admin_dashboard():
    """Main Executive Management and Analytics portal."""
    ticket_repo = TicketRepository()
    dept_repo = DepartmentRepository()
    agent_repo = AgentRepository()
    assignment_mgr = TicketAssignmentManager()
    user = SessionManager.get_current_user()

    # Header with Batch Auto-Assign Trigger
    head_c1, head_c2 = st.columns([3, 1])
    with head_c1:
        st.markdown("### 📊 Executive IT Helpdesk Intelligence")
        st.caption("Real-time operational metrics, SLA compliance, advanced SQL BI & queue optimization")

    # Fetch all tickets
    all_tickets = ticket_repo.get_filtered_tickets()

    # Build DataFrame
    ticket_data = []
    for t in all_tickets:
        ticket_data.append({
            "ticket_id": t.ticket_id,
            "ticket_number": t.ticket_number,
            "title": t.title,
            "department": t.department.name if t.department else "N/A",
            "category": t.category.name if t.category else "N/A",
            "priority": t.priority,
            "status": t.status,
            "agent": t.assigned_agent.full_name if t.assigned_agent else "Unassigned",
            "is_breached": t.is_breached(),
            "created_at": t.created_at,
            "resolved_at": t.resolved_at,
            "resolution_deadline": t.resolution_deadline,
            "reopened_count": t.reopened_count
        })

    df = pd.DataFrame(ticket_data) if ticket_data else pd.DataFrame(columns=[
        "ticket_id", "ticket_number", "title", "department", "category", "priority", "status", "agent", "is_breached", "created_at", "resolved_at"
    ])

    unassigned_count = len(df[df["agent"] == "Unassigned"]) if not df.empty else 0

    with head_c2:
        if unassigned_count > 0:
            if st.button(f"⚡ Auto-Route ({unassigned_count} Unassigned)", type="primary", use_container_width=True, key="admin_batch_assign"):
                unassigned_objs = [t for t in all_tickets if t.assigned_agent_id is None]
                routed = 0
                for u in unassigned_objs:
                    try:
                        assignment_mgr.auto_assign_ticket(u.ticket_id, assigned_by_user_id=user.user_id if user else 1)
                        routed += 1
                    except Exception as e:
                        log_error(f"Batch routing failed for ticket {u.ticket_id}", e)
                st.success(f"Successfully auto-routed {routed} tickets!")
                st.rerun()

    # 1. Executive KPIs
    total_tickets = len(df)
    open_tickets = len(df[df["status"].isin(["OPEN", "ASSIGNED", "IN PROGRESS", "REOPENED"])]) if not df.empty else 0
    resolved_tickets = len(df[df["status"].isin(["RESOLVED", "CLOSED"])]) if not df.empty else 0
    breached_tickets = len(df[df["is_breached"] == True]) if not df.empty else 0

    # Calculate compliance %
    compliance_pct = round(((total_tickets - breached_tickets) / total_tickets * 100), 1) if total_tickets > 0 else 100.0

    # Calculate avg resolution hours
    resolved_df = df[df["resolved_at"].notnull()] if not df.empty else pd.DataFrame()
    if not resolved_df.empty:
        durations = (resolved_df["resolved_at"] - resolved_df["created_at"]).dt.total_seconds() / 3600.0
        avg_res_hours = round(durations.mean(), 1)
    else:
        avg_res_hours = 0.0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        render_kpi_card("Total Tickets", str(total_tickets), "System-wide", "📈")
    with kpi2:
        render_kpi_card("Active Load", str(open_tickets), f"{unassigned_count} unassigned", "⚡")
    with kpi3:
        render_kpi_card("Resolved", str(resolved_tickets), f"Avg: {avg_res_hours} hrs", "✅")
    with kpi4:
        render_kpi_card("SLA Compliance", f"{compliance_pct}%", f"{breached_tickets} breaches", "🎯")
    with kpi5:
        render_kpi_card("Critical Issues", str(len(df[df['priority'] == 'Critical']) if not df.empty else 0), "P1 Incidents", "🚨")

    st.divider()

    # Tabs for analytics vs management views vs SQL Intelligence vs Exports
    tab_analytics, tab_agents, tab_sla, tab_sql, tab_export = st.tabs([
        "📈 Operational Analytics",
        "👥 Agent Leaderboard",
        "🚨 SLA Breach Monitor",
        "🔬 Deep SQL Intelligence",
        "📥 Export & Executive PDF"
    ])

    with tab_analytics:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.plotly_chart(create_status_donut(df), use_container_width=True)
        with col_c2:
            st.plotly_chart(create_priority_chart(df), use_container_width=True)

        col_c3, col_c4 = st.columns(2)
        with col_c3:
            st.plotly_chart(create_department_bar(df), use_container_width=True)
        with col_c4:
            st.plotly_chart(create_category_bar(df), use_container_width=True)

    with tab_agents:
        st.markdown("#### 🏆 Support Team & Agent Rankings")
        agents = agent_repo.get_all()
        agent_metrics = []

        for a in agents:
            a_tickets = df[df["agent"] == a.full_name] if not df.empty else pd.DataFrame()
            a_total = len(a_tickets)
            a_resolved = len(a_tickets[a_tickets["status"].isin(["RESOLVED", "CLOSED"])]) if not a_tickets.empty else 0
            a_active = a_total - a_resolved
            a_breaches = len(a_tickets[a_tickets["is_breached"] == True]) if not a_tickets.empty else 0
            a_comp = round(((a_total - a_breaches) / a_total * 100), 1) if a_total > 0 else 100.0

            agent_metrics.append({
                "agent_name": a.full_name,
                "team": a.team.name if a.team else "General",
                "specialization": a.specialization,
                "total_assigned": a_total,
                "resolved_tickets": a_resolved,
                "active_tickets": a_active,
                "sla_compliance_pct": f"{a_comp}%",
                "status": "Available" if a.is_available else "Busy"
            })

        st.plotly_chart(create_agent_performance_bar(agent_metrics), use_container_width=True)

        agent_table_df = pd.DataFrame(agent_metrics)
        if not agent_table_df.empty:
            st.dataframe(
                agent_table_df.rename(columns={
                    "agent_name": "Agent Name",
                    "team": "Team",
                    "specialization": "Specialization",
                    "total_assigned": "Total Assigned",
                    "resolved_tickets": "Resolved",
                    "active_tickets": "Active Queue",
                    "sla_compliance_pct": "SLA %",
                    "status": "Availability"
                }),
                use_container_width=True,
                hide_index=True
            )

    with tab_sla:
        st.markdown("#### 🚨 SLA Deadline & Breach Tracker")
        st.plotly_chart(create_sla_compliance_gauge(compliance_pct), use_container_width=True)

        breach_list = df[df["is_breached"] == True] if not df.empty else pd.DataFrame()
        if breach_list.empty:
            st.success("🎉 Zero SLA breaches recorded! All tickets resolved within deadlines.")
        else:
            st.warning(f"⚠️ {len(breach_list)} ticket(s) currently past their SLA resolution target:")
            st.dataframe(
                breach_list[["ticket_number", "title", "department", "priority", "status", "agent", "created_at", "resolution_deadline"]],
                use_container_width=True,
                hide_index=True
            )

    with tab_sql:
        st.markdown("#### 🔬 Enterprise SQL Intelligence & Query Catalog")
        st.caption("Execute advanced SQL queries (CTEs, Window Functions, HAVING, Correlated Subqueries) directly against the database engine.")

        queries_catalog = {
            "🏆 Agent Performance (DENSE_RANK Window Function)": (
                QUERY_AGENT_PERFORMANCE_WINDOW, {},
                "Calculates dense performance ranks across agents by resolution volume and SLA compliance rate."
            ),
            "⚖️ Workload Capacity & Team Benchmarks (Multi-Stage CTE)": (
                QUERY_WORKLOAD_ANALYSIS_CTE, {},
                "Evaluates individual agent load vs. team average using Common Table Expressions."
            ),
            "🏢 Problematic Departments (GROUP BY & HAVING)": (
                QUERY_PROBLEMATIC_DEPARTMENTS_HAVING, {"min_count": 1, "min_hours": 0.5},
                "Identifies departments with high incident rates and prolonged resolution cycles."
            ),
            "🔄 Recurring Technical Hotspots & Reopened Issues": (
                QUERY_RECURRING_PROBLEMS, {},
                "Groups problem frequencies and repeat reopenings to isolate root causes."
            ),
            "📈 Cumulative Monthly Trajectory (Running Total Window)": (
                QUERY_MONTHLY_CUMULATIVE_WINDOW, {},
                "Computes unbounded preceding rolling cumulative ticket counts and resolution throughput."
            ),
            "⏱️ Department Outlier Resolution Anomalies (Correlated Subquery)": (
                QUERY_CORRELATED_SUBQUERY_LONGER_THAN_DEPT, {},
                "Identifies tickets taking significantly longer than the department's baseline average."
            )
        }

        selected_query_title = st.selectbox("Select Analytical SQL Query", list(queries_catalog.keys()))
        sql_text, sql_params, explanation = queries_catalog[selected_query_title]

        st.info(f"💡 **Analysis Goal:** {explanation}")

        with st.expander("📝 View Raw SQL Query Statement", expanded=False):
            st.code(sql_text, language="sql")

        try:
            query_results_df = SQLQueryManager.run_query_df(sql_text, sql_params)
            if not query_results_df.empty:
                st.markdown(f"**Execution Output ({len(query_results_df)} records returned):**")
                st.dataframe(query_results_df, use_container_width=True)
            else:
                st.warning("Query executed successfully, but no matching rows were returned.")
        except Exception as sql_err:
            st.error(f"SQL Execution Error: {sql_err}")

    with tab_export:
        st.markdown("#### 📥 Export Operational Reports & Executive PDF")
        st.write("Generate clean data exports for IT management reviews, executive briefings, and compliance auditing.")

        report_gen = ReportGenerator()

        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            st.markdown("##### 📄 Executive PDF Intelligence Report")
            st.caption("Comprehensive multi-page PDF briefing with KPI scorecards, rankings, department velocity, and recurring issue tables.")
            try:
                pdf_bytes = report_gen.generate_executive_bi_pdf()
                st.download_button(
                    label="📥 Download Executive BI Summary (PDF)",
                    data=pdf_bytes,
                    file_name=f"Executive_IT_Helpdesk_Report_{datetime.utcnow().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            except Exception as pdf_err:
                log_error("PDF generation failed", pdf_err)
                st.error(f"Could not generate PDF: {pdf_err}")

        with exp_col2:
            st.markdown("##### 📊 Raw CSV Operational Dumps")
            st.caption("Standardized CSV formats for external BI tools like PowerBI / Tableau.")
            if not df.empty:
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Download Full Ticket Register (CSV)",
                    data=csv_data,
                    file_name=f"it_tickets_export_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                if not agent_table_df.empty:
                    agent_csv = agent_table_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="👥 Download Agent Performance Report (CSV)",
                        data=agent_csv,
                        file_name=f"agent_performance_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.info("No data available to export.")

