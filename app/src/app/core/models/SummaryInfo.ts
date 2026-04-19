export interface MetricDistribution {
  min: number;
  max: number;
  mean: number;
  median: number;
  stddev: number;
}

export interface SummaryInfo {
  totalClasses: number;
  totalRelationships: number;
  structuralRelationships: number;
  behavioralRelationships: number;
  logicalRelationships: number;
  cboDistribution: MetricDistribution;
  lcomDistribution: MetricDistribution;
  ditDistribution: MetricDistribution;
  rfcDistribution: MetricDistribution;
  locDistribution: MetricDistribution;
}
