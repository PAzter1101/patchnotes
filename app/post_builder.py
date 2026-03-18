import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from config import AppConfig

logger = logging.getLogger(__name__)


def _today(config: AppConfig) -> str:
    return datetime.now(ZoneInfo(config.timezone)).date().isoformat()


def _run_dir(config: AppConfig) -> Path:
    """Возвращает директорию для текущего запуска: {output_dir}/{date}/"""
    d = Path(config.output_dir) / _today(config)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _parse_title_and_body(content: str) -> tuple[str, str]:
    """Разбирает ответ LLM на заголовок и тело поста."""
    title = ""
    body_lines: list[str] = []
    in_body = False

    for line in content.splitlines():
        if line.startswith("TITLE:"):
            title = line.removeprefix("TITLE:").strip()
        elif line.startswith("BODY:"):
            in_body = True
        elif in_body:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    # Fallback если модель не соблюла формат
    if not title and not body:
        return "", content.strip()
    if not title:
        return "", body
    return title, body


def save_synthesis(synthesis: str, config: AppConfig) -> None:
    """Сохраняет синтезированный список фич."""
    path = _run_dir(config) / "2_synthesis.txt"
    path.write_text(synthesis, encoding="utf-8")
    logger.info("Synthesis saved to %s", path)


def save_repo_analysis(repo_name: str, summary: str, config: AppConfig) -> None:
    """Сохраняет технический саммари репозитория."""
    safe_name = repo_name.lower().replace(" ", "_")
    path = _run_dir(config) / f"1_{safe_name}_analysis.txt"
    path.write_text(summary, encoding="utf-8")
    logger.info("Repo analysis saved to %s", path)


def write_post(content: str, config: AppConfig) -> Path:
    today = _today(config)
    run_dir = _run_dir(config)

    # Сохраняем сырой ответ LLM для отладки
    raw_path = run_dir / "3_post_raw.txt"
    raw_path.write_text(content, encoding="utf-8")
    logger.info("Raw LLM response saved to %s", raw_path)

    title, body = _parse_title_and_body(content)

    front_matter_lines = [f"date: {today}"]
    if title:
        front_matter_lines.append(f"title: {title}")

    front_matter = "---\n" + "\n".join(front_matter_lines) + "\n---\n\n"

    if title:
        full_content = front_matter + f"# {title}\n\n" + body
    else:
        full_content = front_matter + body

    output_path = run_dir / f"{today}.md"
    output_path.write_text(full_content, encoding="utf-8")

    return output_path
