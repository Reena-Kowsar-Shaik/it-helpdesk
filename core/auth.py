"""Authentication, Password Hashing, Session Management and RBAC."""

import bcrypt
from typing import Optional, Dict, Any, List
from core.database import db
from core.models import User, Employee, SupportAgent
from core.repositories import UserRepository, EmployeeRepository, AgentRepository
from core.exceptions import InvalidLoginError, UnauthorizedAccessError, UserAlreadyExistsError
from core.logger import log_audit, log_error

class PasswordService:
    """Handles secure password hashing and verification using bcrypt."""

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Hash plain text password with auto-generated salt."""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify plain text password against stored bcrypt hash."""
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception as e:
            log_error("Password verification failed", e)
            return False


class AuthService:
    """Core Authentication & Authorization Service."""

    def __init__(self):
        self.user_repo = UserRepository()
        self.employee_repo = EmployeeRepository()
        self.agent_repo = AgentRepository()

    def authenticate(self, username: str, plain_password: str) -> User:
        """Validate credentials and return authenticated User entity."""
        user = self.user_repo.get_by_username(username)
        if not user:
            log_audit("LOGIN_FAILED", username, "User not found", level="WARNING")
            raise InvalidLoginError("Invalid username or password.")

        if not user.is_active:
            log_audit("LOGIN_BLOCKED", username, "Inactive account", level="WARNING")
            raise InvalidLoginError("This account is currently disabled.")

        if not PasswordService.verify_password(plain_password, user.password_hash):
            log_audit("LOGIN_FAILED", username, "Password mismatch", level="WARNING")
            raise InvalidLoginError("Invalid username or password.")

        log_audit("LOGIN_SUCCESS", username, f"Role: {user.role}")
        return user

    def register_user(
        self,
        username: str,
        email: str,
        plain_password: str,
        role: str = "Employee"
    ) -> User:
        """Register a new user account with hashed password."""
        hashed_pw = PasswordService.hash_password(plain_password)
        return self.user_repo.create(
            username=username,
            email=email,
            password_hash=hashed_pw,
            role=role
        )


class SessionManager:
    """Manages Streamlit session state and provides RBAC checks."""

    @staticmethod
    def init_session():
        """Ensure default session state keys are populated."""
        import streamlit as st
        if "user" not in st.session_state:
            st.session_state["user"] = None
        if "role" not in st.session_state:
            st.session_state["role"] = None
        if "profile" not in st.session_state:
            st.session_state["profile"] = None

    @staticmethod
    def login(user: User):
        """Set user session upon successful login."""
        import streamlit as st
        st.session_state["user"] = user
        st.session_state["role"] = user.role

        # Populate corresponding profile
        if user.role == "Employee":
            emp_repo = EmployeeRepository()
            st.session_state["profile"] = emp_repo.get_by_user_id(user.user_id)
        elif user.role in ("Support Agent", "Team Lead"):
            agent_repo = AgentRepository()
            st.session_state["profile"] = agent_repo.get_by_user_id(user.user_id)
        else:
            st.session_state["profile"] = {"name": user.username, "role": user.role}

    @staticmethod
    def logout():
        """Clear user session on logout."""
        import streamlit as st
        username = st.session_state.get("user").username if st.session_state.get("user") else "Unknown"
        log_audit("LOGOUT", username, "User logged out")
        st.session_state["user"] = None
        st.session_state["role"] = None
        st.session_state["profile"] = None

    @staticmethod
    def get_current_user() -> Optional[User]:
        """Return currently logged-in user or None."""
        import streamlit as st
        return st.session_state.get("user")

    @staticmethod
    def is_authenticated() -> bool:
        """Check if user session is active."""
        import streamlit as st
        return st.session_state.get("user") is not None

    @staticmethod
    def require_role(allowed_roles: List[str]):
        """Ensure current user role is authorized or raise exception."""
        import streamlit as st
        current_role = st.session_state.get("role")
        if not current_role or current_role not in allowed_roles:
            raise UnauthorizedAccessError(f"Access requires one of: {', '.join(allowed_roles)}")
