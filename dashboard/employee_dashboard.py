import os
import streamlit as st
import pandas as pd
from datetime import datetime
from core.repositories import (
    TicketRepository, DepartmentRepository, CategoryRepository, EmployeeRepository
)
from core.auth import SessionManager
from core.logger import log_audit, log_error
from dashboard.ui_components import (
    render_kpi_card, get_status_badge, get_priority_badge, get_sla_status_badge, render_ticket_progress_stepper
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _save_uploaded_file(uploaded_file) -> str:
    """Save an uploaded file to the local uploads directory and return its path."""
    if uploaded_file is None:
        return ""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    clean_name = f"{timestamp}_{uploaded_file.name.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, clean_name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return clean_name

def auto_triage_issue(title: str, description: str, category_names: list) -> dict:
    """Rule-based smart NLP keyword analyzer for auto-suggesting category and priority."""
    combined = f"{title} {description}".lower()
    
    # Priority triage
    suggested_prio = "Medium"
    prio_keywords_found = []
    
    critical_words = [
        "outage", "entire team", "production down", "down", "blocker", "emergency", 
        "all users", "breach", "malware", "ransomware", "bsod", "critical", "data loss", "server crash"
    ]
    high_words = [
        "cannot work", "deadline", "urgent", "broken", "failed", "blocked", 
        "asap", "phishing", "locked out", "vpn disconnected", "no internet", "drops"
    ]
    low_words = ["question", "how to", "training", "minor", "typo", "suggestion", "enhancement", "when possible"]

    for w in critical_words:
        if w in combined:
            suggested_prio = "Critical"
            prio_keywords_found.append(w)
            break
            
    if suggested_prio == "Medium":
        for w in high_words:
            if w in combined:
                suggested_prio = "High"
                prio_keywords_found.append(w)
                break

    if suggested_prio == "Medium":
        for w in low_words:
            if w in combined:
                suggested_prio = "Low"
                prio_keywords_found.append(w)
                break

    # Category triage keyword mappings
    cat_rules = {
        "Access & Authentication": ["password", "login", "auth", "mfa", "2fa", "locked", "credentials", "sso", "reset", "active directory", "account", "unlock", "permission", "access denied"],
        "Network & Connectivity": ["vpn", "wifi", "wi-fi", "internet", "dns", "gateway", "disconnection", "packet", "latency", "ping", "network", "firewall", "ethernet", "router", "connection drop", "drops"],
        "Hardware & Peripherals": ["monitor", "keyboard", "mouse", "laptop", "battery", "charger", "screen", "fan", "printer", "headset", "dock", "usb", "boot", "hdmi", "cable", "overheating"],
        "Security & Compliance": ["phishing", "suspicious email", "virus", "malware", "certificate expired", "breach", "security incident", "compromised", "hacked", "unauthorized"],
        "Cloud & Infrastructure": ["aws", "azure", "docker", "kubernetes", "k8s", "ec2", "s3", "vm", "virtual machine", "server", "linux", "cloud", "provision", "database", "postgres", "mysql"],
        "Software & Applications": ["crash", "outlook", "excel", "teams", "slack", "zoom", "install", "license", "error", "bug", "app", "upgrade", "freeze", "hang", "git", "vscode", "pycharm"]
    }
    
    best_cat = None
    max_matches = 0
    cat_keywords_found = []

    for cat_name, keywords in cat_rules.items():
        matches = [kw for kw in keywords if kw in combined]
        if len(matches) > max_matches:
            max_matches = len(matches)
            best_cat = cat_name
            cat_keywords_found = matches

    return {
        "suggested_category": best_cat if best_cat in category_names else category_names[0] if category_names else None,
        "suggested_priority": suggested_prio,
        "cat_keywords": cat_keywords_found,
        "prio_keywords": prio_keywords_found,
        "is_confident": (max_matches > 0 or len(prio_keywords_found) > 0)
    }

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

    # Tabs: My Tickets vs Submit New Ticket vs Self-Service Knowledge Base
    tab_view, tab_create, tab_kb = st.tabs(["📂 My Tickets", "➕ Raise a New Helpdesk Ticket", "💡 Self-Service Knowledge Base"])

    with tab_create:
        st.markdown("#### 📝 Submit Support Request")
        categories = cat_repo.get_all()
        departments = dept_repo.get_all()
        cat_options = {c.name: c.category_id for c in categories}
        cat_names_list = list(cat_options.keys())

        sla_hints = {
            "Critical": "🚨 **Critical**: Target Response within **15 mins** | Target Resolution within **2 hours**",
            "High": "⚡ **High**: Target Response within **30 mins** | Target Resolution within **4 hours**",
            "Medium": "🕒 **Medium**: Target Response within **2 hours** | Target Resolution within **8 hours**",
            "Low": "🌱 **Low**: Target Response within **4 hours** | Target Resolution within **24 hours**"
        }

        col_left, col_right = st.columns([3, 2])
        with col_left:
            title = st.text_input("Summary / Subject *", placeholder="e.g. VPN connection drops or Outlook error...", key="emp_new_title")
            description = st.text_area("Detailed Problem Description *", placeholder="Include error messages, device hostname or steps to reproduce...", height=110, key="emp_new_desc")

            # Real-time Smart NLP Auto-Triage
            triage_info = auto_triage_issue(title, description, cat_names_list)
            
            if triage_info["is_confident"]:
                matched_kw = triage_info["cat_keywords"] + triage_info["prio_keywords"]
                st.markdown(f"""
                <div style="background-color: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 8px; padding: 8px 12px; margin-bottom: 12px; font-size: 0.85rem;">
                    🤖 <strong>Smart Triage Suggested:</strong> 
                    <span style="color:#4F46E5; font-weight:600;">{triage_info['suggested_category']}</span> 
                    (Priority: <strong>{triage_info['suggested_priority']}</strong>) 
                    <span style="color:#64748B; font-size:0.78rem;">• Matched: <em>{', '.join(matched_kw)}</em></span>
                </div>
                """, unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                # Determine default category index based on smart triage
                default_cat_idx = 0
                if triage_info["suggested_category"] in cat_names_list:
                    default_cat_idx = cat_names_list.index(triage_info["suggested_category"])
                selected_cat_name = st.selectbox("Issue Category", cat_names_list, index=default_cat_idx, key="emp_new_cat")
                selected_cat_id = cat_options[selected_cat_name]

            with col_b:
                prio_list = ["Low", "Medium", "High", "Critical"]
                default_prio_idx = prio_list.index(triage_info["suggested_priority"]) if triage_info["suggested_priority"] in prio_list else 1
                priority = st.selectbox("Urgency / Priority", prio_list, index=default_prio_idx, key="emp_new_prio")

            uploaded_file = st.file_uploader("📎 Attach Screenshot or Log File (Optional)", type=["png", "jpg", "jpeg", "pdf", "log", "txt"], key="emp_new_attach")

            if st.button("🚀 Submit Ticket", use_container_width=True, type="primary", key="emp_btn_submit"):
                if not title.strip() or not description.strip():
                    st.error("Please provide both a summary title and detailed description.")
                else:
                    try:
                        final_desc = description.strip()
                        if uploaded_file:
                            saved_name = _save_uploaded_file(uploaded_file)
                            final_desc += f"\n\n[📎 Attachment: {saved_name}]"

                        new_ticket = ticket_repo.create_ticket(
                            employee_id=employee.employee_id,
                            department_id=employee.department_id,
                            category_id=selected_cat_id,
                            title=title.strip(),
                            description=final_desc,
                            priority=priority,
                            user_id=user.user_id
                        )
                        st.success(f"🎉 Ticket **#{new_ticket.ticket_number}** created successfully! Target deadline: {new_ticket.resolution_deadline.strftime('%Y-%m-%d %H:%M')}")
                        st.rerun()
                    except Exception as e:
                        log_error("Employee ticket creation failed", e)
                        st.error(f"Failed to create ticket: {str(e)}")

        with col_right:
            st.markdown("##### ⏱️ SLA Target Guarantee")
            st.info(sla_hints.get(priority, "Target Response: 2h | Target Resolution: 8h"))
            st.markdown("""
            **💡 Smart Triage Assistant:**
            - Category and urgency are automatically analyzed as you type your summary.
            - Keywords like `VPN`, `Blue screen`, `Password`, `Database`, `Outage` trigger auto-tagging.
            - You can manually override the category and urgency at any time.
            """)

    with tab_kb:
        st.markdown("#### 💡 Instant Self-Help & Frequently Asked Questions")
        st.caption("Try these quick steps before raising a ticket:")
        
        with st.expander("🔑 Password Reset & MFA Recovery"):
            st.write("""
            1. Visit **https://auth.company.internal/reset** on your phone or workstation.
            2. Enter your corporate email ID and request a 6-digit verification code.
            3. If your authenticator app is locked, contact the Identity & Access team.
            """)

        with st.expander("🌐 VPN & Network Disconnection Issues"):
            st.write("""
            1. Flush DNS cache via terminal: `ipconfig /flushdns` (Windows) or `dscacheutil -flushcache` (macOS).
            2. Toggle Wi-Fi off for 10 seconds and reconnect.
            3. Verify that your GlobalProtect or Cisco AnyConnect client is updated to v5.2+.
            """)

        with st.expander("💻 Software Installation & License Activation"):
            st.write("""
            1. Open Company Software Portal from Start Menu to install pre-approved software.
            2. For Adobe CC or JetBrains licenses, submit a 'Software & Applications' ticket with manager approval note.
            """)

    with tab_view:
        st.markdown("#### 📋 Ticket History & Tracking")

        # Filters
        f_col1, f_col2, f_col3 = st.columns([3, 1, 1])
        with f_col1:
            search = st.text_input("🔍 Search tickets", placeholder="Search by title, number or keyword...", key="emp_search_filter")
        with f_col2:
            status_filter = st.selectbox("Status", ["All", "OPEN", "ASSIGNED", "IN PROGRESS", "RESOLVED", "CLOSED", "REOPENED"], key="emp_stat_filter")
        with f_col3:
            prio_filter = st.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"], key="emp_prio_filter")

        filtered = [
            t for t in tickets
            if (status_filter == "All" or t.status == status_filter) and
               (prio_filter == "All" or t.priority == prio_filter) and
               (not search or search.lower() in t.title.lower() or search.lower() in t.ticket_number.lower())
        ]

        if not filtered:
            st.info("No matching tickets found.")
        else:
            # Single-open accordion selector
            ticket_options = {f"#{t.ticket_number} — {t.title} ({t.status})": t.ticket_id for t in filtered}
            
            # Default to first ticket if not set or invalid
            if "active_emp_ticket_id" not in st.session_state or st.session_state["active_emp_ticket_id"] not in ticket_options.values():
                st.session_state["active_emp_ticket_id"] = filtered[0].ticket_id

            # Quick selector that automatically opens one ticket and closes all others
            selected_label = st.selectbox(
                "🎯 Select Ticket to View / Expand:",
                list(ticket_options.keys()),
                index=list(ticket_options.values()).index(st.session_state["active_emp_ticket_id"]),
                key="emp_ticket_picker"
            )
            st.session_state["active_emp_ticket_id"] = ticket_options[selected_label]

            for t in filtered:
                is_res = t.status in ("RESOLVED", "CLOSED")
                is_currently_open = (t.ticket_id == st.session_state["active_emp_ticket_id"])
                
                with st.expander(f"**#{t.ticket_number}** — {t.title} | {t.status} ({t.priority})", expanded=is_currently_open):
                    # 1. Visual Progress Stepper
                    st.markdown(render_ticket_progress_stepper(t.status), unsafe_allow_html=True)

                    col_t1, col_t2 = st.columns([2, 1])
                    with col_t1:
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

                        st.caption(f"**Category:** {t.category.name} | **Created:** {t.created_at.strftime('%Y-%m-%d %H:%M')}")
                        if t.assigned_agent:
                            st.caption(f"**Assigned Agent:** {t.assigned_agent.full_name} ({t.team.name if t.team else 'General Support'})")

                    with col_t2:
                        st.markdown(f"**Status:** {get_status_badge(t.status)}", unsafe_allow_html=True)
                        st.markdown(f"**Priority:** {get_priority_badge(t.priority)}", unsafe_allow_html=True)
                        st.markdown(f"**SLA:** {get_sla_status_badge(t.resolution_deadline, is_res, t.resolved_at)}", unsafe_allow_html=True)
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
                                c_text = c.comment_text
                                c_attach = None
                                if "[📎 Attachment: " in c_text:
                                    c_parts = c_text.split("[📎 Attachment: ")
                                    c_text = c_parts[0].strip()
                                    c_attach = c_parts[1].replace("]", "").strip()

                                st.markdown(f"""
                                <div class="comment-bubble">
                                    <div style="font-size:0.75rem; color:#64748B; margin-bottom:4px;">
                                        <strong>{author}</strong> • {c.created_at.strftime('%b %d, %H:%M')}
                                    </div>
                                    <div style="font-size:0.88rem;">{c_text}</div>
                                </div>
                                """, unsafe_allow_html=True)

                                if c_attach:
                                    c_full_path = os.path.join(UPLOAD_DIR, c_attach)
                                    if os.path.exists(c_full_path) and c_attach.lower().endswith((".png", ".jpg", ".jpeg")):
                                        st.image(c_full_path, caption=f"Attachment: {c_attach}", width=300)
                    else:
                        st.caption("No messages yet.")

                    # Add new comment
                    with st.expander("💬 Post Reply / Additional Information"):
                        new_comment = st.text_area("Reply message", height=70, placeholder="Type your message...", key=f"emp_reply_txt_{t.ticket_id}")
                        c_upload = st.file_uploader("📎 Attach Screenshot (Optional)", type=["png", "jpg", "jpeg", "pdf", "log", "txt"], key=f"emp_reply_file_{t.ticket_id}")
                        if st.button("Post Reply", key=f"emp_reply_btn_{t.ticket_id}", type="primary"):
                            if new_comment.strip() or c_upload:
                                post_msg = new_comment.strip() if new_comment.strip() else "Attached screenshot/log file"
                                if c_upload:
                                    c_saved = _save_uploaded_file(c_upload)
                                    post_msg += f"\n\n[📎 Attachment: {c_saved}]"
                                ticket_repo.add_comment(t.ticket_id, user.user_id, post_msg, is_internal=False)
                                st.success("Reply added!")
                                st.rerun()

