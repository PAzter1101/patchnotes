import sys

from config import load_config
from git_diff import collect_repo_diff
from llm import analyze_repo, generate_post
from post_builder import write_post


def main() -> None:
    config = load_config()

    if not config.llm_api_key:
        print("ERROR: LLM_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    if not config.repos:
        print("ERROR: no repositories configured", file=sys.stderr)
        sys.exit(1)

    print(
        f"Collecting diffs for the past {config.period_days} days"
        f" across {len(config.repos)} repositories..."
    )

    repo_summaries: list[str] = []
    for repo in config.repos:
        print(f"  → {repo.name} ({repo.url})")
        repo_diff = collect_repo_diff(repo, config)

        if not repo_diff.has_changes:
            print("    no changes")
            repo_summaries.append(f"Repository «{repo.name}»: no changes.")
            continue

        print(f"    analyzing {len(repo_diff.files)} files...")
        summary = analyze_repo(repo_diff, config)
        repo_summaries.append(summary)
        print("    done")

    print("Generating post...")
    post_content = generate_post(repo_summaries, config)

    output_path = write_post(post_content, config)
    print(f"Post written to {output_path}")


if __name__ == "__main__":
    main()
