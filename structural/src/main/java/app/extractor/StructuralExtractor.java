package app.extractor;

import app.model.EdgeInfo;
import app.model.NodeInfo;
import app.model.RelationType;

import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.expr.*;
import com.github.javaparser.ast.stmt.ExplicitConstructorInvocationStmt;
import com.github.javaparser.ast.type.ClassOrInterfaceType;
import com.github.javaparser.ast.type.Type;
import com.github.javaparser.resolution.types.ResolvedType;

import java.util.*;

/**
 * Extrai relações estruturais e comportamentais entre classes a partir da AST.
 *
 * <p>Relações detectadas:
 * <ul>
 *   <li>INHERITANCE — extends</li>
 *   <li>INTERFACE_IMPLEMENTATION — implements</li>
 *   <li>COMPOSITION — campo cujo tipo é instanciado internamente (new)</li>
 *   <li>AGGREGATION — campo cujo tipo é recebido via construtor ou setter</li>
 *   <li>ASSOCIATION — parâmetro, retorno ou variável local de outro tipo interno</li>
 *   <li>METHOD_CALL — invocação de método de outra classe</li>
 *   <li>ATTRIBUTE_ACCESS — acesso direto a atributo público de outra classe</li>
 *   <li>TYPE_REFERENCE — casts, instanceof, genéricos</li>
 * </ul>
 */
public class StructuralExtractor {

    private final Map<String, NodeInfo> nodeMap;

    public StructuralExtractor(Map<String, NodeInfo> nodeMap) {
        this.nodeMap = nodeMap;
    }

    /**
     * Extrai todas as relações de uma classe declarada em uma CompilationUnit.
     *
     * @param classFQN Fully qualified name da classe analisada.
     * @param cls      Declaração da classe na AST.
     * @param cu       Unidade de compilação que contém a classe.
     * @return Lista de arestas representando as relações detectadas.
     */
    public List<EdgeInfo> extractFromClass(String classFQN, TypeDeclaration<?> cls, CompilationUnit cu) {
        List<EdgeInfo> edges = new ArrayList<>();
        String currentPackage = cu.getPackageDeclaration()
                .map(pd -> pd.getNameAsString()).orElse("");

        if (cls instanceof ClassOrInterfaceDeclaration cid) {
            extractInheritance(classFQN, cid, currentPackage, cu, edges);
            extractInterfaceImpl(classFQN, cid, currentPackage, cu, edges);
        } else if (cls instanceof EnumDeclaration ed) {
            extractEnumImpl(classFQN, ed, currentPackage, cu, edges);
        } else if (cls instanceof RecordDeclaration rd) {
            extractRecordImpl(classFQN, rd, currentPackage, cu, edges);
        }

        Set<String> fieldDependencies = extractFieldRelationships(classFQN, cls, currentPackage, cu, edges);
        extractAssociations(classFQN, cls, currentPackage, cu, edges, fieldDependencies);
        extractMethodCalls(classFQN, cls, currentPackage, cu, edges);
        extractAttributeAccess(classFQN, cls, currentPackage, cu, edges);
        extractTypeReferences(classFQN, cls, currentPackage, cu, edges);

        return edges;
    }

    // ---- Herança ----

    private void extractInheritance(String classFQN, ClassOrInterfaceDeclaration cls,
                                    String pkg, CompilationUnit cu, List<EdgeInfo> edges) {
        for (ClassOrInterfaceType ext : cls.getExtendedTypes()) {
            String target = resolveToInternal(ext.getNameAsString(), pkg, cu);
            if (target != null && !target.equals(classFQN)) {
                edges.add(new EdgeInfo(classFQN, target, RelationType.INHERITANCE, 1.0));
            }
        }
    }

    private void extractInterfaceImpl(String classFQN, ClassOrInterfaceDeclaration cls,
                                      String pkg, CompilationUnit cu, List<EdgeInfo> edges) {
        for (ClassOrInterfaceType impl : cls.getImplementedTypes()) {
            String target = resolveToInternal(impl.getNameAsString(), pkg, cu);
            if (target != null && !target.equals(classFQN)) {
                edges.add(new EdgeInfo(classFQN, target, RelationType.INTERFACE_IMPLEMENTATION, 1.0));
            }
        }
    }

