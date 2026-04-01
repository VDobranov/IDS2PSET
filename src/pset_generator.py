"""IFC PSet Generator module for creating IFC property set libraries.

Спецификация IFC4:
- IfcSimplePropertyTemplate: https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifckernel/lexical/ifcsimplepropertytemplate.htm
- IfcPropertyTemplate: https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifckernel/lexical/ifcpropertytemplate.htm
"""

import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

try:
    import ifcopenshell
except ImportError:
    ifcopenshell = None


@dataclass
class IFCTemplateProperty:
    """Represents a property template for IFC."""
    name: str
    data_type: str
    description: str = ""
    enum_values: List[str] = field(default_factory=list)
    cardinality: str = "optional"


@dataclass
class IFCTemplate:
    """Represents an IFC property set template."""
    name: str
    properties: List[IFCTemplateProperty]
    applicable_entities: List[str]
    template_type: str = "PSET_TYPEDRIVENOVERRIDE"


class PSetGenerator:
    """Generator for IFC property set templates."""

    DATA_TYPE_MAP = {
        'IFCTEXT': 'IfcText',
        'IFCINTEGER': 'IfcInteger',
        'IFCREAL': 'IfcReal',
        'IFCBOOLEAN': 'IfcBoolean',
        'IFCLENGTHMEASURE': 'IfcLengthMeasure',
        'IFCVOLUMEMEASURE': 'IfcVolumeMeasure',
    }

    def __init__(self):
        if ifcopenshell is None:
            raise ImportError("ifcopenshell is required. Install it first.")
        self.file = None
        self.library = None
        self.templates = []
        self.enums = []

    def create_library(self, name: str = "IDS2PSET Library") -> None:
        """Create a new IfcProjectLibrary."""
        self.file = ifcopenshell.file(schema="IFC4")
        self.library = self.file.create_entity("IfcProjectLibrary", Name=name)
        self.templates = []
        self.enums = []

    def create_enumeration(self, name: str, values: List[str]) -> Any:
        """Create an IfcPropertyEnumeration."""
        enum_values = [self.file.create_entity("IfcText", v) for v in values]

        enumeration = self.file.create_entity(
            "IfcPropertyEnumeration",
            Name=name,
            EnumerationValues=enum_values
        )
        self.enums.append(enumeration)
        return enumeration

    def create_simple_property_template(
        self,
        prop: IFCTemplateProperty,
        enumeration: Optional[Any] = None
    ) -> Any:
        """Create an IfcSimplePropertyTemplate.
        
        IFC4 attributes (8 own + 4 inherited from IfcRoot = 12 total):
        Inherited:
          - GlobalId, OwnerHistory, Name, Description
        Own:
          - TemplateType: IfcSimplePropertyTemplateTypeEnum
          - PrimaryMeasureType: IfcLabel (аналог DataType)
          - SecondaryMeasureType: IfcLabel
          - Enumerators: IfcPropertyEnumeration (ссылка на EnumValues)
          - PrimaryUnit: IfcUnit
          - SecondaryUnit: IfcUnit
          - Expression: IfcLabel
          - AccessState: IfcStateEnum
        """
        ifc_type = self.DATA_TYPE_MAP.get(prop.data_type, 'IfcText')
        primitive_type = 'P_ENUMERATEDVALUE' if (prop.enum_values or enumeration) else 'P_SINGLEVALUE'

        template = self.file.create_entity(
            "IfcSimplePropertyTemplate",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=None,
            Name=prop.name,
            Description=prop.description if prop.description else None,
            TemplateType=primitive_type,
            PrimaryMeasureType=ifc_type,  # Аналог DataType в IDS
            SecondaryMeasureType=None,
            Enumerators=enumeration if enumeration else None,
            PrimaryUnit=None,
            SecondaryUnit=None,
            Expression=None,
            AccessState='READWRITE'
        )
        return template

    def create_property_set_template(self, template: IFCTemplate) -> Any:
        """Create an IfcPropertySetTemplate."""
        property_templates = []
        for prop in template.properties:
            enumeration = None
            if prop.enum_values:
                enumeration = self.create_enumeration(prop.name, prop.enum_values)
            prop_template = self.create_simple_property_template(prop, enumeration)
            property_templates.append(prop_template)

        applicable_entity_str = ','.join(template.applicable_entities)

        pset_template = self.file.create_entity(
            "IfcPropertySetTemplate",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=None,
            Name=template.name,
            Description=None,
            TemplateType=template.template_type,
            ApplicableEntity=applicable_entity_str,
            HasPropertyTemplates=property_templates
        )
        return pset_template

    def add_template(self, template: IFCTemplate) -> Any:
        """Add a property set template to the library."""
        pset_template = self.create_property_set_template(template)
        self.templates.append(pset_template)
        return pset_template

    def declare_templates(self) -> None:
        """Create IfcRelDeclares to associate templates with library."""
        if not self.templates:
            return

        self.file.create_entity(
            "IfcRelDeclares",
            RelatingContext=self.library,
            RelatedDefinitions=self.templates
        )

    def generate(self, psets: Dict[str, Any]) -> str:
        """Generate complete IFC file from PSet data."""
        self.create_library("IDS2PSET Library")

        for name, pset_data in psets.items():
            properties = []
            for prop in pset_data['properties']:
                ifc_prop = IFCTemplateProperty(
                    name=prop['name'],
                    data_type=prop['data_type'],
                    description=prop.get('description', ''),
                    enum_values=prop.get('enum_values', []),
                    cardinality=prop.get('cardinality', 'optional')
                )
                properties.append(ifc_prop)

            template = IFCTemplate(
                name=name,
                properties=properties,
                applicable_entities=pset_data['applicable_entities']
            )
            self.add_template(template)

        self.declare_templates()

        return self.file.to_string()

    def validate(self) -> Dict[str, Any]:
        """Validate the generated IFC file."""
        if self.file is None:
            return {'valid': False, 'errors': ['No IFC file generated']}

        errors = []

        try:
            if not self.library:
                errors.append('No IfcProjectLibrary found')

            if not self.templates:
                errors.append('No IfcPropertySetTemplate found')

        except Exception as e:
            errors.append(str(e))

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'template_count': len(self.templates),
            'enum_count': len(self.enums)
        }

    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about generated IFC."""
        return {
            'templates': len(self.templates),
            'enumerations': len(self.enums),
            'total_properties': sum(
                len(getattr(t, 'HasPropertyTemplates', []))
                for t in self.templates
            )
        }
