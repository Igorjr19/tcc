package app.metrics;

import app.model.CKMetrics;
import app.model.EdgeInfo;
import app.model.NodeInfo;
import app.model.RelationType;

import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.expr.FieldAccessExpr;
import com.github.javaparser.ast.expr.NameExpr;
import com.github.javaparser.ast.expr.ThisExpr;

import java.util.*;

/**
 * Calcula as métricas CK (Chidamber & Kemerer) para cada classe do projeto.
 *
 * <p>Métricas calculadas:
 * <ul>
 *   <li><b>CBO</b> — Coupling Between Objects: classes distintas acopladas (bidirecional).</li>
 *   <li><b>LCOM</b> — Lack of Cohesion in Methods: proporção de pares de métodos
 *       que não compartilham acesso a atributos da classe (0 a 1).</li>
 *   <li><b>DIT</b> — Depth of Inheritance Tree: profundidade na hierarquia.</li>
 *   <li><b>NOC</b> — Number of Children: subclasses diretas.</li>
 *   <li><b>RFC</b> — Response for a Class: métodos próprios + métodos externos invocados.</li>
 *   <li>Contadores auxiliares: numberOfMethods, numberOfAttributes, linesOfCode.</li>
 * </ul>
 */
public class CKMetricsCalculator {

    /**
     * Calcula todas as métricas CK para cada nó a partir das declarações e arestas.
     */
    public static void calculateAll(Map<String, NodeInfo> nodeMap,
                                    Map<String, TypeDeclaration<?>> declarations,
                                    Map<String, CompilationUnit> cuMap,
                                    List<EdgeInfo> edges) {
        calculateCBO(nodeMap, edges);
        calculateDIT(nodeMap, edges);
        calculateNOC(nodeMap, edges);

        for (Map.Entry<String, NodeInfo> entry : nodeMap.entrySet()) {
            String fqn = entry.getKey();
            NodeInfo node = entry.getValue();
            TypeDeclaration<?> td = declarations.get(fqn);
            CompilationUnit cu = cuMap.get(fqn);
            if (td == null) continue;

            calculateLCOM(node, td);
            calculateRFC(node, td);
            calculateBasicCounts(node, td, cu);
        }
    }

    /**
     * CBO: para cada classe, conta as classes distintas com as quais há
     * acoplamento (considerando arestas em ambas as direções).
     */
    private static void calculateCBO(Map<String, NodeInfo> nodeMap, List<EdgeInfo> edges) {
        Map<String, Set<String>> coupledClasses = new HashMap<>();

        for (EdgeInfo edge : edges) {
            if (edge.getType() == RelationType.CO_CHANGE) continue;

            coupledClasses.computeIfAbsent(edge.getSource(), k -> new HashSet<>())
                    .add(edge.getTarget());
            coupledClasses.computeIfAbsent(edge.getTarget(), k -> new HashSet<>())
                    .add(edge.getSource());
        }

        for (Map.Entry<String, NodeInfo> entry : nodeMap.entrySet()) {
            Set<String> coupled = coupledClasses.getOrDefault(entry.getKey(), Set.of());
            entry.getValue().getMetrics().setCbo(coupled.size());
        }
    }

    /**
     * DIT: percorre a cadeia de herança (INHERITANCE edges) até a raiz.
     * Usa memoização para eficiência.
     */
    private static void calculateDIT(Map<String, NodeInfo> nodeMap, List<EdgeInfo> edges) {
        // Monta mapa: classe → classe pai
        Map<String, String> parentMap = new HashMap<>();
        for (EdgeInfo edge : edges) {
            if (edge.getType() == RelationType.INHERITANCE) {
                parentMap.put(edge.getSource(), edge.getTarget());
            }
        }

        Map<String, Integer> ditCache = new HashMap<>();
        for (String fqn : nodeMap.keySet()) {
            int depth = computeDIT(fqn, parentMap, ditCache, nodeMap);
            nodeMap.get(fqn).getMetrics().setDit(depth);
        }
    }

    private static int computeDIT(String fqn, Map<String, String> parentMap,
                                  Map<String, Integer> cache, Map<String, NodeInfo> nodeMap) {
        if (cache.containsKey(fqn)) return cache.get(fqn);

        String parent = parentMap.get(fqn);
        int depth;
        if (parent == null || !nodeMap.containsKey(parent)) {
            depth = 0;
        } else {
            depth = 1 + computeDIT(parent, parentMap, cache, nodeMap);
        }
        cache.put(fqn, depth);
        return depth;
    }

