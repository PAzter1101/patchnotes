# patchnotes

Автоматически генерирует человекочитаемые посты об изменениях из git diff нескольких репозиториев с помощью LLM и публикует их через MkDocs Material + RSS.

## Как работает

```
git репозитории → git diff → фильтрация шума → анализ LLM (по репозиторию)
  → синтез фич → генерация поста → ревью поста → MkDocs .md
```

1. Клонирует каждый репозиторий параллельно и собирает `git diff` за настроенный период
2. Фильтрует шум: lock-файлы, миграции, автогенерированный код
3. Приоритизирует файлы по паттернам из конфига (глобальные + per-repo); большие файлы суммаризирует отдельно
4. Анализирует каждый репозиторий технически (LLM)
5. Синтезирует связанные изменения из разных репозиториев в логические цепочки
6. Генерирует пост в нужном стиле — задаётся через промпт и настройки в конфиге
7. Ревьювер проверяет пост и при необходимости отправляет на доработку (до `max_review_iterations` раз)
8. Публикует `.md` файл в блог MkDocs Material

## Компоненты

```
┌──────────────────────────────────────────┐
│            Shared PVC (данные)            │
│  config.yml   output/   posts/           │
└──────────────────────────────────────────┘
         │                       │
┌────────┴──────────┐   ┌───────┴──────┐
│  Admin (Streamlit)│   │  MkDocs      │
│                   │   │  (Material)  │
│  Веб-интерфейс    │   │              │
│  Планировщик      │   │  Блог + RSS  │
│  Генератор        │   │              │
└───────────────────┘   └──────────────┘
```

| Компонент | Образ | Описание |
|---|---|---|
| **Admin** | `patchnotes-admin` | Streamlit-панель: генерация, редактирование постов/конфига, расписание, логи |
| **MkDocs** | `patchnotes-mkdocs` | Блог на MkDocs Material с RSS |

## Структура

```
patchnotes/
├── app/                    # генератор постов
│   ├── main.py             # точка входа
│   ├── config.py           # загрузка конфигурации
│   ├── git_diff.py         # клонирование и анализ diff
│   ├── llm.py              # запросы к LLM
│   └── post_builder.py     # генерация .md файла
├── admin/                  # веб-интерфейс (Streamlit)
│   ├── admin_app.py        # точка входа
│   ├── scheduler.py        # APScheduler планировщик
│   ├── Dockerfile
│   └── pages/              # страницы UI
├── mkdocs/                 # блог
│   ├── mkdocs.yml          # конфигурация MkDocs
│   ├── Dockerfile
│   └── docs/               # контент
├── .helm/                  # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── prompts/                # промпты для LLM
└── config.example.yml      # пример конфигурации
```

## Быстрый старт

### Деплой в Kubernetes (Helm)

```bash
helm install patchnotes oci://ghcr.io/pazter1101/charts/patchnotes \
  --set secrets.llmApiKey=sk-or-v1-... \
  --set secrets.gitToken=glpat-... \
  --set admin.ingress.enabled=true \
  --set admin.ingress.host=admin.patchnotes.example.com \
  --set mkdocs.ingress.enabled=true \
  --set mkdocs.ingress.host=patchnotes.example.com
```

Или с файлом значений:

```bash
helm install patchnotes oci://ghcr.io/pazter1101/charts/patchnotes -f values-prod.yaml
```

### Запуск локально (Python)

```bash
pip install -r requirements.txt
CONFIG_PATH=config.yml OUTPUT_DIR=output PROMPTS_DIR=prompts python app/main.py
```

### Запуск через Docker

```bash
docker run --rm \
  -v ./config.yml:/data/config.yml:ro \
  -v ./prompts:/app/prompts:ro \
  -v ./output:/data/output \
  ghcr.io/pazter1101/patchnotes-admin
```

Результат появится в `output/{дата}/`.

## Конфигурация

### config.yml

Все настройки — в одном файле. Полный пример: [`config.example.yml`](config.example.yml).

```yaml
llm_api_key: sk-or-v1-...
llm_base_url: https://openrouter.ai/api/v1

timezone: Europe/Moscow         # часовой пояс для даты в имени файла
period_days: 7                  # период анализа в днях
max_review_iterations: 3        # сколько раз пробовать переписать пост

repos:
  - url: https://github.com/your-org/repo.git
    name: backend
    branch: main
    token: ghp-xxx              # токен для приватного репозитория
    diff_mode: period           # "period" — по дням | "tag" — по тегам
    noise_patterns:             # дополнительные исключения (к глобальным)
      - "__pycache__/"
      - "*.pyc"

  - url: https://github.com/your-org/mobile.git
    name: mobile
    branch: main
    diff_mode: tag
    tag_lookback_periods: 3     # глубина поиска базового тега (в периодах)
    noise_patterns:
      - "*.g.dart"
      - "*.freezed.dart"

llm:
  analysis:
    model: nvidia/nemotron-3-super-120b-a12b:free
    temperature: 0.2
    max_tokens: 4000
  post:
    model: arcee-ai/trinity-large-preview:free
    temperature: 0.7
    max_tokens: 1500
  review:
    model: arcee-ai/trinity-large-preview:free
    temperature: 0.2
    max_tokens: 500

post:
  site_name: My Project
  language: ru
```

