import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _get_conf(key: str, default=None, *alt_keys):
    """Safely retrieves configuration from environment variables or Streamlit secrets."""
    # 1. Check direct environment variables
    for k in (key, *alt_keys):
        val = os.getenv(k)
        if val is not None and str(val).strip() != "":
            return val

    # 2. Check Streamlit secrets (if running inside Streamlit Cloud / local Streamlit)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            for k in (key, key.lower(), key.upper(), *alt_keys):
                if k in st.secrets and str(st.secrets[k]).strip() != "":
                    return st.secrets[k]
            # Check nested sections [database] or [mysql]
            for sec in ("database", "mysql"):
                if sec in st.secrets:
                    sec_dict = st.secrets[sec]
                    for k in (key, key.lower(), key.upper(), *alt_keys):
                        if k in sec_dict and str(sec_dict[k]).strip() != "":
                            return sec_dict[k]
    except Exception:
        pass

    return default


# Database Configuration
# Check if a complete connection URL is provided
RAW_DATABASE_URL = _get_conf("DATABASE_URL", None, "DATABASE_URI", "some_key")

if RAW_DATABASE_URL and ("://" in str(RAW_DATABASE_URL)):
    DATABASE_URI = str(RAW_DATABASE_URL).strip()
    DB_TYPE = "sqlite" if DATABASE_URI.startswith("sqlite") else "mysql"
    DB_HOST = "from_url"
    DB_PORT = 3306
    DB_USER = "from_url"
    DB_PASSWORD = "from_url"
    DB_NAME = "from_url"
else:
    DB_TYPE = str(_get_conf("DB_TYPE", "mysql", "type")).lower()
    DB_HOST = str(_get_conf("DB_HOST", "localhost", "host", "MYSQL_HOST")).strip()
    DB_PORT = int(_get_conf("DB_PORT", 3306, "port", "MYSQL_PORT"))
    DB_USER = str(_get_conf("DB_USER", "root", "db_username", "username", "user", "MYSQL_USER")).strip()
    DB_PASSWORD = str(_get_conf("DB_PASSWORD", "password", "db_token", "password", "token", "MYSQL_PASSWORD")).strip()
    DB_NAME = str(_get_conf("DB_NAME", "it_helpdesk_db", "database", "dbname", "MYSQL_DATABASE")).strip()

    # SQLite database path (fixed typo from itrthelpdesk.db to it_helpdesk.db)
    SQLITE_DB_PATH = BASE_DIR / "it_helpdesk.db"

    if DB_TYPE == "sqlite":
        DATABASE_URI = f"sqlite:///{SQLITE_DB_PATH}"
    else:
        # Build MySQL connection URI using mysql-connector-python
        DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLite fallback path
SQLITE_DB_PATH = BASE_DIR / "it_helpdesk.db"

# Fallback setting: do not silently switch to SQLite on connection failure unless explicitly enabled
ALLOW_SQLITE_FALLBACK = str(_get_conf("ALLOW_SQLITE_FALLBACK", "false")).lower() in ("true", "1")

# Logging Configuration
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# Application Settings
APP_TITLE = "IT Helpdesk & Ticket Management System"
DEFAULT_PAGE_ICON = "🎫"

