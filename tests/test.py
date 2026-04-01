"""Tests for IDS parser module."""

import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ids_parser import (  # noqa: E402
    parse_ids_file,
    parse_ids_content,
    PropertyRequirement,
    PSetGroup,
)


class TestPropertyRequirement:
    """Tests for PropertyRequirement dataclass."""

    def test_create_property_requirement(self):
        """Test creating a PropertyRequirement with required fields."""
        prop = PropertyRequirement(
            name="TestProperty",
            property_set="TestPSet",
            data_type="IFCTEXT",
            cardinality="required",
        )
        assert prop.name == "TestProperty"
        assert prop.property_set == "TestPSet"
        assert prop.data_type == "IFCTEXT"
        assert prop.cardinality == "required"
        assert prop.description == ""
        assert prop.enum_values == []

    def test_create_property_requirement_with_optional_fields(self):
        """Test creating a PropertyRequirement with all fields."""
        prop = PropertyRequirement(
            name="Material",
            property_set="MaterialPSet",
            data_type="IFCTEXT",
            cardinality="optional",
            description="Material type",
            enum_values=["Steel", "Concrete", "Wood"],
        )
        assert prop.name == "Material"
        assert prop.description == "Material type"
        assert len(prop.enum_values) == 3
        assert "Steel" in prop.enum_values


class TestPSetGroup:
    """Tests for PSetGroup dataclass."""

    def test_create_pset_group(self):
        """Test creating a PSetGroup."""
        pset = PSetGroup(name="TestPSet")
        assert pset.name == "TestPSet"
        assert pset.properties == []
        assert pset.applicable_entities == []

    def test_add_property_to_pset(self):
        """Test adding properties to PSetGroup."""
        pset = PSetGroup(name="TestPSet")
        prop = PropertyRequirement(
            name="Prop1",
            property_set="TestPSet",
            data_type="IFCTEXT",
            cardinality="required",
        )
        pset.properties.append(prop)
        assert len(pset.properties) == 1
        assert pset.properties[0].name == "Prop1"

    def test_add_entity_to_pset(self):
        """Test adding entities to PSetGroup."""
        pset = PSetGroup(name="TestPSet")
        pset.applicable_entities.append("IFCWALL")
        pset.applicable_entities.append("IFCSLAB")
        assert len(pset.applicable_entities) == 2
        assert "IFCWALL" in pset.applicable_entities


class TestParseIdsFile:
    """Tests for parse_ids_file function."""

    def test_parse_minimal_ids(self):
        """Test parsing minimal IDS file."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "minimal.ids"
        )
        result = parse_ids_file(fixture_path)

        assert "TestPSet" in result
        pset = result["TestPSet"]
        assert pset.name == "TestPSet"
        assert len(pset.properties) == 2
        assert "IFCWALL" in pset.applicable_entities

    def test_parse_minimal_ids_properties(self):
        """Test parsing properties from minimal IDS."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "minimal.ids"
        )
        result = parse_ids_file(fixture_path)

        pset = result["TestPSet"]
        prop1 = pset.properties[0]
        assert prop1.name == "Property1"
        assert prop1.data_type == "IFCTEXT"
        assert prop1.cardinality == "required"
        assert prop1.description == "Test property 1"

        prop2 = pset.properties[1]
        assert prop2.name == "Property2"
        assert prop2.data_type == "IFCREAL"
        assert prop2.cardinality == "optional"

    def test_parse_enumeration_ids(self):
        """Test parsing IDS with enumeration values."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "with_enumeration.ids"
        )
        result = parse_ids_file(fixture_path)

        assert "MaterialPSet" in result
        pset = result["MaterialPSet"]
        assert len(pset.properties) == 1

        prop = pset.properties[0]
        assert prop.name == "Material"
        assert len(prop.enum_values) == 3
        assert "Steel" in prop.enum_values
        assert "Concrete" in prop.enum_values
        assert "Wood" in prop.enum_values

    def test_parse_multi_entity_ids(self):
        """Test parsing IDS with multiple specifications and same PSet name."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "multi_entity.ids"
        )
        result = parse_ids_file(fixture_path)

        # Should have one PSet grouped from two specifications
        assert "CommonPSet" in result
        pset = result["CommonPSet"]

        # Should have entities from both specifications
        assert "IFCBEAM" in pset.applicable_entities
        assert "IFCSLAB" in pset.applicable_entities

    def test_parse_empty_requirements(self):
        """Test parsing IDS with empty requirements section."""
        ids_content = """<?xml version="1.0" encoding="UTF-8"?>
        <ids xmlns="http://standards.buildingsmart.org/IDS">
            <specification name="Test">
                <applicability>
                    <entityPart name="IFCWALL"/>
                </applicability>
                <requirements>
                </requirements>
            </specification>
        </ids>"""

        import tempfile as tf

        with tf.NamedTemporaryFile(mode="w", suffix=".ids", delete=False) as f:
            f.write(ids_content)
            temp_path = f.name

        try:
            result = parse_ids_file(temp_path)
            # Should return empty dict for no requirements
            assert isinstance(result, dict)
        finally:
            import os

            os.unlink(temp_path)


