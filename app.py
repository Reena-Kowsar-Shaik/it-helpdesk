"""Main Streamlit Application Entrypoint."""

import streamlit as st
import config
from core.database import db
from core.auth import AuthService, SessionManager
from core.exceptions import InvalidLoginError, HelpdeskException
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
    """Renders authentication login screen with demo credentials assistance."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            f"<div style='text-align: center; margin-bottom: 25px;'>"
            f"<h1 style='color: #6366F1;'>🎫 {config.APP_TITLE}</h1>"
            f"<p style='color: #94A3B8;'>Enterprise Issue Tracking, SLA Management & SQL Intelligence</p>"
            f"</div>",
            unsafe_allow_html=True
        )

        tab_login, tab_demo = st.tabs(["🔐 Sign In", "🚀 Quick Demo Logins"])

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
