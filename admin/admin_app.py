"""Patchnotes Admin — точка входа."""

import streamlit as st

from scheduler import get_scheduler

st.set_page_config(
    page_title="Patchnotes Admin",
    page_icon=":material/newsmode:",
    layout="wide",
)

# Инициализируем планировщик один раз при старте
get_scheduler()

pages = {
    "Генерация": [
        st.Page("pages/generation.py", title="Запуск", icon=":material/play_circle:"),
        st.Page("pages/schedule.py", title="Расписание", icon=":material/schedule:"),
        st.Page("pages/logs.py", title="Логи", icon=":material/terminal:"),
    ],
    "Контент": [
        st.Page("pages/posts.py", title="Посты", icon=":material/article:"),
        st.Page("pages/mkdocs_editor.py", title="Блог", icon=":material/web:"),
    ],
    "Настройки": [
        st.Page("pages/settings.py", title="Основные", icon=":material/tune:"),
        st.Page("pages/repos.py", title="Репозитории", icon=":material/folder_copy:"),
        st.Page("pages/prompts.py", title="Промпты", icon=":material/edit_note:"),
        st.Page("pages/config_editor.py", title="Конфиг YAML", icon=":material/code:"),
    ],
}

pg = st.navigation(pages)
pg.run()
