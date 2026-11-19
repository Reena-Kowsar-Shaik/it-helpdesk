import os
import sqlite3
import pymysql
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import config
from utils.logger import get_logger

logger = get_logger("database_connection")

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._engine = None
            cls._instance._active_db_type = config.DB_TYPE
            cls._instance._init_connection()
        return cls._instance

    def _init_connection(self):
        """Initializes database engine for MySQL, SQLite, or custom DATABASE_URL."""
        # 1. Custom DATABASE_URL (if provided)
        if config.DATABASE_URL:
            try:
                db_url = config.DATABASE_URL
                if db_url.startswith("sqlite"):
                    self._active_db_type = "sqlite"
                    self._engine = create_engine(db_url, echo=False)
                    self._ensure_sqlite_schema()
                else:
                    self._active_db_type = "mysql"
                    self._engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=3600, echo=False)
                    with self._engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                logger.info(f"Successfully connected using DATABASE_URL ({self._active_db_type})")
                return
            except Exception as e:
                logger.warning(f"DATABASE_URL connection failed ({e}). Falling back to local SQLite engine.")
                self._active_db_type = "sqlite"

        # 2. MySQL Mode
        if self._active_db_type == "mysql":
            try:
                # First ensure MySQL database exists
                self._ensure_mysql_database()
                connection_str = (
                    f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@"
                    f"{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}?charset=utf8mb4"
                )
                self._engine = create_engine(
                    connection_str,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False
                )
                # Test connection
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info(f"Successfully connected to MySQL database '{config.DB_NAME}' at {config.DB_HOST}:{config.DB_PORT}")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to MySQL ({e}). Falling back seamlessly to high-performance local SQLite engine.")
                self._active_db_type = "sqlite"

        # 3. SQLite Mode (Default & Resilient Fallback)
        sqlite_uri = f"sqlite:///{config.SQLITE_PATH.as_posix()}"
        self._engine = create_engine(sqlite_uri, echo=False)
        self._ensure_sqlite_schema()
        logger.info(f"Using SQLite database engine at {config.SQLITE_PATH}")

    def _ensure_sqlite_schema(self):
        """Ensures that SQLite database has required tables; auto-initializes and seeds if missing."""
        try:
            with self._engine.connect() as conn:
                res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
                if not res.fetchone():
                    logger.info("Database tables not found. Automatically initializing schema and seeding data...")
                    self.init_db()
                    try:
                        from database.seed_data import seed_database
                        seed_database()
                    except Exception as se:
                        logger.warning(f"Seed note: {se}")
        except Exception as e:
            logger.warning(f"Schema check error: {e}")

    def _ensure_mysql_database(self):
        """Creates the MySQL database if it doesn't already exist."""
        try:
            conn = pymysql.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                charset='utf8mb4'
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"Could not auto-create database on server: {e}")
            raise e

    def switch_db_type(self, db_type: str, host=None, port=None, user=None, password=None, db_name=None):
        """Allows switching between MySQL and SQLite dynamically from UI."""
        self._active_db_type = db_type
        if db_type == "mysql":
            if host: config.DB_HOST = host
            if port: config.DB_PORT = int(port)
            if user: config.DB_USER = user
            if password is not None: config.DB_PASSWORD = password
            if db_name: config.DB_NAME = db_name
        self._init_connection()
        return self.get_db_info()

    def get_db_info(self):
        """Returns metadata about current DB connection."""
        return {
            "type": self._active_db_type.upper(),
            "host": config.DB_HOST if self._active_db_type == "mysql" else "Local File",
            "port": config.DB_PORT if self._active_db_type == "mysql" else "N/A",
            "database": config.DB_NAME if self._active_db_type == "mysql" else config.SQLITE_PATH.name,
            "engine": str(self._engine.url) if self._engine else "None"
        }

    def get_engine(self):
        if self._engine is None:
            self._init_connection()
        return self._engine

    def execute_query(self, query_str: str, params: dict = None):
        """Executes a SELECT query and returns rows as dictionaries."""
        with self.get_engine().connect() as conn:
            result = conn.execute(text(query_str), params or {})
            if result.returns_rows:
                return [dict(row._mapping) for row in result.fetchall()]
            return []

    def execute_non_query(self, query_str: str, params: dict = None):
        """Executes INSERT, UPDATE, DELETE with transaction commit."""
        with self.get_engine().begin() as conn:
            result = conn.execute(text(query_str), params or {})
            try:
                last_id = result.lastrowid
            except Exception:
                last_id = None
            row_count = result.rowcount
            return {"lastrowid": last_id, "rowcount": row_count}

    def fetch_dataframe(self, query_str: str, params: dict = None) -> pd.DataFrame:
        """Executes query and returns results directly into a Pandas DataFrame."""
        try:
            with self.get_engine().connect() as conn:
                df = pd.read_sql(text(query_str), conn, params=params or {})
                return df
        except Exception as e:
            logger.error(f"Error fetching dataframe for query: {e}")
            return pd.DataFrame()

    def init_db(self, force_recreate: bool = False):
        """Reads database/schema.sql and initializes tables."""
        schema_file = config.BASE_DIR / "database" / "schema.sql"
        if not schema_file.exists():
            logger.error("schema.sql not found!")
            return False

        with open(schema_file, "r", encoding="utf-8") as f:
            sql_statements = f.read()

        statements = [stmt.strip() for stmt in sql_statements.split(";") if stmt.strip()]

        with self.get_engine().begin() as conn:
            if force_recreate:
                table_drops = [
                    "system_audit_logs", "canned_responses", "knowledge_base",
                    "ticket_comments", "ticket_history", "tickets",
                    "sla_policies", "agents", "users", "support_teams", "departments"
                ]
                for tbl in table_drops:
                    try:
                        conn.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
                    except Exception as e:
                        logger.debug(f"Drop error for {tbl}: {e}")

            for stmt in statements:
                # Remove comments
                lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
                cleaned_stmt = "\n".join(lines).strip()
                if not cleaned_stmt:
                    continue
                try:
                    if self._active_db_type == "sqlite":
                        cleaned_stmt = cleaned_stmt.replace("INT AUTO_INCREMENT PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
                        cleaned_stmt = cleaned_stmt.replace("AUTO_INCREMENT", "")
                    conn.execute(text(cleaned_stmt))
                except Exception as e:
                    logger.warning(f"Error executing statement: {e} in {cleaned_stmt[:60]}...")
        logger.info("Database schema initialized successfully.")
        return True

# Singleton accessor
db_manager = DatabaseManager()
