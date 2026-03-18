import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import AppConfig, RepoConfig, load_config
from git_diff import collect_repo_diff
from llm import analyze_repo, generate_post, review_post, synthesize_features
from post_builder import save_repo_analysis, save_synthesis, write_post

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _process_repo(repo: RepoConfig, config: AppConfig) -> str:
    logger.info("=== Repository: %s (%s) ===", repo.name, repo.url)

    repo_diff = collect_repo_diff(repo, config)

    if not repo_diff.has_changes:
        logger.info(
            "[%s] No changes in the past %d days", repo.name, config.period_days
        )
        return f"Repository «{repo.name}»: no changes."

    total = len(repo_diff.files)
    large = sum(1 for f in repo_diff.files if f.is_large)
    logger.info(
        "[%s] Found %d changed files (%d large, will be summarized separately)",
        repo.name,
        total,
        large,
    )
    for f in repo_diff.files:
        logger.debug(
            "  [%s] [priority=%d large=%s] %s (+%d/-%d)",
            repo.name,
            f.priority,
            f.is_large,
            f.path,
            f.insertions,
            f.deletions,
        )

    logger.info("[%s] Analyzing with model: %s", repo.name, config.llm.analysis.model)
    summary = analyze_repo(repo_diff, config)
    logger.debug("[%s] Repo summary:\n%s", repo.name, summary)
    save_repo_analysis(repo.name, summary, config)
    logger.info("[%s] Analysis done", repo.name)
    return summary


def main() -> None:
    config = load_config()

    if not config.llm_api_key:
        logger.error("LLM_API_KEY is not set")
        sys.exit(1)

    if not config.repos:
        logger.error("No repositories configured")
        sys.exit(1)

    logger.info(
        "Starting: %d repositories, period %d days,"
        " analysis model: %s, post model: %s",
        len(config.repos),
        config.period_days,
        config.llm.analysis.model,
        config.llm.post.model,
    )

    repo_summaries: list[str] = []
    with ThreadPoolExecutor(max_workers=len(config.repos)) as executor:
        futures = {
            executor.submit(_process_repo, repo, config): repo for repo in config.repos
        }
        for future in as_completed(futures):
            repo = futures[future]
            try:
                repo_summaries.append(future.result())
            except Exception:
                logger.exception("Failed to process repository: %s", repo.name)

    logger.info(
        "=== Synthesizing features with model: %s ===", config.llm.analysis.model
    )
    features = synthesize_features(repo_summaries, config)
    logger.debug("Synthesis result:\n%s", features)
    save_synthesis(features, config)
    logger.info("Synthesis done")

    logger.info("=== Generating post with model: %s ===", config.llm.post.model)
    post_content = ""
    feedback = ""
    for attempt in range(1, config.max_review_iterations + 1):
        post_content = generate_post(features, config, post_content, feedback)
        logger.debug("Post attempt %d:\n%s", attempt, post_content)

        logger.info(
            "=== Reviewing post (attempt %d/%d) ===",
            attempt,
            config.max_review_iterations,
        )
        passed, feedback = review_post(post_content, features, config)
        if passed:
            logger.info("Post approved on attempt %d", attempt)
            break
        logger.warning("Post rejected (attempt %d): %s", attempt, feedback[:120])
    else:
        logger.warning("Max review iterations reached, publishing last attempt anyway")

    output_path = write_post(post_content, config)
    logger.info("Post written to %s", output_path)


if __name__ == "__main__":
    main()
