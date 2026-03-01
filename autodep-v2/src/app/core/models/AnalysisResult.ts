import { ClassInfo } from './ClassInfo';

export interface AnalysisResult {
  projectName: string;
  projectPath: string;
  projectGroupId: string;
  totalClasses: number;
  averageCoupling: number;
  maxCoupling: number;
  highlyCoupledClasses: number;
  classes: ClassInfo[];
}
