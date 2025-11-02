from typing import List, Literal
from pydantic import BaseModel, SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


LOG_DEFAULT_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

WORKER_LOG_DEFAULT_FORMAT = "[%(asctime)s.%(msecs)03d][%(processName)s] %(module)16s:%(lineno)-3d %(levelname)-7s - %(message)s"


class LoggingConfig(BaseModel):
    log_level: Literal[
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    ] = "info"
    log_format: str = LOG_DEFAULT_FORMAT
    date_format: str = "%Y-%m-%d %H:%M:%S"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="bot/.env",
        env_file_encoding="utf-8",
        validate_default=False,
        case_sensitive=False,
    )

    admins: List[int] = Field(...)
    bot_token: SecretStr = Field(...)
    db_url: str = Field(...)
    ttl_default: int = Field(...)

    logging: LoggingConfig = LoggingConfig()


config = Settings()
