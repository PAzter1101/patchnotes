"""Страница редактирования настроек MkDocs."""

import streamlit as st
import yaml

from scheduler import DATA_DIR

MKDOCS_PATH = DATA_DIR / "mkdocs.yml"
DEFAULT_MKDOCS = "/app/mkdocs-default.yml"

st.header("Настройки блога")


def _ensure_mkdocs_config() -> str:
    """Копирует дефолтный mkdocs.yml на PVC если отсутствует."""
    if MKDOCS_PATH.exists():
        return MKDOCS_PATH.read_text(encoding="utf-8")
    from pathlib import Path

    default = Path(DEFAULT_MKDOCS)
    if default.exists():
        content = default.read_text(encoding="utf-8")
        MKDOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
        MKDOCS_PATH.write_text(content, encoding="utf-8")
        return content
    return "site_name: Patchnotes\n"


config_text = _ensure_mkdocs_config()

edited = st.text_area("mkdocs.yml", value=config_text, height=400)

if st.button("Сохранить", type="primary"):
    try:
        yaml.safe_load(edited)
    except yaml.YAMLError as e:
        st.error(f"Ошибка YAML: {e}")
    else:
        MKDOCS_PATH.write_text(edited, encoding="utf-8")
        st.success("Настройки сохранены! MkDocs подхватит изменения автоматически.")
