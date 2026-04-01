# 12. Pre-commit хуки и CI/CD

## 12.1 Pre-commit хуки

**Цель:** Автоматическая проверка кода перед коммитом

**Состав хуков:**

### Python
- `black` — форматирование кода
- `flake8` — линтинг (PEP8)
- `pytest` — запуск тестов
- `mypy` — проверка типов (опционально)

### JavaScript
- `eslint` — линтинг
- `prettier` — форматирование
- `node --test` — запуск JS тестов

### Общие
- `check-merge-conflict` — проверка конфликтов слияния
- `check-added-large-files` — запрет больших файлов (>1MB)
- `trailing-whitespace` — удаление пробелов в конце строк

**Конфигурация:** `.pre-commit-config.yaml`

**Установка:**
```bash
pip install pre-commit
pre-commit install
```

---

## 12.2 CI/CD тестирование

**Платформа:** GitHub Actions

**Рабочий процесс:** `.github/workflows/test.yml`

### Триггеры
- `push` на `main`
- `pull_request` на `main`

### Задачи (Jobs)

#### 1. Python тесты
```yaml
- Python 3.11, 3.12, 3.13
- Установка зависимостей
- Запуск pytest с coverage
- Покрытие ≥100%
```

#### 2. JS тесты
```yaml
- Node.js 18+
- Запуск node --test
- Все тесты должны проходить
```

#### 3. Валидация IFC (в тестах)
```yaml
- ifcopenshell.validate
- ifc-gherkin-rules
- Блокировка при ошибках
```

### Статусы
- ✅ Все тесты прошли
- ❌ Тесты не прошли (блокировка merge)

---

## 12.3 Покрытие кода

**Требование:** 100% покрытие Python и JS кода

**Инструменты:**
- Python: `pytest-cov`
- JS: встроенный coverage в `node --test`

**Отчёт:** HTML отчёт в артефактах CI

---

## 12.4 Ссылки
- [[10_technical_decisions](10_technical_decisions.md) — Технические решения
- [[10a_tdd](10a_tdd.md) — TDD и валидация
- [[11_implementation_plan](11_implementation_plan.md) — План реализации

---
*Версия: 0.1 | Статус: Черновик*
