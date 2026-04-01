# 6. Правила анализа IDS

## 6.1 Критерии отнесения к PSet

Требование IDS относится к PSet, если элемент `requirement` содержит:
1. Элемент `propertySet` с `simpleValue` (имя набора свойств)
2. Элемент `baseName` с `simpleValue` (имя свойства)

**Пример XML**:
```xml
<property cardinality="required" dataType="IFCTEXT" 
          instructions="Описание свойства">
  <propertySet><simpleValue>Местоположение</simpleValue></propertySet>
  <baseName><simpleValue>Номер корпуса</simpleValue></baseName>
  <value>
    <xs:restriction base="xs:string">
      <xs:enumeration value="Значение1" />
    </xs:restriction>
  </value>
</property>
```

---

## 6.2 Группировка требований

Группировка выполняется по ключу: **`propertySet Name`**

**Пример из IDS:**
- PSet "Местоположение" (IfcWall + IfcBuilding) → один шаблон
- PSet "Маркировка" → отдельный шаблон
- PSet "Характеристики бетона" → отдельный шаблон

**Внутри группы:**
- Свойства объединяются от всех entity
- `ApplicableEntity` формируется как список уникальных entity

---

## 6.3 Обработка множественных IDS

При загрузке нескольких IDS:
1. Все `specification` объединяются
2. Группировка выполняется по всему набору данных
3. При коллизиях (одинаковые Entity+PSet) — свойства объединяются

---

## 6.4 Обработка enumerations

Если `property/value/xs:enumeration` присутствует:
1. Создаётся `IfcPropertyEnumeration`
2. Имя = `baseName/simpleValue`
3. Значения = список `@value` из `xs:enumeration`
4. `IfcSimplePropertyTemplate.EnumValues` ссылается на enumeration

---

## 6.5 Валидация результата

Сгенерированный IFC должен:
- Содержать валидный `IfcProjectLibrary`
- Иметь корректную структуру `IfcPropertySetTemplate`
- Все `DataType` должны соответствовать таблице маппинга
- Проходить валидацию IFC-валидатором (`ifcopenshell.validate`)

**Ссылки**: [[07_ifc_mapping](07_ifc_mapping.md)

---

## 6.6 Ссылки
- [[03_features](03_features.md#FR-2) — Анализ IDS
- [[03_features](03_features.md#FR-4) — Генерация IFC
- [[07_ifc_mapping](07_ifc_mapping.md) — Маппинг IFC

---
*Версия: 0.2 | Статус: Черновик*
