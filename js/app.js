/**
 * IDS2PSET App - основная логика приложения
 */

class IDS2PSETApp {
    constructor() {
        this.files = new Map();
        this.psetsByIDS = {}; // { idsName: { psetName: psetData } }
        this.selectedPSetNames = new Set();
        this.ifcByIDS = {}; // { idsName: ifcContent or 'generating' }
        this.logs = [];

        this.init();
    }

    /**
     * Склонение существительных: 1 файл, 2 файла, 5 файлов
     */
    declension(n, forms) {
        // forms: [единственное, 2-3-4, 5+]
        const mod10 = n % 10;
        const mod100 = n % 100;
        if (mod100 >= 11 && mod100 <= 19) return forms[2];
        if (mod10 === 1) return forms[0];
        if (mod10 >= 2 && mod10 <= 4) return forms[1];
        return forms[2];
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
        generateBtn?.addEventListener('click', () => this.generate());
    }

    /**
     * Обработка загруженных файлов
     * @param {FileList} fileList - Список файлов
     */
    async handleFiles(fileList) {
        for (const file of fileList) {
            if (!file.name.endsWith('.ids') && !file.name.endsWith('.xml')) {
                this.log(`Пропущен файл: ${file.name} (не .ids или .xml)`);
                continue;
            }

            this.log(`Загрузка: ${file.name}`);
            this.files.set(file.name, file);

            // Парсинг IDS
            try {
                const content = await file.text();
                const result = await window.pyodideBridge.parseIDS(content);
                this.mergePSets(result, file.name);
                this.log(`Распарсен: ${file.name}`);
            } catch (error) {
                this.log(`Ошибка парсинга ${file.name}: ${error.message}`);
            }

            // Рендер после парсинга
            this.renderFilesList();
        }

        // Показываем/скрываем preview-section с PSet
        const hasValidPSets = Object.values(this.psetsByIDS).some(psets =>
            Object.values(psets).some(pset => !pset.is_pattern)
        );
        const generateBtn = document.getElementById('generate-btn');

        if (hasValidPSets) {
            this.renderPSetColumns();
            document.getElementById('preview-section').classList.remove('hidden');
            generateBtn.disabled = false;
        } else {
            document.getElementById('preview-section').classList.add('hidden');
            generateBtn.disabled = true;
        }
    }

