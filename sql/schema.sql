-- ==========================================================
-- IT Helpdesk & Ticket Management System Database Schema
-- Main Focus: Relational Integrity, Constraints, Normalization
-- ==========================================================

-- 1. Create Database if not exists
CREATE DATABASE IF NOT EXISTS it_helpdesk_db;
USE it_helpdesk_db;

-- Drop tables in reverse dependency order for clean schema recreation
DROP TABLE IF EXISTS ticket_resolutions;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS ticket_history;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS sla_rules;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS support_agents;
DROP TABLE IF EXISTS support_teams;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS departments;

-- ==========================================================
-- 2. DEPARTMENTS TABLE
-- ==========================================================
CREATE TABLE departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 3. USERS TABLE (Authentication & Base RBAC)
-- ==========================================================
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('Employee', 'Support Agent', 'Team Lead', 'Admin') NOT NULL DEFAULT 'Employee',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_username (username),
    INDEX idx_users_email (email),
    INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 4. EMPLOYEES TABLE
-- ==========================================================
CREATE TABLE employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    department_id INT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(25),
    job_title VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_employees_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_employees_department FOREIGN KEY (department_id) 
        REFERENCES departments(department_id) ON DELETE RESTRICT,
    INDEX idx_employees_dept (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 5. SUPPORT TEAMS TABLE
-- ==========================================================
CREATE TABLE support_teams (
    team_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 6. SUPPORT AGENTS TABLE
-- ==========================================================
CREATE TABLE support_agents (
    agent_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    team_id INT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) DEFAULT 'General IT',
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_agents_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_agents_team FOREIGN KEY (team_id) 
        REFERENCES support_teams(team_id) ON DELETE RESTRICT,
    INDEX idx_agents_team (team_id),
    INDEX idx_agents_available (is_available)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 7. CATEGORIES TABLE
-- ==========================================================
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    default_priority ENUM('Critical', 'High', 'Medium', 'Low') NOT NULL DEFAULT 'Medium',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 8. SLA RULES TABLE
-- ==========================================================
CREATE TABLE sla_rules (
    sla_id INT AUTO_INCREMENT PRIMARY KEY,
    priority ENUM('Critical', 'High', 'Medium', 'Low') NOT NULL UNIQUE,
    response_time_minutes INT NOT NULL,     -- Max minutes to first agent response
    resolution_time_minutes INT NOT NULL,   -- Max minutes to ticket resolution
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_sla_positive_response CHECK (response_time_minutes > 0),
    CONSTRAINT chk_sla_positive_resolution CHECK (resolution_time_minutes > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 9. TICKETS TABLE
-- ==========================================================
CREATE TABLE tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number VARCHAR(30) NOT NULL UNIQUE,
    employee_id INT NOT NULL,
    department_id INT NOT NULL,
    category_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    priority ENUM('Critical', 'High', 'Medium', 'Low') NOT NULL DEFAULT 'Medium',
    status ENUM('OPEN', 'ASSIGNED', 'IN PROGRESS', 'RESOLVED', 'CLOSED', 'REOPENED') NOT NULL DEFAULT 'OPEN',
    assigned_team_id INT NULL,
    assigned_agent_id INT NULL,
    sla_id INT NULL,
    response_deadline DATETIME NULL,
    resolution_deadline DATETIME NULL,
    first_responded_at DATETIME NULL,
    resolved_at DATETIME NULL,
    closed_at DATETIME NULL,
    reopened_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_tickets_employee FOREIGN KEY (employee_id) 
        REFERENCES employees(employee_id) ON DELETE RESTRICT,
    CONSTRAINT fk_tickets_department FOREIGN KEY (department_id) 
        REFERENCES departments(department_id) ON DELETE RESTRICT,
    CONSTRAINT fk_tickets_category FOREIGN KEY (category_id) 
        REFERENCES categories(category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_tickets_team FOREIGN KEY (assigned_team_id) 
        REFERENCES support_teams(team_id) ON DELETE SET NULL,
    CONSTRAINT fk_tickets_agent FOREIGN KEY (assigned_agent_id) 
        REFERENCES support_agents(agent_id) ON DELETE SET NULL,
    CONSTRAINT fk_tickets_sla FOREIGN KEY (sla_id) 
        REFERENCES sla_rules(sla_id) ON DELETE SET NULL,
    INDEX idx_tickets_status (status),
    INDEX idx_tickets_priority (priority),
    INDEX idx_tickets_employee (employee_id),
    INDEX idx_tickets_agent (assigned_agent_id),
    INDEX idx_tickets_dept (department_id),
    INDEX idx_tickets_category (category_id),
    INDEX idx_tickets_created_at (created_at),
    INDEX idx_tickets_deadlines (resolution_deadline, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 10. TICKET HISTORY TABLE (Audit Trail)
-- ==========================================================
CREATE TABLE ticket_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    old_status VARCHAR(30) NULL,
    new_status VARCHAR(30) NOT NULL,
    changed_by_user_id INT NULL,
    comment TEXT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_history_ticket FOREIGN KEY (ticket_id) 
        REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_history_user FOREIGN KEY (changed_by_user_id) 
        REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_history_ticket (ticket_id),
    INDEX idx_history_date (changed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 11. COMMENTS TABLE
-- ==========================================================
CREATE TABLE comments (
    comment_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    user_id INT NOT NULL,
    comment_text TEXT NOT NULL,
    is_internal BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comments_ticket FOREIGN KEY (ticket_id) 
        REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_comments_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_comments_ticket (ticket_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================
-- 12. TICKET RESOLUTIONS TABLE
-- ==========================================================
CREATE TABLE ticket_resolutions (
    resolution_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL UNIQUE,
    agent_id INT NOT NULL,
    root_cause TEXT NOT NULL,
    resolution_steps TEXT NOT NULL,
    resolution_category VARCHAR(100) DEFAULT 'Technical Fix',
    resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_resolutions_ticket FOREIGN KEY (ticket_id) 
        REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_resolutions_agent FOREIGN KEY (agent_id) 
        REFERENCES support_agents(agent_id) ON DELETE RESTRICT,
    INDEX idx_resolutions_ticket (ticket_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
