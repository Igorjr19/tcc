import { Injectable } from '@angular/core';
import { invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';
import { AnalysisPort } from './AnalysisPort';
import { AnalysisResult } from '../models/AnalysisResult';

@Injectable({
    providedIn: 'root'
})
export class TauriAnalysisService implements AnalysisPort {

    private isTauri(): boolean {
        return !!(window as any).__TAURI_INTERNALS__;
    }

    async openFolderPicker(): Promise<string | null> {
        if (!this.isTauri()) {
            throw new Error("A seleção de pastas funciona apenas no Desktop (Tauri).");
        }
        try {
            const selected = await open({
                directory: true,
                multiple: false,
                title: 'Selecione o diretório do projeto'
            });
            return selected ? (Array.isArray(selected) ? selected[0] : selected) : null;
        } catch (error) {
            console.error("Dialog error:", error);
            throw new Error("Ocorreu um erro ao abrir a seleção de arquivos.");
        }
    }

    async analyzeProject(projectPath: string): Promise<AnalysisResult> {
        if (!this.isTauri()) {
            throw new Error("A análise funciona apenas no Desktop (Tauri).");
        }

        try {
            const resultString = await invoke<string>('analyze_project', { projectPath });
            const parsedResult = JSON.parse(resultString) as AnalysisResult;

            parsedResult.classes = parsedResult.classes.map(c => {
                const total = (c.couplingIn || 0) + (c.couplingOut || 0);
                const inst = total === 0 ? 0 : (c.couplingOut || 0) / total;
                return {
                    ...c,
                    totalCoupling: total,
                    instability: inst
                };
            });

            return parsedResult;
        } catch (error) {
            console.error("Tauri analysis failed:", error);
            if (error instanceof Error) {
                throw error;
            } else if (typeof error === 'string') {
                throw new Error(error);
            }
            throw new Error("Falha na comunicação com o Rust.");
        }
    }
}
