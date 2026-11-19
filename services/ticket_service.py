from datetime import datetime, timedelta
from typing import Optional, List, Dict
from database.connection import db_manager
from utils.logger import get_logger
import config

logger = get_logger("ticket_service")

class TicketService:
    @staticmethod
    def get_category_team_mapping(category: str) -> int:
        """Determines best support team based on ticket category."""
        mapping = {
            "Hardware & Workstations": 4,  # Workplace Hardware Support
            "Software & Licensing": 1,     # Tier-1 Service Desk
            "Network & VPN Connectivity": 2, # Infrastructure & Cloud Ops
            "Identity & Access Management": 3, # Cybersecurity & IAM
            "Database & Cloud Infrastructure": 2, # Infrastructure & Cloud Ops
            "Email & Communication Systems": 1,
            "Security & Incident Response": 3,
            "Printer & Peripherals": 4,
            "General IT Support": 1
        }
        return mapping.get(category, 1)

    @staticmethod
    def auto_assign_agent(team_id: int) -> Optional[int]:
        """
        Intelligent Workload-Aware Auto-Assignment.
        Finds the available agent in the specified team with the lowest current active ticket load.
        """
        sql = """
            SELECT a.agent_id, a.max_active_tickets,
                   COUNT(t.ticket_id) AS active_load
            FROM agents a
            LEFT JOIN tickets t ON a.agent_id = t.assigned_agent_id AND t.status NOT IN ('Resolved', 'Closed')
            WHERE a.team_id = :team_id AND a.status = 'Available'
            GROUP BY a.agent_id, a.max_active_tickets
            HAVING active_load < a.max_active_tickets
            ORDER BY active_load ASC, a.agent_id ASC
            LIMIT 1;
        """
        res = db_manager.execute_query(sql, {"team_id": team_id})
        if res:
            return res[0]["agent_id"]
        return None

    @staticmethod
    def create_ticket(
        title: str,
        description: str,
        category: str,
        priority: str,
        requester_id: int,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None,
        assigned_agent_id: Optional[int] = None,
        auto_assign: bool = True
    ) -> Dict:
        """Creates a new IT support ticket with SLA calculations and audit logging."""
        now = datetime.now()
        
        # Determine team if not provided
        if not team_id:
            team_id = TicketService.get_category_team_mapping(category)

        # Auto assign agent if requested
        if auto_assign and not assigned_agent_id:
            assigned_agent_id = TicketService.auto_assign_agent(team_id)

        # Determine SLA hours
        sla_hours = config.DEFAULT_SLA.get(priority, {}).get("resolution", 24)
        sla_due_date = now + timedelta(hours=sla_hours)

        # Generate Ticket Number
        res = db_manager.execute_query("SELECT COUNT(*) AS cnt FROM tickets;")
        count = res[0]["cnt"] if res else 0
        ticket_number = f"TCK-{1000 + count + 1}"

        status = "Assigned" if assigned_agent_id else "Open"

        insert_sql = """
            INSERT INTO tickets (
                ticket_number, title, description, category, priority, status,
                requester_id, department_id, team_id, assigned_agent_id,
                created_at, sla_due_date, reopen_count, sla_breached
            ) VALUES (
                :ticket_number, :title, :description, :category, :priority, :status,
                :requester_id, :department_id, :team_id, :assigned_agent_id,
                :created_at, :sla_due_date, 0, 0
            );
        """
        try:
            exec_res = db_manager.execute_non_query(insert_sql, {
                "ticket_number": ticket_number,
                "title": title.strip(),
                "description": description.strip(),
                "category": category,
                "priority": priority,
                "status": status,
                "requester_id": requester_id,
                "department_id": department_id,
                "team_id": team_id,
                "assigned_agent_id": assigned_agent_id,
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "sla_due_date": sla_due_date.strftime("%Y-%m-%d %H:%M:%S")
            })
            new_ticket_id = exec_res.get("lastrowid")

            # Audit log
            db_manager.execute_non_query(
                """INSERT INTO ticket_history (ticket_id, changed_by, action_type, old_status, new_status, notes)
                   VALUES (:t_id, :user_id, 'Created', NULL, :status, :notes)""",
                {
                    "t_id": new_ticket_id,
                    "user_id": requester_id,
                    "status": status,
                    "notes": f"Ticket #{ticket_number} created with priority '{priority}'."
                }
            )

            logger.info(f"Created ticket {ticket_number} (ID: {new_ticket_id})")
            return {"success": True, "ticket_id": new_ticket_id, "ticket_number": ticket_number}
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_ticket_status(
        ticket_id: int,
        new_status: str,
        user_id: int,
        resolution_notes: Optional[str] = None,
        root_cause: Optional[str] = None,
        actual_hours: Optional[float] = None
    ) -> bool:
        """Updates ticket lifecycle status, calculates SLA breach, and records audit trail."""
        now = datetime.now()
        
        # Fetch current ticket details
        cur = db_manager.execute_query("SELECT * FROM tickets WHERE ticket_id = :1", {"1": ticket_id})
        if not cur:
            return False
        ticket = cur[0]
        old_status = ticket["status"]

        update_fields = ["status = :new_status"]
        params = {"ticket_id": ticket_id, "new_status": new_status}

        if new_status == "Resolved" and old_status != "Resolved":
            update_fields.append("resolved_at = :resolved_at")
            params["resolved_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
            if resolution_notes:
                update_fields.append("resolution_notes = :notes")
                params["notes"] = resolution_notes
            if root_cause:
                update_fields.append("root_cause = :root_cause")
                params["root_cause"] = root_cause
            if actual_hours is not None:
                update_fields.append("actual_hours = :act_hrs")
                params["act_hrs"] = actual_hours

            # Check if breached SLA
            sla_due = ticket["sla_due_date"]
            if sla_due:
                if isinstance(sla_due, str):
                    sla_due_dt = datetime.strptime(sla_due[:19], "%Y-%m-%d %H:%M:%S")
                else:
                    sla_due_dt = sla_due
                if now > sla_due_dt:
                    update_fields.append("sla_breached = 1")

        elif new_status == "Closed":
            update_fields.append("closed_at = :closed_at")
            params["closed_at"] = now.strftime("%Y-%m-%d %H:%M:%S")

        elif new_status == "In Progress" and not ticket["first_response_at"]:
            update_fields.append("first_response_at = :resp_at")
            params["resp_at"] = now.strftime("%Y-%m-%d %H:%M:%S")

        sql = f"UPDATE tickets SET {', '.join(update_fields)} WHERE ticket_id = :ticket_id"
        db_manager.execute_non_query(sql, params)

        # Audit record
        db_manager.execute_non_query(
            """INSERT INTO ticket_history (ticket_id, changed_by, action_type, old_status, new_status, notes)
               VALUES (:t_id, :user_id, 'Status Transition', :old_status, :new_status, :notes)""",
            {
                "t_id": ticket_id,
                "user_id": user_id,
                "old_status": old_status,
                "new_status": new_status,
                "notes": resolution_notes or f"Status changed from {old_status} to {new_status}"
            }
        )
        return True

    @staticmethod
    def assign_ticket(ticket_id: int, agent_id: int, team_id: int, user_id: int) -> bool:
        """Assigns ticket to a specific agent and team."""
        db_manager.execute_non_query(
            """UPDATE tickets 
               SET assigned_agent_id = :agent_id, team_id = :team_id, status = 'Assigned'
               WHERE ticket_id = :ticket_id""",
            {"ticket_id": ticket_id, "agent_id": agent_id, "team_id": team_id}
        )
        # Log to audit history
        db_manager.execute_non_query(
            """INSERT INTO ticket_history (ticket_id, changed_by, action_type, notes)
               VALUES (:t_id, :user_id, 'Agent Assigned', :notes)""",
            {"t_id": ticket_id, "user_id": user_id, "notes": f"Assigned to Agent #{agent_id} in Team #{team_id}"}
        )
        return True

    @staticmethod
    def reopen_ticket(ticket_id: int, user_id: int, reason: str) -> bool:
        """Reopens a resolved/closed ticket and increments reopen counter."""
        db_manager.execute_non_query(
            """UPDATE tickets 
               SET status = 'Reopened', reopen_count = reopen_count + 1, resolved_at = NULL, closed_at = NULL
               WHERE ticket_id = :ticket_id""",
            {"ticket_id": ticket_id}
        )
        db_manager.execute_non_query(
            """INSERT INTO ticket_history (ticket_id, changed_by, action_type, old_status, new_status, notes)
               VALUES (:t_id, :user_id, 'Ticket Reopened', 'Resolved', 'Reopened', :reason)""",
            {"t_id": ticket_id, "user_id": user_id, "reason": f"Reopened by requester: {reason}"}
        )
        return True

    @staticmethod
    def submit_feedback(ticket_id: int, rating: int, comments: str) -> bool:
        """Submits user CSAT rating (1 to 5) and feedback on a resolved ticket."""
        db_manager.execute_non_query(
            """UPDATE tickets 
               SET satisfaction_rating = :rating, feedback_comments = :comments, status = 'Closed'
               WHERE ticket_id = :ticket_id""",
            {"ticket_id": ticket_id, "rating": rating, "comments": comments}
        )
        return True

    @staticmethod
    def add_comment(ticket_id: int, user_id: int, message: str, comment_type: str = "Public") -> bool:
        """Adds a public communication or internal note to a ticket."""
        db_manager.execute_non_query(
            """INSERT INTO ticket_comments (ticket_id, user_id, comment_type, message)
               VALUES (:ticket_id, :user_id, :comment_type, :message)""",
            {"ticket_id": ticket_id, "user_id": user_id, "comment_type": comment_type, "message": message.strip()}
        )
        return True

    @staticmethod
    def get_ticket_details(ticket_id: int) -> Optional[Dict]:
        """Fetches complete ticket details including requester, agent, comments, and audit timeline."""
        sql = """
            SELECT 
                t.*,
                req.full_name AS requester_name,
                req.email AS requester_email,
                req.phone AS requester_phone,
                d.name AS department_name,
                st.name AS team_name,
                ag_u.full_name AS agent_name,
                ag_u.email AS agent_email,
                ag.tier AS agent_tier
            FROM tickets t
            JOIN users req ON t.requester_id = req.user_id
            LEFT JOIN departments d ON t.department_id = d.department_id
            LEFT JOIN support_teams st ON t.team_id = st.team_id
            LEFT JOIN agents ag ON t.assigned_agent_id = ag.agent_id
            LEFT JOIN users ag_u ON ag.user_id = ag_u.user_id
            WHERE t.ticket_id = :ticket_id
        """
        rows = db_manager.execute_query(sql, {"ticket_id": ticket_id})
        if not rows:
            return None
        ticket = rows[0]

        # Fetch comments
        comments_sql = """
            SELECT c.*, u.full_name AS author_name, u.role AS author_role
            FROM ticket_comments c
            JOIN users u ON c.user_id = u.user_id
            WHERE c.ticket_id = :ticket_id
            ORDER BY c.created_at ASC
        """
        ticket["comments"] = db_manager.execute_query(comments_sql, {"ticket_id": ticket_id})

        # Fetch audit history
        history_sql = """
            SELECT h.*, u.full_name AS changed_by_name
            FROM ticket_history h
            LEFT JOIN users u ON h.changed_by = u.user_id
            WHERE h.ticket_id = :ticket_id
            ORDER BY h.created_at ASC
        """
        ticket["history"] = db_manager.execute_query(history_sql, {"ticket_id": ticket_id})

        return ticket
