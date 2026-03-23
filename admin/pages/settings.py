"""Визуальный редактор основных настроек."""

import streamlit as st
import yaml

from scheduler import DATA_DIR

CONFIG_PATH = DATA_DIR / "config.yml"
MKDOCS_PATH = DATA_DIR / "mkdocs.yml"

LANGUAGES = ["ru", "en", "de", "fr", "es", "zh", "ja", "ko"]
MODEL_DEFAULTS = {
    "analysis": ("nvidia/nemotron-3-super-120b-a12b:free", 0.2, 4000),
    "post": ("arcee-ai/trinity-large-preview:free", 0.7, 1500),
    "review": ("arcee-ai/trinity-large-preview:free", 0.2, 500),
}

st.header("Настройки")


def _load_yaml(path):  # type: ignore[no-untyped-def]
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {}


def _save_yaml(path, data):  # type: ignore[no-untyped-def]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


def _lines_to_list(text: str) -> list[str]:
    return [line.strip() for line in text.strip().splitlines() if line.strip()]


config = _load_yaml(CONFIG_PATH)

# --- API ---
st.subheader("API")
col1, col2 = st.columns(2)
with col1:
    llm_api_key = st.text_input(
        "LLM API Key *",
        value=config.get("llm_api_key", ""),
        type="password",
        help="Ключ от OpenAI-совместимого провайдера (OpenRouter, Ollama и др.)",
    )
with col2:
    llm_base_url = st.text_input(
        "LLM Base URL *",
        value=config.get("llm_base_url", "https://openrouter.ai/api/v1"),
        help="Базовый URL API. Поддерживается любой OpenAI-совместимый провайдер",
    )
git_token = st.text_input(
    "Git Token (глобальный)",
    value=config.get("git_token", ""),
    type="password",
    help="Токен по умолчанию для всех репозиториев. Можно переопределить per-repo",
)

# --- Site ---
st.subheader("Сайт")
post_cfg = config.get("post", {})
col1, col2, col3 = st.columns([2, 3, 1])
with col1:
    site_name = st.text_input(
        "Название сайта *",
        value=post_cfg.get("site_name", "My Project"),
        help="Используется в заголовке поста и в MkDocs",
    )
with col2:
    site_desc = st.text_input(
        "Описание сайта",
        value=post_cfg.get("site_description", ""),
        help="Описание для MkDocs (мета-тег description)",
    )
with col3:
    lang_value = post_cfg.get("language", "en")
    lang_idx = LANGUAGES.index(lang_value) if lang_value in LANGUAGES else 0
    language = st.selectbox(
        "Язык",
        options=LANGUAGES,
        index=lang_idx,
        help="Язык генерируемых постов и интерфейса MkDocs",
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
        help="За сколько дней собирать git diff",
    )
with col2:
    timezone = st.text_input(
        "Часовой пояс",
        value=config.get("timezone", "UTC"),
        help="Для даты в имени файла поста (напр. Europe/Moscow)",
    )
with col3:
    max_review = st.number_input(
        "Макс. итераций ревью",
        value=config.get("max_review_iterations", 3),
        min_value=0,
        max_value=10,
        help="Сколько раз ревьювер может отправить пост на доработку",
    )
with col4:
    log_cleanup = st.checkbox(
        "Очистка логов",
        value=config.get("log_cleanup_enabled", False),
        help="Автоматически удалять старые логи генерации",
    )
    log_retention = st.number_input(
        "Хранить логи (дни)",
        value=config.get("log_retention_days", 30),
        min_value=1,
        max_value=365,
        disabled=not log_cleanup,
    )

# --- Global filters ---
st.subheader("Глобальные фильтры файлов")
col1, col2, col3 = st.columns(3)
with col1:
    noise = st.text_area(
        "Шум",
        value="\n".join(config.get("noise_patterns", [])),
        height=120,
        help="Glob-паттерны файлов, полностью исключённых из анализа "
        "(lock-файлы, сборки, кэши). По одному на строку",
    )
with col2:
    priority = st.text_area(
        "Приоритетные",
        value="\n".join(config.get("priority_patterns", [])),
        height=120,
        help="Файлы, попадающие в diff первыми "
        "(основной код: app/**, lib/**, src/**)",
    )
with col3:
    secondary = st.text_area(
        "Вторичные",
        value="\n".join(config.get("secondary_patterns", [])),
        height=120,
        help="Файлы, попадающие последними, если остался бюджет "
        "(тесты, конфиги, CI)",
    )

# --- LLM Models ---
st.subheader("Модели LLM")
llm_cfg = config.get("llm", {})
STAGE_HELP = {
    "analysis": (
        "Анализ",
        "Технический анализ каждого репозитория. Точность важнее креативности",
    ),
    "post": (
        "Генерация поста",
        "Генерация текста поста. Нужен живой, читаемый текст",
    ),
    "review": (
        "Ревью",
        "Проверка поста на качество. Строгая проверка, минимальная вариативность",
    ),
}

for stage, (label, stage_help) in STAGE_HELP.items():
    st.caption(label)
    mc = llm_cfg.get(stage, {})
    defaults = MODEL_DEFAULTS[stage]
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.text_input(
            "Модель",
            value=mc.get("model", defaults[0]),
            key=f"{stage}_m",
            help=stage_help,
        )
    with col2:
        st.number_input(
            "Temperature",
            value=mc.get("temperature", defaults[1]),
            min_value=0.0,
            max_value=2.0,
            step=0.1,
            key=f"{stage}_t",
            help="0 = детерминированный, 2 = максимально креативный",
        )
    with col3:
        st.number_input(
            "Max tokens",
            value=mc.get("max_tokens", defaults[2]),
            min_value=100,
            max_value=16000,
            step=100,
            key=f"{stage}_k",
            help="Максимальная длина ответа модели",
        )

# --- Save ---
st.divider()
if st.button("Сохранить", type="primary", use_container_width=True):
    errors = []
    if not llm_api_key:
        errors.append("LLM API Key — обязательное поле")
    if not llm_base_url:
        errors.append("LLM Base URL — обязательное поле")
    if not site_name:
        errors.append("Название сайта — обязательное поле")
    if errors:
        for e in errors:
            st.error(e)
    else:
        config["llm_api_key"] = llm_api_key
        config["llm_base_url"] = llm_base_url
        config["git_token"] = git_token
        config["period_days"] = period_days
        config["timezone"] = timezone
        config["max_review_iterations"] = max_review
        config["log_cleanup_enabled"] = log_cleanup
        config["log_retention_days"] = log_retention
        config["noise_patterns"] = _lines_to_list(noise)
        config["priority_patterns"] = _lines_to_list(priority)
        config["secondary_patterns"] = _lines_to_list(secondary)
        config["post"] = {
            "site_name": site_name,
            "site_description": site_desc,
            "language": language,
        }
        config["llm"] = {}
        for stage in STAGE_HELP:
            config["llm"][stage] = {
                "model": st.session_state[f"{stage}_m"],
                "temperature": st.session_state[f"{stage}_t"],
                "max_tokens": st.session_state[f"{stage}_k"],
            }
        _save_yaml(CONFIG_PATH, config)

        mkdocs = _load_yaml(MKDOCS_PATH)
        mkdocs["site_name"] = site_name
        if site_desc:
            mkdocs["site_description"] = site_desc
        elif "site_description" in mkdocs:
            del mkdocs["site_description"]
        _save_yaml(MKDOCS_PATH, mkdocs)

        st.success("Настройки сохранены!")
