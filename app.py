"""Main Streamlit Application Entrypoint."""

import streamlit as st
import config
from core.database import db
from core.auth import AuthService, SessionManager
from core.repositories import DepartmentRepository, AgentRepository
from core.exceptions import InvalidLoginError, UserAlreadyExistsError, ValidationError, HelpdeskException
from dashboard.ui_components import apply_custom_styles
from dashboard.employee_dashboard import render_employee_dashboard
from dashboard.agent_dashboard import render_agent_dashboard
from dashboard.admin_dashboard import render_admin_dashboard

# Streamlit Page Setup
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.DEFAULT_PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply styling
apply_custom_styles()
SessionManager.init_session()

def render_login_page():
    """Renders authentication login screen with registration and demo credentials assistance."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            f"<div style='text-align: center; margin-bottom: 25px;'>"
            f"<h1 style='color: #4F46E5;'>🎫 {config.APP_TITLE}</h1>"
            f"<p style='color: #64748B;'>Enterprise Issue Tracking, SLA Management & SQL Intelligence</p>"
            f"</div>",
            unsafe_allow_html=True
        )

        tab_login, tab_register, tab_demo = st.tabs(["🔐 Sign In", "✨ Create Account", "🚀 Quick Demo Logins"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username or Email", placeholder="e.g. admin or ravi_agent")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Sign In to Portal", use_container_width=True, type="primary")

                if submit:
                    if not username.strip() or not password.strip():
                        st.error("Please enter both username and password.")
                    else:
                        try:
                            auth_service = AuthService()
                            user = auth_service.authenticate(username.strip(), password.strip())
                            SessionManager.login(user)
                            st.success(f"Welcome back, {user.username}!")
                            st.rerun()
                        except InvalidLoginError as e:
                            st.error(str(e))
                        except Exception as e:
                            st.error(f"Authentication error: {str(e)}")

        with tab_register:
            st.markdown("##### 📝 Register New Helpdesk Account")
            st.caption("Create your profile to raise support requests or assist teammates.")

            dept_repo = DepartmentRepository()
            agent_repo = AgentRepository()
            departments = dept_repo.get_all()
            teams = agent_repo.get_all_teams()

            dept_options = {d.name: d.department_id for d in departments}
            team_options = {t.name: t.team_id for t in teams}

            with st.form("registration_form", clear_on_submit=False):
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    full_name = st.text_input("Full Name *", placeholder="e.g. Sarah Connor")
                    username_reg = st.text_input("Username *", placeholder="e.g. sarah_c")
                    email_reg = st.text_input("Email Address *", placeholder="e.g. sarah@company.com")

                with r_col2:
                    role_reg = st.selectbox("Role *", ["Employee", "Support Agent"], index=0)
                    if role_reg == "Employee":
                        dept_name = st.selectbox("Department *", list(dept_options.keys()) if dept_options else ["General"])
                        job_title = st.text_input("Job Title", placeholder="e.g. Software Engineer")
                        phone_reg = st.text_input("Phone Number", placeholder="e.g. +1-555-0199")
                    else:
                        team_name = st.selectbox("Support Team *", list(team_options.keys()) if team_options else ["Tier 1 Support"])
                        spec_reg = st.text_input("Specialization", placeholder="e.g. Cloud & Network")
                        phone_reg = None
                        job_title = None

                p_col1, p_col2 = st.columns(2)
                with p_col1:
                    pass_reg = st.text_input("Password *", type="password", placeholder="Min. 6 characters")
                with p_col2:
                    pass_confirm = st.text_input("Confirm Password *", type="password", placeholder="Re-enter password")

                reg_submit = st.form_submit_button("✨ Create Account & Sign In", use_container_width=True, type="primary")

                if reg_submit:
                    if not full_name.strip() or not username_reg.strip() or not email_reg.strip() or not pass_reg.strip():
                        st.error("Please fill in all required fields marked with *.")
                    elif "@" not in email_reg or "." not in email_reg:
                        st.error("Please provide a valid email address.")
                    elif len(pass_reg) < 6:
                        st.error("Password must be at least 6 characters long.")
                    elif pass_reg != pass_confirm:
                        st.error("Passwords do not match. Please verify and retry.")
                    else:
                        try:
                            auth_service = AuthService()
                            dept_id = dept_options.get(dept_name) if role_reg == "Employee" else None
                            team_id = team_options.get(team_name) if role_reg == "Support Agent" else None

                            new_user = auth_service.register_user_with_profile(
                                username=username_reg.strip().lower(),
                                email=email_reg.strip().lower(),
                                plain_password=pass_reg.strip(),
                                role=role_reg,
                                full_name=full_name.strip(),
                                department_id=dept_id,
                                phone=phone_reg.strip() if phone_reg else None,
                                job_title=job_title.strip() if job_title else None,
                                team_id=team_id,
                                specialization=spec_reg.strip() if role_reg == "Support Agent" and spec_reg else "General IT"
                            )

                            st.success(f"🎉 Account created successfully for **{new_user.username}**! Logging you in...")
                            SessionManager.login(new_user)
                            st.rerun()

                        except UserAlreadyExistsError as e:
                            st.error(f"⚠️ {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Failed to create account: {str(e)}")

        with tab_demo:
            st.markdown("##### ⚡ Instant Role-Based Demo Logins")
            st.caption("Click any persona below to quickly test the application:")

            auth_service = AuthService()

            d_col1, d_col2 = st.columns(2)
            with d_col1:
                if st.button("👑 Admin (System Lead)", use_container_width=True):
                    user = auth_service.authenticate("admin", "admin123")
                    SessionManager.login(user)
                    st.rerun()

                if st.button("🎧 Agent (Ravi Kumar)", use_container_width=True):
                    user = auth_service.authenticate("ravi_agent", "agent123")
                    SessionManager.login(user)
                    st.rerun()

            with d_col2:
                if st.button("👥 Team Lead (Vikram)", use_container_width=True):
                    user = auth_service.authenticate("lead_vikram", "lead123")
                    SessionManager.login(user)
                    st.rerun()

                if st.button("👤 Employee (John Doe)", use_container_width=True):
                    user = auth_service.authenticate("john_doe", "employee123")
                    SessionManager.login(user)
                    st.rerun()


def main():
    """Main application loop and role-based router."""
    current_user = SessionManager.get_current_user()

    if not current_user:
        render_login_page()
        return

    # Sidebar Navigation & User Info
    with st.sidebar:
        st.markdown(f"### 🎫 **IT Helpdesk**")
        st.markdown(f"**Logged in as:** `{current_user.username}`")

        role_colors = {
            "Admin": "badge-critical",
            "Team Lead": "badge-assigned",
            "Support Agent": "badge-in-progress",
            "Employee": "badge-open"
        }
        badge_cls = role_colors.get(current_user.role, "badge-open")
        st.markdown(f'<span class="badge {badge_cls}">{current_user.role}</span>', unsafe_allow_html=True)
        st.divider()

        # Dynamic navigation options based on role
        if current_user.role == "Admin":
            nav_options = ["📊 Executive Analytics", "🎧 Support Workspace", "👤 Employee Portal"]
        elif current_user.role in ("Team Lead", "Support Agent"):
            nav_options = ["🎧 Support Workspace", "👤 Raise/View My Tickets", "📊 Operational Overview"]
        else:
            nav_options = ["👤 Employee Portal"]

        selected_page = st.radio("Navigation", nav_options)

        st.divider()
        if st.button("🚪 Log Out", use_container_width=True):
            SessionManager.logout()
            st.rerun()

    # Route to appropriate view
    if selected_page in ("📊 Executive Analytics", "📊 Operational Overview"):
        render_admin_dashboard()
    elif selected_page == "🎧 Support Workspace":
        render_agent_dashboard()
    else:
        render_employee_dashboard()


if __name__ == "__main__":
    main()
