import os
from dataclasses import dataclass, field

import yaml


@dataclass
class RepoConfig:
    url: str
    name: str
    branch: str = "main"


@dataclass
class LLMConfig:
    analysis_model: str = "deepseek/deepseek-chat-v3-0324:free"
    post_model: str = "meta-llama/llama-4-maverick:free"


@dataclass
class PostConfig:
    site_name: str = "My Project"
    language: str = "en"


@dataclass
class AppConfig:
    repos: list[RepoConfig]
    noise_patterns: list[str] = field(default_factory=list)
    priority_patterns: list[str] = field(default_factory=list)
    secondary_patterns: list[str] = field(default_factory=list)
    large_file_threshold: int = 300
    max_diff_chars: int = 24_000
    period_days: int = 7
    llm: LLMConfig = field(default_factory=LLMConfig)
    post: PostConfig = field(default_factory=PostConfig)
    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    git_token: str = ""
    output_dir: str = "/output"
    prompts_dir: str = "/prompts"


def load_config() -> AppConfig:
    config_path = os.environ.get("CONFIG_PATH", "/config.yml")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    repos = [
        RepoConfig(
            url=r["url"],
            name=r.get(
                "name", r["url"].rstrip("/").split("/")[-1].removesuffix(".git")
            ),
            branch=r.get("branch", "main"),
        )
        for r in data.get("repos", [])
    ]

    llm_data = data.get("llm", {})
    post_data = data.get("post", {})

    return AppConfig(
        repos=repos,
        noise_patterns=data.get("noise_patterns", []),
        priority_patterns=data.get("priority_patterns", []),
        secondary_patterns=data.get("secondary_patterns", []),
        large_file_threshold=data.get("large_file_threshold", 300),
        max_diff_chars=data.get("max_diff_chars", 24_000),
        period_days=data.get("period_days", 7),
        llm=LLMConfig(
            analysis_model=llm_data.get(
                "analysis_model", "deepseek/deepseek-chat-v3-0324:free"
            ),
            post_model=llm_data.get("post_model", "meta-llama/llama-4-maverick:free"),
        ),
        post=PostConfig(
            site_name=post_data.get("site_name", "My Project"),
            language=post_data.get("language", "en"),
        ),
        llm_api_key=os.environ.get("LLM_API_KEY", ""),
        llm_base_url=os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        git_token=os.environ.get("GIT_TOKEN", ""),
        output_dir=os.environ.get("OUTPUT_DIR", "/output"),
        prompts_dir=os.environ.get("PROMPTS_DIR", "/prompts"),
    )
