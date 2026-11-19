import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import hashlib
import random
from datetime import datetime, timedelta
from database.connection import db_manager
from utils.logger import get_logger
import config

logger = get_logger("seed_data")

def hash_pw(password: str) -> str:
    """Generates a secure SHA-256 hash for seed users."""
    return hashlib.sha256(password.encode()).hexdigest()

def seed_database():
    """Populates the database with rich, realistic enterprise IT data."""
    logger.info("Initializing database schema...")
    db_manager.init_db(force_recreate=True)

    # 1. SEED DEPARTMENTS
    departments = [
        ("Software Engineering", "ENG", "Dr. Alex Wright", "eng-lead@enterprise.com", "BU-101"),
        ("Sales & Marketing", "SALES", "Sophia Martinez", "sales-lead@enterprise.com", "BU-202"),
        ("Finance & Accounts", "FIN", "Robert Vance", "finance@enterprise.com", "BU-303"),
        ("Human Resources", "HR", "Emily Watson", "hr@enterprise.com", "BU-404"),
        ("Customer Operations", "OPS", "David Miller", "ops-lead@enterprise.com", "BU-505"),
    ]
    for d in departments:
        db_manager.execute_non_query(
            "INSERT INTO departments (name, code, head_name, contact_email, budget_code) VALUES (:1, :2, :3, :4, :5)",
            {"1": d[0], "2": d[1], "3": d[2], "4": d[3], "5": d[4]}
        )

    # 2. SEED SUPPORT TEAMS
    teams = [
        ("Tier-1 Service Desk", "First Contact Resolution, Password Resets & General Triage", "John Carter", "24x7 Coverage"),
        ("Infrastructure & Cloud Ops", "Servers, VPNs, AWS/Azure, Databases & Networks", "Samantha Reed", "24x7 Shift"),
        ("Cybersecurity & IAM", "Access Controls, SSO, Endpoint Security, Malware & Phishing", "Marcus Brody", "9am - 8pm EST"),
        ("Workplace Hardware Support", "Laptops, Monitors, MacBooks, Peripherals & Repairs", "Liam O'Connor", "9am - 6pm EST"),
    ]
    for t in teams:
        db_manager.execute_non_query(
            "INSERT INTO support_teams (name, specialization, lead_name, operating_hours) VALUES (:1, :2, :3, :4)",
            {"1": t[0], "2": t[1], "3": t[2], "4": t[3]}
        )

    # 3. SEED SLA POLICIES
    sla_policies = [
        ("Critical", 0.5, 4.0, 2.0, "P1 Incidents: Severe business disruption or outage. 30min response, 4h fix."),
        ("High", 1.0, 8.0, 4.0, "P2 Incidents: High impact, major feature offline or blocked employee."),
        ("Medium", 4.0, 24.0, 16.0, "P3 Incidents: Normal operational requests & software glitches."),
        ("Low", 8.0, 48.0, 36.0, "P4 Requests: General inquiries, hardware upgrades & minor requests."),
    ]
    for sla in sla_policies:
        db_manager.execute_non_query(
            "INSERT INTO sla_policies (priority, response_time_hours, resolution_time_hours, escalation_time_hours, description) VALUES (:1, :2, :3, :4, :5)",
            {"1": sla[0], "2": sla[1], "3": sla[2], "4": sla[3], "5": sla[4]}
        )

    # 4. SEED USERS (Password for all demo accounts: 'admin123' or 'password123')
    default_pw = hash_pw("admin123")
    users = [
        # Admins & Leads
        ("Admin Root", "admin@enterprise.com", default_pw, "IT Admin", 1, "IT Operations Director", "+1-555-0101"),
        ("Executive Chief", "cio@enterprise.com", default_pw, "Executive", 1, "Chief Information Officer", "+1-555-0100"),
        ("John Carter", "john.carter@enterprise.com", default_pw, "Team Lead", 1, "ServiceDesk Lead", "+1-555-0102"),
        ("Samantha Reed", "samantha.r@enterprise.com", default_pw, "Team Lead", 1, "Cloud Ops Lead", "+1-555-0103"),

        # Support Agents
        ("Alice Chen", "alice.chen@enterprise.com", default_pw, "Support Agent", 1, "Senior Support Specialist", "+1-555-0104"),
        ("Brian Taylor", "brian.t@enterprise.com", default_pw, "Support Agent", 1, "Cloud Systems Engineer", "+1-555-0105"),
        ("Chloe Bennett", "chloe.b@enterprise.com", default_pw, "Support Agent", 1, "Security Analyst", "+1-555-0106"),
        ("Daniel Kim", "daniel.k@enterprise.com", default_pw, "Support Agent", 1, "Hardware Tech Specialist", "+1-555-0107"),
        ("Elena Rostova", "elena.r@enterprise.com", default_pw, "Support Agent", 1, "L1 Triage Support Agent", "+1-555-0108"),

        # Regular Employees (Requesters)
        ("Michael Scott", "michael.s@enterprise.com", default_pw, "Employee", 2, "Regional Sales Director", "+1-555-0201"),
        ("Jim Halpert", "jim.h@enterprise.com", default_pw, "Employee", 2, "Senior Sales Executive", "+1-555-0202"),
        ("Pam Beesly", "pam.b@enterprise.com", default_pw, "Employee", 4, "Office Administrator", "+1-555-0203"),
        ("Dwight Schrute", "dwight.s@enterprise.com", default_pw, "Employee", 2, "Assistant Regional Manager", "+1-555-0204"),
        ("Angela Martin", "angela.m@enterprise.com", default_pw, "Employee", 3, "Senior Accountant", "+1-555-0205"),
        ("Kevin Malone", "kevin.m@enterprise.com", default_pw, "Employee", 3, "Accountant", "+1-555-0206"),
        ("Oscar Martinez", "oscar.m@enterprise.com", default_pw, "Employee", 3, "Financial Analyst", "+1-555-0207"),
        ("Toby Flenderson", "toby.f@enterprise.com", default_pw, "Employee", 4, "HR Specialist", "+1-555-0208"),
        ("Ryan Howard", "ryan.h@enterprise.com", default_pw, "Employee", 5, "Product Operations Lead", "+1-555-0209"),
        ("Kelly Kapoor", "kelly.k@enterprise.com", default_pw, "Employee", 5, "Customer Care Representative", "+1-555-0210"),
    ]

    for u in users:
        db_manager.execute_non_query(
            """INSERT INTO users (full_name, email, password_hash, role, department_id, designation, phone) 
               VALUES (:1, :2, :3, :4, :5, :6, :7)""",
            {"1": u[0], "2": u[1], "3": u[2], "4": u[3], "5": u[4], "6": u[5], "7": u[6]}
        )

    # 5. SEED AGENTS (linking users 5-9 to support teams)
    agents = [
        # (user_id, team_id, tier, max_tickets, status, skills)
        (5, 1, "L2", 12, "Available", "Windows 11, Office365, Active Directory, Triage"),
        (6, 2, "L3", 8, "Available", "AWS EC2, PostgreSQL, Docker, Kubernetes, Linux"),
        (7, 3, "Specialist", 10, "Available", "Okta SSO, CrowdStrike, Firewalls, MFA Reset"),
        (8, 4, "L1", 15, "Available", "MacBook Pro, Dell XPS, Printers, DisplayPorts"),
        (9, 1, "L1", 14, "Busy", "First Contact Support, Zoom, Slack, VPN setup"),
    ]
    for a in agents:
        db_manager.execute_non_query(
            """INSERT INTO agents (user_id, team_id, tier, max_active_tickets, status, skills)
               VALUES (:1, :2, :3, :4, :5, :6)""",
            {"1": a[0], "2": a[1], "3": a[2], "4": a[3], "5": a[4], "6": a[5]}
        )

    # 6. SEED KNOWLEDGE BASE
    kb_articles = [
        ("How to configure Enterprise GlobalProtect VPN", "Network & VPN Connectivity", 
         "1. Download GlobalProtect from the internal portal.\n2. Enter portal address: `vpn.enterprise.com`.\n3. Authenticate with Okta MFA push notification.\n4. Ensure split-tunneling is enabled.", 
         "vpn, remote-work, globalprotect, network", 142, 38, 1),
        ("Troubleshooting Blue Screen / Kernel Panic on Windows", "Hardware & Workstations",
         "If encountering DRIVER_IRQL_NOT_LESS_OR_EQUAL:\n1. Restart in Safe Mode.\n2. Run `sfc /scannow` in Admin Terminal.\n3. Check Dell Command Update for graphics drivers.\n4. Contact Tier-1 if dump persists.",
         "bsod, crash, windows, driver, reboot", 95, 21, 1),
        ("Resetting Expired Corporate Okta Password", "Identity & Access Management",
         "Visit https://sso.enterprise.com/recovery\n- Enter corporate email\n- Use SMS / YubiKey MFA token\n- Password must be at least 14 characters with uppercase, symbols, and numbers.",
         "password, okta, sso, reset, login", 310, 89, 1),
        ("Connecting to Office High-Speed Secure Wi-Fi (Enterprise 802.1X)", "Network & VPN Connectivity",
         "Select SSID: 'Corp-Internal-5G'\nEAP Method: PEAP\nPhase 2 Auth: MSCHAPv2\nCA Certificate: Trust on First Use / Enterprise Root CA.",
         "wifi, wireless, network, internet, connection", 215, 67, 1),
    ]
    for kb in kb_articles:
        db_manager.execute_non_query(
            """INSERT INTO knowledge_base (title, category, content, tags, view_count, helpful_count, created_by)
               VALUES (:1, :2, :3, :4, :5, :6, :7)""",
            {"1": kb[0], "2": kb[1], "3": kb[2], "4": kb[3], "5": kb[4], "6": kb[5], "7": kb[6]}
        )

    # 7. SEED CANNED RESPONSES
    canned = [
        ("Password Reset Standard Instructions", "Identity & Access Management", 
         "Hello, we have initiated a self-service password reset token to your secondary phone number. Please follow the instructions at sso.enterprise.com/recovery and reply if you need further help.", "PR_RESET"),
        ("VPN Split-Tunneling Quick Fix", "Network & VPN Connectivity",
         "Hi, please disconnect GlobalProtect VPN, close open browsers, toggle Wi-Fi off and on, and reconnect using gateway 'gw-east.enterprise.com'.", "VPN_FIX"),
        ("Laptop Replacement Policy Acknowledgement", "Hardware & Workstations",
         "Your hardware refresh ticket has been approved by IT Ops. Please bring your older asset to Room 4B on Tuesday between 10am-3pm to receive your new MacBook/Dell laptop.", "HW_REFRESH"),
    ]
    for c in canned:
        db_manager.execute_non_query(
            "INSERT INTO canned_responses (title, category, message_body, shortcut_code) VALUES (:1, :2, :3, :4)",
            {"1": c[0], "2": c[1], "3": c[2], "4": c[3]}
        )

    # 8. SEED TICKETS (Comprehensive realistic dataset)
    now = datetime.now()
    ticket_samples = [
        # (title, description, category, priority, status, requester_id, dept_id, team_id, agent_id, days_ago, res_hours, sla_breached, reopen, csat, root_cause, notes)
        ("Production Database Connection Timeout", "Financial reporting jobs failing due to DB connection pool exhaustion in read replica.", "Database & Cloud Infrastructure", "Critical", "Resolved", 14, 3, 2, 2, 25, 3.2, 0, 0, 5, "Connection pool maxed out at 500 connections", "Scaled connection pool and added PgBouncer proxy."),
        ("VPN Disconnecting Every 10 Minutes", "GlobalProtect drops VPN tunnel continuously while on home Wi-Fi.", "Network & VPN Connectivity", "High", "Resolved", 10, 2, 2, 2, 20, 6.5, 0, 0, 4, "MTU packet size mismatch on ISP router", "Adjusted MTU size to 1350 in VPN adapter settings."),
        ("Cannot Log In to Salesforce SSO", "Okta prompt gives error 'User not assigned to application group'. Blocked from client calls.", "Identity & Access Management", "High", "Resolved", 11, 2, 3, 3, 18, 2.1, 0, 0, 5, "Sales security group assignment missing in Okta directory", "Assigned user to Salesforce-Standard-Sales role in Active Directory."),
        ("MacBook Pro Screen Flickering & Freeze", "Display flashes horizontal purple lines and kernel panics upon connecting external 4K monitor.", "Hardware & Workstations", "Medium", "Resolved", 12, 4, 4, 4, 15, 22.0, 0, 0, 5, "Faulty Thunderbolt 4 cable and outdated DisplayLink driver", "Replaced cable and updated macOS DisplayLink drivers."),
        ("Payroll Spreadsheet Macro Crashing Excel", "Excel 365 crashes instantly when calculating Q3 bonus withholding macros.", "Software & Licensing", "Critical", "Resolved", 15, 3, 1, 1, 14, 5.5, 1, 1, 3, "64-bit Office VBA incompatibility with 32-bit legacy DLLs", "Re-compiled DLL wrapper for 64-bit Excel."),
        ("Request for Docker Desktop License", "Need licensed Docker Desktop for microservices local development.", "Software & Licensing", "Low", "Closed", 10, 1, 1, 5, 12, 18.0, 0, 0, 5, "Standard software request", "Assigned business seat license via Docker Admin Console."),
        ("Conference Room 3B Polycom Teams Mic Not Working", "Mic dead during hybrid client pitch meeting. Echoing loudly.", "Hardware & Workstations", "High", "Resolved", 13, 2, 4, 4, 10, 7.8, 0, 0, 4, "USB audio interface firmware stuck in sleep mode", "Power cycled USB DAC and updated Poly firmware."),
        ("Suspected Phishing Email Received", "Received fake DocuSign invoice from unknown sender claiming $14,000 overdue fee.", "Security & Incident Response", "Critical", "Closed", 16, 3, 3, 3, 8, 1.5, 0, 0, 5, "Credential harvesting phishing campaign", "Quarantined email domain across Microsoft Defender 365."),
        ("HR BambooHR Portal Access Denied", "New hire cannot view benefits enrollment page. Gets 403 Forbidden.", "Identity & Access Management", "Medium", "Resolved", 17, 4, 3, 3, 7, 14.0, 0, 0, 4, "Role synchronization delay between Workday and BambooHR", "Forced manual API sync between HR systems."),
        ("Slow Wi-Fi on 4th Floor Marketing Wing", "Speed tests showing only 1.2 Mbps download speed on Corp-Internal Wi-Fi.", "Network & VPN Connectivity", "Medium", "In Progress", 11, 2, 2, 2, 3, None, 0, 0, None, None, "Investigating AP channel interference on 5GHz band."),
        ("Outlook Search Index Broken on Windows 11", "Searching for emails returns zero results even for recent emails.", "Email & Communication Systems", "Low", "In Progress", 18, 5, 1, 5, 2, None, 0, 0, None, None, "Rebuilding Windows search catalog indexing database."),
        ("Dell XPS Battery Swelling Warning", "Trackpad is popping out of laptop chassis, urgent hardware inspection needed.", "Hardware & Workstations", "Critical", "In Progress", 19, 5, 4, 4, 1, None, 0, 0, None, None, "Safety hazard: Replacement XPS 15 prepared for dispatch."),
        ("AWS Production Kubernetes Pod CrashLoopBackOff", "Customer API service pods failing liveness probes under peak load.", "Database & Cloud Infrastructure", "Critical", "Assigned", 10, 1, 2, 2, 1, None, 0, 0, None, None, "Investigating OOM killer memory limit thresholds."),
        ("Need Access to Git Repository 'core-payments'", "New engineer joined team, needs read/write permissions to GitHub repo.", "Identity & Access Management", "Medium", "Open", 10, 1, 3, None, 0, None, 0, 0, None, None, None),
        ("Printer on 2nd Floor Paper Jam & Toner Low", "Department laser printer flashing error 13.00.00 Paper Jam and Cyan toner empty.", "Printer & Peripherals", "Low", "Open", 14, 3, 4, None, 0, None, 0, 0, None, None, None),
        ("Zoom Room Speaker Echo in Boardroom", "Board meeting audio has 2-second acoustic feedback loop.", "Hardware & Workstations", "High", "Open", 17, 4, 4, None, 0, None, 0, 0, None, None, None),
        ("Weekly Billing Job Out of Memory Error", "Batch transaction process crashed at 3 AM with Java Heap Space Error.", "Database & Cloud Infrastructure", "High", "Resolved", 15, 3, 2, 2, 30, 9.2, 1, 1, 2, "Unindexed transaction query doing full table scan on 20M rows", "Added composite index on `transactions(created_at, status)` and allocated 16GB JVM heap."),
        ("Jira Cloud Service Account Token Renewal", "Automated deployment webhook failing authentication against Jira API.", "Software & Licensing", "Medium", "Resolved", 10, 1, 1, 1, 35, 12.0, 0, 0, 5, "Expired API access token", "Generated rotated bearer token with 180-day expiry."),
        ("Keyboard Spacebar Sticky on Lenovo ThinkPad", "Physical key stuck after coffee splash.", "Hardware & Workstations", "Low", "Closed", 12, 4, 4, 4, 40, 30.0, 0, 0, 4, "Physical liquid damage", "Replaced top keyboard assembly under on-site warranty."),
        ("Slack Desktop App Freezing on Screen Share", "Sharing 4K monitor causes Slack to freeze entirely on macOS Sonoma.", "Email & Communication Systems", "Medium", "Closed", 11, 2, 1, 5, 42, 16.0, 0, 0, 4, "Hardware acceleration bug with Metal rendering", "Disabled hardware acceleration in Slack advanced preferences."),
        ("Suspicious Foreign Login Attempt on CEO Office365", "Login from Lagos, Nigeria flagged by Azure Conditional Access.", "Security & Incident Response", "Critical", "Closed", 1, 1, 3, 3, 45, 0.8, 0, 0, 5, "Credential breach from third-party vendor compromise", "Revoked all active sessions, forced password reset, and locked IP range."),
        ("Tableau Server License Expiration Warning", "Dashboard users seeing red banner 'License expires in 48 hours'.", "Software & Licensing", "High", "Closed", 16, 3, 1, 1, 50, 6.0, 0, 0, 5, "Annual renewal key was not activated on primary node", "Applied newly purchased core license keys."),
        ("Wi-Fi Certificate Expired on Guest Network", "Contractors unable to connect to 'Enterprise-Guest' Wi-Fi portal.", "Network & VPN Connectivity", "High", "Closed", 13, 2, 2, 2, 55, 7.5, 0, 0, 4, "Radius server SSL certificate expired", "Renewed wildcard SSL certificate on Radius auth server."),
        ("Customer Data Export Script Broken", "Nightly Python ETL script failing with S3 AccessDenied exception.", "Database & Cloud Infrastructure", "High", "Closed", 18, 5, 2, 2, 60, 5.0, 0, 0, 5, "IAM role permissions were pruned during security cleanup", "Restored required S3:GetObject and S3:PutObject policy."),
        ("Dual Monitor DisplayPort Cable Missing", "Need second display cable for new 27-inch Dell UltraSharp monitor.", "Printer & Peripherals", "Low", "Closed", 19, 5, 4, 4, 65, 20.0, 0, 0, 5, "Peripheral request", "Provided DisplayPort to USB-C cable from IT storage."),
        ("Intranet SharePoint Wiki Search Down", "Searching internal policies returns 500 internal server error.", "Software & Licensing", "Medium", "Closed", 17, 4, 1, 1, 70, 19.5, 0, 0, 4, "Elasticsearch cluster node ran out of disk space", "Cleaned up old log indexes and expanded disk volume."),
        ("Malware Quarantine on Sales Laptop", "Windows Defender flagged Trojan:Win32/Wacatac in Downloads folder.", "Security & Incident Response", "Critical", "Closed", 13, 2, 3, 3, 75, 1.2, 0, 0, 5, "Downloaded infected attachment from malicious recruiter email", "Isolated host, purged infected temp file, completed full endpoint scan."),
        ("Reopened: VPN Drops During Video Calls", "Ticket #1002 was closed but issue returned when running Zoom on VPN.", "Network & VPN Connectivity", "High", "Resolved", 10, 2, 2, 2, 12, 10.0, 1, 2, 3, "UDP port blocking on client home router", "Switched GlobalProtect tunnel transport protocol from IPsec to SSL."),
        ("Reopened: Payroll Tax Formula Bug in ERP", "Calculations for state tax still omitting Oregon surcharge.", "Software & Licensing", "Critical", "Resolved", 15, 3, 1, 1, 8, 4.0, 0, 1, 4, "Missing state tax rule table mapping", "Updated NetSuite tax nexus mapping rules for Oregon.")
    ]

    ticket_counter = 1001
    for t in ticket_samples:
        title, desc, cat, prio, status, req_id, dept_id, team_id, ag_id, days_ago, res_hrs, breached, reopens, csat, root_c, notes = t
        
        created_dt = now - timedelta(days=days_ago, hours=random.randint(1, 12), minutes=random.randint(5, 55))
        sla_hours = config.DEFAULT_SLA.get(prio, {}).get("resolution", 24)
        sla_due_dt = created_dt + timedelta(hours=sla_hours)
        
        first_resp_dt = created_dt + timedelta(minutes=random.randint(15, 90))
        resolved_dt = created_dt + timedelta(hours=res_hrs) if res_hrs else None
        closed_dt = resolved_dt + timedelta(hours=random.randint(4, 24)) if resolved_dt and status == "Closed" else None
        
        # Check actual breach
        is_breached = breached
        if res_hrs and res_hrs > sla_hours:
            is_breached = 1

        ticket_no = f"TCK-{ticket_counter}"
        ticket_counter += 1

        db_manager.execute_non_query(
            """INSERT INTO tickets (
                ticket_number, title, description, category, priority, status,
                requester_id, department_id, team_id, assigned_agent_id,
                created_at, first_response_at, resolved_at, closed_at, sla_due_date,
                sla_breached, reopen_count, satisfaction_rating, resolution_notes, root_cause,
                actual_hours
            ) VALUES (
                :t_num, :title, :desc, :cat, :prio, :status,
                :req_id, :dept_id, :team_id, :ag_id,
                :created_at, :first_resp, :resolved_at, :closed_at, :sla_due,
                :sla_breached, :reopen_cnt, :csat, :notes, :root_c,
                :act_hrs
            )""",
            {
                "t_num": ticket_no,
                "title": title,
                "desc": desc,
                "cat": cat,
                "prio": prio,
                "status": status,
                "req_id": req_id,
                "dept_id": dept_id,
                "team_id": team_id,
                "ag_id": ag_id,
                "created_at": created_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "first_resp": first_resp_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "resolved_at": resolved_dt.strftime("%Y-%m-%d %H:%M:%S") if resolved_dt else None,
                "closed_at": closed_dt.strftime("%Y-%m-%d %H:%M:%S") if closed_dt else None,
                "sla_due": sla_due_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "sla_breached": is_breached,
                "reopen_cnt": reopens,
                "csat": csat,
                "notes": notes,
                "root_c": root_c,
                "act_hrs": res_hrs
            }
        )

        # Insert ticket history audit
        db_manager.execute_non_query(
            """INSERT INTO ticket_history (ticket_id, changed_by, action_type, old_status, new_status, notes, created_at)
               VALUES (:1, :2, :3, :4, :5, :6, :7)""",
            {
                "1": ticket_counter - 1001,
                "2": req_id,
                "3": "Ticket Created",
                "4": None,
                "5": "Open",
                "6": "Ticket submitted via Web Portal",
                "7": created_dt.strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        if ag_id:
            db_manager.execute_non_query(
                """INSERT INTO ticket_history (ticket_id, changed_by, action_type, old_status, new_status, notes, created_at)
                   VALUES (:1, :2, :3, :4, :5, :6, :7)""",
                {
                    "1": ticket_counter - 1001,
                    "2": ag_id,
                    "3": "Status Updated",
                    "4": "Open",
                    "5": status,
                    "6": notes or "Assigned and in active remediation",
                    "7": (created_dt + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
                }
            )

    logger.info("Database successfully seeded with realistic enterprise IT records!")
    return True

if __name__ == "__main__":
    seed_database()
