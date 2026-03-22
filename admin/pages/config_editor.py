"""Страница редактирования конфигурации."""

import sys

import streamlit as st
import yaml

from scheduler import DATA_DIR

CONFIG_PATH = DATA_DIR / "config.yml"

st.header("Конфигурация")

if CONFIG_PATH.exists():
    config_text = CONFIG_PATH.read_text(encoding="utf-8")
else:
    config_text = "# Конфигурация пока не создана\nrepos: []\n"

edited_config = st.text_area("config.yml", value=config_text, height=500)

col1, col2 = st.columns(2)

with col1:
    if st.button("Сохранить", type="primary"):
        try:
            yaml.safe_load(edited_config)
        except yaml.YAMLError as e:
            st.error(f"Ошибка YAML: {e}")
        else:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(edited_config, encoding="utf-8")
            st.success("Конфигурация сохранена!")

with col2:
    if st.button("Валидировать"):
        try:
            data = yaml.safe_load(edited_config)
            sys.path.insert(0, "/app/generator")
            from config import AppConfig

            AppConfig.model_validate(data)
            st.success("Конфигурация валидна!")
        except Exception as e:
            st.error(f"Ошибка валидации: {e}")
