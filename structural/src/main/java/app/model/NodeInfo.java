package app.model;

/**
 * Representa um nó no grafo de dependências (uma classe, interface, enum ou record).
 */
public class NodeInfo {
    private String id;
    private String simpleName;
    private String packageName;
    private String filePath;
    private String type;
    private CKMetrics metrics;
    private boolean isInterface;
    private boolean isAbstract;

    public NodeInfo() {
        this.metrics = new CKMetrics();
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getSimpleName() { return simpleName; }
    public void setSimpleName(String simpleName) { this.simpleName = simpleName; }

    public String getPackageName() { return packageName; }
    public void setPackageName(String packageName) { this.packageName = packageName; }

    public String getFilePath() { return filePath; }
    public void setFilePath(String filePath) { this.filePath = filePath; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public CKMetrics getMetrics() { return metrics; }
    public void setMetrics(CKMetrics metrics) { this.metrics = metrics; }

    public boolean isInterface() { return isInterface; }
    public void setInterface(boolean anInterface) { isInterface = anInterface; }

    public boolean isAbstract() { return isAbstract; }
    public void setAbstract(boolean anAbstract) { isAbstract = anAbstract; }
}
