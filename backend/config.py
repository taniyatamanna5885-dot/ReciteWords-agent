"""应用配置管理"""
import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = BASE_DIR / "config.yaml"


class LLMSettings(BaseSettings):
    """LLM 配置"""
    provider: str = "openai"  # openai / ollama / custom
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000


class StudySettings(BaseSettings):
    """学习配置"""
    daily_word_count: int = 20  # 每日新词数量
    review_interval_days: list[int] = [1, 3, 7, 14, 30]  # 复习间隔


class AppSettings(BaseSettings):
    """应用总配置"""
    app_name: str = "EngLearn - 背单词Agent"
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'englearn.db'}"
    llm: LLMSettings = LLMSettings()
    study: StudySettings = StudySettings()


def load_settings() -> AppSettings:
    """从 config.yaml 和环境变量加载配置"""
    config_data = {}

    # 从 config.yaml 读取
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

    # 构建 LLM 配置
    llm_data = config_data.get("llm", {})
    # 环境变量优先
    llm_settings = LLMSettings(
        provider=os.getenv("LLM_PROVIDER", llm_data.get("provider", "openai")),
        model=os.getenv("LLM_MODEL", llm_data.get("model", "gpt-4o-mini")),
        api_key=os.getenv("LLM_API_KEY", llm_data.get("api_key")),
        base_url=os.getenv("LLM_BASE_URL", llm_data.get("base_url")),
        temperature=float(os.getenv("LLM_TEMPERATURE", llm_data.get("temperature", 0.7))),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", llm_data.get("max_tokens", 2000))),
    )

    # 构建学习配置
    study_data = config_data.get("study", {})
    study_settings = StudySettings(
        daily_word_count=int(os.getenv("DAILY_WORD_COUNT", study_data.get("daily_word_count", 20))),
    )

    return AppSettings(
        llm=llm_settings,
        study=study_settings,
        database_url=os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'englearn.db'}"),
    )


settings = load_settings()
