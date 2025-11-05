from pathlib import Path

from typing import List, Literal

# from functools import lru_cache

from pydantic import BaseModel, SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource


LOG_DEFAULT_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
WORKER_LOG_DEFAULT_FORMAT = "[%(asctime)s.%(msecs)03d][%(processName)s] %(module)16s:%(lineno)-3d %(levelname)-7s - %(message)s"

BASE_DIR = Path(__file__).parent.parent
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
        validate_default=False,
        case_sensitive=False,
        yaml_file=yaml_file_path,
        extra="ignore",
    )

    bot: BotSettings

    logging: LoggingConfig = LoggingConfig()

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

# @lru_cache(maxsize=1)
# def get_config() -> Settings:
#     return Settings()


# @lru_cache(maxsize=1)
# def get_env() -> EnvSettings:
#     return EnvSettings()
