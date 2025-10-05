package app;

import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.type.ClassOrInterfaceType;
import com.github.javaparser.ast.expr.ObjectCreationExpr;
import com.github.javaparser.ast.expr.MethodCallExpr;
import com.github.javaparser.ast.expr.FieldAccessExpr;
import java.util.HashSet;
import java.util.Set;
import java.util.Map;
import java.util.HashMap;

/**
 * Analisa uma unidade de compilação (arquivo Java) para extrair
 * dependências estruturais e informações para o cálculo de métricas.
 *
 */
public class CodeParser {

    /**
     * Coleta as dependências de acoplamento e informações para RFC e LCOM.
     *
     * @param cu A unidade de compilação do arquivo Java.
     * @return Um mapa com os dados extraídos, incluindo dependências e informações de métodos.
     */
    public static Map<String, Object> parseClassData(CompilationUnit cu) {
        Map<String, Object> result = new HashMap<>();
        Set<String> dependencies = new HashSet<>();
        Map<String, Set<String>> methodFieldAccess = new HashMap<>();
        Set<String> methodCalls = new HashSet<>();

        cu.findAll(ClassOrInterfaceDeclaration.class).forEach(c -> {
            // 1. Dependências de Herança e Interface
            c.getExtendedTypes().forEach(t -> dependencies.add(t.getNameAsString()));
            c.getImplementedTypes().forEach(t -> dependencies.add(t.getNameAsString()));

            // 2. Dependências de Composição/Agregação (atributos)
            c.findAll(FieldDeclaration.class).forEach(f -> {
                f.getElementType().ifClassOrInterfaceType(t -> dependencies.add(t.getNameAsString()));
            });

            // 3. Dependências de Uso de Métodos e Informações para LCOM/RFC
            c.findAll(MethodDeclaration.class).forEach(m -> {
                Set<String> accessedFields = new HashSet<>();
                // Coleta campos acessados para LCOM
                m.findAll(FieldAccessExpr.class).forEach(f -> accessedFields.add(f.getNameAsString()));
                methodFieldAccess.put(m.getNameAsString(), accessedFields);

                // Coleta chamadas de método para RFC
                m.findAll(MethodCallExpr.class).forEach(call -> {
                    // Adiciona o nome do método chamado, independentemente do objeto
                    methodCalls.add(call.getNameAsString());
                });

                // Tipos de retorno e parâmetros para acoplamento
                m.getParameters().forEach(p -> {
                    p.getType().ifClassOrInterfaceType(t -> dependencies.add(t.getNameAsString()));
                });
                m.getType().ifClassOrInterfaceType(t -> dependencies.add(t.getNameAsString()));
                m.findAll(ObjectCreationExpr.class).forEach(e -> dependencies.add(e.getType().getNameAsString()));
            });
        });

        result.put("dependencies", dependencies);
        result.put("methodFieldAccess", methodFieldAccess);
        result.put("methodCalls", methodCalls);
        return result;
    }
}
