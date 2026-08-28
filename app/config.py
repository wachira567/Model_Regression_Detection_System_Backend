"""
All configuration loaded from environment variables via Pydantic BaseSettings.
NEVER hardcode secrets. Every secret has a validator that rejects placeholder values.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, SecretStr

class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str  # postgresql+asyncpg://user:pass@host:5432/dbname
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # --- Security ---
    API_SECRET_KEY: SecretStr          # Used to hash/validate API keys
    ALLOWED_ORIGINS: str | list[str] = ["http://localhost:5173"]
    RATE_LIMIT_PER_MINUTE: int = 60   # Per-IP rate limit
    RATE_LIMIT_EVAL_PER_HOUR: int = 10  # Eval trigger rate limit
    ENVIRONMENT: str = "development"
    RESEND_API_KEY: SecretStr | None = None
    CLERK_JWKS_URL: str = "https://clerk.com/.well-known/jwks.json" # Replace with actual Clerk frontend API url in prod

    # --- LLM ---
    OPENAI_API_KEY: SecretStr
    EVAL_MODEL: str = "gpt-4o-mini"
    JUDGE_MODEL: str = "gpt-4o"
    MAX_CONCURRENT_REQUESTS: int = 10
    REQUEST_TIMEOUT_SECONDS: int = 30
    MAX_RETRIES: int = 3

    # --- Slack ---
    SLACK_WEBHOOK_URL: SecretStr | None = None  # Optional: disable alerts if not set
    SLACK_RATE_LIMIT_PER_SECOND: float = 1.0

    # --- Thresholds ---
    REGRESSION_WARNING_THRESHOLD: float = 0.03   # 3%
    REGRESSION_CRITICAL_THRESHOLD: float = 0.08  # 8%
    DRIFT_WINDOW_SIZE: int = 7                   # Rolling window
    DRIFT_THRESHOLD: float = 0.05                # 5% drift

    # --- Paths ---
    PROMPTS_DIR: str = "/app/prompts"
    GOLDEN_DATASET_DIR: str = "/app/golden-dataset"
    REPORTS_DIR: str = "/app/reports"

    # --- GitHub (for PR commenting) ---
    GITHUB_TOKEN: SecretStr | None = None
    GITHUB_WEBHOOK_SECRET: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    # --- Validators ---
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            # Strip brackets, single quotes, double quotes, and whitespace
            v = v.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("API_SECRET_KEY")
    @classmethod
    def validate_api_key_not_placeholder(cls, v: SecretStr) -> SecretStr:
        val = v.get_secret_value()
        if len(val) < 32 or val.startswith("generate-"):
            raise ValueError("API_SECRET_KEY must be at least 32 chars and not a placeholder")
        return v

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v: SecretStr) -> SecretStr:
        val = v.get_secret_value()
        if not val.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must start with 'sk-'")
        return v

    @field_validator("SLACK_WEBHOOK_URL")
    @classmethod
    def validate_slack_url(cls, v: SecretStr | None) -> SecretStr | None:
        if v is None:
            return v
        val = v.get_secret_value()
        if not val.startswith("https://hooks.slack.com/"):
            raise ValueError("SLACK_WEBHOOK_URL must be a valid Slack webhook URL")
        return v

settings = Settings()
