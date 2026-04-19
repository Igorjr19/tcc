package app.model;

/**
 * Resumo estatístico da análise de um projeto.
 */
public class SummaryInfo {
    private int totalClasses;
    private int totalRelationships;
    private int structuralRelationships;
    private int behavioralRelationships;
    private int logicalRelationships;

    private MetricDistribution cboDistribution;
    private MetricDistribution lcomDistribution;
    private MetricDistribution ditDistribution;
    private MetricDistribution rfcDistribution;
    private MetricDistribution locDistribution;

    public int getTotalClasses() { return totalClasses; }
    public void setTotalClasses(int totalClasses) { this.totalClasses = totalClasses; }

    public int getTotalRelationships() { return totalRelationships; }
    public void setTotalRelationships(int totalRelationships) { this.totalRelationships = totalRelationships; }

    public int getStructuralRelationships() { return structuralRelationships; }
    public void setStructuralRelationships(int n) { this.structuralRelationships = n; }

    public int getBehavioralRelationships() { return behavioralRelationships; }
    public void setBehavioralRelationships(int n) { this.behavioralRelationships = n; }

    public int getLogicalRelationships() { return logicalRelationships; }
    public void setLogicalRelationships(int n) { this.logicalRelationships = n; }

    public MetricDistribution getCboDistribution() { return cboDistribution; }
    public void setCboDistribution(MetricDistribution d) { this.cboDistribution = d; }

    public MetricDistribution getLcomDistribution() { return lcomDistribution; }
    public void setLcomDistribution(MetricDistribution d) { this.lcomDistribution = d; }

    public MetricDistribution getDitDistribution() { return ditDistribution; }
    public void setDitDistribution(MetricDistribution d) { this.ditDistribution = d; }

    public MetricDistribution getRfcDistribution() { return rfcDistribution; }
    public void setRfcDistribution(MetricDistribution d) { this.rfcDistribution = d; }

    public MetricDistribution getLocDistribution() { return locDistribution; }
    public void setLocDistribution(MetricDistribution d) { this.locDistribution = d; }
}
