# SCADA.AI v3.2.9.1 — Полный контекст для разработки

**Версия**: 3.2.9.1
**Дата последнего обновления**: 2026-07-08
**Разработчик**: Усков Сергей Евгеньевич
**Назначение**: AI-ассистент для оператора SCADA-системы промышленного здания

---

## 📋 Оглавление

1. [Обзор системы](#обзор-системы)
2. [Архитектура](#архитектура)
3. [Структура файлов](#структура-файлов)
4. [Backend детали](#backend-детали)
5. [Frontend детали](#frontend-детали)
6. [Модули](#модули)
7. [API Endpoints](#api-endpoints)
8. [База данных](#база-данных)
9. [Конфигурация](#конфигурация)
10. [Математика и алгоритмы](#математика-и-алгоритмы)
11. [Примеры кода](#примеры-кода)
12. [Известные проблемы](#известные-проблемы)

---

## Обзор системы

SCADA.AI — это модульная система AI-ассистента для оператора SCADA-системы промышленного здания. Система анализирует исторические данные из базы PostgreSQL (TimescaleDB), предоставляет детерминированные отчёты о здоровье системы, выполняет глубокий анализ данных (DDA) с детекцией аномалий, сезонных паттернов и A/B сравнениями, а также позволяет задавать вопросы на естественном языке.

### Ключевые возможности

#### 🏥 Мониторинг здоровья системы
- **Индекс здоровья системы** — композитная оценка состояния (0-100) с детализацией расчёта
- **Индекс жизнеобеспечения** — параметры среды (CO2, температура, влажность, давление, VOC)
- **Журнал аварий** — приоритеты HIGH/MEDIUM/LOW с детализацией и drilldown
- **Детекция битых/офлайн/дребезжащих/залипших датчиков** — автоматическая диагностика оборудования

#### 📊 Глубокий анализ данных (Deep Data Analysis — DDA)
- **Детекция аномалий** — три алгоритма (Isolation Forest, Z-score, IQR) с типизацией (spike/dip/drift/noise)
- **Сезонный анализ (FFT)** — автодетект доминирующих периодов через Fast Fourier Transform
- **Типичные паттерны** — извлечение суточных/недельных профилей поведения
- **Корреляционный анализ** — Pearson correlation matrix для multi-tag сравнений
- **Scatter plots** — визуализация попарных зависимостей с линией регрессии
- **Тепловая карта корреляций** — интерактивная визуализация связей между параметрами
- **A/B анализ** — статистическое сравнение двух периодов или оборудования (Welch's t-test, Cohen's d)

#### 📈 Аналитика и прогнозы
- **Тренд-анализ** — линейная регрессия с slope_per_day и R²
- **Прогнозирование** — экстраполяция трендов на 7/30/90/365 дней
- **Корреляции параметров** — Pearson + временной лаг ±24 часа между метриками
- **Impact Score** — ранжирование проблем по комплексной оценке

#### ⚡ Энергоучёт
- **Расчёт стоимости ресурсов** — электричество, вода, тепло (текущий и прошлый месяц)
- **Интервальные тарифы** — автоматический выбор тарифа по дате
- **Интеграция с ЛЭРС** — consumption через теги счётчиков

#### 🤖 AI-функции
- **Системные логи** — AI-анализ через tool calling (YandexGPT 5.1)
- **Естественный язык** — задавайте вопросы о системе в чате
- **LLM-интерпретация** — человекочитаемые отчёты по результатам DDA
- **Tool calling** — вызов функций анализа из диалога

#### 🎛️ Конфигуратор
- **Управление модулями** — включение/выключение функциональности
- **Настройка тарифов** — CRUD интервальных тарифов с валидацией дат
- **Конфигурация тегов** — привязка счётчиков к ресурсам
- **Настройки DDA** — параметры детекции, downsampling, корреляций
- **Документация** — встроенный DocsViewer с Markdown рендерингом

---

## Архитектура

### Общая схема потока данных

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (Svelte 5)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐     │
│  │ Home.svelte  │  │ Config.svelte│  │ SystemLogsPanel  │     │
│  └──────────────┘  └──────────────┘  └──────────────────┘     │
│           │                  │                     │           │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              Deep Analysis Components                  │   │
│  │  DeepAnalysisControls  │  ABComparisonModal  │         │   │
│  │  DeepAnalysisResults   │  ChartModal        │         │   │
│  │  DDAInterpretation                              │         │   │
│  └────────────────────────────────────────────────────────┘   │
│           │                                                    │
│           └──────────────────┴────────────────────┘            │
│                              │                                 │
│                     POST /chat                                  │
│                    GET /health/*                                │
│                    GET /system/info                             │
│              POST /api/v1/deep_analysis/analyze                 │
│              POST /api/v1/deep_analysis/ab                      │
│              GET  /api/v1/deep_analysis/tags                    │
└──── ──────────────────────────┼─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                         │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routers                           │  │
│  │  /chat  /health  /system  /config  /logs                 │  │
│  │  /api/v1/deep_analysis  /analytics  /energy  /docs       │  │
│  └──────────────────────────────────────────────────────────┘  │
│           │                                                    │
│           ▼                                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Module Registry (auto-discovery)          │    │
│  │  modules/health      modules/hello    modules/logs     │    │
│  │  modules/analytics   modules/energy_* modules/deep_*   │    │
│  └────────────────────────────────────────────────────────┘    │
│           │                                                    │
│           ▼                                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Tool Executor (dispatch)                  │    │
│  │  analyze_logs()  get_health_report()                   │    │
│  │  calculate_electricity_cost()                          │    │
│  └────────────────────────────────────────────────────────┘    │
│           │                                                    │
│           ▼                                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              LLM Provider (YandexGPT 5.1)              │    │
│  │  generate()  generate_with_tools()                     │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────────┼─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                   PostgreSQL (SCADA DB)                        │
│  tags_value  alarm_events_history  tags_dict  zones_dict       │
│  anomaly_events (deep_analysis)                                │
└────────────────────────────────────────────────────────────────┘
```

### Технологический стек

#### Backend
- **FastAPI** + **asyncpg** (PostgreSQL / TimescaleDB)
- **YandexGPT 5.1** (tool calling, function calls)
- **scipy** (статистика: Welch's t-test, FFT, корреляции)
- **numpy** (числовые вычисления, линейная алгебра)
- **scikit-learn** (Isolation Forest для детекции аномалий)
- **structlog** (структурированное логирование)
- **pydantic-settings** (конфигурация из .env)
- **pyyaml** (конфигурация модулей)

#### Frontend
- **Svelte 5** + runes (reactive state management)
- **Tailwind CSS** (utility-first styling)
- **Chart.js** + **chartjs-plugin-zoom** (интерактивные графики)
- **svelte-chartjs** (Chart.js wrapper)
- **ky** (HTTP client)
- **lucide-svelte** (иконки)
- **marked** (Markdown рендеринг)
- **svelte-routing** (роутинг)

#### База данных
- **PostgreSQL** + **TimescaleDB** (time-series данные)
- Таблицы: `tags_value`, `alarm_events_history`, `anomaly_events`

---

## Структура файлов

### Корневая структура

```
/workspace/
├── backend/                    # Backend код (FastAPI)
│   ├── main.py                 # Точка входа FastAPI приложения
│   ├── api/
│   │   └── routes/
│   │       ├── chat.py         # POST /chat (главный endpoint)
│   │       ├── health.py       # GET /health/* (metrics, alarms, environmental)
│   │       ├── system.py       # GET /system/info
│   │       ├── config.py       # CRUD модулей и промптов
│   │       ├── docs.py         # GET /docs/* (whitelist MD файлов)
│   │       ├── analytics.py    # GET /analytics/report
│   │       ├── energy.py       # GET /energy/*
│   │       └── deep_analysis.py # POST /api/v1/deep_analysis/*
│   ├── core/
│   │   ├── module_registry.py  # Автообнаружение модулей
│   │   ├── tool_executor.py    # Dispatch tool calls
│   │   ├── db.py               # asyncpg pool
│   │   ├── logger.py           # Файловое логирование
│   │   └── llm/
│   │       ├── base.py         # Abstract LLM provider
│   │       ├── yandex.py       # YandexGPT implementation
│   │       └── factory.py      # get_provider()
│   ├── modules/                # Модули системы
│   │   ├── energy_electricity/ # Расчёт стоимости электроэнергии
│   │   ├── energy_water/       # Учёт потребления воды
│   │   ├── energy_heat/        # Учёт потребления тепла
│   │   ├── health/             # Анализ здоровья системы
│   │   ├── analytics/          # Тренд-анализ, прогнозы
│   │   ├── deep_analysis/      # Глубокий анализ данных
│   │   └── hello/              # Базовые ответы
│   ├── config/
│   │   └── settings.py         # Pydantic settings
│   ├── data/
│   │   ├── tariffs.json        # Интервальные тарифы
│   │   └── energy_config.json  # Конфигурация счётчиков
│   └── docs/                   # Документация (MD файлы)
│
├── frontend/                   # Frontend код (Svelte 5)
│   ├── src/
│   │   ├── App.svelte          # Главный компонент (роутинг)
│   │   ├── main.ts             # Точка входа
│   │   ├── routes/
│   │   │   ├── Home.svelte     # Операторский интерфейс
│   │   │   └── Config.svelte   # Конфигуратор
│   │   ├── components/
│   │   │   ├── Input.svelte
│   │   │   ├── NarrativePanel.svelte
│   │   │   ├── WidgetRouter.svelte
│   │   │   ├── SystemLogsPanel.svelte
│   │   │   ├── ChartModal.svelte
│   │   │   ├── ABComparisonModal.svelte
│   │   │   ├── DeepAnalysisControls.svelte
│   │   │   ├── DeepAnalysisResults.svelte
│   │   │   ├── DDAInterpretation.svelte
│   │   │   ├── DocsViewer.svelte
│   │   │   ├── analytics/
│   │   │   │   ├── AnalyticsPanel.svelte
│   │   │   │   ├── TrendChart.svelte
│   │   │   │   └── PeriodSelector.svelte
│   │   │   ├── config/
│   │   │   │   └── DDAConfigPanel.svelte
│   │   │   └── health/
│   │   │       ├── HealthScoreCard.svelte
│   │   │       ├── LifeSupportCard.svelte
│   │   │       ├── EnvironmentalPanel.svelte
│   │   │       ├── AlarmsPanel.svelte
│   │   │       ├── EnergyCostCard.svelte
│   │   │       └── IssuesList.svelte
│   │   ├── stores/
│   │   │   ├── chat.ts         # messages, isLoading
│   │   │   ├── theme.ts        # dark/light mode
│   │   │   └── ui.ts           # currentPage
│   │   └── lib/
│   │       └── api.ts          # ky HTTP client
│   ├── index.html
│   ├── package.json
│   ├── svelte.config.js
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── docs/                       # Дополнительная документация
└── *.py                        # Скрипты разработки/фиксов (~200 файлов)
```

### Backend модули (подробно)

```
backend/modules/
├── health/
│   ├── __init__.py             # Регистрация модуля
│   ├── config.yaml             # Конфигурация (prompts, tools)
│   ├── prompts.py              # HEALTH_SYSTEM_PROMPT
│   ├── data_collectors.py      # SQL queries к БД
│   ├── analysis.py             # Детерминированные формулы
│   ├── renderers.py            # narrative/voice/visual
│   ├── localization.py         # Перевод статусов на русский
│   └── tools.py                # TOOLS = []
│
├── deep_analysis/
│   ├── __init__.py
│   ├── api.py                  # FastAPI endpoints
│   ├── core.py                 # Оркестрация анализа
│   ├── settings.py             # Параметры DDA
│   ├── prompts.py              # Промпты для LLM
│   ├── tools.py                # Tools для LLM
│   ├── analyzers/
│   │   ├── anomalies.py        # Isolation Forest, Z-score, IQR
│   │   ├── seasonal.py         # FFT, seasonal pattern extraction
│   │   ├── correlations.py     # Pearson correlation matrix
│   │   ├── stats.py            # compute_basic_stats, downsampling
│   │   └── ab.py               # A/B анализ (Welch's t-test, Cohen's d)
│   ├── collectors/
│   │   ├── data_fetcher.py     # Загрузка данных из БД
│   │   └── tag_resolver.py     # Резолвинг тегов
│   ├── visualizers/
│   │   └── chart_specs.py      # Спецификации графиков Chart.js
│   ├── llm/
│   │   └── interpreter.py      # LLM интерпретация результатов
│   ├── reporter/
│   │   └── __init__.py         # Генерация отчётов
│   └── history/
│       └── storage.py          # Хранение истории анализов
│
├── analytics/
│   ├── __init__.py
│   ├── prompts.py
│   ├── tools.py
│   ├── renderers.py
│   ├── collectors/
│   │   └── history.py          # Сбор из TimescaleDB
│   ├── analyzers/
│   │   ├── trends.py           # Линейная регрессия, R², slope
│   │   ├── correlations.py     # Pearson + временной лаг
│   │   └── aggregators.py      # Ранжирование проблем
│   └── llm/
│       └── analyzer.py         # YandexGPT + fallback
│
├── energy_electricity/
│   ├── __init__.py
│   ├── config.yaml
│   ├── prompts.py
│   ├── tools.py                # calculate_electricity_cost
│   └── data_collector.py       # SQL queries к ЛЭРС
│
├── energy_water/
│   └── ... (аналогично electricity)
│
├── energy_heat/
│   └── ... (аналогично electricity)
│
└── hello/
    ├── __init__.py
    ├── config.yaml
    └── prompts.py
```

### Frontend компоненты (подробно)

```
frontend/src/
├── routes/
│   ├── Home.svelte             # Операторский интерфейс
│   │   - Header с кнопками (логи, DDA, тема, конфигуратор)
│   │   - Chat input (Input.svelte)
│   │   - NarrativePanel (текстовые ответы AI)
│   │   - WidgetRouter (динамический рендеринг виджетов)
│   │   - DeepAnalysisControls (панель управления DDA)
│   │   - DeepAnalysisResults (4 вкладки результатов)
│   │   - SystemLogsPanel (просмотр логов)
│   │
│   └── Config.svelte           # Конфигуратор
│         - Вкладка "Модули" (список активных модулей)
│         - Вкладка "Тарифы" (CRUD интервальных тарифов)
│         - Вкладка "Счётчики" (привязка тегов)
│         - Вкладка "DDA" (настройки глубокого анализа)
│         - Вкладка "Документация" (DocsViewer)
│
├── components/
│   ├── Input.svelte            # Поле ввода сообщения
│   ├── NarrativePanel.svelte   # Текстовые ответы AI
│   ├── WidgetRouter.svelte     # Роутинг виджетов по типу
│   ├── SystemLogsPanel.svelte  # Просмотр системных логов
│   ├── ChartModal.svelte       # Полноэкранные графики с zoom
│   ├── ABComparisonModal.svelte # Модалка A/B анализа
│   ├── DeepAnalysisControls.svelte # Выбор тегов/периодов DDA
│   ├── DeepAnalysisResults.svelte  # 4 вкладки результатов DDA
│   ├── DDAInterpretation.svelte    # LLM интерпретация DDA
│   ├── DocsViewer.svelte       # Просмотр MD документации
│   │
│   ├── analytics/
│   │   ├── AnalyticsPanel.svelte # Виджет аналитики (4 вкладки)
│   │   ├── TrendChart.svelte     # График трендов
│   │   └── PeriodSelector.svelte # Выбор периода прогноза
│   │
│   ├── config/
│   │   └── DDAConfigPanel.svelte # Настройки DDA
│   │
│   └── health/
│       ├── HealthScoreCard.svelte  # Индекс здоровья (0-100)
│       ├── LifeSupportCard.svelte  # Параметры среды
│       ├── EnvironmentalPanel.svelte # CO2, temp, humidity, VOC
│       ├── AlarmsPanel.svelte      # Журнал аварий
│       ├── EnergyCostCard.svelte   # Стоимость ресурсов
│       └── IssuesList.svelte       # Список проблем
│
├── stores/
│   ├── chat.ts                 # messages[], isLoading
│   ├── theme.ts                # 'dark' | 'light'
│   └── ui.ts                   # currentPage
│
└── lib/
    └── api.ts                  # ky HTTP client
```

---

## Backend детали

### main.py — точка входа

```python
"""SCADA.AI v3.2.9.1 — Main application"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from structlog import get_logger

from config.settings import settings
from core.logger import system_logger, install_structlog_bridge

log = get_logger()

# Фильтр для uvicorn access log — убирает спам от polling /system/logs
class AccessLogFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'args') and len(record.args) >= 3:
            _, method, path = record.args[:3]
            if path and '/system/logs' in path and method == 'GET':
                return False
        return True

logging.getLogger("uvicorn.access").addFilter(AccessLogFilter())

install_structlog_bridge()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Старт приложения
    log.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Проверка БД
    from core.db import get_pool
    pool = await get_pool()

    # Загрузка модулей
    from core.module_registry import get_registry
    registry = get_registry()
    registry.load_all(settings.enabled_modules_list)

    # Регистрация tools
    from core.tool_executor import get_executor
    executor = get_executor()
    for tool in registry.get_all_tools():
        executor.register_tool(name=tool["name"], func=tool["function"], schema=tool)

    # Инициализация LLM
    from core.llm import get_provider
    provider = get_provider()

    yield

    # Shutdown
    from core.db import close_pool
    await close_pool()
    system_logger.close()

app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

# CORS middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# Роутеры
from api.routes import chat, config, health, system, docs, energy, analytics, deep_analysis
app.include_router(chat.router, tags=["chat"])
app.include_router(config.router, tags=["config"])
app.include_router(health.router)
app.include_router(system.router)
app.include_router(docs.router)
app.include_router(energy.router)
app.include_router(analytics.router)
app.include_router(deep_analysis.router)
```

### config/settings.py — настройки

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "SCADA.AI v3"
    app_version: str = "3.2.9.1"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Database
    db_host: str = "172.27.10.216"
    db_port: int = 5432
    db_name: str = "scada_ai"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # YandexGPT
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_gpt_model: str = "yandexgpt-lite"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1500
    llm_timeout: int = 60

    # Location
    city: str = "Нижний Тагил"
    timezone: str = "Asia/Yekaterinburg"
    latitude: float = 57.9167
    longitude: float = 59.9417

    # Modules
    enabled_modules: str = "hello,health,logs"

    @property
    def enabled_modules_list(self) -> list[str]:
        return [m.strip() for m in self.enabled_modules.split(",") if m.strip()]

    @property
    def database_url(self) -> str:
        password = quote_plus(self.db_password)
        return f"postgresql://{self.db_user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"

settings = Settings()
```

### core/module_registry.py — реестр модулей

```python
class Module:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.config: Dict[str, Any] = {}
        self.tools: list = []
        self.prompts: Dict[str, str] = {}
        self._loaded = False

    def load(self):
        # Читаем config.yaml
        config_path = self.path / "config.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}

        # Загружаем prompts (только строки)
        prompts_module = importlib.import_module(f"modules.{self.name}.prompts")
        self.prompts = {
            name: getattr(prompts_module, name)
            for name in dir(prompts_module)
            if not name.startswith("_") and isinstance(getattr(prompts_module, name), str)
        }

        # Загружаем tools
        try:
            tools_module = importlib.import_module(f"modules.{self.name}.tools")
            self.tools = getattr(tools_module, "TOOLS", [])
        except ImportError:
            self.tools = []

        self._loaded = True


class ModuleRegistry:
    def __init__(self, modules_dir: Path):
        self.modules_dir = modules_dir
        self._modules: Dict[str, Module] = {}

    def discover_modules(self) -> list[str]:
        modules = []
        for path in self.modules_dir.iterdir():
            if path.is_dir() and (path / "__init__.py").exists():
                modules.append(path.name)
        return sorted(modules)

    def load_module(self, name: str) -> Optional[Module]:
        if name in self._modules and self._modules[name].is_loaded:
            return self._modules[name]

        module_path = self.modules_dir / name
        module = Module(name, module_path)
        module.load()
        self._modules[name] = module
        return module

    def load_all(self, enabled: list[str] | None = None) -> Dict[str, Module]:
        available = self.discover_modules()
        to_load = enabled if enabled else available
        for name in to_load:
            if name in available:
                self.load_module(name)
        return self._modules

    def get_all_tools(self) -> list:
        tools = []
        for module in self._modules.values():
            tools.extend(module.tools)
        return tools


# Singleton
_registry: Optional[ModuleRegistry] = None

def get_registry() -> ModuleRegistry:
    global _registry
    if _registry is None:
        modules_dir = Path(__file__).parent.parent / "modules"
        _registry = ModuleRegistry(modules_dir)
    return _registry
```

### core/tool_executor.py — выполнение tools

```python
class ToolExecutor:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, dict] = {}

    def register_tool(self, name: str, func: Callable, schema: dict):
        self._tools[name] = func
        self._schemas[name] = schema

    async def execute(self, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")
        func = self._tools[name]
        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        return func(**kwargs)

    def get_schemas(self) -> list:
        return list(self._schemas.values())


_executor: Optional[ToolExecutor] = None

def get_executor() -> ToolExecutor:
    global _executor
    if _executor is None:
        _executor = ToolExecutor()
    return _executor
```

### core/llm/yandex.py — YandexGPT provider

```python
class YandexGPTProvider:
    def __init__(self, api_key: str, folder_id: str, model: str, temperature: float, max_tokens: int):
        self.api_key = api_key
        self.folder_id = folder_id
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.provider_name = "YandexGPT"

    async def generate(self, system: str, user: str) -> str:
        # Вызов YandexGPT API
        pass

    async def generate_with_tools(self, system: str, user: str, tools: list,
                                   tool_executor: ToolExecutor, max_iterations: int = 5) -> dict:
        # Tool calling цикл
        messages = [{"role": "system", "text": system}, {"role": "user", "text": user}]

        for _ in range(max_iterations):
            response = await self._call_api(messages, tools)

            if response.has_tool_calls():
                for tool_call in response.tool_calls():
                    result = await tool_executor.execute(tool_call.name, **tool_call.args)
                    messages.append({"role": "tool", "name": tool_call.name, "content": result})
            else:
                return {"text": response.text(), "tool_calls": response.tool_calls()}

        return {"text": "Max iterations reached", "tool_calls": []}
```

### api/routes/chat.py — главный endpoint

```python
HEALTH_KEYWORDS = ["здоров", "состояни", "проблем", "авари", "диагност", "отчёт", "что с", "как дела"]
ANALYTICS_KEYWORDS = ["аналитик", "тренд", "прогноз", "рекомендац", "корреляц", "analytics"]

def is_health_query(text: str) -> bool:
    return any(kw in text.lower() for kw in HEALTH_KEYWORDS)

def is_analytics_query(text: str) -> bool:
    return any(kw in text.lower() for kw in ANALYTICS_KEYWORDS)

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    from core.llm import get_provider
    provider = get_provider()

    # Проверка на аналитику
    if is_analytics_query(req.message):
        return await handle_analytics_query(req.message, provider)

    # Проверка на здоровье
    if is_health_query(req.message):
        return await handle_health_query(req.message, provider)

    # Tool calling
    from core.tool_executor import get_executor
    executor = get_executor()
    tools_schemas = executor.get_schemas()

    system = "Ты — AI-ассистент для оператора SCADA-системы. Отвечай на русском, кратко."

    if tools_schemas:
        result = await provider.generate_with_tools(
            system=system, user=req.message, tools=tools_schemas,
            tool_executor=executor, max_iterations=5
        )
        return ChatResponse(response=result["text"], status="ok",
                           tool_calls=[tc.name for tc in result.get("tool_calls", [])])
    else:
        text = await provider.generate(system, req.message)
        return ChatResponse(response=text, status="ok")
```

---

## Frontend детали

### Home.svelte — операторский интерфейс

```svelte
<script lang="ts">
  import { onMount } from 'svelte'
  import { getHealth } from '../lib/api'
  import { messages, isLoading, addMessage } from '../stores/chat'
  import { navigate } from '../stores/ui'
  import { theme } from '../stores/theme'
  import Input from '../components/Input.svelte'
  import SystemLogsPanel from '../components/SystemLogsPanel.svelte'
  import DeepAnalysisControls from '../components/DeepAnalysisControls.svelte'
  import DeepAnalysisResults from '../components/DeepAnalysisResults.svelte'
  import NarrativePanel from '../components/NarrativePanel.svelte'
  import WidgetRouter from '../components/WidgetRouter.svelte'
  import api from '../lib/api'
  import { Activity, Terminal, Sun, Moon, Settings, Volume2 } from 'lucide-svelte'

  interface SystemInfo {
    app_name: string
    app_version: string
    modules: string[]
    tools_count: number
    db_status: 'ok' | 'error' | 'unknown'
    llm_status: 'ok' | 'error' | 'not_configured'
    capabilities: { text: string; category: string; action?: string }[]
  }

  let health = $state<any>(null)
  let currentWidgets = $state<any[]>([])
  let systemInfo = $state<SystemInfo | null>(null)
  let showLogsPanel = $state(false)
  let showDeepAnalysisPanel = $state(false)
  let ddaTags = $state<any[]>([])
  let ddaSelectedTags = $state<string[]>([])
  let ddaPeriod = $state<number>(30)
  let ddaIsAnalyzing = $state(false)
  let ddaAnalysisResult = $state<any>(null)
  let ddaError = $state<string | null>(null)
  let ddaForceTab = $state<'overview' | 'correlations' | 'table' | 'interpretation' | null>(null)

  onMount(async () => {
    try { health = await getHealth() } catch (e) { console.error(e) }
    try { systemInfo = await api.get('system/info').json<SystemInfo>() } catch (e) { console.error(e) }
  })

  // Загрузка тегов для DDA
  $effect(() => {
    if (showDeepAnalysisPanel && ddaTags.length === 0) {
      api.get('api/v1/deep_analysis/tags').json().then((tags: any[]) => {
        ddaTags = tags
        if (tags.length > 0 && ddaSelectedTags.length === 0) {
          ddaSelectedTags = [tags[0].tag_name]
        }
      })
    }
  })

  async function handleSend(message: string) {
    const lower = message.toLowerCase()

    // Special commands
    if (lower.includes('логи')) { showLogsPanel = true; return }
    if (lower.includes('глубокий анализ')) { showDeepAnalysisPanel = true; return }
    if (lower.includes('конфигуратор')) { navigate('config'); return }

    addMessage('user', message)
    isLoading.set(true)
    currentWidgets = []

    try {
      const resp: any = await api.post('chat', { json: { message } }).json()
      addMessage('assistant', resp.response)

      if (resp.visual?.widgets && resp.visual.widgets.length > 0) {
        currentWidgets = resp.visual.widgets
      }

      if (resp.voice?.text) {
        speak(resp.voice.text)
      }
    } catch (e: any) {
      addMessage('system', `Ошибка: ${e?.message}`)
    } finally {
      isLoading.set(false)
    }
  }

  function speak(text: string) {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      const utter = new SpeechSynthesisUtterance(text)
      utter.lang = 'ru-RU'
      window.speechSynthesis.speak(utter)
    }
  }
</script>

<div class="flex flex-col h-screen bg-neutral-50 dark:bg-neutral-900">
  <header class="bg-neutral-100 dark:bg-neutral-800 border-b px-6 py-3 flex justify-between">
    <h1 class="text-base font-mono">SCADA.AI <span class="text-neutral-400">v3.2.9.1</span></h1>
    <div class="flex gap-2">
      <button onclick={() => showLogsPanel = !showLogsPanel}><Terminal size={18} /></button>
      <button onclick={() => showDeepAnalysisPanel = !showDeepAnalysisPanel}><Activity size={18} /></button>
      <button onclick={() => theme.toggle()}>{$theme === 'dark' ? <Sun/> : <Moon/>}</button>
      <button onclick={() => navigate('config')}><Settings size={18} /></button>
    </div>
  </header>

  <div class="flex-1 flex overflow-hidden">
    {#if showLogsPanel}
      <SystemLogsPanel onClose={() => showLogsPanel = false} />
    {/if}

    {#if showDeepAnalysisPanel}
      <DeepAnalysisControls
        tags={ddaTags}
        selectedTags={ddaSelectedTags}
        period={ddaPeriod}
        isAnalyzing={ddaIsAnalyzing}
        error={ddaError}
        onTagsChange={(tags) => ddaSelectedTags = tags}
        onPeriodChange={(p) => ddaPeriod = p}
        onAnalyze={runDDAAnalysis}
      />

      {#if ddaAnalysisResult}
        <DeepAnalysisResults
          result={ddaAnalysisResult}
          forceTab={ddaForceTab}
          onUseInAnalysis={() => {/* передать в чат */}}
        />
      {/if}
    {/if}

    <main class="flex-1 flex flex-col">
      <NarrativePanel messages={$messages} />

      {#if currentWidgets.length > 0}
        <WidgetRouter widgets={currentWidgets} onClose={handleCloseWidgets} />
      {/if}

      <Input onSend={handleSend} disabled={$isLoading} />
    </main>
  </div>
</div>
```

### WidgetRouter.svelte — роутинг виджетов

```svelte
<script lang="ts">
  import HealthScoreCard from './health/HealthScoreCard.svelte'
  import LifeSupportCard from './health/LifeSupportCard.svelte'
  import EnvironmentalPanel from './health/EnvironmentalPanel.svelte'
  import AlarmsPanel from './health/AlarmsPanel.svelte'
  import EnergyCostCard from './health/EnergyCostCard.svelte'
  import IssuesList from './health/IssuesList.svelte'
  import AnalyticsPanel from './analytics/AnalyticsPanel.svelte'

  export let widgets: any[] = []
  export let onClose: () => void = () => {}

  function getComponent(type: string) {
    switch (type) {
      case 'health_score': return HealthScoreCard
      case 'life_support_card': return LifeSupportCard
      case 'environmental_panel': return EnvironmentalPanel
      case 'alarms_panel': return AlarmsPanel
      case 'energy_cost_card': return EnergyCostCard
      case 'issues_list': return IssuesList
      case 'analytics_panel': return AnalyticsPanel
      default: return null
    }
  }
</script>

<div class="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {#each widgets as widget (widget.type)}
    {@const Component = getComponent(widget.type)}
    {#if Component}
      <div class="bg-white dark:bg-neutral-800 rounded-lg shadow p-4">
        <Component data={widget.data} />
      </div>
    {:else}
      <div class="text-red-500">Виджет не найден: {widget.type}</div>
    {/if}
  {/each}
</div>
```

### stores/chat.ts — хранилище чата

```typescript
import { writable } from 'svelte/store'

export interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

export const messages = writable<Message[]>([])
export const isLoading = writable<boolean>(false)

export function addMessage(role: Message['role'], content: string) {
  messages.update(msgs => [...msgs, { role, content, timestamp: new Date() }])
}

export function clearMessages() {
  messages.set([])
}
```

### stores/theme.ts — тема

```typescript
import { writable } from 'svelte/store'

type Theme = 'dark' | 'light'

function createThemeStore() {
  const { subscribe, update } = writable<Theme>('light')

  return {
    subscribe,
    toggle: () => update(t => {
      const next = t === 'dark' ? 'light' : 'dark'
      document.documentElement.classList.toggle('dark', next === 'dark')
      localStorage.setItem('theme', next)
      return next
    }),
    init: () => {
      const saved = localStorage.getItem('theme') as Theme | null
      if (saved) {
        document.documentElement.classList.toggle('dark', saved === 'dark')
        update(() => saved)
      }
    }
  }
}

export const theme = createThemeStore()
```

---

## Модули

### Список модулей

| Модуль | Тип | Описание | Tools | Виджеты |
|--------|-----|----------|-------|---------|
| **health** | Детерминированный + LLM | Анализ здоровья системы (alarms, environmental, equipment) | get_health_report | health_score, life_support_card, environmental_panel, alarms_panel |
| **deep_analysis** | Детерминированный | DDA: аномалии, сезонность, корреляции, A/B | (через API) | dda_panel |
| **analytics** | Детерминированный + LLM | Тренды, прогнозы, impact scoring | (через /chat) | analytics_panel |
| **energy_electricity** | Детерминированный | Расчёт стоимости электроэнергии | calculate_electricity_cost, get_consumption | energy_cost_card |
| **energy_water** | Детерминированный | Учёт потребления воды | calculate_water_cost, get_consumption | — |
| **energy_heat** | Детерминированный | Учёт потребления тепла | calculate_heat_cost, get_consumption | — |
| **logs** | LLM (tool calling) | Анализ системных логов | analyze_logs | — |
| **hello** | Текстовый | Базовые ответы на приветствия | — | — |

### health модуль

**Файлы**:
- `modules/health/__init__.py` — регистрация
- `modules/health/prompts.py` — HEALTH_SYSTEM_PROMPT
- `modules/health/data_collectors.py` — SQL queries
- `modules/health/analysis.py` — детерминированные формулы
- `modules/health/renderers.py` — narrative/voice/visual
- `modules/health/localization.py` — перевод на русский
- `modules/health/tools.py` — TOOLS = []

**Формула health_score**:
```python
score = 0.40 * alarm_index + 0.35 * environmental_index + 0.25 * equipment_index
```

**Статусы**:
- EXCELLENT: score >= 85
- GOOD: 60 <= score < 85
- WARNING: 30 <= score < 60
- CRITICAL: score < 30

### deep_analysis модуль

**Файлы**:
- `modules/deep_analysis/api.py` — FastAPI endpoints
- `modules/deep_analysis/core.py` — оркестрация
- `modules/deep_analysis/analyzers/anomalies.py` — Isolation Forest, Z-score, IQR
- `modules/deep_analysis/analyzers/seasonal.py` — FFT, pattern extraction
- `modules/deep_analysis/analyzers/correlations.py` — Pearson matrix
- `modules/deep_analysis/analyzers/stats.py` — basic stats, downsampling
- `modules/deep_analysis/analyzers/ab.py` — Welch's t-test, Cohen's d
- `modules/deep_analysis/visualizers/chart_specs.py` — Chart.js specs
- `modules/deep_analysis/llm/interpreter.py` — LLM интерпретация

**API Endpoints**:
- `POST /api/v1/deep_analysis/analyze` — запуск анализа
- `POST /api/v1/deep_analysis/ab` — A/B сравнение
- `GET /api/v1/deep_analysis/tags` — список тегов

### analytics модуль

**Файлы**:
- `modules/analytics/collectors/history.py` — сбор данных
- `modules/analytics/analyzers/trends.py` — линейная регрессия
- `modules/analytics/analyzers/correlations.py` — Pearson + lag
- `modules/analytics/analyzers/aggregators.py` — ranking
- `modules/analytics/llm/analyzer.py` — LLM insights
- `modules/analytics/renderers.py` — визуализация

**Прогнозы**: 7/30/90/365 дней

### energy_* модули

**Файлы**:
- `modules/energy_electricity/tools.py` — calculate_electricity_cost
- `modules/energy_electricity/data_collector.py` — SQL к ЛЭРС
- `data/tariffs.json` — интервальные тарифы
- `data/energy_config.json` — теги счётчиков

**Логика выбора тарифа**:
```python
def get_active_tariff(resource: str, date: datetime) -> float:
    for tariff in tariffs[resource]:
        if tariff.start_date <= date and (tariff.end_date is None or date < tariff.end_date):
            return tariff.price_per_unit
    return DEFAULT_TARIFF
```

---

## API Endpoints

### Основные

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Root endpoint (name, version, status) |
| GET | `/health` | Проверка работоспособности |
| POST | `/chat` | Диалог с AI-ассистентом |
| GET | `/system/info` | Информация о системе |
| GET | `/debug/routes` | Список всех роутов |

### Health

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/health/metrics-summary` | Сводка по параметрам среды |
| GET | `/health/alarms` | Журнал аварий |
| GET | `/health/environmental` | Параметры среды |

### Deep Analysis

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/deep_analysis/analyze` | Запуск глубокого анализа |
| POST | `/api/v1/deep_analysis/ab` | A/B сравнение |
| GET | `/api/v1/deep_analysis/tags` | Список доступных тегов |

### Analytics

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/analytics/report` | Отчёт по трендам и прогнозам |

### Energy

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/energy/cost` | Стоимость ресурсов |
| GET | `/energy/consumption` | Потребление ресурсов |

### Config

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/config/modules` | Список модулей |
| PUT | `/config/modules/{name}/enabled` | Включить/выключить модуль |
| GET | `/config/prompts` | Список промптов |
| PUT | `/config/prompts/{name}` | Обновить промпт |

### Docs

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/docs/list` | Список MD файлов |
| GET | `/docs/{filename}` | Содержимое файла |

---

## База данных

### Таблицы

#### tags_value
```sql
CREATE TABLE tags_value (
    id BIGSERIAL PRIMARY KEY,
    tag_name VARCHAR(255) NOT NULL,
    value DOUBLE PRECISION,
    timestamp TIMESTAMPTZ NOT NULL,
    quality INTEGER
);
CREATE INDEX ON tags_value (tag_name, timestamp DESC);
```

#### alarm_events_history
```sql
CREATE TABLE alarm_events_history (
    id BIGSERIAL PRIMARY KEY,
    tag_name VARCHAR(255),
    priority VARCHAR(20), -- HIGH, MEDIUM, LOW
    event_type VARCHAR(50),
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    description TEXT
);
```

#### anomaly_events (deep_analysis)
```sql
CREATE TABLE anomaly_events (
    id BIGSERIAL PRIMARY KEY,
    analysis_id VARCHAR(100),
    tag_name VARCHAR(255),
    anomaly_type VARCHAR(50), -- spike, dip, drift, noise
    timestamp TIMESTAMPTZ,
    value DOUBLE PRECISION,
    confidence FLOAT
);
```

### SQL запросы

#### Получение данных тега
```python
async def get_tag_data(tag_name: str, start: datetime, end: datetime, limit: int = 10000):
    query = """
        SELECT timestamp, value
        FROM tags_value
        WHERE tag_name = $1 AND timestamp BETWEEN $2 AND $3
        ORDER BY timestamp DESC
        LIMIT $4
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, tag_name, start, end, limit)
    return [{"timestamp": r["timestamp"], "value": r["value"]} for r in rows]
```

#### Аварии за период
```python
async def get_alarms(start: datetime, end: datetime):
    query = """
        SELECT tag_name, priority, event_type, start_time, end_time, description
        FROM alarm_events_history
        WHERE start_time BETWEEN $1 AND $2
        ORDER BY start_time DESC
    """
    async with pool.acquire() as conn:
        return await conn.fetch(query, start, end)
```

---

## Конфигурация

### .env файл

```bash
# Database
DB_HOST=172.27.10.216
DB_PORT=5432
DB_NAME=scada_ai
DB_USER=postgres
DB_PASSWORD=postgres

# YandexGPT
YANDEX_API_KEY=y0_...
YANDEX_FOLDER_ID=b1g...
YANDEX_GPT_MODEL=yandexgpt-lite

# LLM settings
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1500
LLM_TIMEOUT=60

# Location
CITY=Нижний Тагил
TIMEZONE=Asia/Yekaterinburg
LATITUDE=57.9167
LONGITUDE=59.9417

# Modules
ENABLED_MODULES=hello,health,logs,energy_electricity,analytics,deep_analysis

# Logs
LOG_POLL_INTERVAL_MS=2000
LOG_POLL_MAX_ENTRIES=500
```

### data/tariffs.json

```json
{
  "electricity": [
    {
      "id": "t1",
      "start_date": "2025-01-01",
      "end_date": "2026-02-01",
      "price_per_unit": 5.50,
      "currency": "RUB"
    },
    {
      "id": "t2",
      "start_date": "2026-02-01",
      "end_date": null,
      "price_per_unit": 6.20,
      "currency": "RUB"
    }
  ],
  "water": [...],
  "heat": [...]
}
```

### data/energy_config.json

```json
{
  "electricity": {
    "counter_tag": "R001-EnergyCounter",
    "unit": "kWh"
  },
  "water": {
    "counter_tag": "R002-WaterCounter",
    "unit": "m³"
  },
  "heat": {
    "counter_tag": "R003-HeatCounter",
    "unit": "GCal"
  }
}
```

---

## Математика и алгоритмы

### Детекция аномалий

#### Isolation Forest
```python
from sklearn.ensemble import IsolationForest

clf = IsolationForest(contamination=0.05, random_state=42)
predictions = clf.fit_predict(data.reshape(-1, 1))
# -1 = anomaly, 1 = normal
```

#### Z-score
```python
import numpy as np

mean = np.mean(data)
std = np.std(data)
z_scores = np.abs((data - mean) / std)
anomalies = z_scores > 3  # threshold = 3σ
```

#### IQR (Interquartile Range)
```python
Q1 = np.percentile(data, 25)
Q3 = np.percentile(data, 75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
anomalies = (data < lower_bound) | (data > upper_bound)
```

#### Типизация аномалий
- **spike**: резкий пик (1-2 точки)
- **dip**: резкое падение
- **drift**: плавный уход от нормы
- **noise**: шумовая аномалия (серия точек)

### Сезонный анализ (FFT)

#### Fast Fourier Transform
```python
from scipy import fft

# Вычисление FFT
fft_result = fft.fft(data)
freqs = fft.fftfreq(len(data), d=sampling_interval)

# Power Spectrum Density
psd = np.abs(fft_result) ** 2

# Поиск пиков (доминирующих частот)
peaks = find_peaks(psd, height=threshold)
periods = 1 / freqs[peaks]
```

#### Извлечение паттерна
```python
def get_seasonal_pattern(data, period):
    # Фолдинг данных по периоду
    n_cycles = len(data) // period
    folded = data[:n_cycles * period].reshape(n_cycles, period)

    # Усреднение по фазам
    pattern = np.mean(folded, axis=0)

    return pattern
```

#### Декомпозиция
```python
def decompose(data, period):
    # Trend (rolling mean)
    trend = data.rolling(window=period, center=True).mean()

    # Detrended
    detrended = data - trend

    # Seasonal (average by phase)
    seasonal = get_seasonal_pattern(detrended, period)

    # Residual
    residual = data - trend - seasonal

    return trend, seasonal, residual
```

### A/B Анализ

#### Welch's t-test
```python
from scipy import stats

t_stat, p_value = stats.ttest_ind(sample_a, sample_b, equal_var=False)
```

#### Cohen's d (effect size)
```python
def cohens_d(a, b):
    n_a, n_b = len(a), len(b)
    var_a, var_b = np.var(a, ddof=1), np.var(b, ddof=1)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))

    if pooled_std == 0:
        return 0

    return (np.mean(b) - np.mean(a)) / pooled_std
```

#### Интерпретация Cohen's d
- |d| < 0.2: negligible
- 0.2 ≤ |d| < 0.5: small
- 0.5 ≤ |d| < 0.8: medium
- |d| ≥ 0.8: large

#### Сравнение паттернов
```python
pattern_corr = np.corrcoef(pattern_a, pattern_b)[0, 1]
delta_amplitude = (amplitude_b - amplitude_a) / amplitude_a * 100
```

### Тренд-анализ

#### Линейная регрессия
```python
from scipy import stats

slope, intercept, r_value, p_value, std_err = stats.linregress(x_days, y_values)

# Прогноз
forecast_days = np.arange(last_day, last_day + forecast_period)
forecast_values = slope * forecast_days + intercept
```

#### R² (coefficient of determination)
```python
r_squared = r_value ** 2
# 0 = no fit, 1 = perfect fit
```

### Корреляции

#### Pearson correlation
```python
corr_matrix = np.corrcoef(data_tags.T)
# corr_matrix[i, j] = correlation between tag i and tag j
```

#### Временной лаг
```python
def cross_correlation(x, y, max_lag=24):
    correlations = []
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            x_shifted, y_shifted = x[:lag], y[-lag:]
        elif lag > 0:
            x_shifted, y_shifted = x[lag:], y[:-lag]
        else:
            x_shifted, y_shifted = x, y

        corr = np.corrcoef(x_shifted, y_shifted)[0, 1]
        correlations.append((lag, corr))

    return max(correlations, key=lambda x: abs(x[1]))
```

---

## Примеры кода

### Запуск DDA анализа (Frontend)

```typescript
async function runDDAAnalysis() {
  if (ddaSelectedTags.length === 0) {
    ddaError = 'Выберите тег для анализа'
    return
  }

  ddaIsAnalyzing = true
  ddaError = null

  try {
    const response = await api.post('api/v1/deep_analysis/analyze', {
      json: {
        tags: ddaSelectedTags,
        period: ddaPeriod,
        params: {
          anomaly_detection: true,
          seasonal_analysis: true,
          correlation_matrix: true
        }
      }
    }).json()

    ddaAnalysisResult = response
  } catch (e: any) {
    ddaError = e?.message || 'Ошибка анализа'
  } finally {
    ddaIsAnalyzing = false
  }
}
```

### A/B Сравнение (Frontend)

```typescript
async function compareSnapshots(mode: 'before_after' | 'equipment',
                                snapshotA: any, snapshotB: any) {
  try {
    const result = await api.post('api/v1/deep_analysis/ab', {
      json: {
        mode,
        snapshot_a: snapshotA,
        snapshot_b: snapshotB
      }
    }).json()

    // Добавить результат в DDA для LLM интерпретации
    if (ddaAnalysisResult) {
      ddaAnalysisResult.ab_comparison = result
    }

    // Переключить на вкладку интерпретации
    ddaForceTab = 'interpretation'
  } catch (e: any) {
    console.error('A/B comparison failed:', e)
  }
}
```

### Обработка health запроса (Backend)

```python
async def handle_health_query(message: str, provider) -> ChatResponse:
    from modules.health.prompts import HEALTH_SYSTEM_PROMPT
    from modules.health.data_collectors import collect_all_health_data
    from modules.health.analysis import compute_health_report
    from modules.health.renderers import render_all

    # Сбор данных
    data = await collect_all_health_data()

    # LLM генерация
    llm_response = await provider.generate(HEALTH_SYSTEM_PROMPT, json.dumps(data))

    # Парсинг JSON
    report_data = _extract_json(llm_response)

    # Детерминированный расчёт (fallback)
    if not report_data:
        report = compute_health_report(data)
        report_data = report.dict()

    # Рендеринг
    rendered = render_all(report_data)

    return ChatResponse(
        response=rendered["narrative"],
        status="ok",
        voice=rendered["voice"],
        visual={"widgets": rendered["visual"]["widgets"]}
    )
```

---

## Известные проблемы

### Health модуль
- Если SCADA не пишет данные последние 24 часа, отображаются нули (данные есть, но старые)

### DDA
- UnicodeEncodeError при логировании результатов с символами ↔ — исправлено в v3.2.9.1
- Кнопки зума на маленьком графике "Типичный паттерн" для multi-tag — исправлено в v3.2.9.1

### Общие
- Нет авторизации — все endpoints публичные
- Нет CORS — только localhost
- Single instance — не распределённая система

---

## Быстрый старт

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8081

# Frontend
cd frontend
npm install
npm run dev
```

---

## Ссылки на документацию

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — архитектура системы
- [MODULES.md](docs/MODULES.md) — описание модулей
- [DDA.md](docs/DDA.md) — Deep Data Analysis
- [SEASON_ANALYSIS.md](docs/SEASON_ANALYSIS.md) — сезонный анализ и FFT
- [AB_ANALYSIS.md](docs/AB_ANALYSIS.md) — A/B анализ с математикой
- [ANALYTICS.md](docs/ANALYTICS.md) — тренд-анализ и прогнозы
- [API.md](docs/API.md) — HTTP endpoints
- [CHANGELOG.md](docs/CHANGELOG.md) — история изменений
- [README.md](docs/README.md) — обзор системы

---

**Этот файл содержит полную информацию о системе SCADA.AI v3.2.9.1 для использования в качестве контекста при разработке.**
