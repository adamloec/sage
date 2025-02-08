import * as vscode from 'vscode';
const { spawn, exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);
const { platform } = require('os');
const path = require('path');

class ServerManager {
    private _context: vscode.ExtensionContext;
    private _process: any;
    private _isStarting: boolean;
    private _envName: string;
    private _port: number;

    constructor(context: vscode.ExtensionContext) {
        this._context = context;
        this._process = null;
        this._isStarting = false;
        this._envName = 'sage_vscode_env';
        this._port = 8000;
    }

    async startServer() {
        if (this._process) {
            console.log('Server already running');
            return;
        }

        console.log('=== Starting server ===');
        
        const command = await this._getStartCommand();
        console.log('Command:', command);

        this._process = spawn(command.command, command.args, {
            shell: true,
            env: { 
                ...process.env, 
                PYTHONUNBUFFERED: '1',
                PYTHONFAULTHANDLER: '1'
            }
        });

        console.log('Process spawned with PID:', this._process.pid);

        return new Promise<void>((resolve, reject) => {
            const timeout = setTimeout(() => {
                console.log('=== Server startup timed out ===');
                console.log('Last known process state:', this._process ? 'alive' : 'null');
                reject(new Error('Server startup timed out'));
            }, 10000);

            let errorOutput = '';

            this._process.stdout.on('data', (data: Buffer) => {
                const output = data.toString();
                console.log('Server stdout:', output);
            });

            this._process.stderr.on('data', (data: any) => {
                const error = data.toString();
                errorOutput += error;
                console.log('Server stderr:', error);
                
                // Uvicorn logs its startup messages to stderr
                if (error.includes('Uvicorn running on http://')) {
                    console.log('=== Server startup complete ===');
                    clearTimeout(timeout);
                    resolve();
                }
            });

            this._process.on('error', (error: any) => {
                console.log('=== Server process error ===');
                console.log('Error:', error.message);
                clearTimeout(timeout);
                this._process = null;
                reject(error);
            });

            this._process.on('exit', (code: number, signal: string) => {
                console.log('=== Server process exit ===');
                console.log('Exit code:', code);
                console.log('Exit signal:', signal);
                console.log('Collected error output:', errorOutput);
                clearTimeout(timeout);
                this._process = null;
                if (code !== 0 && code !== null) {
                    reject(new Error(`Server exited with code ${code}. Error: ${errorOutput}`));
                }
            });
        });
    }

    async stopServer() {
        if (!this._process) {
            console.log('No server process to stop');
            return;
        }

        console.log('=== Stopping server ===');
        console.log('Killing process:', this._process.pid);
        this._process.kill();
        this._process = null;
        console.log('Server stopped');
    }

    async _getStartCommand() {
        try {
            const envPath = path.join(this._context.extensionPath, this._envName);
            const sagePath = process.platform === 'win32' ?
                path.join(envPath, 'Scripts', 'sage.exe') :
                path.join(envPath, 'bin', 'sage');

            return {
                command: sagePath,
                args: ['serve', '--port', this._port.toString()],
                useShell: true
            };
        } catch (error) {
            console.log('=== Command error ===');
            console.log(error);
            throw error;
        }
    }

    isRunning() {
        return this._process !== null;
    }
}

module.exports = { ServerManager };