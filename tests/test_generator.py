"""Tests for IFC PSet Generator module."""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from pset_generator import PSetGenerator, IFCTemplate, IFCTemplateProperty

    IFCSHELL_AVAILABLE = True
except ImportError:
    IFCSHELL_AVAILABLE = False


@pytest.mark.skipif(not IFCSHELL_AVAILABLE, reason="ifcopenshell not available")
class TestIFCTemplateProperty:
    """Tests for IFCTemplateProperty dataclass."""

    def test_create_property_minimal(self):
        """Test creating property with minimal fields."""
        prop = IFCTemplateProperty(name="TestProperty", data_type="IFCTEXT")
        assert prop.name == "TestProperty"
        assert prop.data_type == "IFCTEXT"
        assert prop.description == ""
        assert prop.enum_values == []
        assert prop.cardinality == "optional"

    def test_create_property_full(self):
        """Test creating property with all fields."""
        prop = IFCTemplateProperty(
            name="Material",
            data_type="IFCTEXT",
            description="Material type",
            enum_values=["Steel", "Concrete"],
            cardinality="required",
        )
        assert prop.name == "Material"
        assert prop.description == "Material type"
        assert len(prop.enum_values) == 2
        assert prop.cardinality == "required"


@pytest.mark.skipif(not IFCSHELL_AVAILABLE, reason="ifcopenshell not available")
class TestIFCTemplate:
    """Tests for IFCTemplate dataclass."""

    def test_create_template(self):
        """Test creating a template."""
        prop = IFCTemplateProperty(name="Prop1", data_type="IFCTEXT")
        template = IFCTemplate(
            name="TestPSet", properties=[prop], applicable_entities=["IFCWALL"]
        )
        assert template.name == "TestPSet"
        assert len(template.properties) == 1
        assert "IFCWALL" in template.applicable_entities


