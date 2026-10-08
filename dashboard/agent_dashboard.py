import os
import streamlit as st
import pandas as pd
from datetime import datetime
from core.repositories import TicketRepository, AgentRepository, SLARepository
from core.auth import SessionManager
from core.logger import log_audit, log_error
from dashboard.ui_components import render_kpi_card, get_status_badge, get_priority_badge, get_sla_status_badge, render_ticket_progress_stepper
from tickets.ticket_assignment import TicketAssignmentManager

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def render_agent_dashboard():
    """Main dashboard for Support Agents and Team Leads."""
    user = SessionManager.get_current_user()
    agent_repo = AgentRepository()
    ticket_repo = TicketRepository()
    assignment_mgr = TicketAssignmentManager()

    agent = agent_repo.get_by_user_id(user.user_id)
    is_team_lead = user.role in ("Team Lead", "Admin")

    # Header and Status Bar
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown(f"### 🎧 Support Operations: **{agent.full_name if agent else user.username}**")
        st.caption(f"Team: **{agent.team.name if agent and agent.team else 'Management'}** | Specialization: **{agent.specialization if agent else 'Support Lead'}**")
    
    with header_col2:
        if agent:
            avail_status = st.toggle("🟢 Available for Routing", value=agent.is_available, key="agent_avail_toggle")
            if avail_status != agent.is_available:
                agent_repo.update_availability(agent.agent_id, avail_status)
                st.toast(f"Availability updated to {'Available' if avail_status else 'Away'}")
                st.rerun()

    # Fetch agent tickets & global tickets
    my_tickets = ticket_repo.get_filtered_tickets(agent_id=agent.agent_id if agent else None)
    all_tickets = ticket_repo.get_filtered_tickets()

    # KPI summary
    my_active = sum(1 for t in my_tickets if t.status in ("ASSIGNED", "IN PROGRESS", "REOPENED"))
    my_resolved = sum(1 for t in my_tickets if t.status in ("RESOLVED", "CLOSED"))
    unassigned_tickets = [t for t in all_tickets if t.assigned_agent_id is None and t.status in ("OPEN", "ASSIGNED", "REOPENED")]
    unassigned_count = len(unassigned_tickets)
    breached = sum(1 for t in my_tickets if t.is_breached() and t.status not in ("RESOLVED", "CLOSED"))
    
    # Calculate CSAT for agent
    agent_csat_ratings = [t.csat_rating for t in my_tickets if t.csat_rating is not None]
    avg_csat = round(sum(agent_csat_ratings) / len(agent_csat_ratings), 1) if agent_csat_ratings else 5.0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_kpi_card("Active Assigned", str(my_active), "Requires attention", "⚡")
    with col2:
        render_kpi_card("Unassigned Queue", str(unassigned_count), "Available in pool", "📥")
    with col3:
        render_kpi_card("SLA Breaches", str(breached), "Overdue resolution", "🚨")
    with col4:
        render_kpi_card("Resolved by Me", str(my_resolved), "Completed tickets", "🏆")
    with col5:
        render_kpi_card("CSAT Rating", f"⭐ {avg_csat} / 5.0", f"{len(agent_csat_ratings)} ratings", "🌟")

    st.divider()

    tab_my, tab_unassigned, tab_workload, tab_all = st.tabs([
        "📌 My Active Queue", "📥 Unassigned Pool", "👥 Agent Workloads", "🔍 Global Ticket Search"
    ])

    with tab_my:
        st.markdown("#### 🛠️ My Assigned Tickets")
        active_list = [t for t in my_tickets if t.status not in ("CLOSED",)]

        # Quick urgency sort: Breached / High priority first
        active_list.sort(key=lambda x: (not x.is_breached(), x.priority != "Critical", x.priority != "High"))

        if not active_list:
            st.success("✨ Your queue is clear! No pending assigned tickets.")
        else:
            # Single-open accordion selector for agents
            agent_ticket_options = {f"#{t.ticket_number} — {t.title} [{t.priority}] ({t.status})": t.ticket_id for t in active_list}
            if "active_agent_ticket_id" not in st.session_state or st.session_state["active_agent_ticket_id"] not in agent_ticket_options.values():
                st.session_state["active_agent_ticket_id"] = active_list[0].ticket_id

            selected_agent_label = st.selectbox(
                "🎯 Select Ticket to Work On:",
                list(agent_ticket_options.keys()),
                index=list(agent_ticket_options.values()).index(st.session_state["active_agent_ticket_id"]),
                key="agent_ticket_picker"
            )
            st.session_state["active_agent_ticket_id"] = agent_ticket_options[selected_agent_label]

            for t in active_list:
                is_open = (t.ticket_id == st.session_state["active_agent_ticket_id"])
                with st.expander(f"**#{t.ticket_number}** — {t.title} | {t.status} ({t.priority})", expanded=is_open):
                    _render_agent_ticket_card(t, user, agent, ticket_repo, agent_repo, prefix="my_queue")

    with tab_unassigned:
        col_u1, col_u2 = st.columns([3, 1])
        with col_u1:
            st.markdown("#### 📥 Unassigned Tickets Pool")
            st.caption("Tickets awaiting assignment to appropriate specialists")
        with col_u2:
            if unassigned_tickets and st.button("⚡ Smart Auto-Route All", type="primary", use_container_width=True, key="batch_auto_route_btn"):
                assigned_count = 0
                for unassigned_t in unassigned_tickets:
                    try:
                        assignment_mgr.auto_assign_ticket(unassigned_t.ticket_id, assigned_by_user_id=user.user_id)
                        assigned_count += 1
                    except Exception as ex:
                        log_error(f"Auto routing failed for ticket {unassigned_t.ticket_id}", ex)
                st.success(f"🎉 Smart-routed {assigned_count} tickets to least-loaded specialists!")
                st.rerun()

        if not unassigned_tickets:
            st.info("No unassigned tickets in pool. All tickets have been assigned!")
        else:
            for t in unassigned_tickets:
                is_res = t.status in ("RESOLVED", "CLOSED")
                with st.expander(f"**#{t.ticket_number}** — {t.title} [{t.priority}] (Dept: {t.department.name if t.department else 'General'})"):
                    col_det, col_meta = st.columns([3, 1])
                    with col_det:
                        st.write(t.description)
                        st.caption(f"Created by **{t.employee.full_name if t.employee else 'Unknown'}** at {t.created_at.strftime('%Y-%m-%d %H:%M')}")
                    with col_meta:
                        st.markdown(f"**Priority:** {get_priority_badge(t.priority)}", unsafe_allow_html=True)
                        st.markdown(f"**SLA:** {get_sla_status_badge(t.resolution_deadline, is_res, t.resolved_at)}", unsafe_allow_html=True)

                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if agent and st.button(f"✋ Claim Myself (#{t.ticket_number})", key=f"unassigned_claim_{t.ticket_id}", use_container_width=True):
                            assignment_mgr.claim_ticket(t.ticket_id, agent.agent_id, user.user_id)
                            st.success(f"Claimed #{t.ticket_number}! Moved to In Progress.")
                            st.rerun()
                    with btn_c2:
                        if st.button(f"⚡ Smart Auto-Assign (#{t.ticket_number})", key=f"unassigned_auto_{t.ticket_id}", use_container_width=True):
                            try:
                                _, best_agent = assignment_mgr.auto_assign_ticket(t.ticket_id, assigned_by_user_id=user.user_id)
                                st.success(f"Auto-assigned #{t.ticket_number} to {best_agent.full_name} ({best_agent.specialization})")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Routing failed: {str(e)}")

    with tab_workload:
        st.markdown("#### 👥 Real-Time Support Team Workload & Availability")
        workloads = assignment_mgr.get_agent_workloads()
        if workloads:
            wl_df = pd.DataFrame(workloads)
            st.dataframe(
                wl_df.rename(columns={
                    "full_name": "Agent Name",
                    "team_name": "Team",
                    "specialization": "Specialization",
                    "is_available": "Available",
                    "active_tickets": "Active Queue",
                    "resolved_tickets": "Resolved Total",
                    "workload_status": "Workload Level"
                })[["Agent Name", "Team", "Specialization", "Available", "Active Queue", "Resolved Total", "Workload Level"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No agents found.")

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
    is_res = t.status in ("RESOLVED", "CLOSED")
    
    # 1. Visual Progress Stepper
    st.markdown(render_ticket_progress_stepper(t.status), unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        # Clean description & render attachment preview
        desc_text = t.description
        attach_file = None
        if "[📎 Attachment: " in desc_text:
            parts = desc_text.split("[📎 Attachment: ")
            desc_text = parts[0].strip()
            attach_file = parts[1].replace("]", "").strip()

        st.markdown(f"**Description:**\n{desc_text}")

        if attach_file:
            full_attach_path = os.path.join(UPLOAD_DIR, attach_file)
            if os.path.exists(full_attach_path):
                if attach_file.lower().endswith((".png", ".jpg", ".jpeg")):
                    st.image(full_attach_path, caption=f"Screenshot: {attach_file}", width=350)
                else:
                    st.caption(f"📎 **Attached File:** `{attach_file}`")

        emp_name = t.employee.full_name if t.employee else "Unknown Employee"
        dept_name = t.department.name if t.department else (t.employee.department.name if t.employee and t.employee.department else "General")
        cat_name = t.category.name if t.category else "General"
        st.caption(f"Employee: **{emp_name}** ({dept_name}) | Category: **{cat_name}**")
        if t.resolution_deadline:
            st.caption(f"Target SLA: {t.resolution_deadline.strftime('%Y-%m-%d %H:%M')}")

    with col_b:
        st.markdown(f"**Status:** {get_status_badge(t.status)}", unsafe_allow_html=True)
        st.markdown(f"**Priority:** {get_priority_badge(t.priority)}", unsafe_allow_html=True)
        st.markdown(f"**SLA:** {get_sla_status_badge(t.resolution_deadline, is_res, t.resolved_at)}", unsafe_allow_html=True)

        if t.csat_rating:
            st.markdown(f"""
            <div style="background-color: #FEF3C7; border: 1px solid #FDE68A; border-radius: 6px; padding: 6px 10px; margin-top: 6px;">
                <div style="color: #92400E; font-weight: 600; font-size: 0.8rem;">⭐ Employee Rating: {'⭐' * t.csat_rating} ({t.csat_rating}/5)</div>
                {f'<div style="font-size: 0.78rem; color: #451A03;">"{t.csat_feedback}"</div>' if t.csat_feedback else ''}
            </div>
            """, unsafe_allow_html=True)

    # Workflow Actions Box
    st.markdown("##### ⚡ Workflow Actions")
    act_col1, act_col2, act_col3 = st.columns(3)

    with act_col1:
        if t.status in ("ASSIGNED", "OPEN"):
            if st.button("▶️ Start Progress", key=f"{prefix}_start_{t.ticket_id}", use_container_width=True, type="primary"):
                ticket_repo.update_status(t.ticket_id, "IN PROGRESS", user_id=user.user_id)
                st.rerun()

    with act_col2:
        if t.status in ("IN PROGRESS", "REOPENED", "ASSIGNED"):
            with st.popover("✅ Resolve Ticket", use_container_width=True):
                st.markdown(f"**Resolve #{t.ticket_number}**")
                root_cause = st.text_input("Root Cause *", placeholder="e.g. DNS cache stale / Expired cert / Bad cable", key=f"{prefix}_rc_{t.ticket_id}")
                steps = st.text_area("Resolution Steps Taken *", placeholder="Detailed steps applied to solve...", key=f"{prefix}_step_{t.ticket_id}")
                cat = st.selectbox("Resolution Category", ["Technical Fix", "User Configuration", "Hardware Replacement", "Access Granted", "Workaround"], key=f"{prefix}_rescat_{t.ticket_id}")
                if st.button("Submit Resolution", key=f"{prefix}_btn_res_{t.ticket_id}", type="primary", use_container_width=True):
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
        if user.role in ("Team Lead", "Admin") or (agent and t.assigned_agent_id == agent.agent_id):
            with st.popover("🔄 Reassign Ticket", use_container_width=True):
                all_agents = agent_repo.get_all()
                agent_dict = {f"{a.full_name} ({a.team.name if a.team else 'General'})": a.agent_id for a in all_agents}
                chosen_agent_label = st.selectbox("Assign to Agent", list(agent_dict.keys()), key=f"{prefix}_reassign_sel_{t.ticket_id}")
                chosen_agent_id = agent_dict[chosen_agent_label]
                reassign_note = st.text_input("Reassignment Reason", placeholder="Specialist required...", key=f"{prefix}_reassign_note_{t.ticket_id}")
                if st.button("Confirm Reassignment", key=f"{prefix}_reassign_btn_{t.ticket_id}", type="primary", use_container_width=True):
                    chosen_agent = next(a for a in all_agents if a.agent_id == chosen_agent_id)
                    ticket_repo.assign_ticket(
                        ticket_id=t.ticket_id,
                        agent_id=chosen_agent_id,
                        team_id=chosen_agent.team_id,
                        user_id=user.user_id,
                        comment=f"Reassigned to {chosen_agent.full_name}: {reassign_note.strip()}" if reassign_note.strip() else f"Reassigned to {chosen_agent.full_name}"
                    )
                    st.success(f"Reassigned #{t.ticket_number} to {chosen_agent.full_name}!")
                    st.rerun()

    # Communication & History
    c_tab1, c_tab2 = st.tabs(["💬 Messages & Internal Notes", "📜 Audit Trail"])

    with c_tab1:
        full_ticket = ticket_repo.get_by_id(t.ticket_id)
        if full_ticket and full_ticket.comments:
            for c in full_ticket.comments:
                is_int = c.is_internal
                badge_type = "<span style='color:#D97706; font-weight:600;'>[INTERNAL NOTE]</span>" if is_int else ""
                author = c.user.username if c.user else "System"
                st.markdown(f"""
                <div class="comment-bubble {'internal' if is_int else ''}">
                    <div style="font-size:0.75rem; color:#64748B;"><strong>{author}</strong> {badge_type} • {c.created_at.strftime('%b %d, %H:%M')}</div>
                    <div style="font-size:0.88rem; margin-top:4px; color:#1E293B;">{c.comment_text}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No comments posted.")

        # Canned responses & reply form
        canned_options = [
            "Custom message...",
            "🔍 We are currently investigating your request and analyzing server & network logs.",
            "🛠️ Please collect and attach diagnostic log files from %TEMP% or ~/.logs.",
            "🔑 Password / MFA token has been reset. Please test your login and verify.",
            "🔄 Configuration update deployed. Please restart your workstation and verify.",
            "⚡ Escalated to Tier-3 Infrastructure Engineering for specialized remediation.",
            "📦 Replacement hardware has been dispatched. Courier tracking will be updated shortly.",
            "⏳ Waiting for employee confirmation. Please let us know if everything is functioning."
        ]
        chosen_canned = st.selectbox("⚡ Quick Canned Templates", canned_options, key=f"{prefix}_canned_{t.ticket_id}")
        default_val = "" if chosen_canned == "Custom message..." else chosen_canned

        with st.form(key=f"{prefix}_agent_comment_form_{t.ticket_id}", clear_on_submit=True):
            reply_text = st.text_area("Write public message or internal note...", value=default_val, height=65, key=f"{prefix}_reply_txt_{t.ticket_id}")
            is_internal = st.checkbox("🔒 Internal Note (Only visible to IT Staff)", value=False, key=f"{prefix}_chk_int_{t.ticket_id}")
            if st.form_submit_button("Send Response", use_container_width=True):
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
                    {f'<div style="font-size:0.8rem; color:#64748B;">{h.comment}</div>' if h.comment else ''}
                </div>
                """, unsafe_allow_html=True)

