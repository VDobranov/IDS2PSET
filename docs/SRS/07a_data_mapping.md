# 7a. Таблицы маппинга данных

## 7a.1 Элементы IDS → IFC4

| Элемент IDS | IFC4 | Примечание |
|-------------|------|------------|
| `specification` | — | не создаёт объектов IFC |
| `entity/name/simpleValue` | `ApplicableEntity` | список entity PSet |
| `propertySet/simpleValue` | `IfcPropertySetTemplate.Name` | имя PSet (ключ группировки) |
| `property` | `IfcSimplePropertyTemplate` | свойство |
| `baseName/simpleValue` | `Name` | имя свойства |
| `@instructions` | `Description` | описание |
| `@dataType` | `DataType` | см. таблицу ниже |
| `@cardinality` | — | не используется |
| `value/xs:enumeration` | `IfcPropertyEnumeration` | список значений |

---

## 7a.2 Типы данных IDS → IFC

| IDS dataType | IFC тип | Пример |
|--------------|---------|--------|
| IFCTEXT | `IfcText` | `"Стена"` |
| IFCINTEGER | `IfcInteger` | `5` |
| IFCREAL | `IfcReal` | `3.14` |
| IFCBOOLEAN | `IfcBoolean` | `.T.` / `.F.` |
| IFCLENGTHMEASURE | `IfcLengthMeasure` | `3000.0` |
| IFCVOLUMEMEASURE | `IfcVolumeMeasure` | `27.0` |

---

## 7a.3 Cardinality IDS → IFC

| IDS | IFC |
|-----|-----|
| `required` | `"1"` |
| `optional` | `"0..1"` |

---

## 7a.4 TemplateType

Всегда `.PSET_TYPEDRIVENOVERRIDE.` для PSet из IDS.

**Ссылки**: [IfcPropertySetTemplateTypeEnum](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/lexical/IfcPropertySetTemplateTypeEnum.htm)

---

## 7a.5 IfcRelDeclares

Для связи `IfcPropertySetTemplate` с `IfcProjectLibrary`:

```python
library.create_entity("IfcRelDeclares",
    RelatingContext=project,
    RelatedDefinitions=[pset_template1, ...]
)
```

**Ссылки**: [IfcRelDeclares](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/lexical/IfcRelDeclares.htm)

---

## 7a.6 Ссылки
- [[07_ifc_mapping](07_ifc_mapping.md) — Структуры IFC
- [[06_rules](06_rules.md) — Правила анализа

---
*Версия: 0.1 | Статус: Черновик*
