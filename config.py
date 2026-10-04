import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "mysql")  # 'mysql' or 'sqlite'
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "it_helpdesk_db")

# SQLite fallback path
SQLITE_DB_PATH = BASE_DIR / "it_helpdesk.db"

# SQLAlchemy Database URI builder
if DB_TYPE.lower() == "sqlite":
    DATABASE_URI = f"sqlite:///{SQLITE_DB_PATH}"
else:
    # MySQL connection string using mysqlconnector or pymysql
    DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Logging Configuration
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# Application Settings
APP_TITLE = "IT Helpdesk & Ticket Management System"
DEFAULT_PAGE_ICON = "🎫"
