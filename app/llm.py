import logging
import time
from pathlib import Path

from config import AppConfig, ModelConfig
from git_diff import RepoDiff
from openai import OpenAI

logger = logging.getLogger(__name__)


def _client(config: AppConfig) -> OpenAI:
    return OpenAI(
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
    )


def _load_prompt(config: AppConfig, filename: str, **kwargs) -> str:
    path = Path(config.prompts_dir) / filename
    template = path.read_text(encoding="utf-8")
    return template.format(**kwargs)


def _chat(
    client: OpenAI, mc: ModelConfig, system: str, user: str, retries: int = 3
) -> str:
    logger.debug(
        "LLM request → model=%s temp=%.1f system=%d chars user=%d chars",
        mc.model,
        mc.temperature,
        len(system),
        len(user),
    )
    last_exc: Exception = RuntimeError("No attempts made")
    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=mc.model,
                temperature=mc.temperature,
                max_tokens=mc.max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            if not response.choices:
                raise RuntimeError(f"Empty choices from model {mc.model}")
            content = response.choices[0].message.content
            result = content.strip() if content else ""
            if not result:
                raise RuntimeError(f"Empty content from model {mc.model}")
            logger.debug("LLM response ← %d chars", len(result))
            return result
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                delay = 2**attempt
                logger.warning(
                    "LLM request failed (attempt %d/%d): %s — retrying in %ds",
                    attempt,
                    retries,
                    exc,
                    delay,
                )
                time.sleep(delay)
    raise last_exc


def _summarize_large_file(
    client: OpenAI, mc: ModelConfig, file_path: str, diff: str, config: AppConfig
) -> str:
    logger.info("  Summarizing large file: %s (%d chars)", file_path, len(diff))
    system = _load_prompt(config, "summarize_file.txt")
    return _chat(
        client, mc, system, f"File: {file_path}\n\nDiff:\n{diff}", config.llm_retries
    )


def analyze_repo(repo_diff: RepoDiff, config: AppConfig) -> str:
    """Возвращает технический саммари по одному репозиторию."""
    if not repo_diff.has_changes:
        return (
            f"Repository «{repo_diff.name}»: no changes"
            f" in the past {config.period_days} days."
        )

    client = _client(config)
    mc = config.llm.analysis

    # Суммаризируем большие файлы отдельно
    large_summaries: list[str] = []
    for f in repo_diff.files:
        if f.is_large:
            summary = _summarize_large_file(client, mc, f.path, f.diff, config)
            large_summaries.append(
                f"**{f.path}** (+{f.insertions}/-{f.deletions}" f" lines):\n{summary}"
            )

    # Собираем маленькие файлы в рамках бюджета
    small_diffs: list[str] = []
    total_chars = 0
    skipped = 0
    for f in repo_diff.files:
        if f.is_large:
            continue
        if total_chars + len(f.diff) > config.max_diff_chars:
            skipped += 1
            continue
        small_diffs.append(f.diff)
        total_chars += len(f.diff)

    if skipped:
        logger.info(
            "  %d small files skipped (budget %d chars exhausted)",
            skipped,
            config.max_diff_chars,
        )

    prompt_parts = [f"Repository: {repo_diff.name}", "", "## Git stat", repo_diff.stat]
    if repo_diff.commit_log:
        prompt_parts += ["", "## Commit messages", repo_diff.commit_log]
    if large_summaries:
        prompt_parts += ["", "## Large file summaries"] + large_summaries
    if small_diffs:
        prompt_parts += ["", "## Detailed diff"] + small_diffs

    system = _load_prompt(
        config,
        "analyze_repo.txt",
        period_days=config.period_days,
    )
    user = "\n".join(prompt_parts)
    logger.info(
        "  Sending analysis request:"
        " %d large summaries, %d small diffs, %d total chars",
        len(large_summaries),
        len(small_diffs),
        len(user),
    )
    return _chat(client, mc, system, user, config.llm_retries)


def synthesize_features(repo_summaries: list[str], config: AppConfig) -> str:
    """Синтезирует связанные изменения из нескольких репо в фич-цепочки."""
    client = _client(config)
    mc = config.llm.analysis

    system = _load_prompt(
        config,
        "synthesize.txt",
        period_days=config.period_days,
        language=config.post.language,
    )
    summaries_text = "\n\n---\n\n".join(repo_summaries)
    user = f"Technical summaries from all repositories:\n\n{summaries_text}"
    logger.info("Sending synthesis request: %d chars total", len(user))
    return _chat(client, mc, system, user, config.llm_retries)


def generate_post(
    features: str,
    config: AppConfig,
    previous_attempt: str = "",
    feedback: str = "",
) -> str:
    """Генерирует пост. При повторной попытке принимает предыдущую версию и фидбек."""
    client = _client(config)
    mc = config.llm.post

    if previous_attempt and feedback:
        feedback_section = (
            "A previous attempt was REJECTED by the reviewer. "
            "Fix the issues listed below before writing the new version.\n\n"
            f"Previous attempt:\n{previous_attempt}\n\n"
            f"Reviewer feedback:\n{feedback}\n\n"
        )
    else:
        feedback_section = ""

    system = _load_prompt(
        config,
        "generate_post.txt",
        site_name=config.post.site_name,
        period_days=config.period_days,
        language=config.post.language,
        feedback_section=feedback_section,
    )
    user = f"Feature chains:\n\n{features}"
    logger.info(
        "Sending post generation request: system=%d user=%d chars%s",
        len(system),
        len(user),
        " (with reviewer feedback)" if feedback_section else "",
    )
    return _chat(client, mc, system, user, config.llm_retries)


def review_post(post: str, features: str, config: AppConfig) -> tuple[bool, str]:
    """Проверяет пост. Возвращает (passed, feedback)."""
    client = _client(config)
    mc = config.llm.review

    system = _load_prompt(
        config,
        "review_post.txt",
        language=config.post.language,
    )
    user = (
        f"Feature chains (source of truth):\n\n{features}"
        f"\n\n---\n\nPost to review:\n\n{post}"
    )
    logger.info("Sending post review request: %d chars total", len(user))
    result = _chat(client, mc, system, user, config.llm_retries)

    passed = result.strip().startswith("VERDICT: PASS")
    feedback = ""
    if not passed:
        in_feedback = False
        feedback_lines = []
        for line in result.splitlines():
            if line.startswith("FEEDBACK:"):
                in_feedback = True
            elif in_feedback:
                feedback_lines.append(line)
        feedback = "\n".join(feedback_lines).strip()

    logger.info("Review verdict: %s", "PASS" if passed else f"FAIL — {feedback[:100]}")
    return passed, feedback
