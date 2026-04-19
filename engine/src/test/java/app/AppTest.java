package app;

import app.extractor.ProjectAnalyzer;
import app.extractor.StructuralExtractor;
import app.metrics.CKMetricsCalculator;
import app.model.*;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.TypeDeclaration;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class AppTest {

    // ---- Testes do StructuralExtractor ----

    @Nested
    class InheritanceExtractionTest {

        @Test
        void detectsInheritance() {
            String parent = "package p;\npublic class Animal {}";
            String child = "package p;\npublic class Dog extends Animal {}";

            Map<String, NodeInfo> nodeMap = parseToNodeMap(parent, child);
            StructuralExtractor ext = new StructuralExtractor(nodeMap);

            CompilationUnit cu = StaticJavaParser.parse(child);
            TypeDeclaration<?> td = cu.getType(0);
            List<EdgeInfo> edges = ext.extractFromClass("p.Dog", td, cu);

            assertTrue(edges.stream().anyMatch(e ->
                    e.getType() == RelationType.INHERITANCE
                            && e.getSource().equals("p.Dog")
                            && e.getTarget().equals("p.Animal")
                            && e.getCategory() == RelationCategory.STRUCTURAL
            ), "Deve detectar herança Dog -> Animal");
        }

        @Test
        void detectsInterfaceImplementation() {
            String iface = "package p;\npublic interface Runnable {}";
            String impl = "package p;\npublic class Worker implements Runnable {}";

            Map<String, NodeInfo> nodeMap = parseToNodeMap(iface, impl);
            StructuralExtractor ext = new StructuralExtractor(nodeMap);

            CompilationUnit cu = StaticJavaParser.parse(impl);
            List<EdgeInfo> edges = ext.extractFromClass("p.Worker", cu.getType(0), cu);

            assertTrue(edges.stream().anyMatch(e ->
                    e.getType() == RelationType.INTERFACE_IMPLEMENTATION
                            && e.getTarget().equals("p.Runnable")
            ));
        }
    }

    @Nested
    class CompositionAggregationTest {

        @Test
        void detectsComposition() {
            String dep = "package p;\npublic class Engine {}";
            String owner = "package p;\npublic class Car {\n"
                    + "  private Engine engine = new Engine();\n"
                    + "}";

            Map<String, NodeInfo> nodeMap = parseToNodeMap(dep, owner);
            StructuralExtractor ext = new StructuralExtractor(nodeMap);

            CompilationUnit cu = StaticJavaParser.parse(owner);
            List<EdgeInfo> edges = ext.extractFromClass("p.Car", cu.getType(0), cu);

            assertTrue(edges.stream().anyMatch(e ->
                    e.getType() == RelationType.COMPOSITION
                            && e.getSource().equals("p.Car")
                            && e.getTarget().equals("p.Engine")
            ), "Deve detectar composição quando campo é instanciado com new");
        }

        @Test
        void detectsAggregation() {
            String dep = "package p;\npublic class Engine {}";
            String owner = "package p;\npublic class Car {\n"
                    + "  private Engine engine;\n"
                    + "  public Car(Engine engine) { this.engine = engine; }\n"
                    + "}";

            Map<String, NodeInfo> nodeMap = parseToNodeMap(dep, owner);
            StructuralExtractor ext = new StructuralExtractor(nodeMap);

            CompilationUnit cu = StaticJavaParser.parse(owner);
            List<EdgeInfo> edges = ext.extractFromClass("p.Car", cu.getType(0), cu);

            assertTrue(edges.stream().anyMatch(e ->
                    e.getType() == RelationType.AGGREGATION
                            && e.getTarget().equals("p.Engine")
            ), "Deve detectar agregação quando campo é recebido via construtor");
        }
    }

    @Nested
    class AssociationTest {

        @Test
        void detectsMethodParameterAssociation() {
            String dep = "package p;\npublic class Validator {}";
            String user = "package p;\npublic class Service {\n"
                    + "  public void process(Validator v) {}\n"
                    + "}";

            Map<String, NodeInfo> nodeMap = parseToNodeMap(dep, user);
            StructuralExtractor ext = new StructuralExtractor(nodeMap);

            CompilationUnit cu = StaticJavaParser.parse(user);
            List<EdgeInfo> edges = ext.extractFromClass("p.Service", cu.getType(0), cu);

            assertTrue(edges.stream().anyMatch(e ->
                    e.getType() == RelationType.ASSOCIATION
                            && e.getTarget().equals("p.Validator")
            ));
        }
    }

    @Nested
    class CKMetricsTest {

        @Test
        void calculatesCBOFromEdges() {
            Map<String, NodeInfo> nodeMap = new LinkedHashMap<>();
            nodeMap.put("A", createNode("A"));
            nodeMap.put("B", createNode("B"));
            nodeMap.put("C", createNode("C"));

            List<EdgeInfo> edges = List.of(
                    new EdgeInfo("A", "B", RelationType.INHERITANCE, 1.0),
                    new EdgeInfo("A", "C", RelationType.METHOD_CALL, 1.0),
                    new EdgeInfo("B", "C", RelationType.ASSOCIATION, 1.0)
            );

            CKMetricsCalculator.calculateAll(nodeMap, Map.of(), Map.of(), edges);

            assertEquals(2, nodeMap.get("A").getMetrics().getCbo(), "A acopla com B e C");
            assertEquals(2, nodeMap.get("B").getMetrics().getCbo(), "B acopla com A e C");
            assertEquals(2, nodeMap.get("C").getMetrics().getCbo(), "C acopla com A e B");
        }

        @Test
        void calculatesDITWithHierarchy() {
            Map<String, NodeInfo> nodeMap = new LinkedHashMap<>();
            nodeMap.put("A", createNode("A"));
            nodeMap.put("B", createNode("B"));
            nodeMap.put("C", createNode("C"));

            List<EdgeInfo> edges = List.of(
                    new EdgeInfo("B", "A", RelationType.INHERITANCE, 1.0),
                    new EdgeInfo("C", "B", RelationType.INHERITANCE, 1.0)
            );

            CKMetricsCalculator.calculateAll(nodeMap, Map.of(), Map.of(), edges);

            assertEquals(0, nodeMap.get("A").getMetrics().getDit(), "A é raiz");
            assertEquals(1, nodeMap.get("B").getMetrics().getDit(), "B estende A");
            assertEquals(2, nodeMap.get("C").getMetrics().getDit(), "C estende B que estende A");
        }

        @Test
        void calculatesNOC() {
            Map<String, NodeInfo> nodeMap = new LinkedHashMap<>();
            nodeMap.put("Base", createNode("Base"));
            nodeMap.put("Child1", createNode("Child1"));
            nodeMap.put("Child2", createNode("Child2"));

            List<EdgeInfo> edges = List.of(
                    new EdgeInfo("Child1", "Base", RelationType.INHERITANCE, 1.0),
                    new EdgeInfo("Child2", "Base", RelationType.INHERITANCE, 1.0)
            );

            CKMetricsCalculator.calculateAll(nodeMap, Map.of(), Map.of(), edges);

            assertEquals(2, nodeMap.get("Base").getMetrics().getNoc(), "Base tem 2 filhos diretos");
            assertEquals(0, nodeMap.get("Child1").getMetrics().getNoc());
        }
    }

    // ---- Helpers ----

    private Map<String, NodeInfo> parseToNodeMap(String... sources) {
        Map<String, NodeInfo> map = new LinkedHashMap<>();
        for (String src : sources) {
            CompilationUnit cu = StaticJavaParser.parse(src);
            String pkg = cu.getPackageDeclaration()
                    .map(p -> p.getNameAsString()).orElse("");
            for (TypeDeclaration<?> td : cu.getTypes()) {
                String fqn = pkg.isEmpty() ? td.getNameAsString() : pkg + "." + td.getNameAsString();
                NodeInfo node = new NodeInfo();
                node.setId(fqn);
                node.setSimpleName(td.getNameAsString());
                node.setPackageName(pkg);
                map.put(fqn, node);
            }
        }
        return map;
    }

    private NodeInfo createNode(String name) {
        NodeInfo node = new NodeInfo();
        node.setId(name);
        node.setSimpleName(name);
        node.setPackageName("");
        return node;
    }
}
