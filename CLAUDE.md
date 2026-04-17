# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

**IDS2PSET** — бессерверное SPA, генерирующее библиотеки свойств IFC4 из IDS-спецификаций (Information Delivery Specification). Работает полностью в браузере через WebAssembly (Pyodide).

## Commands

```bash
# Активация виртуального окружения (создать: python3 -m venv .venv)
source .venv/bin/activate

# Python-тесты — все модули
pytest tests/ -v --cov=src --cov-report=term-missing

# Один модуль / один тест
pytest tests/test_parser.py -v
pytest tests/test_parser.py::TestParseIdsFile::test_parse_minimal_ids -v

# JS-тесты (Node.js built-in test runner)
node --test tests/test.js
node --test tests/test_e2e.js
```

Python-тесты разбиты по модулям: `test_parser.py`, `test_generator.py`, `test_validator.py`, `test_gherkin.py`, `test_e2e.py`.

## Architecture

Приложение состоит из двух слоёв — JavaScript (браузер) и Python (Pyodide/WASM):

### Python-модули (`src/`)

- **`ids_parser.py`** — парсит IDS XML и возвращает `Dict[str, PSetGroup]`. Основная точка входа: `parse_ids_file(path)` / `parse_ids_content(str)`. Поддерживает `simpleValue`, `xs:enumeration` и `xs:pattern` для имён сущностей, PSet и свойств. Различает "жёсткий" regex (`xs:pattern` → `is_pattern=True`) и "мягкий" (regex-символы в `simpleValue` → `simple_value_pattern=True`).
- **`pset_generator.py`** — принимает разобранные PSet и генерирует IFC4-файл через `ifcopenshell`. Класс `PSetGenerator`, метод `generate(psets_dict)`.
- **`validator.py`** — валидирует сгенерированный IFC через `ifcopenshell.validate`. Класс `IFCValidator`, метод `validate_file(path)`.

### JavaScript (`js/`)

- **`pyodide-bridge.js`** — загружает Pyodide v0.29.3 (Python 3.13 + WASM), устанавливает `ifcopenshell` из CDN-wheel, копирует Python-модули в виртуальную FS Pyodide. Singleton `window.pyodideBridge` с методами `parseIDS(content)`, `generateIFC(psets, names)`, `validateIFC(content)`. `ifcopenshell` загружается лениво — только при генерации/валидации, не при парсинге.
- **`app.js`** — UI-логика: `IDS2PSETApp`, drag-and-drop загрузка файлов, рендеринг дерева PSet, навигация между несколькими IDS. Каждый загруженный IDS хранит свои PSet независимо (`psetsByIDS`) и генерирует отдельный IFC (`ifcByIDS`).

### Поток данных

```
.ids файл → app.js:handleFiles()
         → pyodideBridge.parseIDS()
         → Python: ids_parser.parse_ids_file()
         → PSetGroup dataclasses
         → JSON → JS объект
         → app.js:renderPSetColumns() (превью)
         → [Кнопка "Сгенерировать"]
         → pyodideBridge.generateIFC()
         → Python: PSetGenerator.generate()
         → IFC-строка → скачивание
```

### Ключевые данные-структуры

`PSetGroup` (Python) → JSON-объект (JS):
- `is_pattern`: PSet-имя задано через `xs:pattern` → не генерируется в IFC
- `simple_value_pattern`: regex-символы в `simpleValue` → предупреждение в UI, но генерируется
- `entity_warning`: не удалось определить сущность из IDS
- `invalid_entities`: список сущностей, не найденных в `_VALID_IFC_ENTITIES`

## Key constraints

- `ifcopenshell` совместим **только** с Pyodide v0.29.3 (Python 3.13, `pyodide_2025_0`). Не менять версию Pyodide без проверки wheel-совместимости.
- Wheel `ifcopenshell-0.8.4-cp313-cp313-pyodide_2025_0_wasm32.whl` хранится в `wheels/` и раздаётся с GitHub CDN.
- Тесты Python: `tests/test_*.py` (pytest). Фикстуры (`.ids` XML) — в `tests/fixtures/`.
