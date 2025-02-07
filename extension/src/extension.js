const vscode = require('vscode');
const { BackendInstaller } = require('./installation');
const { SagePanel } = require('./panel/panel');

function registerCommands(context) {
    // Install backend command
    const installCommand = vscode.commands.registerCommand('sage.installBackend', async () => {
        console.log('Install command triggered');
        const installer = new BackendInstaller(context);
        await installer.install();
    });

    // Open panel command
    const openPanelCommand = vscode.commands.registerCommand('sage.openPanel', () => {
        SagePanel.createOrShow(context);
    });

    // Add all commands to subscriptions
    context.subscriptions.push(
        installCommand,
        openPanelCommand
    );
}

async function activate(context) {
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
