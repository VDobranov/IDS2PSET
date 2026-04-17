"""IDS Parser module for extracting PSet requirements."""

import xml.etree.ElementTree as ET
from typing import Dict, List
from dataclasses import dataclass, field

import entities
from entities import validate_entities, is_regex_like

# Re-export for backward compatibility
_VALID_IFC_ENTITIES = entities._VALID_IFC_ENTITIES
_REGEX_PATTERNS = entities._REGEX_PATTERNS


def _is_regex_like(text):
    """Проверяет, содержит ли текст паттерны, характерные для regex."""
    return is_regex_like(text)


@dataclass
class PropertyRequirement:
    """Represents a single property requirement from IDS."""

    name: str
    property_set: str
    data_type: str
    cardinality: str
    description: str = ""
    enum_values: List[str] = field(default_factory=list)
    template_type: str = "P_SINGLEVALUE"
    is_pattern: bool = False  # True если имя свойства задано regex
    simple_value_pattern: bool = (
        False  # True если regex в simpleValue (потенциально некорректный IDS)
    )


@dataclass
class PSetGroup:
    """Represents a grouped PSet with all its properties."""

    name: str
    properties: List[PropertyRequirement] = field(default_factory=list)
    applicable_entities: List[str] = field(default_factory=list)
    is_pattern: bool = False  # True если имя PSet задано regex
    simple_value_pattern: bool = (
        False  # True если regex в simpleValue (потенциально некорректный IDS)
    )
    entity_warning: bool = False  # True если entity не удалось однозначно определить
    invalid_entities: List[str] = field(
        default_factory=list
    )  # Сущности, не найденные в IFC4


def _validate_entities(entities: List[str]) -> List[str]:
    """Проверяет сущности на валидность (существуют ли в IFC4).

    Returns список невалидных сущностей.
    """
    return validate_entities(entities)


def _extract_entity_names(elem, ns, xs_ns):
    """Extract entity names from ids:name element.

    Handles:
    - simpleValue: direct value
    - xs:restriction with xs:enumeration: multiple values
    - xs:restriction with xs:pattern: split by | for alternatives

    Returns tuple: (names, has_warning) where has_warning is True if entity
    could not be unambiguously determined.
    """
    if elem is None:
        return ([], False)

    # Try simpleValue first
    simple_value = elem.find("ids:simpleValue", ns)
    if simple_value is not None and simple_value.text:
        return ([simple_value.text], False)

    # Try xs:restriction
    restriction = elem.find("xs:restriction", xs_ns)
    if restriction is not None:
        # Try xs:enumeration
        enumerations = restriction.findall("xs:enumeration", xs_ns)
        if enumerations:
            values = [e.get("value") for e in enumerations if e.get("value")]
            return (values, False)

        # Try xs:pattern — split by | for alternative entity types
        pattern = restriction.find("xs:pattern", xs_ns)
        if pattern is not None:
            pattern_value = pattern.get("value")
            if pattern_value:
                # Split by | to get individual entity types
                entities = [e.strip() for e in pattern_value.split("|") if e.strip()]
                if entities:
                    return (entities, False)
                else:
                    return ([pattern_value], True)  # Could not parse

    return ([], True)  # Could not determine entity


def _extract_values(elem, ns, xs_ns):
    """Extract all values from simpleValue or xs:restriction with xs:enumeration.

    Returns tuple: (values, has_pattern) where has_pattern is True if xs:pattern was found.
    """
    if elem is None:
        return ([], False)

    values = []

    # Try simpleValue first
    simple_value = elem.find("ids:simpleValue", ns)
    if simple_value is not None and simple_value.text:
        # simpleValue всегда валиден для IFC, даже если содержит regex-символы
        return ([simple_value.text], False)

    # Try xs:restriction with xs:enumeration
    restriction = elem.find("xs:restriction", xs_ns)
    if restriction is not None:
        enumerations = restriction.findall("xs:enumeration", xs_ns)
        for enum in enumerations:
            enum_val = enum.get("value")
            if enum_val:
                values.append(enum_val)

        # Also try xs:pattern if no enumerations
        if not values:
            pattern = restriction.find("xs:pattern", xs_ns)
            if pattern is not None:
                pattern_value = pattern.get("value")
                if pattern_value:
                    return ([pattern_value], True)  # has_pattern = True

    return (values, False)


def _extract_entity_with_type(entity_elem, ns, xs_ns):
    """Extract entity name with optional predefined type.

    Returns list of all combinations of entity name and predefined type.
    For example, if entity has 2 names and 2 predefined types, returns 4 combinations.
    """
    if entity_elem is None:
        return []

    # Get entity names using new parser
    entity_names, _ = _extract_entity_names(entity_elem.find("ids:name", ns), ns, xs_ns)

    # Get predefined types (can be multiple via enumeration)
    predefined_type_elem = entity_elem.find("ids:predefinedType", ns)
    predefined_types = []
    if predefined_type_elem is not None:
        predefined_types, _ = _extract_values(predefined_type_elem, ns, xs_ns)

    # Generate all combinations
    result = []
    if entity_names:
        if predefined_types:
            # All combinations of entity name + predefined type
            for name in entity_names:
                for ptype in predefined_types:
                    result.append(f"{name}/{ptype}")
        else:
            # Just entity names without predefined type
            result = entity_names

    return result