class TestParseIdsContent:
    """Tests for parse_ids_content function."""

    def test_parse_content_string(self):
        """Test parsing IDS from string content."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns:xs="http://www.w3.org/2001/XMLSchema"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://standards.buildingsmart.org/IDS
                         http://standards.buildingsmart.org/IDS/1.0/ids.xsd"
     xmlns="http://standards.buildingsmart.org/IDS">
  <info>
    <title>Inline Test</title>
  </info>
  <specifications>
    <specification name="Test" ifcVersion="IFC4">
      <applicability minOccurs="1" maxOccurs="unbounded">
        <entity>
          <name><simpleValue>IFCCOLUMN</simpleValue></name>
        </entity>
      </applicability>
      <requirements>
        <property cardinality="required" dataType="IFCINTEGER">
          <propertySet><simpleValue>InlinePSet</simpleValue></propertySet>
          <baseName><simpleValue>Count</simpleValue></baseName>
        </property>
      </requirements>
    </specification>
  </specifications>
</ids>"""

        result = parse_ids_content(content)

        assert "InlinePSet" in result
        pset = result["InlinePSet"]
        assert pset.name == "InlinePSet"
        assert len(pset.properties) == 1
        assert pset.properties[0].name == "Count"
        assert pset.properties[0].data_type == "IFCINTEGER"
        assert "IFCCOLUMN" in pset.applicable_entities

    def test_parse_missing_property_set(self):
        """Test parsing IDS with missing propertySet element."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT">
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        # Should skip properties without propertySet
        assert result == {}

    def test_parse_empty_property_set_name(self):
        """Test parsing IDS with empty propertySet name."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT">
        <propertySet><simpleValue></simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        # Should skip properties with empty propertySet name
        assert result == {}

    def test_parse_empty_ids(self):
        """Test parsing empty IDS."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <info><title>Empty</title></info>
</ids>"""

        result = parse_ids_content(content)
        assert result == {}

    def test_parse_ids_no_requirements(self):
        """Test parsing IDS with no requirements."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <info><title>No Requirements</title></info>
  <specifications>
    <specification name="Empty Spec" ifcVersion="IFC4">
      <applicability>
        <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
      </applicability>
    </specification>
  </specifications>
</ids>"""

        result = parse_ids_content(content)
        assert result == {}


class TestIntegration:
    """Integration tests."""

    def test_full_parse_and_verify(self):
        """Test full parsing workflow with verification."""
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "minimal.ids"
        )
        result = parse_ids_file(fixture_path)

        # Verify structure
        assert len(result) == 1
        assert "TestPSet" in result

        pset = result["TestPSet"]
        assert isinstance(pset, PSetGroup)
        assert len(pset.properties) == 2
        assert all(isinstance(p, PropertyRequirement) for p in pset.properties)
        assert len(pset.applicable_entities) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=ids_parser", "--cov-report=term-missing"])
