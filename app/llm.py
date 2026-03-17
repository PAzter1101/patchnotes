from pathlib import Path

from config import AppConfig
from git_diff import RepoDiff
from openai import OpenAI


def _client(config: AppConfig) -> OpenAI:
    return OpenAI(
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
    )


def _load_prompt(config: AppConfig, filename: str, **kwargs) -> str:
    path = Path(config.prompts_dir) / filename
    template = path.read_text(encoding="utf-8")
    return template.format(**kwargs)


def _chat(client: OpenAI, model: str, system: str, user: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = response.choices[0].message.content
    return content.strip() if content else ""


def _summarize_large_file(
    client: OpenAI, model: str, file_path: str, diff: str, config: AppConfig
) -> str:
    system = _load_prompt(config, "summarize_file.txt", language=config.post.language)
    return _chat(client, model, system, f"File: {file_path}\n\nDiff:\n{diff}")


def analyze_repo(repo_diff: RepoDiff, config: AppConfig) -> str:
    """Возвращает технический саммари по одному репозиторию."""
    if not repo_diff.has_changes:
        return (
            f"Repository «{repo_diff.name}»: no changes"
            f" in the past {config.period_days} days."
        )

    client = _client(config)
    model = config.llm.analysis_model

    # Суммаризируем большие файлы отдельно
    large_summaries: list[str] = []
    for f in repo_diff.files:
        if f.is_large:
            summary = _summarize_large_file(client, model, f.path, f.diff, config)
            large_summaries.append(
                f"**{f.path}** (+{f.insertions}/-{f.deletions} lines):\n{summary}"
            )

    # Собираем маленькие файлы в рамках бюджета
    small_diffs: list[str] = []
    total_chars = 0
    for f in repo_diff.files:
        if f.is_large:
            continue
        if total_chars + len(f.diff) > config.max_diff_chars:
            break
        small_diffs.append(f.diff)
        total_chars += len(f.diff)

    prompt_parts = [f"Repository: {repo_diff.name}", "", "## Git stat", repo_diff.stat]

    if large_summaries:
        prompt_parts += ["", "## Large file summaries"] + large_summaries

    if small_diffs:
        prompt_parts += ["", "## Detailed diff"] + small_diffs

    system = _load_prompt(
        config,
        "analyze_repo.txt",
        period_days=config.period_days,
        language=config.post.language,
    )
    return _chat(client, model, system, "\n".join(prompt_parts))


def generate_post(repo_summaries: list[str], config: AppConfig) -> str:
    """Генерирует финальный пост для пользователей из технических саммари."""
    client = _client(config)
    model = config.llm.post_model

    system = _load_prompt(
        config,
        "generate_post.txt",
        site_name=config.post.site_name,
        period_days=config.period_days,
        language=config.post.language,
    )
    summaries_text = "\n\n---\n\n".join(repo_summaries)
    return _chat(client, model, system, f"Technical summaries:\n\n{summaries_text}")
