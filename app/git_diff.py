import shutil
import subprocess
import tempfile
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


def collect_repo_diff(repo: RepoConfig, config: AppConfig) -> RepoDiff:
    tmpdir = tempfile.mkdtemp(prefix="patchnotes_")
    try:
        token = repo.token or config.git_token
        _clone_repo(repo, token, tmpdir)

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
            return RepoDiff(name=repo.name, url=repo.url, stat="", has_changes=False)

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
