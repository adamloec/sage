import * as vscode from 'vscode';
const { ServerManager } = require('../utils/server_manager');
const axios = require('axios');
const { ConfigPanel } = require('./config_panel');

class SagePanel {
    private _context: vscode.ExtensionContext;
    private _panel: vscode.WebviewPanel | undefined;
    private _serverManager: typeof ServerManager;
    private _disposables: vscode.Disposable[];
    static currentPanel: SagePanel | undefined;
    private _currentSessionId: string | undefined;

    constructor(context: vscode.ExtensionContext) {
        this._context = context;
        this._panel = undefined;
        this._serverManager = new ServerManager(context);
        this._disposables = [];
        this._currentSessionId = undefined;
    }

    static async createOrShow(context: vscode.ExtensionContext) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : vscode.ViewColumn.Two;

        // If we already have a panel, show it
        if (SagePanel.currentPanel && SagePanel.currentPanel._panel) {
            SagePanel.currentPanel._panel.reveal(column);
            return;
        }

        // Create a new panel
        const panel = vscode.window.createWebviewPanel(
            'sagePanel',
            'Sage',
            column || vscode.ViewColumn.Two,
            {
                enableScripts: true
            }
        );

        SagePanel.currentPanel = new SagePanel(context);
        SagePanel.currentPanel._panel = panel;
        await SagePanel.currentPanel._initialize();

        // Handle panel disposal
        panel.onDidDispose(
            async () => {
                try {
                    // Stop the server and clean up
                    if (SagePanel.currentPanel) {
                        await SagePanel.currentPanel.dispose();
                        vscode.window.showInformationMessage('Sage server stopped successfully');
                    }
                } catch (error: any) {
                    console.error('Error during panel disposal:', error);
                    vscode.window.showErrorMessage(`Failed to stop server: ${error.message}`);
                }
            },
            null,
            context.subscriptions
        );

