// extension.js
const vscode = require('vscode');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// Track the Python process
let pythonProcess = null;

// Platform-specific settings
const isWindows = process.platform === 'win32';
const isMac = process.platform === 'darwin';
const isLinux = process.platform === 'linux';

function getPythonCommand() {
    if (isWindows) {
        return 'python';
    } else {
        return 'python3';
    }
}

function getVenvPython(venvPath) {
    if (isWindows) {
        return path.join(venvPath, 'Scripts', 'python.exe');
    } else {
        return path.join(venvPath, 'bin', 'python');
    }
}

function getVenvPip(venvPath) {
    if (isWindows) {
        return path.join(venvPath, 'Scripts', 'pip.exe');
    } else {
        return path.join(venvPath, 'bin', 'pip');
    }
}

/**
 * @param {vscode.ExtensionContext} context
 */
async function activate(context) {
    console.log('Extension is being activated');

    // Register commands
    let startBackendCommand = vscode.commands.registerCommand('sage.startBackend', () => {
        startPythonBackend(context);
    });

    let installDepsCommand = vscode.commands.registerCommand('sage.installDependencies', () => {
        installSageBackend(context);
    });

    context.subscriptions.push(startBackendCommand);
    context.subscriptions.push(installDepsCommand);

    // Automatically check installation on activation
    await checkAndInstallDependencies(context);
}

function deactivate() {
    if (pythonProcess) {
        pythonProcess.kill();
    }
}

async function checkAndInstallDependencies(context) {
    console.log('Checking dependencies...');
    const configPath = path.join(context.globalStorageUri.fsPath, '.installed');
    const venvPath = path.join(context.extensionPath, 'venv');
    
    // Check if venv exists and has Python
    const venvPython = getVenvPython(venvPath);
    const venvExists = fs.existsSync(venvPython);
    
    console.log('Venv exists:', venvExists);
    console.log('Config path:', configPath);
    
    if (!venvExists || !fs.existsSync(configPath)) {
        console.log('Need to install dependencies');
        const choice = await vscode.window.showInformationMessage(
            'This extension requires the Sage backend. Would you like to install it now?',
            'Yes', 'No'
        );
        
        if (choice === 'Yes') {
            const success = await installSageBackend(context);
            if (success) {
                fs.mkdirSync(path.dirname(configPath), { recursive: true });
                fs.writeFileSync(configPath, 'installed');
            }
        }
    } else {
        console.log('Dependencies already installed');
    }
}

async function installSageBackend(context) {
    try {
        // Get path for virtual environment within extension directory
        const venvPath = path.join(context.extensionPath, 'venv');
        const pythonCmd = getPythonCommand();
        
        // Create a terminal for installation
        const terminal = vscode.window.createTerminal({
            name: 'Sage Setup',
            hideFromUser: false
        });
        
        // Show the terminal
        terminal.show(true);  // true means bring terminal to front
        
        // Clear any existing venv
        if (fs.existsSync(venvPath)) {
            console.log('Removing existing venv');
            if (isWindows) {
                terminal.sendText(`rmdir /s /q "${venvPath}"`);
            } else {
                terminal.sendText(`rm -rf "${venvPath}"`);
            }
            await new Promise(resolve => setTimeout(resolve, 2000));
        }

        console.log('Creating new venv');
        // Create new venv
        terminal.sendText(`${pythonCmd} -m venv "${venvPath}"`);
        await new Promise(resolve => setTimeout(resolve, 5000));

        // Get the virtual environment's Python and pip paths
        const venvPython = getVenvPython(venvPath);
        const venvPip = getVenvPip(venvPath);

        console.log('Upgrading pip');
        // Upgrade pip
        terminal.sendText(`"${venvPython}" -m pip install --upgrade pip`);
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        console.log('Installing sage');
        // Install sage
        terminal.sendText(`"${venvPip}" install git+https://github.com/adamloec/sage.git#egg=sage`);
        
        // Show progress
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Installing Sage backend...",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Creating virtual environment..." });
            await new Promise(resolve => setTimeout(resolve, 5000));
            
            progress.report({ increment: 30, message: "Upgrading pip..." });
            await new Promise(resolve => setTimeout(resolve, 5000));
            
            progress.report({ increment: 60, message: "Installing Sage..." });
            await new Promise(resolve => setTimeout(resolve, 15000));
            
            progress.report({ increment: 100, message: "Installation complete!" });
        });

        // Verify installation
        if (fs.existsSync(venvPython)) {
            vscode.window.showInformationMessage('Sage backend installed successfully!');
            return true;
        } else {
            throw new Error('Virtual environment Python not found after installation');
        }
    } catch (error) {
        console.error('Installation error:', error);
        vscode.window.showErrorMessage(`Failed to install Sage backend: ${error.message}`);
        return false;
    }
}

async function startPythonBackend(context) {
    if (pythonProcess) {
        vscode.window.showInformationMessage('Sage backend is already running!');
        return;
    }

    const venvPath = path.join(context.extensionPath, 'venv');
    const venvPython = getVenvPython(venvPath);

    if (!fs.existsSync(venvPython)) {
        const choice = await vscode.window.showErrorMessage(
            'Sage backend is not installed. Would you like to install it now?',
            'Yes', 'No'
        );
        
        if (choice === 'Yes') {
            const success = await installSageBackend(context);
            if (!success) return;
        } else {
            return;
        }
    }

    pythonProcess = spawn(venvPython, ['-m', 'sage.main']);

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend output: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Backend error: ${data}`);
        vscode.window.showErrorMessage(`Backend error: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
        pythonProcess = null;
        if (code !== 0) {
            vscode.window.showErrorMessage(`Backend process exited with code ${code}`);
        }
    });

    vscode.window.showInformationMessage('Sage backend started successfully!');
}

module.exports = {
    activate,
    deactivate
}