import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True, slots=True)
class Settings:
    """App configuration, read once at import time.

    frozen=True so settings cannot be changed at runtime.
    """

    # ---------- App ----------
    app_name: str = "InsightAPI"

    # ---------- OpenAI-compatible LLM ----------
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "sk-replace-me")
    openai_base_url: str | None = os.getenv("OPENAI_BASE_URL")
    allowed_models: tuple[str, ...] = ("openai/gpt-oss-20b",)

    # ---------- Rate limiting ----------
    # Default per-user limit, in requests per minute.
    rate_limit_per_minute: int = 10
    rate_limits: dict[str, int] = field(
        default_factory=lambda: {
            "mona": 3,
            "ali": 5,
        }
    )

    # ---------- Logging ----------
    log_file: str = "logs/insight_api.log"
    log_level: str = "INFO"
    log_max_bytes: int = 10 * 1024 * 1024
    log_backup_count: int = 5

    # ---------- Auth ----------
    # Maps an API key to the internal user id used for rate limiting.
    api_keys: dict[str, str] = field(
        default_factory=lambda: {
            "dev-key-123": "ahmed",
            "dev-key-456": "ali",
            "dev-key-789": "mona",
        }
    )


# Single shared instance used across the app
settings = Settings()
