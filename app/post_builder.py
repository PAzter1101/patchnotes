from datetime import date
from pathlib import Path

from config import AppConfig


def write_post(content: str, config: AppConfig) -> Path:
    today = date.today().isoformat()

    front_matter = f"---\ndate: {today}\n---\n\n"
    full_content = front_matter + content

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{today}.md"
    output_path.write_text(full_content, encoding="utf-8")

    return output_path
