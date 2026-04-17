"""Tests for IDS parser module."""

import os
import sys
import pytest
import xml.etree.ElementTree as ET

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ids_parser import (  # noqa: E402
    parse_ids_file,
    parse_ids_content,
    PropertyRequirement,
    PSetGroup,
    _validate_entities,
    _extract_entity_names,
    _VALID_IFC_ENTITIES,
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
        assert "IFCWALL" in pset.applicable_entities
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


class TestValidateEntities:
    """Tests for _validate_entities function."""

    def test_valid_entities_no_invalid(self):
        """Test that valid entities return empty list."""
        entities = ["IFCWALL", "IFCSLAB", "IFCDOOR"]
        result = _validate_entities(entities)
        assert result == []

    def test_invalid_entity_detected(self):
        """Test that invalid entities are detected."""
        entities = ["IFCWALL", "IFCMAGICWALL", "IFCSLAB"]
        result = _validate_entities(entities)
        assert result == ["IFCMAGICWALL"]

    def test_all_invalid(self):
        """Test all entities invalid."""
        entities = ["IFCNOTREAL", "IFCFAKE"]
        result = _validate_entities(entities)
        assert len(result) == 2

    def test_entity_with_predefined_type(self):
        """Test entity with predefined type (e.g., IFCSTAIR/PREFABRICATED)."""
        entities = ["IFCSTAIR/PREFABRICATED", "IFCWALL"]
        result = _validate_entities(entities)
        assert result == []  # IFCSTAIR is valid

    def test_predefined_type_invalid(self):
        """Test entity with invalid base and predefined type."""
        entities = ["IFCFAKE/PREFABRICATED"]
        result = _validate_entities(entities)
        assert result == ["IFCFAKE/PREFABRICATED"]

    def test_empty_entities(self):
        """Test empty entity list."""
        result = _validate_entities([])
        assert result == []


class TestExtractEntityNames:
    """Tests for _extract_entity_names function."""

    def _make_elem(self, xml_snippet):
        """Helper to create XML element from snippet."""
        import xml.etree.ElementTree as ET

        ns = {
            "ids": "http://standards.buildingsmart.org/IDS",
            "xs": "http://www.w3.org/2001/XMLSchema",
        }
        wrapped = (
            f'<root xmlns:ids="{ns["ids"]}" xmlns:xs="{ns["xs"]}">{xml_snippet}</root>'
        )
        root = ET.fromstring(wrapped)
        return root.find("ids:name", ns)

    def test_simple_value(self):
        """Test extracting simpleValue entity name."""
        elem = self._make_elem(
            "<ids:name><ids:simpleValue>IFCWALL</ids:simpleValue></ids:name>"
        )
        names, warning = _extract_entity_names(
            elem,
            {"ids": "http://standards.buildingsmart.org/IDS"},
            {"xs": "http://www.w3.org/2001/XMLSchema"},
        )
        assert names == ["IFCWALL"]
        assert warning is False

    def test_xs_enumeration(self):
        """Test extracting xs:enumeration entity names."""
        elem = self._make_elem(
            '<ids:name><xs:restriction base="xs:string">'
            '<xs:enumeration value="IFCWALL"/>'
            '<xs:enumeration value="IFCSLAB"/>'
            "</xs:restriction></ids:name>"
        )
        names, warning = _extract_entity_names(
            elem,
            {"ids": "http://standards.buildingsmart.org/IDS"},
            {"xs": "http://www.w3.org/2001/XMLSchema"},
        )
        assert set(names) == {"IFCWALL", "IFCSLAB"}
        assert warning is False

    def test_xs_pattern_split(self):
        """Test extracting xs:pattern entity names split by |."""
        elem = self._make_elem(
            '<ids:name><xs:restriction base="xs:string">'
            '<xs:pattern value="IFCSTAIRFLIGHT|IFCSLAB"/>'
            "</xs:restriction></ids:name>"
        )
        names, warning = _extract_entity_names(
            elem,
            {"ids": "http://standards.buildingsmart.org/IDS"},
            {"xs": "http://www.w3.org/2001/XMLSchema"},
        )
        assert set(names) == {"IFCSTAIRFLIGHT", "IFCSLAB"}
        assert warning is False

    def test_xs_pattern_empty(self):
        """Test xs:pattern with empty value returns warning."""
        elem = self._make_elem(
            '<ids:name><xs:restriction base="xs:string">'
            '<xs:pattern value=""/>'
            "</xs:restriction></ids:name>"
        )
        names, warning = _extract_entity_names(
            elem,
            {"ids": "http://standards.buildingsmart.org/IDS"},
            {"xs": "http://www.w3.org/2001/XMLSchema"},
        )
        # Empty pattern value is filtered out, returns warning with empty list
        assert names == []
        assert warning is True

    def test_none_element(self):
        """Test None element returns empty with no warning."""
        names, warning = _extract_entity_names(
            None,
            {"ids": "http://standards.buildingsmart.org/IDS"},
            {"xs": "http://www.w3.org/2001/XMLSchema"},
        )
        assert names == []
        assert warning is False


class TestEntityWarningAndInvalid:
    """Tests for entity_warning and invalid_entities in parse results."""

    def test_entity_warning_no_applicability(self):
        """Test entity_warning when applicability section is empty."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        assert "TestPSet" in result
        assert result["TestPSet"].entity_warning is True

    def test_valid_entities_no_invalid(self):
        """Test that valid entities produce no invalid_entities."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        assert result["TestPSet"].invalid_entities == []

    def test_invalid_entity_in_result(self):
        """Test that invalid entities appear in invalid_entities."""
        # Используем несуществующую сущность
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity><name><simpleValue>IFCFAKEWALL</simpleValue></name></entity>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        assert result["TestPSet"].invalid_entities == ["IFCFAKEWALL"]

    def test_entity_pattern_split_in_result(self):
        """Test that entity xs:pattern is split into individual entities."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns:xs="http://www.w3.org/2001/XMLSchema"
     xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity>
        <name>
          <xs:restriction base="xs:string">
            <xs:pattern value="IFCSTAIRFLIGHT|IFCSLAB"/>
          </xs:restriction>
        </name>
      </entity>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        assert "TestPSet" in result
        assert "IFCSTAIRFLIGHT" in result["TestPSet"].applicable_entities
        assert "IFCSLAB" in result["TestPSet"].applicable_entities
        assert result["TestPSet"].invalid_entities == []


class TestPSetGroupNewFields:
    """Tests for new PSetGroup fields."""

    def test_psetgroup_entity_warning_default(self):
        """Test entity_warning defaults to False."""
        pset = PSetGroup(name="TestPSet")
        assert pset.entity_warning is False

    def test_psetgroup_invalid_entities_default(self):
        """Test invalid_entities defaults to empty list."""
        pset = PSetGroup(name="TestPSet")
        assert pset.invalid_entities == []

    def test_psetgroup_entity_warning_set(self):
        """Test entity_warning can be set."""
        pset = PSetGroup(name="TestPSet", entity_warning=True)
        assert pset.entity_warning is True

    def test_psetgroup_invalid_entities_set(self):
        """Test invalid_entities can be set."""
        pset = PSetGroup(name="TestPSet", invalid_entities=["IFCFAKE"])
        assert pset.invalid_entities == ["IFCFAKE"]


class TestValidIfcEntities:
    """Tests for _VALID_IFC_ENTITIES set."""

    def test_common_entities_present(self):
        """Test that common entities are in the valid set."""
        assert "IFCWALL" in _VALID_IFC_ENTITIES
        assert "IFCSLAB" in _VALID_IFC_ENTITIES
        assert "IFCDOOR" in _VALID_IFC_ENTITIES
        assert "IFCWINDOW" in _VALID_IFC_ENTITIES
        assert "IFCCOLUMN" in _VALID_IFC_ENTITIES
        assert "IFCSTAIRFLIGHT" in _VALID_IFC_ENTITIES
        assert "IFCRAILING" in _VALID_IFC_ENTITIES
        assert "IFCELEMENTASSEMBLY" in _VALID_IFC_ENTITIES

    def test_fake_entity_not_present(self):
        """Test that fake entities are not in the valid set."""
        assert "IFCFAKEWALL" not in _VALID_IFC_ENTITIES
        assert "IFCMAGICWALL" not in _VALID_IFC_ENTITIES


class TestIsRegexLike:
    """Tests for _is_regex_like function."""

    def test_empty_text(self):
        """Test empty text returns False."""
        from ids_parser import _is_regex_like

        assert _is_regex_like("") is False
        assert _is_regex_like(None) is False

    def test_regex_patterns_detected(self):
        """Test regex patterns are detected."""
        from ids_parser import _is_regex_like

        assert _is_regex_like(".*wall") is True
        assert _is_regex_like("[A-Z]+") is True
        assert _is_regex_like("\\d+") is True

    def test_plain_text_not_regex(self):
        """Test plain text is not detected as regex."""
        from ids_parser import _is_regex_like

        assert _is_regex_like("IFCWALL") is False
        assert _is_regex_like("TestPSet") is False


class TestExtractValuesPattern:
    """Tests for _extract_values with xs:pattern."""

    def _make_elem(self, xml_snippet):
        import xml.etree.ElementTree as ET
        from ids_parser import _extract_values

        self._extract_values = _extract_values

        ns = {
            "ids": "http://standards.buildingsmart.org/IDS",
            "xs": "http://www.w3.org/2001/XMLSchema",
        }
        wrapped = (
            f'<root xmlns:ids="{ns["ids"]}" xmlns:xs="{ns["xs"]}">{xml_snippet}</root>'
        )
        root = ET.fromstring(wrapped)
        return root.find("ids:propertySet", ns), ns

    def test_xs_pattern_in_property_set(self):
        """Test xs:pattern in propertySet returns has_pattern=True."""
        from ids_parser import _extract_values

        elem, ns = self._make_elem(
            '<ids:propertySet><xs:restriction base="xs:string">'
            '<xs:pattern value=".*wall.*"/>'
            "</xs:restriction></ids:propertySet>"
        )
        values, has_pattern = _extract_values(
            elem, ns, {"xs": "http://www.w3.org/2001/XMLSchema"}
        )
        assert values == [".*wall.*"]
        assert has_pattern is True

    def test_xs_pattern_in_base_name(self):
        """Test xs:pattern in baseName returns has_pattern=True."""
        import xml.etree.ElementTree as ET
        from ids_parser import _extract_values

        ns = {
            "ids": "http://standards.buildingsmart.org/IDS",
            "xs": "http://www.w3.org/2001/XMLSchema",
        }
        wrapped = (
            '<root xmlns:ids="http://standards.buildingsmart.org/IDS" '
            'xmlns:xs="http://www.w3.org/2001/XMLSchema">'
            '<ids:baseName><xs:restriction base="xs:string">'
            '<xs:pattern value=".*prop.*"/>'
            "</xs:restriction></ids:baseName></root>"
        )
        root = ET.fromstring(wrapped)
        elem = root.find("ids:baseName", ns)
        values, has_pattern = _extract_values(
            elem, ns, {"xs": "http://www.w3.org/2001/XMLSchema"}
        )
        assert values == [".*prop.*"]
        assert has_pattern is True


class TestParseIdsContentWithEntityInRequirements:
    """Tests for parsing entity from requirements section."""

    def test_entity_in_requirements(self):
        """Test parsing entity from requirements instead of applicability."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <requirements>
      <entity><name><simpleValue>IFCBEAM</simpleValue></name></entity>
      <property dataType="IFCTEXT">
        <propertySet><simpleValue>BeamPSet</simpleValue></propertySet>
        <baseName><simpleValue>Material</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        assert "BeamPSet" in result
        assert "IFCBEAM" in result["BeamPSet"].applicable_entities


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_xs_pattern_not_split_entity(self):
        """Test xs:pattern without | is handled as regex pattern."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns:xs="http://www.w3.org/2001/XMLSchema"
     xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity>
        <name>
          <xs:restriction base="xs:string">
            <xs:pattern value=".*wall.*"/>
          </xs:restriction>
        </name>
      </entity>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        assert "TestPSet" in result
        assert ".*wall.*" in result["TestPSet"].applicable_entities
        assert ".*wall.*" in result["TestPSet"].invalid_entities

    def test_property_with_no_data_type(self):
        """Test property without dataType uses default IFCTEXT."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
    </applicability>
    <requirements>
      <property>
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        assert "TestPSet" in result
        prop = result["TestPSet"].properties[0]
        assert prop.data_type == "IFCTEXT"

    def test_cardinality_defaults(self):
        """Test cardinality defaults to optional when not specified."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
    </applicability>
    <requirements>
      <property>
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        prop = result["TestPSet"].properties[0]
        assert prop.cardinality == "optional"

    def test_cardinality_required(self):
        """Test explicit required cardinality."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
    </applicability>
    <requirements>
      <property cardinality="required">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        prop = result["TestPSet"].properties[0]
        assert prop.cardinality == "required"

    def test_invalid_xml_structure(self):
        """Test parsing handles malformed XML gracefully."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
      <broken>
    </requirements>
  </specification>
</ids>"""
        try:
            result = parse_ids_content(content)
            assert isinstance(result, dict)
        except ET.ParseError:
            pass

    def test_multiple_properties_same_pset(self):
        """Test multiple properties in same PSet are collected."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>Prop1</simpleValue></baseName>
      </property>
      <property dataType="IFCREAL">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>Prop2</simpleValue></baseName>
      </property>
      <property dataType="IFCINTEGER">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>Prop3</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        assert "TestPSet" in result
        assert len(result["TestPSet"].properties) == 3
        names = [p.name for p in result["TestPSet"].properties]
        assert "Prop1" in names
        assert "Prop2" in names
        assert "Prop3" in names

    def test_specification_without_name(self):
        """Test specification without name attribute."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification>
    <applicability>
      <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        assert "TestPSet" in result

    def test_pset_name_with_spaces(self):
        """Test PSet name with spaces is handled correctly."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT">
        <propertySet><simpleValue>Test PSet Name</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        assert "Test PSet Name" in result

    def test_property_description_empty(self):
        """Test property with empty instructions."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT" instructions="">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        prop = result["TestPSet"].properties[0]
        assert prop.description == ""

    def test_entity_with_multiple_predefined_types(self):
        """Test entity with multiple predefined types via enumeration."""
        content = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns:xs="http://www.w3.org/2001/XMLSchema"
     xmlns="http://standards.buildingsmart.org/IDS">
  <specification name="Test">
    <applicability>
      <entity>
        <name><simpleValue>IFCSTAIR</simpleValue></name>
        <predefinedType>
          <xs:restriction base="xs:string">
            <xs:enumeration value="STRAIGHT"/>
            <xs:enumeration value="CURVED"/>
            <xs:enumeration value="SPIRAL"/>
          </xs:restriction>
        </predefinedType>
      </entity>
    </applicability>
    <requirements>
      <property dataType="IFCTEXT">
        <propertySet><simpleValue>TestPSet</simpleValue></propertySet>
        <baseName><simpleValue>TestProp</simpleValue></baseName>
      </property>
    </requirements>
  </specification>
</ids>"""
        result = parse_ids_content(content)
        assert "TestPSet" in result
        entities = result["TestPSet"].applicable_entities
        assert "IFCSTAIR/STRAIGHT" in entities
        assert "IFCSTAIR/CURVED" in entities
        assert "IFCSTAIR/SPIRAL" in entities


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=ids_parser", "--cov-report=term-missing"])
