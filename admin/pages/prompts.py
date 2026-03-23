"""Страница редактирования промптов для LLM."""

from pathlib import Path

import streamlit as st

from scheduler import DATA_DIR

# Промпты на PVC (редактируемые), фолбэк — встроенные в образ
PROMPTS_DIR = DATA_DIR / "prompts"
DEFAULT_PROMPTS_DIR = Path("/app/prompts")

PROMPT_FILES = {
    "analyze_repo.txt": "Анализ репозитория",
    "summarize_file.txt": "Суммаризация большого файла",
    "synthesize.txt": "Синтез фич из нескольких репозиториев",
    "generate_post.txt": "Генерация поста",
    "review_post.txt": "Ревью поста",
}

st.header("Промпты")
st.caption(
    "Шаблоны запросов к LLM."
    " Переменные в `{фигурных скобках}` подставляются автоматически."
)


def _read_prompt(filename: str) -> str:
    pvc_path = PROMPTS_DIR / filename
    if pvc_path.exists():
        return pvc_path.read_text(encoding="utf-8")
    default_path = DEFAULT_PROMPTS_DIR / filename
    if default_path.exists():
        return default_path.read_text(encoding="utf-8")
    return ""


def _save_prompt(filename: str, content: str) -> None:
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    (PROMPTS_DIR / filename).write_text(content, encoding="utf-8")


tabs = st.tabs(list(PROMPT_FILES.values()))

for tab, (filename, label) in zip(tabs, PROMPT_FILES.items()):
    with tab:
        current = _read_prompt(filename)
        edited = st.text_area(
            filename, value=current, height=300, key=f"prompt_{filename}"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Сохранить", key=f"save_{filename}", type="primary"):
                _save_prompt(filename, edited)
                st.success("Сохранено!")
        with col2:
            if st.button("Сбросить к дефолту", key=f"reset_{filename}"):
                default = DEFAULT_PROMPTS_DIR / filename
                if default.exists():
                    _save_prompt(filename, default.read_text(encoding="utf-8"))
                    st.success("Сброшено к значению по умолчанию!")
                    st.rerun()
                else:
                    st.warning("Дефолтный промпт не найден")
