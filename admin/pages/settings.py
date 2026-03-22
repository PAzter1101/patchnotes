"""Визуальный редактор основных настроек."""

import streamlit as st
import yaml

from scheduler import DATA_DIR

CONFIG_PATH = DATA_DIR / "config.yml"

LANGUAGES = ["ru", "en", "de", "fr", "es", "zh", "ja", "ko"]
MODEL_DEFAULTS = {
    "analysis": ("nvidia/nemotron-3-super-120b-a12b:free", 0.2, 4000),
    "post": ("arcee-ai/trinity-large-preview:free", 0.7, 1500),
    "review": ("arcee-ai/trinity-large-preview:free", 0.2, 500),
}

st.header("Настройки")


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return {}


def _save_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


config = _load_config()

# --- API ---
st.subheader("API")
col1, col2 = st.columns(2)
with col1:
    llm_api_key = st.text_input(
        "LLM API Key", value=config.get("llm_api_key", ""), type="password"
    )
with col2:
    llm_base_url = st.text_input(
        "LLM Base URL",
        value=config.get("llm_base_url", "https://openrouter.ai/api/v1"),
    )
git_token = st.text_input(
    "Git Token (глобальный)", value=config.get("git_token", ""), type="password"
)

# --- General ---
st.subheader("Общие")
col1, col2, col3, col4 = st.columns(4)
with col1:
    period_days = st.number_input(
        "Период анализа (дни)",
        value=config.get("period_days", 7),
        min_value=1,
        max_value=90,
    )
with col2:
    timezone = st.text_input("Часовой пояс", value=config.get("timezone", "UTC"))
with col3:
    max_review = st.number_input(
        "Макс. итераций ревью",
        value=config.get("max_review_iterations", 3),
        min_value=0,
        max_value=10,
    )
with col4:
    log_cleanup = st.checkbox(
        "Очистка логов",
        value=config.get("log_cleanup_enabled", False),
    )
    log_retention = st.number_input(
        "Хранить логи (дни)",
        value=config.get("log_retention_days", 30),
        min_value=1,
        max_value=365,
        disabled=not log_cleanup,
    )

# --- Post ---
st.subheader("Пост")
post_cfg = config.get("post", {})
col1, col2 = st.columns(2)
with col1:
    site_name = st.text_input(
        "Название сайта", value=post_cfg.get("site_name", "My Project")
    )
with col2:
    lang_value = post_cfg.get("language", "en")
    lang_idx = LANGUAGES.index(lang_value) if lang_value in LANGUAGES else 0
    language = st.selectbox("Язык", options=LANGUAGES, index=lang_idx)

# --- LLM Models ---
st.subheader("Модели LLM")
llm_cfg = config.get("llm", {})
stage_labels = {"analysis": "Анализ", "post": "Генерация поста", "review": "Ревью"}

for stage, label in stage_labels.items():
    st.caption(label)
    mc = llm_cfg.get(stage, {})
    defaults = MODEL_DEFAULTS[stage]
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.text_input("Модель", value=mc.get("model", defaults[0]), key=f"{stage}_m")
    with col2:
        st.number_input(
            "Temperature",
            value=mc.get("temperature", defaults[1]),
            min_value=0.0,
            max_value=2.0,
            step=0.1,
            key=f"{stage}_t",
        )
    with col3:
        st.number_input(
            "Max tokens",
            value=mc.get("max_tokens", defaults[2]),
            min_value=100,
            max_value=16000,
            step=100,
            key=f"{stage}_k",
        )

# --- Save ---
st.divider()
if st.button("Сохранить", type="primary", use_container_width=True):
    config["llm_api_key"] = llm_api_key
    config["llm_base_url"] = llm_base_url
    config["git_token"] = git_token
    config["period_days"] = period_days
    config["timezone"] = timezone
    config["max_review_iterations"] = max_review
    config["log_cleanup_enabled"] = log_cleanup
    config["log_retention_days"] = log_retention
    config["post"] = {"site_name": site_name, "language": language}
    config["llm"] = {}
    for stage in stage_labels:
        config["llm"][stage] = {
            "model": st.session_state[f"{stage}_m"],
            "temperature": st.session_state[f"{stage}_t"],
            "max_tokens": st.session_state[f"{stage}_k"],
        }
    _save_config(config)
    st.success("Настройки сохранены!")
