"""Страница просмотра логов генерации."""

import streamlit as st

from scheduler import LOGS_DIR

st.header("Логи генерации")

if not LOGS_DIR.exists() or not list(LOGS_DIR.glob("*.log")):
    st.info("Логов пока нет")
    st.stop()

log_files = sorted(LOGS_DIR.glob("*.log"), reverse=True)

selected_log = st.selectbox("Выберите лог", [f.name for f in log_files])

if selected_log:
    log_content = (LOGS_DIR / selected_log).read_text(encoding="utf-8")
    st.code(log_content, language="log")
