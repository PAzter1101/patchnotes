"""Страница настройки расписания автогенерации."""

import streamlit as st

from scheduler import get_next_run, get_state, remove_schedule, set_schedule

st.header("Расписание автогенерации")

state = get_state()

st.markdown(
    """
Формат cron: `минута час день месяц день_недели`

| Пример | Значение |
|---|---|
| `0 10 * * 1` | Каждый понедельник в 10:00 |
| `0 9 * * 1,4` | Понедельник и четверг в 09:00 |
| `30 18 * * *` | Каждый день в 18:30 |
"""
)

cron_input = st.text_input(
    "Cron-выражение",
    value=state.get("cron", ""),
    placeholder="0 10 * * 1",
)

col1, col2 = st.columns(2)

with col1:
    if st.button("Включить расписание", type="primary"):
        if not cron_input.strip():
            st.error("Введите cron-выражение")
        else:
            try:
                set_schedule(cron_input.strip())
                st.success(f"Расписание установлено: `{cron_input}`")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

with col2:
    if st.button("Отключить расписание", disabled=not state["enabled"]):
        remove_schedule()
        st.success("Расписание отключено")
        st.rerun()

if state["enabled"]:
    next_run = get_next_run()
    if next_run:
        st.info(f"Следующий запуск: **{next_run:%Y-%m-%d %H:%M:%S}**")
