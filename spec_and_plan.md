# Competitive Intelligence Pipeline — Спецификация и план разработки

## 0. Идея проекта

Система принимает URL сайта компании и:
1. извлекает контекст о бизнесе (домен, ЦА, ценностное предложение);
2. находит 3–5 релевантных конкурентов;
3. по запросу пользователя собирает мониторинг-бриф (новости о компании, конкурентах, отрасли).

Запуск — по клику пользователя (polling job), без cron/scheduler на этом этапе.
Хранилище — опционально (как заглушка на будущее, не реализуем логику дедупликации между запусками).

---

## 1. Зафиксированный технологический стек

| Слой | Технология | Почему |
|---|---|---|
| Оркестрация агентов | LangGraph | явный граф узлов, легко тестировать каждый узел изолированно |
| Скрейпинг сайта | crawl4ai (Apache 2.0, self-hosted) | бесплатно, LLM-ready markdown на выходе |
| Веб-поиск | duckduckgo-search (`ddgs`) как основной, интерфейс с возможностью подмены на SearXNG | бесплатно, без ключей |
| LLM | OpenRouter (OpenAI-совместимый API) | один клиент, доступ к бесплатным моделям, лёгкая замена модели |
| Backend | FastAPI (async) | тот же паттерн polling job, что и в референс-проекте |
| Хранилище job'ов | in-memory dict на старте → интерфейс `JobStore`, с возможностью подключить Mongo позже | не усложняем раньше времени |
| Тесты | pytest + pytest-asyncio + responses/respx (мокать HTTP) | детерминированные тесты без реальных сетевых вызовов |

**Принцип:** каждый внешний сервис (scraper, search, LLM) спрятан за собственным Python-интерфейсом (Protocol/ABC). Это даёт возможность:
- писать тесты с моками, не трогая сеть;
- в будущем безболезненно поменять duckduckgo-search на SearXNG или Tavily.

---

## 2. Архитектура пайплайна (граф LangGraph)

```
[URL] 
  → WebsiteScraperNode        (scraper adapter)
  → ContextExtractorNode      (LLM adapter)      → {domain, audience, value_prop, keywords}
  → CompetitorFinderNode      (search + LLM)      → [{name, url, reason}]
  → NewsFetcherNode           (search, fan-out: company + each competitor + industry keywords)
  → CuratorNode               (dedup + relevance filter, чистая логика без сети)
  → BriefingNode              (LLM)               → короткие summary по категориям
  → EditorNode                (LLM)               → финальный структурированный Brief (JSON + markdown)
```

Каждый узел — чистая функция `State -> State` (или async-функция), без побочных эффектов кроме вызовов через переданные адаптеры. Это ключевое требование для тестируемости.

---

## 3. Контракты данных (Pydantic-модели)

Это должно быть реализовано и покрыто тестами **в первую очередь**, до любой бизнес-логики — потому что все узлы графа общаются через эти модели.

```python
# domain/models.py

class CompanyContext(BaseModel):
    source_url: HttpUrl
    domain: str                 # напр. "B2B SaaS для управления проектами"
    target_audience: str
    value_proposition: str
    keywords: list[str]         # для генерации поисковых запросов

class Competitor(BaseModel):
    name: str
    url: HttpUrl | None
    reason: str                 # почему признан конкурентом

class NewsItem(BaseModel):
    title: str
    url: HttpUrl
    source: str
    published_at: datetime | None
    snippet: str
    related_entity: str         # "company" | имя конкурента | "industry"

class MonitoringBrief(BaseModel):
    company: CompanyContext
    competitors: list[Competitor]
    items: list[NewsItem]
    generated_at: datetime
    summary_markdown: str
```

---

## 4. Интерфейсы внешних сервисов (Ports)

```python
# ports/scraper.py
class WebScraper(Protocol):
    async def fetch_markdown(self, url: str) -> ScrapedPage: ...

# ports/search.py
class WebSearch(Protocol):
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]: ...

# ports/llm.py
class LLMClient(Protocol):
    async def complete(self, system: str, user: str, response_model: type[T] | None = None) -> T | str: ...
```

Реализации (`Crawl4AIScraper`, `DuckDuckGoSearch`, `OpenRouterClient`) — отдельные adapter-классы в `adapters/`. Узлы графа зависят только от Protocol, не от конкретных реализаций (Dependency Injection через конструктор графа).

---

## 5. API-контракт (FastAPI)

