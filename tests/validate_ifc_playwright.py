#!/usr/bin/env python3
"""
IFC Validation Script для Playwright E2E тестов.

Использование:
    python validate_ifc_playwright.py [path_to_ifc_file]

По умолчанию использует: .playwright-mcp/IDS2PSET-Library.ifc
"""

import sys
import os


def validate_ifc_file(ifc_path):
    """Validate IFC file and return True if all checks pass."""

    print("=" * 60)
    print("ВАЛИДАЦИЯ IFC ФАЙЛА (Playwright E2E тест)")
    print("=" * 60)

    # 1. Проверка существования файла
    if not os.path.exists(ifc_path):
        print(f"✗ Файл не найден: {ifc_path}")
        return False

    with open(ifc_path, "r") as f:
        ifc_content = f.read()

    print(f"\n1. ✓ Файл прочитан ({len(ifc_content)} байт)")

    # 2. Проверка структуры IFC
    checks = {
        "ISO-10303-21 заголовок": "ISO-10303-21" in ifc_content,
        "IFC4 версия": "IFC4" in ifc_content,
        "IFCPROJECTLIBRARY": "IFCPROJECTLIBRARY" in ifc_content,
        "IFCPROPERTYSETTEMPLATE": "IFCPROPERTYSETTEMPLATE" in ifc_content,
        "IFCSIMPLEPROPERTYTEMPLATE": "IFCSIMPLEPROPERTYTEMPLATE" in ifc_content,
        "IFCRELDECLARES": "IFCRELDECLARES" in ifc_content,
        "ISO-10303-21 футер": "END-ISO-10303-21" in ifc_content,
    }

    print("\n2. Структура IFC:")
    all_passed = True
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False

    # 3. Валидация через ifcopenshell
    print("\n3. ifcopenshell валидация:")
    try:
        import ifcopenshell

        f = ifcopenshell.open(ifc_path)
        print(f"   ✓ Файл открыт (schema: {f.schema})")

        libraries = f.by_type("IfcProjectLibrary")
        print(f"   ✓ IfcProjectLibrary: {len(libraries)}")

        templates = f.by_type("IfcPropertySetTemplate")
        print(f"   ✓ IfcPropertySetTemplate: {len(templates)}")

        for t in templates:
            print(f"      - {t.Name} (entity: {t.ApplicableEntity or 'N/A'})")

        simple_templates = f.by_type("IfcSimplePropertyTemplate")
        print(f"   ✓ IfcSimplePropertyTemplate: {len(simple_templates)}")

        for prop in simple_templates:
            # IFC4 использует PrimaryMeasureType вместо DataType
            measure_type = getattr(prop, "PrimaryMeasureType", None)
            print(f"      - {prop.Name} ({prop.TemplateType}, {measure_type or 'N/A'})")

        declares = f.by_type("IfcRelDeclares")
        print(f"   ✓ IfcRelDeclares: {len(declares)}")

    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        all_passed = False

    # 4. Валидация через ifcopenshell.validate
    print("\n4. ifcopenshell.validate валидация:")
    try:
        import ifcopenshell
        import ifcopenshell.validate

        f = ifcopenshell.open(ifc_path)
        logger = ifcopenshell.validate.json_logger()
        ifcopenshell.validate.validate(ifc_path, logger)

        if logger.statements:
            print(f"   ✗ Найдено ошибок: {len(logger.statements)}")
            for stmt in logger.statements[:5]:
                if isinstance(stmt, dict):
                    print(f"      - {stmt.get('type')}: {stmt.get('message', stmt)}")
                else:
                    print(f"      - {stmt}")
            all_passed = False
        else:
            print("   ✓ ifcopenshell.validate: ошибок нет")

    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        all_passed = False

    # 5. Валидация через gherkin-rules (только для полных моделей зданий)
    print("\n5. gherkin-rules валидация:")
    try:
        # Добавляем src в path
        src_path = os.path.join(os.path.dirname(__file__), "..", "src")
        sys.path.insert(0, src_path)

        from gherkin_validator import GherkinValidator, GHERKIN_AVAILABLE

        if GHERKIN_AVAILABLE:
            # Проверяем тип файла
            import ifcopenshell

            f = ifcopenshell.open(ifc_path)
            libraries = f.by_type("IfcProjectLibrary")
            has_buildings = len(f.by_type("IfcBuilding")) > 0

            is_pset_library = len(libraries) > 0 and not has_buildings

            if is_pset_library:
                print("   ℹ PSet Library — gherkin правила не применимы")
                print("   (gherkin требует IfcPropertySet, IfcBuilding, геометрию)")
            else:
                validator = GherkinValidator()
                result = validator.validate_file(ifc_path, rule_type="ALL")

                if result["valid"]:
                    print("   ✓ gherkin-rules: пройдено")
                else:
                    print(f"   ✗ Найдено ошибок: {result['error_count']}")
                    for error in result["errors"][:5]:
                        print(f"      - {error}")
                    all_passed = False  # gherkin ошибка = провал всей валидации
        else:
            print("   ⚠ Gherkin validator недоступен")

    except Exception as e:
        print(f"   ⚠ Пропущено: {e}")

    # 6. Итог
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ВСЕ ВАЛИДАЦИИ ПРОЙДЕНЫ")
        return True
    else:
        print("✗ НЕКОТОРЫЕ ВАЛИДАЦИИ НЕ ПРОЙДЕНЫ")
        return False


if __name__ == "__main__":
    # Путь по умолчанию
    ifc_path = ".playwright-mcp/IDS2PSET-Library.ifc"

    # Или из аргумента командной строки
    if len(sys.argv) > 1:
        ifc_path = sys.argv[1]

    success = validate_ifc_file(ifc_path)
    sys.exit(0 if success else 1)
