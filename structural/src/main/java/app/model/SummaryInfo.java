package app.model;

/**
 * Resumo estatístico da análise de um projeto.
 */
public class SummaryInfo {
    private int totalClasses;
    private int totalRelationships;
    private int totalCoChangeRelationships;
    private double averageCBO;
    private double averageLCOM;

    public int getTotalClasses() { return totalClasses; }
    public void setTotalClasses(int totalClasses) { this.totalClasses = totalClasses; }

    public int getTotalRelationships() { return totalRelationships; }
    public void setTotalRelationships(int totalRelationships) { this.totalRelationships = totalRelationships; }

    public int getTotalCoChangeRelationships() { return totalCoChangeRelationships; }
    public void setTotalCoChangeRelationships(int n) { this.totalCoChangeRelationships = n; }

    public double getAverageCBO() { return averageCBO; }
    public void setAverageCBO(double averageCBO) { this.averageCBO = averageCBO; }

    public double getAverageLCOM() { return averageLCOM; }
    public void setAverageLCOM(double averageLCOM) { this.averageLCOM = averageLCOM; }
}
