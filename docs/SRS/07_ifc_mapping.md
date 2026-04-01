# 7. Маппинг IDS → IFC4

## 7.1 IfcPropertySetTemplate

**Пример из IFC:**
```express
#1=IFCPROPERTYSETTEMPLATE('0BZ7_BN9n3tvRCrtasImjo',$,
  'Местоположение','',.PSET_TYPEDRIVENOVERRIDE.,
  'IfcObject,IfcTypeObject',(#4,#2,#3));
```

**Параметры создания:**
| Параметр | Источник |
|----------|----------|
| `GlobalId` | UUID |
| `Name` | `propertySet/simpleValue` |
| `Description` | `$` (пусто) |
| `TemplateType` | `.PSET_TYPEDRIVENOVERRIDE.` |
| `ApplicableEntity` | все entity из требований PSet |
| `HasPropertyTemplates` | список свойств PSet |

**Ссылки**: 
- [IFC4 — IfcPropertySetTemplate](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/lexical/IfcPropertySetTemplate.htm)
- [[13_references](13_references.md) — Справочные материалы

---

## 7.2 IfcSimplePropertyTemplate

**Пример:**
```express
#2=IFCSIMPLEPROPERTYTEMPLATE('1ACgjThqHDpw89UMxZkdyv',$,
  'Номер корпуса','',.P_SINGLEVALUE.,
  'IfcText',$,$,$,$,$,.READWRITE.);
```

**Параметры:**
| Параметр | Источник |
|----------|----------|
| `Name` | `baseName/simpleValue` |
| `Description` | `property/@instructions` |
| `DataType` | `property/@dataType` → маппинг |
| `EnumValues` | `#...` или `$` |
| `Usage` | `.READWRITE.` |

**Ссылки**: [IFC4 — IfcSimplePropertyTemplate](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/lexical/IfcSimplePropertyTemplate.htm)

---

## 7.3 IfcPropertyEnumeration

**Пример:**
```express
#14=IFCPROPERTYENUMERATION('Материал',
  (IFCTEXT('Д'),IFCTEXT('С'),IFCTEXT('Б'),...),$);
```

**Создаётся если:** `property/value/xs:enumeration` присутствует

**Ссылки**: [IFC4 — IfcPropertyEnumeration](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/lexical/IfcPropertyEnumeration.htm)

---

## 7.4 IfcProjectLibrary

**Пример создания:**
```python
library = ifcopenshell.file(schema="IFC4")
project = library.create_entity("IfcProjectLibrary", Name="IDS2PSET Library")
```

**Атрибуты:** `Name`, `LongDescription` (опционально)

**Ссылки**: [IFC4 — IfcProjectLibrary](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/lexical/IfcProjectLibrary.htm)

---

## 7.5 Ссылки
- [[07a_data_mapping](07a_data_mapping.md) — Таблицы маппинга
- [[03_features](03_features.md#FR-4) — Генерация IFC
- [[06_rules](06_rules.md) — Правила анализа

---
*Версия: 0.4 | Статус: Черновик*
