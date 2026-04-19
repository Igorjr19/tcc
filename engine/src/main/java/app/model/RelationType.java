package app.model;

/**
 * Tipos de relação entre classes detectados pela análise.
 */
public enum RelationType {
    /** Herança direta (extends). */
    INHERITANCE,
    /** Implementação de interface (implements). */
    INTERFACE_IMPLEMENTATION,
    /** Atributo de tipo de outra classe instanciado internamente. */
    COMPOSITION,
    /** Atributo de tipo de outra classe recebido por construtor ou setter. */
    AGGREGATION,
    /** Referência a outra classe como parâmetro de método, variável local ou retorno. */
    ASSOCIATION,
    /** Invocação de método de outra classe. */
    METHOD_CALL,
    /** Acesso direto a atributo público de outra classe. */
    ATTRIBUTE_ACCESS,
    /** Uso de outra classe como tipo (casts, instanceof, generics). */
    TYPE_REFERENCE,
    /** Classes modificadas juntas no histórico Git. */
    CO_CHANGE
}
