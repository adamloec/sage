import * as vscode from 'vscode';
const axios = require('axios');
const { MessageManager } = require('../utils/message_manager');

class LLMPanel {
    private _panel: vscode.WebviewPanel | undefined;
    private _disposables: vscode.Disposable[] = [];
    static currentPanel: LLMPanel | undefined;

    static createOrShow() {
        const column = vscode.ViewColumn.Two;

        if (LLMPanel.currentPanel) {
            LLMPanel.currentPanel._panel?.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'sageLLM',
            'Sage LLM Settings',
            column,
            { enableScripts: true }
        );

        LLMPanel.currentPanel = new LLMPanel(panel);
    }

    private constructor(panel: vscode.WebviewPanel) {
        this._panel = panel;
        this._update();
        
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        this._panel.webview.onDidReceiveMessage(async (message: any) => {
            if (message.command === 'saveConfig') {
                try {
                    const config = message.config;
                    // Save config via API
                    const response = await axios.post('http://localhost:8000/api/llm/configs', config);
                    if (response.status !== 200) {
                        throw new Error(`Failed to save config: ${response.statusText}`);
                    }

                    MessageManager.showInfo('Configuration saved successfully!');
                    this._panel?.dispose();
                } catch (error: any) {
                    MessageManager.showError(`Failed to save config: ${error.message}`);
                }
            }
        });
    }

