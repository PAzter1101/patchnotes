# patchnotes

Автоматически генерирует человекочитаемые посты об изменениях из git diff нескольких репозиториев с помощью LLM и публикует их через MkDocs Material + RSS.

## Как работает

```
git репозитории → net diff → фильтрация шума → анализ LLM (по репозиторию)
  → синтез фич → генерация поста → ревью поста → MkDocs .md
```

1. Клонирует каждый репозиторий параллельно и собирает `git diff` за настроенный период
2. Фильтрует шум: lock-файлы, миграции, автогенерированный код
3. Приоритизирует файлы по паттернам из конфига; большие файлы суммаризирует отдельно
4. Анализирует каждый репозиторий технически (LLM)
5. Синтезирует связанные изменения из разных репозиториев в логические цепочки
6. Генерирует пост в нужном стиле — задаётся через промпт и настройки в конфиге
7. Ревьювер проверяет пост и при необходимости отправляет на доработку (до `max_review_iterations` раз)
8. Записывает `.md` файл готовый для блога [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)

## Структура

```
patchnotes/
├── app/
│   ├── main.py              # точка входа
│   ├── config.py            # загрузка конфигурации
│   ├── git_diff.py          # клонирование и анализ diff
│   ├── llm.py               # запросы к LLM
│   └── post_builder.py      # генерация .md файла
├── prompts/
│   ├── analyze_repo.txt     # анализ одного репозитория
│   ├── summarize_file.txt   # суммаризация большого файла
│   ├── synthesize.txt       # синтез фич из нескольких репозиториев
│   ├── generate_post.txt    # генерация поста
│   └── review_post.txt      # ревью и gate-проверка поста
├── config.example.yml       # пример конфигурации
├── Dockerfile
└── requirements.txt
```

## Быстрый старт

1. Скопируйте и заполните конфиг:

```bash
cp config.example.yml config.yml
# Укажите repos, llm_api_key, llm_base_url, llm.analysis_model, llm.post_model
```

2. Запуск локально (Python):

```bash
pip install -r requirements.txt
CONFIG_PATH=config.yml OUTPUT_DIR=output PROMPTS_DIR=prompts python app/main.py
```

3. Запуск через Docker:

```bash
docker run --rm \
  -v ./config.yml:/config.yml:ro \
  -v ./prompts:/prompts:ro \
  -v ./output:/output \
  ghcr.io/your-org/patchnotes
```

Результат появится в директории `output/`.

## Конфигурация

### config.yml

Все настройки — в одном файле. Смотрите [`config.example.yml`](config.example.yml).

```yaml
llm_api_key: sk-or-v1-...           # API ключ LLM провайдера
llm_base_url: https://openrouter.ai/api/v1  # OpenAI-совместимый эндпоинт

period_days: 7                      # период анализа в днях
max_review_iterations: 3            # сколько раз пробовать переписать пост

repos:
  - url: https://github.com/your-org/repo.git
    name: backend
    branch: main
    token: ghp-xxx                  # токен для приватного репозитория

llm:
  analysis_model: deepseek/deepseek-chat-v3-0324:free
  post_model: meta-llama/llama-4-maverick:free

post:
  site_name: My Project
  language: ru                      # язык генерируемого поста
```

Через `llm_base_url` можно подключить любой OpenAI-совместимый провайдер: [OpenRouter](https://openrouter.ai), [Ollama](https://ollama.com), Together AI, Groq и другие.

### Переменные окружения

Env переменные перекрывают значения из `config.yml`. Удобны для CI/CD и секретов:

| Переменная | Описание |
|---|---|
| `LLM_API_KEY` | API ключ LLM провайдера |
| `LLM_BASE_URL` | Base URL OpenAI-совместимого API |
| `GIT_TOKEN` | Глобальный токен для репозиториев (если не указан per-repo) |
| `CONFIG_PATH` | Путь к файлу конфигурации (дефолт: `/config.yml`) |
| `OUTPUT_DIR` | Куда записывать `.md` файл (дефолт: `/output`) |
| `PROMPTS_DIR` | Путь к директории с промптами (дефолт: `/prompts`) |
| `LOG_LEVEL` | Уровень логирования: `DEBUG`, `INFO`, `WARNING` (дефолт: `INFO`) |

### Токены для приватных репозиториев

Каждый репозиторий может иметь свой токен:

```yaml
repos:
  - url: https://github.com/org/repo.git
    token: ghp-xxx        # GitHub Personal Access Token
  - url: https://gitlab.com/org/repo.git
    token: glpat-yyy      # GitLab Personal Access Token
```

**Необходимые права:**

| Сервис | Тип токена | Права |
|---|---|---|
| GitHub | Personal Access Token (classic) | `repo` → `read:repo` |
| GitHub | Fine-grained | `Contents: Read` |
| GitLab | Personal / Project Access Token | `read_repository` |
| Bitbucket | Repository Access Token | `Repositories: Read` |

### Промпты

Промпты в `prompts/` можно изменять без пересборки образа. Доступные переменные:

| Файл | Переменные |
|---|---|
| `analyze_repo.txt` | `{period_days}`, `{language}` |
| `summarize_file.txt` | `{language}` |
| `synthesize.txt` | `{period_days}`, `{language}` |
| `generate_post.txt` | `{site_name}`, `{period_days}`, `{language}` |
| `review_post.txt` | `{language}` |

## Результат

Каждый запуск создаёт несколько файлов в `output/`:

| Файл | Содержимое |
|---|---|
| `2026-03-17.md` | Готовый пост для MkDocs |
| `2026-03-17_synthesis.txt` | Синтезированные фич-цепочки |
| `2026-03-17_post_raw.txt` | Сырой ответ LLM до ревью |
| `2026-03-17_{repo}_analysis.txt` | Технический анализ каждого репозитория |

Формат `.md` совместим с [MkDocs Material Blog](https://squidfunk.github.io/mkdocs-material/plugins/blog/).

## Настройка MkDocs

```yaml
plugins:
  - blog
  - rss:
      match_path: blog/posts/.*
```

```bash
pip install mkdocs-material mkdocs-rss-plugin
```

## Модели

По умолчанию используются бесплатные модели через [OpenRouter](https://openrouter.ai):

- **Анализ / синтез**: `deepseek/deepseek-chat-v3-0324:free`
- **Пост / ревью**: `meta-llama/llama-4-maverick:free`

Актуальный список бесплатных моделей: [openrouter.ai/models](https://openrouter.ai/models?supported_parameters=free)

## Кастомизация стиля

Стиль и тон поста полностью определяются промптами. Отредактируйте `prompts/generate_post.txt` под свой проект — технический блог, продуктовый changelog, новостная рассылка или любой другой формат. Промпты монтируются в контейнер и не требуют пересборки образа.

## Лицензия

MIT
