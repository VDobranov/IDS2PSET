# 4. Интерфейсы

## 4.1 Пользовательские интерфейсы

### UI-1: Область загрузки IDS
**Элементы**:
- Зона drag-and-drop для файлов `.ids`
- Кнопка выбора файлов
- Поддержка множественной загрузки
- Список загруженных файлов с именами
- Индикатор статуса обработки

**Ссылки**: [[03_features](03_features.md#FR-1), [[05_constraints](05_constraints.md#TECH-3)

---

### UI-2: Область результата
**Элементы**:
- Кнопка «Скачать IFC» (активна после генерации)
- Индикатор прогресса генерации
- Сообщение об успехе/ошибке

**Ссылки**: [[03_features](03_features.md#FR-6)

---

### UI-3: Панель предпросмотра PSet
**Элементы**:
- Дерево: Entity → PSet → Свойства
- Для каждого свойства: имя, тип, cardinality, ограничения
- Кнопка «Сгенерировать IFC»

**Ссылки**: [[03_features](03_features.md#FR-3)

---

### UI-4: Панель логов
**Элементы**:
- Текстовая область с логами
- Разделение по этапам: загрузка → анализ → генерация
- Подсветка ошибок/предупреждений

**Ссылки**: [[03_features](03_features.md#FR-5)

---

## 4.2 Программные интерфейсы

### API-1: Pyodide
**Источник:** `https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide.js`

**Версия:** v0.29.3 (Python 3.13)

**Назначение:** Python runtime в браузере

**Использование:**
- Загрузка через `<script src="https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide.js">`
- Инициализация: `loadPyodide({ indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.29.3/full/' })`
- Установка пакетов: `micropip.install()`

**Почему v0.29.3:**
- v0.27.2 (Python 3.12) — не совместим с wheel ifcopenshell
- **v0.29.3 (Python 3.13, pyodide_2025_0)** — совместим с `ifcopenshell-0.8.4-cp313-cp313-pyodide_2025_0_wasm32.whl`
- dev/full (Python 3.14+) — не совместим с wheel

Закомментированные альтернативы в `pyodide-bridge.js`:
```js
// const PYODIDE_CDN = 'https://cdn.jsdelivr.net/pyodide/v0.27.2/full/';
const PYODIDE_CDN = 'https://cdn.jsdelivr.net/pyodide/v0.29.3/full/';
// const PYODIDE_CDN = 'https://cdn.jsdelivr.net/pyodide/dev/full/';
```

**Ссылки:** [[05_constraints](05_constraints.md#TECH-3)]

---

### API-2: ifcopenshell
**Источник:** `./wheels/ifcopenshell-*.whl` (локальный wheel)

**Назначение:** Создание и валидация IFC файлов

**Использование:**
- `ifcopenshell.file()` — создание IFC файла
- `ifcopenshell.template` — шаблонные структуры
- `ifcopenshell.validate` — валидация структуры

**Ссылки:** [[06_library_structure](06_library_structure.md)], [[07_ifc_mapping](07_ifc_mapping.md)]

---

### API-3: File API браузера
**Назначение:** Работа с локальными файлами

**Использование:**
- Чтение файлов через `FileReader`
- Drag-and-drop через `DataTransfer`
- Создание Blob для скачивания: `URL.createObjectURL(blob)`

**Ссылки:** [[03_features](03_features.md#FR-1)], [[03_features](03_features.md#FR-6)]

---

### API-4: Внутренние Python модули
**Модули:**
- `src/ids_parser.py` — парсинг IDS XML
- `src/pset_generator.py` — генерация IFC4
- `src/validator.py` — валидация IFC
- `src/gherkin_validator.py` — ifc-gherkin-rules (33 категории)

**Загрузка:** Копирование в `/src/` файловую систему Pyodide

**Ссылки:** [[08_data_flow](08_data_flow.md)]
