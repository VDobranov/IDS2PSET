/**
 * Tests for IDS2PSET application.
 * Run with: node --test test.js
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Mock browser globals for Node.js environment
global.Blob = class Blob {
    constructor(parts, options) {
        this.parts = parts;
        this.type = options?.type || '';
    }
};

global.URL = {
    createObjectURL: (blob) => `blob:test/${Date.now()}`,
    revokeObjectURL: () => {}
};

describe('IDS2PSET App', () => {
    describe('File Loading', () => {
        it('should load HTML file', () => {
            const htmlPath = join(__dirname, '..', 'index.html');
            const html = readFileSync(htmlPath, 'utf-8');
            
            assert.ok(html.includes('IDS2PSET'));
            assert.ok(html.includes('drop-zone'));
        });
        
        it('should load CSS file', () => {
            const cssPath = join(__dirname, '..', 'css', 'style.css');
            const css = readFileSync(cssPath, 'utf-8');
            
            assert.ok(css.length > 0);
        });
        
        it('should load JS app file', () => {
            const jsPath = join(__dirname, '..', 'js', 'app.js');
            const js = readFileSync(jsPath, 'utf-8');
            
            assert.ok(js.length > 0);
        });
    });
    
    describe('File Validation', () => {
        it('IDS fixture minimal.ids should exist', () => {
            const fixturePath = join(__dirname, 'fixtures', 'minimal.ids');
            const content = readFileSync(fixturePath, 'utf-8');
            
            assert.ok(content.includes('<?xml'));
            assert.ok(content.includes('<ids'));
            assert.ok(content.includes('</ids>'));
        });
        
        it('IDS fixture with_enumeration.ids should exist', () => {
            const fixturePath = join(__dirname, 'fixtures', 'with_enumeration.ids');
            const content = readFileSync(fixturePath, 'utf-8');
            
            assert.ok(content.includes('enumeration'));
        });
        
        it('IDS fixture multi_entity.ids should exist', () => {
            const fixturePath = join(__dirname, 'fixtures', 'multi_entity.ids');
            const content = readFileSync(fixturePath, 'utf-8');
            
            assert.ok(content.includes('specification'));
            assert.ok((content.match(/specification/g) || []).length >= 2);
        });
    });
});

describe('Pyodide Bridge', () => {
    describe('Module Structure', () => {
        it('should have pyodide-bridge.js file', () => {
            const bridgePath = join(__dirname, '..', 'js', 'pyodide-bridge.js');
            const content = readFileSync(bridgePath, 'utf-8');
            
            assert.ok(content.length > 0);
        });
    });
});

describe('UI Components', () => {
    it('should have drop zone element in HTML', () => {
        const htmlPath = join(__dirname, '..', 'index.html');
        const html = readFileSync(htmlPath, 'utf-8');
        
        assert.ok(html.includes('drop-zone') || html.includes('dropzone'));
    });
    
    it('should have file input element in HTML', () => {
        const htmlPath = join(__dirname, '..', 'index.html');
        const html = readFileSync(htmlPath, 'utf-8');
        
        assert.ok(html.includes('type="file"') || html.includes('input'));
    });
    
    it('should have preview container in HTML', () => {
        const htmlPath = join(__dirname, '..', 'index.html');
        const html = readFileSync(htmlPath, 'utf-8');
        
        assert.ok(html.includes('preview') || html.includes('pset-tree'));
    });
});

describe('CSS Styles', () => {
    it('should have basic styles', () => {
        const cssPath = join(__dirname, '..', 'css', 'style.css');
        const css = readFileSync(cssPath, 'utf-8');
        
        assert.ok(css.includes('body') || css.includes(':root'));
    });
    
    it('should have drop zone styles', () => {
        const cssPath = join(__dirname, '..', 'css', 'style.css');
        const css = readFileSync(cssPath, 'utf-8');
        
        assert.ok(css.includes('drop') || css.includes('zone'));
    });
});
