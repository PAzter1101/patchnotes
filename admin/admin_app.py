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
    "Генерация": [st.Page("pages/generation.py", title="Генерация", icon=":material/play_circle:")],
    "Контент": [
        st.Page("pages/posts.py", title="Посты", icon=":material/article:"),
        st.Page("pages/config_editor.py", title="Генератор", icon=":material/settings:"),
        st.Page("pages/mkdocs_editor.py", title="Блог", icon=":material/web:"),
    ],
    "Система": [
        st.Page("pages/schedule.py", title="Расписание", icon=":material/schedule:"),
        st.Page("pages/logs.py", title="Логи", icon=":material/terminal:"),
    ],
}

pg = st.navigation(pages)
pg.run()
