"""E2E Tests for IDS2PSET - Full cycle testing."""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from ids_parser import parse_ids_file
    from pset_generator import PSetGenerator
    from validator import IFCValidator
    from gherkin_validator import GherkinValidator, GHERKIN_AVAILABLE

    ALL_MODULES_AVAILABLE = True
except ImportError:
    ALL_MODULES_AVAILABLE = False


@pytest.mark.skipif(not ALL_MODULES_AVAILABLE, reason="Modules not available")
class TestE2EFullCycle:
    """End-to-End tests for complete IDS → IFC workflow."""

    def test_minimal_ids_full_cycle(self):
        """Test complete cycle with minimal IDS fixture."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "minimal.ids"
        )

        # Step 1: Parse IDS
        parsed = parse_ids_file(fixture_path)
        assert len(parsed) > 0, "Should parse at least one PSet"

        # Step 2: Convert to generator format
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

        # Step 3: Generate IFC
        generator = PSetGenerator()
        ifc_content = generator.generate(psets_data)
        assert len(ifc_content) > 0, "Should generate IFC content"
        assert "IFC4" in ifc_content, "Should be IFC4 format"
        assert "IFCPROJECTLIBRARY" in ifc_content, "Should have library"

        # Step 4: Validate with ifcopenshell
        validator = IFCValidator()
        result = validator.validate_string(ifc_content)
        assert result["valid"], f"Should be valid IFC: {result['errors']}"

        # Step 5: Validate with gherkin rules
        if GHERKIN_AVAILABLE:
            gherkin_validator = GherkinValidator()
            gherkin_result = gherkin_validator.validate_string(ifc_content)
            assert gherkin_result is not None, "Gherkin validation should complete"

    def test_enumeration_ids_full_cycle(self):
        """Test complete cycle with enumeration IDS fixture."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "with_enumeration.ids"
        )

        # Parse
        parsed = parse_ids_file(fixture_path)
        assert "MaterialPSet" in parsed, "Should have MaterialPSet"

        # Convert
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
        assert result["valid"], f"Should be valid IFC: {result['errors']}"

    def test_multi_entity_full_cycle(self):
        """Test complete cycle with multi-entity IDS fixture."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "multi_entity.ids"
        )

        # Parse
        parsed = parse_ids_file(fixture_path)
        assert "CommonPSet" in parsed, "Should have CommonPSet"

        # Verify entities are merged
        pset = parsed["CommonPSet"]
        assert "IFCWALL" in pset.applicable_entities
        assert "IFCSLAB" in pset.applicable_entities

        # Convert
        psets_data = {
            "CommonPSet": {
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
        }

        # Generate
        generator = PSetGenerator()
        ifc_content = generator.generate(psets_data)

        # Validate
        validator = IFCValidator()
        result = validator.validate_string(ifc_content)
        assert result["valid"], f"Should be valid IFC: {result['errors']}"

    def test_pset_selection_filtering(self):
        """Test filtering PSet by selection."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "multi_entity.ids"
        )

        # Parse
        parsed = parse_ids_file(fixture_path)

        # Convert
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

        # Select only specific PSet
        selected_names = list(psets_data.keys())[:1]
        filtered_psets = {
            name: pset for name, pset in psets_data.items() if name in selected_names
        }

        # Generate
        generator = PSetGenerator()
        ifc_content = generator.generate(filtered_psets)

        # Validate
        validator = IFCValidator()
        result = validator.validate_string(ifc_content)
        assert result["valid"], f"Should be valid IFC: {result['errors']}"

    def test_all_gherkin_categories(self):
        """Test validation against all 33 gherkin rule categories."""
        if not GHERKIN_AVAILABLE:
            pytest.skip("Gherkin validator not available")

        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "minimal.ids"
        )

        # Parse and generate
        parsed = parse_ids_file(fixture_path)
        psets_data = {
            name: {
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
            for name, pset in parsed.items()
        }

        generator = PSetGenerator()
        ifc_content = generator.generate(psets_data)

        # Validate against all rules
        validator = GherkinValidator()
        result = validator.validate_all_rules(ifc_content)

        assert result is not None
        assert "results_by_category" in result
        assert (
            len(result["results_by_category"]) == 33
        ), "Should validate all 33 categories"

    def test_ifc_content_structure(self):
        """Test generated IFC has correct structure."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "minimal.ids"
        )

        parsed = parse_ids_file(fixture_path)
        psets_data = {
            name: {
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
            for name, pset in parsed.items()
        }

        generator = PSetGenerator()
        ifc_content = generator.generate(psets_data)

        # Check IFC structure
        assert "ISO-10303-21" in ifc_content, "Should have IFC header"
        assert "END-ISO-10303-21" in ifc_content, "Should have IFC footer"
        assert "IFCPROJECT" in ifc_content, "Should have IfcProject"
        assert "IFCPROJECTLIBRARY" in ifc_content, "Should have IfcProjectLibrary"
        assert "IFCPROPERTYSETTEMPLATE" in ifc_content, "Should have templates"
        assert (
            "IFCSIMPLEPROPERTYTEMPLATE" in ifc_content
        ), "Should have simple templates"


@pytest.mark.skipif(not ALL_MODULES_AVAILABLE, reason="Modules not available")
class TestE2EErrorHandling:
    """E2E tests for error handling."""

    def test_invalid_ids_handling(self):
        """Test handling of invalid IDS content."""
        invalid_ids = """<?xml version="1.0"?>
        <ids>
            <invalid_structure>
        </ids>"""

        # Should not crash
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ids", delete=False) as f:
            f.write(invalid_ids)
            temp_path = f.name

        try:
            # May raise exception or return empty result
            result = parse_ids_file(temp_path)
            assert isinstance(result, dict)
        except Exception:
            pass  # Expected for invalid XML
        finally:
            os.unlink(temp_path)

    def test_empty_pset_handling(self):
        """Test handling of empty PSet data."""
        generator = PSetGenerator()
        ifc_content = generator.generate({})

        # Should generate valid (but empty) IFC
        assert len(ifc_content) > 0
        assert "IFC4" in ifc_content


@pytest.mark.skipif(not ALL_MODULES_AVAILABLE, reason="Modules not available")
class TestIFCValidationScript:
    """Tests for validate_ifc_playwright.py script."""

    def test_validate_generated_ifc(self):
        """Test validation script with generated IFC."""
        from validate_ifc_playwright import validate_ifc_file
        import tempfile

        # Generate IFC
        generator = PSetGenerator()
        psets = {
            "TestPSet": {
                "name": "TestPSet",
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

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ifc", delete=False) as f:
            f.write(ifc_content)
            temp_path = f.name

        try:
            # Run validation
            result = validate_ifc_file(temp_path)
            assert result is True, "Validation should pass"
        finally:
            os.unlink(temp_path)

    def test_validate_fixture_ifc(self):
        """Test validation script with Playwright generated IFC."""
        from validate_ifc_playwright import validate_ifc_file

        ifc_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            ".playwright-mcp",
            "IDS2PSET-Library.ifc",
        )

        if not os.path.exists(ifc_path):
            pytest.skip("Playwright IFC file not found")

        result = validate_ifc_file(ifc_path)
        assert result is True, "Validation should pass"
