import os

import yaml
from pydantic import BaseModel, Field, model_validator


class RepoConfig(BaseModel):
    url: str
    name: str = ""
    branch: str = "main"
    token: str = ""  # перекрывает глобальный GIT_TOKEN
    diff_mode: str = "period"  # "period" | "tag"
    # для diff_mode=tag: глубина поиска базового тега/коммита (в периодах)
    tag_lookback_periods: int = 1
    # дополнительные паттерны, объединяются с глобальными
    noise_patterns: list[str] = Field(default_factory=list)
    priority_patterns: list[str] = Field(default_factory=list)
    secondary_patterns: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def set_name_from_url(cls, values: dict) -> dict:
        if not values.get("name"):
            url = values.get("url", "")
            values["name"] = url.rstrip("/").split("/")[-1].removesuffix(".git")
        return values


class ModelConfig(BaseModel):
    model: str
    temperature: float = 0.3
    max_tokens: int = 2000


class LLMConfig(BaseModel):
    # Анализ репозиториев и синтез: точность важнее креативности
    analysis: ModelConfig = Field(
        default_factory=lambda: ModelConfig(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            temperature=0.2,
            max_tokens=4000,
        )
    )
    # Генерация поста: нужен живой текст
    post: ModelConfig = Field(
        default_factory=lambda: ModelConfig(
            model="arcee-ai/trinity-large-preview:free",
            temperature=0.7,
            max_tokens=1500,
        )
    )
    # Ревью: строгая проверка, минимальная вариативность
    review: ModelConfig = Field(
        default_factory=lambda: ModelConfig(
            model="arcee-ai/trinity-large-preview:free",
            temperature=0.2,
            max_tokens=500,
        )
    )


class PostConfig(BaseModel):
    site_name: str = "My Project"
    language: str = "en"


class AppConfig(BaseModel):
    repos: list[RepoConfig]
    noise_patterns: list[str] = Field(default_factory=list)
    priority_patterns: list[str] = Field(default_factory=list)
    secondary_patterns: list[str] = Field(default_factory=list)
    large_file_threshold: int = 300
    max_diff_chars: int = 24_000
    period_days: int = 7
    max_review_iterations: int = 3
    llm_retries: int = 3
    llm: LLMConfig = Field(default_factory=LLMConfig)
    post: PostConfig = Field(default_factory=PostConfig)
    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    git_token: str = ""
    output_dir: str = "/output"
    prompts_dir: str = "/prompts"
    timezone: str = "UTC"


def load_config() -> AppConfig:
    config_path = os.environ.get("CONFIG_PATH", "/config.yml")

    with open(config_path) as f:
        data: dict = yaml.safe_load(f) or {}

    # Переменные окружения перекрывают значения из конфига
    env_map = {
        "LLM_API_KEY": "llm_api_key",
        "LLM_BASE_URL": "llm_base_url",
        "GIT_TOKEN": "git_token",
        "OUTPUT_DIR": "output_dir",
        "PROMPTS_DIR": "prompts_dir",
    }
    for env_key, config_key in env_map.items():
        val = os.environ.get(env_key)
        if val:
            data[config_key] = val

    return AppConfig.model_validate(data)
