const { exec, spawn } = require('child_process');
const { promisify } = require('util');
const path = require('path');
const fs = require('fs');

const execAsync = promisify(exec);

class EnvironmentManager {
    constructor(context) {
        this.context = context;
        this.extensionPath = context.extensionPath;
        this.ENV_NAME = 'sage_vscode_env';
    }

    async executeInEnvironment(command) {
        const envType = await this.detectEnvironmentType();
        if (!envType) {
            throw new Error('No Sage environment found. Please install the backend first.');
        }

        if (envType === 'conda') {
            // Use conda activate, then run command
            const activateCommand = process.platform === 'win32'
                ? `conda activate ${this.ENV_NAME} && ${command}`
                : `conda activate ${this.ENV_NAME} && ${command}`;
            return await execAsync(activateCommand, { 
                shell: process.platform === 'win32' ? 'cmd.exe' : '/bin/bash',
                env: {
                    ...process.env,
                    CONDA_SHLVL: "1"  // Ensure conda environment is initialized
                }
            });
        } else {
            const envPath = path.join(this.extensionPath, '..', this.ENV_NAME);
            const binPath = process.platform === 'win32' ? 
                path.join(envPath, 'Scripts') :
                path.join(envPath, 'bin');
            
            const env = { ...process.env };
            env.PATH = `${binPath}${path.delimiter}${env.PATH}`;
            return await execAsync(command, { env });
        }
    }

    async spawnInEnvironment(command, args = []) {
        const envType = await this.detectEnvironmentType();
        if (!envType) {
            throw new Error('No Sage environment found. Please install the backend first.');
        }

        if (envType === 'conda') {
            // For Windows
            if (process.platform === 'win32') {
                return spawn('cmd', ['/c', `conda activate ${this.ENV_NAME} && ${command}`], {
                    shell: true
                });
            }
            // For Unix-like systems
            return spawn('/bin/bash', ['-c', `conda activate ${this.ENV_NAME} && ${command}`], {
                shell: true,
                env: {
                    ...process.env,
                    CONDA_SHLVL: "1"  // Ensure conda environment is initialized
                }
            });
        } else {
            const envPath = path.join(this.extensionPath, '..', this.ENV_NAME);
            const binPath = process.platform === 'win32' ? 
                path.join(envPath, 'Scripts') :
                path.join(envPath, 'bin');
            
            const env = { ...process.env };
            env.PATH = `${binPath}${path.delimiter}${env.PATH}`;
            return spawn(command, args, {
                env,
                shell: true
            });
        }
    }

    async detectEnvironmentType() {
        try {
            // Check for conda environment
            const { stdout: condaList } = await execAsync('conda env list');
            if (condaList.includes(this.ENV_NAME)) {
                return 'conda';
            }

            // Check for venv environment
            const venvPath = path.join(this.extensionPath, '..', this.ENV_NAME);
            if (fs.existsSync(venvPath)) {
                return 'venv';
            }

            return null;
        } catch (error) {
            console.error('Error detecting environment:', error);
            return null;
        }
    }
}

module.exports = { EnvironmentManager }; 