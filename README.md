# AI Code Review Agent

Автономная мультиагентная система для статического и динамического анализа Python-кода: локализует потенциальные уязвимости (SQLi, RCE, хардкод), верифицирует их наличие через генерацию и безопасный запуск эксплойтов в изолированных микро-VM, а также инкрементально обучается на основе подтвержденных находок.

## Требования к окружению

- Python >= 3.13, локальный рантайм Ollama (модели: `gemma2:2b`, `qwen2.5-coder:7b`, `llama3.1:8b`)
- Ключи в `.env`: `E2B_API_KEY` (для песочницы Firecracker), `LANGCHAIN_API_KEY` (для сбора трейсов в LangSmith)

## Быстрый старт

1. Настройка окружения:
```bash
git clone <ссылка_на_репозиторий>
cd SE_2_agent
python -m venv .venv
source .venv/bin/activate  # Для Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Загрузка локальных моделей:
```bash
ollama pull gemma2:2b && ollama pull qwen2.5-coder:7b && ollama pull llama3.1:8b
```

3. Запуск интерактивного аудита:
```bash
cp .env.example .env
python main.py
```

## Сценарии использования и проверка

- `python main.py` - основной CLI-интерфейс для выбора уязвимого примера или ручного ввода кастомного python-кода на аудит
- `python graph.py` - прямой запуск основного управляющего графа оркестрации (LangGraph)
- `python evals.py` - запуск бенчмаркинга системы на тестовых кейсах (расчет Accuracy, Recall и сквозной Latency контура)

## Метрики и Observability

| Компонент / Задача | Инструмент / Стек                  | Вход / Способ контроля |
|---|------------------------------------|---|
| Оркестрация и петли рефлексии | LangGraph (StateGraph)             | Код узлов в `graph.py` (лимит `reflection_count`) |
| Анализ траекторий и спанов | LangSmith Cloud                    | Дашборд по имени проекта из `LANGCHAIN_PROJECT` |
| Долгосрочная память правил | SQLite (`long_term_memory.db`)     | Прямой SQL-запрос `SELECT * FROM facts;` |
| Краткосрочные чекпоинты сессий | SqliteSaver (`checkpoints.sqlite`) | Автоматическое сохранение состояния по `thread_id` |
| Аппаратная изоляция эксплойтов | E2B Sandbox                        | secure-runtime среда исполнения (Firecracker microVM) |

Архитектурные диаграммы (C4 Context, Container, Component, Code + Sequence Flow) расположены в каталоге: `docs/architecture/`.
