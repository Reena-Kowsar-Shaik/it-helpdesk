-- ==========================================================
-- IT HELPDESK & TICKET MANAGEMENT SYSTEM SCHEMA
-- Relational DDL with Tables, Indexes, and Analytical Views
-- ==========================================================

-- 1. DEPARTMENTS
CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(20) NOT NULL UNIQUE,
    head_name VARCHAR(100),
    contact_email VARCHAR(150),
    budget_code VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. SUPPORT TEAMS
CREATE TABLE IF NOT EXISTS support_teams (
    team_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    specialization VARCHAR(150) NOT NULL,
    lead_name VARCHAR(100),
    operating_hours VARCHAR(100) DEFAULT '24x7 / 9am-6pm IST',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. USERS / EMPLOYEES
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Employee',
    department_id INT,
    designation VARCHAR(100),
    phone VARCHAR(30),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
);

-- 4. SUPPORT AGENTS (Extends users table)
CREATE TABLE IF NOT EXISTS agents (
    agent_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    team_id INT,
    tier VARCHAR(20) DEFAULT 'L1', -- L1, L2, L3, Specialist
    max_active_tickets INT DEFAULT 10,
    status VARCHAR(30) DEFAULT 'Available', -- Available, Busy, On Leave, Offline
    skills VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES support_teams(team_id) ON DELETE SET NULL
);

-- 5. SLA POLICIES
CREATE TABLE IF NOT EXISTS sla_policies (
    sla_id INT AUTO_INCREMENT PRIMARY KEY,
    priority VARCHAR(30) NOT NULL UNIQUE,
    response_time_hours DECIMAL(6, 2) NOT NULL,
    resolution_time_hours DECIMAL(6, 2) NOT NULL,
    escalation_time_hours DECIMAL(6, 2) NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. TICKETS (Primary Transaction Table)
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    priority VARCHAR(30) NOT NULL DEFAULT 'Medium',
    status VARCHAR(50) NOT NULL DEFAULT 'Open',
    requester_id INT NOT NULL,
    department_id INT,
    team_id INT,
    assigned_agent_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    first_response_at DATETIME NULL,
    resolved_at DATETIME NULL,
    closed_at DATETIME NULL,
    sla_due_date DATETIME NULL,
    sla_breached BOOLEAN DEFAULT FALSE,
    response_sla_breached BOOLEAN DEFAULT FALSE,
    reopen_count INT DEFAULT 0,
    satisfaction_rating INT NULL, -- 1 to 5
    feedback_comments TEXT NULL,
    resolution_notes TEXT NULL,
    root_cause VARCHAR(255) NULL,
    estimated_hours DECIMAL(5,2) DEFAULT 2.0,
    actual_hours DECIMAL(5,2) NULL,
    FOREIGN KEY (requester_id) REFERENCES users(user_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (team_id) REFERENCES support_teams(team_id),
    FOREIGN KEY (assigned_agent_id) REFERENCES agents(agent_id)
);

-- 7. TICKET AUDIT / HISTORY (Relational Audit Log)
CREATE TABLE IF NOT EXISTS ticket_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    changed_by INT,
    action_type VARCHAR(50) NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    old_priority VARCHAR(30),
    new_priority VARCHAR(30),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 8. TICKET COMMENTS / CONVERSATIONS
CREATE TABLE IF NOT EXISTS ticket_comments (
    comment_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    user_id INT NOT NULL,
    comment_type VARCHAR(30) DEFAULT 'Public',
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 9. KNOWLEDGE BASE ARTICLES
CREATE TABLE IF NOT EXISTS knowledge_base (
    article_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    tags VARCHAR(255),
    view_count INT DEFAULT 0,
    helpful_count INT DEFAULT 0,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- 10. CANNED RESPONSES
CREATE TABLE IF NOT EXISTS canned_responses (
    response_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    message_body TEXT NOT NULL,
    shortcut_code VARCHAR(30)
);

-- 11. SYSTEM AUDIT LOGS
CREATE TABLE IF NOT EXISTS system_audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    event_type VARCHAR(50) NOT NULL,
    details TEXT,
    ip_address VARCHAR(50) DEFAULT '127.0.0.1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES FOR HIGH-PERFORMANCE SQL EXECUTION
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_agent ON tickets(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_tickets_dept ON tickets(department_id);
CREATE INDEX IF NOT EXISTS idx_history_ticket_id ON ticket_history(ticket_id);

-- ==========================================================
-- ANALYTICAL SQL VIEWS
-- ==========================================================

-- VIEW 1: Department Demand Analytics View
CREATE VIEW IF NOT EXISTS v_department_load AS
SELECT 
    d.department_id,
    d.name AS department_name,
    d.code AS department_code,
    d.head_name,
    COUNT(t.ticket_id) AS total_requests,
    SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_tickets,
    SUM(CASE WHEN t.priority = 'High' THEN 1 ELSE 0 END) AS high_tickets,
    SUM(CASE WHEN t.status IN ('Open', 'Assigned', 'In Progress') THEN 1 ELSE 0 END) AS pending_tickets,
    SUM(CASE WHEN t.sla_breached = 1 THEN 1 ELSE 0 END) AS breached_tickets
FROM departments d
LEFT JOIN tickets t ON d.department_id = t.department_id
GROUP BY d.department_id, d.name, d.code, d.head_name;

-- VIEW 2: Recurring Problems Analysis View
CREATE VIEW IF NOT EXISTS v_recurring_problems AS
SELECT 
    category,
    COUNT(*) AS incident_frequency,
    SUM(CASE WHEN priority IN ('Critical', 'High') THEN 1 ELSE 0 END) AS severe_incidents,
    SUM(CASE WHEN reopen_count > 0 THEN 1 ELSE 0 END) AS reopened_count,
    ROUND(AVG(CASE WHEN satisfaction_rating IS NOT NULL THEN satisfaction_rating END), 2) AS avg_rating
FROM tickets
GROUP BY category;

-- VIEW 3: SLA Performance View
CREATE VIEW IF NOT EXISTS v_sla_compliance AS
SELECT 
    t.priority,
    COUNT(*) AS total_tickets,
    SUM(CASE WHEN t.sla_breached = 1 THEN 1 ELSE 0 END) AS breached_count,
    SUM(CASE WHEN t.sla_breached = 0 THEN 1 ELSE 0 END) AS within_sla_count,
    ROUND((SUM(CASE WHEN t.sla_breached = 0 THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 1) AS sla_met_pct
FROM tickets t
GROUP BY t.priority;
