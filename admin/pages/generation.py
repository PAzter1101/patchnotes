"""Страница ручного запуска генерации."""

from pathlib import Path

import streamlit as st

from scheduler import DATA_DIR, get_next_run, get_state, run_now

OUTPUT_DIR = DATA_DIR / "output"

st.header("Генерация поста")

col1, col2 = st.columns(2)

with col1:
    state = get_state()
    if state["enabled"]:
        next_run = get_next_run()
        msg = f"Расписание активно: `{state['cron']}`"
        if next_run:
            msg += f"  \nСледующий запуск: **{next_run:%Y-%m-%d %H:%M}**"
        st.success(msg)
    else:
        st.info("Автоматическое расписание не настроено")

with col2:
    if OUTPUT_DIR.exists():
        date_dirs = sorted(
            [d for d in OUTPUT_DIR.iterdir() if d.is_dir()], reverse=True
        )
        if date_dirs:
            st.metric("Последняя генерация", date_dirs[0].name)

st.divider()

if st.button("Запустить генерацию", type="primary", use_container_width=True):
    with st.spinner("Генерация... это может занять несколько минут"):
        log_path = run_now()
        log_content = Path(log_path).read_text(encoding="utf-8")

    if "Post written to" in log_content:
        st.success("Пост сгенерирован и опубликован!")
    else:
        st.error("Генерация завершилась с ошибкой")

    with st.expander("Логи", expanded=True):
        st.code(log_content, language="log")
