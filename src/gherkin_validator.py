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

        # Определяем тип IFC файла для выбора правил
        try:
            import ifcopenshell

            f = ifcopenshell.open(file_path)

            # Проверяем это ли PSet Library
            libraries = f.by_type("IfcProjectLibrary")
            has_buildings = len(f.by_type("IfcBuilding")) > 0
            has_geometry = len(f.by_type("IfcShapeRepresentation")) > 0

            is_pset_library = (
                len(libraries) > 0 and not has_buildings and not has_geometry
            )

            # Для PSet Library используем только PSE правила
            if is_pset_library:
                rule_type = "PSE"
        except Exception:
            pass  # Если не смогли определить, используем заданный rule_type

        # Для PSet Library запускаем только PSE feature файлы
        if rule_type == "PSE":
            return self._validate_pse_only(file_path, max_outcomes)

        # Map rule type string to RuleType
        # PSE rules have @implementer-agreement tag
        rule_type_map = {
            "ALL": RuleType.ALL if RuleType else None,
            "PSE": RuleType.IMPLEMENTER_AGREEMENT if RuleType else None,
            "IFC": RuleType.IMPLEMENTER_AGREEMENT if RuleType else None,
            "CRITICAL": RuleType.CRITICAL if RuleType else None,
        }

        rt = rule_type_map.get(rule_type, RuleType.ALL if RuleType else None)

        try:
            # Run validation in TESTING mode to get results back
            from main import ExecutionMode

            result_generator = run_gherkin_validation(
                filename=file_path,
                rule_type=rt,
                max_outcomes=max_outcomes,
                with_console_output=False,
                execution_mode=ExecutionMode.TESTING,  # Важно для получения результатов
            )

            # Iterate generator to get results
            # Collect ALL results (outcomes, scenarios, etc.)
            all_results = []
            for result in result_generator:
                all_results.append(result)

            # Если результатов нет - behave упал до запуска тестов
            if len(all_results) == 0:
                self.errors.append(
                    "Gherkin validation failed to run - check Django/setup errors"
                )
                return {
                    "valid": False,
                    "errors": self.errors,
                    "warnings": self.warnings,
                    "error_count": len(self.errors),
                    "warning_count": len(self.warnings),
                    "results": {},
                }

            # Parse all results
            for result in all_results:
                if result:  # Skip None results
                    if isinstance(result, str):
                        # JSON string result
                        import json

                        result = json.loads(result)
                    self._parse_results(result)

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

    def _validate_pse_only(self, file_path: str, max_outcomes: int) -> Dict[str, Any]:
        """Validate PSet Library using only PSE rules."""
        import subprocess
        import tempfile
        import os
        import json
        import base64

        # Находим путь к ifc-gherkin-rules
        cwd = os.path.dirname(os.path.abspath(__file__))
        vendor_path = None

        # Ищем vendor относительно текущего файла или корня проекта
        for base in [
            os.path.join(cwd, "..", "vendor"),
            os.path.join(cwd, "..", "..", "vendor"),
            "vendor",
        ]:
            candidate = os.path.abspath(os.path.join(base, "ifc-gherkin-rules"))
            if os.path.exists(candidate):
                vendor_path = candidate
                break

        if not vendor_path:
            self.errors.append("ifc-gherkin-rules not found")
            return {
                "valid": False,
                "errors": self.errors,
                "warnings": self.warnings,
                "error_count": len(self.errors),
                "warning_count": len(self.warnings),
                "results": {},
            }

        fd, jsonfn = tempfile.mkstemp("pse.json")

        try:
            # Запускаем behave только с PSE правилами (по тегу @PSE)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "behave",
                    "--tags",
                    "@PSE",  # Только PSE правила по тегу
                    "--tags=-disabled",
                    "--define",
                    f"input={os.path.abspath(file_path)}",
                    "--define",
                    f"max_outcomes_per_rule={max_outcomes}",
                    "--define",
                    "execution_mode=ExecutionMode.TESTING",
                    "-f",
                    "outcome_embedding_json",
                    "-o",
                    jsonfn,
                ],
                cwd=vendor_path,
                capture_output=True,
            )

            # Читаем результаты
            with open(jsonfn) as f:
                log = json.load(f)

            # Парсим outcomes
            for item in log:
                for el in item.get("elements", []):
                    # Protocol errors
                    for key in ["protocol_errors", "caught_exceptions"]:
                        data = self._decode_and_load_data(el, key)
                        if data:
                            if key == "protocol_errors":
                                for error in data:
                                    self.errors.append(f"Protocol error: {error}")
                            else:
                                for exc in data:
                                    exc_type = exc.get("type", "Unknown")
                                    exc_msg = exc.get("message", str(exc))
                                    self.errors.append(
                                        f"Exception: {exc_type}: {exc_msg}"
                                    )

                    # Validation outcomes
                    validation_outcomes = (
                        json.loads(
                            base64.b64decode(
                                el.get("validation_outcomes", [{}])[0].get("data", "")
                            ).decode("utf-8")
                        )
                        if el.get("validation_outcomes")
                        else []
                    )
                    for outcome in validation_outcomes:
                        severity = outcome.get("severity", "warning")
                        message = outcome.get("message", str(outcome))
                        if severity == "error":
                            self.errors.append(message)
                        elif severity == "warning":
                            self.warnings.append(message)

        except Exception as e:
            self.errors.append(f"PSE validation error: {str(e)}")
        finally:
            os.close(fd)
            os.unlink(jsonfn)

        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "results": {},
        }

    def _decode_and_load_data(self, element, key):
        """Decode base64 encoded data and load it as json"""
        import json
        import base64

        return (
            json.loads(
                base64.b64decode(element.get(key, [{}])[0].get("data", "")).decode(
                    "utf-8"
                )
            )
            if element.get(key)
            else []
        )

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
        # Results can be:
        # 1. Feature summary: {'feature_name': ..., 'rule_is_disabled': ...}
        # 2. protocol_errors: {'protocol_errors': [...]}
        # 3. caught_exceptions: {'caught_exceptions': [...]}
        # 4. validation_outcome: {'severity': ..., 'outcome_code': ..., 'message': ...}
        # 5. Old format with outcomes list: {'outcomes': [...], 'scenarios': [...]}

        # Skip feature summaries
        if "feature_name" in result and "rule_is_disabled" in result:
            return

        # Check for protocol errors
        if "protocol_errors" in result:
            for error in result["protocol_errors"]:
                self.errors.append(f"Protocol error: {error}")

        # Check for caught exceptions
        if "caught_exceptions" in result:
            for exc in result["caught_exceptions"]:
                self.errors.append(
                    f"Exception: {exc.get('type', 'Unknown')}: {exc.get('message', str(exc))}"
                )

        # Old format: outcomes list
        if "outcomes" in result:
            for outcome in result["outcomes"]:
                severity = outcome.get("severity", "warning")
                message = outcome.get("message", str(outcome))
                if severity == "error":
                    self.errors.append(message)
                elif severity == "warning":
                    self.warnings.append(message)

        # Old format: scenarios
        if "scenarios" in result:
            failed_count = 0
            for scenario in result["scenarios"]:
                if scenario.get("status") == "failed":
                    failed_count += 1
                    if failed_count <= 10:
                        self.errors.append(
                            f"Scenario '{scenario.get('name', 'unknown')}' failed"
                        )
            if failed_count > 10:
                self.errors.append(f"... and {failed_count - 10} more failed scenarios")

        # New format: direct outcome (from TESTING mode)
        if "severity" in result and "outcomes" not in result:
            severity = result.get("severity", "warning")
            message = result.get("message", str(result))

            if severity == "error":
                self.errors.append(message)
            elif severity == "warning":
                self.warnings.append(message)
            elif severity == "passed":
                pass  # OK

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
