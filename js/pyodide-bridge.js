/**
 * Pyodide Bridge - связующий модуль между JS и Python
 */

class PyodideBridge {
    constructor() {
        this.pyodide = null;
        this.initialized = false;
        this.pythonModulesLoaded = false;
        this.ifcOpenshellLoaded = false;
    }

    /**
     * Инициализация Pyodide
     */
    async init() {
        if (this.initialized) {
            return this.pyodide;
        }

        // Загрузка Pyodide (dev версия)
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/pyodide/dev/full/pyodide.js';
        await new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });

        // Инициализация
        this.pyodide = await loadPyodide({
            indexURL: 'https://cdn.jsdelivr.net/pyodide/dev/full/'
        });

        this.initialized = true;
        return this.pyodide;
    }

    /**
     * Загрузка Python модулей из src/ и wheels/
     * @param {boolean} needIFCOpenShell - Загружать ли ifcopenshell
     */
    async loadModules(needIFCOpenShell = true) {
        await this.init();

        if (this.pythonModulesLoaded && (!needIFCOpenShell || this.ifcOpenshellLoaded)) {
            return true;
        }

        // Загрузка micropip для установки пакетов
        await this.pyodide.loadPackage('micropip');
        const micropip = this.pyodide.pyimport('micropip');

        // Установка ifcopenshell из CDN (только если нужен)
        if (needIFCOpenShell && !this.ifcOpenshellLoaded) {
            try {
                // Используем jsdelivr CDN для CORS доступа
                const wheelUrl = 'https://cdn.jsdelivr.net/gh/VDobranov/IDS2PSET@main/wheels/ifcopenshell-0.8.4-cp313-cp313-pyodide_2025_0_wasm32.whl';

                // Установка через micropip с URL
                await micropip.install(wheelUrl);
                this.ifcOpenshellLoaded = true;
            } catch (e) {
                console.error('Ошибка установки ifcopenshell:', e);
                throw new Error('ifcopenshell недоступен: ' + e.message);
            }
        }

        // Копирование локальных модулей в файловую систему Pyodide (только один раз)
        if (!this.pythonModulesLoaded) {
            this.pyodide.FS.mkdir('/src');

            // Загрузка ids_parser.py
            const idsParserResponse = await fetch('./src/ids_parser.py');
            const idsParserContent = await idsParserResponse.text();
            this.pyodide.FS.writeFile('/src/ids_parser.py', idsParserContent);

            // Загрузка pset_generator.py
            const psetGeneratorResponse = await fetch('./src/pset_generator.py');
            const psetGeneratorContent = await psetGeneratorResponse.text();
            this.pyodide.FS.writeFile('/src/pset_generator.py', psetGeneratorContent);

            // Загрузка validator.py
            const validatorResponse = await fetch('./src/validator.py');
            const validatorContent = await validatorResponse.text();
            this.pyodide.FS.writeFile('/src/validator.py', validatorContent);

            this.pythonModulesLoaded = true;
        }

        return true;
    }

    /**
     * Парсинг IDS файла
     * @param {string} content - Содержимое IDS файла
     * @returns {Promise<Object>} - Распарсенные данные PSet
     */
    async parseIDS(content) {
        // Загружаем только Python модули, без ifcopenshell
        await this.loadModules(false);

        // Передача контента в Python
        this.pyodide.FS.writeFile('/tmp/input.ids', content);

        // Выполнение Python кода
        const result = this.pyodide.runPython(`
            import sys
            sys.path.insert(0, '/src')
            from ids_parser import parse_ids_file
            import json

            psets = parse_ids_file('/tmp/input.ids')

            # Конвертация в JSON-сериализуемый формат
            result = {}
            for name, pset in psets.items():
                result[name] = {
                    'name': pset.name,
                    'properties': [
                        {
                            'name': p.name,
                            'property_set': p.property_set,
                            'data_type': p.data_type,
                            'cardinality': p.cardinality,
                            'description': p.description,
                            'enum_values': p.enum_values
                        }
                        for p in pset.properties
                    ],
                    'applicable_entities': pset.applicable_entities
                }

            json.dumps(result)
        `);

        return JSON.parse(result);
    }

    /**
     * Генерация IFC файла
     * @param {Object} psets - Данные PSet
     * @param {Array} selectedPSetNames - Выбранные имена PSet
     * @returns {Promise<string>} - Содержимое IFC файла
     */
    async generateIFC(psets, selectedPSetNames) {
        // Загружаем модули с ifcopenshell
        await this.loadModules(true);

        // Фильтрация выбранных PSet
        const filteredPSetNames = selectedPSetNames || Object.keys(psets);

        // Конвертация JS объекта в Python формат
        const psetsJson = JSON.stringify(psets);
        const selectedJson = JSON.stringify(filteredPSetNames);

        // Выполнение Python кода
        const ifcContent = this.pyodide.runPython(`
            import sys
            sys.path.insert(0, '/src')
            from pset_generator import PSetGenerator
            import json

            # Загрузка данных
            psets_data = json.loads('${psetsJson}')
            selected_names = json.loads('${selectedJson}')

            # Фильтрация
            filtered_psets = {
                name: pset for name, pset in psets_data.items()
                if name in selected_names
            }

            # Генерация IFC
            generator = PSetGenerator()
            ifc_content = generator.generate(filtered_psets)

            ifc_content
        `);

        return ifcContent;
    }

    /**
     * Валидация IFC файла
     * @param {string} ifcContent - Содержимое IFC файла
     * @returns {Promise<Object>} - Результат валидации
     */
    async validateIFC(ifcContent) {
        // Загружаем модули с ifcopenshell для валидации
        await this.loadModules(true);

        // Запись IFC в файл
        this.pyodide.FS.writeFile('/tmp/output.ifc', ifcContent);

        // Выполнение Python кода
        const result = this.pyodide.runPython(`
            import sys
            sys.path.insert(0, '/src')
            from validator import IFCValidator
            import json

            validator = IFCValidator()
            result = validator.validate_file('/tmp/output.ifc')
            json.dumps(result)
        `);

        return JSON.parse(result);
    }

    /**
     * Очистка ресурсов
     */
    cleanup() {
        if (this.pyodide) {
            this.pyodide.FS.unlink('/tmp/input.ids');
        }
    }
}

// Экспорт экземпляра
window.pyodideBridge = new PyodideBridge();
