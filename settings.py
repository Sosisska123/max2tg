from pathlib import Path

from typing import List

from pydantic import BaseModel, SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource


LOG_DEFAULT_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DATE_DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S"

BASE_DIR = Path(__file__).parent
yaml_file_path = str(BASE_DIR / "shared" / "config.yaml")
env_file_path = str(BASE_DIR / "shared" / ".env")

# Validate required configuration files exist
_yaml_path = Path(yaml_file_path)
_env_path = Path(env_file_path)
if not _yaml_path.exists():
    raise FileNotFoundError(f"Required config file not found: {yaml_file_path}")
if not _env_path.exists():
    raise FileNotFoundError(f"Required env file not found: {env_file_path}")


class BotSettings(BaseModel):
    admins: List[int] = Field(...)
    db_url: str = Field(...)
    ttl_default: int = Field(...)


class LoggingConfig(BaseModel):
    log_format: str = Field(..., alias="format")
    date_format: str = Field(...)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        validate_default=False,
        case_sensitive=False,
        yaml_file=yaml_file_path,
        extra="ignore",
    )

    bot: BotSettings
    logging: LoggingConfig

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