```
POST /research
  body: { "url": "https://example.com" }
  → { "job_id": "uuid" }

GET /research/{job_id}/status
  → { "status": "pending" | "running" | "done" | "error", "current_step": "scraping" | ... }

GET /research/{job_id}/report
  → MonitoringBrief (если done) | 409 (если ещё не готово)
```

---

## 6. Структура репозитория

```
repo/
├── app/
│   ├── domain/
│   │   └── models.py
│   ├── ports/
│   │   ├── scraper.py
│   │   ├── search.py
│   │   └── llm.py
│   ├── adapters/
│   │   ├── crawl4ai_scraper.py
│   │   ├── duckduckgo_search.py
│   │   ├── searxng_search.py       # альтернативная реализация того же порта
│   │   └── openrouter_llm.py
│   ├── graph/
│   │   ├── nodes/
│   │   │   ├── website_scraper.py
│   │   │   ├── context_extractor.py
│   │   │   ├── competitor_finder.py
│   │   │   ├── news_fetcher.py
│   │   │   ├── curator.py
│   │   │   ├── briefing.py
│   │   │   └── editor.py
│   │   └── build_graph.py
│   ├── jobs/
│   │   └── job_store.py            # in-memory, интерфейс под будущий Mongo
│   └── api/
│       └── main.py                 # FastAPI роуты
├── tests/
│   ├── unit/                       # тесты узлов и адаптеров с моками
│   ├── integration/                # тест графа целиком с фейковыми адаптерами
│   └── contract/                   # тесты Pydantic-моделей (валидация, edge cases)
├── pyproject.toml
├── README.md
└── .github/workflows/ci.yml
```

---

## 7. План разработки (по фазам, TDD)

Каждая фаза = отдельный тикет/промпт для кодинг-агента. Порядок важен: сначала контракты и тесты, потом реализация, потом рефакторинг.

### Фаза 0 — Инициализация репозитория
**Цель:** пустой, но полностью настроенный проект.
- Инициализировать git, `pyproject.toml` (poetry/uv), Python 3.11+.
- Настроить `pytest`, `pytest-asyncio`, `ruff` (lint), `mypy` (типы).
- Настроить `.github/workflows/ci.yml`: запуск lint + mypy + pytest на каждый push/PR.
- README с описанием архитектуры (можно взять из этого документа).
- **Definition of Done:** `pytest` запускается и проходит (пусть даже без единого теста), CI зелёный на пустом коммите.

### Фаза 1 — Domain-модели
**Цель:** зафиксировать контракты данных.
- Сначала пишем тесты в `tests/contract/test_models.py`: валидные/невалидные данные, обязательные поля, сериализация в JSON.
- Затем реализуем `domain/models.py`, пока тесты не пройдут.
- **DoD:** все модели из раздела 3 реализованы, 100% покрытие тестами базовых сценариев валидации.

### Фаза 2 — Порты и фейковые адаптеры для тестов
**Цель:** зафиксировать интерфейсы, до реальных внешних вызовов.
- Определить `Protocol`-классы (раздел 4).
- Написать `FakeScraper`, `FakeSearch`, `FakeLLM` в `tests/fakes/` — они возвращают заранее заданные данные, без сети. Это позволит тестировать граф ещё до готовности реальных адаптеров.
- **DoD:** фейки реализуют протоколы (проверяется через `isinstance`/структурные тесты), используются в тестах фазы 3.

### Фаза 3 — Узлы графа (по одному, TDD)
Для **каждого** узла отдельно:
1. Пишем unit-тест узла с фейковым адаптером (например: `ContextExtractorNode` получает markdown → возвращает корректный `CompanyContext`, с моком LLM, который отвечает заранее заданным JSON).
2. Реализуем узел, пока тест не пройдёт.
3. Добавляем edge-case тесты (пустой контент, LLM вернул невалидный JSON, сайт вернул 403 и т.п.) и обрабатываем их в коде.

Порядок узлов: `website_scraper` → `context_extractor` → `competitor_finder` → `news_fetcher` → `curator` → `briefing` → `editor`.

**DoD по каждому узлу:** тест "happy path" + минимум 2 edge-case теста проходят.

### Фаза 4 — Сборка графа (integration-тест)
**Цель:** проверить, что узлы правильно передают данные друг другу.
- `tests/integration/test_graph_e2e.py`: собираем граф с фейковыми адаптерами, гоняем от URL до готового `MonitoringBrief`, проверяем структуру результата.
- **DoD:** полный прогон графа на фейках проходит детерминированно.

