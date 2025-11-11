from pathlib import Path

from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource


LOG_DEFAULT_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
WORKER_LOG_DEFAULT_FORMAT = "[%(asctime)s.%(msecs)03d][%(processName)s] %(module)16s:%(lineno)-3d %(levelname)-7s - %(message)s"

BASE_DIR = Path(__file__).parent.parent
yaml_file_path = str(BASE_DIR / "shared" / "config.yaml")


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
        yaml_config_section="ws",
        extra="ignore",
    )

    ws_url: str = Field(alias="url")

    logging: LoggingConfig = LoggingConfig()

    @classmethod
    def settings_customise_sources(cls, settings_cls, **kwargs):
        return (YamlConfigSettingsSource(settings_cls),)


config = Settings()