Через `llm_base_url` можно подключить любой OpenAI-совместимый провайдер: [OpenRouter](https://openrouter.ai), [Ollama](https://ollama.com), Together AI, Groq и другие.

### Фильтры файлов

Паттерны фильтрации задаются на двух уровнях — глобально и per-repo. Паттерны репозитория **добавляются** к глобальным:

| Уровень | Описание |
|---|---|
| `noise_patterns` | Полностью игнорируются (lock-файлы, сборки, кэши) |
| `priority_patterns` | Попадают в diff первыми (`app/**`, `lib/**`, `src/**`) |
| `secondary_patterns` | Попадают последними, если остался бюджет (тесты, конфиги) |

### Режимы diff

| `diff_mode` | Поведение |
|---|---|
| `period` | Диф за последние `period_days` дней. Подходит для репозиториев без тегов. |
| `tag` | Диф между тегами. Target — последний тег в текущем периоде (нет тега = репозиторий пропускается). Base определяется каскадно (см. ниже). |

**Каскад поиска базового тега** (`diff_mode: tag`):

1. Последний тег в прошлом периоде `[period, 2×period]`
2. Последний тег в расширенном окне `[2×period, (1+lookback)×period]`
3. Самый старый коммит в окне `[period, (1+lookback)×period]`
4. Последний коммит до начала окна

`tag_lookback_periods` (по умолчанию `1`) управляет глубиной поиска. Увеличьте значение, если между релизами бывают долгие периоды без тегов.

### Переменные окружения

Env переменные перекрывают значения из `config.yml`. Удобны для CI/CD и секретов:

| Переменная | Описание |
|---|---|
| `LLM_API_KEY` | API ключ LLM провайдера |
| `LLM_BASE_URL` | Base URL OpenAI-совместимого API |
| `GIT_TOKEN` | Глобальный токен для репозиториев (если не указан per-repo) |
| `CONFIG_PATH` | Путь к файлу конфигурации (дефолт: `/data/config.yml`) |
| `OUTPUT_DIR` | Куда записывать результаты (дефолт: `/data/output`) |
| `PROMPTS_DIR` | Путь к директории с промптами (дефолт: `/app/prompts`) |
| `LOG_LEVEL` | Уровень логирования: `DEBUG`, `INFO`, `WARNING` (дефолт: `INFO`) |

### Токены для приватных репозиториев

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

## Helm chart

### Установка

```bash
helm install patchnotes oci://ghcr.io/pazter1101/charts/patchnotes \
  --set secrets.llmApiKey=sk-or-v1-... \
  --set secrets.gitToken=glpat-...
```

### Основные параметры values.yaml

| Параметр | Описание | По умолчанию |
|---|---|---|
| `admin.ingress.enabled` | Включить Ingress для админки | `false` |
| `admin.ingress.host` | Домен админки | `admin.patchnotes.example.com` |
| `mkdocs.ingress.enabled` | Включить Ingress для блога | `false` |
| `mkdocs.ingress.host` | Домен блога | `patchnotes.example.com` |
| `storage.size` | Размер PVC | `1Gi` |
| `storage.storageClassName` | StorageClass (пусто = default) | `""` |
| `storage.accessMode` | Режим доступа PVC | `ReadWriteMany` |
| `secrets.llmApiKey` | API ключ LLM | `""` |
| `secrets.gitToken` | Глобальный git-токен | `""` |
| `admin.auth.username` | Логин для basic auth админки | `admin` |
| `admin.auth.password` | Пароль для basic auth (пусто = без защиты) | `""` |

### Веб-интерфейс (Admin)

Streamlit-панель управления доступна по адресу Ingress `admin.ingress.host`:

- **Генерация** — ручной запуск генерации постов
- **Посты** — просмотр, редактирование и публикация постов
- **Генератор** — редактирование `config.yml`
- **Блог** — редактирование `mkdocs.yml` (название сайта, тема, плагины)
- **Расписание** — настройка автоматической генерации (cron)
- **Логи** — просмотр логов генерации

## Промпты

Промпты в `prompts/` можно изменять без пересборки образа. Доступные переменные:

| Файл | Переменные |
|---|---|
| `analyze_repo.txt` | `{period_days}` |
| `summarize_file.txt` | — |
| `synthesize.txt` | `{period_days}`, `{language}` |
| `generate_post.txt` | `{site_name}`, `{period_days}`, `{language}`, `{feedback_section}` |
| `review_post.txt` | `{language}` |

## Результат

Каждый запуск создаёт поддиректорию `output/{дата}/`:

| Файл | Содержимое |
|---|---|
| `{дата}.md` | Готовый пост для MkDocs |
| `2_synthesis.txt` | Синтезированные фич-цепочки |
| `3_post_raw.txt` | Сырой ответ LLM до парсинга |
| `1_{repo}_analysis.txt` | Технический анализ каждого репозитория |

## Модели

По умолчанию используются бесплатные модели через [OpenRouter](https://openrouter.ai):

- **Анализ / синтез**: `nvidia/nemotron-3-super-120b-a12b:free`
- **Пост / ревью**: `arcee-ai/trinity-large-preview:free`

Актуальный список бесплатных моделей: [openrouter.ai/models](https://openrouter.ai/models?supported_parameters=free)

## Кастомизация стиля

Стиль и тон поста полностью определяются промптами. Отредактируйте `prompts/generate_post.txt` под свой проект — технический блог, продуктовый changelog, новостная рассылка или любой другой формат.

## Лицензия

MIT