        return SagePanel.currentPanel;
    }

    async _initialize() {
        if (!this._panel) {
            return;
        }

        // Show initial starting status
        this._updateContent('Starting server...', false);
        
        // Start server automatically
        try {
            await this._serverManager.startServer();
            // Update both the panel content and show notification after successful start
            this._updateContent('Server running', true);
            vscode.window.showInformationMessage('Sage server started successfully');
            this._panel?.webview.postMessage({ 
                command: 'showStatus', 
                message: 'Server started successfully' 
            });

            // Add message handler for button clicks
            this._panel.webview.onDidReceiveMessage(
                async (message: { command: string; text?: string }) => {
                    switch (message.command) {
                        case 'openSettings':
                            vscode.commands.executeCommand('workbench.action.openSettings', 'sage');
                            break;

                        case 'openConfig':
                            ConfigPanel.createOrShow();
                            break;

                        case 'sendMessage':
                            try {
                                // Check if model is loaded first
                                const modelResponse = await axios.get('http://localhost:8000/llm');
                                if (!modelResponse.data?.model_name) {
                                    this._panel?.webview.postMessage({ 
                                        command: 'showError', 
                                        message: 'Please load a model before sending messages' 
                                    });
                                    // Clear the pending message from UI
                                    this._panel?.webview.postMessage({ 
                                        command: 'clearPendingMessage' 
                                    });
                                    return;
                                }

                                // If we have a model and message text, proceed with chat
                                if (message.text) {
                                    // Create session if this is the first message
                                    if (!this._currentSessionId) {
                                        const sessionResponse = await axios.post('http://localhost:8000/chat/sessions');
                                        this._currentSessionId = sessionResponse.data.session_id;
                                        // Load initial chat history
                                        this._panel?.webview.postMessage({
                                            command: 'updateChatHistory',
                                            messages: sessionResponse.data.messages
                                        });
                                    }

                                    // Send the message
                                    const response = await axios.post(`http://localhost:8000/chat/sessions/${this._currentSessionId}/messages`, {
                                        content: message.text
                                    });

                                    // Update UI with the new message
                                    if (response.data.message) {
                                        this._panel?.webview.postMessage({
                                            command: 'addMessage',
                                            message: response.data.message
                                        });
                                    }
                                }
                            } catch (error: any) {
                                console.error('Error sending message:', error);
                                this._panel?.webview.postMessage({ 
                                    command: 'showError', 
                                    message: `Error sending message: ${error.message}` 
                                });
                                // Clear the pending message from UI
                                this._panel?.webview.postMessage({ 
                                    command: 'clearPendingMessage' 
                                });
                            }
                            break;
                    }
                },
                undefined,
                this._disposables
            );
        } catch (error: any) {
            const errorMessage = `Failed to start server: ${error.message}`;
            console.error(errorMessage);
            this._updateContent('Server stopped', false);
            vscode.window.showErrorMessage(errorMessage);
            this._panel?.webview.postMessage({ 
                command: 'showError', 
                message: errorMessage 
            });
        }
    }

    _updateContent(status: string, isRunning: boolean = false) {
        if (!this._panel) {
            return;
        }

        this._panel.webview.html = this._getWebviewContent(status, isRunning);
    }

    _getWebviewContent(status: string, isRunning: boolean = false): string {
        return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sage</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
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
        <body class="bg-dark-grey text-gray-200 h-screen">
            <div class="container mx-auto max-w-4xl h-full flex flex-col p-6">
                <!-- Server Status Text -->
                <div class="w-[90%] mx-auto mb-2 text-sm">
                    <span class="${isRunning ? 'text-green-500' : 'text-red-500'}">
                        ${status || (isRunning ? 'Server running' : 'Server stopped')}
                    </span>
                </div>

                <!-- Status Bar -->
                <div class="w-[90%] mx-auto mb-2 p-4 bg-light-grey rounded-xl flex justify-between items-center shadow-lg">
                    <div class="flex items-center gap-4">
                        <div id="modelStatus" class="text-gray-400">
                            No model loaded
                        </div>
                    </div>
                    <button 
                        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm"
                        onclick="openConfig()">
                        Edit Config
                    </button>
                </div>
                
                <!-- Status Messages -->
                <div id="statusMessages" class="w-[90%] mx-auto fixed left-1/2 -translate-x-1/2 bottom-32 flex flex-col items-center gap-2"></div>

                <!-- Chat History -->
                <div id="chatHistory" class="w-[90%] mx-auto flex-1 overflow-y-auto mb-24 p-4 rounded-xl shadow-lg">
                    <!-- Chat messages will be populated here -->
                </div>

                <!-- Floating Input Container -->
                <div class="fixed bottom-8 left-1/2 -translate-x-1/2 w-[95%] max-w-4xl">
                    <div class="flex gap-2 p-4 bg-light-grey border border-border-grey rounded-xl shadow-lg">
                        <textarea 
                            class="flex-1 p-3 bg-lighter-grey border border-border-grey rounded-md resize-none min-h-[40px] focus:outline-none focus:border-blue-500"
                            placeholder="Type your message here..."
                            id="messageInput"
                            rows="1"
                            onkeydown="handleKeyPress(event)"
                        ></textarea>
                        <button 
                            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                            onclick="sendMessage()">
                            Send
                        </button>
                    </div>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                
                function showStatusMessage(message, isError = false) {
                    const statusDiv = document.getElementById('statusMessages');
                    const messageEl = document.createElement('div');
                    messageEl.className = \`transform transition-all duration-300 ease-in-out px-4 py-2 rounded-lg shadow-lg bg-lighter-grey text-white\`;
                    messageEl.textContent = message;
                    
                    // Add initial opacity class
                    messageEl.classList.add('opacity-0', 'translate-y-[-20px]');
                    statusDiv.appendChild(messageEl);
                    
                    // Animate in
                    requestAnimationFrame(() => {
                        messageEl.classList.remove('opacity-0', 'translate-y-[-20px]');
                    });
                    
                    // Remove after 3 seconds
                    setTimeout(() => {
                        messageEl.classList.add('opacity-0', 'translate-y-[-20px]');
                        setTimeout(() => messageEl.remove(), 300);
                    }, 3000);

                    // Re-enable the server toggle button
                    const button = document.getElementById('serverStatus');
                    button.classList.remove('bg-red-500', 'bg-green-500');
                    button.classList.add(isError ? 'bg-red-500' : 'bg-green-500');
                }

                // Add message handler for server responses
                window.addEventListener('message', event => {
                    const message = event.data;
                    switch (message.command) {
                        case 'showStatus':
                            showStatusMessage(message.message);
                            break;
                        case 'showError':
                            showStatusMessage(message.message, true);
                            break;
                        case 'clearPendingMessage':
                            // Do nothing - message wasn't added to UI yet
                            break;
                        case 'addMessage':
                            const chatHistory = document.getElementById('chatHistory');
                            // Add both user and assistant messages
                            if (message.message.role === 'user') {
                                chatHistory.innerHTML += \`
                                    <div class="flex justify-end mb-2">
                                        <div class="bg-blue-600 text-white rounded-lg py-2 px-4 max-w-[80%]">
                                            \${message.message.content}
                                        </div>
                                    </div>
                                \`;
                            } else {
                                chatHistory.innerHTML += \`
                                    <div class="flex justify-start mb-2">
                                        <div class="bg-lighter-grey text-white rounded-lg py-2 px-4 max-w-[80%]">
                                            \${message.message.content}
                                        </div>
                                    </div>
                                \`;
                            }
                            chatHistory.scrollTop = chatHistory.scrollHeight;
                            break;
                        case 'updateChatHistory':
                            const history = document.getElementById('chatHistory');
                            history.innerHTML = ''; // Clear existing messages
                            message.messages.forEach(msg => {
                                if (msg.role === 'user') {
                                    history.innerHTML += \`
                                        <div class="flex justify-end mb-2">
                                            <div class="bg-blue-600 text-white rounded-lg py-2 px-4 max-w-[80%]">
                                                \${msg.content}
                                            </div>
                                        </div>
                                    \`;
                                } else {
                                    history.innerHTML += \`
                                        <div class="flex justify-start mb-2">
                                            <div class="bg-lighter-grey text-white rounded-lg py-2 px-4 max-w-[80%]">
                                                \${msg.content}
                                            </div>
                                        </div>
                                    \`;
                                }
                            });
                            history.scrollTop = history.scrollHeight;
                            break;
                    }
                });

                function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    if (message) {
                        // Store message in input but don't display yet
                        const pendingMessage = message;
                        
                        // Clear input right away
                        input.value = '';
                        input.style.height = 'auto';
                        
                        // Send to extension
                        vscode.postMessage({ 
                            command: 'sendMessage',
                            text: pendingMessage 
                        });
                    }
                }

                function handleKeyPress(event) {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        sendMessage();
                    }
                }

                // Auto-resize textarea
                const textarea = document.getElementById('messageInput');
                textarea.addEventListener('input', function() {
                    this.style.height = 'auto';
                    this.style.height = this.scrollHeight + 'px';
                });

                function openSettings() {
                    vscode.postMessage({ command: 'openSettings' });
                }

                function openConfig() {
                    vscode.postMessage({ command: 'openConfig' });
                }

                async function checkModelStatus() {
                    try {
                        const response = await fetch('http://localhost:8000/llm');
                        const data = await response.json();
                        const modelStatus = document.getElementById('modelStatus');
                        if (data && data.model_name) {
                            modelStatus.textContent = data.model_name;
                            modelStatus.classList.remove('text-gray-400');
                            modelStatus.classList.add('text-white');
                        } else {
                            modelStatus.textContent = 'No model loaded';
                            modelStatus.classList.remove('text-white');
                            modelStatus.classList.add('text-gray-400');
                        }
                    } catch (error) {
                        console.error('Failed to check model status:', error);
                    }
                }

                // Check model status every 5 seconds when server is running
                setInterval(checkModelStatus, 5000);
                // Initial check
                checkModelStatus();
            </script>
        </body>
        </html>`;
    }

    async dispose() {
        if (this._panel) {
            this._panel.dispose();
        }
        await this._serverManager.stopServer();
        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
        SagePanel.currentPanel = undefined;
    }
}

module.exports = { SagePanel };