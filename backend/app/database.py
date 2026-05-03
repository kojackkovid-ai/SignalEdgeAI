import os
import warnings
import logging
from sqlalchemy.engine import make_url, URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from app.config import settings

logger = logging.getLogger(__name__)

# Database setup - PostgreSQL primary, SQLite fallback for local dev
def create_database_engine():
    """Create database engine - uses PostgreSQL with fallback to SQLite for local dev"""
    DATABASE_URL = settings.database_url
    safe_url = DATABASE_URL.replace(settings.db_pass, '***') if settings.db_pass else DATABASE_URL
    
    # Log database connection details safely
    logger.info("[DATABASE] Connecting to: %s", safe_url)
    logger.debug("[DATABASE] DB_HOST: %s, DB_PORT: %s, DB_NAME: %s", settings.db_host, settings.db_port, settings.db_name)
    
    # SQLite support for local development
    if "sqlite" in DATABASE_URL:
        logger.info("[DATABASE] Using SQLite for local development at: %s", settings.db_host)
        engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False}
        )
        logger.info("[DATABASE] SQLite engine created successfully")
        return engine
    
    # PostgreSQL for production/Docker
    logger.info("[DATABASE] Configuring PostgreSQL connection pool (pool_size=%s, max_overflow=%s)", 
                settings.db_pool_size, settings.db_max_overflow)
    connect_args = {}
    try:
        parsed_url = make_url(DATABASE_URL)
        drivername = str(parsed_url.drivername)
        if drivername in ("postgres", "postgresql"):
            drivername = "postgresql+asyncpg"

        query_params = dict(parsed_url.query) if parsed_url.query else {}
        sslmode = query_params.pop("sslmode", None)
        if sslmode is None:
            sslmode = settings.db_sslmode or os.getenv("PGSSLMODE")
            if sslmode:
                logger.info("[DATABASE] Using SSL mode from environment: %s", sslmode)

        if sslmode is None and parsed_url.host and str(parsed_url.host).endswith(".flycast"):
            sslmode = "disable"
            logger.info("[DATABASE] Detected Fly internal host %s, defaulting sslmode=disable", parsed_url.host)

        if sslmode is not None:
            connect_args["ssl"] = False if sslmode.lower() == "disable" else True
            logger.info("[DATABASE] Converted sslmode=%s -> ssl=%s", sslmode, connect_args["ssl"])

        parsed_url = URL.create(
            drivername=drivername,
            username=parsed_url.username,
            password=parsed_url.password,
            host=parsed_url.host,
            port=parsed_url.port,
            database=parsed_url.database,
            query=query_params or None
        )
        DATABASE_URL = parsed_url
        safe_db_url = parsed_url.render_as_string(hide_password=True)
    except Exception as e:
        logger.warning(f"[DATABASE] Could not normalize database URL driver: {e}")
        safe_db_url = DATABASE_URL if isinstance(DATABASE_URL, str) else DATABASE_URL.render_as_string(hide_password=True)

    if isinstance(DATABASE_URL, str):
        if "@" in DATABASE_URL:
            safe_db_url = DATABASE_URL.replace(DATABASE_URL.split('@')[-1], '***')
    else:
        safe_db_url = DATABASE_URL.render_as_string(hide_password=True)

    logger.info("[DATABASE] Using DATABASE_URL: %s", safe_db_url)
    connect_args = connect_args or {}
    engine_kwargs = {
        "echo": settings.db_echo,
        "future": True,
        "pool_pre_ping": settings.db_pool_pre_ping,
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_recycle": settings.db_pool_recycle,
        "connect_args": connect_args,
    }
    logger.debug("[DATABASE] connect_args: %s", connect_args)

    engine = create_async_engine(DATABASE_URL, **engine_kwargs)
    
    logger.info("[DATABASE] [OK] PostgreSQL engine created successfully")
    return engine

engine = create_database_engine()


AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Alias for compatibility
SessionLocal = AsyncSessionLocal

Base = declarative_base()

