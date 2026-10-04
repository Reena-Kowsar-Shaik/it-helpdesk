"""Support Agent & Team Lead Workspace."""

import streamlit as st
import pandas as pd
from datetime import datetime
from core.repositories import TicketRepository, AgentRepository, SLARepository
from core.auth import SessionManager
from core.logger import log_audit, log_error
from dashboard.ui_components import render_kpi_card, get_status_badge, get_priority_badge

def render_agent_dashboard():
    """Main dashboard for Support Agents and Team Leads."""
    user = SessionManager.get_current_user()
    agent_repo = AgentRepository()
    ticket_repo = TicketRepository()

    agent = agent_repo.get_by_user_id(user.user_id)
    is_team_lead = user.role == "Team Lead"

    st.markdown(f"### 🎧 Support Operations: **{agent.full_name if agent else user.username}**")
    st.caption(f"Team: **{agent.team.name if agent and agent.team else 'Management'}** | Specialization: **{agent.specialization if agent else 'Support Lead'}**")

    # Fetch agent tickets & global tickets
    my_tickets = ticket_repo.get_filtered_tickets(agent_id=agent.agent_id if agent else None)
    all_tickets = ticket_repo.get_filtered_tickets()

    # KPI summary
    my_active = sum(1 for t in my_tickets if t.status in ("ASSIGNED", "IN PROGRESS", "REOPENED"))
    my_resolved = sum(1 for t in my_tickets if t.status in ("RESOLVED", "CLOSED"))
    unassigned = sum(1 for t in all_tickets if t.status == "OPEN" or t.assigned_agent_id is None)
    breached = sum(1 for t in my_tickets if t.is_breached() and t.status not in ("RESOLVED", "CLOSED"))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card("Active Assigned", str(my_active), "Requires attention", "⚡")
    with col2:
        render_kpi_card("Unassigned Queue", str(unassigned), "Available to claim", "📥")
    with col3:
        render_kpi_card("SLA Breaches", str(breached), "Overdue resolution", "🚨")
    with col4:
        render_kpi_card("Resolved by Me", str(my_resolved), "Completed tickets", "🏆")

    st.divider()

    tab_my, tab_unassigned, tab_all = st.tabs(["📌 My Active Queue", "📥 Unassigned Pool", "🔍 Global Ticket Search"])

    with tab_my:
        st.markdown("#### 🛠️ My Assigned Tickets")
        active_list = [t for t in my_tickets if t.status not in ("CLOSED",)]

        if not active_list:
            st.success("✨ Your queue is clear! No pending assigned tickets.")
        else:
            for t in active_list:
                _render_agent_ticket_card(t, user, agent, ticket_repo, agent_repo, prefix="my_queue")

    with tab_unassigned:
        st.markdown("#### 📥 Unassigned Tickets Pool")
        unassigned_list = [t for t in all_tickets if t.assigned_agent_id is None and t.status in ("OPEN", "ASSIGNED", "REOPENED")]

        if not unassigned_list:
            st.info("No unassigned tickets in pool.")
        else:
            for t in unassigned_list:
                with st.expander(f"**#{t.ticket_number}** — {t.title} [{t.priority}] (Dept: {t.department.name if t.department else 'General'})"):
                    st.write(t.description)
                    st.caption(f"Created by **{t.employee.full_name if t.employee else 'Unknown'}** at {t.created_at.strftime('%Y-%m-%d %H:%M')}")
                    if agent and st.button(f"✋ Claim & Assign to Me (#{t.ticket_number})", key=f"unassigned_claim_{t.ticket_id}"):
                        ticket_repo.assign_ticket(
                            ticket_id=t.ticket_id,
                            agent_id=agent.agent_id,
                            team_id=agent.team_id,
                            user_id=user.user_id,
                            comment=f"Claimed by agent {agent.full_name}"
                        )
                        ticket_repo.update_status(t.ticket_id, "IN PROGRESS", user_id=user.user_id)
                        st.success(f"Claimed #{t.ticket_number}! Moved to In Progress.")
                        st.rerun()

    with tab_all:
        st.markdown("#### 🔍 All Tickets Overview")
        f1, f2, f3 = st.columns(3)
        with f1:
            q_status = st.selectbox("Filter Status", ["All", "OPEN", "ASSIGNED", "IN PROGRESS", "RESOLVED", "CLOSED", "REOPENED"], key="ag_stat")
        with f2:
            q_priority = st.selectbox("Filter Priority", ["All", "Critical", "High", "Medium", "Low"], key="ag_prio")
        with f3:
            q_search = st.text_input("Keyword Search", key="ag_search")

        results = ticket_repo.get_filtered_tickets(status=q_status, priority=q_priority, search_query=q_search)
        st.caption(f"Found {len(results)} tickets")

        for t in results[:15]:
            agent_name = t.assigned_agent.full_name if t.assigned_agent else 'Unassigned'
            with st.expander(f"**#{t.ticket_number}** — {t.title} | {t.status} | Agent: {agent_name}"):
                _render_agent_ticket_card(t, user, agent, ticket_repo, agent_repo, prefix="search_queue")


