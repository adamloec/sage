
import * as vscode from 'vscode';
const { BackendInstaller } = require('../installation');
import axios from 'axios';

class ConnectionPanel {
    private _context: vscode.ExtensionContext;
    private _panel: vscode.WebviewPanel | undefined;
    private _disposables: vscode.Disposable[];
    static currentPanel: ConnectionPanel | undefined;

    constructor(context: vscode.ExtensionContext) {
        this._context = context;
        this._panel = undefined;
        this._disposables = [];
    }

    static createOrShow(context: vscode.ExtensionContext) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : vscode.ViewColumn.Two;

        if (ConnectionPanel.currentPanel) {
            ConnectionPanel.currentPanel._panel?.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'sageConnection',
            'Sage Backend Configuration',
            column || vscode.ViewColumn.Two,
            { enableScripts: true }
        );

        ConnectionPanel.currentPanel = new ConnectionPanel(context);
        ConnectionPanel.currentPanel._panel = panel;
        ConnectionPanel.currentPanel._initialize();
    }

    private async _initialize() {
        if (!this._panel) return;

        // Get current configuration
        const config = vscode.workspace.getConfiguration('sage');
        const currentBackendUrl = config.get('backendUrl') as string;
        const isStandalone = config.get('standalone') as boolean;
        const isConfigured = config.get('isConfigured') as boolean;

        // Check if backend is installed locally
        const installer = new BackendInstaller(this._context);
        const isInstalled = await installer.isInstalled();

        this._updateContent(isInstalled, currentBackendUrl, isStandalone, isConfigured);

        this._panel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.command) {
                    case 'saveConfiguration':
                        try {
                            const { mode, backendUrl } = message;
                            const isStandalone = mode === 'standalone';

                            // Validate configuration
                            if (isStandalone && !isInstalled) {
                                throw new Error('Local backend not installed');
                            }

                            if (!isStandalone && !backendUrl) {
                                throw new Error('Backend URL required for remote connection');
                            }

                            // Test connection
                            if (!isStandalone) {
                                const response = await axios.get(`${backendUrl}/health`);
                                if (response.status !== 200) {
                                    throw new Error('Could not connect to backend');
                                }
                            }

                            // Update configuration
                            await vscode.workspace.getConfiguration().update('sage.standalone', isStandalone, true);
                            await vscode.workspace.getConfiguration().update('sage.backendUrl', 
                                isStandalone ? 'http://localhost:8000' : backendUrl, 
                                true
                            );
                            await vscode.workspace.getConfiguration().update('sage.isConfigured', true, true);

                            // Show success and open main panel
                            vscode.window.showInformationMessage('Backend configuration saved successfully');
                            this.dispose();
                            await vscode.commands.executeCommand('sage.openPanel');
                        } catch (error: any) {
                            vscode.window.showErrorMessage(`Configuration failed: ${error}`);
                        }
                        break;

                    case 'installBackend':
                        try {
                            const installer = new BackendInstaller(this._context);
                            await installer.install();
                            this._initialize(); // Refresh panel after installation
                        } catch (error: any) {
                            vscode.window.showErrorMessage(`Installation failed: ${error}`);
                        }
                        break;
                }

            },
            undefined,
            this._disposables
        );

        this._panel.onDidDispose(
            () => {
                ConnectionPanel.currentPanel = undefined;
                this.dispose();
            },
            null,
            this._disposables
        );
    }

    private _updateContent(
        isInstalled: boolean, 
        currentBackendUrl: string, 
        isStandalone: boolean,
        isConfigured: boolean
    ) {
        if (!this._panel) return;

        this._panel.webview.html = `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sage Backend Configuration</title>
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
        <body class="bg-dark-grey text-gray-200 h-screen flex items-center justify-center">
            <div class="max-w-md w-full p-8 bg-light-grey rounded-xl shadow-lg">
                <h1 class="text-2xl font-bold mb-6 text-center">Configure Sage Backend</h1>
                
                <div class="space-y-6">
                    <!-- Mode Selection -->
                    <div class="space-y-4">
                        <label class="block font-medium mb-2">Backend Mode</label>
                        <div class="space-y-2">
                            <label class="flex items-center space-x-3">
                                <input type="radio" name="mode" value="standalone" 
                                    ${isStandalone ? 'checked' : ''} 
                                    class="form-radio"
                                    onchange="updateMode('standalone')">
                                <span>Standalone (Local Backend)</span>
                            </label>
                            <label class="flex items-center space-x-3">
                                <input type="radio" name="mode" value="remote" 
                                    ${!isStandalone ? 'checked' : ''} 
                                    class="form-radio"
                                    onchange="updateMode('remote')">
                                <span>Remote Backend</span>
                            </label>
                        </div>
                    </div>

                    <!-- Standalone Section -->
                    <div id="standaloneSection" class="p-4 bg-lighter-grey rounded-lg ${!isStandalone ? 'hidden' : ''}">
                        ${isInstalled ? 
                            `<p class="text-sm text-green-500 mb-4">✓ Local backend is installed</p>` :
                            `<p class="text-sm text-gray-400 mb-4">Local backend needs to be installed</p>
                            <button 
                                onclick="installBackend()"
                                class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                                Install Backend
                            </button>`
                        }
                    </div>

                    <!-- Remote Section -->
                    <div id="remoteSection" class="p-4 bg-lighter-grey rounded-lg ${isStandalone ? 'hidden' : ''}">
                        <input 
                            type="text" 
                            id="backendUrl"
                            value="${!isStandalone ? currentBackendUrl : ''}"
                            placeholder="Enter backend URL (e.g., http://localhost:8000)"
                            class="w-full p-2 mb-4 bg-dark-grey border border-border-grey rounded-md focus:outline-none focus:border-blue-500"
                        >
                    </div>

                    <!-- Save Button -->
                    <button 
                        onclick="saveConfiguration()"
                        class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                        Save Configuration
                    </button>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                let currentMode = '${isStandalone ? 'standalone' : 'remote'}';

                function updateMode(mode) {
                    currentMode = mode;
                    document.getElementById('standaloneSection').classList.toggle('hidden', mode !== 'standalone');
                    document.getElementById('remoteSection').classList.toggle('hidden', mode === 'standalone');
                }

                function installBackend() {
                    vscode.postMessage({ command: 'installBackend' });
                }

                function saveConfiguration() {
                    const backendUrl = document.getElementById('backendUrl').value.trim();
                    vscode.postMessage({ 
                        command: 'saveConfiguration',
                        mode: currentMode,
                        backendUrl: currentMode === 'standalone' ? null : backendUrl
                    });
                }
            </script>
        </body>
        </html>`;
    }

    dispose() {
        this._panel?.dispose();
        while (this._disposables.length) {
            const disposables = this._disposables.pop();
            if (disposables) {
                disposables.dispose();
            }
        }
    }
}

module.exports = { ConnectionPanel };