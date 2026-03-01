import { Injectable, inject, signal, computed } from '@angular/core';
import { AnalysisResult } from '../models/AnalysisResult';
import { ANALYSIS_SERVICE_TOKEN } from '../services/AnalysisPort';

@Injectable({
  providedIn: 'root',
})
export class AnalysisFacade {
  private analysisService = inject(ANALYSIS_SERVICE_TOKEN);

  // State
  private readonly _analysisData = signal<AnalysisResult | null>(null);
  private readonly _selectedPath = signal<string | null>(null);
  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  // Computed state for components to consume
  readonly analysisData = computed(() => this._analysisData());
  readonly selectedPath = computed(() => this._selectedPath());
  readonly isLoading = computed(() => this._isLoading());
  readonly error = computed(() => this._error());

  // Actions
  async selectProjectFolder(): Promise<void> {
    try {
      this._error.set(null);
      const path = await this.analysisService.openFolderPicker();
      if (path) {
        this._selectedPath.set(path);
      }
    } catch (err: any) {
      this._error.set(err.message || 'Failed to select folder');
    }
  }

  async runAnalysis(): Promise<void> {
    const currentPath = this._selectedPath();
    if (!currentPath) {
      this._error.set('No project selected to analyze');
      return;
    }

    this._isLoading.set(true);
    this._error.set(null);

    try {
      const result = await this.analysisService.analyzeProject(currentPath);
      this._analysisData.set(result);
    } catch (err: any) {
      this._error.set(err.message || 'Failed to analyze project');
    } finally {
      this._isLoading.set(false);
    }
  }

  reset(): void {
    this._analysisData.set(null);
    this._selectedPath.set(null);
    this._error.set(null);
  }
}
