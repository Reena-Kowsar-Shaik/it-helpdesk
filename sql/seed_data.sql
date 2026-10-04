-- ==========================================================
-- IT Helpdesk & Ticket Management System Seed Data
-- Passwords:
--   admin / admin123
--   lead_vikram / lead123
--   ravi_agent / agent123
--   priya_agent / agent123
--   arun_agent / agent123
--   john_doe / employee123
--   sarah_smith / employee123
--   amit_sharma / employee123
--   neha_verma / employee123
-- ==========================================================

USE it_helpdesk_db;

-- 1. DEPARTMENTS
INSERT INTO departments (department_id, name, code, description) VALUES
(1, 'Information Technology', 'IT', 'Internal IT Infrastructure, Network & Systems'),
(2, 'Human Resources', 'HR', 'HR Management, Onboarding, Payroll inquiries'),
(3, 'Finance & Accounting', 'FIN', 'Accounts Payable, Billing, Audit & Tax systems'),
(4, 'Software Engineering', 'ENG', 'Product Development, QA, Cloud Engineering'),
(5, 'Marketing & Sales', 'MKT', 'Campaigns, CRM Systems, Customer Portals')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 2. CATEGORIES
INSERT INTO categories (category_id, name, default_priority, description) VALUES
(1, 'Network & Connectivity', 'High', 'VPN, Wi-Fi, DNS, LAN, Firewall access issues'),
(2, 'Hardware & Peripherals', 'Medium', 'Laptops, Monitors, Docking stations, Printers'),
(3, 'Software & Application', 'Medium', 'OS errors, License issues, Dev tools, Office 365'),
(4, 'Access & Authentication', 'High', 'Password resets, 2FA, Active Directory, SSO'),
(5, 'Security & Compliance', 'Critical', 'Phishing alerts, Malware, Security certificate breaches'),
(6, 'Cloud & Infrastructure', 'High', 'AWS, Azure, Docker, VM provisioning issues')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 3. SLA RULES
-- Priority: Response SLA (mins) | Resolution SLA (mins)
-- Critical: 15 mins (0.25h)    | 120 mins (2h)
-- High:     30 mins (0.5h)     | 240 mins (4h)
-- Medium:   120 mins (2h)      | 480 mins (8h)
-- Low:      240 mins (4h)      | 1440 mins (24h)
INSERT INTO sla_rules (sla_id, priority, response_time_minutes, resolution_time_minutes, is_active) VALUES
(1, 'Critical', 15, 120, TRUE),
(2, 'High', 30, 240, TRUE),
(3, 'Medium', 120, 480, TRUE),
(4, 'Low', 240, 1440, TRUE)
ON DUPLICATE KEY UPDATE priority=VALUES(priority);

-- 4. USERS
-- bcrypt hashed passwords for demo accounts
-- admin123: $2b$12$K1r6K/0V/WJ5fXvP1K5wE.7r8jU20lS92I5.gDqm4U9i8E9n4Q6iW (or verified via core/auth.py)
INSERT INTO users (user_id, username, email, password_hash, role, is_active) VALUES
(1, 'admin', 'admin@enterprise.com', '$2b$12$80jB24Yn8yC6l1pI1Z4kCeXJ3Wk.gI6hO5U9/h78VwL0V4eGzK3kK', 'Admin', TRUE),
(2, 'lead_vikram', 'vikram.singh@enterprise.com', '$2b$12$80jB24Yn8yC6l1pI1Z4kCeXJ3Wk.gI6hO5U9/h78VwL0V4eGzK3kK', 'Team Lead', TRUE),
(3, 'ravi_agent', 'ravi.kumar@enterprise.com', '$2b$12$80jB24Yn8yC6l1pI1Z4kCeXJ3Wk.gI6hO5U9/h78VwL0V4eGzK3kK', 'Support Agent', TRUE),
(4, 'priya_agent', 'priya.nair@enterprise.com', '$2b$12$80jB24Yn8yC6l1pI1Z4kCeXJ3Wk.gI6hO5U9/h78VwL0V4eGzK3kK', 'Support Agent', TRUE),
(5, 'arun_agent', 'arun.patel@enterprise.com', '$2b$12$80jB24Yn8yC6l1pI1Z4kCeXJ3Wk.gI6hO5U9/h78VwL0V4eGzK3kK', 'Support Agent', TRUE),
(6, 'john_doe', 'john.doe@enterprise.com', '$2b$12$80jB24Yn8yC6l1pI1Z4kCeXJ3Wk.gI6hO5U9/h78VwL0V4eGzK3kK', 'Employee', TRUE),
(7, 'sarah_smith', 'sarah.smith@enterprise.com', '$2b$12$80jB24Yn8yC6l1pI1Z4kCeXJ3Wk.gI6hO5U9/h78VwL0V4eGzK3kK', 'Employee', TRUE),
(8, 'amit_sharma', 'amit.sharma@enterprise.com', '$2b$12$80jB24Yn8yC6l1pI1Z4kCeXJ3Wk.gI6hO5U9/h78VwL0V4eGzK3kK', 'Employee', TRUE),
(9, 'neha_verma', 'neha.verma@enterprise.com', '$2b$12$80jB24Yn8yC6l1pI1Z4kCeXJ3Wk.gI6hO5U9/h78VwL0V4eGzK3kK', 'Employee', TRUE)
ON DUPLICATE KEY UPDATE username=VALUES(username);

