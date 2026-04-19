package app.extractor;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParserConfiguration;
import com.github.javaparser.symbolsolver.JavaSymbolSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.CombinedTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.JavaParserTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.ReflectionTypeSolver;

import java.io.*;
import java.nio.file.Path;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Configura o JavaParser com o SymbolSolver para resolução de tipos.
 *
 * <p>A resolução usa duas fontes:
 * <ul>
 *   <li>ReflectionTypeSolver — tipos do JDK (java.lang, java.util, etc.)</li>
 *   <li>JavaParserTypeSolver — tipos do próprio projeto analisado</li>
 * </ul>
 */
public class TypeResolverConfig {

    private static final Pattern PACKAGE_PATTERN =
            Pattern.compile("^\\s*package\\s+([\\w.]+)\\s*;");

    /**
     * Cria um JavaParser configurado com o SymbolSolver para o projeto informado.
     * Se a configuração do solver falhar, retorna um parser sem resolução simbólica.
     */
    public static JavaParser createParser(File projectDir, List<File> javaFiles) {
        ParserConfiguration config = new ParserConfiguration()
                .setLanguageLevel(ParserConfiguration.LanguageLevel.JAVA_17);

        try {
            Set<Path> sourceRoots = findSourceRoots(javaFiles);
            if (!sourceRoots.isEmpty()) {
                CombinedTypeSolver solver = new CombinedTypeSolver();
                solver.add(new ReflectionTypeSolver());
                for (Path root : sourceRoots) {
                    solver.add(new JavaParserTypeSolver(root));
                }
                config.setSymbolResolver(new JavaSymbolSolver(solver));
            }
        } catch (Exception e) {
            System.err.println("Warning: Could not configure SymbolSolver: " + e.getMessage());
        }

        return new JavaParser(config);
    }

    /**
     * Descobre os source roots do projeto analisando as declarações de pacote
     * dos arquivos Java e derivando o diretório raiz correspondente.
     *
     * <p>Por exemplo, se um arquivo em {@code src/main/java/com/example/Foo.java}
     * declara {@code package com.example}, o source root é {@code src/main/java/}.
     */
    static Set<Path> findSourceRoots(List<File> javaFiles) {
        Set<Path> roots = new LinkedHashSet<>();

        for (File f : javaFiles) {
            String pkg = readPackageLine(f);
            if (pkg == null || pkg.isEmpty()) continue;

            Path parent = f.toPath().getParent();
            Path pkgPath = Path.of(pkg.replace('.', File.separatorChar));

            if (parent.endsWith(pkgPath)) {
                Path root = parent;
                for (int i = 0; i < pkgPath.getNameCount(); i++) {
                    root = root.getParent();
                }
                roots.add(root);
            }
        }
        return roots;
    }

    private static String readPackageLine(File file) {
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            String line;
            int linesRead = 0;
            while ((line = reader.readLine()) != null && linesRead < 30) {
                linesRead++;
                Matcher m = PACKAGE_PATTERN.matcher(line);
                if (m.find()) {
                    return m.group(1);
                }
                // Se encontrou uma declaração de classe/interface antes do package, não tem package
                if (line.trim().startsWith("public ") || line.trim().startsWith("class ")
                        || line.trim().startsWith("interface ")) {
                    break;
                }
            }
        } catch (IOException e) {
            // Ignora
        }
        return null;
    }
}
