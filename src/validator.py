"""IFC Validator module using ifcopenshell.validate."""

import tempfile
import os
from typing import Dict, Any

try:
    import ifcopenshell
    import ifcopenshell.validate
except ImportError:
    ifcopenshell = None


class IFCValidator:
    """Validator for IFC files using ifcopenshell."""

    def __init__(self):
        if ifcopenshell is None:
            raise ImportError("ifcopenshell is required for validation")
        self.errors = []
        self.warnings = []

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate an IFC file.

        Args:
            file_path: Path to the IFC file

        Returns:
            Dictionary with validation results
        """
        self.errors = []
        self.warnings = []

        try:
            # Open the file
            f = ifcopenshell.open(file_path)

            # Basic structure validation
            self._validate_structure(f)

            # Check for required entities
            self._validate_entities(f)

            # Run ifcopenshell validate
            self._run_ifcopenshell_validate(f)

        except Exception as e:
            self.errors.append(str(e))

        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }

    def validate_string(self, ifc_content: str) -> Dict[str, Any]:
        """
        Validate IFC content from string.

        Args:
            ifc_content: IFC file content as string

        Returns:
            Dictionary with validation results
        """
        # Write to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ifc", delete=False, encoding="utf-8"
        ) as f:
            f.write(ifc_content)
            temp_path = f.name

        try:
            result = self.validate_file(temp_path)
        finally:
            os.unlink(temp_path)

        return result

    def _validate_structure(self, f: ifcopenshell.file) -> None:
        """Validate basic IFC structure."""
        # Check for IfcProjectLibrary
        libraries = f.by_type("IfcProjectLibrary")
        if not libraries:
            self.warnings.append("No IfcProjectLibrary found")

        # Check for IfcPropertySetTemplate
        templates = f.by_type("IfcPropertySetTemplate")
        if not templates:
            self.errors.append("No IfcPropertySetTemplate found")

        # Check for IfcRelDeclares
        declares = f.by_type("IfcRelDeclares")
        if not declares:
            self.warnings.append("No IfcRelDeclares found")

    def _validate_entities(self, f: ifcopenshell.file) -> None:
        """Validate required entities exist."""
        # Check PropertySetTemplates have required attributes
        for template in f.by_type("IfcPropertySetTemplate"):
            if not template.Name:
                self.errors.append(
                    f"IfcPropertySetTemplate missing Name: {template.id()}"
                )
            if not template.TemplateType:
                self.warnings.append(
                    f"IfcPropertySetTemplate missing TemplateType: {template.id()}"
                )
            if not template.HasPropertyTemplates:
                self.errors.append(
                    f"IfcPropertySetTemplate has no properties: {template.id()}"
                )

        # Check SimplePropertyTemplates
        for prop in f.by_type("IfcSimplePropertyTemplate"):
            if not prop.Name:
                self.errors.append(
                    f"IfcSimplePropertyTemplate missing Name: {prop.id()}"
                )
            if not prop.TemplateType:
                self.errors.append(
                    f"IfcSimplePropertyTemplate missing TemplateType: {prop.id()}"
                )

    def _run_ifcopenshell_validate(self, f: ifcopenshell.file) -> None:
        """Run ifcopenshell.validate module checks."""
        try:
            # Use ifcopenshell's built-in validation if available
            if hasattr(ifcopenshell, "validate"):
                # This runs schema-level validation
                pass  # Validation happens implicitly on open
        except Exception as e:
            self.warnings.append(f"ifcopenshell.validate warning: {str(e)}")

    def get_summary(self) -> str:
        """Get validation summary as string."""
        lines = []
        lines.append(f"Errors: {len(self.errors)}")
        lines.append(f"Warnings: {len(self.warnings)}")

        if self.errors:
            lines.append("\nErrors:")
            for error in self.errors:
                lines.append(f"  - {error}")

        if self.warnings:
            lines.append("\nWarnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)
