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
            'Sage Connection',
            column || vscode.ViewColumn.Two,
            { enableScripts: true }
        );

        ConnectionPanel.currentPanel = new ConnectionPanel(context);
        ConnectionPanel.currentPanel._panel = panel;
        ConnectionPanel.currentPanel._initialize();
    }

    private async _initialize() {
        if (!this._panel) return;

        this._updateContent();

        this._panel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.command) {
                    case 'installBackend':
                        try {
                            const installer = new BackendInstaller(this._context);
                            await installer.install();
                            vscode.window.showInformationMessage('Backend installed successfully!');
                            
                            // Wait a moment for the server to fully start
                            await new Promise(resolve => setTimeout(resolve, 2000));
                            
                            // Check if server is actually running
                            try {
                                const response = await axios.get('http://localhost:8000/health');
                                if (response.status === 200) {
                                    // Update configuration
                                    await vscode.workspace.getConfiguration().update(
                                        'sage.backendUrl', 
                                        'http://localhost:8000', 
                                        true
                                    );
                                    this._panel?.dispose();
                                    await vscode.commands.executeCommand('sage.openPanel');
                                }
                            } catch (error) {
                                vscode.window.showErrorMessage('Backend installed but not responding. Please try again.');
                            }
                        } catch (error: any) {
                            vscode.window.showErrorMessage(`Installation failed: ${error.message}`);
                        }
                        break;
                    case 'connectBackend':
                        const ip = message.ip;
                        try {
                            // Test connection before saving
                            const response = await axios.get(`${ip}/health`);
                            if (response.status === 200) {
                                // Save the IP to settings
                                await vscode.workspace.getConfiguration().update('sage.backendUrl', ip, true);
                                vscode.window.showInformationMessage('Backend connection configured!');
                                this._panel?.dispose();
                                await vscode.commands.executeCommand('sage.openPanel');
                            }
                        } catch (error) {
                            vscode.window.showErrorMessage('Could not connect to the specified backend. Please check the URL and try again.');
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
            },
            null,
            this._disposables
        );
    }

    private _updateContent() {
        if (!this._panel) return;

        this._panel.webview.html = `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sage Connection</title>
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
                <h1 class="text-2xl font-bold mb-6 text-center">Connect to Sage Backend</h1>
                
                <div class="space-y-6">
                    <div class="p-4 bg-lighter-grey rounded-lg">
                        <h2 class="font-semibold mb-2">Install Local Backend</h2>
                        <p class="text-sm text-gray-400 mb-4">Install and run a local Sage backend on your machine</p>
                        <button 
                            onclick="installBackend()"
                            class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                            Install Backend
                        </button>
                    </div>

                    <div class="p-4 bg-lighter-grey rounded-lg">
                        <h2 class="font-semibold mb-2">Connect to Remote Backend</h2>
                        <p class="text-sm text-gray-400 mb-4">Connect to an existing Sage backend</p>
                        <input 
                            type="text" 
                            id="backendIp"
                            placeholder="Enter backend IP (e.g., http://localhost:8000)"
                            class="w-full p-2 mb-4 bg-dark-grey border border-border-grey rounded-md focus:outline-none focus:border-blue-500"
                        >
                        <button 
                            onclick="connectBackend()"
                            class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                            Connect
                        </button>
                    </div>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();

                function installBackend() {
                    vscode.postMessage({ command: 'installBackend' });
                }

                function connectBackend() {
                    const ip = document.getElementById('backendIp').value.trim();
                    if (!ip) {
                        // Show error in UI
                        return;
                    }
                    vscode.postMessage({ command: 'connectBackend', ip });
                }
            </script>
        </body>
        </html>`;
    }

    dispose() {
        this._panel?.dispose();
        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}

module.exports = { ConnectionPanel }; 