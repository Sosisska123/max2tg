from pathlib import Path

from typing import List, Literal

from pydantic import BaseModel, SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource


LOG_DEFAULT_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DATE_DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S"

BASE_DIR = Path(__file__).parent
yaml_file_path = str(BASE_DIR / "shared" / "config.yaml")
env_file_path = str(BASE_DIR / "shared" / ".env")


class BotSettings(BaseModel):
    admins: List[int] = Field(...)
    db_url: str = Field(...)
    ttl_default: int = Field(...)


class MaxSettings(BaseModel):
    db_url: str = Field(..., alias="max_db_url")


class LoggingConfig(BaseModel):
    log_level: Literal[
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    ] = "info"

    log_format: str = Field(..., alias="format")
    date_format: str = Field(...)


class WebSocket(BaseModel):
    url: str = Field(...)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        validate_default=False,
        case_sensitive=False,
        yaml_file=yaml_file_path,
        extra="ignore",
    )

    bot: BotSettings
    max: MaxSettings
    logging: LoggingConfig
    ws: WebSocket

    @classmethod
    def settings_customise_sources(cls, settings_cls, **kwargs):
        return (YamlConfigSettingsSource(settings_cls),)


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        validate_default=False,
        case_sensitive=False,
        env_file=env_file_path,
        env_file_encoding="utf-8",
    )

    bot_token: SecretStr = Field(...)


config = Settings()
env = EnvSettings()
