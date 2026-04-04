"""IDS Parser module for extracting PSet requirements."""

import re
import xml.etree.ElementTree as ET
from typing import Dict, List
from dataclasses import dataclass, field

# Regex-символы, указывающие что simpleValue может содержать регулярное выражение
_REGEX_CHARS = re.compile(r"[.\*\+\?\[\]\(\)\{\}\|\^\$]")


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
        # Проверяем содержит ли simpleValue regex-символы
        # Это может указывать на потенциально некорректный IDS
        has_regex = bool(_REGEX_CHARS.search(simple_value.text))
        return ([simple_value.text], has_regex)

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

    # Get entity names (can be multiple via enumeration)
    name_elem = entity_elem.find("ids:name", ns)
    entity_names = []
    if name_elem is not None:
        entity_names, _ = _extract_values(name_elem, ns, xs_ns)

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


def parse_ids_file(file_path: str) -> Dict[str, PSetGroup]:
    """
    Parse IDS file and extract PSet requirements grouped by PSet name.
    Supports both simpleValue and xs:restriction with xs:pattern.
    Combines PSet with same name but different entities.

    Args:
        file_path: Path to the IDS XML file

    Returns:
        Dictionary mapping PSet names to PSetGroup objects
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Handle namespaces
    ns = {"ids": "http://standards.buildingsmart.org/IDS"}
    xs_ns = {"xs": "http://www.w3.org/2001/XMLSchema"}

    psets: Dict[str, PSetGroup] = {}

    # Find all specifications
    specifications = root.findall(".//ids:specification", ns)

    for spec in specifications:
        # Get entity from applicability with predefined type
        entities = []
        applicability = spec.find("ids:applicability", ns)
        if applicability is not None:
            entity_elem = applicability.find("ids:entity", ns)
            if entity_elem is not None:
                entity_values = _extract_entity_with_type(entity_elem, ns, xs_ns)
                entities.extend(entity_values)

        # Get requirements
        requirements = spec.find("ids:requirements", ns)
        if requirements is None:
            continue

        for prop in requirements.findall("ids:property", ns):
            # Extract property set name
            prop_set_elem = prop.find("ids:propertySet", ns)
            if prop_set_elem is None:
                continue

            pset_values, pset_is_pattern = _extract_values(prop_set_elem, ns, xs_ns)
            if not pset_values:
                continue

            pset_name = pset_values[0]  # Use first value

            # Extract base name
            base_name_elem = prop.find("ids:baseName", ns)
            if base_name_elem is None:
                continue

            base_name_list, base_is_pattern = _extract_values(base_name_elem, ns, xs_ns)
            if not base_name_list:
                continue

            base_name = base_name_list[0]  # Use first value

            # Get attributes
            data_type = prop.get("dataType", "IFCTEXT")
            cardinality = prop.get("cardinality", "optional")
            instructions = prop.get("instructions", "")

            # Get enum values if present
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

            # Create property requirement
            prop_req = PropertyRequirement(
                name=base_name,
                property_set=pset_name,
                data_type=data_type,
                cardinality=cardinality,
                description=instructions,
                enum_values=enum_values,
                template_type="P_SINGLEVALUE",
                is_pattern=base_is_pattern,
                simple_value_pattern=base_is_pattern
                and bool(_REGEX_CHARS.search(base_name)),
            )

            # Group by PSet name
            if pset_name not in psets:
                psets[pset_name] = PSetGroup(
                    name=pset_name,
                    is_pattern=pset_is_pattern,
                    simple_value_pattern=pset_is_pattern
                    and bool(_REGEX_CHARS.search(pset_name)),
                )

            # Add property if not already present
            existing_names = [p.name for p in psets[pset_name].properties]
            if prop_req.name not in existing_names:
                psets[pset_name].properties.append(prop_req)

            # Add/merge entities - combine all entities with comma
            for entity in entities:
                if entity not in psets[pset_name].applicable_entities:
                    psets[pset_name].applicable_entities.append(entity)

    return psets


def parse_ids_content(content: str) -> Dict[str, PSetGroup]:
    """
    Parse IDS content from string.

    Args:
        content: IDS XML content as string

    Returns:
        Dictionary mapping PSet names to PSetGroup objects
    """
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ids", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        temp_path = f.name

    try:
        result = parse_ids_file(temp_path)
    finally:
        os.unlink(temp_path)

    return result
