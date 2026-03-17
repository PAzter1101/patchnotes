# patchnotes

Автоматически генерирует человекочитаемые посты из git diff нескольких репозиториев с помощью LLM и публикует их через MkDocs Material + RSS.

## Как работает

```
git репозитории → net diff → фильтрация шума → анализ LLM (по репозиторию) → генерация поста → MkDocs .md
```

1. Клонирует каждый репозиторий и собирает `git diff` за настроенный период
2. Фильтрует шум: lock-файлы, миграции, автогенерированный код, бинарники
3. Приоритизирует файлы по паттернам из конфига; большие файлы суммаризирует отдельно
4. Отправляет технический саммари каждого репозитория в LLM
5. Генерирует единый человекочитаемый пост из всех саммари
6. Записывает `.md` файл готовый для блога [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)

Итоговый пост предназначен для пользователей — без технического жаргона, только что нового.

## Структура

```
patchnotes/
├── app/
│   ├── main.py          # точка входа
│   ├── config.py        # загрузка конфигурации
│   ├── git_diff.py      # клонирование и анализ diff
│   ├── llm.py           # запросы к LLM
│   └── post_builder.py  # генерация .md файла
├── prompts/
│   ├── analyze_repo.txt     # промпт для анализа репозитория
│   ├── summarize_file.txt   # промпт для суммаризации большого файла
│   └── generate_post.txt    # промпт для генерации поста
├── config.example.yml   # пример конфигурации
├── Dockerfile
└── requirements.txt
```

## Быстрый старт

1. Скопируйте и заполните конфиг:

```bash
cp config.example.yml config.yml
```

2. Запустите:

```bash
docker run --rm \
  -e LLM_API_KEY=your-api-key \
  -e OUTPUT_DIR=/output \
  -v ./config.yml:/config.yml \
  -v ./prompts:/prompts \
  -v ./output:/output \
  ghcr.io/your-org/patchnotes
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | Дефолт |
|---|---|---|
| `LLM_API_KEY` | API ключ LLM провайдера | — |
| `LLM_BASE_URL` | Base URL OpenAI-совместимого API | `https://openrouter.ai/api/v1` |
| `GIT_TOKEN` | GitHub/GitLab токен для приватных репозиториев | — |
| `CONFIG_PATH` | Путь к файлу конфигурации | `/config.yml` |
| `OUTPUT_DIR` | Куда записывать сгенерированный `.md` файл | `/output` |
| `PROMPTS_DIR` | Путь к директории с промптами | `/prompts` |

Через `LLM_BASE_URL` можно подключить любой OpenAI-совместимый провайдер: [OpenRouter](https://openrouter.ai), [Ollama](https://ollama.com), Together AI, Groq и другие.

### config.yml

Репозитории, паттерны фильтрации, модели и настройки поста задаются в `config.yml`. Смотрите [`config.example.yml`](config.example.yml) как отправную точку.

Ключевые параметры:

```yaml
period_days: 7              # период анализа в днях

repos:
  - url: https://github.com/your-org/repo.git
    name: Название
    branch: main

llm:
  analysis_model: google/gemini-3.1-flash-lite-preview
  post_model: nvidia/nemotron-3-super-120b-a12b:free

post:
  site_name: My Project
  language: ru              # язык генерируемого поста
```

### Промпты

Промпты хранятся в директории `prompts/` и монтируются в контейнер. Вы можете изменять их без пересборки образа.

Доступные переменные в промптах:

| Файл | Переменные |
|---|---|
| `analyze_repo.txt` | `{period_days}`, `{language}` |
| `summarize_file.txt` | `{language}` |
| `generate_post.txt` | `{site_name}`, `{period_days}`, `{language}` |

## Результат

Каждый запуск создаёт один `.md` файл, например `2026-03-17.md`:

```markdown
---
date: 2026-03-17
---

Что нового на этой неделе...
```

## Настройка MkDocs

Добавьте в `mkdocs.yml`:

```yaml
plugins:
  - blog
  - rss:
      match_path: blog/posts/.*
```

Установите зависимости:

```bash
pip install mkdocs-material mkdocs-rss-plugin
```

## Модели

По умолчанию используются бесплатные модели через [OpenRouter](https://openrouter.ai):

- **Анализ**: `google/gemini-3.1-flash-lite-preview` — 1M контекст, отлично понимает код
- **Пост**: `nvidia/nemotron-3-super-120b-a12b:free` — 120B параметров, качественный текст

Актуальный список бесплатных моделей: [openrouter.ai/models](https://openrouter.ai/models?supported_parameters=free)

## Лицензия

MIT
