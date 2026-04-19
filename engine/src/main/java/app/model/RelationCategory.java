package app.model;

/**
 * Categoria de uma relação entre classes.
 */
public enum RelationCategory {
    /** Relações explícitas na estrutura do código (herança, composição, etc.). */
    STRUCTURAL,
    /** Relações de invocação e acesso em tempo de execução. */
    BEHAVIORAL,
    /** Relações implícitas detectadas por co-mudança no histórico Git. */
    LOGICAL;

    /**
     * Determina a categoria de uma relação a partir do seu tipo.
     */
    public static RelationCategory fromRelationType(RelationType type) {
        return switch (type) {
            case INHERITANCE, INTERFACE_IMPLEMENTATION, COMPOSITION, AGGREGATION, ASSOCIATION -> STRUCTURAL;
            case METHOD_CALL, ATTRIBUTE_ACCESS, TYPE_REFERENCE -> BEHAVIORAL;
            case CO_CHANGE -> LOGICAL;
        };
    }
}
