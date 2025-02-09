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

        // Check if backend is installed locally
        const installer = new BackendInstaller(this._context);
        const isInstalled = await installer.isInstalled();

        // Get current backend URL and standalone status from settings
        const config = vscode.workspace.getConfiguration('sage');
        const currentBackendUrl = config.get('backendUrl') as string || '';
        const isStandalone = config.get('standalone') as boolean;

        this._updateContent(isInstalled, currentBackendUrl, isStandalone);

        this._panel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.command) {
                    case 'installBackend':
                        try {
                            const installer = new BackendInstaller(this._context);
                            await installer.install();
                            
                            // Update configurations
                            await vscode.workspace.getConfiguration().update('sage.backendUrl', 'http://localhost:8000', true);
                            await vscode.workspace.getConfiguration().update('sage.standalone', true, true);
                            this._panel?.dispose();
                            await vscode.commands.executeCommand('sage.openPanel');
                        } catch (error: any) {
                            vscode.window.showErrorMessage(`Installation failed: ${error.message}`);
                        }
                        break;
                    case 'connectBackend':
                        const ip = message.ip;
                        try {
                            // Save the IP to settings and update standalone status
                            await vscode.workspace.getConfiguration().update('sage.backendUrl', ip, true);
                            await vscode.workspace.getConfiguration().update('sage.standalone', ip === 'http://localhost:8000', true);
                            vscode.window.showInformationMessage('Backend URL configured!');
                            this._panel?.dispose();
                            await vscode.commands.executeCommand('sage.openPanel');
                        } catch (error) {
                            vscode.window.showErrorMessage('Failed to update backend URL configuration.');
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

    private _updateContent(isInstalled: boolean, currentBackendUrl: string, isStandalone: boolean) {
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
                <h1 class="text-2xl font-bold mb-6 text-center">Configure Sage Backend</h1>
                
                <div class="space-y-6">
                    <div class="p-4 bg-lighter-grey rounded-lg">
                        <h2 class="font-semibold mb-2">Local Backend</h2>
                        ${isInstalled ? 
                            isStandalone ? `
                                <p class="text-sm text-green-500 mb-4">✓ Currently using local backend</p>
                            ` : `
                                <p class="text-sm text-green-500 mb-4">✓ Local backend is installed</p>
                                <button 
                                    onclick="useLocalBackend()"
                                    class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors mb-2">
                                    Use Local Backend
                                </button>
                            `
                        : `
                            <p class="text-sm text-gray-400 mb-4">Install and run a local Sage backend on your machine</p>
                            <button 
                                onclick="installBackend()"
                                class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                                Install Backend
                            </button>
                        `}
                    </div>

                    <div class="p-4 bg-lighter-grey rounded-lg">
                        <h2 class="font-semibold mb-2">Remote Backend</h2>
                        <p class="text-sm text-gray-400 mb-4">Connect to an existing Sage backend</p>
                        <input 
                            type="text" 
                            id="backendIp"
                            value="${isStandalone ? '' : currentBackendUrl}"
                            placeholder="Enter backend URL (e.g., http://localhost:8000)"
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

                function useLocalBackend() {
                    vscode.postMessage({ command: 'connectBackend', ip: 'http://localhost:8000' });
                }

                function connectBackend() {
                    const ip = document.getElementById('backendIp').value.trim();
                    if (!ip) {
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