@pytest.mark.skipif(not IFCSHELL_AVAILABLE, reason="ifcopenshell not available")
class TestPSetGenerator:
    """Tests for PSetGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = PSetGenerator()

    def test_create_library(self):
        """Test creating IfcProjectLibrary."""
        self.generator.create_library("Test Library")
        assert self.generator.library is not None
        assert self.generator.library.Name == "Test Library"

    def test_create_enumeration(self):
        """Test creating IfcPropertyEnumeration."""
        self.generator.create_library()
        enum = self.generator.create_enumeration("MaterialEnum", ["Steel", "Concrete"])
        assert enum is not None
        assert enum.Name == "MaterialEnum"
        assert len(self.generator.enums) == 1

    def test_create_simple_property_template(self):
        """Test creating IfcSimplePropertyTemplate."""
        self.generator.create_library()
        prop = IFCTemplateProperty(
            name="TestProp", data_type="IFCTEXT", description="Test description"
        )
        template = self.generator.create_simple_property_template(prop)
        assert template is not None
        assert template.Name == "TestProp"
        assert template.PrimaryMeasureType == "IfcText"

    def test_create_simple_property_template_with_enum(self):
        """Test creating property template with enumeration."""
        self.generator.create_library()
        enum = self.generator.create_enumeration("TestEnum", ["A", "B"])
        prop = IFCTemplateProperty(
            name="EnumProp", data_type="IFCTEXT", enum_values=["A", "B"]
        )
        template = self.generator.create_simple_property_template(prop, enum)
        assert template is not None
        assert template.Enumerators is not None

    def test_create_property_set_template(self):
        """Test creating IfcPropertySetTemplate."""
        self.generator.create_library()
        prop = IFCTemplateProperty(name="Prop1", data_type="IFCTEXT")
        template = IFCTemplate(
            name="TestPSet",
            properties=[prop],
            applicable_entities=["IFCWALL", "IFCSLAB"],
        )
        pset_template = self.generator.create_property_set_template(template)
        assert pset_template is not None
        assert pset_template.Name == "TestPSet"
        assert "IFCWALL" in pset_template.ApplicableEntity
        assert "IFCSLAB" in pset_template.ApplicableEntity

    def test_add_template(self):
        """Test adding template to library."""
        self.generator.create_library()
        prop = IFCTemplateProperty(name="Prop1", data_type="IFCTEXT")
        template = IFCTemplate(
            name="TestPSet", properties=[prop], applicable_entities=["IFCWALL"]
        )
        result = self.generator.add_template(template)
        assert result is not None
        assert len(self.generator.templates) == 1

    def test_declare_templates(self):
        """Test creating IfcRelDeclares."""
        self.generator.create_library()
        prop = IFCTemplateProperty(name="Prop1", data_type="IFCTEXT")
        template = IFCTemplate(
            name="TestPSet", properties=[prop], applicable_entities=["IFCWALL"]
        )
        self.generator.add_template(template)
        self.generator.declare_templates()
        # Should not raise exception

    def test_generate_from_dict(self):
        """Test generating IFC from dictionary."""
        psets = {
            "TestPSet": {
                "name": "TestPSet",
                "properties": [
                    {
                        "name": "Property1",
                        "data_type": "IFCTEXT",
                        "description": "Test property",
                        "enum_values": [],
                        "cardinality": "required",
                    }
                ],
                "applicable_entities": ["IFCWALL"],
            }
        }
        result = self.generator.generate(psets)
        assert result is not None
        assert isinstance(result, str)
        assert "IFCPROJECTLIBRARY" in result
        assert "IFCPROPERTYSETTEMPLATE" in result
        assert "TestPSet" in result

    def test_generate_with_enumeration(self):
        """Test generating IFC with enumeration."""
        psets = {
            "MaterialPSet": {
                "name": "MaterialPSet",
                "properties": [
                    {
                        "name": "Material",
                        "data_type": "IFCTEXT",
                        "description": "Material type",
                        "enum_values": ["Steel", "Concrete", "Wood"],
                        "cardinality": "optional",
                    }
                ],
                "applicable_entities": ["IFCBEAM"],
            }
        }
        result = self.generator.generate(psets)
        assert result is not None
        assert "IFCPROPERTYENUMERATION" in result
        assert "Steel" in result

    def test_generate_multiple_psets(self):
        """Test generating IFC with multiple PSets."""
        psets = {
            "PSet1": {
                "name": "PSet1",
                "properties": [
                    {
                        "name": "Prop1",
                        "data_type": "IFCTEXT",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "required",
                    }
                ],
                "applicable_entities": ["IFCWALL"],
            },
            "PSet2": {
                "name": "PSet2",
                "properties": [
                    {
                        "name": "Prop2",
                        "data_type": "IFCREAL",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "optional",
                    }
                ],
                "applicable_entities": ["IFCSLAB"],
            },
        }
        result = self.generator.generate(psets)
        assert result is not None
        assert isinstance(result, str)
        assert "PSet1" in result
        assert "PSet2" in result

    def test_validate_success(self):
        """Test validation with valid IFC."""
        psets = {
            "TestPSet": {
                "name": "TestPSet",
                "properties": [
                    {
                        "name": "Prop1",
                        "data_type": "IFCTEXT",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "required",
                    }
                ],
                "applicable_entities": ["IFCWALL"],
            }
        }
        self.generator.generate(psets)
        result = self.generator.validate()
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_no_file(self):
        """Test validation without generated file."""
        generator = PSetGenerator()
        result = generator.validate()
        assert result["valid"] is False
        assert "No IFC file generated" in result["errors"]

    def test_get_statistics(self):
        """Test getting statistics."""
        psets = {
            "TestPSet": {
                "name": "TestPSet",
                "properties": [
                    {
                        "name": "Prop1",
                        "data_type": "IFCTEXT",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "required",
                    },
                    {
                        "name": "Prop2",
                        "data_type": "IFCREAL",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "optional",
                    },
                ],
                "applicable_entities": ["IFCWALL"],
            }
        }
        self.generator.generate(psets)
        stats = self.generator.get_statistics()
        assert stats["templates"] == 1
        assert stats["enumerations"] == 0
        assert stats["total_properties"] == 2


@pytest.mark.skipif(not IFCSHELL_AVAILABLE, reason="ifcopenshell not available")
class TestDataTypeMapping:
    """Tests for data type mapping."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = PSetGenerator()
        self.generator.create_library()

    def test_map_ifctext(self):
        """Test IFCTEXT mapping."""
        prop = IFCTemplateProperty(name="Test", data_type="IFCTEXT")
        template = self.generator.create_simple_property_template(prop)
        assert template.PrimaryMeasureType == "IfcText"

    def test_map_ifcreal(self):
        """Test IFCREAL mapping."""
        prop = IFCTemplateProperty(name="Test", data_type="IFCREAL")
        template = self.generator.create_simple_property_template(prop)
        assert template.PrimaryMeasureType == "IfcReal"

    def test_map_ifcinteger(self):
        """Test IFCINTEGER mapping."""
        prop = IFCTemplateProperty(name="Test", data_type="IFCINTEGER")
        template = self.generator.create_simple_property_template(prop)
        assert template.PrimaryMeasureType == "IfcInteger"

    def test_map_ifcboolean(self):
        """Test IFCBOOLEAN mapping."""
        prop = IFCTemplateProperty(name="Test", data_type="IFCBOOLEAN")
        template = self.generator.create_simple_property_template(prop)
        assert template.PrimaryMeasureType == "IfcBoolean"


