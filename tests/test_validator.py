"""Tests for IFC Validator module."""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from validator import IFCValidator

    IFCSHELL_AVAILABLE = True
except ImportError:
    IFCSHELL_AVAILABLE = False


@pytest.mark.skipif(not IFCSHELL_AVAILABLE, reason="ifcopenshell not available")
class TestIFCValidator:
    """Tests for IFCValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = IFCValidator()

    def test_validator_creation(self):
        """Test creating validator."""
        assert self.validator is not None
        assert self.validator.errors == []
        assert self.validator.warnings == []

    def test_validate_requires_ifcopenshell(self):
        """Test that IFCValidator raises ImportError when ifcopenshell is unavailable."""
        import importlib.util

        original_ifcopenshell = sys.modules.get("ifcopenshell")
        try:
            sys.modules["ifcopenshell"] = None  # type: ignore[assignment]
            spec = importlib.util.spec_from_file_location(
                "validator_no_ifc",
                os.path.join(os.path.dirname(__file__), "..", "src", "validator.py"),
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            with pytest.raises(ImportError):
                mod.IFCValidator()
        finally:
            if original_ifcopenshell is not None:
                sys.modules["ifcopenshell"] = original_ifcopenshell
            else:
                sys.modules.pop("ifcopenshell", None)

    def test_validate_generated_ifc(self):
        """Test validation of generated IFC."""
        from pset_generator import PSetGenerator

        generator = PSetGenerator()
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

        generator.generate(psets)
        ifc_content = generator.generate(psets)

        result = self.validator.validate_string(ifc_content)

        assert result["valid"] is True
        assert result["error_count"] == 0

    def test_validate_empty_ifc(self):
        """Test validation of minimal IFC."""
        from pset_generator import PSetGenerator

        generator = PSetGenerator()
        generator.create_library()
        ifc_content = generator.file.to_string()

        result = self.validator.validate_string(ifc_content)

        # Should have warnings for missing entities
        assert len(result["warnings"]) > 0
        assert "No IfcRelDeclares found" in result["warnings"]

    def test_validate_with_enumeration(self):
        """Test validation of IFC with enumeration."""
        from pset_generator import PSetGenerator

        generator = PSetGenerator()
        psets = {
            "MaterialPSet": {
                "name": "MaterialPSet",
                "properties": [
                    {
                        "name": "Material",
                        "data_type": "IFCTEXT",
                        "description": "Material type",
                        "enum_values": ["Steel", "Concrete"],
                        "cardinality": "optional",
                    }
                ],
                "applicable_entities": ["IFCBEAM"],
            }
        }

        ifc_content = generator.generate(psets)
        result = self.validator.validate_string(ifc_content)

        assert result["valid"] is True
        assert result["error_count"] == 0

    def test_validate_multiple_psets(self):
        """Test validation of IFC with multiple PSets."""
        from pset_generator import PSetGenerator

        generator = PSetGenerator()
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

        ifc_content = generator.generate(psets)
        result = self.validator.validate_string(ifc_content)

        assert result["valid"] is True
        assert result["error_count"] == 0

    def test_get_summary(self):
        """Test validation summary."""
        self.validator.errors = ["Error 1", "Error 2"]
        self.validator.warnings = ["Warning 1"]

        summary = self.validator.get_summary()

        assert "Errors: 2" in summary
        assert "Warnings: 1" in summary
        assert "Error 1" in summary
        assert "Warning 1" in summary

    def test_validate_ifc_project_library_exists(self):
        """Test that IfcProjectLibrary is created."""
        from pset_generator import PSetGenerator

        generator = PSetGenerator()
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

        ifc_content = generator.generate(psets)
        result = self.validator.validate_string(ifc_content)

        # Should not have warning about missing library
        assert "No IfcProjectLibrary found" not in result["warnings"]

    def test_validate_property_templates_have_names(self):
        """Test that all property templates have names."""
        from pset_generator import PSetGenerator

        generator = PSetGenerator()
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

        ifc_content = generator.generate(psets)
        result = self.validator.validate_string(ifc_content)

        # Should not have errors about missing names
        for error in result["errors"]:
            assert "missing Name" not in error


@pytest.mark.skipif(not IFCSHELL_AVAILABLE, reason="ifcopenshell not available")
class TestIntegration:
    """Integration tests with full workflow."""

    def test_full_workflow_with_validation(self):
        """Test complete workflow: parse IDS → generate IFC → validate."""
        from ids_parser import parse_ids_file
        from pset_generator import PSetGenerator
        from validator import IFCValidator

        # Parse IDS
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "minimal.ids"
        )
        psets_data = {}
        parsed = parse_ids_file(fixture_path)
        for name, pset in parsed.items():
            psets_data[name] = {
                "name": pset.name,
                "properties": [
                    {
                        "name": p.name,
                        "data_type": p.data_type,
                        "description": p.description,
                        "enum_values": p.enum_values,
                        "cardinality": p.cardinality,
                    }
                    for p in pset.properties
                ],
                "applicable_entities": pset.applicable_entities,
            }

        # Generate IFC
        generator = PSetGenerator()
        ifc_content = generator.generate(psets_data)

        # Validate
        validator = IFCValidator()
        result = validator.validate_string(ifc_content)

        assert result["valid"] is True
        assert result["error_count"] == 0

    def test_real_ids_file_validation(self):
        """Test validation with real IDS example."""
        from ids_parser import parse_ids_file
        from pset_generator import PSetGenerator
        from validator import IFCValidator

        # Try to parse the real example if it exists
        example_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "examples",
            "IDS СПб ГАУ ЦГЭ (Конструктивные решения)_corrected.ids",
        )

        if not os.path.exists(example_path):
            pytest.skip("Example IDS file not found")

        # Parse
        parsed = parse_ids_file(example_path)

        # Convert to generator format
        psets_data = {}
        for name, pset in parsed.items():
            psets_data[name] = {
                "name": pset.name,
                "properties": [
                    {
                        "name": p.name,
                        "data_type": p.data_type,
                        "description": p.description,
                        "enum_values": p.enum_values,
                        "cardinality": p.cardinality,
                    }
                    for p in pset.properties
                ],
                "applicable_entities": pset.applicable_entities,
            }

        # Generate
        generator = PSetGenerator()
        ifc_content = generator.generate(psets_data)

        # Validate
        validator = IFCValidator()
        result = validator.validate_string(ifc_content)

        assert result["valid"] is True, f"Validation failed: {result['errors']}"
        assert result["error_count"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=validator", "--cov-report=term-missing"])
