"""Executive Management & Admin Analytics Dashboard."""

import streamlit as st
import pandas as pd
from datetime import datetime
from core.repositories import TicketRepository, DepartmentRepository, AgentRepository, SLARepository
from core.database import db
from core.auth import SessionManager
from dashboard.ui_components import render_kpi_card, get_status_badge, get_priority_badge
from dashboard.charts import (
    create_status_donut, create_priority_chart, create_department_bar,
    create_sla_compliance_gauge, create_agent_performance_bar, create_category_bar
)

def render_admin_dashboard():
    """Main Executive Management and Analytics portal."""
    ticket_repo = TicketRepository()
    dept_repo = DepartmentRepository()
    agent_repo = AgentRepository()

    st.markdown("### 📊 Executive IT Helpdesk Intelligence")
    st.caption("Real-time operational metrics, SLA compliance & support workload analytics")

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
        render_kpi_card("Active Load", str(open_tickets), "In progress queue", "⚡")
    with kpi3:
        render_kpi_card("Resolved", str(resolved_tickets), f"Avg: {avg_res_hours} hrs", "✅")
    with kpi4:
        render_kpi_card("SLA Compliance", f"{compliance_pct}%", f"{breached_tickets} breaches", "🎯")
    with kpi5:
        render_kpi_card("Critical Issues", str(len(df[df['priority'] == 'Critical']) if not df.empty else 0), "P1 Incidents", "🚨")

    st.divider()

    # Tabs for analytics vs management views
    tab_analytics, tab_agents, tab_sla, tab_export = st.tabs([
        "📈 Operational Analytics", "👥 Agent Performance Leaderboard", "🚨 SLA Breach Monitor", "📥 Export & Reports"
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

    with tab_export:
        st.markdown("#### 📥 Export Operational Reports")
        st.write("Generate clean data exports for IT management reviews and compliance auditing.")

        if not df.empty:
            csv_data = df.to_csv(index=False).encode('utf-8')
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    label="📄 Download Full Ticket Dump (CSV)",
                    data=csv_data,
                    file_name=f"it_tickets_export_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )
            with col_d2:
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
