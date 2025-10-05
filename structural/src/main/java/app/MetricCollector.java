package app;

import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import java.util.Set;
import java.util.Map;
import java.util.HashSet;

/**
 * Coleta e calcula métricas de qualidade para uma classe.
 *
 */
public class MetricCollector {

    /**
     * Calcula o CBO (Coupling Between Objects) para uma classe.
     *
     * @param dependencies O conjunto de dependências.
     * @return O valor de CBO.
     */
    public static int calculateCBO(Set<String> dependencies) {
        return dependencies.size();
    }

    /**
     * Calcula o DIT (Depth of Inheritance Tree) para uma classe.
     * Para este protótipo, a implementação é simplificada.
     *
     * @param cu A unidade de compilação.
     * @return O valor de DIT (neste caso, 1 se estende outra classe, 0 caso contrário).
     */
    public static int calculateDIT(CompilationUnit cu) {
        final int[] dit = {0};
        cu.findFirst(ClassOrInterfaceDeclaration.class).ifPresent(c -> {
            if (!c.getExtendedTypes().isEmpty()) {
                dit[0] = 1;
            }
        });
        return dit[0];
    }

    /**
     * Calcula o LCOM (Lack of Cohesion in Methods) para uma classe.
     * A implementação é simplificada para este protótipo, contando pares de
     * métodos que não acessam nenhum campo em comum.
     *
     * @param methodFieldAccess Um mapa de métodos para os campos que eles acessam.
     * @return O valor de LCOM.
     */
    public static int calculateLCOM(Map<String, Set<String>> methodFieldAccess) {
        if (methodFieldAccess.size() <= 1) {
            return 0;
        }

        int p = 0; // Pares de métodos sem campos em comum
        int q = 0; // Pares de métodos com campos em comum
        Set<String> methods = methodFieldAccess.keySet();
        String[] methodArray = methods.toArray(new String[0]);

        for (int i = 0; i < methodArray.length; i++) {
            for (int j = i + 1; j < methodArray.length; j++) {
                Set<String> fields1 = methodFieldAccess.get(methodArray[i]);
                Set<String> fields2 = methodFieldAccess.get(methodArray[j]);

                Set<String> intersection = new HashSet<>(fields1);
                intersection.retainAll(fields2);

                if (intersection.isEmpty()) {
                    p++;
                } else {
                    q++;
                }
            }
        }
        return p > q ? p - q : 0;
    }

    /**
     * Calcula o RFC (Response For a Class) para uma classe.
     *
     * @param cu A unidade de compilação.
     * @param methodCalls Um conjunto de nomes de métodos chamados.
     * @return O valor de RFC.
     */
    public static int calculateRFC(CompilationUnit cu, Set<String> methodCalls) {
        long declaredMethods = cu.findFirst(ClassOrInterfaceDeclaration.class)
                                 .map(c -> c.getMethods().size())
                                 .orElse(0);
        return (int) (declaredMethods + methodCalls.size());
    }
}
