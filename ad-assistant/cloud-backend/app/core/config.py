"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised settings loaded from env / .env file."""

    # ---- Application -------------------------------------------------------
    APP_NAME: str = "AI 图文广告助手 Cloud Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ---- Database ----------------------------------------------------------
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/ad_assistant_dev"
    )

    # ---- JWT ---------------------------------------------------------------
    JWT_SECRET_KEY: str = "change-me-in-production-use-env-var"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 30 * 60               # 30 minutes
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 30 * 24 * 3600       # 30 days

    # ---- Device ------------------------------------------------------------
    MAX_DEVICES_PER_USER: int = 3

    # ---- Account lockout ---------------------------------------------------
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_SECONDS: int = 15 * 60                     # 15 minutes

    # ---- DeepSeek Provider --------------------------------------------------
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ---- Credit / Cost conversion -------------------------------------------
    CREDITS_PER_CNY: int = 100  # 1 credit = ¥0.01, ceiling after multiply

    # ---- Pre-flight balance check -------------------------------------------
    MIN_CREDIT_BALANCE_FOR_PROVIDER_CALL: int = 1  # absolute floor
    FEATURE_MIN_CREDITS: dict = {
        "mock_ad_copy": 2,   # MockProvider default usage ≈ 2 credits
        "ocr": 1,            # local OCR, minimal cost
        "text_gen": 2,       # text generation similar to ad_copy
        "image_edit": 5,     # image processing costs more
    }

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
