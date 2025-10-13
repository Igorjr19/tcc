package app;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Classe principal para extrair métricas de um projeto Java.
 *
 * Esta classe é responsável por percorrer um diretório de projeto,
 * encontrar todos os arquivos .java e invocar o parser para análise.
 *
 */
public class MetricExtractor {

    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Uso: java MetricExtractor <caminho_do_projeto>");
            return;
        }

        String projectPath = args[0];
        File projectDir = new File(projectPath);

        if (!projectDir.exists() || !projectDir.isDirectory()) {
            System.err.println("O caminho fornecido não é um diretório válido.");
            return;
        }

        List<File> javaFiles = findJavaFiles(projectDir);

        if (javaFiles.isEmpty()) {
            System.err.println("Nenhum arquivo .java encontrado no diretório.");
            return;
        }

        System.out.println("Iniciando a análise de " + javaFiles.size() + " arquivos Java...");

        JavaParser javaParser = new JavaParser();
        Map<String, Map<String, Object>> metrics = new HashMap<>();

        for (File file : javaFiles) {
            try {
                System.out.println("Analisando o arquivo: " + file.getAbsolutePath());
                CompilationUnit cu = javaParser.parse(file).getResult().get();

                cu.findFirst(ClassOrInterfaceDeclaration.class).ifPresent(c -> {
                    String className = c.getNameAsString();
                    System.out.println("Extraindo métricas para a classe: " + className);

                    // Extraindo dependências e informações para as métricas
                    Map<String, Object> parseData = CodeParser.parseClassData(cu);
                    Set<String> dependencies = (Set<String>) parseData.get("dependencies");
                    Map<String, Set<String>> methodFieldAccess = (Map<String, Set<String>>) parseData.get("methodFieldAccess");
                    Set<String> methodCalls = (Set<String>) parseData.get("methodCalls");

                    // Calculando métricas
                    int cbo = MetricCollector.calculateCBO(dependencies);
                    int dit = MetricCollector.calculateDIT(cu);
                    int lcom = MetricCollector.calculateLCOM(methodFieldAccess);
                    int rfc = MetricCollector.calculateRFC(cu, methodCalls);

                    // Armazenando os resultados
                    Map<String, Object> classMetrics = new HashMap<>();
                    classMetrics.put("CBO", cbo);
                    classMetrics.put("DIT", dit);
                    classMetrics.put("LCOM", lcom);
                    classMetrics.put("RFC", rfc);
                    classMetrics.put("Dependencies", dependencies);
                    metrics.put(className, classMetrics);
                });

            } catch (FileNotFoundException e) {
                System.err.println("Arquivo não encontrado: " + file.getAbsolutePath());
            } catch (Exception e) {
                System.err.println("Erro ao analisar o arquivo " + file.getAbsolutePath() + ": " + e.getMessage());
            }
        }

        System.out.println("\n--- Análise Concluída ---");
        metrics.forEach((className, classMetrics) -> {
            System.out.println("\nClasse: " + className);
            System.out.println("  CBO: " + classMetrics.get("CBO"));
            System.out.println("  DIT: " + classMetrics.get("DIT"));
            System.out.println("  LCOM: " + classMetrics.get("LCOM"));
            System.out.println("  RFC: " + classMetrics.get("RFC"));
            System.out.println("  Dependências: " + classMetrics.get("Dependencies"));
        });

        // Exportar métricas para CSV
        exportMetricsToCSV(metrics, "metrics.csv");
        
        // Exportar dependências para CSV
        exportDependenciesToCSV(metrics, "dependencies.csv");
    }

    /**
     * Encontra recursivamente todos os arquivos .java em um diretório.
     *
     * @param directory O diretório a ser pesquisado.
     * @return Uma lista de arquivos .java.
     */
    private static List<File> findJavaFiles(File directory) {
        List<File> javaFiles = new ArrayList<>();
        File[] files = directory.listFiles();
        if (files != null) {
            for (File file : files) {
                if (file.isDirectory()) {
                    javaFiles.addAll(findJavaFiles(file));
                } else if (file.getName().endsWith(".java")) {
                    javaFiles.add(file);
                }
            }
        }
        return javaFiles;
    }

    /**
     * Exporta as métricas para um arquivo CSV.
     *
     * @param metrics Mapa com as métricas de cada classe.
     * @param outputFile Nome do arquivo de saída.
     */
    private static void exportMetricsToCSV(Map<String, Map<String, Object>> metrics, String outputFile) {
        try (java.io.PrintWriter writer = new java.io.PrintWriter(new java.io.FileWriter(outputFile))) {
            // Cabeçalho
            writer.println("Classe,CBO,DIT,LCOM,RFC");
            
            // Dados
            metrics.forEach((className, classMetrics) -> {
                writer.printf("%s,%s,%s,%s,%s%n",
                    className,
                    classMetrics.get("CBO"),
                    classMetrics.get("DIT"),
                    classMetrics.get("LCOM"),
                    classMetrics.get("RFC")
                );
            });
            
            System.out.println("\nMétricas exportadas para: " + outputFile);
        } catch (java.io.IOException e) {
            System.err.println("Erro ao exportar métricas: " + e.getMessage());
        }
    }

    /**
     * Exporta as dependências explícitas para um arquivo CSV.
     *
     * @param metrics Mapa com as métricas e dependências de cada classe.
     * @param outputFile Nome do arquivo de saída.
     */
    private static void exportDependenciesToCSV(Map<String, Map<String, Object>> metrics, String outputFile) {
        try (java.io.PrintWriter writer = new java.io.PrintWriter(new java.io.FileWriter(outputFile))) {
            // Cabeçalho
            writer.println("Classe1,Classe2,DependenciaExplicita");
            
            // Dados - extrair pares de dependências
            metrics.forEach((className, classMetrics) -> {
                @SuppressWarnings("unchecked")
                Set<String> dependencies = (Set<String>) classMetrics.get("Dependencies");
                if (dependencies != null && !dependencies.isEmpty()) {
                    dependencies.forEach(dependency -> {
                        // Remove qualificadores de pacote para simplificar
                        String simpleDependency = dependency.contains(".") 
                            ? dependency.substring(dependency.lastIndexOf('.') + 1) 
                            : dependency;
                        writer.printf("%s,%s,1%n", className, simpleDependency);
                    });
                }
            });
            
            System.out.println("Dependências exportadas para: " + outputFile);
        } catch (java.io.IOException e) {
            System.err.println("Erro ao exportar dependências: " + e.getMessage());
        }
    }
}
