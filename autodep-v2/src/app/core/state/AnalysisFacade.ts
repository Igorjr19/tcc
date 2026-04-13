import { Injectable, inject, signal, computed } from '@angular/core';
import { AnalysisResult } from '../models/AnalysisResult';
import { NodeInfo } from '../models/NodeInfo';
import { RelationCategory } from '../models/types';
import { ANALYSIS_SERVICE_TOKEN } from '../services/AnalysisPort';

@Injectable({ providedIn: 'root' })
export class AnalysisFacade {
  private analysisService = inject(ANALYSIS_SERVICE_TOKEN);

  private readonly _analysisData = signal<AnalysisResult | null>(null);
  private readonly _selectedPath = signal<string | null>(null);
  private readonly _isLoading = signal(false);
  private readonly _error = signal<string | null>(null);
  private readonly _selectedNode = signal<NodeInfo | null>(null);
  private readonly _activeCategories = signal<Set<RelationCategory>>(
    new Set(['STRUCTURAL', 'BEHAVIORAL', 'LOGICAL']),
  );

  readonly analysisData = computed(() => this._analysisData());
  readonly selectedPath = computed(() => this._selectedPath());
  readonly isLoading = computed(() => this._isLoading());
  readonly error = computed(() => this._error());
  readonly selectedNode = computed(() => this._selectedNode());
  readonly activeCategories = computed(() => this._activeCategories());

  readonly filteredEdges = computed(() => {
    const data = this._analysisData();
    const cats = this._activeCategories();
    if (!data) return [];
    return data.edges.filter((e) => cats.has(e.category));
  });

  async selectProjectFolder(): Promise<void> {
    try {
      this._error.set(null);
      const path = await this.analysisService.openFolderPicker();
      if (path) this._selectedPath.set(path);
    } catch (err: any) {
      this._error.set(err.message || 'Falha ao selecionar pasta');
    }
  }

  async runAnalysis(): Promise<void> {
    const currentPath = this._selectedPath();
    if (!currentPath) {
      this._error.set('Nenhum projeto selecionado');
      return;
    }

    this._isLoading.set(true);
    this._error.set(null);
    this._selectedNode.set(null);

    try {
      const result = await this.analysisService.analyzeProject(currentPath);
      this._analysisData.set(result);
    } catch (err: any) {
      this._error.set(err.message || 'Falha na análise');
    } finally {
      this._isLoading.set(false);
    }
  }

  selectNode(node: NodeInfo | null): void {
    this._selectedNode.set(node);
  }

  toggleCategory(cat: RelationCategory): void {
    const current = new Set(this._activeCategories());
    if (current.has(cat)) {
      current.delete(cat);
    } else {
      current.add(cat);
    }
    this._activeCategories.set(current);
  }

  reset(): void {
    this._analysisData.set(null);
    this._selectedPath.set(null);
    this._selectedNode.set(null);
    this._error.set(null);
  }
}