-- 5. SUPPORT TEAMS
INSERT INTO support_teams (team_id, name, description) VALUES
(1, 'Network Operations (NOC)', 'Specializes in routing, switches, VPN, and corporate ISP lines'),
(2, 'End-User Computing (EUC)', 'Handles workstations, laptops, operating systems, and peripherals'),
(3, 'Security Operations (SecOps)', 'Incident response, access control, identity and threat management'),
(4, 'Cloud & DevOps Support', 'Cloud infrastructure, CI/CD pipelines, container orchestration')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 6. SUPPORT AGENTS
INSERT INTO support_agents (agent_id, user_id, team_id, full_name, specialization, is_available) VALUES
(1, 3, 1, 'Ravi Kumar', 'Network & Firewalls', TRUE),
(2, 4, 2, 'Priya Nair', 'Hardware & OS Troubleshooting', TRUE),
(3, 5, 3, 'Arun Patel', 'IAM & Cyber Security', TRUE)
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name);

-- 7. EMPLOYEES
INSERT INTO employees (employee_id, user_id, department_id, full_name, phone, job_title) VALUES
(1, 6, 4, 'John Doe', '+1-555-0101', 'Senior Backend Engineer'),
(2, 7, 3, 'Sarah Smith', '+1-555-0102', 'Senior Financial Analyst'),
(3, 8, 2, 'Amit Sharma', '+1-555-0103', 'HR Business Partner'),
(4, 9, 5, 'Neha Verma', '+1-555-0104', 'Digital Marketing Lead')
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name);

