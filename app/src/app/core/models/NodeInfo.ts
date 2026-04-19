import { CKMetrics } from './CKMetrics';
import { NodeType } from './types';

export interface NodeInfo {
  id: string;
  simpleName: string;
  packageName: string;
  filePath: string;
  type: NodeType;
  metrics: CKMetrics;
  isInterface: boolean;
  isAbstract: boolean;
}
