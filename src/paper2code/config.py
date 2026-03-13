from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PAPER2CODE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Paper2Code"
    env: str = "development"
    log_level: str = "INFO"
    data_dir: Path = Field(default=Path("./data"))
    output_dir: Path = Field(default=Path("./data/runs"))
    groq_api_key: str = ""
    text_model: str = "llama-3.1-8b-instant"
    vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    max_critic_iterations: int = 1
    request_timeout_seconds: int = 60
    min_llm_request_interval_seconds: float = 5.0
    max_architecture_figures: int = 1
    max_plan_modules: int = 4
    paper_excerpt_char_limit: int = 2500
    planner_methodology_char_limit: int = 2500
    planner_architecture_char_limit: int = 1200
    test_code_sample_char_limit: int = 3000


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "inputs").mkdir(parents=True, exist_ok=True)
    return settings