-- 8. SAMPLE TICKETS
INSERT INTO tickets (
    ticket_id, ticket_number, employee_id, department_id, category_id,
    title, description, priority, status, assigned_team_id, assigned_agent_id,
    sla_id, response_deadline, resolution_deadline, first_responded_at, resolved_at, closed_at, reopened_count, created_at
) VALUES
(
    1, 'TCK-2026-001', 1, 4, 1,
    'VPN Gateway Timeout in Hyderabad Region',
    'Cannot connect to corporate staging cluster via OpenVPN. Error: TLS handshake timeout.',
    'High', 'IN PROGRESS', 1, 1,
    2, DATE_SUB(NOW(), INTERVAL 2 HOUR), DATE_ADD(NOW(), INTERVAL 2 HOUR), DATE_SUB(NOW(), INTERVAL 110 MINUTE), NULL, NULL, 0, DATE_SUB(NOW(), INTERVAL 3 HOUR)
),
(
    2, 'TCK-2026-002', 2, 3, 4,
    'Urgent: Password reset for SAP ERP accounting module',
    'Locked out of SAP billing portal right before quarter-end reconciliation.',
    'Critical', 'RESOLVED', 3, 3,
    1, DATE_SUB(NOW(), INTERVAL 6 HOUR), DATE_SUB(NOW(), INTERVAL 4 HOUR), DATE_SUB(NOW(), INTERVAL 5 HOUR), DATE_SUB(NOW(), INTERVAL 4 HOUR), NULL, 0, DATE_SUB(NOW(), INTERVAL 6 HOUR)
),
(
    3, 'TCK-2026-003', 3, 2, 2,
    'External 4K Monitor Flickering & HDMI Disconnects',
    'Dell UltraSharp monitor keeps cutting out when connected via USB-C dock.',
    'Medium', 'ASSIGNED', 2, 2,
    3, DATE_SUB(NOW(), INTERVAL 1 HOUR), DATE_ADD(NOW(), INTERVAL 5 HOUR), NULL, NULL, NULL, 0, DATE_SUB(NOW(), INTERVAL 2 HOUR)
),
(
    4, 'TCK-2026-004', 4, 5, 3,
    'Adobe Premiere Pro 2026 License Activation Failure',
    'Creative Cloud error 205 when launching video editing suite.',
    'Low', 'OPEN', 2, NULL,
    4, DATE_ADD(NOW(), INTERVAL 2 HOUR), DATE_ADD(NOW(), INTERVAL 20 HOUR), NULL, NULL, NULL, 0, DATE_SUB(NOW(), INTERVAL 1 HOUR)
),
(
    5, 'TCK-2026-005', 1, 4, 5,
    'Suspicious Spear-Phishing Email received with ZIP payload',
    'Received email claiming to be from Payroll requesting banking verification via executable link.',
    'Critical', 'CLOSED', 3, 3,
    1, DATE_SUB(NOW(), INTERVAL 24 HOUR), DATE_SUB(NOW(), INTERVAL 22 HOUR), DATE_SUB(NOW(), INTERVAL 23 HOUR), DATE_SUB(NOW(), INTERVAL 22 HOUR), DATE_SUB(NOW(), INTERVAL 20 HOUR), 0, DATE_SUB(NOW(), INTERVAL 24 HOUR)
),
(
    6, 'TCK-2026-006', 2, 3, 1,
    'Finance floor printer network interface offline',
    'Network printer at 3rd Floor East Wing is unreachable over IP 10.10.4.55.',
    'Medium', 'REOPENED', 1, 1,
    3, DATE_SUB(NOW(), INTERVAL 12 HOUR), DATE_SUB(NOW(), INTERVAL 4 HOUR), DATE_SUB(NOW(), INTERVAL 11 HOUR), DATE_SUB(NOW(), INTERVAL 8 HOUR), NULL, 1, DATE_SUB(NOW(), INTERVAL 14 HOUR)
)
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- 9. TICKET HISTORY AUDIT ENTRIES
INSERT INTO ticket_history (ticket_id, old_status, new_status, changed_by_user_id, comment, changed_at) VALUES
(1, NULL, 'OPEN', 6, 'Ticket created by employee John Doe', DATE_SUB(NOW(), INTERVAL 3 HOUR)),
(1, 'OPEN', 'ASSIGNED', 2, 'Assigned to NOC team and Agent Ravi Kumar', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(1, 'ASSIGNED', 'IN PROGRESS', 3, 'Investigating gateway logs and IP routing tables', DATE_SUB(NOW(), INTERVAL 110 MINUTE)),
(2, NULL, 'OPEN', 7, 'Ticket created by employee Sarah Smith', DATE_SUB(NOW(), INTERVAL 6 HOUR)),
(2, 'OPEN', 'IN PROGRESS', 5, 'Verified identity via OTP and reset SAP Master credentials', DATE_SUB(NOW(), INTERVAL 5 HOUR)),
(2, 'IN PROGRESS', 'RESOLVED', 5, 'Credentials pushed to user, verified login successful', DATE_SUB(NOW(), INTERVAL 4 HOUR)),
(5, 'IN PROGRESS', 'RESOLVED', 5, 'Domain blocked at perimeter firewall, threat neutralized', DATE_SUB(NOW(), INTERVAL 22 HOUR)),
(5, 'RESOLVED', 'CLOSED', 1, 'Auto-closed after user confirmed resolution', DATE_SUB(NOW(), INTERVAL 20 HOUR)),
(6, 'RESOLVED', 'REOPENED', 7, 'Printer printed 2 pages then dropped connection again', DATE_SUB(NOW(), INTERVAL 5 HOUR));

-- 10. COMMENTS
INSERT INTO comments (ticket_id, user_id, comment_text, is_internal, created_at) VALUES
(1, 6, 'Happens specifically when on fiber broadband connection.', FALSE, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(1, 3, 'Routing table update scheduled on edge gateway router 02.', TRUE, DATE_SUB(NOW(), INTERVAL 90 MINUTE)),
(6, 7, 'Still getting error: Host unreachable.', FALSE, DATE_SUB(NOW(), INTERVAL 4 HOUR));

-- 11. RESOLUTIONS
INSERT INTO ticket_resolutions (ticket_id, agent_id, root_cause, resolution_steps, resolution_category, resolved_at) VALUES
(2, 3, 'Account locked out due to expired annual password policy', 'Generated temporary token, synced LDAP directory, forced password renewal on next login.', 'Access Control', DATE_SUB(NOW(), INTERVAL 4 HOUR)),
(5, 3, 'Targeted phishing email with malicious zip archive attachment', 'Quarantined message across exchange server, added sender domain to blackhole DNS.', 'Security Incident', DATE_SUB(NOW(), INTERVAL 22 HOUR));
