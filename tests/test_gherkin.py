"""Tests for Gherkin Rules Validator."""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from gherkin_validator import GherkinValidator, GHERKIN_AVAILABLE
except ImportError:
    GHERKIN_AVAILABLE = False
    GherkinValidator = None


@pytest.mark.skipif(not GHERKIN_AVAILABLE, reason="ifc-gherkin-rules not available")
class TestGherkinValidator:
    """Tests for GherkinValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = GherkinValidator()

    def test_validator_creation(self):
        """Test creating validator."""
        assert self.validator is not None

    def test_validate_generated_ifc(self):
        """Test gherkin validation of generated IFC."""
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

        ifc_content = generator.generate(psets)
        result = self.validator.validate_string(ifc_content)

        # Gherkin validation should complete without errors
        assert result is not None

    def test_check_pse_rules(self):
        """Test PSE rules validation."""
        from pset_generator import PSetGenerator

        generator = PSetGenerator()
        psets = {
            "MaterialPSet": {
                "name": "MaterialPSet",
                "properties": [
                    {
                        "name": "Material",
                        "data_type": "IFCTEXT",
                        "description": "",
                        "enum_values": [],
                        "cardinality": "optional",
                    }
                ],
                "applicable_entities": ["IFCBEAM"],
            }
        }

        ifc_content = generator.generate(psets)
        result = self.validator.check_pse_rules(ifc_content)

        assert result is not None

    def test_check_pse002_valid_name(self):
        """Test PSE002 with valid PSet name (not starting with 'pset')."""
        from pset_generator import PSetGenerator

        generator = PSetGenerator()
        psets = {
            "TestPSet": {
                "name": "TestPSet",  # Valid - doesn't start with 'pset'
                "properties": [
                    {
                        "name": "Property1",
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
        result = self.validator.check_pse002(ifc_content)

        # Should be valid - name doesn't start with 'pset'
        assert result["valid"] is True

    def test_get_summary(self):
        """Test validation summary."""
        self.validator.errors = ["Error 1"]
        self.validator.warnings = ["Warning 1"]

        summary = self.validator.get_summary()

        assert "Errors: 1" in summary
        assert "Warnings: 1" in summary


@pytest.mark.skipif(not GHERKIN_AVAILABLE, reason="ifc-gherkin-rules not available")
class TestGherkinIntegration:
    """Integration tests with gherkin rules."""

    def test_full_workflow_with_gherkin(self):
        """Test complete workflow with gherkin validation."""
        from ids_parser import parse_ids_file
        from pset_generator import PSetGenerator
        from gherkin_validator import GherkinValidator

        # Parse IDS
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "minimal.ids"
        )
        parsed = parse_ids_file(fixture_path)

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

        # Generate IFC
        generator = PSetGenerator()
        ifc_content = generator.generate(psets_data)

        # Validate with gherkin
        validator = GherkinValidator()
        result = validator.validate_string(ifc_content)

        assert result is not None

    def test_real_ids_with_gherkin(self):
        """Test gherkin validation with real IDS example."""
        from ids_parser import parse_ids_file
        from pset_generator import PSetGenerator
        from gherkin_validator import GherkinValidator

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

        # Generate (limit to first 5 PSet for speed)
        generator = PSetGenerator()
        limited_psets = dict(list(psets_data.items())[:5])
        ifc_content = generator.generate(limited_psets)

        # Validate with gherkin
        validator = GherkinValidator()
        result = validator.validate_string(ifc_content, rule_type="PSE")

        assert result is not None


if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "--cov=gherkin_validator", "--cov-report=term-missing"]
    )