    private void extractEnumImpl(String classFQN, EnumDeclaration cls,
                                 String pkg, CompilationUnit cu, List<EdgeInfo> edges) {
        for (ClassOrInterfaceType impl : cls.getImplementedTypes()) {
            String target = resolveToInternal(impl.getNameAsString(), pkg, cu);
            if (target != null && !target.equals(classFQN)) {
                edges.add(new EdgeInfo(classFQN, target, RelationType.INTERFACE_IMPLEMENTATION, 1.0));
            }
        }
    }

    private void extractRecordImpl(String classFQN, RecordDeclaration cls,
                                   String pkg, CompilationUnit cu, List<EdgeInfo> edges) {
        for (ClassOrInterfaceType impl : cls.getImplementedTypes()) {
            String target = resolveToInternal(impl.getNameAsString(), pkg, cu);
            if (target != null && !target.equals(classFQN)) {
                edges.add(new EdgeInfo(classFQN, target, RelationType.INTERFACE_IMPLEMENTATION, 1.0));
            }
        }
    }

    // ---- Composição / Agregação (campos) ----

    /**
     * Analisa os campos da classe e classifica as dependências como
     * COMPOSITION (instanciado internamente) ou AGGREGATION (recebido externamente).
     *
     * @return Conjunto de FQNs que foram classificados como dependências de campo,
     *         para exclusão na extração de ASSOCIATION.
     */
    private Set<String> extractFieldRelationships(String classFQN, TypeDeclaration<?> cls,
                                                  String pkg, CompilationUnit cu, List<EdgeInfo> edges) {
        // Mapeia FQN do tipo do campo → se existe
        Map<String, String> fieldTypeFQNs = new LinkedHashMap<>();
        for (FieldDeclaration field : cls.getFields()) {
            for (String fqn : resolveAllFromType(field.getCommonType(), pkg, cu)) {
                fieldTypeFQNs.put(fqn, fqn);
            }
        }

        // Tipos instanciados com new dentro da classe
        Set<String> instantiated = new HashSet<>();
        cls.findAll(ObjectCreationExpr.class).forEach(expr -> {
            String fqn = resolveToInternal(expr.getType().getNameAsString(), pkg, cu);
            if (fqn != null) instantiated.add(fqn);
        });

        // Tipos recebidos via construtor
        Set<String> constructorParams = new HashSet<>();
        cls.findAll(ConstructorDeclaration.class).forEach(ctor ->
            ctor.getParameters().forEach(param -> {
                for (String fqn : resolveAllFromType(param.getType(), pkg, cu)) {
                    constructorParams.add(fqn);
                }
            })
        );

        // Tipos recebidos via setters (setXxx com 1 parâmetro)
        Set<String> setterParams = new HashSet<>();
        cls.findAll(MethodDeclaration.class).stream()
                .filter(m -> m.getNameAsString().startsWith("set") && m.getParameters().size() == 1)
                .forEach(m -> {
                    for (String fqn : resolveAllFromType(m.getParameter(0).getType(), pkg, cu)) {
                        setterParams.add(fqn);
                    }
                });

        Set<String> fieldDeps = new HashSet<>();
        for (String fqn : fieldTypeFQNs.keySet()) {
            if (fqn.equals(classFQN)) continue;
            fieldDeps.add(fqn);

            if (instantiated.contains(fqn)) {
                edges.add(new EdgeInfo(classFQN, fqn, RelationType.COMPOSITION, 1.0));
            } else if (constructorParams.contains(fqn) || setterParams.contains(fqn)) {
                edges.add(new EdgeInfo(classFQN, fqn, RelationType.AGGREGATION, 1.0));
            } else {
                // Campo cujo tipo é interno mas não é claramente composição nem agregação:
                // classifica como associação (referência de campo)
                edges.add(new EdgeInfo(classFQN, fqn, RelationType.ASSOCIATION, 1.0));
            }
        }
        return fieldDeps;
    }

    // ---- Associação (parâmetros, retornos, variáveis locais) ----

