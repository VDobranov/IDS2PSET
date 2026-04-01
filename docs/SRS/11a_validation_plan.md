# 11a. План валидации

**Назначение:** Детали валидации IFC. Общий статус этапа 7 см. в [11_implementation_plan.md](11_implementation_plan.md).

---

## Инструменты

### ifcopenshell.validate

Базовая проверка структуры IFC:
- Наличие `IfcProjectLibrary`, `IfcPropertySetTemplate`, `IfcRelDeclares`
- Атрибуты сущностей (Name, TemplateType)

### ifc-gherkin-rules

Проверка по правилам buildingSMART (33 категории):
```
ALB, ALS, ANN, ASM, AXG, BBX, BLT, BRP, CLS, CTX,
GDP, GEM, GRF, GRP, IFC, LAY, LIP, LOP, MAT, MPD,
OJP, OJT, PSE, PJS, POR, QTY, SPA, SPS, SWE, SYS,
TAS, VER, VRT
```
**PSE002:** имена PSet не должны начинаться с 'pset'

---

## Реализация

| Файл | Назначение |
|------|------------|
| src/validator.py | Базовая валидация (ifcopenshell) |
| src/gherkin_validator.py | 33 категории gherkin-rules |
| vendor/ifc-gherkin-rules | Git submodule (buildingSMART) |

---

## Тесты

### tests/test_validator.py (10 тестов)

test_validator_creation, test_validate_generated_ifc, test_validate_empty_ifc, test_validate_with_enumeration, test_validate_multiple_psets, test_get_summary, test_validate_ifc_project_library_exists, test_validate_property_templates_have_names, test_full_workflow_with_validation, test_real_ids_file_validation

### tests/test_gherkin.py (7 тестов)

test_validator_creation, test_validate_generated_ifc, test_validate_all_rules, test_get_summary, test_full_workflow_with_gherkin, test_real_ids_with_gherkin

---

## CI/CD

**Pre-commit:** `pytest tests/ -v`

**GitHub Actions:** `pytest tests/ -v --cov=src --cov-fail-under=90`

---

## Ссылки

- [[11_implementation_plan](11_implementation_plan.md) — Общий план
- [[10a_tdd](10a_tdd.md) — TDD
- [ifc-gherkin-rules](https://buildingsmart.github.io/ifc-gherkin-rules/branches/main/features/index.html)

---
*Версия: 0.5 | Статус: Этап 7 выполнен ✅*
