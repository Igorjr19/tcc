package app;

import app.extractor.ProjectAnalyzer;
import app.model.*;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Teste de integração end-to-end: executa ProjectAnalyzer.analyze() num
 * mini-projeto Java e valida nós, arestas, métricas e summary.
 */
class IntegrationTest {

    @TempDir
    static Path tempDir;

    private static AnalysisResult result;

    @BeforeAll
    static void analyzeProject() throws Exception {
        Path srcDir = tempDir.resolve("src/main/java/sample");
        Files.createDirectories(srcDir);

        Files.writeString(srcDir.resolve("Animal.java"),
                """
                package sample;
                public class Animal {
                    private String name;
                    public String getName() { return name; }
                    public void setName(String name) { this.name = name; }
                    public void eat() { System.out.println(name + " is eating"); }
                }
                """);

        Files.writeString(srcDir.resolve("Dog.java"),
                """
                package sample;
                public class Dog extends Animal {
                    private Collar collar;
                    public Dog(String name) {
                        setName(name);
                        this.collar = new Collar();
                    }
                    public void bark() { System.out.println(getName() + " barks!"); }
                    public Collar getCollar() { return collar; }
                }
                """);

        Files.writeString(srcDir.resolve("Collar.java"),
                """
                package sample;
                public class Collar {
                    private String color;
                    public Collar() { this.color = "red"; }
                    public String getColor() { return color; }
                }
                """);

        Files.writeString(srcDir.resolve("Walkable.java"),
                """
                package sample;
                public interface Walkable {
                    void walk();
                }
                """);

        Files.writeString(srcDir.resolve("PetService.java"),
                """
                package sample;
                public class PetService implements Walkable {
                    private Dog dog;
                    public PetService(Dog dog) { this.dog = dog; }
                    @Override
                    public void walk() {
                        dog.bark();
                        System.out.println("Walking " + dog.getName());
                    }
                    public void feed(Animal animal) { animal.eat(); }
                }
                """);

        ProjectAnalyzer analyzer = new ProjectAnalyzer();
        result = analyzer.analyze(tempDir.toFile());
    }

    @Nested
    class NodeDetectionTest {

        @Test
        void detectsAllFiveTypes() {
            assertEquals(5, result.getNodes().size(), "Deve encontrar 5 tipos");
        }

        @Test
        void containsExpectedClasses() {
            Set<String> ids = result.getNodes().stream()
                    .map(NodeInfo::getId).collect(Collectors.toSet());
            assertTrue(ids.contains("sample.Animal"));
            assertTrue(ids.contains("sample.Dog"));
            assertTrue(ids.contains("sample.Collar"));
            assertTrue(ids.contains("sample.Walkable"));
            assertTrue(ids.contains("sample.PetService"));
        }

        @Test
        void classifiesTypesCorrectly() {
            assertEquals("INTERFACE", findNode("sample.Walkable").getType());
            assertEquals("CLASS", findNode("sample.Dog").getType());
            assertTrue(findNode("sample.Walkable").isInterface());
        }
    }

    @Nested
    class EdgeDetectionTest {

        @Test
        void detectsInheritance() {
            assertTrue(hasEdge("sample.Dog", "sample.Animal", RelationType.INHERITANCE),
                    "Dog extends Animal");
        }

        @Test
        void detectsInterfaceImplementation() {
            assertTrue(hasEdge("sample.PetService", "sample.Walkable", RelationType.INTERFACE_IMPLEMENTATION),
                    "PetService implements Walkable");
        }

        @Test
        void detectsComposition() {
            assertTrue(hasEdge("sample.Dog", "sample.Collar", RelationType.COMPOSITION),
                    "Dog cria Collar com new -> composição");
        }

        @Test
        void detectsAggregation() {
            assertTrue(hasEdge("sample.PetService", "sample.Dog", RelationType.AGGREGATION),
                    "PetService recebe Dog via construtor -> agregação");
        }

        @Test
        void categoriesAreCorrect() {
            List<EdgeInfo> structural = result.getEdges().stream()
                    .filter(e -> e.getCategory() == RelationCategory.STRUCTURAL)
                    .toList();
            List<EdgeInfo> behavioral = result.getEdges().stream()
                    .filter(e -> e.getCategory() == RelationCategory.BEHAVIORAL)
                    .toList();

            assertFalse(structural.isEmpty(), "Deve ter relações estruturais");
            assertFalse(behavioral.isEmpty(), "Deve ter relações comportamentais");
        }
    }

    @Nested
    class MetricsTest {

        @Test
        void dogHasCBOGreaterThanZero() {
            NodeInfo dog = findNode("sample.Dog");
            assertTrue(dog.getMetrics().getCbo() >= 2,
                    "Dog acopla com Animal e Collar, CBO >= 2");
        }

        @Test
        void dogHasDITOf1() {
            NodeInfo dog = findNode("sample.Dog");
            assertEquals(1, dog.getMetrics().getDit(), "Dog extends Animal -> DIT=1");
        }

        @Test
        void animalHasNOCOf1() {
            NodeInfo animal = findNode("sample.Animal");
            assertEquals(1, animal.getMetrics().getNoc(), "Animal tem 1 filho direto (Dog)");
        }

        @Test
        void rfcIsCalculated() {
            NodeInfo service = findNode("sample.PetService");
            assertTrue(service.getMetrics().getRfc() > 0, "PetService tem métodos + chamadas externas");
        }

        @Test
        void locIsCalculated() {
            NodeInfo animal = findNode("sample.Animal");
            assertTrue(animal.getMetrics().getLinesOfCode() > 0, "LOC deve ser > 0");
        }
    }

    @Nested
    class SummaryTest {

        @Test
        void summaryHasCorrectTotals() {
            SummaryInfo s = result.getSummary();
            assertEquals(5, s.getTotalClasses());
            assertTrue(s.getTotalRelationships() > 0);
        }

        @Test
        void summaryHasDistributions() {
            SummaryInfo s = result.getSummary();
            assertNotNull(s.getCboDistribution());
            assertNotNull(s.getLcomDistribution());
            assertNotNull(s.getDitDistribution());
            assertNotNull(s.getRfcDistribution());
            assertNotNull(s.getLocDistribution());
        }

        @Test
        void cboDistributionIsConsistent() {
            MetricDistribution d = result.getSummary().getCboDistribution();
            assertTrue(d.getMin() <= d.getMedian());
            assertTrue(d.getMedian() <= d.getMax());
            assertTrue(d.getMean() >= d.getMin());
            assertTrue(d.getStddev() >= 0);
        }

        @Test
        void categoryCountsSumToTotal() {
            SummaryInfo s = result.getSummary();
            assertEquals(s.getTotalRelationships(),
                    s.getStructuralRelationships() + s.getBehavioralRelationships() + s.getLogicalRelationships(),
                    "Soma das categorias deve igualar o total");
        }
    }

    // --- Helpers ---

    private static NodeInfo findNode(String fqn) {
        return result.getNodes().stream()
                .filter(n -> n.getId().equals(fqn))
                .findFirst()
                .orElseThrow(() -> new AssertionError("Node not found: " + fqn));
    }

    private static boolean hasEdge(String source, String target, RelationType type) {
        return result.getEdges().stream().anyMatch(e ->
                e.getSource().equals(source) &&
                e.getTarget().equals(target) &&
                e.getType() == type);
    }
}
