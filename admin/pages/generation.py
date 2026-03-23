"""Страница ручного запуска генерации."""

import streamlit as st

from scheduler import DATA_DIR, get_next_run, get_state, start_generation

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
    process, log_path = start_generation()

    with st.status("Генерация...", expanded=True) as status:
        log_area = st.empty()
        lines: list[str] = []

        assert process.stdout is not None
        for line in process.stdout:
            lines.append(line)
            log_area.code("".join(lines), language="log")

        process.wait()
        log_path.write_text("".join(lines), encoding="utf-8")

        if process.returncode == 0:
            status.update(
                label="Пост сгенерирован! Опубликуйте его на странице Посты",
                state="complete",
            )
        else:
            status.update(label="Ошибка генерации", state="error")
