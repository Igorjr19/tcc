import { NodeInfo } from './NodeInfo';
import { EdgeInfo } from './EdgeInfo';
import { SummaryInfo } from './SummaryInfo';

export interface AnalysisResult {
  projectName: string;
  analyzedAt: string;
  summary: SummaryInfo;
  nodes: NodeInfo[];
  edges: EdgeInfo[];
}