### Фаза 5 — Реальные адаптеры
Для **каждого** адаптера отдельно (crawl4ai, duckduckgo-search, openrouter):
1. Пишем тест с замоканным HTTP-слоем (`respx`/`responses`), проверяем, что адаптер правильно формирует запрос и парсит ответ в наши модели (`ScrapedPage`, `SearchResult`).
2. Реализуем адаптер.
3. Отдельно — **ручной smoke-тест** (не в CI, в `scripts/smoke_test.py`) с реальным сайтом/реальным API — чтобы убедиться, что интеграция реально работает, но не гонять его в CI (нестабильно, зависит от сети).

**DoD:** мок-тесты в CI зелёные; smoke-тест руками пройден хотя бы раз.

### Фаза 6 — API-слой (FastAPI)
- Тесты на `TestClient` из FastAPI: `POST /research` → job_id, `GET /research/{id}/status` меняется по мере выполнения, `GET /research/{id}/report` отдаёт корректный JSON.
- Job выполняется в background task, граф собирается с реальными адаптерами (через DI/factory).
- **DoD:** интеграционные тесты API проходят с реальным графом, но с замоканными внешними сервисами (переиспользуем моки из фазы 5).

### Фаза 7 — Устойчивость и production-hardening
- Таймауты и retries на всех внешних вызовах (scraper, search, LLM) — с тестами на то, что retry действительно срабатывает и что после N попыток система деградирует gracefully (например, узел `website_scraper` при неудаче возвращает пустой контекст с флагом `scrape_failed=True`, а не роняет весь пайплайн).
- Rate-limit защита для DuckDuckGo (у него нет официального API — учащённые запросы = бан).
- Логирование (structured logging, напр. `structlog`) на каждом узле: вход/выход/ошибка.
- **DoD:** тесты на таймаут/ошибку внешнего сервиса → пайплайн не падает целиком, возвращает частичный результат с пометкой о проблеме.

### Фаза 8 — Документация и финальная приёмка
- README: как запустить, какие env-переменные нужны (`OPENROUTER_API_KEY` и т.д.), архитектурная диаграмма.
- Проверка полного покрытия тестами (`pytest --cov`, цель — не ниже 80% на `domain/` и `graph/`).
- Финальный ручной прогон: реальный URL → реальный бриф.

---

## 8. Стратегия тестирования (сводно)

| Тип теста | Что проверяет | Внешние вызовы |
|---|---|---|
| `tests/contract/` | Валидность Pydantic-моделей | нет |
| `tests/unit/` (узлы) | Логика одного узла | нет (фейки) |
| `tests/unit/` (адаптеры) | Парсинг реального API-ответа | нет (замокан HTTP) |
| `tests/integration/` | Граф целиком, API endpoints | нет (фейки/моки) |
| `scripts/smoke_test.py` | Реальная интеграция | да, вручную, не в CI |

Правило: **в CI никогда не должно быть реальных сетевых вызовов** — иначе тесты станут нестабильными (flaky) и будут ломаться не из-за багов в коде, а из-за состояния внешнего сайта/API.

---

## 9. Чек-лист "production-grade / maintainable"

- [ ] Типизация везде (`mypy --strict` на `domain/` и `ports/`)
- [ ] Все внешние вызовы — через порты/адаптеры, никаких прямых `httpx.get()` внутри узлов графа
- [ ] Timeout + retry на каждом внешнем вызове
- [ ] Graceful degradation при отказе одного из источников (не роняем весь пайплайн)
- [ ] Структурированное логирование
- [ ] CI: lint + типы + тесты на каждый PR
- [ ] Покрытие тестами ≥ 80% на domain/graph слоях
- [ ] README с инструкцией по запуску и архитектурной схемой
- [ ] Секреты только через env-переменные, не в коде

---

## 10. Как использовать этот документ с кодинг-агентом

Рекомендуемый порядок промптов агенту — **по одной фазе за раз**, не всё сразу:
1. Дать агенту Фазу 0 → проверить, что репозиторий и CI действительно работают.
2. Дать Фазу 1 → проверить тесты моделей.
3. Дать Фазу 2 → проверить, что фейки реализуют протоколы.
4. Дальше — по одному узлу из Фазы 3 за раз (не весь граф сразу), с явным указанием "сначала напиши тест, покажи его мне, потом реализацию".
5. Fazы 4–8 — аналогично, по готовности предыдущей.

Так вы контролируете качество на каждом шаге и не получите "стену кода", которую сложно ревьюить.
