package app.extractor;

import app.model.*;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.*;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Orquestrador principal da análise estática de um projeto Java.
 *
 * <p>Fluxo:
 * <ol>
 *   <li>Encontra todos os arquivos .java do projeto (excluindo tests e target).</li>
 *   <li>Configura o JavaParser com o SymbolSolver.</li>
 *   <li>Faz o parsing de cada arquivo e constrói o mapa de nós (classes).</li>
 *   <li>Extrai as relações tipificadas entre classes.</li>
 *   <li>Monta o resultado final com nós, arestas e resumo.</li>
 * </ol>
 */
public class ProjectAnalyzer {

    /**
     * Executa a análise completa do projeto no diretório informado.
     */
    public AnalysisResult analyze(File projectDir) throws Exception {
        List<File> javaFiles = findJavaFiles(projectDir);
        if (javaFiles.isEmpty()) {
            throw new IllegalArgumentException("Nenhum arquivo .java encontrado em: " + projectDir);
        }

        System.err.println("Encontrados " + javaFiles.size() + " arquivos Java.");

        // 1. Configura parser com SymbolSolver
        JavaParser parser = TypeResolverConfig.createParser(projectDir, javaFiles);

        // 2. Parse de todos os arquivos e construção do mapa de nós
        Map<String, NodeInfo> nodeMap = new LinkedHashMap<>();
        Map<String, TypeDeclaration<?>> typeDeclarations = new LinkedHashMap<>();
        Map<String, CompilationUnit> compilationUnits = new LinkedHashMap<>();

        for (File javaFile : javaFiles) {
            try {
                ParseResult<CompilationUnit> result = parser.parse(javaFile);
                if (result.getResult().isEmpty()) continue;

                CompilationUnit cu = result.getResult().get();
                String packageName = cu.getPackageDeclaration()
                        .map(pd -> pd.getNameAsString()).orElse("");

                processTypeDeclarations(cu, packageName, javaFile, projectDir,
                        nodeMap, typeDeclarations, compilationUnits);
            } catch (Exception e) {
                System.err.println("Warning: falha ao processar " + javaFile.getName() + ": " + e.getMessage());
            }
        }

        System.err.println("Processados " + nodeMap.size() + " tipos.");

        // 3. Extração de relações
        StructuralExtractor extractor = new StructuralExtractor(nodeMap);
        List<EdgeInfo> allEdges = new ArrayList<>();

        for (Map.Entry<String, TypeDeclaration<?>> entry : typeDeclarations.entrySet()) {
            String fqn = entry.getKey();
            TypeDeclaration<?> td = entry.getValue();
            CompilationUnit cu = compilationUnits.get(fqn);
            if (cu == null) continue;

            try {
                List<EdgeInfo> edges = extractor.extractFromClass(fqn, td, cu);
                allEdges.addAll(edges);
            } catch (Exception e) {
                System.err.println("Warning: falha ao extrair relações de " + fqn + ": " + e.getMessage());
            }
        }

        System.err.println("Extraídas " + allEdges.size() + " relações.");

        // 4. Cálculo de métricas CK
        app.metrics.CKMetricsCalculator.calculateAll(nodeMap, typeDeclarations, compilationUnits, allEdges);

        // 5. Montagem do resultado
        return buildResult(projectDir.getName(), nodeMap, allEdges);
    }

    /**
     * Processa todas as declarações de tipo (classes, interfaces, enums, records)
     * encontradas em uma CompilationUnit.
     */
    private void processTypeDeclarations(CompilationUnit cu, String packageName,
                                         File javaFile, File projectDir,
                                         Map<String, NodeInfo> nodeMap,
                                         Map<String, TypeDeclaration<?>> typeDeclarations,
                                         Map<String, CompilationUnit> compilationUnits) {
        String relativePath = projectDir.toPath().relativize(javaFile.toPath()).toString();

        for (TypeDeclaration<?> td : cu.getTypes()) {
            String simpleName = td.getNameAsString();
            String fqn = packageName.isEmpty() ? simpleName : packageName + "." + simpleName;

            NodeInfo node = new NodeInfo();
            node.setId(fqn);
            node.setSimpleName(simpleName);
            node.setPackageName(packageName);
            node.setFilePath(relativePath);
            node.setType(classifyType(td));
            node.setInterface(td instanceof ClassOrInterfaceDeclaration cid && cid.isInterface());
            node.setAbstract(td instanceof ClassOrInterfaceDeclaration cid && cid.isAbstract());

            nodeMap.put(fqn, node);
            typeDeclarations.put(fqn, td);
            compilationUnits.put(fqn, cu);
        }
    }

    private String classifyType(TypeDeclaration<?> td) {
        if (td instanceof ClassOrInterfaceDeclaration cid) {
            return cid.isInterface() ? "INTERFACE" : "CLASS";
        } else if (td instanceof EnumDeclaration) {
            return "ENUM";
        } else if (td instanceof RecordDeclaration) {
            return "RECORD";
        }
        return "CLASS";
    }

    private AnalysisResult buildResult(String projectName,
                                       Map<String, NodeInfo> nodeMap,
                                       List<EdgeInfo> edges) {
        List<NodeInfo> nodes = new ArrayList<>(nodeMap.values());

        // Resumo
        SummaryInfo summary = new SummaryInfo();
        summary.setTotalClasses(nodes.size());
        summary.setTotalRelationships(edges.size());
        summary.setTotalCoChangeRelationships(
                (int) edges.stream().filter(e -> e.getType() == RelationType.CO_CHANGE).count());
        summary.setAverageCBO(nodes.stream()
                .mapToInt(n -> n.getMetrics().getCbo()).average().orElse(0));
        summary.setAverageLCOM(nodes.stream()
                .mapToDouble(n -> n.getMetrics().getLcom()).average().orElse(0));

        AnalysisResult result = new AnalysisResult();
        result.setProjectName(projectName);
        result.setAnalyzedAt(Instant.now().toString());
        result.setSummary(summary);
        result.setNodes(nodes);
        result.setEdges(edges);
        return result;
    }

    /**
     * Encontra todos os arquivos .java do projeto, excluindo diretórios de teste,
     * build e arquivos gerados.
     */
    static List<File> findJavaFiles(File dir) throws Exception {
        try (Stream<Path> paths = Files.walk(dir.toPath())) {
            return paths
                    .filter(Files::isRegularFile)
                    .filter(p -> p.toString().endsWith(".java"))
                    .filter(p -> {
                        String s = p.toString();
                        return !s.contains("/test/") && !s.contains("/tests/")
                                && !s.contains("/target/") && !s.contains("/build/")
                                && !s.contains("/generated/") && !s.contains("/.git/");
                    })
                    .map(Path::toFile)
                    .collect(Collectors.toList());
        }
    }
}