    /**
     * Добавление PSet из IDS
     * @param {Object} newPSets - Новые данные PSet
     * @param {string} sourceFile - Имя файла IDS источника
     */
    mergePSets(newPSets, sourceFile) {
        if (!this.psetsByIDS[sourceFile]) {
            this.psetsByIDS[sourceFile] = {};
        }
        for (const [name, pset] of Object.entries(newPSets)) {
            this.psetsByIDS[sourceFile][name] = { ...pset, source: sourceFile };
            this.selectedPSetNames.add(name);
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

            // Подсчитываем PSet и свойства с регулярными выражениями для этого файла
            let patternPSetCount = 0;
            let patternPropCount = 0;
            let validPSetCount = 0;
            let simpleValuePatternCount = 0; // regex в simpleValue (потенциально некорректный IDS)
            const idsPSets = this.psetsByIDS[name] || {};
            for (const [psetName, pset] of Object.entries(idsPSets)) {
                if (pset.is_pattern) patternPSetCount++;
                else validPSetCount++;
                patternPropCount += pset.properties.filter(p => p.is_pattern).length;
                if (pset.simple_value_pattern) simpleValuePatternCount++;
            }

            // Статус генерации для этого IDS
            const ifcStatus = this.ifcByIDS[name];
            const isGenerated = ifcStatus && ifcStatus !== 'generating';
            const allRegex = validPSetCount === 0;

            item.innerHTML = `
                <div class="file-item__content">
                    <div class="file-item__header">
                        <span class="file-item__name">${name}</span>
                        <button class="file-item__remove" data-file="${name}">×</button>
                    </div>
                    ${patternPSetCount > 0 ? `<div class="file-item__warning">${patternPSetCount} ${this.declension(patternPSetCount, ['PSet описан регулярным выражением', 'PSet описаны регулярными выражениями', 'PSet описаны регулярными выражениями'])}</div>` : ''}
                    ${patternPropCount > 0 ? `<div class="file-item__warning">${patternPropCount} ${this.declension(patternPropCount, ['свойство описано регулярным выражением', 'свойства описаны регулярными выражениями', 'свойств описано регулярными выражениями'])}</div>` : ''}
                    ${simpleValuePatternCount > 0 ? '<div class="file-item__warning file-item__warning--ids-issue">⚠️ Возможно, IDS некорректен — регулярные выражения указаны напрямую. Проверьте файл отдельно.</div>' : ''}
                    ${allRegex ? '<div class="file-item__warning file-item__warning--error">IFC не будет сгенерирован — все PSet описаны регулярными выражениями</div>' : ''}

                    ${isGenerated ? `
                    <div class="file-item__ifc">
                        <div class="file-item__ifc-status">Готово</div>
                        <button class="file-item__ifc-download" data-file="${name}">Скачать IFC</button>
                    </div>
                    ` : ''}
                </div>
            `;
            container.appendChild(item);
        }

        // Обработчики удаления
        container.querySelectorAll('.file-item__remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const name = e.target.dataset.file;
                this.files.delete(name);
                delete this.ifcByIDS[name];

                // Удаляем PSet из этого IDS
                delete this.psetsByIDS[name];
                this.selectedPSetNames.clear();
                for (const [idsName, psets] of Object.entries(this.psetsByIDS)) {
                    for (const psetName of Object.keys(psets)) {
                        this.selectedPSetNames.add(psetName);
                    }
                }

                // Скрываем панель деталей если она открыта
                const detailsPanel = document.getElementById('pset-details');
                if (detailsPanel) {
                    detailsPanel.classList.add('hidden');
                }

                this.renderFilesList();
                this.renderPSetColumns();

                // Обновляем состояние кнопки генерации и видимость секции
                const hasValidPSets = Object.values(this.psetsByIDS).some(psets =>
                    Object.values(psets).some(pset => !pset.is_pattern)
                );
                document.getElementById('generate-btn').disabled = !hasValidPSets;
                document.getElementById('preview-section').classList.toggle('hidden', !hasValidPSets);
            });
        });

        // Обработчики скачивания для каждого IDS
        container.querySelectorAll('.file-item__ifc-download').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const name = e.target.dataset.file;
                this.downloadIFCForIDS(name);
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
     * Отрисовка колонок PSet для каждого IDS
     */
    renderPSetColumns() {
        const container = document.getElementById('pset-container');
        container.innerHTML = '';

        // Считаем количество IDS с валидными PSet
        let validIDSCount = 0;
        for (const [source, psets] of Object.entries(this.psetsByIDS)) {
            const hasValid = Object.values(psets).some(pset => !pset.is_pattern);
            if (hasValid) validIDSCount++;
        }

        // Если нет IDS с валидными PSet, скрываем секцию
        if (validIDSCount === 0) {
            document.getElementById('preview-section').classList.add('hidden');
            document.getElementById('pset-nav-prev').classList.add('hidden');
            document.getElementById('pset-nav-next').classList.add('hidden');
            return;
        }

        // Создаём колонку только для IDS с валидными PSet
        for (const [source, psets] of Object.entries(this.psetsByIDS)) {
            const psetEntries = Object.entries(psets);
            const validPSets = psetEntries.filter(([name, pset]) => !pset.is_pattern);

            // Пропускаем IDS без валидных PSet
            if (validPSets.length === 0) continue;

            const patternCount = psetEntries.filter(([name, pset]) => pset.is_pattern).length;
            const column = document.createElement('div');
            column.className = 'pset-column';

            column.innerHTML = `
                <div class="pset-column__header">
                    <div class="pset-column__title">${source}</div>
                    ${patternCount > 0 ? `<div class="pset-column__pattern-warning">${patternCount} ${this.declension(patternCount, ['PSet описан регулярным выражением', 'PSet описаны регулярными выражениями', 'PSet описаны регулярными выражениями'])}</div>` : ''}
                </div>
                <div class="pset-column__content">
                    <div class="pset-tree">${validPSets.map(([name, pset]) => this.renderPSetNode(name, pset)).join('')}</div>
                </div>
            `;
            container.appendChild(column);
        }

        // Навигация по колонкам
        this.setupPSetNav();

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
     * Навигация по колонкам PSet
     */
    setupPSetNav() {
        const container = document.getElementById('pset-container');
        const prevBtn = document.getElementById('pset-nav-prev');
        const nextBtn = document.getElementById('pset-nav-next');
        const label = document.getElementById('pset-nav-label');

        const columns = container.querySelectorAll('.pset-column');
        const total = columns.length;

        if (total <= 1) {
            prevBtn.classList.add('hidden');
            nextBtn.classList.add('hidden');
            if (total === 1 && columns[0]) {
                label.textContent = columns[0].querySelector('.pset-column__title')?.textContent || '';
            } else {
                label.textContent = '';
            }
            return;
        }

        prevBtn.classList.remove('hidden');
        nextBtn.classList.remove('hidden');

        const update = () => {
            const colWidth = columns[0]?.clientWidth;
            if (!colWidth) {
                label.textContent = '';
                return;
            }
            const scrollLeft = container.scrollLeft;
            const current = Math.round(scrollLeft / colWidth) + 1;
            const safeCurrent = Math.min(Math.max(current, 1), total);
            prevBtn.disabled = false;
            nextBtn.disabled = false;
            const title = columns[safeCurrent - 1]?.querySelector('.pset-column__title')?.textContent || '';
            label.textContent = `${safeCurrent} / ${total} — ${title}`;
        };

        prevBtn.onclick = () => {
            const colWidth = columns[0]?.clientWidth;
            if (!colWidth) return;
            const current = Math.round(container.scrollLeft / colWidth);
            if (current === 0) {
                container.scrollLeft = colWidth * (total - 1);
            } else {
                container.scrollLeft = colWidth * (current - 1);
            }
        };

        nextBtn.onclick = () => {
            const colWidth = columns[0]?.clientWidth;
            if (!colWidth) return;
            const current = Math.round(container.scrollLeft / colWidth);
            if (current >= total - 1) {
                container.scrollLeft = 0;
            } else {
                container.scrollLeft = colWidth * (current + 1);
            }
        };

        container.addEventListener('scroll', update, { passive: true });
        requestAnimationFrame(update);
    }

    /**
     * Отрисовка узла PSet
     */
    renderPSetNode(name, pset) {
        const patternProps = pset.properties.filter(p => p.is_pattern);
        const patternCount = patternProps.length;

        return `
            <div class="tree-node">
                <div class="tree-node__header">
                    <input type="checkbox"
                           id="pset-${name}"
                           ${this.selectedPSetNames.has(name) ? 'checked' : ''}
                           data-pset="${name}">
                    <label for="pset-${name}">
                        ${name} (${this.formatEntities(pset.applicable_entities)})
                    </label>
                </div>
                ${patternCount > 0 ? `<div class="tree-node__pattern-warning">${patternCount} ${this.declension(patternCount, ['свойство описано регулярным выражением', 'свойства описаны регулярными выражениями', 'свойств описано регулярными выражениями'])} — не будут созданы</div>` : ''}
                <div class="tree-node__children">
                    ${pset.properties.filter(prop => !prop.is_pattern).map(prop => {
                        const measureType = prop.data_type || 'IfcText';
                        const templateType = prop.template_type || 'P_SINGLEVALUE';
                        return `
                        <div class="property-item">
                            <div class="property-item__header">
                                ${prop.name} (${measureType}, ${templateType})
                            </div>
                            ${prop.description ? `<div class="property-item__description">${prop.description}</div>` : ''}
                        </div>
                    `}).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Генерация IFC для всех загруженных IDS
     */
    async generate() {
        // Собираем все PSet из всех IDS
        const selectedPSets = {};
        let selectedCount = 0;
        for (const [idsName, psets] of Object.entries(this.psetsByIDS)) {
            for (const [name, pset] of Object.entries(psets)) {
                if (!pset.is_pattern) {
                    selectedPSets[name] = pset;
                    selectedCount++;
                }
            }
        }

        if (selectedCount === 0) {
            alert('Нет PSet для генерации');
            return;
        }

        const generateBtn = document.getElementById('generate-btn');
        generateBtn.disabled = true;
        generateBtn.textContent = 'Генерация...';
        this.log('Генерация IFC...');

        try {
            const ifcContent = await window.pyodideBridge.generateIFC(
                selectedPSets,
                Object.keys(selectedPSets)
            );

            // Сохраняем результат только для IDS с валидными PSet
            for (const idsName of this.files.keys()) {
                const idsPSets = this.psetsByIDS[idsName] || {};
                const hasValid = Object.values(idsPSets).some(pset => !pset.is_pattern);
                if (hasValid) {
                    this.ifcByIDS[idsName] = ifcContent;
                }
            }

            this.log('IFC сгенерирован');
        } catch (error) {
            this.log(`Ошибка генерации: ${error.message}`);
        }

        generateBtn.disabled = false;
        generateBtn.textContent = 'Сгенерировать IFC';
        this.renderFilesList();
    }

    /**
     * Скачивание IFC для конкретного IDS файла
     */
    downloadIFCForIDS(idsName) {
        const ifcContent = this.ifcByIDS[idsName];
        if (!ifcContent) return;

        const baseName = idsName.replace('.ids', '').replace('.xml', '');
        const fileName = baseName + '_PSet_Library.ifc';
        const blob = new Blob([ifcContent], { type: 'application/x-step' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        a.click();
        URL.revokeObjectURL(url);

        this.log(`Скачан: ${fileName}`);
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
        fileInfo.textContent = `Файл: ${fileName}`;

        // Сохраняем имя файла для скачивания
        this.outputFileName = fileName;

        document.getElementById('result-section').classList.remove('hidden');
    }

    /**
     * Подсчёт общего количества свойств
     */
    getTotalPropertiesCount() {
        let count = 0;
        for (const [idsName, psets] of Object.entries(this.psetsByIDS)) {
            for (const [name, pset] of Object.entries(psets)) {
                if (this.selectedPSetNames.has(name) && !pset.is_pattern) {
                    count += pset.properties.filter(p => !p.is_pattern).length;
                }
            }
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

        this.log('Файл скачан');
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
