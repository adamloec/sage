import * as vscode from 'vscode';
import axios from 'axios';
const { BackendInstaller } = require('./installation');
const { SagePanel } = require('./panel/panel');
const { ConnectionPanel } = require('./panel/connection_panel');
const { LLMPanel } = require('./panel/llm_panel');

async function checkBackendConnection(backendUrl: string = 'http://localhost:8000'): Promise<boolean> {
    try {
        const response = await axios.get(`${backendUrl}/health`);
        return response.status === 200;
    } catch (error) {
        return false;
    }
}

async function isBackendInstalled(context: vscode.ExtensionContext): Promise<boolean> {
    const installer = new BackendInstaller(context);
    return installer.isInstalled();
}

function registerCommands(context: vscode.ExtensionContext) {
    // Install backend command
    const installCommand = vscode.commands.registerCommand('sage.installBackend', async () => {
        console.log('Install command triggered');
        const installer = new BackendInstaller(context);
        await installer.install();
    });

    // Open panel command
    const openPanelCommand = vscode.commands.registerCommand('sage.openPanel', async () => {
        const config = vscode.workspace.getConfiguration('sage');
        const backendUrl = config.get('backendUrl') as string;
        
        if (backendUrl && backendUrl !== 'http://localhost:8000') {
            // For remote backends, check if they're actually running
            const isConnected = await checkBackendConnection(backendUrl);
            if (isConnected) {
                SagePanel.createOrShow(context);
                return;
            }
        } else {
            // For local backend, just check if it's installed
            const installed = await isBackendInstalled(context);
            if (installed) {
                SagePanel.createOrShow(context);
                return;
            }
        }

        // If we get here, either the backend isn't installed or the remote connection failed
        ConnectionPanel.createOrShow(context);
    });

    // Open connection panel command
    const openConnectionPanelCommand = vscode.commands.registerCommand('sage.openConnectionPanel', () => {
        ConnectionPanel.createOrShow(context);
    });

    // Open LLM panel command
    const openLLMPanelCommand = vscode.commands.registerCommand('sage.openLLMPanel', () => {
        LLMPanel.createOrShow();
    });

    // Add all commands to subscriptions
    context.subscriptions.push(
        installCommand,
        openPanelCommand,
        openConnectionPanelCommand,
        openLLMPanelCommand
    );
}

async function activate(context: vscode.ExtensionContext) {
    console.log('Sage extension activating...');

    // Register all commands
    registerCommands(context);

    // Check if backend is installed and prompt if not
    console.log('Running installation check...');
    const installer = new BackendInstaller(context);

    console.log('Showing installation prompt...');
    const result = await vscode.window.showInformationMessage(
        'Would you like to install the Sage backend?',
        'Yes', 'No', 'Later'
    );
    
    console.log('User response:', result);
    if (result === 'Yes') {
        await installer.install();
    }

    console.log('Sage extension activation complete');
}

function deactivate() {
    console.log('Sage extension deactivated');
}

module.exports = {
    activate,
    deactivate
};
