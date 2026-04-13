package app.model;

import java.util.List;

/**
 * Resultado completo da análise de um projeto Java.
 * Este é o objeto raiz serializado como JSON.
 */
public class AnalysisResult {
    private String projectName;
    private String analyzedAt;
    private SummaryInfo summary;
    private List<NodeInfo> nodes;
    private List<EdgeInfo> edges;

    public String getProjectName() { return projectName; }
    public void setProjectName(String projectName) { this.projectName = projectName; }

    public String getAnalyzedAt() { return analyzedAt; }
    public void setAnalyzedAt(String analyzedAt) { this.analyzedAt = analyzedAt; }

    public SummaryInfo getSummary() { return summary; }
    public void setSummary(SummaryInfo summary) { this.summary = summary; }

    public List<NodeInfo> getNodes() { return nodes; }
    public void setNodes(List<NodeInfo> nodes) { this.nodes = nodes; }

    public List<EdgeInfo> getEdges() { return edges; }
    public void setEdges(List<EdgeInfo> edges) { this.edges = edges; }
}
