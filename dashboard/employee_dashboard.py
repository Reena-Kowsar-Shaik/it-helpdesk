"""Employee Portal: Ticket Creation, Status Tracking & Comments."""

import streamlit as st
import pandas as pd
from datetime import datetime
from core.repositories import (
    TicketRepository, DepartmentRepository, CategoryRepository, EmployeeRepository
)
from core.auth import SessionManager
from core.logger import log_audit, log_error
from dashboard.ui_components import render_kpi_card, get_status_badge, get_priority_badge

def render_employee_dashboard():
    """Main rendering function for employee workspace."""
    user = SessionManager.get_current_user()
    emp_repo = EmployeeRepository()
    ticket_repo = TicketRepository()
    dept_repo = DepartmentRepository()
    cat_repo = CategoryRepository()

    employee = emp_repo.get_by_user_id(user.user_id)
    if not employee:
        if user.role == "Admin":
            all_employees = emp_repo.get_all()
            st.info("ℹ️ **Admin Mode:** You can submit/view tickets as Administrator or simulate any employee:")
            sim_options = {"👑 My Admin Account": None}
            for e in all_employees:
                sim_options[f"{e.full_name} ({e.department.name})"] = e
            
            selected_label = st.selectbox("Active Persona", list(sim_options.keys()), key="admin_emp_sim")
            if sim_options[selected_label] is not None:
                employee = sim_options[selected_label]
            else:
                employee = emp_repo.create_or_link_employee(user.user_id, full_name="System Administrator", job_title="IT Administrator")
        else:
            # Auto-provision employee profile for support agents, team leads, or newly registered users
            employee = emp_repo.create_or_link_employee(
                user_id=user.user_id,
                full_name=user.username.replace("_", " ").title(),
                job_title=user.role if user.role != "Employee" else "Staff Specialist"
            )

    if not employee:
        st.error("⚠️ Unable to initialize employee profile. Please refresh the page.")
        return

    st.markdown(f"### 👋 Employee Portal: **{employee.full_name}**")
    st.caption(f"🏢 Department: **{employee.department.name}** | 💼 Role: **{employee.job_title}**")

    # Fetch user's tickets
    tickets = ticket_repo.get_filtered_tickets(employee_id=employee.employee_id)

    # 1. Summary Metrics
    total = len(tickets)
    open_count = sum(1 for t in tickets if t.status in ("OPEN", "ASSIGNED"))
    in_prog = sum(1 for t in tickets if t.status == "IN PROGRESS")
    resolved = sum(1 for t in tickets if t.status in ("RESOLVED", "CLOSED"))
    reopened = sum(1 for t in tickets if t.status == "REOPENED")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_kpi_card("Total Tickets", str(total), "Lifetime submitted", "📋")
    with col2:
        render_kpi_card("Open / Assigned", str(open_count), "Awaiting action", "⏳")
    with col3:
        render_kpi_card("In Progress", str(in_prog), "Under investigation", "⚙️")
    with col4:
        render_kpi_card("Resolved", str(resolved), "Successfully closed", "✅")
    with col5:
        render_kpi_card("Reopened", str(reopened), "Needs follow-up", "🔄")

    st.divider()

    # Tabs: My Tickets vs Submit New Ticket
    tab_view, tab_create = st.tabs(["📂 My Tickets", "➕ Raise a New Helpdesk Ticket"])

    with tab_create:
        st.markdown("#### 📝 Submit Support Request")
        categories = cat_repo.get_all()
        departments = dept_repo.get_all()

        with st.form("create_ticket_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                cat_options = {c.name: c.category_id for c in categories}
                selected_cat_name = st.selectbox("Issue Category", list(cat_options.keys()))
                selected_cat_id = cat_options[selected_cat_name]

            with col_b:
                priority = st.selectbox("Urgency / Priority", ["Low", "Medium", "High", "Critical"], index=1)

            title = st.text_input("Summary / Subject", placeholder="Brief description of the problem...")
            description = st.text_area("Detailed Problem Description", placeholder="Include error messages, steps to reproduce, device info...")

            submitted = st.form_submit_button("🚀 Submit Ticket", use_container_width=True, type="primary")
            if submitted:
                if not title.strip() or not description.strip():
                    st.error("Please provide both a summary title and detailed description.")
                else:
                    try:
                        new_ticket = ticket_repo.create_ticket(
                            employee_id=employee.employee_id,
                            department_id=employee.department_id,
                            category_id=selected_cat_id,
                            title=title.strip(),
                            description=description.strip(),
                            priority=priority,
                            user_id=user.user_id
                        )
                        st.success(f"🎉 Ticket **#{new_ticket.ticket_number}** created successfully! Our team will respond shortly.")
                        st.rerun()
                    except Exception as e:
                        log_error("Employee ticket creation failed", e)
                        st.error(f"Failed to create ticket: {str(e)}")

    with tab_view:
        st.markdown("#### 📋 Ticket History & Tracking")

        # Filters
        f_col1, f_col2 = st.columns([3, 1])
        with f_col1:
            search = st.text_input("🔍 Search tickets", placeholder="Search by title, number or keyword...")
        with f_col2:
            status_filter = st.selectbox("Status", ["All", "OPEN", "ASSIGNED", "IN PROGRESS", "RESOLVED", "CLOSED", "REOPENED"])

        filtered = [
            t for t in tickets
            if (status_filter == "All" or t.status == status_filter) and
               (not search or search.lower() in t.title.lower() or search.lower() in t.ticket_number.lower())
        ]

        if not filtered:
            st.info("No matching tickets found.")
        else:
            for t in filtered:
                with st.expander(f"**#{t.ticket_number}** — {t.title} | {t.status} ({t.priority})", expanded=False):
                    col_t1, col_t2 = st.columns([2, 1])
                    with col_t1:
                        st.markdown(f"**Description:**\n{t.description}")
                        st.caption(f"**Category:** {t.category.name} | **Created:** {t.created_at.strftime('%Y-%m-%d %H:%M')}")
                        if t.assigned_agent:
                            st.caption(f"**Assigned Agent:** {t.assigned_agent.full_name} ({t.team.name if t.team else 'General'})")

                    with col_t2:
                        st.markdown(f"**Status:** {get_status_badge(t.status)}", unsafe_allow_html=True)
                        st.markdown(f"**Priority:** {get_priority_badge(t.priority)}", unsafe_allow_html=True)
                        if t.resolution_deadline:
                            st.caption(f"**Target SLA:** {t.resolution_deadline.strftime('%Y-%m-%d %H:%M')}")

                    # Resolution info & actions
                    if t.resolution:
                        st.markdown(f"""
                        <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 12px 16px; margin: 12px 0;">
                            <div style="color: #166534; font-weight: 600; font-size: 0.9rem;">✅ Resolution Provided by Support</div>
                            <div style="color: #1E293B; font-size: 0.88rem; margin-top: 4px;"><strong>Solution:</strong> {t.resolution.resolution_steps}</div>
                            <div style="color: #475569; font-size: 0.8rem; margin-top: 2px;"><em>Root Cause: {t.resolution.root_cause} (Category: {t.resolution.resolution_category})</em></div>
                        </div>
                        """, unsafe_allow_html=True)

                    if t.status == "RESOLVED":
                        st.markdown("##### 📌 Verify Resolution & Close")
                        col_act1, col_act2 = st.columns(2)
                        
                        with col_act1:
                            with st.form(key=f"close_form_{t.ticket_id}"):
                                st.markdown("###### ✅ Everything working? Close Ticket")
                                rating = st.selectbox("How was your support experience?", ["⭐⭐⭐⭐⭐ Excellent", "⭐⭐⭐⭐ Good", "⭐⭐⭐ Satisfactory", "⭐⭐ Needs Improvement", "⭐ Poor"], key=f"csat_rate_{t.ticket_id}")
                                close_note = st.text_input("Feedback / Closing Note (Optional)", placeholder="Thanks for the quick help!", key=f"csat_note_{t.ticket_id}")
                                if st.form_submit_button("🔒 Confirm & Close Ticket", type="primary", use_container_width=True):
                                    comment_msg = f"Closed by requester with rating: {rating}. Feedback: {close_note.strip()}" if close_note.strip() else f"Closed by requester with rating: {rating}"
                                    ticket_repo.update_status(t.ticket_id, "CLOSED", user_id=user.user_id, comment=comment_msg)
                                    st.success("🎉 Ticket closed! Thank you for your feedback.")
                                    st.rerun()

                        with col_act2:
                            with st.form(key=f"reopen_form_{t.ticket_id}"):
                                st.markdown("###### ⚠️ Still facing the issue?")
                                reopen_comment = st.text_input("Reason for Reopening *", placeholder="e.g. Issue reoccurred after reboot", key=f"reopen_text_{t.ticket_id}")
                                if st.form_submit_button("🔄 Reopen Ticket", use_container_width=True):
                                    if reopen_comment.strip():
                                        ticket_repo.update_status(t.ticket_id, "REOPENED", user_id=user.user_id, comment=reopen_comment.strip())
                                        st.success("Ticket has been reopened and returned to the support queue.")
                                        st.rerun()
                                    else:
                                        st.error("Please enter a reason before reopening.")

                    elif t.status == "CLOSED":
                        st.caption("🔒 This ticket has been completed and closed.")
                        with st.expander("Need to reopen this closed ticket?"):
                            reopen_comment_closed = st.text_input("Reason for reopening:", key=f"reopen_closed_txt_{t.ticket_id}")
                            if st.button("🔄 Reopen Closed Ticket", key=f"reopen_closed_btn_{t.ticket_id}"):
                                if reopen_comment_closed.strip():
                                    ticket_repo.update_status(t.ticket_id, "REOPENED", user_id=user.user_id, comment=reopen_comment_closed.strip())
                                    st.success("Ticket has been reopened.")
                                    st.rerun()
                                else:
                                    st.warning("Please provide a reason.")

                    # Comments thread
                    st.markdown("##### 💬 Conversation & Updates")
                    full_ticket = ticket_repo.get_by_id(t.ticket_id)
                    if full_ticket.comments:
                        for c in full_ticket.comments:
                            if not c.is_internal:
                                author = c.user.username if c.user else "User"
                                st.markdown(f"""
                                <div class="comment-bubble">
                                    <div style="font-size:0.75rem; color:#64748B; margin-bottom:4px;">
                                        <strong>{author}</strong> • {c.created_at.strftime('%b %d, %H:%M')}
                                    </div>
                                    <div style="font-size:0.88rem;">{c.comment_text}</div>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.caption("No messages yet.")

                    # Add new comment
                    with st.form(key=f"comment_form_{t.ticket_id}", clear_on_submit=True):
                        new_comment = st.text_area("Reply / Add info", height=70, placeholder="Type your message...")
                        if st.form_submit_button("Post Reply"):
                            if new_comment.strip():
                                ticket_repo.add_comment(t.ticket_id, user.user_id, new_comment.strip(), is_internal=False)
                                st.success("Reply added!")
                                st.rerun()
