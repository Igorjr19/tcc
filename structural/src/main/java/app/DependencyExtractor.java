package app;

import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import com.github.javaparser.utils.SourceRoot;
import com.github.javaparser.utils.ProjectRoot;
import com.github.javaparser.symbolsolver.JavaSymbolSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.CombinedTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.ReflectionTypeSolver;
import com.github.javaparser.symbolsolver.utils.SymbolSolverCollectionStrategy;
import com.github.javaparser.resolution.declarations.ResolvedMethodDeclaration;

import java.io.File;
import java.io.IOException;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

public class DependencyExtractor {

    public static void main(String[] args) throws IOException {
        if (args.length == 0) {
            System.out.println("Usage: java DependencyExtractor <path-to-project>");
            return;
        }
        File projectDir = new File(args[0]);
        List<String> dependencies = extractDependencies(projectDir);
        dependencies.forEach(System.out::println);
    }

    public static List<String> extractDependencies(File projectDir) throws IOException {
        // For now, this is a placeholder. We will implement pom.xml parsing later.
        // This example shows how to use JavaParser to analyze Java code.
        List<String> dependencies = new ArrayList<>();
        
        // Setup a symbol solver
        CombinedTypeSolver combinedTypeSolver = new CombinedTypeSolver();
        combinedTypeSolver.add(new ReflectionTypeSolver());
        JavaSymbolSolver symbolSolver = new JavaSymbolSolver(combinedTypeSolver);

        // Configure JavaParser to use the symbol solver
        ProjectRoot projectRoot = new SymbolSolverCollectionStrategy().collect(projectDir.toPath());
        
        projectRoot.getSourceRoots().forEach(sourceRoot -> {
            try {
                sourceRoot.tryToParse().forEach(parseResult -> {
                    parseResult.ifSuccessful(compilationUnit -> {
                        compilationUnit.findAll(MethodDeclaration.class).forEach(method -> {
                            try {
                                ResolvedMethodDeclaration resolvedMethod = method.resolve();
                                dependencies.add("Method: " + resolvedMethod.getQualifiedSignature());
                            } catch (Exception e) {
                                // Ignore methods that cannot be resolved
                            }
                        });
                    });
                });
            } catch (IOException e) {
                e.printStackTrace();
            }
        });

        return dependencies;
    }
}
