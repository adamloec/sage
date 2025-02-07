const vscode = require('vscode');
const { EnvironmentManager } = require('../utils/environment');

class SagePanel {
    constructor(context) {
        this.context = context;
        this._panel = undefined;
        this._serverProcess = undefined;
        this._environmentManager = new EnvironmentManager(context);
    }

    async startServer() {
        try {
            this._panel.webview.html = getWebviewContent('Starting Sage server...');
            this._serverProcess = await this._environmentManager.spawnInEnvironment('sage serve');

            let serverStarted = false;
            
            this._serverProcess.stdout.on('data', (data) => {
                const output = data.toString();
                console.log(`Server stdout: ${output}`);
                
                // Uvicorn typically outputs this when the server is ready
                if (output.includes('Application startup complete')) {
                    serverStarted = true;
                    this._panel.webview.html = getWebviewContent('Sage server is running! 🚀');
                }
            });

            this._serverProcess.stderr.on('data', (data) => {
                console.error(`Server stderr: ${data}`);
                this._panel.webview.html = getWebviewContent(`Server error: ${data}`);
            });

            this._serverProcess.on('error', (error) => {
                const errorMessage = `Failed to start Sage server: ${error.message}`;
                console.error(errorMessage);
                vscode.window.showErrorMessage(errorMessage);
                this._panel.webview.html = getWebviewContent(errorMessage);
            });

            // Check if server started after a timeout
            setTimeout(() => {
                if (!serverStarted) {
                    const timeoutMessage = 'Server startup is taking longer than expected...';
                    console.warn(timeoutMessage);
                    this._panel.webview.html = getWebviewContent(timeoutMessage);
                }
            }, 5000);

        } catch (error) {
            const errorMessage = `Failed to start server: ${error.message}`;
            console.error(errorMessage);
            vscode.window.showErrorMessage(errorMessage);
            this._panel.webview.html = getWebviewContent(errorMessage);
        }
    }

    static createOrShow(context) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : vscode.ViewColumn.Two;

        // If we already have a panel, show it
        if (SagePanel.currentPanel) {
            SagePanel.currentPanel._panel.reveal(column);
            return;
        }

        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(
            'sagePanel',
            'Sage',
            column,
            {
                enableScripts: true
            }
        );

        panel.webview.html = getWebviewContent();
        SagePanel.currentPanel = new SagePanel(context);
        SagePanel.currentPanel._panel = panel;
        SagePanel.currentPanel.startServer();

        // Handle panel disposal
        panel.onDidDispose(
            () => {
                // Kill the server process when the panel is closed
                if (SagePanel.currentPanel._serverProcess) {
                    SagePanel.currentPanel._serverProcess.kill();
                }
                SagePanel.currentPanel = undefined;
            },
            null,
            context.subscriptions
        );
    }
}

function getWebviewContent(status = 'Welcome to Sage!') {
    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sage</title>
        <style>
            body {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .status {
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
                background-color: var(--vscode-textBlockQuote-background);
            }
        </style>
    </head>
    <body>
        <h1>Sage</h1>
        <div class="status">
            Status: ${status}
        </div>
        <p>This panel will be enhanced with more features soon.</p>
    </body>
    </html>`;
}

module.exports = { SagePanel }; 