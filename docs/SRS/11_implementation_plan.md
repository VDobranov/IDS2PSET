# 11. План реализации

## Этап 1: Каркас проекта

- [ ] `index.html` — базовая разметка
- [ ] `css/style.css` — минимальные стили
- [ ] `js/app.js` — заготовка UI
- [ ] Настройка Pyodide

**Тесты:**
- [ ] `test.js` — инициализация страницы

**Критерий готовности:** Страница загружается, Pyodide инициализируется

---

## Этап 2: Загрузка IDS

- [ ] Drag-and-drop зона
- [ ] Чтение файлов через File API
- [ ] Отображение списка файлов

**Тесты:**
- [ ] `test.js` — загрузка файла

**Критерий готовности:** Файл загружается, контент в памяти

---

## Этап 3: Парсинг IDS

- [ ] `src/ids_parser.py` — XML парсер
- [ ] Извлечение `specification` → `applicability` → `requirements`
- [ ] Фильтрация только `property` требований

**Тесты:**
- [ ] `test.py` — парсинг минимального IDS
- [ ] `test.py` — парсинг enumerations

**Критерий готовности:** IDS распарсен, данные в структуре Python

---

## Этап 4: Группировка PSet

- [ ] Группировка по `propertySet Name`
- [ ] Объединение свойств в рамках одного PSet
- [ ] Объединение `ApplicableEntity` через запятую

**Тесты:**
- [ ] `test.py` — группировка PSet
- [ ] `test.py` — объединение entity из разных specification

**Критерий готовности:** Данные сгруппированы

---

## Этап 5: Отображение PSet

- [ ] Дерево Specification → Entity → PSet → Свойства
- [ ] Чекбоксы для фильтрации
- [ ] Детали свойств (тип, cardinality, ограничения)

**Тесты:**
- [ ] `test.js` — отображение дерева
- [ ] `test.js` — фильтрация чекбоксами

**Критерий готовности:** PSet видны, фильтрация работает

---

## Этап 6: Генерация IFC

- [ ] `src/pset_generator.py` — создание IFC
- [ ] `IfcProjectLibrary`
- [ ] `IfcPropertySetTemplate`
- [ ] `IfcSimplePropertyTemplate`
- [ ] `IfcPropertyEnumeration`

**Тесты:**
- [ ] `test.py` — создание библиотеки
- [ ] `test.py` — создание PSet с enumeration
- [ ] Валидация: ifcopenshell.validate
- [ ] Валидация: ifc-gherkin-rules

**Критерий готовности:** IFC сгенерирован в памяти

---

## 11.1 Ссылки
- [[10_technical_decisions](10_technical_decisions.md) — Технические решения
- [[10a_tdd](10a_tdd.md) — TDD и валидация
- [[11a_validation_plan](11a_validation_plan.md) — Валидация и скачивание

---
*Версия: 0.4 | Статус: Черновик*