    private async _update() {
        if (!this._panel) return;

        try {
            const response = await axios.get('http://localhost:8000/api/llm/configs');
            const savedConfigs = response.data;

            this._panel.webview.html = `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <script src="https://cdn.tailwindcss.com"></script>
                <script>
                    tailwind.config = {
                        theme: {
                            extend: {
                                colors: {
                                    'dark-grey': '#1e1e1e',
                                    'light-grey': '#2d2d2d',
                                    'lighter-grey': '#3d3d3d',
                                    'border-grey': '#4d4d4d',
                                }
                            }
                        }
                    }
                </script>
            </head>
            <body class="bg-dark-grey text-gray-200 p-6">
                <div class="max-w-2xl mx-auto">
                    ${savedConfigs.length > 0 ? `
                        <div class="flex justify-between items-center mb-6">
                            <h2 class="text-xl font-semibold">Saved Models</h2>
                            <button 
                                class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                                onclick="showAddConfig()">
                                Add New Model
                            </button>
                        </div>
                        
                        <div id="modelsList" class="space-y-4">
                            ${savedConfigs.map((config: any) => `
                                <div class="p-4 bg-lighter-grey border border-border-grey rounded-md">
                                    <div class="flex justify-between items-center">
                                        <h3 class="font-semibold">${config.model_name}</h3>
                                        <div class="space-x-2">
                                            <button 
                                                onclick="editConfig(${JSON.stringify(config).replace(/"/g, '&quot;')})"
                                                class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
                                                Edit
                                            </button>
                                            <button 
                                                onclick="deleteConfig(${config.id})"
                                                class="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700">
                                                Delete
                                            </button>
                                        </div>
                                    </div>
                                    <div class="mt-2 text-sm text-gray-400">
                                        <div>Path: ${config.model_path || 'Not specified'}</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div id="configForm" class="hidden mt-6">
                    ` : `
                        <div class="flex justify-between items-center mb-6">
                            <h2 class="text-xl font-semibold">Add New Model</h2>
                        </div>
                        <div id="modelsList" class="hidden"></div>
                        <div id="configForm">
                    `}
                        <div class="space-y-4">
                            <div>
                                <label class="block mb-1">Model Name*</label>
                                <input type="text" id="model_name" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>
                            <div>
                                <label class="block mb-1">Model Path</label>
                                <input type="text" id="model_path" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>
                            
                            <h3 class="font-semibold mt-6">Core Model Parameters</h3>
                            <div class="flex items-center space-x-2">
                                <input type="checkbox" id="trust_remote_code" class="bg-lighter-grey border border-border-grey rounded">
                                <label>Trust Remote Code</label>
                            </div>
                            <div>
                                <label class="block mb-1">Data Type</label>
                                <select id="dtype" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                                    <option value="float16">float16</option>
                                    <option value="float32">float32</option>
                                </select>
                            </div>
                            <div class="flex items-center space-x-2">
                                <input type="checkbox" id="local_files_only" checked class="bg-lighter-grey border border-border-grey rounded">
                                <label>Local Files Only</label>
                            </div>
                            <div class="flex items-center space-x-2">
                                <input type="checkbox" id="use_cache" checked class="bg-lighter-grey border border-border-grey rounded">
                                <label>Use Cache</label>
                            </div>
                            <div class="flex items-center space-x-2">
                                <input type="checkbox" id="return_dict_in_generate" checked class="bg-lighter-grey border border-border-grey rounded">
                                <label>Return Dict in Generate</label>
                            </div>
                            <div class="flex items-center space-x-2">
                                <input type="checkbox" id="output_attentions" class="bg-lighter-grey border border-border-grey rounded">
                                <label>Output Attentions</label>
                            </div>
                            <div class="flex items-center space-x-2">
                                <input type="checkbox" id="output_hidden_states" class="bg-lighter-grey border border-border-grey rounded">
                                <label>Output Hidden States</label>
                            </div>
                            <div class="flex items-center space-x-2">
                                <input type="checkbox" id="low_cpu_mem_usage" checked class="bg-lighter-grey border border-border-grey rounded">
                                <label>Low CPU Memory Usage</label>
                            </div>

                            <h3 class="font-semibold mt-6">Generation Parameters</h3>
                            <div>
                                <label class="block mb-1">Max New Tokens</label>
                                <input type="number" id="max_new_tokens" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>
                            <div>
                                <label class="block mb-1">Temperature</label>
                                <input type="number" id="temperature" step="0.1" min="0" max="2" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>
                            <div class="flex items-center space-x-2">
                                <input type="checkbox" id="do_sample" class="bg-lighter-grey border border-border-grey rounded">
                                <label>Do Sample</label>
                            </div>
                            <div>
                                <label class="block mb-1">Top P</label>
                                <input type="number" id="top_p" step="0.05" min="0" max="1" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>
                            <div>
                                <label class="block mb-1">Top K</label>
                                <input type="number" id="top_k" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>

                            <button 
                                class="w-full mt-6 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                                onclick="saveConfig()">
                                Save Configuration
                            </button>
                        </div>
                    </div>
                </div>

                <script>
                    const vscode = acquireVsCodeApi();

                    function showAddConfig() {
                        document.getElementById('modelsList').classList.add('hidden');
                        document.getElementById('configForm').classList.remove('hidden');
                    }

                    function editConfig(config) {
                        document.getElementById('modelsList').classList.add('hidden');
                        document.getElementById('configForm').classList.remove('hidden');
                        
                        // Populate form with config values
                        Object.keys(config).forEach(key => {
                            const element = document.getElementById(key);
                            if (element) {
                                if (element.type === 'checkbox') {
                                    element.checked = config[key];
                                } else {
                                    element.value = config[key];
                                }
                            }
                        });
                    }

                    function deleteConfig(id) {
                        vscode.postMessage({ 
                            command: 'deleteConfig',
                            id: id 
                        });
                    }

                    function saveConfig() {
                        const config = {
                            model_name: document.getElementById('model_name').value,
                            model_path: document.getElementById('model_path').value,
                            trust_remote_code: document.getElementById('trust_remote_code').checked,
                            dtype: document.getElementById('dtype').value,
                            local_files_only: document.getElementById('local_files_only').checked,
                            use_cache: document.getElementById('use_cache').checked,
                            return_dict_in_generate: document.getElementById('return_dict_in_generate').checked,
                            output_attentions: document.getElementById('output_attentions').checked,
                            output_hidden_states: document.getElementById('output_hidden_states').checked,
                            low_cpu_mem_usage: document.getElementById('low_cpu_mem_usage').checked,
                            max_new_tokens: parseInt(document.getElementById('max_new_tokens').value) || null,
                            temperature: parseFloat(document.getElementById('temperature').value) || null,
                            do_sample: document.getElementById('do_sample').checked,
                            top_p: parseFloat(document.getElementById('top_p').value) || null,
                            top_k: parseInt(document.getElementById('top_k').value) || null
                        };

                        vscode.postMessage({ 
                            command: 'saveConfig',
                            config: config 
                        });
                    }
                </script>
            </body>
            </html>`;
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to load configurations: ${error.message}`);
        }
    }

    private dispose() {
        LLMPanel.currentPanel = undefined;
        this._panel = undefined;

        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            disposable?.dispose();
        }
    }
}

module.exports = { LLMPanel }; 