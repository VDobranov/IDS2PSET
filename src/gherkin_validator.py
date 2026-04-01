"""IFC Gherkin Rules Validator - обёртка для ifc-gherkin-rules."""

import os
import sys
import tempfile
from typing import Dict, Any

# Добавляем vendor в path
# Ищем vendor относительно текущего файла или корня проекта
VENDOR_PATH = None
for base in [
    os.path.join(os.path.dirname(__file__), "..", "vendor"),
    os.path.join(os.path.dirname(__file__), "..", "..", "vendor"),
    "vendor",
]:
    candidate = os.path.abspath(os.path.join(base, "ifc-gherkin-rules"))
    if os.path.exists(candidate):
        VENDOR_PATH = candidate
        break

if VENDOR_PATH and os.path.exists(VENDOR_PATH):
    sys.path.insert(0, VENDOR_PATH)

try:
    from main import run as run_gherkin_validation
    from main import RuleType

    GHERKIN_AVAILABLE = True
except ImportError as e:
    GHERKIN_AVAILABLE = False
    run_gherkin_validation = None
    RuleType = None
    print(f"Gherkin validator warning: {e}")


class GherkinValidator:
    """Validator for IFC files using ifc-gherkin-rules."""

    # Все категории правил из ifc-gherkin-rules
    RULE_CATEGORIES = [
        "ALB",
        "ALS",
        "ANN",
        "ASM",
        "AXG",
        "BBX",
        "BLT",
        "BRP",
        "CLS",
        "CTX",
        "GDP",
        "GEM",
        "GRF",
        "GRP",
        "IFC",
        "LAY",
        "LIP",
        "LOP",
        "MAT",
        "MPD",
        "OJP",
        "OJT",
        "PSE",
        "PJS",
        "POR",
        "QTY",
        "SPA",
        "SPS",
        "SWE",
        "SYS",
        "TAS",
        "VER",
        "VRT",
    ]

    def __init__(self):
        if not GHERKIN_AVAILABLE:
            raise ImportError(
                "ifc-gherkin-rules not available. "
                "Ensure git submodule is initialized: "
                "git submodule update --init"
            )
        self.results = {}
        self.errors = []
        self.warnings = []

    def validate_file(
        self, file_path: str, rule_type: str = "ALL", max_outcomes: int = 0
    ) -> Dict[str, Any]:
        """
        Validate IFC file using gherkin rules.

        Args:
            file_path: Path to IFC file
            rule_type: Type of rules to check (ALL, PSE, IFC, etc.)
            max_outcomes: Max number of outcomes to return (0 = all)

        Returns:
            Dictionary with validation results
        """
        self.errors = []
        self.warnings = []

        # Map rule type string to RuleType
        rule_type_map = {
            "ALL": RuleType.ALL if RuleType else None,
            "PSE": RuleType.INDUSTRY_PRACTICE if RuleType else None,
            "IFC": RuleType.IMPLEMENTER_AGREEMENT if RuleType else None,
            "CRITICAL": RuleType.CRITICAL if RuleType else None,
        }

        rt = rule_type_map.get(rule_type, RuleType.ALL if RuleType else None)

        try:
            # Run validation
            result = run_gherkin_validation(
                filename=file_path,
                rule_type=rt,
                max_outcomes=max_outcomes,
                with_console_output=False,
            )

            # Parse results
            if isinstance(result, dict):
                self.results = result
                self._parse_results(result)
            elif isinstance(result, str):
                # JSON string result
                import json

                self.results = json.loads(result)
                self._parse_results(self.results)

        except Exception as e:
            self.errors.append(f"Gherkin validation error: {str(e)}")

        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "results": self.results,
        }

    def validate_string(
        self, ifc_content: str, rule_type: str = "ALL"
    ) -> Dict[str, Any]:
        """
        Validate IFC content from string.

        Args:
            ifc_content: IFC file content as string
            rule_type: Type of rules to check

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
            result = self.validate_file(temp_path, rule_type)
        finally:
            os.unlink(temp_path)

        return result

    def _parse_results(self, result: Dict) -> None:
        """Parse gherkin validation results."""
        # Results structure depends on gherkin output format
        # Typically contains scenarios, steps, and outcomes

        if "scenarios" in result:
            for scenario in result["scenarios"]:
                if scenario.get("status") == "failed":
                    self.errors.append(
                        f"Scenario '{scenario.get('name', 'unknown')}' failed"
                    )
                elif scenario.get("status") == "passed":
                    pass  # OK

        if "outcomes" in result:
            for outcome in result["outcomes"]:
                severity = outcome.get("severity", "warning")
                message = outcome.get("message", str(outcome))

                if severity == "error":
                    self.errors.append(message)
                else:
                    self.warnings.append(message)

    def get_summary(self) -> str:
        """Get validation summary as string."""
        lines = []
        lines.append("Gherkin Rules Validation Summary")
        lines.append("=" * 40)
        lines.append(f"Errors: {len(self.errors)}")
        lines.append(f"Warnings: {len(self.warnings)}")

        if self.errors:
            lines.append("\nErrors:")
            for error in self.errors:
                lines.append(f"  ✗ {error}")

        if self.warnings:
            lines.append("\nWarnings:")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")

        return "\n".join(lines)

    def validate_all_rules(self, ifc_content: str) -> Dict[str, Any]:
        """
        Validate IFC against ALL gherkin rules.

        Args:
            ifc_content: IFC file content as string

        Returns:
            Dictionary with validation results for all rule categories
        """
        all_results = {}
        all_errors = []
        all_warnings = []

        for category in self.RULE_CATEGORIES:
            try:
                result = self.validate_string(ifc_content, rule_type=category)
                all_results[category] = result
                all_errors.extend(result.get("errors", []))
                all_warnings.extend(result.get("warnings", []))
            except Exception as e:
                all_results[category] = {"error": str(e)}

        return {
            "valid": len(all_errors) == 0,
            "errors": all_errors,
            "warnings": all_warnings,
            "error_count": len(all_errors),
            "warning_count": len(all_warnings),
            "results_by_category": all_results,
        }

    def check_pse_rules(self, ifc_content: str) -> Dict[str, Any]:
        """
        Check PSE (Property Set Extension) rules specifically.

        Args:
            ifc_content: IFC file content as string

        Returns:
            Dictionary with PSE validation results
        """
        return self.validate_string(ifc_content, rule_type="PSE")

    def check_pse002(self, ifc_content: str) -> Dict[str, Any]:
        """
        Check PSE002 rule specifically.

        PSE002: Property set names must not start with 'pset' (any case)
        to avoid confusion with standardized IFC PSet names (Pset_*).

        Args:
            ifc_content: IFC file content as string

        Returns:
            Dictionary with PSE002 validation result
        """
        result = self.check_pse_rules(ifc_content)

        # Filter for PSE002 specifically
        pse002_errors = [
            e for e in result["errors"] if "PSE002" in e or "pset" in e.lower()
        ]

        return {
            "valid": len(pse002_errors) == 0,
            "errors": pse002_errors,
            "all_errors": result["errors"],
            "warnings": result["warnings"],
        }
