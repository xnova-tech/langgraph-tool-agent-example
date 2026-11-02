# LangGraph-агент с инструментами

Минимальный пример XNova показывает граф `model → tools → model` на Python. Настоящий `StateGraph`, `MessagesState` и `ToolNode` выполняют два read-only инструмента, а детерминированная функция заменяет LLM, чтобы маршрут можно было проверить без API-ключей и внешней сети.

## Что понадобится

- Python 3.12;
- Git;
- терминал.

## Установка

```bash
git clone https://github.com/xnova-tech/langgraph-tool-agent-example.git
cd langgraph-tool-agent-example
python3.12 -m venv .venv
```

Активируйте окружение:

- macOS и Linux: `source .venv/bin/activate`;
- Windows PowerShell: `.venv\Scripts\Activate.ps1`;
- Windows cmd: `.venv\Scripts\activate.bat`.

Установите закреплённые зависимости:

```bash
python -m pip install -r requirements-dev.txt
```

## Запуск примера

```bash
python agent_graph.py
```

Ожидаемый stdout:

```text
get_status -> HTTP 503
get_runbook -> проверить журнал и upstream
completed: HTTP 503; следующий шаг: проверить журнал и upstream.
```

`HTTP 503` здесь — строка из локального словаря, а не результат сетевого запроса.

## Запуск тестов

```bash
python -m pytest -q
```

Шесть тестов проверяют два успешных вызова инструментов, завершение без инструмента, неизвестный инструмент, недопустимый аргумент, `GraphRecursionError` при достижении лимита и прямые ограничения read-only функций.

## Структура

- `agent_graph.py` — детерминированный LangGraph с настоящим `ToolNode`;
- `tests/test_agent_graph.py` — pytest-контракт положительных и отрицательных сценариев;
- `.github/workflows/check.yml` — проверки на Linux, macOS и Windows.

Проект не обращается к LLM, сети, пользовательским файлам или секретам и не выполняет изменяющих операций. Он проверяет исполнение графа, но не качество решений настоящей модели.

Исходники распространяются по Apache-2.0; условия находятся в `LICENSE`.
