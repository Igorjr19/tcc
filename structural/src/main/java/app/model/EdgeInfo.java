package app.model;

/**
 * Representa uma aresta no grafo de dependências (uma relação entre duas classes).
 */
public class EdgeInfo {
    private String source;
    private String target;
    private RelationType type;
    private RelationCategory category;
    private double weight;

    public EdgeInfo() {}

    public EdgeInfo(String source, String target, RelationType type, double weight) {
        this.source = source;
        this.target = target;
        this.type = type;
        this.category = RelationCategory.fromRelationType(type);
        this.weight = weight;
    }

    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }

    public String getTarget() { return target; }
    public void setTarget(String target) { this.target = target; }

    public RelationType getType() { return type; }
    public void setType(RelationType type) { this.type = type; }

    public RelationCategory getCategory() { return category; }
    public void setCategory(RelationCategory category) { this.category = category; }

    public double getWeight() { return weight; }
    public void setWeight(double weight) { this.weight = weight; }
}