    private void extractAssociations(String classFQN, TypeDeclaration<?> cls,
                                     String pkg, CompilationUnit cu, List<EdgeInfo> edges,
                                     Set<String> fieldDeps) {
        Set<String> associations = new HashSet<>();

        for (MethodDeclaration method : cls.getMethods()) {
            // Tipo de retorno
            for (String fqn : resolveAllFromType(method.getType(), pkg, cu)) {
                associations.add(fqn);
            }
            // Parâmetros
            method.getParameters().forEach(param -> {
                for (String fqn : resolveAllFromType(param.getType(), pkg, cu)) {
                    associations.add(fqn);
                }
            });
            // Variáveis locais
            method.findAll(VariableDeclarator.class).forEach(v -> {
                for (String fqn : resolveAllFromType(v.getType(), pkg, cu)) {
                    associations.add(fqn);
                }
            });
        }

        // Também inclui parâmetros de construtores (que não estejam em fieldDeps)
        cls.findAll(ConstructorDeclaration.class).forEach(ctor ->
            ctor.getParameters().forEach(param -> {
                for (String fqn : resolveAllFromType(param.getType(), pkg, cu)) {
                    associations.add(fqn);
                }
            })
        );

        associations.remove(classFQN);
        associations.removeAll(fieldDeps);

        for (String fqn : associations) {
            edges.add(new EdgeInfo(classFQN, fqn, RelationType.ASSOCIATION, 1.0));
        }
    }

    // ---- Chamadas de método ----

    private void extractMethodCalls(String classFQN, TypeDeclaration<?> cls,
                                    String pkg, CompilationUnit cu, List<EdgeInfo> edges) {
        Set<String> targets = new HashSet<>();

        cls.findAll(MethodCallExpr.class).forEach(call -> {
            if (call.getScope().isEmpty()) return;
            Expression scope = call.getScope().get();

            // Tenta resolução via SymbolSolver
            String resolved = tryResolveExpression(scope);
            if (resolved != null && nodeMap.containsKey(resolved) && !resolved.equals(classFQN)) {
                targets.add(resolved);
                return;
            }

            // Fallback: se o scope é um NameExpr, busca o tipo da variável/campo
            if (scope.isNameExpr()) {
                String varType = findVariableType(scope.asNameExpr().getNameAsString(), cls, pkg, cu);
                if (varType != null && !varType.equals(classFQN)) {
                    targets.add(varType);
                }
            }
        });

        for (String t : targets) {
            edges.add(new EdgeInfo(classFQN, t, RelationType.METHOD_CALL, 1.0));
        }
    }

    // ---- Acesso a atributos ----

    private void extractAttributeAccess(String classFQN, TypeDeclaration<?> cls,
                                        String pkg, CompilationUnit cu, List<EdgeInfo> edges) {
        Set<String> targets = new HashSet<>();

        cls.findAll(FieldAccessExpr.class).forEach(fa -> {
            Expression scope = fa.getScope();
            if (scope.isThisExpr()) return; // Acesso ao próprio campo, ignorar

            String resolved = tryResolveExpression(scope);
            if (resolved != null && nodeMap.containsKey(resolved) && !resolved.equals(classFQN)) {
                targets.add(resolved);
                return;
            }

            if (scope.isNameExpr()) {
                String varType = findVariableType(scope.asNameExpr().getNameAsString(), cls, pkg, cu);
                if (varType != null && !varType.equals(classFQN)) {
                    targets.add(varType);
                }
            }
        });

        for (String t : targets) {
            edges.add(new EdgeInfo(classFQN, t, RelationType.ATTRIBUTE_ACCESS, 1.0));
        }
    }

    // ---- Referências de tipo (casts, instanceof, genéricos) ----

