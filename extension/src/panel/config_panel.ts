import * as vscode from 'vscode';
const axios = require('axios');

class ConfigPanel {
    private _panel: vscode.WebviewPanel | undefined;
    private _disposables: vscode.Disposable[] = [];
    static currentPanel: ConfigPanel | undefined;

    static createOrShow() {
        const column = vscode.ViewColumn.Two;

        if (ConfigPanel.currentPanel) {
            ConfigPanel.currentPanel._panel?.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'sageConfig',
            'Sage Configuration',
            column,
            { enableScripts: true }
        );

        ConfigPanel.currentPanel = new ConfigPanel(panel);
    }

    private constructor(panel: vscode.WebviewPanel) {
        this._panel = panel;
        this._update();
        
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        this._panel.webview.onDidReceiveMessage(async (message: any) => {
            if (message.command === 'saveConfig') {
                try {
                    const config = message.config;
                    // Update VSCode settings
                    const vscodeConfig = vscode.workspace.getConfiguration('sage');
                    await vscodeConfig.update('modelConfig.modelName', config.model_name);
                    await vscodeConfig.update('modelConfig.modelPath', config.model_path);
                    await vscodeConfig.update('modelConfig.contextWindow', config.context_window);
                    await vscodeConfig.update('modelConfig.maxTokens', config.max_tokens);
                    await vscodeConfig.update('modelConfig.trustRemoteCode', config.trust_remote_code);
                    await vscodeConfig.update('modelConfig.dtype', config.dtype);
                    await vscodeConfig.update('modelConfig.temperature', config.temperature);
                    await vscodeConfig.update('modelConfig.doSample', config.do_sample);
                    await vscodeConfig.update('modelConfig.topP', config.top_p);
                    await vscodeConfig.update('modelConfig.topK', config.top_k);

                    // Make API call to update model config
                    const response = await axios.put('http://localhost:8000/llm', config);
                    if (response.status !== 200) {
                        throw new Error(`Failed to update model config: ${response.statusText}`);
                    }

                    vscode.window.showInformationMessage('Configuration saved successfully!');
                    this._panel?.dispose();
                } catch (error: any) {
                    vscode.window.showErrorMessage(`Failed to save config: ${error.message}`);
                }
            }
        });
    }

    private async _update() {
        if (!this._panel) return;

        try {
            // Fetch saved models from the API
            const response = await axios.get('http://localhost:8000/llm/configs');
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
                                        <div>Path: ${config.model_path}</div>
                                        <div>Context Window: ${config.context_window}</div>
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
                                <label class="block mb-1">Model Name</label>
                                <input type="text" id="modelName" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>
                            <div>
                                <label class="block mb-1">Model Path</label>
                                <input type="text" id="modelPath" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>
                            <div>
                                <label class="block mb-1">Context Window</label>
                                <input type="number" id="contextWindow" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>
                            <div>
                                <label class="block mb-1">Max Tokens</label>
                                <input type="number" id="maxTokens" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>
                            <div>
                                <label class="block mb-1">Data Type</label>
                                <select id="dtype" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                                    <option value="float16">float16</option>
                                    <option value="float32">float32</option>
                                </select>
                            </div>
                            <div>
                                <label class="block mb-1">Temperature</label>
                                <input type="number" id="temperature" step="0.1" min="0" max="2" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>
                            <div>
                                <label class="block mb-1">Top P</label>
                                <input type="number" id="topP" step="0.05" min="0" max="1" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>
                            <div>
                                <label class="block mb-1">Top K</label>
                                <input type="number" id="topK" step="1" min="0" class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                            </div>
                            <div class="flex items-center space-x-2">
                                <input type="checkbox" id="trustRemoteCode" class="bg-lighter-grey border border-border-grey rounded">
                                <label>Trust Remote Code</label>
                            </div>
                            <div class="flex items-center space-x-2">
                                <input type="checkbox" id="doSample" class="bg-lighter-grey border border-border-grey rounded">
                                <label>Do Sample</label>
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
                            model_name: document.getElementById('modelName').value,
                            model_path: document.getElementById('modelPath').value,
                            context_window: parseInt(document.getElementById('contextWindow').value),
                            max_tokens: parseInt(document.getElementById('maxTokens').value),
                            trust_remote_code: document.getElementById('trustRemoteCode').checked,
                            dtype: document.getElementById('dtype').value,
                            temperature: parseFloat(document.getElementById('temperature').value),
                            do_sample: document.getElementById('doSample').checked,
                            top_p: parseFloat(document.getElementById('topP').value),
                            top_k: parseInt(document.getElementById('topK').value)
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
        ConfigPanel.currentPanel = undefined;
        this._panel = undefined;

        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            disposable?.dispose();
        }
    }
}

module.exports = { ConfigPanel }; 