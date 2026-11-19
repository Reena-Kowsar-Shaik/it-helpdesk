import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

def get_config(key: str, default=None):
    """Retrieve setting from Streamlit secrets (if available) or environment variables."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

# Database Configuration
DATABASE_URL = get_config("DATABASE_URL", None)
DB_TYPE = str(get_config("DB_TYPE", "sqlite")).lower()  # Default to 'sqlite' for zero-config deployments
DB_HOST = get_config("DB_HOST", "localhost")
DB_PORT = int(get_config("DB_PORT", "3306"))
DB_USER = get_config("DB_USER", "root")
DB_PASSWORD = get_config("DB_PASSWORD", "root")
DB_NAME = get_config("DB_NAME", "it_helpdesk_db")

SQLITE_PATH = BASE_DIR / "helpdesk.db"

# Application Settings
APP_TITLE = "IT ServiceDesk Pro - Enterprise SQL IT Management"
APP_TAGLINE = "SQL-Driven IT Helpdesk, SLA Intelligence & Service Analytics"
APP_VERSION = "2.4.0"

# SLA Defaults (in hours)
DEFAULT_SLA = {
    "Critical": {"response": 0.5, "resolution": 4, "escalation": 2},
    "High": {"response": 1, "resolution": 8, "escalation": 4},
    "Medium": {"response": 4, "resolution": 24, "escalation": 16},
    "Low": {"response": 8, "resolution": 48, "escalation": 36},
}

CATEGORIES = [
    "Hardware & Workstations",
    "Software & Licensing",
    "Network & VPN Connectivity",
    "Identity & Access Management",
    "Database & Cloud Infrastructure",
    "Email & Communication Systems",
    "Security & Incident Response",
    "Printer & Peripherals",
    "General IT Support"
]

PRIORITIES = ["Critical", "High", "Medium", "Low"]
STATUSES = ["Open", "Assigned", "In Progress", "Pending Customer", "Resolved", "Closed", "Reopened"]
ROLES = ["Employee", "Support Agent", "Team Lead", "IT Admin", "Executive"]
