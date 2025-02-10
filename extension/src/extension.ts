import * as vscode from 'vscode';
import axios from 'axios';
const { BackendInstaller } = require('./installation');
const { SagePanel } = require('./panel/panel');
const { ConnectionPanel } = require('./panel/connection_panel');

// Configuration type for better type safety
interface SageConfig {
    backendUrl: string;
    standalone: boolean;
    isConfigured: boolean; // New setting to track if user has made initial choice
}

async function getConfiguration(): Promise<SageConfig> {
    const config = vscode.workspace.getConfiguration('sage');
    return {
        backendUrl: config.get('backendUrl') as string,
        standalone: config.get('standalone') as boolean,
        isConfigured: config.get('isConfigured') as boolean
    };
}

async function updateConfiguration(updates: Partial<SageConfig>): Promise<void> {
    const config = vscode.workspace.getConfiguration('sage');
    for (const [key, value] of Object.entries(updates)) {
        await config.update(`sage.${key}`, value, true);
    }
}

async function checkBackendConnection(backendUrl: string): Promise<boolean> {
    try {
        const response = await axios.get(`${backendUrl}/health`);
        return response.status === 200;
    } catch (error) {
        return false;
    }
}

function registerCommands(context: vscode.ExtensionContext) {
    // Open panel command - now always checks configuration first
    const openPanelCommand = vscode.commands.registerCommand('sage.openPanel', async () => {
        const config = await getConfiguration();
        
        // If not configured, show connection panel first
        if (!config.isConfigured) {
            await vscode.commands.executeCommand('sage.openConnectionPanel');
            return;
        }

        // Verify connection based on mode
        let canConnect = false;
        if (config.standalone) {
            const installer = new BackendInstaller(context);
            canConnect = await installer.isInstalled();
        } else {
            canConnect = await checkBackendConnection(config.backendUrl);
        }

        if (canConnect) {
            SagePanel.createOrShow(context);
        } else {
            vscode.window.showErrorMessage(
                'Cannot connect to backend. Please check your connection settings.',
                'Configure Backend'
            ).then(selection => {
                if (selection === 'Configure Backend') {
                    vscode.commands.executeCommand('sage.openConnectionPanel');
                }
            });
        }
    });

    // Open connection panel command
    const openConnectionPanelCommand = vscode.commands.registerCommand(
        'sage.openConnectionPanel', 
        () => ConnectionPanel.createOrShow(context)
    );

    context.subscriptions.push(openPanelCommand, openConnectionPanelCommand);
}

async function activate(context: vscode.ExtensionContext) {
    console.log('Sage extension activating...');
    
    // Register commands
    registerCommands(context);

    // Check if configuration exists
    const config = await getConfiguration();
    
    // Check for existing backend installation
    const installer = new BackendInstaller(context);
    const isBackendInstalled = await installer.isInstalled();
    
    if (isBackendInstalled) {
        const choice = await vscode.window.showInformationMessage(
            'An existing Sage backend installation was detected. Would you like to remove it?',
            'Yes, remove it', 
            'No, keep it'
        );
        
        if (choice === 'Yes, remove it') {
            await installer.cleanup();
            vscode.window.showInformationMessage('Existing backend installation removed.');
        } else if (choice === 'No, keep it') {
            // Set standalone mode since there's an existing installation
            await updateConfiguration({
                standalone: true,
                isConfigured: true
            });
            return;
        }
    }

    if (!config.isConfigured) {
        // Show connection panel on first activation
        vscode.commands.executeCommand('sage.openConnectionPanel');
    }
}

export function deactivate(context: vscode.ExtensionContext) {
    const { deactivate } = require('./installation');
    return deactivate(context);
}

module.exports = {
    activate,
    deactivate
};