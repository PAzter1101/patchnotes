"""Страница управления репозиториями."""

import streamlit as st
import yaml

from scheduler import DATA_DIR

CONFIG_PATH = DATA_DIR / "config.yml"

st.header("Репозитории")


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


def _lines_to_list(text: str) -> list[str]:
    return [line.strip() for line in text.strip().splitlines() if line.strip()]


def _render_repo(repo: dict, idx: int) -> dict | None:
    """Рендерит форму репозитория. Возвращает None если удалён."""
    name = repo.get("name") or repo.get("url", f"repo-{idx}")
    with st.expander(f"**{name}** — {repo.get('url', '')}", expanded=False):
        col1, col2 = st.columns([4, 1])
        with col1:
            url = st.text_input(
                "URL *",
                value=repo.get("url", ""),
                key=f"r{idx}_url",
                help="HTTPS-ссылка на git-репозиторий",
            )
        with col2:
            if st.button("Удалить", key=f"r{idx}_del", type="secondary"):
                return None

        col1, col2, col3 = st.columns(3)
        with col1:
            rname = st.text_input(
                "Имя",
                value=repo.get("name", ""),
                key=f"r{idx}_n",
                help="Отображаемое имя. Если пусто — берётся из URL",
            )
        with col2:
            branch = st.text_input(
                "Ветка", value=repo.get("branch", "main"), key=f"r{idx}_br"
            )
        with col3:
            token = st.text_input(
                "Токен",
                value=repo.get("token", ""),
                type="password",
                key=f"r{idx}_tok",
                help="Персональный токен для этого репозитория. "
                "Перекрывает глобальный Git Token",
            )

        col1, col2 = st.columns(2)
        with col1:
            modes = ["period", "tag"]
            mode_idx = modes.index(repo.get("diff_mode", "period"))
            diff_mode = st.selectbox(
                "Режим diff",
                options=modes,
                index=mode_idx,
                key=f"r{idx}_dm",
                help="period — diff за N дней. "
                "tag — diff между git-тегами (релизами)",
            )
        with col2:
            lookback = st.number_input(
                "Глубина поиска тега (периодов)",
                value=repo.get("tag_lookback_periods", 1),
                min_value=1,
                max_value=10,
                key=f"r{idx}_lb",
                disabled=diff_mode != "tag",
                help="Сколько периодов назад искать базовый тег. "
                "Увеличьте, если между релизами большие паузы",
            )

        col1, col2, col3 = st.columns(3)
        with col1:
            r_noise = st.text_area(
                "Шум",
                value="\n".join(repo.get("noise_patterns", [])),
                height=100,
                key=f"r{idx}_np",
                help="Дополнительные паттерны к глобальным. " "По одному на строку",
            )
        with col2:
            r_prio = st.text_area(
                "Приоритетные",
                value="\n".join(repo.get("priority_patterns", [])),
                height=100,
                key=f"r{idx}_pp",
            )
        with col3:
            r_sec = st.text_area(
                "Вторичные",
                value="\n".join(repo.get("secondary_patterns", [])),
                height=100,
                key=f"r{idx}_sp",
            )

        if not url:
            st.warning("URL — обязательное поле")

        result: dict[str, object] = {
            "url": url,
            "branch": branch,
            "diff_mode": diff_mode,
        }
        if rname:
            result["name"] = rname
        if token:
            result["token"] = token
        if diff_mode == "tag":
            result["tag_lookback_periods"] = lookback
        np = _lines_to_list(r_noise)
        pp = _lines_to_list(r_prio)
        sp = _lines_to_list(r_sec)
        if np:
            result["noise_patterns"] = np
        if pp:
            result["priority_patterns"] = pp
        if sp:
            result["secondary_patterns"] = sp
        return result


config = _load_config()
repos: list[dict] = config.get("repos", [])

updated: list[dict] = []
for i, repo in enumerate(repos):
    result = _render_repo(repo, i)
    if result is not None:
        updated.append(result)

# --- Add new ---
st.divider()
with st.expander("Добавить репозиторий", icon=":material/add:"):
    new_url = st.text_input(
        "URL *", key="new_url", placeholder="https://github.com/..."
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        new_name = st.text_input("Имя", key="new_name")
    with col2:
        new_branch = st.text_input("Ветка", value="main", key="new_branch")
    with col3:
        new_token = st.text_input("Токен", type="password", key="new_token")

    if st.button("Добавить", type="primary"):
        if not new_url:
            st.error("URL — обязательное поле")
        else:
            new_repo: dict[str, object] = {
                "url": new_url,
                "branch": new_branch,
            }
            if new_name:
                new_repo["name"] = new_name
            if new_token:
                new_repo["token"] = new_token
            updated.append(new_repo)
            config["repos"] = updated
            _save_config(config)
            st.success("Репозиторий добавлен!")
            st.rerun()

# --- Save all ---
st.divider()
if st.button("Сохранить изменения", type="primary", use_container_width=True):
    invalid = [r for r in updated if not r.get("url")]
    if invalid:
        st.error("У всех репозиториев должен быть указан URL")
    else:
        config["repos"] = updated
        _save_config(config)
        st.success("Репозитории сохранены!")
