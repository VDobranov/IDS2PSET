# 1. Введение

## 1.1 Назначение документа
Описание требований к системе **IDS2PSET** — инструменту генерации IFC-библиотек свойств на основе IDS-спецификаций.

## 1.2 Назначение системы
**IDS2PSET** — бессерверное веб-приложение, которое:
- Принимает на вход валидные файлы IDS (Information Delivery Specification)
- Анализирует требования IDS, относящиеся к свойствам объектов
- Генерирует IFC-файл с объектами `IfcPropertySetTemplate` в рамках `IfcProjectLibrary`
- Предоставляет результат пользователю для скачивания

## 1.3 Область применения
Система используется в процессе BIM-проектирования для автоматизации создания библиотек свойств, обеспечивающих выполнение требований IDS.

## 1.4 Определения и аббревиатуры
| Термин | Определение |
|--------|-------------|
| IDS | Information Delivery Specification — спецификация передачи информации |
| IFC | Industry Foundation Classes — формат данных для BIM |
| PSet | Property Set — набор свойств объекта |
| BIM | Building Information Modeling |
| САПР | Система автоматизированного проектирования |

## 1.5 Ссылки на документы
- [[02_overview](02_overview.md) — Общее описание системы
- [[03_features](03_features.md) — Функциональные требования
- [[04_interfaces](04_interfaces.md) — Интерфейсы
- [[05_constraints](05_constraints.md) — Ограничения
- [[06_rules](06_rules.md) — Правила анализа IDS
- [[07_ifc_mapping](07_ifc_mapping.md) — Маппинг IFC4
- [[07a_data_mapping](07a_data_mapping.md) — Таблицы маппинга
- [[08_ui_mockups](08_ui_mockups.md) — Мокапы интерфейса
- [[08a_result_mockups](08a_result_mockups.md) — Мокапы результата
- [[09_use_cases](09_use_cases.md) — Сценарии использования
- [[09a_download_uses](09a_download_uses.md) — Сценарии скачивания
- [[10_technical_decisions](10_technical_decisions.md) — Технические решения
- [[10a_tdd](10a_tdd.md) — TDD и валидация
- [[11_implementation_plan](11_implementation_plan.md) — План реализации (этапы 1-6)
- [[11a_validation_plan](11a_validation_plan.md) — План реализации (этапы 6b-8)
- [[12_precommit_ci](12_precommit_ci.md) — Pre-commit хуки и CI/CD
- [[13_references](13_references.md) — Справочные материалы

---
*Версия: 0.6 | Статус: Черновик*