def _parse_ids_root(root) -> Dict[str, PSetGroup]:
    """
    Parse IDS XML root element and extract PSet requirements grouped by PSet name.
    Supports both simpleValue and xs:restriction with xs:pattern.
    Combines PSet with same name but different entities.

    Args:
        root: XML root element (ET.Element)

    Returns:
        Dictionary mapping PSet names to PSetGroup objects
    """
    ns = {"ids": "http://standards.buildingsmart.org/IDS"}
    xs_ns = {"xs": "http://www.w3.org/2001/XMLSchema"}

    psets: Dict[str, PSetGroup] = {}

    specifications = root.findall(".//ids:specification", ns)

    for spec in specifications:
        entities = []
        entity_warning = False

        # Try ids:applicability first
        applicability = spec.find("ids:applicability", ns)
        if applicability is not None:
            entity_elem = applicability.find("ids:entity", ns)
            if entity_elem is not None:
                entity_values = _extract_entity_with_type(entity_elem, ns, xs_ns)
                if not entity_values:
                    entity_warning = True
                entities.extend(entity_values)
            else:
                entity_warning = True

        # Also try ids:requirements (some IDS put entity there)
        requirements = spec.find("ids:requirements", ns)
        if requirements is not None:
            entity_elem = requirements.find("ids:entity", ns)
            if entity_elem is not None:
                entity_values = _extract_entity_with_type(entity_elem, ns, xs_ns)
                if not entity_values:
                    entity_warning = True
                entities.extend(entity_values)

        if requirements is None:
            continue

        for prop in requirements.findall("ids:property", ns):
            prop_set_elem = prop.find("ids:propertySet", ns)
            if prop_set_elem is None:
                continue

            pset_values, pset_is_pattern = _extract_values(prop_set_elem, ns, xs_ns)
            if not pset_values:
                continue

            pset_name = pset_values[0]
            pset_has_simple_value_regex = _is_regex_like(pset_name)

            base_name_elem = prop.find("ids:baseName", ns)
            if base_name_elem is None:
                continue

            base_name_list, base_is_pattern = _extract_values(base_name_elem, ns, xs_ns)
            if not base_name_list:
                continue

            base_name = base_name_list[0]
            prop_has_simple_value_regex = _is_regex_like(base_name)

            data_type = prop.get("dataType", "IFCTEXT")
            cardinality = prop.get("cardinality", "optional")
            instructions = prop.get("instructions", "")

            enum_values = []
            value_elem = prop.find("ids:value", ns)
            if value_elem is not None:
                restriction = value_elem.find("xs:restriction", xs_ns)
                if restriction is not None:
                    enumerations = restriction.findall("xs:enumeration", xs_ns)
                    for enum in enumerations:
                        enum_val = enum.get("value")
                        if enum_val:
                            enum_values.append(enum_val)

            prop_req = PropertyRequirement(
                name=base_name,
                property_set=pset_name,
                data_type=data_type,
                cardinality=cardinality,
                description=instructions,
                enum_values=enum_values,
                template_type="P_SINGLEVALUE",
                is_pattern=base_is_pattern,
                simple_value_pattern=prop_has_simple_value_regex,
            )

            if pset_name not in psets:
                psets[pset_name] = PSetGroup(
                    name=pset_name,
                    is_pattern=pset_is_pattern,
                    simple_value_pattern=pset_has_simple_value_regex,
                    entity_warning=entity_warning,
                )
            elif entity_warning:
                psets[pset_name].entity_warning = True

            existing_names = [p.name for p in psets[pset_name].properties]
            if prop_req.name not in existing_names:
                psets[pset_name].properties.append(prop_req)

            for entity in entities:
                if entity not in psets[pset_name].applicable_entities:
                    psets[pset_name].applicable_entities.append(entity)

    # Validate entities once after all specifications are processed
    for pset in psets.values():
        pset.invalid_entities = _validate_entities(pset.applicable_entities)

    return psets


def parse_ids_file(file_path: str) -> Dict[str, PSetGroup]:
    """
    Parse IDS file and extract PSet requirements grouped by PSet name.

    Args:
        file_path: Path to the IDS XML file

    Returns:
        Dictionary mapping PSet names to PSetGroup objects
    """
    root = ET.parse(file_path).getroot()
    return _parse_ids_root(root)


def parse_ids_content(content: str) -> Dict[str, PSetGroup]:
    """
    Parse IDS content from string.

    Args:
        content: IDS XML content as string

    Returns:
        Dictionary mapping PSet names to PSetGroup objects
    """
    root = ET.fromstring(content)
    return _parse_ids_root(root)
