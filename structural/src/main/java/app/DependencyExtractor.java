package app;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.type.ClassOrInterfaceType;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import org.apache.maven.model.Model;
import org.apache.maven.model.io.xpp3.MavenXpp3Reader;

import java.io.File;
import java.io.FileReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class DependencyExtractor {

    public static void main(String[] args) {
        if (args.length == 0) {
            System.err.println("Usage: java DependencyExtractor <path-to-project>");
            System.exit(1);
        }
        
        try {
            File projectDir = new File(args[0]);
            AnalysisResult result = analyzeProject(projectDir);
            
            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            System.out.println(gson.toJson(result));
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }

    public static AnalysisResult analyzeProject(File projectDir) throws Exception {
        // 1. Parse pom.xml to get project info
        File pomFile = new File(projectDir, "pom.xml");
        String projectName = projectDir.getName();
        String projectGroupId = null;
        
        if (pomFile.exists()) {
            try {
                MavenXpp3Reader reader = new MavenXpp3Reader();
                Model model = reader.read(new FileReader(pomFile));
                projectName = model.getName() != null ? model.getName() : model.getArtifactId();
                projectGroupId = model.getGroupId();
                if (projectGroupId == null && model.getParent() != null) {
                    projectGroupId = model.getParent().getGroupId();
                }
            } catch (Exception e) {
                System.err.println("Warning: Could not parse pom.xml: " + e.getMessage());
            }
        }

        // 2. Find all Java source files
        List<File> javaFiles = findJavaFiles(projectDir);
        
        // 3. Build map of all internal classes
        Map<String, ClassInfo> classMap = new HashMap<>();
        Set<String> internalPackages = new HashSet<>();
        
        for (File javaFile : javaFiles) {
            try {
                CompilationUnit cu = StaticJavaParser.parse(javaFile);
                
                // Get package name
                String packageName = cu.getPackageDeclaration()
                    .map(pd -> pd.getNameAsString())
                    .orElse("");
                
                if (!packageName.isEmpty()) {
                    internalPackages.add(packageName);
                }
                
                // Get all classes in file
                cu.findAll(ClassOrInterfaceDeclaration.class).forEach(cls -> {
                    String fullClassName = packageName.isEmpty() ? 
                        cls.getNameAsString() : 
                        packageName + "." + cls.getNameAsString();
                    
                    ClassInfo classInfo = new ClassInfo();
                    classInfo.className = fullClassName;
                    classInfo.simpleName = cls.getNameAsString();
                    classInfo.packageName = packageName;
                    classInfo.filePath = projectDir.toPath().relativize(javaFile.toPath()).toString();
                    classInfo.isInterface = cls.isInterface();
                    classInfo.isAbstract = cls.isAbstract();
                    
                    // Count methods
                    classInfo.methodCount = cls.getMethods().size();
                    
                    // Count fields
                    classInfo.fieldCount = (int) cls.getFields().stream().count();
                    
                    classMap.put(fullClassName, classInfo);
                });
            } catch (Exception e) {
                System.err.println("Warning: Could not parse " + javaFile.getName() + ": " + e.getMessage());
            }
        }

        // 4. Analyze dependencies between classes
        for (File javaFile : javaFiles) {
            try {
                CompilationUnit cu = StaticJavaParser.parse(javaFile);
                String packageName = cu.getPackageDeclaration()
                    .map(pd -> pd.getNameAsString())
                    .orElse("");
                
                cu.findAll(ClassOrInterfaceDeclaration.class).forEach(cls -> {
                    String fullClassName = packageName.isEmpty() ? 
                        cls.getNameAsString() : 
                        packageName + "." + cls.getNameAsString();
                    
                    ClassInfo classInfo = classMap.get(fullClassName);
                    if (classInfo == null) return;
                    
                    Set<String> dependencies = new HashSet<>();
                    
                    // 1. Dependencies from imports (only internal)
                    cu.getImports().forEach(imp -> {
                        String importName = imp.getNameAsString();
                        if (classMap.containsKey(importName)) {
                            dependencies.add(importName);
                        }
                    });
                    
                    // 2. Dependencies from extends/implements
                    cls.getExtendedTypes().forEach(ext -> {
                        String typeName = resolveType(ext.getNameAsString(), packageName, cu, classMap);
                        if (typeName != null && classMap.containsKey(typeName)) {
                            dependencies.add(typeName);
                        }
                    });
                    
                    cls.getImplementedTypes().forEach(impl -> {
                        String typeName = resolveType(impl.getNameAsString(), packageName, cu, classMap);
                        if (typeName != null && classMap.containsKey(typeName)) {
                            dependencies.add(typeName);
                        }
                    });
                    
                    // 3. Dependencies from field types
                    cls.getFields().forEach(field -> {
                        String typeName = field.getCommonType().asString();
                        String resolvedType = resolveType(typeName, packageName, cu, classMap);
                        if (resolvedType != null && classMap.containsKey(resolvedType)) {
                            dependencies.add(resolvedType);
                        }
                    });
                    
                    // 4. Dependencies from method parameters and return types
                    cls.getMethods().forEach(method -> {
                        // Return type
                        String returnType = method.getType().asString();
                        String resolvedReturn = resolveType(returnType, packageName, cu, classMap);
                        if (resolvedReturn != null && classMap.containsKey(resolvedReturn)) {
                            dependencies.add(resolvedReturn);
                        }
                        
                        // Parameters
                        method.getParameters().forEach(param -> {
                            String paramType = param.getType().asString();
                            String resolvedParam = resolveType(paramType, packageName, cu, classMap);
                            if (resolvedParam != null && classMap.containsKey(resolvedParam)) {
                                dependencies.add(resolvedParam);
                            }
                        });
                    });
                    
                    classInfo.dependsOn = new ArrayList<>(dependencies);
                    classInfo.couplingOut = dependencies.size();
                });
            } catch (Exception e) {
                System.err.println("Warning: Could not analyze dependencies for " + javaFile.getName());
            }
        }

        // 5. Calculate incoming dependencies (CBO in)
        for (ClassInfo classInfo : classMap.values()) {
            for (String dependency : classInfo.dependsOn) {
                ClassInfo depClass = classMap.get(dependency);
                if (depClass != null) {
                    depClass.dependedByClasses.add(classInfo.className);
                    depClass.couplingIn++;
                }
            }
        }

        // 6. Sort classes by coupling
        List<ClassInfo> classList = new ArrayList<>(classMap.values());
        classList.sort((a, b) -> Integer.compare(b.getTotalCoupling(), a.getTotalCoupling()));

        AnalysisResult result = new AnalysisResult();
        result.projectName = projectName;
        result.projectPath = projectDir.getAbsolutePath();
        result.projectGroupId = projectGroupId;
        result.totalClasses = classList.size();
        result.classes = classList;
        
        // Calculate summary metrics
        int totalCoupling = classList.stream().mapToInt(ClassInfo::getTotalCoupling).sum();
        result.averageCoupling = classList.isEmpty() ? 0 : (double) totalCoupling / classList.size();
        result.maxCoupling = classList.stream().mapToInt(ClassInfo::getTotalCoupling).max().orElse(0);
        
        // Identify highly coupled classes (top 20%)
        int threshold = (int) Math.ceil(classList.size() * 0.2);
        result.highlyCoupledClasses = (int) classList.stream()
            .limit(threshold)
            .filter(c -> c.getTotalCoupling() > 0)
            .count();

        return result;
    }

    private static List<File> findJavaFiles(File dir) throws Exception {
        try (Stream<Path> paths = Files.walk(dir.toPath())) {
            return paths
                .filter(Files::isRegularFile)
                .filter(p -> p.toString().endsWith(".java"))
                .filter(p -> !p.toString().contains("/test/")) // Exclude test files
                .filter(p -> !p.toString().contains("/target/")) // Exclude compiled files
                .map(Path::toFile)
                .collect(Collectors.toList());
        }
    }

    /**
     * Resolve a simple type name to its fully qualified name.
     */
    private static String resolveType(String typeName, String currentPackage, 
                                     CompilationUnit cu, Map<String, ClassInfo> classMap) {
        // Remove generics
        typeName = typeName.replaceAll("<.*>", "").trim();
        
        // Remove array brackets
        typeName = typeName.replace("[]", "").trim();
        
        // Skip primitives and common Java types
        if (isPrimitive(typeName) || typeName.startsWith("java.") || typeName.startsWith("javax.")) {
            return null;
        }
        
        // Already fully qualified?
        if (classMap.containsKey(typeName)) {
            return typeName;
        }
        
        // Try with current package
        String withPackage = currentPackage.isEmpty() ? typeName : currentPackage + "." + typeName;
        if (classMap.containsKey(withPackage)) {
            return withPackage;
        }
        
        // Check imports
        for (ImportDeclaration imp : cu.getImports()) {
            String importName = imp.getNameAsString();
            if (importName.endsWith("." + typeName)) {
                if (classMap.containsKey(importName)) {
                    return importName;
                }
            }
        }
        
        return null;
    }

    private static boolean isPrimitive(String type) {
        return type.equals("int") || type.equals("long") || type.equals("double") || 
               type.equals("float") || type.equals("boolean") || type.equals("char") || 
               type.equals("byte") || type.equals("short") || type.equals("void") ||
               type.equals("String") || type.equals("Object");
    }

    public static class AnalysisResult {
        public String projectName;
        public String projectPath;
        public String projectGroupId;
        public int totalClasses;
        public double averageCoupling;
        public int maxCoupling;
        public int highlyCoupledClasses;
        public List<ClassInfo> classes;
    }

    public static class ClassInfo {
        public String className;
        public String simpleName;
        public String packageName;
        public String filePath;
        public boolean isInterface;
        public boolean isAbstract;
        public int methodCount;
        public int fieldCount;
        
        // Coupling metrics
        public List<String> dependsOn = new ArrayList<>();
        public List<String> dependedByClasses = new ArrayList<>();
        public int couplingOut = 0; // Efferent coupling (CBO out)
        public int couplingIn = 0;  // Afferent coupling (CBO in)
        
        public int getTotalCoupling() {
            return couplingOut + couplingIn;
        }
        
        public double getInstability() {
            int total = couplingOut + couplingIn;
            return total == 0 ? 0 : (double) couplingOut / total;
        }
    }
}
