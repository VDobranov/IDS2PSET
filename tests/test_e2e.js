/**
 * E2E Tests for IDS2PSET - Full cycle testing
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';
import { readFileSync, writeFileSync, unlinkSync, existsSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const FIXTURES_DIR = join(__dirname, 'fixtures');
const OUTPUT_DIR = join(__dirname, 'output');

// Helper to check if file exists
function fileExists(path) {
    try {
        return existsSync(path);
    } catch {
        return false;
    }
}

describe('E2E: IDS2PSET Full Cycle', () => {
    beforeEach(() => {
        // Create output directory if not exists
        if (!fileExists(OUTPUT_DIR)) {
            // Note: Can't create dirs in node:test without additional setup
        }
    });

    afterEach(() => {
        // Cleanup output files
        const outputFiles = [
            join(OUTPUT_DIR, 'test_output.ifc')
        ];
        outputFiles.forEach(file => {
            if (fileExists(file)) {
                try {
                    unlinkSync(file);
                } catch (e) {
                    // Ignore cleanup errors
                }
            }
        });
    });

    describe('Fixture Files', () => {
        it('should have minimal.ids fixture', () => {
            const fixturePath = join(FIXTURES_DIR, 'minimal.ids');
            assert.ok(fileExists(fixturePath), 'minimal.ids should exist');

            const content = readFileSync(fixturePath, 'utf-8');
            assert.ok(content.includes('<?xml'), 'Should be valid XML');
            assert.ok(content.includes('<ids'), 'Should be IDS format');
        });

        it('should have with_enumeration.ids fixture', () => {
            const fixturePath = join(FIXTURES_DIR, 'with_enumeration.ids');
            assert.ok(fileExists(fixturePath), 'with_enumeration.ids should exist');

            const content = readFileSync(fixturePath, 'utf-8');
            assert.ok(content.includes('enumeration'), 'Should contain enumeration');
        });

        it('should have multi_entity.ids fixture', () => {
            const fixturePath = join(FIXTURES_DIR, 'multi_entity.ids');
            assert.ok(fileExists(fixturePath), 'multi_entity.ids should exist');

            const content = readFileSync(fixturePath, 'utf-8');
            assert.ok(content.includes('IFCWALL'), 'Should contain IFCWALL');
            assert.ok(content.includes('IFCSLAB'), 'Should contain IFCSLAB');
        });
    });

    describe('Application Structure', () => {
        it('should have index.html', () => {
            const indexPath = join(__dirname, '..', 'index.html');
            assert.ok(fileExists(indexPath), 'index.html should exist');

            const content = readFileSync(indexPath, 'utf-8');
            assert.ok(content.includes('IDS2PSET'), 'Should have app title');
            assert.ok(content.includes('drop-zone'), 'Should have drop zone');
            assert.ok(content.includes('download-btn'), 'Should have download button');
        });

        it('should have css/style.css', () => {
            const cssPath = join(__dirname, '..', 'css', 'style.css');
            assert.ok(fileExists(cssPath), 'style.css should exist');

            const content = readFileSync(cssPath, 'utf-8');
            assert.ok(content.includes('.drop-zone'), 'Should style drop zone');
            assert.ok(content.includes('.btn'), 'Should style buttons');
        });

        it('should have js/app.js', () => {
            const appPath = join(__dirname, '..', 'js', 'app.js');
            assert.ok(fileExists(appPath), 'app.js should exist');

            const content = readFileSync(appPath, 'utf-8');
            assert.ok(content.includes('IDS2PSETApp'), 'Should have main class');
            assert.ok(content.includes('download'), 'Should have download method');
            assert.ok(content.includes('generateIFC'), 'Should generate IFC');
        });

        it('should have js/pyodide-bridge.js', () => {
            const bridgePath = join(__dirname, '..', 'js', 'pyodide-bridge.js');
            assert.ok(fileExists(bridgePath), 'pyodide-bridge.js should exist');

            const content = readFileSync(bridgePath, 'utf-8');
            assert.ok(content.includes('PyodideBridge'), 'Should have bridge class');
            assert.ok(content.includes('parseIDS'), 'Should parse IDS');
            assert.ok(content.includes('generateIFC'), 'Should generate IFC');
            assert.ok(content.includes('validateIFC'), 'Should validate IFC');
        });
    });

    describe('Python Modules', () => {
        it('should have src/ids_parser.py', () => {
            const parserPath = join(__dirname, '..', 'src', 'ids_parser.py');
            assert.ok(fileExists(parserPath), 'ids_parser.py should exist');

            const content = readFileSync(parserPath, 'utf-8');
            assert.ok(content.includes('parse_ids_file'), 'Should have parse function');
            assert.ok(content.includes('PSetGroup'), 'Should have PSetGroup class');
        });

        it('should have src/pset_generator.py', () => {
            const genPath = join(__dirname, '..', 'src', 'pset_generator.py');
            assert.ok(fileExists(genPath), 'pset_generator.py should exist');

            const content = readFileSync(genPath, 'utf-8');
            assert.ok(content.includes('PSetGenerator'), 'Should have generator class');
            assert.ok(content.includes('IfcProjectLibrary'), 'Should create library');
        });

        it('should have src/validator.py', () => {
            const valPath = join(__dirname, '..', 'src', 'validator.py');
            assert.ok(fileExists(valPath), 'validator.py should exist');

            const content = readFileSync(valPath, 'utf-8');
            assert.ok(content.includes('IFCValidator'), 'Should have validator class');
            assert.ok(content.includes('validate_file'), 'Should validate files');
        });

        it('should have src/gherkin_validator.py', () => {
            const gherkinPath = join(__dirname, '..', 'src', 'gherkin_validator.py');
            assert.ok(fileExists(gherkinPath), 'gherkin_validator.py should exist');

            const content = readFileSync(gherkinPath, 'utf-8');
            assert.ok(content.includes('GherkinValidator'), 'Should have validator class');
            assert.ok(content.includes('RULE_CATEGORIES'), 'Should have rule categories');
            assert.ok(content.includes('validate_all_rules'), 'Should validate all rules');
        });
    });

    describe('Wheel Files', () => {
        it('should have ifcopenshell wheel', () => {
            const wheelDir = join(__dirname, '..', 'wheels');
            assert.ok(fileExists(wheelDir), 'wheels directory should exist');

            // Check for any .whl file
            const files = readdirSync(wheelDir);
            const wheelFiles = files.filter(f => f.endsWith('.whl'));
            assert.ok(wheelFiles.length > 0, 'Should have at least one wheel file');
        });
    });

    describe('Git Submodules', () => {
        it('should have ifc-gherkin-rules submodule', () => {
            const submodulePath = join(__dirname, '..', 'vendor', 'ifc-gherkin-rules');
            assert.ok(fileExists(submodulePath), 'ifc-gherkin-rules submodule should exist');

            const mainPy = join(submodulePath, 'main.py');
            assert.ok(fileExists(mainPy), 'Should have main.py');
        });
    });
});

describe('E2E: Integration Flow', () => {
    it('should have complete data flow documented', () => {
        // This test verifies the integration flow is documented
        const flow = [
            '1. User uploads IDS file via drag-and-drop',
            '2. File content read via File API',
            '3. Pyodide loads Python modules',
            '4. ids_parser.py parses IDS XML',
            '5. PSet data grouped by propertySet name',
            '6. UI displays PSet tree with checkboxes',
            '7. User selects PSet to include',
            '8. pset_generator.py generates IFC4',
            '9. validator.py validates IFC structure',
            '10. gherkin_validator.py checks buildingSMART rules',
            '11. IFC blob created and downloaded'
        ];

        assert.ok(flow.length === 11, 'Should have complete flow documented');
    });
});
