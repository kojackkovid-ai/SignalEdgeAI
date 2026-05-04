from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
import secrets
import warnings
import logging
from pathlib import Path

# Load .env explicitly before anything else
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Database - Let pydantic load from environment/env_file
    db_user: str = "postgres"
    db_pass: str = ""
    db_host: str = "localhost"
    db_port: str = "5432"
    db_name: str = "sports_predictions"

    # API
    api_title: str = "Sports Prediction Platform API"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Frontend Configuration
    frontend_url: str = "http://localhost:5173"

    # Security - MUST be set in environment
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ML
    model_update_interval: int = 3600
    retrain_days: int = 7
    min_training_samples: int = 1000
    ml_models_dir: str = "ml-models/trained"

    
    # Monetization
    stripe_public_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    sentry_dsn: Optional[str] = None
    
    # Email - SendGrid
    sendgrid_api_key: str = ""
    sendgrid_sender: str = "noreply@sportstats.com"
    sendgrid_sender_name: str = "SignalEdge AI"
    
    # Redis
    redis_url: Optional[str] = os.environ.get("REDIS_URL", "redis://localhost:6379")

    # Postgres SSL mode override
    db_sslmode: Optional[str] = None

    # Database Connection Pooling
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 3600  # Recycle connections after 1 hour
    db_pool_pre_ping: bool = True
    db_echo: bool = False

    # Weather API
    openweather_api_key: str = ""
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5/"

    # Odds API - MUST be set in environment, no hardcoded defaults
    odds_api_key: str = ""
    odds_api_key_backup_1: Optional[str] = None
    odds_api_key_backup_2: Optional[str] = None
    odds_api_key_backup_3: Optional[str] = None
    odds_api_key_backup_4: Optional[str] = None
    odds_api_key_backup_5: Optional[str] = None
    odds_api_base_url: str = "https://api.the-odds-api.com/v4/"
    
    # Security Settings
    allowed_hosts: str = "localhost,127.0.0.1"
    cors_origins: str = ""
    enable_https_redirect: bool = False
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_security_settings()
    
    def _validate_security_settings(self):
        """Validate critical security settings and warn if using defaults"""
        warnings.filterwarnings('always', category=SecurityWarning)
        
        # Determine environment mode and enforce production safety
        if self.is_production:
            if not self.secret_key or len(self.secret_key) < 32:
                raise ValueError(
                    "SECRET_KEY must be set to a strong value of at least 32 characters in production."
                )
            if not self.stripe_secret_key:
                raise ValueError("STRIPE_SECRET_KEY must be configured in production.")
            if not self.odds_api_key:
                raise ValueError("ODDS_API_KEY must be configured in production.")
            if not self.cors_origins:
                raise ValueError("CORS origins must be explicitly configured in production.")
            if not self.allowed_hosts:
                raise ValueError("ALLOWED_HOSTS must be configured in production.")
            if not self.sentry_dsn:
                warnings.warn(
                    "SENTRY_DSN is not configured in production. Error tracking will be disabled.",
                    SecurityWarning,
                    stacklevel=2
                )
            if not self.enable_https_redirect:
                warnings.warn(
                    "HTTPS redirect is disabled in production. Set ENABLE_HTTPS_REDIRECT=true for better security.",
                    SecurityWarning,
                    stacklevel=2
                )
        else:
            # Development defaults: warn instead of failing.
            if not self.secret_key or len(self.secret_key) < 32:
                if not self.secret_key:
                    self.secret_key = secrets.token_urlsafe(32)
                    warnings.warn(
                        "SECRET_KEY not set in environment. Using temporary key - "
                        "THIS IS INSECURE FOR PRODUCTION. Set a strong SECRET_KEY in your .env file.",
                        SecurityWarning,
                        stacklevel=2
                    )
                else:
                    warnings.warn(
                        f"SECRET_KEY is too short ({len(self.secret_key)} chars). "
                        "Use at least 32 characters for production.",
                        SecurityWarning,
                        stacklevel=2
                    )
        
        # Check odds API keys
        if not self.odds_api_keys:
            warnings.warn(
                "ODDS_API_KEY not set. Odds API features will be disabled. "
                "Set your API key or fallback keys in the environment.",
                SecurityWarning,
                stacklevel=2
            )

    @property
    def is_production(self) -> bool:
        """Detect running in a production environment."""
        return os.getenv("ENVIRONMENT", "").lower() == "production"

    @property
    def database_url(self) -> str:
        """Get database URL"""
        
        # Check if DATABASE_URL is set (for Docker/production)
        fly_database_url = os.getenv("FLY_DATABASE_URL")
        if fly_database_url:
            logger.info("[CONFIG] Using FLY_DATABASE_URL from environment")
            return fly_database_url

        database_url = os.getenv("DATABASE_URL")
        if database_url:
            logger.info("[CONFIG] Using DATABASE_URL from environment")
            return database_url
        
        # Check if running in Docker (indicated by DB_HOST != localhost)
        in_docker = self.db_host not in ("localhost", "127.0.0.1")
        
        # For local development without PostgreSQL, use SQLite
        # But NOT in Docker - always use PostgreSQL in Docker
        use_sqlite = os.getenv("USE_SQLITE", "false" if in_docker else "true").lower() == "true"
        if use_sqlite:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sports_predictions.db")
            url = f"sqlite+aiosqlite:///{db_path}"
            logger.info("[CONFIG] Using SQLite for local development: %s", db_path)
            return url
        
        # Build PostgreSQL URL from individual components
        url = f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"
        logger.info("[CONFIG] Using PostgreSQL: %s:%s/%s", self.db_host, self.db_port, self.db_name)
        logger.info("[CONFIG] Database URL: %s", url.replace(self.db_pass, "***"))
        return url
    
    @property
    def allowed_hosts_list(self) -> list:
        """Parse allowed hosts from comma-separated string"""
        hosts = [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]
        return hosts if hosts else ["*"]
    
    @property
    def cors_origins_list(self) -> list:
        """Parse CORS origins from comma-separated string"""
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if not origins and not self.is_production:
            return ["*"]
        return origins

    @property
    def odds_api_keys(self) -> list[str]:
        """Return primary and fallback Odds API keys in priority order."""
        keys = []
        if self.odds_api_key:
            keys.append(self.odds_api_key.strip())
        for backup_key in (
            self.odds_api_key_backup_1,
            self.odds_api_key_backup_2,
            self.odds_api_key_backup_3,
            self.odds_api_key_backup_4,
            self.odds_api_key_backup_5,
        ):
            if backup_key:
                keys.append(backup_key.strip())
        return [k for k in keys if k]

class SecurityWarning(Warning):
    """Custom warning for security-related issues"""
    pass

settings = Settings()
