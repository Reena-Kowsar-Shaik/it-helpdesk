"""Database Initialization and Seeding Script."""

from datetime import datetime, timedelta
from core.database import db, Base
from core.auth import PasswordService
from core.models import (
    Department, User, Employee, SupportTeam, SupportAgent,
    Category, SLARule, Ticket, TicketHistory, Comment, TicketResolution
)
from core.logger import logger

def seed_database():
    """Create all tables and seed sample data."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=db.engine)

    with db.get_session() as session:
        # Check if already seeded
        if session.query(User).first():
            logger.info("Database already contains data. Skipping initial seeding.")
            return

        logger.info("Seeding initial reference data...")

        # 1. Departments
        depts = [
            Department(department_id=1, name="Information Technology", code="IT", description="Internal IT Infrastructure & Systems"),
            Department(department_id=2, name="Human Resources", code="HR", description="HR Management & Payroll inquiries"),
            Department(department_id=3, name="Finance & Accounting", code="FIN", description="Accounts, Billing & Audit systems"),
            Department(department_id=4, name="Software Engineering", code="ENG", description="Product Development & Cloud QA"),
            Department(department_id=5, name="Marketing & Sales", code="MKT", description="Campaigns & CRM Systems"),
        ]
        session.add_all(depts)
        session.flush()

        # 2. Categories
        cats = [
            Category(category_id=1, name="Network & Connectivity", default_priority="High", description="VPN, Wi-Fi, DNS, LAN issues"),
            Category(category_id=2, name="Hardware & Peripherals", default_priority="Medium", description="Laptops, Monitors, Docking stations"),
            Category(category_id=3, name="Software & Applications", default_priority="Medium", description="OS errors, License issues, Dev tools"),
            Category(category_id=4, name="Access & Authentication", default_priority="High", description="Password resets, 2FA, Active Directory"),
            Category(category_id=5, name="Security & Compliance", default_priority="Critical", description="Phishing, Malware, Certificate breaches"),
            Category(category_id=6, name="Cloud & Infrastructure", default_priority="High", description="AWS, Azure, Docker, VM provisioning"),
        ]
        session.add_all(cats)
        session.flush()

        # 3. SLA Rules
        slas = [
            SLARule(sla_id=1, priority="Critical", response_time_minutes=15, resolution_time_minutes=120, is_active=True),
            SLARule(sla_id=2, priority="High", response_time_minutes=30, resolution_time_minutes=240, is_active=True),
            SLARule(sla_id=3, priority="Medium", response_time_minutes=120, resolution_time_minutes=480, is_active=True),
            SLARule(sla_id=4, priority="Low", response_time_minutes=240, resolution_time_minutes=1440, is_active=True),
        ]
        session.add_all(slas)
        session.flush()

        # 4. Support Teams
        teams = [
            SupportTeam(team_id=1, name="Network Operations (NOC)", description="Routing, switches, VPN, ISP lines"),
            SupportTeam(team_id=2, name="End-User Computing (EUC)", description="Workstations, laptops, OS & peripherals"),
            SupportTeam(team_id=3, name="Security Operations (SecOps)", description="Incident response, IAM and threats"),
            SupportTeam(team_id=4, name="Cloud & DevOps Support", description="Cloud infra, pipelines, Kubernetes"),
        ]
        session.add_all(teams)
        session.flush()

        # 5. Users
        # Pre-hashed passwords
        admin_pw = PasswordService.hash_password("admin123")
        agent_pw = PasswordService.hash_password("agent123")
        lead_pw = PasswordService.hash_password("lead123")
        emp_pw = PasswordService.hash_password("employee123")

        users = [
            User(user_id=1, username="admin", email="admin@enterprise.com", password_hash=admin_pw, role="Admin"),
            User(user_id=2, username="lead_vikram", email="vikram.singh@enterprise.com", password_hash=lead_pw, role="Team Lead"),
            User(user_id=3, username="ravi_agent", email="ravi.kumar@enterprise.com", password_hash=agent_pw, role="Support Agent"),
            User(user_id=4, username="priya_agent", email="priya.nair@enterprise.com", password_hash=agent_pw, role="Support Agent"),
            User(user_id=5, username="arun_agent", email="arun.patel@enterprise.com", password_hash=agent_pw, role="Support Agent"),
            User(user_id=6, username="john_doe", email="john.doe@enterprise.com", password_hash=emp_pw, role="Employee"),
            User(user_id=7, username="sarah_smith", email="sarah.smith@enterprise.com", password_hash=emp_pw, role="Employee"),
            User(user_id=8, username="amit_sharma", email="amit.sharma@enterprise.com", password_hash=emp_pw, role="Employee"),
            User(user_id=9, username="neha_verma", email="neha.verma@enterprise.com", password_hash=emp_pw, role="Employee"),
        ]
        session.add_all(users)
        session.flush()

        # 6. Support Agents
        agents = [
            SupportAgent(agent_id=1, user_id=3, team_id=1, full_name="Ravi Kumar", specialization="Network & Firewalls"),
            SupportAgent(agent_id=2, user_id=4, team_id=2, full_name="Priya Nair", specialization="Hardware & OS Troubleshooting"),
            SupportAgent(agent_id=3, user_id=5, team_id=3, full_name="Arun Patel", specialization="IAM & Cyber Security"),
        ]
        session.add_all(agents)
        session.flush()

        # 7. Employees
        employees = [
            Employee(employee_id=1, user_id=6, department_id=4, full_name="John Doe", phone="+1-555-0101", job_title="Senior Backend Engineer"),
            Employee(employee_id=2, user_id=7, department_id=3, full_name="Sarah Smith", phone="+1-555-0102", job_title="Senior Financial Analyst"),
            Employee(employee_id=3, user_id=8, department_id=2, full_name="Amit Sharma", phone="+1-555-0103", job_title="HR Business Partner"),
            Employee(employee_id=4, user_id=9, department_id=5, full_name="Neha Verma", phone="+1-555-0104", job_title="Digital Marketing Lead"),
        ]
        session.add_all(employees)
        session.flush()

        # 8. Sample Tickets
        now = datetime.utcnow()
        tickets = [
            Ticket(
                ticket_id=1, ticket_number="TCK-2026-0001", employee_id=1, department_id=4, category_id=1,
                title="VPN Gateway Timeout in Hyderabad Region",
                description="Cannot connect to corporate staging cluster via OpenVPN. Error: TLS handshake timeout.",
                priority="High", status="IN PROGRESS", assigned_team_id=1, assigned_agent_id=1, sla_id=2,
                response_deadline=now - timedelta(hours=2), resolution_deadline=now + timedelta(hours=2),
                first_responded_at=now - timedelta(minutes=110), created_at=now - timedelta(hours=3)
            ),
            Ticket(
                ticket_id=2, ticket_number="TCK-2026-0002", employee_id=2, department_id=3, category_id=4,
                title="Urgent: Password reset for SAP ERP accounting module",
                description="Locked out of SAP billing portal right before quarter-end reconciliation.",
                priority="Critical", status="RESOLVED", assigned_team_id=3, assigned_agent_id=3, sla_id=1,
                response_deadline=now - timedelta(hours=6), resolution_deadline=now - timedelta(hours=4),
                first_responded_at=now - timedelta(hours=5), resolved_at=now - timedelta(hours=4), created_at=now - timedelta(hours=6)
            ),
            Ticket(
                ticket_id=3, ticket_number="TCK-2026-0003", employee_id=3, department_id=2, category_id=2,
                title="External 4K Monitor Flickering & HDMI Disconnects",
                description="Dell UltraSharp monitor keeps cutting out when connected via USB-C dock.",
                priority="Medium", status="ASSIGNED", assigned_team_id=2, assigned_agent_id=2, sla_id=3,
                response_deadline=now - timedelta(hours=1), resolution_deadline=now + timedelta(hours=5),
                created_at=now - timedelta(hours=2)
            ),
            Ticket(
                ticket_id=4, ticket_number="TCK-2026-0004", employee_id=4, department_id=5, category_id=3,
                title="Adobe Premiere Pro 2026 License Activation Failure",
                description="Creative Cloud error 205 when launching video editing suite.",
                priority="Low", status="OPEN", assigned_team_id=2, assigned_agent_id=None, sla_id=4,
                response_deadline=now + timedelta(hours=2), resolution_deadline=now + timedelta(hours=20),
                created_at=now - timedelta(hours=1)
            ),
            Ticket(
                ticket_id=5, ticket_number="TCK-2026-0005", employee_id=1, department_id=4, category_id=5,
                title="Suspicious Spear-Phishing Email received with ZIP payload",
                description="Received email claiming to be from Payroll requesting banking verification via executable link.",
                priority="Critical", status="CLOSED", assigned_team_id=3, assigned_agent_id=3, sla_id=1,
                response_deadline=now - timedelta(hours=24), resolution_deadline=now - timedelta(hours=22),
                first_responded_at=now - timedelta(hours=23), resolved_at=now - timedelta(hours=22),
                closed_at=now - timedelta(hours=20), created_at=now - timedelta(hours=24)
            ),
            Ticket(
                ticket_id=6, ticket_number="TCK-2026-0006", employee_id=2, department_id=3, category_id=1,
                title="Finance floor printer network interface offline",
                description="Network printer at 3rd Floor East Wing is unreachable over IP 10.10.4.55.",
                priority="Medium", status="REOPENED", assigned_team_id=1, assigned_agent_id=1, sla_id=3,
                response_deadline=now - timedelta(hours=12), resolution_deadline=now - timedelta(hours=4),
                first_responded_at=now - timedelta(hours=11), resolved_at=now - timedelta(hours=8),
                reopened_count=1, created_at=now - timedelta(hours=14)
            )
        ]
        session.add_all(tickets)
        session.flush()

        # 9. History
        histories = [
            TicketHistory(ticket_id=1, old_status=None, new_status="OPEN", changed_by_user_id=6, comment="Ticket created", changed_at=now - timedelta(hours=3)),
            TicketHistory(ticket_id=1, old_status="OPEN", new_status="ASSIGNED", changed_by_user_id=2, comment="Assigned to Ravi Kumar", changed_at=now - timedelta(hours=2)),
            TicketHistory(ticket_id=1, old_status="ASSIGNED", new_status="IN PROGRESS", changed_by_user_id=3, comment="Checking routing table", changed_at=now - timedelta(minutes=110)),
            TicketHistory(ticket_id=2, old_status=None, new_status="OPEN", changed_by_user_id=7, comment="Ticket created", changed_at=now - timedelta(hours=6)),
            TicketHistory(ticket_id=2, old_status="OPEN", new_status="IN PROGRESS", changed_by_user_id=5, comment="Resetting credentials", changed_at=now - timedelta(hours=5)),
            TicketHistory(ticket_id=2, old_status="IN PROGRESS", new_status="RESOLVED", changed_by_user_id=5, comment="Resolved successfully", changed_at=now - timedelta(hours=4)),
        ]
        session.add_all(histories)

        # 10. Comments
        comments = [
            Comment(ticket_id=1, user_id=6, comment_text="Issue occurs when connected via Wi-Fi and Ethernet.", is_internal=False, created_at=now - timedelta(hours=2)),
            Comment(ticket_id=1, user_id=3, comment_text="Re-routing packet traffic to secondary gateway.", is_internal=True, created_at=now - timedelta(minutes=90)),
        ]
        session.add_all(comments)

        # 11. Resolutions
        resolutions = [
            TicketResolution(
                ticket_id=2, agent_id=3, root_cause="Expired active directory credential token",
                resolution_steps="Regenerated authentication token and reset SAP LDAP profile.",
                resolution_category="Access Control", resolved_at=now - timedelta(hours=4)
            ),
            TicketResolution(
                ticket_id=5, agent_id=3, root_cause="Targeted malicious zip attachment",
                resolution_steps="Quarantined mail across tenant and blacklisted sender IP.",
                resolution_category="Security Threat", resolved_at=now - timedelta(hours=22)
            )
        ]
        session.add_all(resolutions)

        logger.info("Database successfully seeded with realistic enterprise mock data!")

if __name__ == "__main__":
    seed_database()