def _render_agent_ticket_card(t, user, agent, ticket_repo, agent_repo, prefix="card"):
    """Detailed ticket card with agent workflow actions."""
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(f"**Description:**\n{t.description}")
        emp_name = t.employee.full_name if t.employee else "Unknown Employee"
        dept_name = t.department.name if t.department else (t.employee.department.name if t.employee and t.employee.department else "General")
        cat_name = t.category.name if t.category else "General"
        st.caption(f"Employee: **{emp_name}** ({dept_name}) | Category: **{cat_name}**")
        if t.resolution_deadline:
            deadline_color = "red" if t.is_breached() else "#94A3B8"
            st.markdown(f"<span style='color:{deadline_color}; font-size:0.8rem;'><strong>Target SLA:</strong> {t.resolution_deadline.strftime('%Y-%m-%d %H:%M')}</span>", unsafe_allow_html=True)

    with col_b:
        st.markdown(f"**Status:** {get_status_badge(t.status)}", unsafe_allow_html=True)
        st.markdown(f"**Priority:** {get_priority_badge(t.priority)}", unsafe_allow_html=True)

    # Workflow Actions Box
    st.markdown("##### ⚡ Workflow Actions")
    act_col1, act_col2, act_col3 = st.columns(3)

    with act_col1:
        if t.status == "ASSIGNED":
            if st.button("▶️ Start Progress", key=f"{prefix}_start_{t.ticket_id}", use_container_width=True):
                ticket_repo.update_status(t.ticket_id, "IN PROGRESS", user_id=user.user_id)
                st.rerun()

    with act_col2:
        if t.status in ("IN PROGRESS", "REOPENED", "ASSIGNED"):
            # Resolve trigger
            with st.popover("✅ Resolve Ticket"):
                st.markdown(f"**Resolve #{t.ticket_number}**")
                root_cause = st.text_input("Root Cause", placeholder="e.g. DNS cache stale / Expired cert", key=f"{prefix}_rc_{t.ticket_id}")
                steps = st.text_area("Resolution Steps Taken", placeholder="Detailed steps applied...", key=f"{prefix}_step_{t.ticket_id}")
                cat = st.selectbox("Resolution Category", ["Technical Fix", "User Configuration", "Hardware Replacement", "Access Granted", "Workaround"], key=f"{prefix}_rescat_{t.ticket_id}")
                if st.button("Submit Resolution", key=f"{prefix}_btn_res_{t.ticket_id}", type="primary"):
                    if root_cause.strip() and steps.strip():
                        ticket_repo.resolve_ticket(
                            ticket_id=t.ticket_id,
                            agent_id=agent.agent_id if agent else 1,
                            root_cause=root_cause.strip(),
                            resolution_steps=steps.strip(),
                            resolution_category=cat,
                            user_id=user.user_id
                        )
                        st.success("Ticket marked as RESOLVED!")
                        st.rerun()
                    else:
                        st.error("Root cause and resolution steps are required.")

    with act_col3:
        if t.status == "RESOLVED":
            if st.button("🔒 Close Ticket", key=f"{prefix}_close_{t.ticket_id}", use_container_width=True):
                ticket_repo.update_status(t.ticket_id, "CLOSED", user_id=user.user_id, comment="Closed by support agent.")
                st.rerun()

    # Communication & History
    c_tab1, c_tab2 = st.tabs(["💬 Messages & Internal Notes", "📜 Audit Trail"])

    with c_tab1:
        full_ticket = ticket_repo.get_by_id(t.ticket_id)
        if full_ticket and full_ticket.comments:
            for c in full_ticket.comments:
                is_int = c.is_internal
                badge_type = "<span style='color:#F59E0B;'>[INTERNAL NOTE]</span>" if is_int else ""
                author = c.user.username if c.user else "System"
                st.markdown(f"""
                <div class="comment-bubble {'internal' if is_int else ''}">
                    <div style="font-size:0.75rem; color:#94A3B8;"><strong>{author}</strong> {badge_type} • {c.created_at.strftime('%b %d, %H:%M')}</div>
                    <div style="font-size:0.88rem; margin-top:4px;">{c.comment_text}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No comments posted.")

        with st.form(key=f"{prefix}_agent_comment_form_{t.ticket_id}", clear_on_submit=True):
            reply_text = st.text_area("Write message or internal note...", height=60, key=f"{prefix}_reply_txt_{t.ticket_id}")
            is_internal = st.checkbox("🔒 Internal Note (Only visible to IT Staff)", value=False, key=f"{prefix}_chk_int_{t.ticket_id}")
            if st.form_submit_button("Send Response"):
                if reply_text.strip():
                    ticket_repo.add_comment(t.ticket_id, user.user_id, reply_text.strip(), is_internal=is_internal)
                    st.rerun()

    with c_tab2:
        full_ticket = ticket_repo.get_by_id(t.ticket_id)
        if full_ticket and full_ticket.history:
            for h in full_ticket.history:
                changer = h.user.username if h.user else "System / Auto"
                st.markdown(f"""
                <div class="timeline-item">
                    <div class="timeline-date">{h.changed_at.strftime('%Y-%m-%d %H:%M:%S')} by <strong>{changer}</strong></div>
                    <div class="timeline-text">Status: <code>{h.old_status or 'NEW'}</code> ➔ <code>{h.new_status}</code></div>
                    {f'<div style="font-size:0.8rem; color:#94A3B8;">{h.comment}</div>' if h.comment else ''}
                </div>
                """, unsafe_allow_html=True)