    /**
     * NOC: conta o número de subclasses diretas para cada classe.
     */
    private static void calculateNOC(Map<String, NodeInfo> nodeMap, List<EdgeInfo> edges) {
        Map<String, Integer> childCount = new HashMap<>();
        for (EdgeInfo edge : edges) {
            if (edge.getType() == RelationType.INHERITANCE) {
                childCount.merge(edge.getTarget(), 1, Integer::sum);
            }
        }
        for (Map.Entry<String, NodeInfo> entry : nodeMap.entrySet()) {
            entry.getValue().getMetrics().setNoc(childCount.getOrDefault(entry.getKey(), 0));
        }
    }

    /**
     * LCOM: proporção de pares de métodos que NÃO compartilham acesso a atributos.
     *
     * <p>Para cada par de métodos (M_i, M_j):
     * <ul>
     *   <li>Se a interseção dos atributos acessados é vazia → P++</li>
     *   <li>Caso contrário → Q++</li>
     * </ul>
     * LCOM = P / (P + Q), ou 0 se não houver pares.
     */
    private static void calculateLCOM(NodeInfo node, TypeDeclaration<?> td) {
        // Coleta todos os nomes de campos da classe
        Set<String> classFields = new HashSet<>();
        for (FieldDeclaration field : td.getFields()) {
            for (VariableDeclarator v : field.getVariables()) {
                classFields.add(v.getNameAsString());
            }
        }

        if (classFields.isEmpty()) {
            node.getMetrics().setLcom(0);
            return;
        }

        // Para cada método, determina quais campos da classe ele acessa
        List<Set<String>> methodFieldSets = new ArrayList<>();
        for (MethodDeclaration method : td.getMethods()) {
            Set<String> accessed = new HashSet<>();

            // NameExpr que coincidem com nomes de campos
            method.findAll(NameExpr.class).forEach(ne -> {
                if (classFields.contains(ne.getNameAsString())) {
                    accessed.add(ne.getNameAsString());
                }
            });

            // this.field
            method.findAll(FieldAccessExpr.class).forEach(fa -> {
                if (fa.getScope() instanceof ThisExpr) {
                    if (classFields.contains(fa.getNameAsString())) {
                        accessed.add(fa.getNameAsString());
                    }
                }
            });

            methodFieldSets.add(accessed);
        }

        if (methodFieldSets.size() <= 1) {
            node.getMetrics().setLcom(0);
            return;
        }

        int p = 0, q = 0;
        for (int i = 0; i < methodFieldSets.size(); i++) {
            for (int j = i + 1; j < methodFieldSets.size(); j++) {
                Set<String> intersection = new HashSet<>(methodFieldSets.get(i));
                intersection.retainAll(methodFieldSets.get(j));
                if (intersection.isEmpty()) {
                    p++;
                } else {
                    q++;
                }
            }
        }

        double lcom = (p + q) > 0 ? (double) p / (p + q) : 0;
        node.getMetrics().setLcom(Math.round(lcom * 100.0) / 100.0);
    }

    /**
     * RFC: número de métodos da própria classe + número de métodos distintos
     * invocados em outras classes.
     */
    private static void calculateRFC(NodeInfo node, TypeDeclaration<?> td) {
        int ownMethods = td.getMethods().size();

        Set<String> externalCalls = new HashSet<>();
        td.findAll(com.github.javaparser.ast.expr.MethodCallExpr.class).forEach(call -> {
            if (call.getScope().isPresent()) {
                externalCalls.add(call.getNameAsString());
            }
        });

        node.getMetrics().setRfc(ownMethods + externalCalls.size());
    }

    /**
     * Contadores básicos: métodos, atributos e linhas de código.
     */
    private static void calculateBasicCounts(NodeInfo node, TypeDeclaration<?> td,
                                             CompilationUnit cu) {
        node.getMetrics().setNumberOfMethods(td.getMethods().size());

        int fieldCount = 0;
        for (FieldDeclaration f : td.getFields()) {
            fieldCount += f.getVariables().size();
        }
        node.getMetrics().setNumberOfAttributes(fieldCount);

        // LOC: usa o range da declaração de tipo se disponível, senão da CU
        if (td.getRange().isPresent()) {
            int begin = td.getRange().get().begin.line;
            int end = td.getRange().get().end.line;
            node.getMetrics().setLinesOfCode(end - begin + 1);
        } else if (cu != null && cu.getRange().isPresent()) {
            node.getMetrics().setLinesOfCode(
                    cu.getRange().get().end.line - cu.getRange().get().begin.line + 1);
        }
    }
}
