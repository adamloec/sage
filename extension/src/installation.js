const vscode = require('vscode');
const { exec } = require('child_process');
const { promisify } = require('util');
const path = require('path');
const fs = require('fs');

const execAsync = promisify(exec);

class BackendInstaller {
    constructor(context) {
        this.context = context;
        this.extensionPath = context.extensionPath;
        this.ENV_NAME = 'sage_vscode_env';
        this.useCondaEnv = false;
    }

    async checkPythonEnvironment() {
        try {
            const environments = [];
            
            // Check for conda
            try {
                await execAsync('conda --version');
                environments.push('conda');
            } catch (err) {
                console.log('Conda not found');
            }

            // Check for venv/virtualenv
            try {
                await execAsync('python -m venv --help');
                environments.push('venv');
            } catch (err) {
                console.log('venv not found');
            }

            return environments;
        } catch (error) {
            console.error('Error checking Python environment:', error);
            return [];
        }
    }

    async promptForInstallation() {
        const environments = await this.checkPythonEnvironment();
        
        if (environments.length === 0) {
            const result = await vscode.window.showErrorMessage(
                'No Python environment manager found. Please install either Conda or Python venv.',
                'Install Guide'
            );
            if (result === 'Install Guide') {
                vscode.env.openExternal(vscode.Uri.parse('https://docs.conda.io/en/latest/miniconda.html'));
            }
            return null;
        }

        // If both environments are available, let user choose
        if (environments.length > 1) {
            const choice = await vscode.window.showQuickPick(
                environments.map(env => ({
                    label: env === 'conda' ? 'Conda (Recommended)' : 'Local Environment',
                    value: env
                })),
                {
                    placeHolder: 'Select environment type for Sage installation',
                    title: 'Choose Installation Environment'
                }
            );
            
            if (!choice) return null; // User cancelled
            this.useCondaEnv = choice.value === 'conda';
            return { manager: choice.value, name: this.ENV_NAME };
        }

        // If only one environment is available, use that
        this.useCondaEnv = environments[0] === 'conda';
        return { manager: environments[0], name: this.ENV_NAME };
    }

    async install() {
        const choice = await this.promptForInstallation();
        if (!choice) return false;

        let success = false;
        if (choice.manager === 'conda') {
            success = await this.installWithConda(choice.name);
        } else if (choice.manager === 'venv') {
            success = await this.installWithVenv(choice.name);
        }

        if (success) {
            vscode.window.showInformationMessage('Sage backend installed successfully!');
        }
        return success;
    }

    async installWithConda(envName) {
        try {
            // Create and setup environment
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Installing Sage backend',
                cancellable: false
            }, async (progress) => {
                // Remove existing environment if it exists
                const { stdout } = await execAsync('conda env list');
                if (stdout.includes(envName)) {
                    progress.report({ message: 'Removing existing environment...' });
                    await execAsync(`conda env remove -n ${envName}`);
                }

                progress.report({ message: 'Creating environment...' });
                await execAsync(`conda create -n ${envName} python=3.12 -y`);

                progress.report({ message: 'Installing backend...' });
                await execAsync(`conda run -n ${envName} pip install git+https://github.com/adamloec/sage.git#subdirectory=server --no-cache-dir`);
            });

            return true;
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to install: ${error.message}`);
            return false;
        }
    }

    async installWithVenv(envName) {
        try {
            const envPath = path.join(this.extensionPath, '..', envName);

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
                await execAsync(`python -m venv "${envPath}"`);

                progress.report({ message: 'Installing backend...' });
                const pipPath = process.platform === 'win32' ? 
                    path.join(envPath, 'Scripts', 'pip') :
                    path.join(envPath, 'bin', 'pip');
                
                await execAsync(`"${pipPath}" install git+https://github.com/adamloec/sage.git#subdirectory=server --no-cache-dir`);
            });

            return true;
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to install: ${error.message}`);
            return false;
        }
    }

    async installBackend() {
        try {
            // Create environment first
            await this.createEnvironment();

            // Get the path to the sage backend directory (bundled with extension)
            const sagePath = path.join(this.extensionPath, 'sage');

            if (this.useCondaEnv) {
                await execAsync(`conda activate ${this.ENV_NAME} && pip install "${sagePath}"`, {
                    shell: true
                });
            } else {
                const pipPath = process.platform === 'win32'
                    ? path.join(this.extensionPath, '..', this.ENV_NAME, 'Scripts', 'pip')
                    : path.join(this.extensionPath, '..', this.ENV_NAME, 'bin', 'pip');
                
                await execAsync(`"${pipPath}" install "${sagePath}"`, {
                    shell: true
                });
            }

            vscode.window.showInformationMessage('Sage backend installed successfully!');
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to install Sage backend: ${error.message}`);
            throw error;
        }
    }
}

module.exports = { BackendInstaller };
