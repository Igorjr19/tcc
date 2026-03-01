import { InjectionToken } from '@angular/core';
import { AnalysisResult } from '../models/AnalysisResult';

export interface AnalysisPort {
  /**
   * Opens a native folder picker and returns the selected path.
   */
  openFolderPicker(): Promise<string | null>;

  /**
   * Analyzes the project at the given path.
   */
  analyzeProject(projectPath: string): Promise<AnalysisResult>;

  /**
   * Exports the given data in the specified format.
   */
  exportResults?(data: string, format: string): Promise<string | null>;
}

export const ANALYSIS_SERVICE_TOKEN = new InjectionToken<AnalysisPort>('ANALYSIS_SERVICE_TOKEN');
