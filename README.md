# IDS2PSET

Генератор библиотек свойств IFC на основе IDS спецификаций.

## Установка

```bash
# Создание виртуального окружения
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Установка зависимостей
pip install -r requirements.txt

# Установка pre-commit хуков
pip install pre-commit
pre-commit install
```

## Запуск тестов

```bash
# Python тесты
pytest tests/test.py -v --cov=src --cov-report=term-missing

# JS тесты
node --test tests/test.js

# Все тесты
npm test  # или ./run_tests.sh
```

## Структура проекта

```
IDS2PSET/
├── index.html          # Главная страница
├── css/style.css       # Стили
├── js/
│   ├── app.js          # Логика приложения
│   └── pyodide-bridge.js  # Связь с Python
├── src/
│   └── ids_parser.py   # Парсинг IDS
├── tests/
│   ├── test.py         # Python тесты
│   ├── test.js         # JS тесты
│   └── fixtures/       # Тестовые данные
└── docs/SRS/           # Спецификация
```

## Документация

- [SRS документация](docs/SRS/01_introduction.md)
- [План реализации](docs/SRS/11_implementation_plan.md)

## Лицензия

MIT
