/**
 * IDS2PSET App - основная логика приложения
 */

class IDS2PSETApp {
    constructor() {
        this.files = new Map();
        this.psets = {};
        this.selectedPSetNames = new Set();
        this.ifcContent = null;
        this.logs = [];

        this.init();
    }

    /**
     * Инициализация приложения
     */
    init() {
        this.setupDropZone();
        this.setupFileInput();
        this.setupButtons();
        this.log('Приложение инициализировано');
    }

    /**
     * Настройка drag-and-drop зоны
     */
    setupDropZone() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');

        // Клик по зоне -> открытие диалога выбора файлов
        dropZone.addEventListener('click', () => fileInput.click());

        // Drag events
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            this.handleFiles(e.dataTransfer.files);
        });
    }

    /**
     * Настройка input файла
     */
    setupFileInput() {
        const fileInput = document.getElementById('file-input');
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
            fileInput.value = ''; // Сброс для повторной загрузки
        });
    }

    /**
     * Настройка кнопок
     */
    setupButtons() {
        const generateBtn = document.getElementById('generate-btn');
        const downloadBtn = document.getElementById('download-btn');
        const logBtn = document.getElementById('log-btn');

        generateBtn?.addEventListener('click', () => this.generate());
        downloadBtn?.addEventListener('click', () => this.download());
        logBtn?.addEventListener('click', () => this.toggleLog());
    }

    /**
     * Обработка загруженных файлов
     * @param {FileList} fileList - Список файлов
     */
    async handleFiles(fileList) {
        for (const file of fileList) {
            if (!file.name.endsWith('.ids')) {
                this.log(`⚠️ Пропущен файл: ${file.name} (не .ids)`);
                continue;
            }

            this.log(`📁 Загрузка: ${file.name}`);
            this.files.set(file.name, file);
            this.renderFilesList();

            // Парсинг IDS
            try {
                const content = await file.text();
                const result = await window.pyodideBridge.parseIDS(content);
                this.mergePSets(result, file.name);
                this.log(`✓ Распарсен: ${file.name}`);
            } catch (error) {
                this.log(`✗ Ошибка парсинга ${file.name}: ${error.message}`);
            }
        }

        if (Object.keys(this.psets).length > 0) {
            this.renderPSetTree();
            document.getElementById('preview-section').classList.remove('hidden');
        }
    }

    /**
     * Объединение PSet из разных IDS
     * @param {Object} newPSets - Новые данные PSet
     * @param {string} sourceFile - Имя файла IDS источника
     */
    mergePSets(newPSets, sourceFile) {
        for (const [name, pset] of Object.entries(newPSets)) {
            if (!this.psets[name]) {
                this.psets[name] = { ...pset, source: sourceFile };
                this.selectedPSetNames.add(name);
            } else {
                // Объединение свойств
                const existing = this.psets[name];
                for (const prop of pset.properties) {
                    const exists = existing.properties.some(p => p.name === prop.name);
                    if (!exists) {
                        existing.properties.push(prop);
                    }
                }
                // Объединение entity
                for (const entity of pset.applicable_entities) {
                    if (!existing.applicable_entities.includes(entity)) {
                        existing.applicable_entities.push(entity);
                    }
                }
            }
        }
    }

    /**
     * Отрисовка списка файлов
     */
    renderFilesList() {
        const container = document.getElementById('files-list');
        container.innerHTML = '';

        for (const [name, file] of this.files) {
            const item = document.createElement('div');
            item.className = 'file-item';

            // Подсчитываем PSet и свойства с regex patterns для этого файла
            let patternPSetCount = 0;
            let patternPropCount = 0;
            for (const [psetName, pset] of Object.entries(this.psets)) {
                if (pset.source === name) {
                    if (pset.is_pattern) patternPSetCount++;
                    patternPropCount += pset.properties.filter(p => p.is_pattern).length;
                }
            }

            item.innerHTML = `
                <span class="file-item__name">✓ ${name}</span>
                <button class="file-item__remove" data-file="${name}">×</button>
                ${patternPSetCount > 0 ? `<div class="file-item__warning">⚠️ ${patternPSetCount} PSet с regex</div>` : ''}
                ${patternPropCount > 0 ? `<div class="file-item__warning">⚠️ ${patternPropCount} свойств с regex</div>` : ''}
            `;
            container.appendChild(item);
        }

        // Обработчики удаления
        container.querySelectorAll('.file-item__remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const name = e.target.dataset.file;
                this.files.delete(name);

                // Удаляем PSet из этого IDS
                const psetsToRemove = [];
                for (const [psetName, pset] of Object.entries(this.psets)) {
                    if (pset.source === name) {
                        psetsToRemove.push(psetName);
                        this.selectedPSetNames.delete(psetName);
                    }
                }
                psetsToRemove.forEach(psetName => delete this.psets[psetName]);

                // Скрываем панель деталей если она открыта
                const detailsPanel = document.getElementById('pset-details');
                if (detailsPanel) {
                    detailsPanel.classList.add('hidden');
                }

                this.renderFilesList();
                this.renderPSetTree();

                if (Object.keys(this.psets).length === 0) {
                    document.getElementById('preview-section').classList.add('hidden');
                    document.getElementById('result-section').classList.add('hidden');
                }
            });
        });
    }

    /**
     * Форматирование списка entities для отображения
     * Если больше 5 — показываем первое, многоточие, последнее и количество
     * @param {string[]} entities - Список entities
     * @returns {string} Отформатированная строка
     */
    formatEntities(entities) {
        if (!entities || entities.length === 0) {
            return '';
        }
        if (entities.length <= 5) {
            return entities.join(', ');
        }
        // Больше 5: первое, многоточие, последнее и количество
        return `${entities[0]}, ... , ${entities[entities.length - 1]} [${entities.length}]`;
    }

    /**
     * Отрисовка дерева PSet
     */
    renderPSetTree() {
        const container = document.getElementById('pset-tree');
        container.innerHTML = '';

        for (const [name, pset] of Object.entries(this.psets)) {
            const node = document.createElement('div');
            node.className = 'tree-node';

            // Подсчитываем свойства с regex
            const patternProps = pset.properties.filter(p => p.is_pattern);
            const patternCount = patternProps.length;

            node.innerHTML = `
                <div class="tree-node__header">
                    <input type="checkbox"
                           id="pset-${name}"
                           ${this.selectedPSetNames.has(name) ? 'checked' : ''}
                           data-pset="${name}">
                    <label for="pset-${name}">
                        📦 ${name} (${this.formatEntities(pset.applicable_entities)})
                        ${pset.is_pattern ? '<span class="tree-node__warning">⚠️ PSet с regex</span>' : ''}
                    </label>
                </div>
                ${patternCount > 0 ? `<div class="tree-node__pattern-warning">⚠️ ${patternCount} свойств описаны через regex — не будут созданы</div>` : ''}
                <div class="tree-node__children">
                    ${pset.properties.filter(prop => !prop.is_pattern).map(prop => {
                        const measureType = prop.data_type || 'IfcText';
                        const templateType = prop.template_type || 'P_SINGLEVALUE';
                        return `
                        <div class="property-item">
                            <div class="property-item__header">
                                ${this.getDataTypeIcon(prop.data_type)}
                                ${prop.name} (${measureType}, ${templateType})
                            </div>
                            ${prop.description ? `<div class="property-item__description">${prop.description}</div>` : ''}
                        </div>
                    `}).join('')}
                </div>
            `;
            container.appendChild(node);
        }

        // Обработчики чекбоксов
        container.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.addEventListener('change', (e) => {
                const name = e.target.dataset.pset;
                if (e.target.checked) {
                    this.selectedPSetNames.add(name);
                } else {
                    this.selectedPSetNames.delete(name);
                }
            });
        });
    }

    /**
     * Иконка типа данных
     */
    getDataTypeIcon(dataType) {
        const icons = {
            'IFCTEXT': '🔤',
            'IFCINTEGER': '🔢',
            'IFCREAL': '🔢',
            'IFCBOOLEAN': '☑',
            'IFCLENGTHMEASURE': '📏',
            'IFCVOLUMEMEASURE': '📦'
        };
        return icons[dataType] || '📄';
    }

    /**
     * Генерация IFC
     */
    async generate() {
        const selectedPSets = {};
        for (const name of this.selectedPSetNames) {
            selectedPSets[name] = this.psets[name];
        }

        if (Object.keys(selectedPSets).length === 0) {
            alert('Выберите хотя бы один PSet');
            return;
        }

        document.getElementById('progress-section').classList.remove('hidden');
        this.log('🔄 Генерация IFC...');

        try {
            // Получение имени первого файла
            const firstName = this.files.keys().next().value;
            const baseName = firstName.replace('.ids', '');

            this.ifcContent = await window.pyodideBridge.generateIFC(
                selectedPSets,
                Array.from(this.selectedPSetNames)
            );

            this.log('✓ IFC сгенерирован');
            this.showResult(baseName + '_PSet_Library.ifc');
        } catch (error) {
            this.log(`✗ Ошибка генерации: ${error.message}`);
        }

        document.getElementById('progress-section').classList.add('hidden');
    }

    /**
     * Отображение результата
     */
    showResult(fileName) {
        const stats = document.getElementById('stats');
        const fileInfo = document.getElementById('file-info');

        stats.innerHTML = `
            <ul>
                <li>PSet: ${this.selectedPSetNames.size}</li>
                <li>Свойств: ${this.getTotalPropertiesCount()}</li>
            </ul>
        `;
        fileInfo.textContent = `📄 Файл: ${fileName}`;

        // Сохраняем имя файла для скачивания
        this.outputFileName = fileName;

        document.getElementById('result-section').classList.remove('hidden');
    }

    /**
     * Подсчёт общего количества свойств
     */
    getTotalPropertiesCount() {
        let count = 0;
        for (const name of this.selectedPSetNames) {
            count += this.psets[name].properties.length;
        }
        return count;
    }

    /**
     * Скачивание IFC
     */
    download() {
        if (!this.ifcContent) return;

        const blob = new Blob([this.ifcContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = this.outputFileName || 'IDS2PSET_Library.ifc';
        a.click();
        URL.revokeObjectURL(url);

        this.log('⬇ Файл скачан');
    }

    /**
     * Переключение панели логов
     */
    toggleLog() {
        const section = document.getElementById('log-section');
        section.classList.toggle('hidden');
    }

    /**
     * Добавление записи в лог
     */
    log(message) {
        const timestamp = new Date().toLocaleTimeString('ru-RU');
        const entry = `[${timestamp}] ${message}`;
        this.logs.push(entry);

        const logContent = document.getElementById('log-content');
        if (logContent) {
            logContent.textContent = this.logs.join('\n');
        }

        console.log(entry);
    }
}

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    window.app = new IDS2PSETApp();
});
