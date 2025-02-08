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

        this._panel.webview.onDidReceiveMessage(async (message) => {
            if (message.command === 'saveConfig') {
                try {
                    const config = message.config;
                    // Update VSCode settings
                    const vscodeConfig = vscode.workspace.getConfiguration('sage');
                    await vscodeConfig.update('modelConfig.modelName', config.model_name);
                    await vscodeConfig.update('modelConfig.modelPath', config.model_path);
                    await vscodeConfig.update('modelConfig.contextWindow', config.context_window);
                    await vscodeConfig.update('modelConfig.maxTokens', config.max_tokens);

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

    private _update() {
        if (!this._panel) return;

        const config = vscode.workspace.getConfiguration('sage');
        const modelName = config.get('modelConfig.modelName') || '';
        const modelPath = config.get('modelConfig.modelPath') || '';
        const contextWindow = config.get('modelConfig.contextWindow') || 4096;
        const maxTokens = config.get('modelConfig.maxTokens') || 2048;

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
                <h2 class="text-xl font-semibold mb-6">Model Configuration</h2>
                <div class="space-y-4">
                    <div>
                        <label class="block mb-1">Model Name</label>
                        <input type="text" id="modelName" value="${modelName}" 
                            class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                    </div>
                    <div>
                        <label class="block mb-1">Model Path</label>
                        <input type="text" id="modelPath" value="${modelPath}"
                            class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                    </div>
                    <div>
                        <label class="block mb-1">Context Window</label>
                        <input type="number" id="contextWindow" value="${contextWindow}"
                            class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                    </div>
                    <div>
                        <label class="block mb-1">Max Tokens</label>
                        <input type="number" id="maxTokens" value="${maxTokens}"
                            class="w-full p-2 bg-lighter-grey border border-border-grey rounded-md">
                    </div>
                    <button 
                        class="w-full mt-6 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                        onclick="saveConfig()">
                        Save Configuration
                    </button>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();

                function saveConfig() {
                    const config = {
                        model_name: document.getElementById('modelName').value,
                        model_path: document.getElementById('modelPath').value,
                        context_window: parseInt(document.getElementById('contextWindow').value),
                        max_tokens: parseInt(document.getElementById('maxTokens').value)
                    };

                    vscode.postMessage({ 
                        command: 'saveConfig',
                        config: config 
                    });
                }
            </script>
        </body>
        </html>`;
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