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
            const shell = process.platform === 'win32' ? 'cmd.exe' : '/bin/bash';
            return await execAsync(`conda run -n ${this.ENV_NAME} ${command}`, {
                shell,
                env: { ...process.env }
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
            return spawn('conda', ['run', '-n', this.ENV_NAME, command, ...args], {
                shell: true,
                env: { ...process.env }
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