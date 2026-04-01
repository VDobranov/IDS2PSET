# 11. План реализации

## Этап 1: Каркас проекта ✅

- [x] `index.html`, `css/style.css`, `js/app.js`
- [x] Настройка Pyodide

**Критерий:** Страница загружается ✅

## Этап 2: Загрузка IDS ✅

- [x] Drag-and-drop зона, File API
- [x] Отображение списка файлов

**Критерий:** Файл загружается ✅

## Этап 3: Парсинг IDS ✅

- [x] `src/ids_parser.py` — XML парсер
- [x] Извлечение specification → applicability → requirements

**Критерий:** IDS распарсен ✅

## Этап 4: Группировка PSet ✅

- [x] Группировка по `propertySet Name`
- [x] Объединение `ApplicableEntity` через запятую

**Критерий:** Данные сгруппированы ✅

## Этап 5: Отображение PSet ✅

- [x] Дерево Specification → Entity → PSet → Свойства
- [x] Чекбоксы для фильтрации

**Критерий:** PSet видны, фильтрация работает ✅

## Этап 6: Генерация IFC ✅

- [x] `src/pset_generator.py` — создание IFC4
- [x] IfcProjectLibrary, IfcPropertySetTemplate, IfcSimplePropertyTemplate

**Критерий:** IFC сгенерирован ✅

## Этап 7: Валидация IFC ✅

- [x] `src/validator.py` — ifcopenshell.validate
- [x] `src/gherkin_validator.py` — 33 категории gherkin-rules

**Критерий:** Все тесты проходят ✅

**Детали:** [11a_validation_plan.md](11a_validation_plan.md)

## Этап 8: Интеграция ✅

- [x] `js/pyodide-bridge.js` — соединение парсера и генератора
- [x] Запуск Python из JS через Pyodide
- [x] `wheels/ifcopenshell-*.whl` — бинарный wheel для Pyodide

**Критерий:** Полный цикл работает в браузере ✅

## Этап 9: Скачивание IFC ✅

- [x] Создание Blob из IFC строки
- [x] Триггер скачивания через `<a>` элемент
- [x] Имя файла `IDS2PSET_Library.ifc`

**Критерий:** Файл скачивается ✅

## Этап 10: E2E тестирование ⏳ TODO

- [ ] Полный цикл: загрузка → анализ → генерация → скачивание
- [ ] Обработка ошибок

**Критерий:** Всё работает вместе

---

## 11.1 Ссылки

- [[10_technical_decisions](10_technical_decisions.md) — Технические решения
- [[10a_tdd](10a_tdd.md) — TDD
- [[11a_validation_plan](11a_validation_plan.md) — Валидация

---
*Версия: 0.6 | Статус: Этапы 1-7 выполнены, этап 8 в работе*
