import hashlib
from database.connection import db_manager
from utils.logger import get_logger

logger = get_logger("auth_service")

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Computes SHA-256 hash of password."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def login(email: str, password: str):
        """Authenticates a user by email and password."""
        pwd_hash = AuthService.hash_password(password)
        sql = """
            SELECT u.user_id, u.full_name, u.email, u.role, u.department_id, u.designation,
                   d.name AS department_name, a.agent_id, a.team_id, a.tier AS agent_tier
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.department_id
            LEFT JOIN agents a ON u.user_id = a.user_id
            WHERE LOWER(u.email) = LOWER(:email) AND u.password_hash = :password_hash AND u.is_active = 1
        """
        results = db_manager.execute_query(sql, {"email": email.strip(), "password_hash": pwd_hash})
        if results:
            user = results[0]
            # Log login event
            db_manager.execute_non_query(
                "INSERT INTO system_audit_logs (user_id, event_type, details) VALUES (:1, 'USER_LOGIN', :2)",
                {"1": user["user_id"], "2": f"User {user['email']} logged in successfully."}
            )
            logger.info(f"User {email} logged in successfully.")
            return user
        logger.warning(f"Failed login attempt for {email}")
        return None

    @staticmethod
    def register_user(full_name: str, email: str, password: str, role: str, department_id: int, designation: str = "", phone: str = ""):
        """Registers a new user with role-based access control."""
        pwd_hash = AuthService.hash_password(password)
        sql = """
            INSERT INTO users (full_name, email, password_hash, role, department_id, designation, phone)
            VALUES (:full_name, :email, :password_hash, :role, :department_id, :designation, :phone)
        """
        try:
            res = db_manager.execute_non_query(sql, {
                "full_name": full_name.strip(),
                "email": email.strip().lower(),
                "password_hash": pwd_hash,
                "role": role,
                "department_id": department_id,
                "designation": designation.strip(),
                "phone": phone.strip()
            })
            new_user_id = res.get("lastrowid")
            
            # If agent or team lead, create agent record
            if role in ["Support Agent", "Team Lead"]:
                db_manager.execute_non_query(
                    """INSERT INTO agents (user_id, team_id, tier, max_active_tickets, status, skills)
                       VALUES (:user_id, 1, 'L1', 10, 'Available', 'General IT')""",
                    {"user_id": new_user_id}
                )
            
            logger.info(f"User {email} registered successfully with role {role}")
            return {"success": True, "user_id": new_user_id}
        except Exception as e:
            logger.error(f"Error registering user {email}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_all_users():
        """Returns all registered users in the organization."""
        sql = """
            SELECT u.user_id, u.full_name, u.email, u.role, d.name AS department_name, 
                   u.designation, u.phone, u.is_active, u.created_at
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.department_id
            ORDER BY u.user_id ASC
        """
        return db_manager.fetch_dataframe(sql)
