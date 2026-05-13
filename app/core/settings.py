from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


class EnvironmentSettings(BaseModel):
    environmentCode: str = "test"
    baseUrl: str = "http://localhost:3000"
    domainWhitelist: list[str] = Field(default_factory=lambda: ["localhost"])


class Settings(BaseModel):
    app_title: str = "UI Automation Test Agent"
    app_version: str = "0.1.0"
    data_dir: Path = Path("data")
    default_environment: EnvironmentSettings = Field(default_factory=EnvironmentSettings)


def load_settings() -> Settings:
    data_dir = Path(os.getenv("AGENT_DATA_DIR", "data"))
    return Settings(data_dir=data_dir)