async def run_migrations():
    """Run database migrations - add missing columns if needed"""
    from sqlalchemy import text
    
    # Detect database type from URL string (avoids corrupting PostgreSQL transactions)
    db_url = str(settings.database_url)
    is_sqlite = "sqlite" in db_url.lower()
    
    async with engine.begin() as conn:
        try:
            # Check if club_100_unlocked_picks column exists
            if is_sqlite:
                result = await conn.execute(text("PRAGMA table_info(users)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
            else:
                # PostgreSQL
                result = await conn.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='users'"
                ))
                column_names = [row[0] for row in result.fetchall()]
            
            # Add password reset columns if missing
            if 'password_reset_token' not in column_names:
                try:
                    if is_sqlite:
                        # SQLite doesn't support UNIQUE on ALTER TABLE with data, use regular column
                        await conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_token TEXT"))
                    else:
                        await conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_token VARCHAR UNIQUE"))
                    await conn.commit()
                    from app.utils.structured_logging import get_logger
                    logger_instance = get_logger(__name__)
                    logger_instance.info("✅ Migration: Added password_reset_token column")
                except Exception as e:
                    from app.utils.structured_logging import get_logger
                    logger_instance = get_logger(__name__)
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        logger_instance.info("✅ Migration: password_reset_token column already exists")
                    else:
                        logger_instance.warning(f"Migration warning for password_reset_token: {e}")
            
            if 'password_reset_token_expires' not in column_names:
                try:
                    if is_sqlite:
                        await conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_token_expires TIMESTAMP"))
                    else:
                        await conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_token_expires TIMESTAMP"))
                    await conn.commit()
                    from app.utils.structured_logging import get_logger
                    logger_instance = get_logger(__name__)
                    logger_instance.info("✅ Migration: Added password_reset_token_expires column")
                except Exception as e:
                    from app.utils.structured_logging import get_logger
                    logger_instance = get_logger(__name__)
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        logger_instance.info("✅ Migration: password_reset_token_expires column already exists")
                    else:
                        logger_instance.warning(f"Migration warning for password_reset_token_expires: {e}")

            # Add club_100_unlocked_picks if missing
            if 'club_100_unlocked_picks' not in column_names:
                try:
                    if is_sqlite:
                        await conn.execute(text("ALTER TABLE users ADD COLUMN club_100_unlocked_picks JSON DEFAULT '[]'"))
                    else:
                        await conn.execute(text("ALTER TABLE users ADD COLUMN club_100_unlocked_picks JSONB DEFAULT '[]'::jsonb"))
                    await conn.commit()
                    from app.utils.structured_logging import get_logger
                    logger_instance = get_logger(__name__)
                    logger_instance.info("✅ Migration: Added club_100_unlocked_picks column")
                except Exception as e:
                    from app.utils.structured_logging import get_logger
                    logger_instance = get_logger(__name__)
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        logger_instance.info("✅ Migration: club_100_unlocked_picks column already exists")
                    else:
                        logger_instance.warning(f"Migration warning: {e}")
            else:
                from app.utils.structured_logging import get_logger
                logger_instance = get_logger(__name__)
                logger_instance.info("✅ Migration: club_100_unlocked_picks column exists")
                        
        except Exception as e:
            from app.utils.structured_logging import get_logger
            logger_instance = get_logger(__name__)
            logger_instance.warning(f"Could not run migrations: {e}")

async def init_db():
    """Initialize database tables"""
    # Import models to register them with Base
    from app.models.db_models import User, Prediction, ModelPerformance, TrainingLog, SubscriptionPlan
    from app.models.prediction_records import PredictionRecord, PredictionAccuracyStats, PlayerRecord, PlayerSeasonStats, PlayerGameLog, PlayerPropLine
    from app.models.analytics_models import AnalyticsEvent, ConversionFunnel, UserEngagementMetrics, CohortAnalysis
    from app.models.email_models import EmailPreferences, EmailLog, EmailTemplate
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Run migrations after tables are created
    await run_migrations()

async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            try:
                await session.rollback()
            except Exception as rollback_err:
                logger.debug(f"[DATABASE] Session rollback failed during cleanup: {rollback_err}")

async def get_async_session():
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        return session

# Export for direct usage in modules
async_session = AsyncSessionLocal
