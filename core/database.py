"""Database connection engine, session management, and schema initialization."""

import contextlib
from typing import Tuple, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import config
from core.exceptions import DatabaseConnectionError
from core.logger import logger, log_error

# SQLAlchemy Declarative Base for models
Base = declarative_base()


class DatabaseManager:
    """Manages database connection pool and sessions with robust validation and reporting."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        """Initialize database engine based on configuration."""
        self.is_sqlite = config.DB_TYPE.lower() == "sqlite"
        self.connection_error: Optional[str] = None
        self.engine = None

        try:
            if not self.is_sqlite:
                # Primary: MySQL
                self.engine = create_engine(
                    config.DATABASE_URI,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False
                )
                # Test connection immediately
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("Connected successfully to MySQL database.")
            else:
                sqlite_uri = config.DATABASE_URI if config.DATABASE_URI.startswith("sqlite") else f"sqlite:///{config.SQLITE_DB_PATH}"
                self.engine = create_engine(
                    sqlite_uri,
                    connect_args={"check_same_thread": False},
                    echo=False
                )
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info(f"Initialized SQLite database at {sqlite_uri}")

        except Exception as e:
            err_msg = str(e)
            if config.ALLOW_SQLITE_FALLBACK:
                logger.warning(
                    f"Primary database connection failed ({err_msg}). "
                    f"ALLOW_SQLITE_FALLBACK is enabled; falling back to SQLite at {config.SQLITE_DB_PATH}."
                )
                self.is_sqlite = True
                self.engine = create_engine(
                    f"sqlite:///{config.SQLITE_DB_PATH}",
                    connect_args={"check_same_thread": False},
                    echo=False
                )
            else:
                self.connection_error = err_msg
                logger.error(
                    f"Database connection failed for DB_TYPE='{config.DB_TYPE}'. "
                    f"Error details: {err_msg}"
                )
                # Keep engine reference if created, otherwise attempt non-validating engine
                # so that module imports don't fail, but subsequent queries raise clearly
                try:
                    self.engine = create_engine(config.DATABASE_URI, echo=False)
                except Exception:
                    self.engine = None

        if self.engine is not None:
            self.session_factory = sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False
            )
            self.Session = scoped_session(self.session_factory)
        else:
            self.session_factory = None
            self.Session = None

    def check_connection(self) -> Tuple[bool, Optional[str]]:
        """Verify active database connectivity and return status and error message."""
        if self.connection_error and not config.ALLOW_SQLITE_FALLBACK:
            return False, self.connection_error
        if self.engine is None:
            return False, "Database engine could not be initialized."
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, None
        except Exception as e:
            self.connection_error = str(e)
            return False, str(e)

    @contextlib.contextmanager
    def get_session(self):
        """Provide a transactional scope around a series of operations."""
        if self.connection_error and not config.ALLOW_SQLITE_FALLBACK:
            raise DatabaseConnectionError(
                f"Cannot establish database session. Connection failed: {self.connection_error}"
            )
        if not self.Session:
            raise DatabaseConnectionError("Database session factory is not initialized.")

        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            log_error("Database session transaction error", e)
            raise
        finally:
            session.close()

    def execute_raw(self, sql_query: str, params: dict = None):
        """Execute raw SQL statement and return results or rowcount."""
        if self.connection_error and not config.ALLOW_SQLITE_FALLBACK:
            raise DatabaseConnectionError(
                f"Cannot execute SQL query. Connection failed: {self.connection_error}"
            )
        if not self.engine:
            raise DatabaseConnectionError("Database engine is not initialized.")

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query), params or {})
                if result.returns_rows:
                    return result.mappings().all()
                conn.commit()
                return result.rowcount
        except SQLAlchemyError as e:
            log_error(f"SQL execution error on query: {sql_query[:60]}...", e)
            raise DatabaseConnectionError(str(e))

    def init_database(self):
        """Create tables and initialize default seed data if database is empty."""
        is_ok, err = self.check_connection()
        if not is_ok:
            raise DatabaseConnectionError(
                f"Database connection check failed: {err}"
            )

        try:
            # 1. Crucial: Import all models to register them with Base.metadata before create_all
            import core.models  # noqa: F401

            Base.metadata.create_all(bind=self.engine)
            logger.info("Database schema validated / initialized.")

            # 2. Check and seed initial reference data if tables are empty
            from seed_db import seed_database
            seed_database(reset=False, include_rich_analytics=True)
            return True
        except Exception as e:
            log_error("Failed to initialize database tables or seed data", e)
            raise DatabaseConnectionError(str(e))


# Global DB manager singleton
db = DatabaseManager()