    private void extractTypeReferences(String classFQN, TypeDeclaration<?> cls,
                                       String pkg, CompilationUnit cu, List<EdgeInfo> edges) {
        Set<String> refs = new HashSet<>();

        // Casts
        cls.findAll(CastExpr.class).forEach(cast -> {
            for (String fqn : resolveAllFromType(cast.getType(), pkg, cu)) {
                refs.add(fqn);
            }
        });

        // instanceof
        cls.findAll(InstanceOfExpr.class).forEach(iof -> {
            for (String fqn : resolveAllFromType(iof.getType(), pkg, cu)) {
                refs.add(fqn);
            }
        });

        // Argumentos genéricos em todos os ClassOrInterfaceType
        cls.findAll(ClassOrInterfaceType.class).forEach(cit ->
            cit.getTypeArguments().ifPresent(args -> {
                for (Type arg : args) {
                    for (String fqn : resolveAllFromType(arg, pkg, cu)) {
                        refs.add(fqn);
                    }
                }
            })
        );

        refs.remove(classFQN);
        for (String fqn : refs) {
            edges.add(new EdgeInfo(classFQN, fqn, RelationType.TYPE_REFERENCE, 1.0));
        }
    }

    // ---- Resolução de tipos ----

    /**
     * Resolve um nome de tipo simples para o FQN correspondente,
     * retornando null se não for uma classe interna do projeto.
     */
    String resolveToInternal(String typeName, String currentPackage, CompilationUnit cu) {
        if (typeName == null) return null;
        typeName = typeName.replaceAll("<.*>", "").replace("[]", "").trim();

        if (isPrimitive(typeName)) return null;

        // Já é FQN?
        if (nodeMap.containsKey(typeName)) return typeName;

        // Mesmo pacote?
        if (!currentPackage.isEmpty()) {
            String withPkg = currentPackage + "." + typeName;
            if (nodeMap.containsKey(withPkg)) return withPkg;
        }

        // Imports explícitos
        for (ImportDeclaration imp : cu.getImports()) {
            String importName = imp.getNameAsString();
            if (!imp.isAsterisk() && importName.endsWith("." + typeName)) {
                if (nodeMap.containsKey(importName)) return importName;
            }
            if (imp.isAsterisk()) {
                String candidate = importName + "." + typeName;
                if (nodeMap.containsKey(candidate)) return candidate;
            }
        }

        return null;
    }

    /**
     * Resolve um Type da AST para todos os FQNs internos referenciados
     * (incluindo argumentos genéricos, componentes de array).
     */
    private Set<String> resolveAllFromType(Type type, String pkg, CompilationUnit cu) {
        Set<String> result = new HashSet<>();
        if (type == null || type.isPrimitiveType() || type.isVoidType()) return result;

        if (type.isArrayType()) {
            return resolveAllFromType(type.asArrayType().getComponentType(), pkg, cu);
        }

        if (type.isClassOrInterfaceType()) {
            ClassOrInterfaceType cit = type.asClassOrInterfaceType();
            String resolved = resolveToInternal(cit.getNameAsString(), pkg, cu);
            if (resolved != null) result.add(resolved);
        }

        return result;
    }

    /**
     * Tenta resolver uma expressão para o FQN do seu tipo usando o SymbolSolver.
     */
    private String tryResolveExpression(Expression expr) {
        try {
            ResolvedType type = expr.calculateResolvedType();
            if (type.isReferenceType()) {
                return type.asReferenceType().getQualifiedName();
            }
        } catch (Exception e) {
            // SymbolSolver não conseguiu resolver — fallback manual
        }
        return null;
    }

    /**
     * Busca o tipo de uma variável (campo ou parâmetro) pelo nome, resolvendo para FQN interno.
     */
    private String findVariableType(String varName, TypeDeclaration<?> cls,
                                    String pkg, CompilationUnit cu) {
        // Busca em campos
        for (FieldDeclaration field : cls.getFields()) {
            for (VariableDeclarator v : field.getVariables()) {
                if (v.getNameAsString().equals(varName)) {
                    String typeName = v.getType().asString().replaceAll("<.*>", "");
                    return resolveToInternal(typeName, pkg, cu);
                }
            }
        }
        return null;
    }

    private static boolean isPrimitive(String type) {
        return switch (type) {
            case "int", "long", "double", "float", "boolean", "char", "byte", "short", "void",
                 "String", "Object", "Integer", "Long", "Double", "Float", "Boolean", "Character",
                 "Byte", "Short", "Void", "Number" -> true;
            default -> type.startsWith("java.") || type.startsWith("javax.");
        };
    }
}
