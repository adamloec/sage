import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import * as fs from 'fs';

const execAsync = promisify(exec);

class BackendInstaller {
    private context: vscode.ExtensionContext;
    private extensionPath: string;
    private ENV_NAME: string;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.extensionPath = context.extensionPath;
        this.ENV_NAME = 'sage_vscode_env';
    }

    async checkPythonEnvironment() {
        try {
            // Use system Python paths instead of relying on PATH
            const pythonCommand = process.platform === 'win32' 
                ? 'C:\\Python312\\python.exe'  // Windows
                : '/usr/local/bin/python3';    // macOS/Linux

            const { stdout } = await execAsync(`"${pythonCommand}" --version`);
            const version = stdout.trim().split(' ')[1];
            const [major, minor] = version.split('.').map(Number);
            
            if (major !== 3 || minor < 12) {
                throw new Error(`Python 3.12+ required, found ${version}`);
            }

            // Check for venv
            await execAsync(`"${pythonCommand}" -m venv --help`);
            return true;
        } catch (err) {
            // Try fallback to regular python3 command if specific path fails
            try {
                const { stdout } = await execAsync('python3 --version');
                const version = stdout.trim().split(' ')[1];
                const [major, minor] = version.split('.').map(Number);
                
                if (major !== 3 || minor < 12) {
                    throw new Error(`Python 3.12+ required, found ${version}`);
                }

                await execAsync('python3 -m venv --help');
                return true;
            } catch (fallbackErr: any) {
                console.log('Python check failed:', fallbackErr.message);
                return false;
            }
        }
    }

    async promptForInstallation() {
        const hasCorrectPython = await this.checkPythonEnvironment();
        
        if (!hasCorrectPython) {
            const result = await vscode.window.showErrorMessage(
                'Python 3.12 or higher with venv support is required.',
                'Install Python 3.12'
            );
            if (result === 'Install Python 3.12') {
                vscode.env.openExternal(vscode.Uri.parse('https://www.python.org/downloads/'));
            }
            return null;
        }

        return { name: this.ENV_NAME };
    }

    async install() {
        const choice = await this.promptForInstallation();
        if (!choice) return false;

        const success = await this.installWithVenv(choice.name);

        if (success) {
            vscode.window.showInformationMessage('Sage backend installed successfully!');
        }
        return success;
    }

    async installWithVenv(envName: string) {
        try {
            const envPath = path.join(this.extensionPath, envName);
            const pythonCommand = process.platform === 'win32' 
                ? 'C:\\Python312\\python.exe'  // Windows
                : '/usr/local/bin/python3';    // macOS/Linux

            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Installing Sage backend',
                cancellable: false
            }, async (progress) => {
                // Remove existing environment if it exists
                if (fs.existsSync(envPath)) {
                    progress.report({ message: 'Removing existing environment...' });
                    fs.rmSync(envPath, { recursive: true, force: true });
                }

                progress.report({ message: 'Creating environment...' });
                await execAsync(`"${pythonCommand}" -m venv "${envPath}"`);

                progress.report({ message: 'Installing backend...' });
                const pipPath = process.platform === 'win32' ? 
                    path.join(envPath, 'Scripts', 'pip.exe') :
                    path.join(envPath, 'bin', 'pip');
                
                // Upgrade pip first
                await execAsync(`"${pipPath}" install --upgrade pip`);
                
                // Install wheel and setuptools
                await execAsync(`"${pipPath}" install wheel setuptools`);
                
                // Install the sage package with editable mode and egg name
                await execAsync(`"${pipPath}" install -e "git+https://github.com/adamloec/sage.git#subdirectory=server&egg=sage" --no-cache-dir`);
                
                // Verify the installation
                const pythonPath = process.platform === 'win32' ? 
                    path.join(envPath, 'Scripts', 'python.exe') :
                    path.join(envPath, 'bin', 'python');
                
                await execAsync(`"${pythonPath}" -c "import sage; print('Sage package installed successfully')"`)
            });

            return true;
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to install: ${error.message}`);
            return false;
        }
    }

    async isInstalled(): Promise<boolean> {
        try {
            const envPath = path.join(this.extensionPath, this.ENV_NAME);
            const pythonPath = process.platform === 'win32' ? 
                path.join(envPath, 'Scripts', 'python.exe') :
                path.join(envPath, 'bin', 'python');
            
            // Check if the environment exists and sage package is importable
            if (fs.existsSync(envPath)) {
                try {
                    await execAsync(`"${pythonPath}" -c "import sage"`);
                    return true;
                } catch (error) {
                    return false;
                }
            }
            return false;
        } catch (error) {
            return false;
        }
    }
}

module.exports = { BackendInstaller };
