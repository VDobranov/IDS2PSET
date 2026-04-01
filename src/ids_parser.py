"""IDS Parser module for extracting PSet requirements."""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class PropertyRequirement:
    """Represents a single property requirement from IDS."""
    name: str
    property_set: str
    data_type: str
    cardinality: str
    description: str = ""
    enum_values: List[str] = field(default_factory=list)


@dataclass
class PSetGroup:
    """Represents a grouped PSet with all its properties."""
    name: str
    properties: List[PropertyRequirement] = field(default_factory=list)
    applicable_entities: List[str] = field(default_factory=list)


def parse_ids_file(file_path: str) -> Dict[str, PSetGroup]:
    """
    Parse IDS file and extract PSet requirements grouped by PSet name.
    
    Args:
        file_path: Path to the IDS XML file
        
    Returns:
        Dictionary mapping PSet names to PSetGroup objects
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Handle namespace
    ns = {'ids': 'http://standards.buildingsmart.org/IDS'}
    
    psets: Dict[str, PSetGroup] = {}
    
    # Find all specifications
    specifications = root.findall('.//ids:specification', ns)
    
    for spec in specifications:
        # Get entity from applicability
        entities = []
        applicability = spec.find('ids:applicability', ns)
        if applicability is not None:
            entity_elem = applicability.find('ids:entity', ns)
            if entity_elem is not None:
                name_elem = entity_elem.find('ids:name', ns)
                if name_elem is not None:
                    simple_value = name_elem.find('ids:simpleValue', ns)
                    if simple_value is not None and simple_value.text:
                        entities.append(simple_value.text)
        
        # Get requirements
        requirements = spec.find('ids:requirements', ns)
        if requirements is None:
            continue
            
        for prop in requirements.findall('ids:property', ns):
            # Extract property set name
            prop_set_elem = prop.find('ids:propertySet', ns)
            if prop_set_elem is None:
                continue
            prop_set_name = prop_set_elem.find('ids:simpleValue', ns)
            if prop_set_name is None or not prop_set_name.text:
                continue
            
            pset_name = prop_set_name.text
            
            # Extract base name
            base_name_elem = prop.find('ids:baseName', ns)
            if base_name_elem is None:
                continue
            base_name = base_name_elem.find('ids:simpleValue', ns)
            if base_name is None or not base_name.text:
                continue
            
            # Get attributes
            data_type = prop.get('dataType', 'IFCTEXT')
            cardinality = prop.get('cardinality', 'optional')
            instructions = prop.get('instructions', '')
            
            # Get enum values if present
            enum_values = []
            value_elem = prop.find('ids:value', ns)
            if value_elem is not None:
                restriction = value_elem.find('xs:restriction', {'xs': 'http://www.w3.org/2001/XMLSchema'})
                if restriction is not None:
                    enumerations = restriction.findall('xs:enumeration', {'xs': 'http://www.w3.org/2001/XMLSchema'})
                    for enum in enumerations:
                        enum_val = enum.get('value')
                        if enum_val:
                            enum_values.append(enum_val)
            
            # Create property requirement
            prop_req = PropertyRequirement(
                name=base_name.text,
                property_set=pset_name,
                data_type=data_type,
                cardinality=cardinality,
                description=instructions,
                enum_values=enum_values
            )
            
            # Group by PSet name
            if pset_name not in psets:
                psets[pset_name] = PSetGroup(name=pset_name)
            
            # Add property if not already present
            existing_names = [p.name for p in psets[pset_name].properties]
            if prop_req.name not in existing_names:
                psets[pset_name].properties.append(prop_req)
            
            # Add entities
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ids', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        result = parse_ids_file(temp_path)
    finally:
        os.unlink(temp_path)
    
    return result
