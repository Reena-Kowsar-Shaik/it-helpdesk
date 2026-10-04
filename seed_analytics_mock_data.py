"""Enrich database with diverse historical and active tickets for advanced analytics."""

import random
from datetime import datetime, timedelta
from core.database import db
from core.models import Ticket, TicketHistory, TicketResolution, Comment

def enrich_data():
    now = datetime.utcnow()

    # Pre-defined ticket scenarios
    sample_tickets_data = [
        # Ravi Kumar (NOC) - Overloaded queue
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

        # Priya Nair (EUC) - Moderate queue
        ("TCK-2026-0022", 2, 3, 2, "Finance executive laptop battery swelling", "Trackpad raised and casing separating on Dell XPS 15.", "Critical", "IN PROGRESS", 2, 2, 1, -14, -12, -13, None, None, 0),
        ("TCK-2026-0023", 3, 2, 2, "HR onboarding workstation setup for 5 new hires", "Configure Windows 11 Enterprise, domain join, and base software image.", "Medium", "ASSIGNED", 2, 2, 3, -24, -16, None, None, None, 0),
        ("TCK-2026-0024", 4, 5, 2, "Logitech conference room MeetUp camera mic failure", "Boardroom A microphone array muffled and disconnecting in Zoom.", "High", "IN PROGRESS", 2, 2, 2, -8, -4, -7, None, None, 0),
        ("TCK-2026-0025", 1, 4, 2, "Mechanical keyboard key chatter on developer station", "Keys space and E registering double strokes.", "Low", "OPEN", 2, 2, 4, -40, 8, None, None, None, 0),
        ("TCK-2026-0026", 2, 3, 2, "Receipt thermal printer paper jam and cutter motor error", "Epson TM-T88VI flashing red error LED continuously.", "Medium", "ASSIGNED", 2, 2, 3, -12, -4, None, None, None, 0),
        ("TCK-2026-0027", 3, 2, 2, "Docking station dual display port black screen issue", "Dell WD19TB dock second monitor flickers off when video plays.", "High", "IN PROGRESS", 2, 2, 2, -6, -2, -5, None, None, 0),

        # Arun Patel (SecOps) - Optimal queue
        ("TCK-2026-0028", 4, 5, 4, "Executive Assistant mailbox forwarding rule detected", "External auto-forward rule created without IT Sec approval.", "Critical", "IN PROGRESS", 3, 3, 1, -1, 1, -0.5, None, None, 0),
        ("TCK-2026-0029", 1, 4, 5, "Endpoint protection alert: PowerShell obfuscated script", "CrowdStrike flagged suspicious script in temp directory.", "Critical", "ASSIGNED", 3, 3, 1, -2, 0, None, None, None, 0),
        ("TCK-2026-0030", 2, 3, 4, "Reset multifactor authentication token for remote worker", "Employee replaced smartphone and lost Microsoft Authenticator access.", "High", "OPEN", 3, 3, 2, -1, 3, None, None, None, 0),

        # Historical Resolved Tickets for Agent Rankings & SLA Metrics
        # Ravi Kumar resolved tickets
        ("TCK-2026-0031", 1, 4, 1, "VLAN configuration for automated testing rack", "Provisioned isolated VLAN 210 for CI/CD runners.", "Medium", "RESOLVED", 1, 1, 3, -120, -112, -119, -115, None, 0),
        ("TCK-2026-0032", 2, 3, 1, "VPN client install issue on macOS Sonoma", "Replaced outdated kernel extension with system extension tunnel.", "Medium", "CLOSED", 1, 1, 3, -150, -142, -149, -145, -140, 0),
        ("TCK-2026-0033", 3, 2, 1, "Wi-Fi roaming handoff delay between floors 2 and 3", "Tuned 802.11k/v/r neighbor report thresholds across APs.", "High", "RESOLVED", 1, 1, 2, -90, -86, -89, -87, None, 0),
        ("TCK-2026-0034", 4, 5, 1, "Static route missing for partner marketing portal", "Added route metric 10 for partner IP CIDR block via eth1.", "Medium", "CLOSED", 1, 1, 3, -200, -192, -199, -195, -190, 0),
        ("TCK-2026-0035", 1, 4, 1, "SSL inspection certificate bypass for maven repository", "Whitelisted central.maven.org in firewall proxy SSL decryption.", "High", "RESOLVED", 1, 1, 2, -70, -66, -69, -67, None, 0),
        ("TCK-2026-0036", 2, 3, 1, "Internal DNS record update for accounting staging portal", "Updated A record to point to new cluster load balancer IP.", "Low", "CLOSED", 1, 1, 4, -250, -226, -248, -240, -230, 0),

        # Priya Nair resolved tickets
        ("TCK-2026-0037", 3, 2, 2, "Replaced swollen battery in MacBook Pro 16", "Dispatched hardware replacement and completed diagnostics.", "Critical", "RESOLVED", 2, 2, 1, -100, -98, -99, -98.5, None, 0),
        ("TCK-2026-0038", 4, 5, 3, "Install Figma and Sketch plugins for design team", "Deployed approved Figma enterprise desktop package via Intune.", "Low", "CLOSED", 2, 2, 4, -180, -156, -178, -170, -165, 0),
        ("TCK-2026-0039", 1, 4, 2, "Second display flashing magenta on developer ThinkPad", "Updated Intel Iris Xe graphics driver and replaced HDMI 2.1 cable.", "Medium", "RESOLVED", 2, 2, 3, -110, -102, -109, -105, None, 0),
        ("TCK-2026-0040", 2, 3, 3, "Excel crashed with COM add-in error during macro run", "Disabled legacy Bloomberg COM add-in and updated .NET runtime.", "High", "CLOSED", 2, 2, 2, -60, -56, -59, -57, -50, 0),
        ("TCK-2026-0041", 3, 2, 2, "Barcode scanner USB driver error on inventory desk", "Configured HID keyboard emulation mode via scanner configuration barcode.", "Medium", "RESOLVED", 2, 2, 3, -80, -72, -79, -75, None, 0),
        ("TCK-2026-0042", 4, 5, 2, "Webcam microphone array dead on Dell Latitude 5430", "Reinstalled Realtek high definition audio package and reset permissions.", "High", "CLOSED", 2, 2, 2, -140, -136, -139, -137, -130, 0),
        ("TCK-2026-0043", 1, 4, 3, "Docker Desktop WSL 2 memory limit crash", "Configured .wslconfig with 8GB cap and swap file allocation.", "Medium", "RESOLVED", 2, 2, 3, -50, -42, -49, -45, None, 0),

        # Arun Patel resolved tickets (High SLA compliance champion)
        ("TCK-2026-0044", 2, 3, 4, "Locked Active Directory account unlock for CFO", "Verified identity via voice callback and unlocked domain account.", "Critical", "CLOSED", 3, 3, 1, -300, -298, -299.8, -298.8, -298, 0),
        ("TCK-2026-0045", 3, 2, 5, "Ransomware canary file trip alert in HR file share", "Isolated workstation 10.10.2.14, confirmed false positive scanner test.", "Critical", "RESOLVED", 3, 3, 1, -85, -83, -84.8, -83.5, None, 0),
        ("TCK-2026-0046", 4, 5, 4, "Provision Salesforce CRM license for new account executive", "Assigned sales cloud license and security profile role in SSO.", "Medium", "CLOSED", 3, 3, 3, -160, -152, -159, -155, -150, 0),
        ("TCK-2026-0047", 1, 4, 5, "Expired SSL certificate on internal API gateway", "Renewed Let's Encrypt certificate and automated certbot cron hook.", "Critical", "RESOLVED", 3, 3, 1, -45, -43, -44.8, -43.8, None, 0),
        ("TCK-2026-0048", 2, 3, 4, "BitLocker recovery key request after BIOS update", "Retrieved recovery key from Azure AD endpoint and guided unlock.", "High", "CLOSED", 3, 3, 2, -130, -126, -129.5, -127.5, -120, 0),
        ("TCK-2026-0049", 3, 2, 4, "Role-based access permission change for payroll folder", "Added HRBP security group to restricted share with approval log.", "Medium", "RESOLVED", 3, 3, 3, -75, -67, -74, -70, None, 0),
        ("TCK-2026-0050", 4, 5, 5, "Phishing email triage targeting engineering group", "Extracted malicious URL, submitted to firewall blacklist.", "Critical", "CLOSED", 3, 3, 1, -210, -208, -209.8, -208.6, -205, 0),

        # Reopened Tickets (for Reopened analysis)
        ("TCK-2026-0051", 1, 4, 1, "VPN auto-reconnect fails after laptop sleeps", "Reopened: Fix worked on office network but fails when on home Wi-Fi.", "High", "REOPENED", 1, 1, 2, -60, -56, -59, -50, None, 2),
        ("TCK-2026-0052", 2, 3, 4, "Password sync failing between Active Directory and Workday", "Reopened: Password updated in AD but Workday still rejects credentials.", "Critical", "REOPENED", 3, 3, 1, -40, -38, -39.5, -35, None, 1),
        ("TCK-2026-0053", 3, 2, 2, "Office printer printing blank pages intermittently", "Reopened: Blank page issue recurred after 20 print jobs.", "Medium", "REOPENED", 2, 2, 3, -80, -72, -78, -70, None, 1),
    ]

    with db.get_session() as session:
        # Check existing count
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
                created_at=created
            )
            new_tickets.append(t)

        if new_tickets:
            session.add_all(new_tickets)
            session.flush()
            print(f"Added {len(new_tickets)} enterprise tickets.")

            # Add resolutions for resolved tickets
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
            print(f"Added {len(resolutions)} ticket resolutions.")
        else:
            print("No new tickets needed.")

if __name__ == "__main__":
    enrich_data()