@pytest.mark.skipif(not IFCSHELL_AVAILABLE, reason="ifcopenshell not available")
class TestIntegration:
    """Integration tests."""

    def test_full_generation_workflow(self):
        """Test complete generation workflow."""
        generator = PSetGenerator()

        # Simulate parser output
        psets = {
            "Местоположение": {
                "name": "Местоположение",
                "properties": [
                    {
                        "name": "Номер корпуса",
                        "data_type": "IFCTEXT",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "required",
                    },
                    {
                        "name": "Номер секции",
                        "data_type": "IFCTEXT",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "required",
                    },
                ],
                "applicable_entities": ["IFCWALL", "IFCBUILDING"],
            },
            "Материал": {
                "name": "Материал",
                "properties": [
                    {
                        "name": "Тип",
                        "data_type": "IFCTEXT",
                        "description": "Material type",
                        "enum_values": ["Б", "ЖБ", "К"],
                        "cardinality": "optional",
                    }
                ],
                "applicable_entities": ["IFCWALL"],
            },
        }

        # Generate
        result = generator.generate(psets)

        # Validate
        validation = generator.validate()
        assert validation["valid"] is True

        # Statistics
        stats = generator.get_statistics()
        assert stats["templates"] == 2
        assert stats["enumerations"] == 1  # One enum for Материал

        # Check output (Cyrillic is encoded as \X2\...\X0 in IFC STEP files)
        assert "IFCPROJECTLIBRARY" in result
        assert (
            "\\X2\\041C043504410442043E043F043E043B043E04360435043D04380435\\X0\\"
            in result
        )  # Местоположение
        assert "\\X2\\041C043004420435044004380430043B\\X0\\" in result  # Материал
        assert "IFCWALL" in result
        assert "IFCBUILDING" in result


class TestNegativeCases:
    """Negative tests for edge cases and error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = PSetGenerator()

    @pytest.mark.skipif(not IFCSHELL_AVAILABLE, reason="ifcopenshell not available")
    def test_skip_pattern_property(self):
        """Test that properties with is_pattern=True are skipped."""
        psets = {
            "TestPSet": {
                "name": "TestPSet",
                "properties": [
                    {
                        "name": "ValidProp",
                        "data_type": "IFCTEXT",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "required",
                        "is_pattern": False,
                    },
                    {
                        "name": "PatternProp",
                        "data_type": "IFCTEXT",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "optional",
                        "is_pattern": True,
                    },
                ],
                "applicable_entities": ["IFCWALL"],
            }
        }
        result = self.generator.generate(psets)
        assert result is not None
        assert "ValidProp" in result
        assert "PatternProp" not in result

    @pytest.mark.skipif(not IFCSHELL_AVAILABLE, reason="ifcopenshell not available")
    def test_skip_pset_pattern(self):
        """Test that PSets with is_pattern=True are skipped."""
        psets = {
            "ValidPSet": {
                "name": "ValidPSet",
                "properties": [
                    {
                        "name": "Prop1",
                        "data_type": "IFCTEXT",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "required",
                        "is_pattern": False,
                    }
                ],
                "applicable_entities": ["IFCWALL"],
                "is_pattern": False,
            },
            ".*Pattern.*": {
                "name": ".*Pattern.*",
                "properties": [
                    {
                        "name": "Prop2",
                        "data_type": "IFCTEXT",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "optional",
                        "is_pattern": False,
                    }
                ],
                "applicable_entities": ["IFCSLAB"],
                "is_pattern": True,
            },
        }
        result = self.generator.generate(psets)
        assert "ValidPSet" in result
        assert ".*Pattern.*" not in result

    @pytest.mark.skipif(not IFCSHELL_AVAILABLE, reason="ifcopenshell not available")
    def test_empty_properties_list(self):
        """Test generating PSet with no properties creates empty template."""
        psets = {
            "EmptyPSet": {
                "name": "EmptyPSet",
                "properties": [],
                "applicable_entities": ["IFCWALL"],
            }
        }
        result = self.generator.generate(psets)
        assert result is not None
        assert "EmptyPSet" in result

    @pytest.mark.skipif(not IFCSHELL_AVAILABLE, reason="ifcopenshell not available")
    def test_invalid_entity_name(self):
        """Test generating with invalid entity name."""
        psets = {
            "TestPSet": {
                "name": "TestPSet",
                "properties": [
                    {
                        "name": "Prop1",
                        "data_type": "IFCTEXT",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "required",
                        "is_pattern": False,
                    }
                ],
                "applicable_entities": ["IFCFAKEENTITY"],
            }
        }
        result = self.generator.generate(psets)
        assert result is not None
        assert "IFCFAKEENTITY" in result

    @pytest.mark.skipif(not IFCSHELL_AVAILABLE, reason="ifcopenshell not available")
    def test_single_property_pset(self):
        """Test PSet with single property."""
        psets = {
            "SinglePSet": {
                "name": "SinglePSet",
                "properties": [
                    {
                        "name": "OnlyProp",
                        "data_type": "IFCINTEGER",
                        "description": "Just one property",
                        "enum_values": [],
                        "cardinality": "required",
                    }
                ],
                "applicable_entities": ["IFCCOLUMN", "IFCBEAM"],
            }
        }
        result = self.generator.generate(psets)
        assert result is not None
        assert "SinglePSet" in result
        assert "OnlyProp" in result
        assert "IFCCOLUMN" in result
        assert "IFCBEAM" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=pset_generator", "--cov-report=term-missing"])
