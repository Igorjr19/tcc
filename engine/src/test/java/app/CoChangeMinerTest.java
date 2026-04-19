package app;

import app.miner.CoChangeMiner;
import app.model.EdgeInfo;
import app.model.NodeInfo;
import app.model.RelationCategory;
import app.model.RelationType;

import org.eclipse.jgit.api.Git;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class CoChangeMinerTest {

    @Nested
    class CoChangeDetectionTest {

        @Test
        void detectsCoChangesAboveThreshold(@TempDir Path tempDir) throws Exception {
            File repoDir = tempDir.toFile();
            try (Git git = Git.init().setDirectory(repoDir).call()) {
                // Cria estrutura src/main/java/p/
                Path srcDir = tempDir.resolve("src/main/java/p");
                Files.createDirectories(srcDir);

                File fileA = srcDir.resolve("Foo.java").toFile();
                File fileB = srcDir.resolve("Bar.java").toFile();

                // 4 commits modificando ambos os arquivos juntos (>= minCoChanges=3)
                for (int i = 1; i <= 4; i++) {
                    Files.writeString(fileA.toPath(), "package p;\npublic class Foo { int v = " + i + "; }");
                    Files.writeString(fileB.toPath(), "package p;\npublic class Bar { int v = " + i + "; }");
                    git.add().addFilepattern(".").call();
                    git.commit().setMessage("commit " + i).call();
                }

                Map<String, NodeInfo> nodeMap = buildNodeMap(
                        "p.Foo", "src/main/java/p/Foo.java",
                        "p.Bar", "src/main/java/p/Bar.java"
                );

                CoChangeMiner miner = new CoChangeMiner();
                List<EdgeInfo> edges = miner.mine(repoDir, nodeMap);

                assertEquals(1, edges.size(), "Deve gerar 1 aresta CO_CHANGE");
                EdgeInfo edge = edges.get(0);
                assertEquals(RelationType.CO_CHANGE, edge.getType());
                assertEquals(RelationCategory.LOGICAL, edge.getCategory());
                assertEquals(4, edge.getCoChangeCount());
                assertEquals(1.0, edge.getWeight(), 0.01, "weight = 4/max(4,4) = 1.0");
            }
        }

        @Test
        void filtersPairsBelowMinCoChanges(@TempDir Path tempDir) throws Exception {
            File repoDir = tempDir.toFile();
            try (Git git = Git.init().setDirectory(repoDir).call()) {
                Path srcDir = tempDir.resolve("src/main/java/p");
                Files.createDirectories(srcDir);

                File fileA = srcDir.resolve("Foo.java").toFile();
                File fileB = srcDir.resolve("Bar.java").toFile();

                // Apenas 2 commits juntos (< minCoChanges=3)
                for (int i = 1; i <= 2; i++) {
                    Files.writeString(fileA.toPath(), "package p;\npublic class Foo { int v = " + i + "; }");
                    Files.writeString(fileB.toPath(), "package p;\npublic class Bar { int v = " + i + "; }");
                    git.add().addFilepattern(".").call();
                    git.commit().setMessage("commit " + i).call();
                }

                Map<String, NodeInfo> nodeMap = buildNodeMap(
                        "p.Foo", "src/main/java/p/Foo.java",
                        "p.Bar", "src/main/java/p/Bar.java"
                );

                CoChangeMiner miner = new CoChangeMiner();
                List<EdgeInfo> edges = miner.mine(repoDir, nodeMap);

                assertTrue(edges.isEmpty(), "Pares com < 3 co-changes devem ser filtrados");
            }
        }

        @Test
        void skipsCommitsExceedingMaxFiles(@TempDir Path tempDir) throws Exception {
            File repoDir = tempDir.toFile();
            try (Git git = Git.init().setDirectory(repoDir).call()) {
                Path srcDir = tempDir.resolve("src/main/java/p");
                Files.createDirectories(srcDir);

                // Cria 5 arquivos
                List<String> fqns = new ArrayList<>();
                for (int f = 0; f < 5; f++) {
                    String name = "Class" + f;
                    Files.writeString(srcDir.resolve(name + ".java"),
                            "package p;\npublic class " + name + " {}");
                    fqns.add("p." + name);
                }

                // 4 commits modificando TODOS os 5 arquivos (maxFilesPerCommit=3 → serão ignorados)
                for (int i = 1; i <= 4; i++) {
                    for (int f = 0; f < 5; f++) {
                        String name = "Class" + f;
                        Files.writeString(srcDir.resolve(name + ".java"),
                                "package p;\npublic class " + name + " { int v = " + i + "; }");
                    }
                    git.add().addFilepattern(".").call();
                    git.commit().setMessage("big commit " + i).call();
                }

                Map<String, NodeInfo> nodeMap = new LinkedHashMap<>();
                for (int f = 0; f < 5; f++) {
                    String name = "Class" + f;
                    nodeMap.put("p." + name, createNode("p." + name, name,
                            "src/main/java/p/" + name + ".java"));
                }

                // maxFilesPerCommit=3 → todos os commits devem ser ignorados
                CoChangeMiner miner = new CoChangeMiner(3, 3);
                List<EdgeInfo> edges = miner.mine(repoDir, nodeMap);

                assertTrue(edges.isEmpty(), "Commits com > maxFilesPerCommit devem ser ignorados");
            }
        }

        @Test
        void calculatesWeightCorrectly(@TempDir Path tempDir) throws Exception {
            File repoDir = tempDir.toFile();
            try (Git git = Git.init().setDirectory(repoDir).call()) {
                Path srcDir = tempDir.resolve("src/main/java/p");
                Files.createDirectories(srcDir);

                File fileA = srcDir.resolve("Foo.java").toFile();
                File fileB = srcDir.resolve("Bar.java").toFile();

                // 3 commits com ambos
                for (int i = 1; i <= 3; i++) {
                    Files.writeString(fileA.toPath(), "package p;\npublic class Foo { int v = " + i + "; }");
                    Files.writeString(fileB.toPath(), "package p;\npublic class Bar { int v = " + i + "; }");
                    git.add().addFilepattern(".").call();
                    git.commit().setMessage("both " + i).call();
                }

                // 3 commits extras só com Foo (total Foo=6, Bar=3)
                for (int i = 4; i <= 6; i++) {
                    Files.writeString(fileA.toPath(), "package p;\npublic class Foo { int v = " + i + "; }");
                    git.add().addFilepattern(".").call();
                    git.commit().setMessage("foo only " + i).call();
                }

                Map<String, NodeInfo> nodeMap = buildNodeMap(
                        "p.Foo", "src/main/java/p/Foo.java",
                        "p.Bar", "src/main/java/p/Bar.java"
                );

                CoChangeMiner miner = new CoChangeMiner();
                List<EdgeInfo> edges = miner.mine(repoDir, nodeMap);

                assertEquals(1, edges.size());
                EdgeInfo edge = edges.get(0);
                assertEquals(3, edge.getCoChangeCount());
                // weight = 3 / max(6, 3) = 0.5
                assertEquals(0.5, edge.getWeight(), 0.01);
            }
        }

        @Test
        void returnsEmptyWhenNoGitDir(@TempDir Path tempDir) {
            // Diretório sem .git
            Map<String, NodeInfo> nodeMap = buildNodeMap(
                    "p.Foo", "src/main/java/p/Foo.java"
            );

            CoChangeMiner miner = new CoChangeMiner();
            List<EdgeInfo> edges = miner.mine(tempDir.toFile(), nodeMap);

            assertTrue(edges.isEmpty(), "Sem .git deve retornar lista vazia");
        }
    }

    // ---- Helpers ----

    private static Map<String, NodeInfo> buildNodeMap(String... fqnAndPaths) {
        Map<String, NodeInfo> map = new LinkedHashMap<>();
        for (int i = 0; i < fqnAndPaths.length; i += 2) {
            String fqn = fqnAndPaths[i];
            String filePath = fqnAndPaths[i + 1];
            String simpleName = fqn.substring(fqn.lastIndexOf('.') + 1);
            map.put(fqn, createNode(fqn, simpleName, filePath));
        }
        return map;
    }

    private static NodeInfo createNode(String fqn, String simpleName, String filePath) {
        NodeInfo node = new NodeInfo();
        node.setId(fqn);
        node.setSimpleName(simpleName);
        node.setPackageName(fqn.substring(0, fqn.lastIndexOf('.')));
        node.setFilePath(filePath);
        return node;
    }
}
