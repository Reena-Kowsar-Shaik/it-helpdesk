"""Database Initialization and Unified Seeding Script.

Seeds reference data, users, employees, agents, teams, SLA rules, and rich analytics mock tickets.
Usage:
    python seed_db.py                # Initializes and seeds database if empty
    python seed_db.py --reset        # Drops all tables and re-seeds fresh data
    python seed_db.py --rich         # Ensures full historical analytics tickets are populated
"""

import sys
import argparse
from datetime import datetime, timedelta
from core.database import db, Base
from core.auth import PasswordService
from core.models import (
    Department, User, Employee, SupportTeam, SupportAgent,
    Category, SLARule, Ticket, TicketHistory, Comment, TicketResolution, KnowledgeArticle
)
from core.logger import logger

def seed_database(reset: bool = False, include_rich_analytics: bool = True):
    """Create all tables and seed sample data."""
    if reset:
        logger.info("Dropping all existing database tables (--reset enabled)...")
        Base.metadata.drop_all(bind=db.engine)

    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=db.engine)

    with db.get_session() as session:
        # Check if already seeded
        if session.query(User).first() and not reset:
            logger.info("Database already contains data.")
            if include_rich_analytics:
                _seed_rich_analytics_tickets(session)
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
            SupportTeam(team_id=2, name="End User Computing (EUC)", description="Laptops, OS, peripherals, desktop software"),
            SupportTeam(team_id=3, name="Security Operations (SecOps)", description="IAM, access, firewall, incident response"),
        ]
        session.add_all(teams)
        session.flush()

        # 5. Users & Passwords
        demo_users = [
            # Admins & Leads
            User(user_id=1, username="admin", email="admin@enterprise.com", password_hash=PasswordService.hash_password("admin123"), role="Admin"),
            User(user_id=2, username="lead_vikram", email="vikram.lead@enterprise.com", password_hash=PasswordService.hash_password("lead123"), role="Team Lead"),
            # Support Agents
            User(user_id=3, username="ravi_agent", email="ravi.kumar@enterprise.com", password_hash=PasswordService.hash_password("agent123"), role="Support Agent"),
            User(user_id=4, username="priya_agent", email="priya.nair@enterprise.com", password_hash=PasswordService.hash_password("agent123"), role="Support Agent"),
            User(user_id=5, username="arun_agent", email="arun.patel@enterprise.com", password_hash=PasswordService.hash_password("agent123"), role="Support Agent"),
            # Employees
            User(user_id=6, username="john_doe", email="john.doe@enterprise.com", password_hash=PasswordService.hash_password("employee123"), role="Employee"),
            User(user_id=7, username="sarah_hr", email="sarah.jenkins@enterprise.com", password_hash=PasswordService.hash_password("employee123"), role="Employee"),
            User(user_id=8, username="mike_finance", email="mike.ross@enterprise.com", password_hash=PasswordService.hash_password("employee123"), role="Employee"),
            User(user_id=9, username="emily_dev", email="emily.clark@enterprise.com", password_hash=PasswordService.hash_password("employee123"), role="Employee"),
        ]
        session.add_all(demo_users)
        session.flush()

        # 6. Support Agents
        agents = [
            SupportAgent(agent_id=1, user_id=3, team_id=1, full_name="Ravi Kumar", specialization="Network & Firewalls", is_available=True),
            SupportAgent(agent_id=2, user_id=4, team_id=2, full_name="Priya Nair", specialization="Hardware & Workspace", is_available=True),
            SupportAgent(agent_id=3, user_id=5, team_id=3, full_name="Arun Patel", specialization="Security & IAM", is_available=True),
        ]
        session.add_all(agents)
        session.flush()

        # 7. Employees
        employees = [
            Employee(employee_id=1, user_id=6, department_id=4, full_name="John Doe", job_title="Senior Backend Engineer", phone="+1-555-0101"),
            Employee(employee_id=2, user_id=7, department_id=2, full_name="Sarah Jenkins", job_title="HR Talent Lead", phone="+1-555-0102"),
            Employee(employee_id=3, user_id=8, department_id=3, full_name="Mike Ross", job_title="Senior Financial Analyst", phone="+1-555-0103"),
            Employee(employee_id=4, user_id=9, department_id=4, full_name="Emily Clark", job_title="Frontend Specialist", phone="+1-555-0104"),
        ]
        session.add_all(employees)
        session.flush()

        # 8. Base Sample Tickets
        now = datetime.utcnow()
        tickets = [
            Ticket(
                ticket_id=1, ticket_number="TCK-2026-0001", employee_id=1, department_id=4, category_id=1,
                title="VPN Connection failure when connecting to Staging VPC",
                description="Unable to authenticate via Cisco AnyConnect VPN client since morning upgrade.",
                priority="High", status="IN PROGRESS", assigned_team_id=1, assigned_agent_id=1, sla_id=2,
                response_deadline=now - timedelta(minutes=30), resolution_deadline=now + timedelta(hours=3),
                first_responded_at=now - timedelta(minutes=45), created_at=now - timedelta(hours=2)
            ),
            Ticket(
                ticket_id=2, ticket_number="TCK-2026-0002", employee_id=2, department_id=2, category_id=4,
                title="SAP ERP Account Lockout after password change",
                description="Tried resetting credentials via portal but account remains in locked state.",
                priority="Critical", status="RESOLVED", assigned_team_id=3, assigned_agent_id=3, sla_id=1,
                response_deadline=now - timedelta(hours=5), resolution_deadline=now - timedelta(hours=3),
                first_responded_at=now - timedelta(hours=5, minutes=50), resolved_at=now - timedelta(hours=4),
                created_at=now - timedelta(hours=6)
            ),
            Ticket(
                ticket_id=3, ticket_number="TCK-2026-0003", employee_id=3, department_id=3, category_id=2,
                title="External Dell 4K Monitor flickering via USB-C Dock",
                description="Secondary display goes black intermittently when running video calls.",
                priority="Medium", status="OPEN", assigned_team_id=2, assigned_agent_id=None, sla_id=3,
                response_deadline=now + timedelta(hours=1), resolution_deadline=now + timedelta(hours=7),
                created_at=now - timedelta(minutes=40)
            ),
            Ticket(
                ticket_id=4, ticket_number="TCK-2026-0004", employee_id=4, department_id=4, category_id=3,
                title="PyCharm Professional License Key Expired",
                description="IDE prompt requires renewed enterprise jetbrains activation token.",
                priority="Low", status="ASSIGNED", assigned_team_id=2, assigned_agent_id=2, sla_id=4,
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

        # 12. Knowledge Base Articles
        kb_articles = [
            KnowledgeArticle(
                article_id=1,
                category_id=1,
                title="How to Connect to Corporate VPN via Cisco AnyConnect / OpenVPN",
                content="""### Corporate VPN Setup Guide
1. Launch **Cisco AnyConnect Secure Mobility Client** or **OpenVPN Connect**.
2. Enter the gateway host: `vpn.enterprise.com:443`.
3. Enter your Active Directory corporate credentials (`username@enterprise.com`).
4. Approve the push notification on your **Microsoft Authenticator** app.
5. If connection drops, clear DNS cache via terminal (`ipconfig /flushdns` on Windows or `sudo dscacheutil -flushcache` on macOS).""",
                tags="vpn, network, remote work, connectivity, cisco",
                views_count=142,
                helpful_count=38
            ),
            KnowledgeArticle(
                article_id=2,
                category_id=4,
                title="Self-Service Password Reset & MFA Token Re-Registration",
                content="""### Password & Multi-Factor Authentication (MFA)
1. Navigate to the self-service identity portal: `https://identity.enterprise.com/reset`.
2. Confirm identity via secondary email OTP or SMS verification.
3. Passwords must be at least 14 characters, containing uppercase, lowercase, numbers, and symbols.
4. If you upgraded or replaced your mobile phone, submit a ticket under *Access & Authentication* for an instant MFA recovery token.""",
                tags="password, mfa, active directory, lockout, credentials, 2fa",
                views_count=215,
                helpful_count=64
            ),
            KnowledgeArticle(
                article_id=3,
                category_id=2,
                title="Troubleshooting External Monitor Flickering on USB-C Docking Stations",
                content="""### Dell / Lenovo Thunderbolt Dock Troubleshooting
1. Unplug the USB-C dock power cable and hold the dock power button for 15 seconds to discharge residual power.
2. Reconnect the USB-C cable directly to the laptop's primary Thunderbolt port (with the lightning bolt icon).
3. Update Intel/NVIDIA display drivers via the enterprise software portal.
4. Set monitor refresh rate to 60Hz in Display Settings.""",
                tags="monitor, display, dock, hardware, screen, flicker, usb-c",
                views_count=98,
                helpful_count=27
            ),
            KnowledgeArticle(
                article_id=4,
                category_id=3,
                title="Requesting Commercial Software & Developer IDE Licenses",
                content="""### Enterprise Software Procurement
1. Approved tools (JetBrains PyCharm, VS Code Enterprise, Figma, Tableau) can be self-installed from Company Portal.
2. For paid licenses, obtain manager sign-off via email and raise a ticket under *Software & Applications*.
3. License keys will be dispatched within 4 hours during business hours.""",
                tags="software, license, pycharm, figma, installation, developer",
                views_count=76,
                helpful_count=19
            ),
            KnowledgeArticle(
                article_id=5,
                category_id=5,
                title="How to Identify and Report Suspicious Phishing Emails",
                content="""### Phishing & Security Guidelines
1. Check the sender's exact email domain (e.g. `@enterprise-support.com` vs `@enterprise.com`).
2. Never click shortened URLs or execute attachment zip/iso files.
3. Use the **Report Phishing** button in Outlook ribbon or forward the email as attachment to `soc@enterprise.com`.
4. If credentials were submitted, disconnect Wi-Fi and notify IT Security immediately.""",
                tags="security, phishing, email, malware, spam, threat",
                views_count=180,
                helpful_count=52
            )
        ]
        session.add_all(kb_articles)
        session.commit()

        if include_rich_analytics:
            _seed_rich_analytics_tickets(session)

        logger.info("Database successfully seeded with realistic enterprise data!")

def _seed_rich_analytics_tickets(session):
    """Populates historical and active analytics mock tickets for reporting & BI."""
    now = datetime.utcnow()
    sample_tickets_data = [
        # Ravi Kumar (NOC)
        ("TCK-2026-0010", 1, 4, 1, "VPN tunnel degradation between Mumbai and AWS eu-west-1", "Latency spiked to 380ms across redundant IPsec tunnels.", "Critical", "IN PROGRESS", 1, 1, 1, -12, -2, -11, None, None, 0),
        ("TCK-2026-0011", 2, 3, 1, "Finance department subnet unreachable after switch firmware upgrade", "VLAN 40 dropped gateway route on Core Switch 2.", "Critical", "OPEN", 1, 1, 1, -8, -1, None, None, None, 0),
        ("TCK-2026-0012", 3, 2, 1, "Wi-Fi access point AP-04 dropping connections in cafeteria", "Users experiencing frequent de-authentication on 5GHz band.", "Medium", "ASSIGNED", 1, 1, 3, -15, 5, None, None, None, 0),
        ("TCK-2026-0013", 4, 5, 1, "DNS resolution failure for marketing subdomain preview", "CNAME records pointing to expired staging CDN distribution.", "High", "IN PROGRESS", 1, 1, 2, -20, -16, -19, None, None, 0),
        ("TCK-2026-0014", 1, 4, 1, "Corporate firewall blocking outbound Webhook calls to GitHub", "Port 443 egress policy triggered automatic rate limiting rule.", "High", "ASSIGNED", 1, 1, 2, -18, -14, None, None, None, 0),
        ("TCK-2026-0015", 2, 3, 1, "Direct Connect link packet loss on primary BGP circuit", "Carrier reports fiber cut near central metro exchange.", "Critical", "IN PROGRESS", 1, 1, 1, -5, -3, -4, None, None, 0),
        ("TCK-2026-0016", 3, 2, 1, "Guest Wi-Fi portal SSL certificate expiration warning", "Wildcard cert for *.guest.enterprise.com expires in 48 hours.", "Medium", "OPEN", 1, 1, 3, -10, 10, None, None, None, 0),
        ("TCK-2026-0017", 4, 5, 1, "Slow file transfer over SMB share in branch office", "Throughput capped at 1.2 MB/s across SD-WAN tunnel.", "Low", "ASSIGNED", 1, 1, 4, -30, 18, None, None, None, 0),
        ("TCK-2026-0018", 1, 4, 1, "Static IP conflict on engineering lab switch rack 3", "Two test benches configured with same address 192.168.10.45.", "Medium", "IN PROGRESS", 1, 1, 3, -7, 1, -6, None, None, 0),
        ("TCK-2026-0019", 2, 3, 1, "Branch router high CPU utilization alert (98%)", "Spanning tree topology recalculation loop detected on trunk port.", "High", "OPEN", 1, 1, 2, -3, 1, None, None, None, 0),
        ("TCK-2026-0020", 3, 2, 1, "VoIP desk phones unregistering from PBX server", "SIP keepalive UDP packets dropped by stateful inspection rule.", "High", "ASSIGNED", 1, 1, 2, -4, 0, None, None, None, 0),
        ("TCK-2026-0021", 1, 4, 1, "Core router BGP session flapping with upstream ISP", "Session reset every 8 minutes with hold timer expiration.", "Critical", "OPEN", 1, 1, 1, -2, 0, None, None, None, 0),

        # Priya Nair (EUC)
        ("TCK-2026-0022", 2, 3, 2, "Finance executive laptop battery swelling", "Trackpad raised and casing separating on Dell XPS 15.", "Critical", "IN PROGRESS", 2, 2, 1, -14, -12, -13, None, None, 0),
        ("TCK-2026-0023", 3, 2, 2, "HR onboarding workstation setup for 5 new hires", "Configure Windows 11 Enterprise, domain join, and base software image.", "Medium", "ASSIGNED", 2, 2, 3, -24, -16, None, None, None, 0),
        ("TCK-2026-0024", 4, 5, 2, "Logitech conference room MeetUp camera mic failure", "Boardroom A microphone array muffled and disconnecting in Zoom.", "High", "IN PROGRESS", 2, 2, 2, -8, -4, -7, None, None, 0),
        ("TCK-2026-0025", 1, 4, 2, "Mechanical keyboard key chatter on developer station", "Keys space and E registering double strokes.", "Low", "OPEN", 2, 2, 4, -40, 8, None, None, None, 0),
        ("TCK-2026-0026", 2, 3, 2, "Receipt thermal printer paper jam and cutter motor error", "Epson TM-T88VI flashing red error LED continuously.", "Medium", "ASSIGNED", 2, 2, 3, -12, -4, None, None, None, 0),
        ("TCK-2026-0027", 3, 2, 2, "Docking station dual display port black screen issue", "Dell WD19TB dock second monitor flickers off when video plays.", "High", "IN PROGRESS", 2, 2, 2, -6, -2, -5, None, None, 0),

        # Arun Patel (SecOps)
        ("TCK-2026-0028", 4, 5, 4, "Executive Assistant mailbox forwarding rule detected", "External auto-forward rule created without IT Sec approval.", "Critical", "IN PROGRESS", 3, 3, 1, -1, 1, -0.5, None, None, 0),
        ("TCK-2026-0029", 1, 4, 5, "Endpoint protection alert: PowerShell obfuscated script", "CrowdStrike flagged suspicious script in temp directory.", "Critical", "ASSIGNED", 3, 3, 1, -2, 0, None, None, None, 0),
        ("TCK-2026-0030", 2, 3, 4, "Reset multifactor authentication token for remote worker", "Employee replaced smartphone and lost Microsoft Authenticator access.", "High", "OPEN", 3, 3, 2, -1, 3, None, None, None, 0),

        # Historical Resolved Tickets
        ("TCK-2026-0031", 1, 4, 1, "VLAN configuration for automated testing rack", "Provisioned isolated VLAN 210 for CI/CD runners.", "Medium", "RESOLVED", 1, 1, 3, -120, -112, -119, -115, None, 0),
        ("TCK-2026-0032", 2, 3, 1, "VPN client install issue on macOS Sonoma", "Replaced outdated kernel extension with system extension tunnel.", "Medium", "CLOSED", 1, 1, 3, -150, -142, -149, -145, -140, 0),
        ("TCK-2026-0033", 3, 2, 1, "Wi-Fi roaming handoff delay between floors 2 and 3", "Tuned 802.11k/v/r neighbor report thresholds across APs.", "High", "RESOLVED", 1, 1, 2, -90, -86, -89, -87, None, 0),
        ("TCK-2026-0034", 4, 5, 1, "Static route missing for partner marketing portal", "Added route metric 10 for partner IP CIDR block via eth1.", "Medium", "CLOSED", 1, 1, 3, -200, -192, -199, -195, -190, 0),
        ("TCK-2026-0035", 1, 4, 1, "SSL inspection certificate bypass for maven repository", "Whitelisted central.maven.org in firewall proxy SSL decryption.", "High", "RESOLVED", 1, 1, 2, -70, -66, -69, -67, None, 0),
        ("TCK-2026-0036", 2, 3, 1, "Internal DNS record update for accounting staging portal", "Updated A record to point to new cluster load balancer IP.", "Low", "CLOSED", 1, 1, 4, -250, -226, -248, -240, -230, 0),
        ("TCK-2026-0037", 3, 2, 2, "Replaced swollen battery in MacBook Pro 16", "Dispatched hardware replacement and completed diagnostics.", "Critical", "RESOLVED", 2, 2, 1, -100, -98, -99, -98.5, None, 0),
        ("TCK-2026-0038", 4, 5, 3, "Install Figma and Sketch plugins for design team", "Deployed approved Figma enterprise desktop package via Intune.", "Low", "CLOSED", 2, 2, 4, -180, -156, -178, -170, -165, 0),
        ("TCK-2026-0039", 1, 4, 2, "Second display flashing magenta on developer ThinkPad", "Updated Intel Iris Xe graphics driver and replaced HDMI 2.1 cable.", "Medium", "RESOLVED", 2, 2, 3, -110, -102, -109, -105, None, 0),
        ("TCK-2026-0040", 2, 3, 3, "Excel crashed with COM add-in error during macro run", "Disabled legacy Bloomberg COM add-in and updated .NET runtime.", "High", "CLOSED", 2, 2, 2, -60, -56, -59, -57, -50, 0),
        ("TCK-2026-0041", 3, 2, 2, "Barcode scanner USB driver error on inventory desk", "Configured HID keyboard emulation mode via scanner configuration barcode.", "Medium", "RESOLVED", 2, 2, 3, -80, -72, -79, -75, None, 0),
        ("TCK-2026-0042", 4, 5, 2, "Webcam microphone array dead on Dell Latitude 5430", "Reinstalled Realtek high definition audio package and reset permissions.", "High", "CLOSED", 2, 2, 2, -140, -136, -139, -137, -130, 0),
        ("TCK-2026-0043", 1, 4, 3, "Docker Desktop WSL 2 memory limit crash", "Configured .wslconfig with 8GB cap and swap file allocation.", "Medium", "RESOLVED", 2, 2, 3, -50, -42, -49, -45, None, 0),
        ("TCK-2026-0044", 2, 3, 4, "Locked Active Directory account unlock for CFO", "Verified identity via voice callback and unlocked domain account.", "Critical", "CLOSED", 3, 3, 1, -300, -298, -299.8, -298.8, -298, 0),
        ("TCK-2026-0045", 3, 2, 5, "Ransomware canary file trip alert in HR file share", "Isolated workstation 10.10.2.14, confirmed false positive scanner test.", "Critical", "RESOLVED", 3, 3, 1, -85, -83, -84.8, -83.5, None, 0),
        ("TCK-2026-0046", 4, 5, 4, "Provision Salesforce CRM license for new account executive", "Assigned sales cloud license and security profile role in SSO.", "Medium", "CLOSED", 3, 3, 3, -160, -152, -159, -155, -150, 0),
        ("TCK-2026-0047", 1, 4, 5, "Expired SSL certificate on internal API gateway", "Renewed Let's Encrypt certificate and automated certbot cron hook.", "Critical", "RESOLVED", 3, 3, 1, -45, -43, -44.8, -43.8, None, 0),
        ("TCK-2026-0048", 2, 3, 4, "BitLocker recovery key request after BIOS update", "Retrieved recovery key from Azure AD endpoint and guided unlock.", "High", "CLOSED", 3, 3, 2, -130, -126, -129.5, -127.5, -120, 0),
        ("TCK-2026-0049", 3, 2, 4, "Role-based access permission change for payroll folder", "Added HRBP security group to restricted share with approval log.", "Medium", "RESOLVED", 3, 3, 3, -75, -67, -74, -70, None, 0),
        ("TCK-2026-0050", 4, 5, 5, "Phishing email triage targeting engineering group", "Extracted malicious URL, submitted to firewall blacklist.", "Critical", "CLOSED", 3, 3, 1, -210, -208, -209.8, -208.6, -205, 0),

        # Reopened Tickets
        ("TCK-2026-0051", 1, 4, 1, "VPN auto-reconnect fails after laptop sleeps", "Reopened: Fix worked on office network but fails when on home Wi-Fi.", "High", "REOPENED", 1, 1, 2, -60, -56, -59, -50, None, 2),
        ("TCK-2026-0052", 2, 3, 4, "Password sync failing between Active Directory and Workday", "Reopened: Password updated in AD but Workday still rejects credentials.", "Critical", "REOPENED", 3, 3, 1, -40, -38, -39.5, -35, None, 1),
        ("TCK-2026-0053", 3, 2, 2, "Office printer printing blank pages intermittently", "Reopened: Blank page issue recurred after 20 print jobs.", "Medium", "REOPENED", 2, 2, 3, -80, -72, -78, -70, None, 1),
    ]

    existing_numbers = {t.ticket_number for t in session.query(Ticket.ticket_number).all()}
    new_tickets = []
    for row in sample_tickets_data:
        num = row[0]
        if num in existing_numbers:
            continue

        created = now + timedelta(hours=row[11])
        res_deadline = now + timedelta(hours=row[12])
        first_resp = (now + timedelta(hours=row[13])) if row[13] is not None else None
        resolved = (now + timedelta(hours=row[14])) if row[14] is not None else None
        closed = (now + timedelta(hours=row[15])) if row[15] is not None else None

        csat_val = None
        csat_txt = None
        if row[7] in ("RESOLVED", "CLOSED"):
            csat_val = 5 if int(num[-2:]) % 3 != 0 else 4
            feedbacks = [
                "Resolved quickly and effectively!",
                "Great support, very clear instructions.",
                "Issue was fixed smoothly without disruption.",
                "Appreciate the fast turnaround time!",
                "Excellent troubleshooting by the specialist."
            ]
            csat_txt = feedbacks[int(num[-1]) % len(feedbacks)]

        t = Ticket(
            ticket_number=num,
            employee_id=row[1],
            department_id=row[2],
            category_id=row[3],
            title=row[4],
            description=row[5],
            priority=row[6],
            status=row[7],
            assigned_team_id=row[8],
            assigned_agent_id=row[9],
            sla_id=row[10],
            resolution_deadline=res_deadline,
            first_responded_at=first_resp,
            resolved_at=resolved,
            closed_at=closed,
            reopened_count=row[16],
            csat_rating=csat_val,
            csat_feedback=csat_txt,
            created_at=created
        )
        new_tickets.append(t)

    if new_tickets:
        session.add_all(new_tickets)
        session.flush()

        resolutions = [
            TicketResolution(
                ticket_id=t.ticket_id,
                agent_id=t.assigned_agent_id,
                root_cause=f"Identified root cause for {t.title}: configuration or component issue.",
                resolution_steps=f"Executed standard remediation procedure and verified system health.",
                resolution_category="Technical Fix" if t.category_id in (1, 2, 3) else "Access/Security",
                resolved_at=t.resolved_at
            )
            for t in new_tickets if t.status in ("RESOLVED", "CLOSED") and t.assigned_agent_id
        ]
        session.add_all(resolutions)
        session.commit()
        logger.info(f"Enriched database with {len(new_tickets)} enterprise mock tickets.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed IT Helpdesk Database")
    parser.add_argument("--reset", action="store_true", help="Drop existing tables and recreate schema")
    parser.add_argument("--rich", action="store_true", default=True, help="Include rich analytics mock data")
    args = parser.parse_args()

    seed_database(reset=args.reset, include_rich_analytics=args.rich)
