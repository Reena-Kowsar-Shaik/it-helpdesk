"""Database connection engine, session management, and schema initialization."""

import contextlib
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import config
from core.exceptions import DatabaseConnectionError
from core.logger import logger, log_error

# SQLAlchemy Declarative Base for models
Base = declarative_base()

class DatabaseManager:
    """Manages database connection pool and sessions with auto-fallback support."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        """Initialize database engine based on configuration."""
        self.is_sqlite = config.DB_TYPE.lower() == "sqlite"
        try:
            if not self.is_sqlite:
                # Primary: MySQL
                self.engine = create_engine(
                    config.DATABASE_URI,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False
                )
                # Test connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info(f"Connected successfully to MySQL at {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
            else:
                raise OperationalError("SQLite configured as DB_TYPE", None, None)

        except Exception as e:
            logger.warning(f"MySQL unavailable ({str(e)}). Switching to local SQLite fallback.")
            self.is_sqlite = True
            self.engine = create_engine(
                f"sqlite:///{config.SQLITE_DB_PATH}",
                connect_args={"check_same_thread": False},
                echo=False
            )
            logger.info(f"Initialized SQLite database at {config.SQLITE_DB_PATH}")

        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )
        self.Session = scoped_session(self.session_factory)

    @contextlib.contextmanager
    def get_session(self):
        """Provide a transactional scope around a series of operations."""
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
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database schema validated / initialized.")
        except Exception as e:
            log_error("Failed to initialize database tables", e)
            raise DatabaseConnectionError(str(e))

# Global DB manager singleton
db = DatabaseManager()
