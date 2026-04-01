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
                this.mergePSets(result);
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
     */
    mergePSets(newPSets) {
        for (const [name, pset] of Object.entries(newPSets)) {
            if (!this.psets[name]) {
                this.psets[name] = pset;
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
            item.innerHTML = `
                <span class="file-item__name">✓ ${name}</span>
                <button class="file-item__remove" data-file="${name}">×</button>
            `;
            container.appendChild(item);
        }

        // Обработчики удаления
        container.querySelectorAll('.file-item__remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const name = e.target.dataset.file;
                this.files.delete(name);
                this.renderFilesList();
            });
        });
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
            node.innerHTML = `
                <div class="tree-node__header">
                    <input type="checkbox" 
                           id="pset-${name}" 
                           ${this.selectedPSetNames.has(name) ? 'checked' : ''}
                           data-pset="${name}">
                    <label for="pset-${name}">
                        📦 ${name} (${pset.properties.length} свойств, 
                        ${pset.applicable_entities.join(', ')})
                    </label>
                </div>
                <div class="tree-node__children">
                    ${pset.properties.map(prop => `
                        <div class="property-item">
                            ${this.getDataTypeIcon(prop.data_type)}
                            ${prop.name} (${prop.cardinality})
                            ${prop.enum_values.length > 0 ? ` [${prop.enum_values.length} значений]` : ''}
                        </div>
                    `).join('')}
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
        a.download = 'IDS2PSET_Library.ifc';
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
