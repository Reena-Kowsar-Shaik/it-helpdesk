import time
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

# Streamlit Page Configuration
st.set_page_config(
    page_title="ServiceDesk Pro | Enterprise IT & SLA Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Imports
import config
from database.connection import db_manager
from database import queries
from database.sql_analytics import SQL_QUERIES_CATALOG
from services.auth_service import AuthService
from services.ticket_service import TicketService
from services.sla_service import SLAService
from services.analytics_service import AnalyticsService
from services.ai_service import AIAssistantService
from services.kb_service import KBService
from services.export_service import ExportService
from utils.helpers import render_status_badge, render_priority_badge, render_sla_chip, render_metric_card

# Load CSS
css_file = config.BASE_DIR / "assets" / "style.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Session State Initialization
if "user" not in st.session_state:
    default_user = AuthService.login("admin@enterprise.com", "admin123")
    st.session_state.user = default_user or {
        "user_id": 1, "full_name": "Admin Root", "email": "admin@enterprise.com",
        "role": "IT Admin", "department_name": "Software Engineering"
    }

if "selected_ticket_id" not in st.session_state:
    st.session_state.selected_ticket_id = None

# ==========================================================
# SIDEBAR: PORTAL SELECTOR, USER PROFILE & SUB-NAVIGATION
# ==========================================================
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #f1f5f9;">
            <div style="background:#2563eb; width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:18px; color:#ffffff;">🛡️</div>
            <div>
                <h3 style="margin:0; font-size:1.15rem; font-weight:800; color:#0f172a; letter-spacing:-0.02em;">ServiceDesk <span style="color:#2563eb;">PRO</span></h3>
                <p style="margin:0; font-size:0.72rem; color:#64748b; font-weight:500;">Enterprise IT & SLA Suite</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Database Status Indicator
    db_info = db_manager.get_db_info()
    db_color = "#059669" if db_info["type"] == "MYSQL" else "#d97706"
    st.markdown(f"""
        <div style="padding:6px 10px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; font-size:0.72rem; margin-bottom:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#64748b; font-weight:600; text-transform:uppercase; font-size:0.62rem;">Active Engine:</span>
                <span style="font-weight:700; color:{db_color}; font-family:'JetBrains Mono', monospace;">● {db_info['type']}</span>
            </div>
            <div style="color:#334155; font-family:'JetBrains Mono', monospace; font-size:0.65rem; margin-top:1px;">DB: {db_info['database']}</div>
        </div>
    """, unsafe_allow_html=True)

    # Active User Profile Card
    curr_user = st.session_state.user
    st.markdown(f"""
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:8px 12px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; color:#0f172a; font-size:0.82rem;">👤 {curr_user['full_name']}</span>
                <span style="background:#eff6ff; color:#2563eb; border:1px solid #bfdbfe; padding:1px 6px; border-radius:4px; font-size:0.65rem; font-weight:700;">{curr_user['role']}</span>
            </div>
            <div style="font-size:0.68rem; color:#64748b; margin-top:2px;">{curr_user['email']}</div>
        </div>
    """, unsafe_allow_html=True)

    # Quick Switcher
    st.markdown("<p style='font-size:0.68rem; font-weight:700; color:#64748b; margin-bottom:4px; text-transform:uppercase;'>⚡ Role Switcher</p>", unsafe_allow_html=True)
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("👑 Admin", use_container_width=True):
            st.session_state.user = AuthService.login("admin@enterprise.com", "admin123")
            st.rerun()
        if st.button("🛠️ Agent", use_container_width=True):
            st.session_state.user = AuthService.login("alice.chen@enterprise.com", "admin123")
            st.rerun()
    with col_r2:
        if st.button("📈 Exec", use_container_width=True):
            st.session_state.user = AuthService.login("cio@enterprise.com", "admin123")
            st.rerun()
        if st.button("💼 Employee", use_container_width=True):
            st.session_state.user = AuthService.login("michael.s@enterprise.com", "admin123")
            st.rerun()

    st.divider()

    # PRIMARY PORTAL SELECTOR
    st.markdown("<p style='font-size:0.75rem; font-weight:800; color:#1e293b; margin-bottom:6px; text-transform:uppercase; letter-spacing:0.04em;'>🌐 Select Portal Workspace</p>", unsafe_allow_html=True)
    active_portal = st.radio(
        "WORKSPACE",
        [
            "👤 Employee Portal",
            "🛠️ IT Specialist Portal",
            "💡 Lifecycle & Innovations"
        ],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # Contextual Sub-Navigation based on Selected Portal
    if active_portal == "👤 Employee Portal":
        st.markdown("<p style='font-size:0.7rem; font-weight:700; color:#64748b; margin-bottom:4px; text-transform:uppercase;'>Employee Views</p>", unsafe_allow_html=True)
        emp_nav = st.radio(
            "EMP_NAV",
            [
                "➕ Raise Ticket",
                "📋 My Submitted Tickets",
                "📚 Knowledge Base"
            ],
            index=0,
            label_visibility="collapsed"
        )
    elif active_portal == "🛠️ IT Specialist Portal":
        st.markdown("<p style='font-size:0.7rem; font-weight:700; color:#64748b; margin-bottom:4px; text-transform:uppercase;'>IT Operations Views</p>", unsafe_allow_html=True)
        it_nav = st.radio(
            "IT_NAV",
            [
                "📊 Overview & KPIs",
                "🎯 Resolution Hub",
                "⏱️ SLA Matrix",
                "📈 SQL Analytics",
                "🔍 SQL Studio",
                "📑 Export Reports",
                "⚙️ Settings"
            ],
            index=1,
            label_visibility="collapsed"
        )
    else:
        st.markdown("<p style='font-size:0.7rem; font-weight:700; color:#64748b; margin-bottom:4px; text-transform:uppercase;'>System Showcase</p>", unsafe_allow_html=True)
        showcase_nav = st.radio(
            "SHOW_NAV",
            [
                "🚀 How Tickets Are Raised & Solved",
                "💡 What We Improved Over Existing"
            ],
            index=0,
            label_visibility="collapsed"
        )

    st.markdown("---")
    st.caption("ServiceDesk Pro v2.4 • Clean SaaS Architecture")


# ==========================================================
# ==========================================================
# 1. EMPLOYEE PORTAL
# ==========================================================
# ==========================================================
if active_portal == "👤 Employee Portal":

    # ------------------------------------------------------
    # 1.1 RAISE TICKET
    # ------------------------------------------------------
    if emp_nav == "➕ Raise Ticket":
        st.markdown("""
            <div class="saas-header">
                <div>
                    <h1 class="saas-title">➕ Raise Support Ticket // AI Assisted</h1>
                    <p class="saas-subtitle">
                        Describe your issue. Our AI engine will auto-triage the priority, match self-service solutions, and auto-route to the least-loaded engineer.
                    </p>
                </div>
                <div>
                    <span style="background:#eff6ff; color:#2563eb; border:1px solid #bfdbfe; padding:6px 14px; border-radius:9999px; font-size:0.75rem; font-weight:700;">👤 Employee Self-Service</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_form, col_ai = st.columns([6, 4])

        with col_form:
            st.markdown("### 📝 Incident Information")
            new_title = st.text_input("Incident Title *", placeholder="e.g. Cannot access VPN or AWS Staging servers from home network")
            new_desc = st.text_area("Detailed Problem Description *", height=140, placeholder="Explain the symptoms, error messages, when it started, and impact on your work...")

            ai_suggestion = AIAssistantService.analyze_incident(f"{new_title} {new_desc}")

            c_p1, c_p2 = st.columns(2)
            with c_p1:
                cat_default_idx = config.CATEGORIES.index(ai_suggestion["recommended_category"]) if ai_suggestion["recommended_category"] in config.CATEGORIES else 0
                selected_cat = st.selectbox("Category", config.CATEGORIES, index=cat_default_idx)

                depts = db_manager.execute_query("SELECT department_id, name FROM departments;")
                dept_map = {d["name"]: d["department_id"] for d in depts}
                user_dept = st.session_state.user.get("department_name", "Software Engineering")
                default_dept_idx = list(dept_map.keys()).index(user_dept) if user_dept in dept_map else 0
                selected_dept = st.selectbox("Your Department", list(dept_map.keys()), index=default_dept_idx)

            with c_p2:
                prio_default_idx = config.PRIORITIES.index(ai_suggestion["recommended_priority"]) if ai_suggestion["recommended_priority"] in config.PRIORITIES else 2
                selected_prio = st.selectbox("Priority Level", config.PRIORITIES, index=prio_default_idx)

                auto_assign_toggle = st.checkbox("Intelligent Auto-Routing (Assign to least-loaded agent)", value=True)

            if st.button("🚀 Submit Support Ticket", type="primary", use_container_width=True):
                if not new_title.strip() or not new_desc.strip():
                    st.error("Please provide both an incident title and description.")
                else:
                    dept_id = dept_map.get(selected_dept, 1)
                    res = TicketService.create_ticket(
                        title=new_title,
                        description=new_desc,
                        category=selected_cat,
                        priority=selected_prio,
                        requester_id=st.session_state.user["user_id"],
                        department_id=dept_id,
                        auto_assign=auto_assign_toggle
                    )
                    if res["success"]:
                        st.success(f"🎉 Ticket **{res['ticket_number']}** created and routed successfully!")
                        st.balloons()
                    else:
                        st.error(f"Failed to create ticket: {res.get('error')}")

        with col_ai:
            st.markdown("### 🤖 Real-Time AI Triage & Assist")
            if new_title or new_desc:
                st.markdown(f"""
                <div style="background:#ffffff; border:1px solid #bfdbfe; border-radius:12px; padding:16px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <div style="font-weight:700; color:#2563eb; margin-bottom:8px; font-size:0.9rem;">⚡ Auto-Triage Assessment:</div>
                    <div style="font-size:0.85rem; color:#1e293b; line-height:1.7;">
                        • <b>Predicted Priority:</b> {render_priority_badge(ai_suggestion['recommended_priority'])}<br>
                        • <b>Target SLA:</b> <span style="font-weight:700; color:#059669;">{ai_suggestion['target_resolution_hours']} Hours</span><br>
                        • <b>Detected Category:</b> <span style="color:#2563eb; font-weight:600;">{ai_suggestion['recommended_category']}</span><br>
                        • <b>Urgency Assessment:</b> <span style="color:#dc2626; font-weight:600;">{ai_suggestion['urgency']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                similar_tickets = AIAssistantService.find_similar_tickets(f"{new_title} {new_desc}")
                if similar_tickets:
                    st.markdown("**🔍 Similar Past Issues & Solutions:**")
                    for st_item in similar_tickets[:2]:
                        st.markdown(f"""
                        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px; margin-bottom:8px;">
                            <div style="display:flex; justify-content:space-between; font-size:0.75rem;">
                                <span style="font-weight:700; color:#2563eb; font-family:'JetBrains Mono', monospace;">{st_item['ticket_number']}</span>
                                <span style="color:#059669; font-weight:700;">{st_item.get('similarity_score', 0)}% Match</span>
                            </div>
                            <div style="font-size:0.85rem; font-weight:600; color:#0f172a; margin:2px 0;">{st_item['title']}</div>
                            <div style="font-size:0.75rem; color:#64748b;"><b>Past Fix:</b> {st_item.get('resolution_notes') or 'Standard remediation applied'}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("💡 As you type the title or description, AI will instantly evaluate the urgency, calculate SLA limits, and show matching fixes.")

    # ------------------------------------------------------
    # 1.2 MY SUBMITTED TICKETS & LIVE TRACKING
    # ------------------------------------------------------
    elif emp_nav == "📋 My Submitted Tickets":
        st.markdown("""
            <div class="saas-header">
                <div>
                    <h1 class="saas-title">📋 My Tickets & Live Resolution Tracking</h1>
                    <p class="saas-subtitle">
                        Track your submitted incidents, monitor real-time progress, communicate with support agents, and rate your experience upon resolution.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        user_id = st.session_state.user["user_id"]
        my_tickets = db_manager.execute_query("""
            SELECT t.ticket_id, t.ticket_number, t.title, t.priority, t.status, t.created_at, t.sla_due_date,
                   u_agent.full_name as agent_name, st.team_name, t.satisfaction_rating
            FROM tickets t
            LEFT JOIN agents a ON t.assigned_agent_id = a.agent_id
            LEFT JOIN users u_agent ON a.user_id = u_agent.user_id
            LEFT JOIN support_teams st ON t.support_team_id = st.team_id
            WHERE t.requester_id = :uid
            ORDER BY t.created_at DESC;
        """, {"uid": user_id})

        if not my_tickets:
            st.info("You haven't submitted any tickets yet. Click **➕ Raise Ticket** to submit an issue!")
        else:
            col_tlist, col_tdetail = st.columns([5, 5])
            with col_tlist:
                st.markdown(f"**Your Tickets ({len(my_tickets)} total):**")
                for t in my_tickets:
                    t_id = t["ticket_id"]
                    is_sel = (st.session_state.selected_ticket_id == t_id)
                    card_border = "#2563eb" if is_sel else "#e2e8f0"
                    bg_col = "#f8fafc" if is_sel else "#ffffff"

                    st.markdown(f"""
                    <div style="background:{bg_col}; border:1.5px solid {card_border}; border-radius:10px; padding:12px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:800; color:#2563eb; font-family:'JetBrains Mono', monospace; font-size:0.88rem;">{t['ticket_number']}</span>
                            <div>
                                {render_priority_badge(t['priority'])}
                                {render_status_badge(t['status'])}
                            </div>
                        </div>
                        <div style="font-weight:700; color:#0f172a; font-size:0.92rem; margin:6px 0;">{t['title']}</div>
                        <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#64748b;">
                            <span>👨‍💻 Agent: {t['agent_name'] or 'Auto-routing queue'}</span>
                            <span>📅 {t['created_at'][:16] if t['created_at'] else ''}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"View Status #{t['ticket_number']}", key=f"emp_btn_{t_id}", use_container_width=True):
                        st.session_state.selected_ticket_id = t_id
                        st.rerun()

            with col_tdetail:
                if st.session_state.selected_ticket_id:
                    ticket = TicketService.get_ticket_details(st.session_state.selected_ticket_id)
                    if ticket:
                        sla_info = SLAService.get_sla_status(ticket)

                        # Status Step Progress Indicator
                        st_steps = ["Open", "Assigned", "In Progress", "Resolved", "Closed"]
                        curr_step_idx = st_steps.index(ticket["status"]) if ticket["status"] in st_steps else 0
                        
                        st.markdown(f"""
                        <div style="background:#ffffff; border:1px solid #bfdbfe; border-radius:12px; padding:18px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                <span style="font-size:1.2rem; font-weight:800; color:#2563eb; font-family:'JetBrains Mono', monospace;">{ticket['ticket_number']}</span>
                                <div>
                                    {render_sla_chip(sla_info)}
                                    {render_status_badge(ticket['status'])}
                                </div>
                            </div>
                            <h3 style="margin:0 0 8px 0; font-size:1.1rem; color:#0f172a;">{ticket['title']}</h3>
                            <p style="background:#f8fafc; padding:10px; border-radius:6px; font-size:0.85rem; color:#334155; border:1px solid #e2e8f0;">{ticket['description']}</p>
                            
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.75rem; color:#64748b; margin-top:10px;">
                                <div>📁 Category: <b>{ticket['category']}</b></div>
                                <div>👨‍💻 Assigned Specialist: <b>{ticket['agent_name'] or 'Pending Triage'}</b></div>
                                <div>📅 Logged: <b>{ticket['created_at']}</b></div>
                                <div>⏳ SLA Due Date: <b>{ticket['sla_due_date']}</b></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # If Resolved, display Resolution & CSAT Rating
                        if ticket["status"] in ["Resolved", "Closed"]:
                            st.markdown(f"""
                            <div style="background:#ecfdf5; border:1px solid #a7f3d0; border-radius:10px; padding:12px; margin-bottom:12px;">
                                <div style="font-weight:700; color:#059669; font-size:0.9rem;">✅ Incident Resolved by Engineer</div>
                                <div style="font-size:0.82rem; color:#065f46; margin-top:4px;"><b>Resolution Summary:</b> {ticket.get('resolution_notes') or 'Technical remediation completed.'}</div>
                                <div style="font-size:0.78rem; color:#047857; margin-top:2px;"><b>Root Cause:</b> {ticket.get('root_cause') or 'Identified and corrected'}</div>
                            </div>
                            """, unsafe_allow_html=True)

                            if not ticket.get("satisfaction_rating"):
                                st.markdown("#### ⭐ Rate Your Support Experience")
                                c_star = st.slider("Satisfaction Score (1 = Poor, 5 = Excellent)", 1, 5, 5, key=f"emp_csat_star_{ticket['ticket_id']}")
                                c_fb = st.text_input("Comments for the support engineer", placeholder="How was the response speed and resolution quality?", key=f"emp_csat_fb_{ticket['ticket_id']}")
                                if st.button("Submit CSAT Feedback ⭐", type="primary", key=f"emp_btn_sub_csat_{ticket['ticket_id']}"):
                                    TicketService.submit_feedback(ticket["ticket_id"], c_star, c_fb)
                                    st.success("Thank you for your valuable feedback!")
                                    st.rerun()
                            else:
                                st.success(f"⭐ You rated this resolution: **{ticket['satisfaction_rating']} / 5.0 Stars**")

                        # Conversation with Agent
                        st.markdown("#### 💬 Conversation with Support Team")
                        comments = ticket.get("comments", [])
                        pub_comments = [c for c in comments if c.get("comment_type") != "Internal Note"]
                        if pub_comments:
                            for c in pub_comments:
                                is_emp = (c["author_name"] == curr_user["full_name"])
                                bg_bubble = "#eff6ff" if is_emp else "#f8fafc"
                                border_bubble = "#bfdbfe" if is_emp else "#cbd5e1"
                                st.markdown(f"""
                                <div style="background:{bg_bubble}; border-left:3px solid {border_bubble}; padding:8px 12px; border-radius:6px; margin-bottom:6px;">
                                    <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#64748b;">
                                        <span style="font-weight:700; color:#0f172a;">{c['author_name']}</span>
                                        <span>{c['created_at']}</span>
                                    </div>
                                    <div style="font-size:0.85rem; color:#1e293b; margin-top:2px;">{c['message']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.caption("No messages exchanged yet.")

                        c_reply = st.text_area("Reply to the support team", height=60, placeholder="Provide extra information or ask questions...", key=f"emp_rep_{ticket['ticket_id']}")
                        if st.button("Send Message ✉️", key=f"emp_btn_send_{ticket['ticket_id']}"):
                            if c_reply.strip():
                                TicketService.add_comment(ticket["ticket_id"], curr_user["user_id"], c_reply, "Public")
                                st.success("Message sent to the support engineer!")
                                st.rerun()
                else:
                    st.info("👈 Select any of your tickets from the left list to track live progress and message the engineer.")

    # ------------------------------------------------------
    # 1.3 KNOWLEDGE BASE
    # ------------------------------------------------------
    elif emp_nav == "📚 Knowledge Base":
        st.markdown("""
            <div class="saas-header">
                <div>
                    <h1 class="saas-title">📚 Self-Service Knowledge Base & Solutions</h1>
                    <p class="saas-subtitle">
                        Search curated IT guides, network configurations, password resets, and verified technical remediations.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        kb_search = st.text_input("🔍 Search Knowledge Base", placeholder="e.g. VPN, Docker, PostgreSQL, Email Setup...")
        kb_articles = KBService.get_articles(search=kb_search if kb_search else None)

        if kb_articles:
            for art in kb_articles:
                with st.expander(f"📄 [{art['category']}] {art['title']}"):
                    st.markdown(art['content'])
                    st.markdown(f"<div style='font-size:0.75rem; color:#64748b; margin-top:8px;'>Tags: <code>{art['tags']}</code> | Helpful votes: <b>{art['helpful_votes']}</b></div>", unsafe_allow_html=True)
                    if st.button("👍 Mark as Helpful", key=f"kb_vote_{art['article_id']}"):
                        KBService.mark_helpful(art['article_id'])
                        st.success("Thank you for your feedback!")
                        st.rerun()
        else:
            st.info("No knowledge base articles found matching your query.")


# ==========================================================
# ==========================================================
# 2. IT SPECIALIST & ADMIN PORTAL
# ==========================================================
# ==========================================================
elif active_portal == "🛠️ IT Specialist Portal":

    # ------------------------------------------------------
    # 2.1 OVERVIEW & KPIS
    # ------------------------------------------------------
    if it_nav == "📊 Overview & KPIs":
        st.markdown("""
            <div class="saas-header">
                <div>
                    <h1 class="saas-title">Executive Operations & SLA Telemetry</h1>
                    <p class="saas-subtitle">
                        Real-time relational SQL telemetry, SLA compliance, resolution velocity, and department workload.
                    </p>
                </div>
                <div>
                    <span style="background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; padding:5px 12px; border-radius:9999px; font-size:0.75rem; font-weight:700;">● Engine Online</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        kpis = AnalyticsService.get_kpi_summary()

        # 6 Metric Cards
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            render_metric_card("Total Tickets", str(kpis.get("total_tickets", 0)), "All-time logged", "+14% MoM", "#0284c7", "🎫", "#f0f9ff")
        with c2:
            open_load = int(kpis.get("open_tickets", 0)) + int(kpis.get("assigned_tickets", 0)) + int(kpis.get("in_progress_tickets", 0))
            render_metric_card("Active Backlog", str(open_load), "Pending triage", "Active triage", "#d97706", "⚡", "#fffbeb")
        with c3:
            render_metric_card("Resolved", str(kpis.get("resolved_tickets", 0)), "Successfully closed", "89.2% rate", "#059669", "✅", "#ecfdf5")
        with c4:
            sla_pct = kpis.get("sla_compliance_pct", 100) or 100
            render_metric_card("SLA Compliance", f"{sla_pct}%", "Target: ≥90%", "Within Target", "#059669" if sla_pct >= 90 else "#dc2626", "⏱️", "#ecfdf5" if sla_pct >= 90 else "#fef2f2")
        with c5:
            render_metric_card("SLA Breaches", str(kpis.get("sla_breached_count", 0)), "Overdue incidents", "Attention req.", "#dc2626", "🚨", "#fef2f2")
        with c6:
            csat = kpis.get("avg_csat_score", 4.8) or 4.8
            render_metric_card("CSAT Rating", f"{csat} / 5.0", "Employee feedback", "★ ★ ★ ★ ★", "#d97706", "⭐", "#fffbeb")

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        # Visuals Row 1
        col_g1, col_g2 = st.columns([6, 4])
        with col_g1:
            st.markdown("""
            <div class="widget-card-header" style="margin-bottom:8px;">
                <span class="widget-card-title">📈 Monthly Volume & Resolution Velocity</span>
            </div>
            """, unsafe_allow_html=True)
            trend_df = AnalyticsService.get_monthly_trends()
            if not trend_df.empty:
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Bar(
                    x=trend_df["month_year"], y=trend_df["total_created"],
                    name="Created", marker=dict(color="#3b82f6")
                ))
                fig_trend.add_trace(go.Bar(
                    x=trend_df["month_year"], y=trend_df["total_resolved"],
                    name="Resolved", marker=dict(color="#10b981")
                ))
                fig_trend.add_trace(go.Scatter(
                    x=trend_df["month_year"], y=trend_df["sla_breaches"],
                    name="SLA Breaches", mode="lines+markers", line=dict(color="#ef4444", width=2.5)
                ))
                fig_trend.update_layout(
                    barmode='group', template="plotly_white",
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=15, t=10, b=20), height=260,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
                    yaxis=dict(showgrid=True, gridcolor="#f1f5f9")
                )
                st.plotly_chart(fig_trend, use_container_width=True)

        with col_g2:
            st.markdown("""
            <div class="widget-card-header" style="margin-bottom:8px;">
                <span class="widget-card-title">🏢 Department Incident Share</span>
            </div>
            """, unsafe_allow_html=True)
            dept_df = AnalyticsService.get_department_load()
            if not dept_df.empty:
                fig_donut = px.pie(
                    dept_df, values="total_requests", names="department_name",
                    hole=0.6, color_discrete_sequence=["#2563eb", "#059669", "#7c3aed", "#ea580c", "#ec4899"]
                )
                fig_donut.update_layout(
                    template="plotly_white", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=10, b=30), height=260,
                    legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5, font=dict(size=10))
                )
                st.plotly_chart(fig_donut, use_container_width=True)

    # ------------------------------------------------------
    # 2.2 RESOLUTION HUB (INVESTIGATE & SOLVE)
    # ------------------------------------------------------
    elif it_nav == "🎯 Resolution Hub":
        st.markdown("""
            <div class="saas-header">
                <div>
                    <h1 class="saas-title">🎯 Incident Resolution Hub // Specialist Queue</h1>
                    <p class="saas-subtitle">
                        Investigate issues, communicate with requesters, add internal notes, provide technical fixes, stamp root causes, and monitor SLAs.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Filter Bar
        with st.expander("🔍 Filter & Search Queue", expanded=False):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                search_query = st.text_input("Keyword Search", placeholder="Search title, ticket #, requester...")
                filter_status = st.selectbox("Status Filter", ["All Statuses"] + config.STATUSES)
            with f_col2:
                filter_priority = st.selectbox("Priority Filter", ["All Priorities"] + config.PRIORITIES)
                filter_category = st.selectbox("Category Filter", ["All Categories"] + config.CATEGORIES)
            with f_col3:
                depts = db_manager.execute_query("SELECT name FROM departments;")
                dept_names = [d["name"] for d in depts]
                filter_dept = st.selectbox("Department", ["All Departments"] + dept_names)
                only_breached = st.checkbox("🚨 Show Only SLA Breached / At-Risk", value=False)
            with f_col4:
                agents_list = db_manager.execute_query("SELECT u.full_name FROM agents a JOIN users u ON a.user_id = u.user_id;")
                agent_names = [a["full_name"] for a in agents_list]
                filter_agent = st.selectbox("Assigned Agent", ["All Agents"] + agent_names)

        # Dynamic Query
        where_clauses = ["1=1"]
        sql_params = {}
        if search_query:
            where_clauses.append("(t.title LIKE :q OR t.ticket_number LIKE :q OR u_req.full_name LIKE :q)")
            sql_params["q"] = f"%{search_query}%"
        if filter_status != "All Statuses":
            where_clauses.append("t.status = :status")
            sql_params["status"] = filter_status
        if filter_priority != "All Priorities":
            where_clauses.append("t.priority = :priority")
            sql_params["priority"] = filter_priority
        if filter_category != "All Categories":
            where_clauses.append("t.category = :category")
            sql_params["category"] = filter_category
        if filter_dept != "All Departments":
            where_clauses.append("d.name = :dept")
            sql_params["dept"] = filter_dept
        if filter_agent != "All Agents":
            where_clauses.append("u_agent.full_name = :agent")
            sql_params["agent"] = filter_agent
        if only_breached:
            where_clauses.append("(t.is_sla_breached = 1 OR (t.status NOT IN ('Resolved','Closed') AND t.sla_due_date < CURRENT_TIMESTAMP))")

        query_str = f"""
            SELECT t.ticket_id, t.ticket_number, t.title, t.category, t.priority, t.status,
                   t.created_at, t.sla_due_date, t.is_sla_breached,
                   u_req.full_name as requester_name, d.name as department_name,
                   u_agent.full_name as agent_name, st.team_name
            FROM tickets t
            LEFT JOIN users u_req ON t.requester_id = u_req.user_id
            LEFT JOIN departments d ON t.department_id = d.department_id
            LEFT JOIN agents a ON t.assigned_agent_id = a.agent_id
            LEFT JOIN users u_agent ON a.user_id = u_agent.user_id
            LEFT JOIN support_teams st ON t.support_team_id = st.team_id
            WHERE {' AND '.join(where_clauses)}
            ORDER BY
                CASE t.priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
                t.created_at DESC;
        """
        tickets_df = pd.DataFrame(db_manager.execute_query(query_str, sql_params))

        # Split-Pane View
        col_list, col_detail = st.columns([5, 5])
        with col_list:
            if tickets_df.empty:
                st.info("No tickets match the selected filters.")
            else:
                for _, row in tickets_df.iterrows():
                    t_id = row["ticket_id"]
                    is_selected = (st.session_state.selected_ticket_id == t_id)
                    card_border = "#2563eb" if is_selected else "#e2e8f0"
                    bg_col = "#eff6ff" if is_selected else "#ffffff"

                    st.markdown(f"""
                    <div style="background:{bg_col}; border:1.5px solid {card_border}; border-radius:10px; padding:12px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:800; color:#2563eb; font-size:0.88rem; font-family:'JetBrains Mono', monospace;">{row['ticket_number']}</span>
                            <div>
                                {render_priority_badge(row['priority'])}
                                {render_status_badge(row['status'])}
                            </div>
                        </div>
                        <div style="font-weight:700; color:#0f172a; font-size:0.92rem; margin-bottom:4px;">{row['title']}</div>
                        <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#64748b;">
                            <span>👤 {row['requester_name']} ({row['department_name'] or 'N/A'})</span>
                            <span>👨‍💻 Agent: {row['agent_name'] or 'Unassigned'}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Inspect #{row['ticket_number']}", key=f"btn_t_{t_id}", use_container_width=True):
                        st.session_state.selected_ticket_id = t_id
                        st.rerun()

        # Detailed Ticket Drawer
        with col_detail:
            if st.session_state.selected_ticket_id:
                ticket = TicketService.get_ticket_details(st.session_state.selected_ticket_id)
                if ticket:
                    sla_info = SLAService.get_sla_status(ticket)
                    st.markdown(f"""
                    <div style="background:#ffffff; border:1.5px solid #2563eb; border-radius:14px; padding:18px; margin-bottom:14px; box-shadow:0 4px 16px rgba(37,99,235,0.06);">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span style="font-size:1.25rem; font-weight:800; color:#2563eb; font-family:'JetBrains Mono', monospace;">{ticket['ticket_number']}</span>
                            <div>
                                {render_sla_chip(sla_info)}
                                {render_priority_badge(ticket['priority'])}
                                {render_status_badge(ticket['status'])}
                            </div>
                        </div>
                        <h3 style="color:#0f172a; margin:0 0 8px 0; font-size:1.1rem;">{ticket['title']}</h3>
                        <p style="color:#334155; font-size:0.85rem; background:#f8fafc; padding:10px; border-radius:6px; line-height:1.5; border:1px solid #e2e8f0;">{ticket['description']}</p>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.75rem; color:#64748b; margin-top:10px;">
                            <div>📁 Category: <b>{ticket['category']}</b></div>
                            <div>🏢 Dept: <b>{ticket['department_name']}</b></div>
                            <div>👤 Requester: <b>{ticket['requester_name']}</b></div>
                            <div>👨‍💻 Agent: <b>{ticket['agent_name'] or 'Unassigned'}</b></div>
                            <div>📅 Created: <b>{ticket['created_at']}</b></div>
                            <div>⏳ SLA Due: <b>{ticket['sla_due_date']}</b></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Action Bar
                    st.markdown("#### ⚡ Specialist Actions & Remediation")
                    act_col1, act_col2 = st.columns(2)
                    with act_col1:
                        new_status = st.selectbox(
                            "Transition Status",
                            config.STATUSES,
                            index=config.STATUSES.index(ticket["status"]) if ticket["status"] in config.STATUSES else 0,
                            key=f"st_sel_{ticket['ticket_id']}"
                        )
                    with act_col2:
                        res_notes = st.text_input("Resolution Notes / Fix Details", value=ticket.get("resolution_notes") or "", placeholder="e.g. Scaled connection pool & added index...", key=f"res_notes_{ticket['ticket_id']}")

                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("💾 Save Resolution & Status", type="primary", use_container_width=True, key=f"btn_apply_{ticket['ticket_id']}"):
                            TicketService.update_ticket_status(
                                ticket_id=ticket["ticket_id"],
                                new_status=new_status,
                                user_id=st.session_state.user["user_id"],
                                resolution_notes=res_notes
                            )
                            st.success(f"Status updated to '{new_status}'!")
                            st.rerun()
                    with col_b2:
                        if ticket["status"] in ["Resolved", "Closed"]:
                            if st.button("🔄 Reopen Incident", use_container_width=True, key=f"btn_reopen_{ticket['ticket_id']}"):
                                TicketService.reopen_ticket(ticket["ticket_id"], st.session_state.user["user_id"], "Reopened by engineer.")
                                st.warning("Ticket reopened!")
                                st.rerun()

                    # Conversation Thread & Internal Notes
                    st.markdown("---")
                    st.markdown("#### 💬 Communication & Internal Notes")
                    comments = ticket.get("comments", [])
                    if comments:
                        for c in comments:
                            c_type = c.get("comment_type", "Public")
                            bg_c = "#eef2ff" if c_type == "Internal Note" else "#f8fafc"
                            border_c = "#6366f1" if c_type == "Internal Note" else "#cbd5e1"
                            st.markdown(f"""
                            <div style="background:{bg_c}; border-left:3px solid {border_c}; padding:8px 12px; border-radius:6px; margin-bottom:6px;">
                                <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#64748b;">
                                    <span style="font-weight:700; color:#0f172a;">{c['author_name']} ({c['author_role']})</span>
                                    <span>{c_type} • {c['created_at']}</span>
                                </div>
                                <div style="font-size:0.85rem; color:#1e293b; margin-top:2px;">{c['message']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.caption("No messages posted yet.")

                    c_msg = st.text_area("Post a note or response", height=60, key=f"c_msg_{ticket['ticket_id']}")
                    c_type_sel = st.selectbox("Type", ["Public", "Internal Note"], key=f"c_type_{ticket['ticket_id']}")
                    if st.button("Post Message", key=f"btn_post_{ticket['ticket_id']}"):
                        if c_msg.strip():
                            TicketService.add_comment(ticket["ticket_id"], st.session_state.user["user_id"], c_msg, c_type_sel)
                            st.success("Message recorded!")
                            st.rerun()
            else:
                st.info("👈 Select any ticket from the queue on the left to inspect, diagnose, fix, and update.")

    # ------------------------------------------------------
    # 2.3 SLA MATRIX
    # ------------------------------------------------------
    elif it_nav == "⏱️ SLA Matrix":
        st.markdown("""
            <div class="saas-header">
                <div>
                    <h1 class="saas-title">SLA Compliance & Breach Matrix</h1>
                    <p class="saas-subtitle">
                        Real-time countdown timers, at-risk ticket escalations (< 2h warning), and SLA policy adjustments.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.subheader("🚨 Active Tickets At Risk or Overdue")
        at_risk_df = SLAService.get_at_risk_tickets()
        if not at_risk_df.empty:
            sla_statuses = []
            for _, r in at_risk_df.iterrows():
                info = SLAService.get_sla_status(r.to_dict())
                sla_statuses.append(info["label"])
            at_risk_df["sla_status"] = sla_statuses

            st.dataframe(
                at_risk_df[["ticket_number", "title", "priority", "status", "sla_status", "assigned_agent", "team_name"]],
                column_config={
                    "ticket_number": "Ticket #",
                    "title": "Incident Title",
                    "priority": "Priority",
                    "status": "Current Status",
                    "sla_status": "SLA Countdown",
                    "assigned_agent": "Assigned Agent",
                    "team_name": "Support Team"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.success("🎉 All active tickets are currently well within their SLA thresholds!")

        st.markdown("---")
        st.subheader("⚙️ Organization SLA Policy Configurations")
        sla_policies_df = SLAService.get_all_policies()
        st.dataframe(
            sla_policies_df,
            column_config={
                "sla_id": "Policy ID",
                "priority": "Incident Priority",
                "response_time_hours": st.column_config.NumberColumn("Target Response (Hrs)", format="%.1f h"),
                "resolution_time_hours": st.column_config.NumberColumn("Target Resolution (Hrs)", format="%.1f h"),
                "escalation_time_hours": st.column_config.NumberColumn("Escalation Trigger (Hrs)", format="%.1f h"),
                "description": "Policy Description"
            },
            hide_index=True,
            use_container_width=True
        )

    # ------------------------------------------------------
    # 2.4 SQL ANALYTICS
    # ------------------------------------------------------
    elif it_nav == "📈 SQL Analytics":
        st.markdown("""
            <div class="saas-header">
                <div>
                    <h1 class="saas-title">Advanced SQL Business Intelligence & Analytics</h1>
                    <p class="saas-subtitle">
                        SQL-Driven insights: Agent rankings with Window Functions (RANK, DENSE_RANK), Recurring Root Causes, and Department demand.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3, tab4 = st.tabs([
            "🏆 Agent Performance Scorecard (Window Functions)",
            "🔄 Recurring Problems & Root Cause (Pareto)",
            "🏢 Department Demand Matrix",
            "🔁 Reopened Ticket Defect Analysis"
        ])

        with tab1:
            st.subheader("Agent Leaderboard (SQL CTE & Window Functions)")
            agent_df = AnalyticsService.get_agent_rankings()
            if not agent_df.empty:
                st.dataframe(
                    agent_df,
                    column_config={
                        "performance_rank": st.column_config.NumberColumn("Company Rank", format="#%d 🏆"),
                        "team_rank": st.column_config.NumberColumn("Team Rank", format="#%d"),
                        "agent_name": "Agent Name",
                        "team_name": "Team",
                        "tier": "Tier",
                        "tickets_resolved": st.column_config.NumberColumn("Resolved", format="%d ✅"),
                        "avg_resolution_hours": st.column_config.NumberColumn("Avg Time", format="%.1f hrs"),
                        "sla_compliance_pct": st.column_config.ProgressColumn("SLA Met %", min_value=0, max_value=100, format="%.1f%%"),
                        "avg_csat": st.column_config.NumberColumn("CSAT Rating", format="%.2f ⭐")
                    },
                    hide_index=True,
                    use_container_width=True
                )

        with tab2:
            st.subheader("Recurring Problem Patterns (SQL Pareto View)")
            rec_df = AnalyticsService.get_recurring_problems()
            if not rec_df.empty:
                st.dataframe(rec_df, hide_index=True, use_container_width=True)

        with tab3:
            st.subheader("Department Demand & Ticket Velocity")
            dept_df = AnalyticsService.get_department_load()
            if not dept_df.empty:
                st.dataframe(dept_df, hide_index=True, use_container_width=True)

        with tab4:
            st.subheader("Reopened Tickets Defect Analysis")
            reopen_df = AnalyticsService.get_reopened_tickets()
            if not reopen_df.empty:
                st.dataframe(reopen_df, hide_index=True, use_container_width=True)
            else:
                st.success("No reopened tickets found in the dataset.")

    # ------------------------------------------------------
    # 2.5 SQL STUDIO
    # ------------------------------------------------------
    elif it_nav == "🔍 SQL Studio":
        st.markdown("""
            <div class="saas-header">
                <div>
                    <h1 class="saas-title">Interactive Relational SQL Studio</h1>
                    <p class="saas-subtitle">
                        Run advanced analytical queries with CTEs, Window Functions, and subqueries directly against the dual MySQL/SQLite engine.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        catalog_titles = [q["title"] for q in SQL_QUERIES_CATALOG]
        sel_title = st.selectbox("📚 Select Pre-Loaded Analytical Query", catalog_titles)
        sel_q = next((q for q in SQL_QUERIES_CATALOG if q["title"] == sel_title), SQL_QUERIES_CATALOG[0])

        st.info(f"**Concept:** {sel_q['concept']} | **Description:** {sel_q['description']}")
        custom_sql = st.text_area("SQL Statement Editor", value=sel_q["sql"], height=160)

        if st.button("▶️ Execute SQL Query", type="primary"):
            start_t = time.time()
            try:
                res_df = AnalyticsService.execute_custom_query(custom_sql)
                exec_ms = round((time.time() - start_t) * 1000, 2)
                st.success(f"Query returned **{len(res_df)} rows** in **{exec_ms} ms**.")
                st.dataframe(res_df, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Error: {str(e)}")

    # ------------------------------------------------------
    # 2.6 EXPORT REPORTS
    # ------------------------------------------------------
    elif it_nav == "📑 Export Reports":
        st.markdown("""
            <div class="saas-header">
                <div>
                    <h1 class="saas-title">Executive Reports & Dossier Generation</h1>
                    <p class="saas-subtitle">
                        Generate formatted PDF Executive Briefs or multi-tab styled Excel Workbooks directly from live SQL data.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        c_exp1, c_exp2 = st.columns(2)
        with c_exp1:
            st.markdown("### 📄 Executive PDF Incident Dossier")
            st.markdown("Includes executive KPI scorecard, SLA compliance breakdown, and recent high-priority incidents.")
            if st.button("Generate Executive PDF", type="primary", use_container_width=True):
                pdf_bytes = ExportService.generate_pdf_report()
                st.download_button(
                    label="⬇️ Download PDF Dossier",
                    data=pdf_bytes,
                    file_name=f"ServiceDesk_Executive_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        with c_exp2:
            st.markdown("### 📊 Multi-Sheet Excel Master Workbook")
            st.markdown("Includes raw tickets, agent rankings, recurring problem Pareto analysis, and SLA logs.")
            if st.button("Generate Excel Master Workbook", type="primary", use_container_width=True):
                excel_bytes = ExportService.generate_excel_report()
                st.download_button(
                    label="⬇️ Download Excel Workbook",
                    data=excel_bytes,
                    file_name=f"ServiceDesk_Master_Data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    # ------------------------------------------------------
    # 2.7 SETTINGS
    # ------------------------------------------------------
    elif it_nav == "⚙️ Settings":
        st.markdown("""
            <div class="saas-header">
                <div>
                    <h1 class="saas-title">Database & System Settings</h1>
                    <p class="saas-subtitle">
                        Configure connection parameters, toggle between MySQL 8.0+ and SQLite engines, and test connections.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        db_stat = db_manager.get_db_info()
        st.json(db_stat)


# ==========================================================
# ==========================================================
# 3. LIFECYCLE & INNOVATIONS SHOWCASE
# ==========================================================
# ==========================================================
else:
    if showcase_nav == "🚀 How Tickets Are Raised & Solved":
        st.markdown("""
            <div class="saas-header">
                <div>
                    <h1 class="saas-title">🚀 Incident Lifecycle: How Tickets Are Raised & Solved</h1>
                    <p class="saas-subtitle">
                        Interactive walkthrough demonstrating how an IT issue moves from employee submission to AI triage, auto-assignment, remediation, root-cause resolution, and CSAT feedback.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="display:grid; grid-template-columns: repeat(5, 1fr); gap:12px; margin-bottom:24px;">
            <div style="background:#ffffff; border:1px solid #bfdbfe; border-radius:10px; padding:14px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="font-size:24px; margin-bottom:4px;">1️⃣ 📝</div>
                <div style="font-weight:700; color:#2563eb; font-size:0.85rem;">1. Raise Ticket</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:2px;">Employee logs issue with title & description</div>
            </div>
            <div style="background:#ffffff; border:1px solid #ddd6fe; border-radius:10px; padding:14px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="font-size:24px; margin-bottom:4px;">2️⃣ 🤖</div>
                <div style="font-weight:700; color:#7c3aed; font-size:0.85rem;">2. AI Auto-Triage</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:2px;">NLP predicts Priority, Category & SLA Target</div>
            </div>
            <div style="background:#ffffff; border:1px solid #fde68a; border-radius:10px; padding:14px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="font-size:24px; margin-bottom:4px;">3️⃣ ⚖️</div>
                <div style="font-weight:700; color:#d97706; font-size:0.85rem;">3. Smart Routing</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:2px;">Assigned to least-loaded specialized agent</div>
            </div>
            <div style="background:#ffffff; border:1px solid #a7f3d0; border-radius:10px; padding:14px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="font-size:24px; margin-bottom:4px;">4️⃣ 🛠️</div>
                <div style="font-weight:700; color:#059669; font-size:0.85rem;">4. Fix & Root Cause</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:2px;">Agent fixes bug, adds notes & root cause</div>
            </div>
            <div style="background:#ffffff; border:1px solid #bae6fd; border-radius:10px; padding:14px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="font-size:24px; margin-bottom:4px;">5️⃣ ⭐</div>
                <div style="font-weight:700; color:#0284c7; font-size:0.85rem;">5. Verify & CSAT</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:2px;">Requester verifies fix & rates 1-5 stars</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("📖 Case Study: 'Production Database Pool Timeout'")
        t1, t2, t3, t4, t5 = st.tabs([
            "Step 1: Raising Incident",
            "Step 2: AI Triage & Duplicate Check",
            "Step 3: SQL Workload Auto-Assignment",
            "Step 4: Active Remediation & Root Cause",
            "Step 5: Employee CSAT & Knowledge Base"
        ])

        with t1:
            st.markdown("""
            **Scenario:** A Financial Analyst (*Angela Martin*) encounters database connection failures while running Q3 tax batch calculations.
            - **Title:** `Production Database Connection Pool Timeout`
            - **Description:** `Read replica connection maxed out at 500 connections. Java batch process crashing with OOM.`
            - **Requester:** `Finance & Accounts Department`
            """)
            st.success("✅ Ticket record inserted into MySQL / SQLite `tickets` table with initial state `Open`.")

        with t2:
            st.markdown("""
            **Real-Time AI Engine Assessment:**
            - **Predicted Priority:** 🔥 **Critical (P1)** (Detected keywords: *database, timeout, crashing*)
            - **Target Resolution SLA:** **4.0 Hours** (SLA Policy for P1)
            - **Suggested Category:** `Database & Cloud Infrastructure`
            - **Similar Ticket Search:** Detected 94% similarity with historical ticket `TCK-1001` (Previous fix: *Scaled PgBouncer connection pool*).
            """)
            st.info("💡 Result: Self-service KB guide & past resolution surfaced immediately to the support engineer.")

        with t3:
            st.markdown("""
            **SQL Workload-Aware Intelligent Routing:**
            - The system queries `agents` and `support_teams` to find who is on the **Infrastructure & Cloud Ops** team.
            - Checks active ticket workload:
              - *Agent Alice:* 6 Active Tickets
              - *Agent Brian:* 2 Active Tickets ➔ **Least Loaded!**
            - Ticket is automatically assigned to **Brian Taylor (L3 Cloud Engineer)**. Status changes to `Assigned`.
            """)
            st.success("✅ Avoided human bottleneck. Ticket reached the right specialist in 0.05 seconds.")

        with t4:
            st.markdown("""
            **Remediation & Technical Resolution:**
            1. Agent Brian investigates and changes status to `In Progress` (setting `first_response_at` timestamp).
            2. Diagnosis: Batch query lacked an index on `created_at` causing table locks and connection pool exhaustion.
            3. Remediation: Added composite index `idx_trans_status` and increased PgBouncer max connections from 500 to 1200.
            4. Status updated to `Resolved` with:
               - **Root Cause:** `Missing database composite index on transactions table`
               - **Resolution Notes:** `Created composite index and tuned PgBouncer pool limits.`
               - **Actual Resolution Time:** `3.2 Hours` (Under 4.0h SLA Target ➔ **SLA MET ✅**)
            """)

        with t5:
            st.markdown("""
            **Employee Verification & Knowledge Base Generation:**
            1. Angela Martin receives notification, verifies reports now generate in 8 seconds, and submits **5.0 / 5.0 ⭐ CSAT rating**.
            2. System automatically audits the resolution in `ticket_history` and updates the **Executive KPI Scorecard**.
            3. The fix is archived into the **Knowledge Base** so future agents can solve similar issues in 5 minutes!
            """)
            st.balloons()

    else:
        st.markdown("""
            <div class="saas-header">
                <div>
                    <h1 class="saas-title">💡 System Architecture & Key Innovations</h1>
                    <p class="saas-subtitle">
                        A clear, transparent breakdown of what has been improved compared to generic ticketing systems, Excel trackers, and basic CRUD applications.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        | Area | ❌ Traditional / Generic Systems | ✨ Our Advanced IT ServiceDesk Pro |
        |---|---|---|
        | **1. Database Engine** | Flat files or basic un-indexed tables | **Relational MySQL 8.0+ / SQLite dual-engine with 11 normalized tables, composite indexes, and analytical SQL Views** (`v_department_load`, `v_recurring_problems`). |
        | **2. Ticket Assignment** | Manual triage by a coordinator or blind round-robin causing agent burnout | **SQL Workload-Aware Auto-Routing**: Dynamically queries active ticket load per agent and assigns to the least-loaded qualified engineer. |
        | **3. SLA Management** | Static deadlines often missed until after the fact | **Live SLA Countdown Matrix**: Real-time timer badges calculating remaining hours, warning at **< 2 hours**, and automatically flagging breaches in SQL. |
        | **4. Workforce Analytics** | Basic count summaries | **Advanced SQL CTEs & Window Functions** (`RANK() OVER (...)`, `DENSE_RANK()`, `NTILE()`, `HAVING`) to rank agent velocity, SLA compliance, and CSAT without bias. |
        | **5. Root Cause Tracking** | Tickets are simply closed with generic "fixed" message | **Structured Defect & Reopen Analysis**: Tracks recurring problem categories, repeated reopens, and root-cause Pareto distributions. |
        | **6. AI & Self-Service** | Users repeatedly log the same issues | **Real-Time NLP Incident Triage**: Instantly predicts urgency, finds similar historical tickets with their fixes, and suggests matching Knowledge Base articles. |
        | **7. Executive Reporting** | Manual copy-pasting into spreadsheets | **1-Click Executive PDF Dossiers & Multi-Tab Styled Excel Master Workbooks** generated dynamically from relational SQL data. |
        """)
