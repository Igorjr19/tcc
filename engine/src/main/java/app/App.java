package app;

import app.extractor.ProjectAnalyzer;
import app.model.AnalysisResult;
import app.output.JsonOutputWriter;

import java.io.File;

/**
 * Ponto de entrada do motor de análise de dependências.
 *
 * <p>Uso: {@code java -jar structural.jar <caminho-do-projeto>}
 *
 * <p>O JSON resultante é impresso em stdout. Mensagens de progresso e warnings
 * são enviadas para stderr, garantindo que o stdout contenha apenas JSON válido.
 */
public class App {

    public static void main(String[] args) {
        if (args.length == 0) {
            System.err.println("Uso: java -jar structural.jar <caminho-do-projeto>");
            System.exit(1);
        }

        File projectDir = new File(args[0]);
        if (!projectDir.exists() || !projectDir.isDirectory()) {
            System.err.println("Erro: o caminho informado não é um diretório válido: " + args[0]);
            System.exit(1);
        }

        try {
            ProjectAnalyzer analyzer = new ProjectAnalyzer();
            AnalysisResult result = analyzer.analyze(projectDir);
            System.out.println(JsonOutputWriter.toJson(result));
        } catch (Exception e) {
            System.err.println("Erro durante a análise: " + e.getMessage());
            e.printStackTrace(System.err);
            System.exit(1);
        }
    }
}
