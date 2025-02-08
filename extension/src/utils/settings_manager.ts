import * as vscode from 'vscode';
import axios from 'axios';

interface ModelConfig {
    model_name: string;
    model_path: string;
    [key: string]: any;  // For other optional properties
}

export class SettingsManager {
    private readonly baseUrl: string;

    constructor(port: number) {
        this.baseUrl = `http://localhost:${port}`;
        this.watchConfigChanges();
    }

    private watchConfigChanges() {
        // Watch for changes in the modelConfig setting
        vscode.workspace.onDidChangeConfiguration(async (event) => {
            if (event.affectsConfiguration('sage.modelConfig')) {
                const config = vscode.workspace.getConfiguration('sage');
                const modelConfig = config.get<ModelConfig>('modelConfig');

                if (modelConfig?.model_name && modelConfig?.model_path) {
                    // If we have valid config, update the model
                    await this.updateModel(modelConfig);
                } else {
                    // If config is cleared/invalid, remove the model
                    await this.removeModel();
                }
            }
        });
    }

    private async updateModel(modelConfig: ModelConfig) {
        try {
            await axios.put(`${this.baseUrl}/llm`, modelConfig);
            vscode.window.showInformationMessage('Sage: Model configuration updated successfully');
        } catch (error: any) {
            vscode.window.showErrorMessage(`Sage: Failed to update model configuration - ${error?.message || 'Unknown error'}`);
        }
    }

    private async removeModel() {
        try {
            await axios.delete(`${this.baseUrl}/llm`);
            vscode.window.showInformationMessage('Sage: Model configuration removed successfully');
        } catch (error: any) {
            vscode.window.showErrorMessage(`Sage: Failed to remove model configuration - ${error?.message || 'Unknown error'}`);
        }
    }

    public async getCurrentModel() {
        try {
            const response = await axios.get(`${this.baseUrl}/llm`);
            return response.data;
        } catch (error: any) {
            vscode.window.showErrorMessage(`Sage: Failed to get current model configuration - ${error?.message || 'Unknown error'}`);
            return null;
        }
    }
}
