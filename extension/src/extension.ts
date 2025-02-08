import * as vscode from 'vscode';
import axios from 'axios';
const { BackendInstaller } = require('./installation');
const { SagePanel } = require('./panel/panel');
const { ConnectionPanel } = require('./panel/connection_panel');

async function checkBackendConnection(backendUrl: string = 'http://localhost:8000'): Promise<boolean> {
    try {
        const response = await axios.get(`${backendUrl}/health`);
        return response.status === 200;
    } catch (error) {
        return false;
    }
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
        // Check if backend is configured
        const config = vscode.workspace.getConfiguration('sage');
        const backendUrl = config.get('backendUrl') as string;
        
        // Check connection
        const isConnected = await checkBackendConnection(backendUrl);
        
        if (isConnected) {
            // If connection successful, open main panel
            SagePanel.createOrShow(context);
        } else {
            // If no connection or connection fails, show connection panel
            ConnectionPanel.createOrShow(context);
        }
    });

    // Add all commands to subscriptions
    context.subscriptions.push(
        installCommand,
        openPanelCommand
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
