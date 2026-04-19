import { InjectionToken } from '@angular/core';
import { AnalysisResult } from '../models/AnalysisResult';

export interface AnalysisPort {
  openFolderPicker(): Promise<string | null>;
  analyzeProject(projectPath: string): Promise<AnalysisResult>;
}

export const ANALYSIS_SERVICE_TOKEN = new InjectionToken<AnalysisPort>('ANALYSIS_SERVICE_TOKEN');
