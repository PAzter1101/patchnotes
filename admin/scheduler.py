"""Планировщик генерации на базе APScheduler."""

import json
import logging
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None
_lock = Lock()

DATA_DIR = Path("/data")
STATE_FILE = DATA_DIR / "scheduler.json"
LOGS_DIR = DATA_DIR / "logs"
GENERATOR_DIR = Path("/app/generator")
CONFIG_PATH = DATA_DIR / "config.yml"
DEFAULT_LOG_RETENTION_DAYS = 30


def _cleanup_old_logs() -> None:
    """Удаляет логи старше log_retention_days, если очистка включена."""
    if not LOGS_DIR.exists():
        return
    try:
        import yaml

        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return
    if not data.get("log_cleanup_enabled", False):
        return
    days = int(data.get("log_retention_days", DEFAULT_LOG_RETENTION_DAYS))
    cutoff = time.time() - days * 86400
    for log_file in LOGS_DIR.glob("*.log"):
        if log_file.stat().st_mtime < cutoff:
            log_file.unlink()
            logger.debug("Удалён старый лог: %s", log_file.name)


def _run_generation() -> None:
    """Запускает генератор как subprocess и публикует результат."""
    _cleanup_old_logs()
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = LOGS_DIR / f"{timestamp}.log"

    logger.info("Запуск генерации...")
    result = subprocess.run(
        ["python", "main.py"],
        cwd=str(GENERATOR_DIR),
        capture_output=True,
        text=True,
        timeout=600,
    )

    log_content = f"=== STDOUT ===\n{result.stdout}\n\n=== STDERR ===\n{result.stderr}"
    log_file.write_text(log_content, encoding="utf-8")

    if result.returncode != 0:
        logger.error("Генерация завершилась с ошибкой (код %d)", result.returncode)
        return

    logger.info("Генерация завершена успешно")
    publish_latest_post()


def publish_latest_post() -> None:
    """Копирует последний сгенерированный пост в директорию MkDocs."""
    output_dir = DATA_DIR / "output"
    posts_dir = DATA_DIR / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    if not output_dir.exists():
        return

    date_dirs = sorted(output_dir.iterdir(), reverse=True)
    for date_dir in date_dirs:
        if not date_dir.is_dir():
            continue
        md_files = list(date_dir.glob("*.md"))
        for md_file in md_files:
            dest = posts_dir / md_file.name
            shutil.copy2(md_file, dest)
            logger.info("Пост опубликован: %s", dest)
            return


def get_scheduler() -> BackgroundScheduler:
    """Возвращает singleton-планировщик."""
    global _scheduler
    with _lock:
        if _scheduler is None:
            _scheduler = BackgroundScheduler()
            _scheduler.start()
            _restore_schedule()
    return _scheduler


def _save_state(cron_expr: str, enabled: bool) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps({"cron": cron_expr, "enabled": enabled}),
        encoding="utf-8",
    )


def _restore_schedule() -> None:
    if not STATE_FILE.exists():
        return
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if state.get("enabled") and state.get("cron"):
            set_schedule(state["cron"])
    except Exception:
        logger.exception("Не удалось восстановить расписание")


def set_schedule(cron_expr: str) -> None:
    """Устанавливает расписание. Формат cron: '0 10 * * 1'."""
    sched = get_scheduler()

    if sched.get_job("generation"):
        sched.remove_job("generation")

    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError(f"Неверный cron-формат: {cron_expr}")

    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
    )
    sched.add_job(_run_generation, trigger, id="generation", replace_existing=True)
    _save_state(cron_expr, enabled=True)
    logger.info("Расписание установлено: %s", cron_expr)


def remove_schedule() -> None:
    """Удаляет расписание."""
    sched = get_scheduler()
    if sched.get_job("generation"):
        sched.remove_job("generation")
    _save_state("", enabled=False)


def get_state() -> dict[str, object]:
    """Возвращает текущее состояние планировщика."""
    if STATE_FILE.exists():
        try:
            result: dict[str, object] = json.loads(
                STATE_FILE.read_text(encoding="utf-8")
            )
            return result
        except Exception:
            pass
    return {"cron": "", "enabled": False}


def get_next_run() -> datetime | None:
    """Возвращает время следующего запуска."""
    sched = get_scheduler()
    job = sched.get_job("generation")
    if job and job.next_run_time:
        return datetime.fromtimestamp(job.next_run_time.timestamp())
    return None


def start_generation() -> tuple[subprocess.Popen, Path]:
    """Запускает генерацию, возвращает (процесс, путь к логу)."""
    _cleanup_old_logs()
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = LOGS_DIR / f"{timestamp}.log"

    process = subprocess.Popen(
        ["python", "-u", "main.py"],
        cwd=str(GENERATOR_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process, log_file
