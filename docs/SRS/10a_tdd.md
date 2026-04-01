# 10a. TDD и валидация

## 10a.1 Покрытие тестами

**Требование:** 100% покрытие Python и JS кода

**Инструменты:**
- Python: `pytest` + `pytest-cov`
- JS: нативный тестовый фреймворк или Jest

---

## 10a.2 Python тесты

**Файл:** `tests/test.py`

**Тестируемые модули:**
- `ids_parser.py` — парсинг XML, извлечение требований
- `pset_generator.py` — создание IFC структур
- `validator.py` — валидация результата

**Тестовые сценарии:**
- Парсинг минимального IDS (1 entity, 1 PSet, 2 свойства)
- Парсинг IDS с enumerations
- Группировка по specification + entity + propertySet
- Создание IfcPropertySetTemplate
- Создание IfcSimplePropertyTemplate с разными типами данных
- Создание IfcPropertyEnumeration

---

## 10a.3 JS тесты

**Файл:** `tests/test.js`

**Тестируемые модули:**
- `app.js` — логика UI
- `pyodide-bridge.js` — связь с Python

**Тестовые сценарии:**
- Инициализация страницы
- Загрузка файлов через File API
- Отображение дерева PSet
- Фильтрация чекбоксами
- Скачивание файла

---

## 10a.4 Валидация в тестах

**Инструменты:**
- `ifcopenshell.validate()` — проверка структуры IFC
- `ifc-gherkin-rules` — проверка по правилам buildingSMART

**Процесс:**
1. Тест генерирует IFC
2. Запускается валидация
3. Тест проходит только если IFC валиден

---

## 10a.5 Ссылки
- [[10_technical_decisions](10_technical_decisions.md) — Структура проекта
- [[11_implementation_plan](11_implementation_plan.md) — План реализации

---
*Версия: 0.1 | Статус: Черновик*
