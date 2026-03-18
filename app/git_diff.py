import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

from config import AppConfig, RepoConfig

# Жёсткий лимит на diff одного большого файла при отдельной суммаризации
LARGE_FILE_MAX_CHARS = 60_000


@dataclass
class FileChange:
    path: str
    insertions: int
    deletions: int
    diff: str
    priority: int  # 0=высокий, 1=средний, 2=обычный
    is_large: bool


@dataclass
class RepoDiff:
    name: str
    url: str
    stat: str
    commit_log: str = ""
    files: list[FileChange] = field(default_factory=list)
    has_changes: bool = False


def _matches_any(path: str, patterns: list[str]) -> bool:
    p = Path(path)
    for pattern in patterns:
        if pattern.endswith("/"):
            if pattern.rstrip("/") in p.parts:
                return True
        elif fnmatch(p.name, pattern) or fnmatch(str(p), pattern):
            return True
    return False


def _get_priority(path: str, config: AppConfig) -> int | None:
    """None означает noise — файл нужно пропустить."""
    if _matches_any(path, config.noise_patterns):
        return None
    if _matches_any(path, config.priority_patterns):
        return 0
    if _matches_any(path, config.secondary_patterns):
        return 1
    return 2


def _run_git(args: list[str], cwd: str) -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _clone_repo(repo: RepoConfig, token: str, target_dir: str) -> None:
    url = repo.url
    if token:
        proto, rest = url.split("://", 1)
        if "gitlab.com" in url:
            # GitLab PAT требует формат oauth2:TOKEN
            url = f"{proto}://oauth2:{token}@{rest}"
        else:
            # GitHub и остальные
            url = f"{proto}://{token}@{rest}"

    result = subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "100",
            "--branch",
            repo.branch,
            url,
            target_dir,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git clone failed for {repo.name}:\n{result.stderr}")


def _parse_file_change(
    line: str, diff_base: str, cwd: str, config: AppConfig
) -> FileChange | None:
    parts = line.split("\t")
    if len(parts) != 3:
        return None
    ins_str, dels_str, path = parts
    try:
        insertions = int(ins_str)
        deletions = int(dels_str)
    except ValueError:
        return None  # бинарный файл

    priority = _get_priority(path, config)
    if priority is None:
        return None  # noise

    is_large = (insertions + deletions) > config.large_file_threshold
    file_diff = _run_git(["diff", diff_base, "--", path], cwd)

    if len(file_diff) > LARGE_FILE_MAX_CHARS:
        original_len = len(file_diff)
        truncation_note = (
            f"\n\n[... truncated, showing {LARGE_FILE_MAX_CHARS}"
            f" of {original_len} chars ...]"
        )
        file_diff = file_diff[:LARGE_FILE_MAX_CHARS] + truncation_note

    return FileChange(
        path=path,
        insertions=insertions,
        deletions=deletions,
        diff=file_diff,
        priority=priority,
        is_large=is_large,
    )


def _tag_age_days(tag: str, cwd: str) -> float | None:
    ts = _run_git(["log", "-1", "--format=%ct", tag], cwd)
    if not ts:
        return None
    return (time.time() - float(ts)) / 86400


def _resolve_diff_base_by_tags(
    repo: RepoConfig, config: AppConfig, cwd: str
) -> str | None:
    """Определяет diff_base по тегам с каскадным поиском базы.

    TARGET: последний тег в текущем периоде (иначе None — пропускаем репо).
    BASE (каскад):
      1. Последний тег в прошлом периоде [period, 2*period]
      2. Последний тег в расширенном окне [2*period, max_lookback]
      3. Самый старый коммит в окне [period, max_lookback]
      4. Последний коммит до начала окна (старше max_lookback)
    """
    period = config.period_days
    max_lookback = (1 + repo.tag_lookback_periods) * period

    all_tags = _run_git(
        ["tag", "--sort=-creatordate", "--merged", "HEAD"],
        cwd,
    ).splitlines()

    tags_with_age = [
        (tag, age) for tag in all_tags if (age := _tag_age_days(tag, cwd)) is not None
    ]

    # TARGET
    current_tags = [t for t, a in tags_with_age if a <= period]
    if not current_tags:
        return None
    target = current_tags[0]

    # BASE шаг 1: последний тег в прошлом периоде
    prev_tags = [t for t, a in tags_with_age if period < a <= 2 * period]
    if prev_tags:
        return f"{prev_tags[0]}..{target}"

    # BASE шаг 2: последний тег в расширенном окне
    extended_tags = [t for t, a in tags_with_age if 2 * period < a <= max_lookback]
    if extended_tags:
        return f"{extended_tags[0]}..{target}"

    # BASE шаг 3: самый старый коммит в окне [period, max_lookback]
    oldest_in_window = _run_git(
        [
            "log",
            f"--before={period} days ago",
            f"--after={max_lookback} days ago",
            "--format=%H",
            "--no-merges",
            "--reverse",
        ],
        cwd,
    )
    if oldest_in_window:
        oldest = oldest_in_window.splitlines()[0]
        parent = _run_git(["rev-parse", "--verify", f"{oldest}^"], cwd)
        base = parent if parent else oldest
        return f"{base}..{target}"

    # BASE шаг 4: последний коммит до начала окна
    last_before = _run_git(
        ["log", f"--before={max_lookback} days ago", "--format=%H", "-1"],
        cwd,
    )
    if last_before:
        return f"{last_before.strip()}..{target}"

    return None


def collect_repo_diff(repo: RepoConfig, config: AppConfig) -> RepoDiff:
    tmpdir = tempfile.mkdtemp(prefix="patchnotes_")
    try:
        token = repo.token or config.git_token
        _clone_repo(repo, token, tmpdir)

        if repo.diff_mode == "tag":
            diff_base = _resolve_diff_base_by_tags(repo, config, tmpdir)
            if diff_base is None:
                return RepoDiff(
                    name=repo.name, url=repo.url, stat="", has_changes=False
                )
        else:
            since_commits = _run_git(
                [
                    "log",
                    f"--since={config.period_days} days ago",
                    "--format=%H",
                    "--no-merges",
                ],
                tmpdir,
            )

            if not since_commits:
                return RepoDiff(
                    name=repo.name, url=repo.url, stat="", has_changes=False
                )

            oldest = since_commits.splitlines()[-1]
            parent = _run_git(["rev-parse", "--verify", f"{oldest}^"], tmpdir)
            diff_base = f"{parent}..HEAD" if parent else f"{oldest}..HEAD"

        stat = _run_git(["diff", "--stat", diff_base], tmpdir)
        if not stat:
            return RepoDiff(name=repo.name, url=repo.url, stat="", has_changes=False)

        commit_log = _run_git(
            [
                "log",
                diff_base,
                "--no-merges",
                "--format=%h %s",
            ],
            tmpdir,
        )

        numstat = _run_git(["diff", "--numstat", diff_base], tmpdir)
        files: list[FileChange] = []
        for line in numstat.splitlines():
            change = _parse_file_change(line, diff_base, tmpdir, config)
            if change is not None:
                files.append(change)

        if not files:
            return RepoDiff(
                name=repo.name,
                url=repo.url,
                stat=stat,
                commit_log=commit_log,
                has_changes=True,
            )

        files.sort(key=lambda f: (f.priority, -(f.insertions + f.deletions)))

        return RepoDiff(
            name=repo.name,
            url=repo.url,
            stat=stat,
            commit_log=commit_log,
            files=files,
            has_changes=True,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
