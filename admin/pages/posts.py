"""Страница управления постами."""

import shutil

import streamlit as st

from scheduler import DATA_DIR

OUTPUT_DIR = DATA_DIR / "output"
POSTS_DIR = DATA_DIR / "posts"

st.header("Управление постами")

if not OUTPUT_DIR.exists():
    st.info("Пока нет сгенерированных постов")
    st.stop()

date_dirs = sorted([d for d in OUTPUT_DIR.iterdir() if d.is_dir()], reverse=True)
if not date_dirs:
    st.info("Пока нет сгенерированных постов")
    st.stop()

selected_date = st.selectbox("Дата генерации", [d.name for d in date_dirs])
run_dir = OUTPUT_DIR / selected_date
md_file = run_dir / f"{selected_date}.md"

if not md_file.exists():
    st.warning(f"Файл {md_file.name} не найден")
    st.stop()

content = md_file.read_text(encoding="utf-8")

tab_preview, tab_edit, tab_files = st.tabs(
    ["Превью", "Редактирование", "Файлы запуска"]
)

with tab_preview:
    parts = content.split("---", 2)
    st.markdown(parts[2] if len(parts) >= 3 else content)

with tab_edit:
    edited = st.text_area("Редактировать пост", value=content, height=400)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Сохранить"):
            md_file.write_text(edited, encoding="utf-8")
            st.success("Сохранено!")
    with col2:
        published = POSTS_DIR / md_file.name
        is_published = published.exists()
        if st.button(
            "Опубликовано" if is_published else "Опубликовать",
            disabled=is_published,
        ):
            POSTS_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md_file, published)
            st.success("Пост опубликован в блог!")
            st.rerun()

with tab_files:
    for f in sorted(run_dir.iterdir()):
        with st.expander(f.name):
            lang = "markdown" if f.suffix == ".md" else "text"
            st.code(f.read_text(encoding="utf-8"), language=lang)
