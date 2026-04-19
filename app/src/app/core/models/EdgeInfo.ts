import { RelationType, RelationCategory } from './types';

export interface EdgeInfo {
  source: string;
  target: string;
  type: RelationType;
  category: RelationCategory;
  weight: number;
  coChangeCount?: number;
  totalCommits?: number;
}
