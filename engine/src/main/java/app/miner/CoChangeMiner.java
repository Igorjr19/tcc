package app.miner;

import app.model.EdgeInfo;
import app.model.NodeInfo;
import app.model.RelationType;

import org.eclipse.jgit.api.Git;
import org.eclipse.jgit.diff.DiffEntry;
import org.eclipse.jgit.diff.DiffFormatter;
import org.eclipse.jgit.lib.ObjectReader;
import org.eclipse.jgit.lib.Repository;
import org.eclipse.jgit.revwalk.RevCommit;
import org.eclipse.jgit.revwalk.RevWalk;
import org.eclipse.jgit.treewalk.AbstractTreeIterator;
import org.eclipse.jgit.treewalk.CanonicalTreeParser;
import org.eclipse.jgit.treewalk.EmptyTreeIterator;
import org.eclipse.jgit.util.io.DisabledOutputStream;

import java.io.File;
import java.io.IOException;
import java.util.*;

/**
 * Minerador de co-changes via histórico Git (JGit).
 *
 * <p>Algoritmo:
 * <ol>
 *   <li>Localiza o diretório .git (caminhando para cima a partir do projectDir).</li>
 *   <li>Itera todos os commits acessíveis a partir de HEAD.</li>
 *   <li>Para cada commit, obtém a lista de arquivos .java modificados.</li>
 *   <li>Ignora commits com mais de {@code maxFilesPerCommit} arquivos (merge commits / refactorings em massa).</li>
 *   <li>Conta co-ocorrências de pares de arquivos e commits individuais por arquivo.</li>
 *   <li>Gera arestas CO_CHANGE com peso = coChangeCount / max(commitsA, commitsB),
 *       filtrando pares com menos de {@code minCoChanges} co-ocorrências.</li>
 * </ol>
 */
public class CoChangeMiner {

    private static final int DEFAULT_MAX_FILES_PER_COMMIT = 30;
    private static final int DEFAULT_MIN_CO_CHANGES = 3;

    private final int maxFilesPerCommit;
    private final int minCoChanges;

    public CoChangeMiner() {
        this(DEFAULT_MAX_FILES_PER_COMMIT, DEFAULT_MIN_CO_CHANGES);
    }

    public CoChangeMiner(int maxFilesPerCommit, int minCoChanges) {
        this.maxFilesPerCommit = maxFilesPerCommit;
        this.minCoChanges = minCoChanges;
    }

    /**
     * Minera co-changes do repositório Git que contém {@code projectDir}.
     *
     * @param projectDir diretório do projeto analisado
     * @param nodeMap    mapa FQN → NodeInfo (com filePath relativo ao projectDir)
     * @return lista de arestas CO_CHANGE
     */
    public List<EdgeInfo> mine(File projectDir, Map<String, NodeInfo> nodeMap) {
        File gitDir = findGitDir(projectDir);
        if (gitDir == null) {
            System.err.println("CoChangeMiner: diretório .git não encontrado. Pulando mineração de co-changes.");
            return Collections.emptyList();
        }

        try (Git git = Git.open(gitDir.getParentFile());
             Repository repo = git.getRepository()) {
            return mineFromRepository(repo, projectDir, gitDir.getParentFile(), nodeMap);
        } catch (Exception e) {
            System.err.println("CoChangeMiner: erro ao minerar co-changes: " + e.getMessage());
            return Collections.emptyList();
        }
    }

    private List<EdgeInfo> mineFromRepository(Repository repo, File projectDir,
                                               File repoRoot, Map<String, NodeInfo> nodeMap) throws IOException {
        // Mapeia caminhos relativos (ao repo root) → FQN usando o filePath do NodeInfo
        Map<String, String> pathToFqn = buildPathToFqnMap(repoRoot, projectDir, nodeMap);
        if (pathToFqn.isEmpty()) {
            System.err.println("CoChangeMiner: nenhum mapeamento path→FQN encontrado.");
            return Collections.emptyList();
        }

        // Contadores
        Map<String, Map<String, Integer>> coChangeCount = new HashMap<>();
        Map<String, Integer> commitCount = new HashMap<>();

        int totalCommits = 0;
        int skippedCommits = 0;

        try (RevWalk revWalk = new RevWalk(repo)) {
            revWalk.markStart(revWalk.parseCommit(repo.resolve("HEAD")));

            for (RevCommit commit : revWalk) {
                totalCommits++;

                if (totalCommits % 1000 == 0) {
                    System.err.println("CoChangeMiner: processados " + totalCommits + " commits...");
                }

                List<String> modifiedFqns = getModifiedFqns(repo, commit, pathToFqn);

                if (modifiedFqns.size() > maxFilesPerCommit) {
                    skippedCommits++;
                    continue;
                }

                if (modifiedFqns.size() < 2) {
                    // Ainda conta commits individuais
                    for (String fqn : modifiedFqns) {
                        commitCount.merge(fqn, 1, Integer::sum);
                    }
                    continue;
                }

                // Conta commits individuais
                for (String fqn : modifiedFqns) {
                    commitCount.merge(fqn, 1, Integer::sum);
                }

                // Conta co-changes para todos os pares
                Collections.sort(modifiedFqns);
                for (int i = 0; i < modifiedFqns.size(); i++) {
                    for (int j = i + 1; j < modifiedFqns.size(); j++) {
                        String a = modifiedFqns.get(i);
                        String b = modifiedFqns.get(j);
                        coChangeCount
                                .computeIfAbsent(a, k -> new HashMap<>())
                                .merge(b, 1, Integer::sum);
                    }
                }
            }
        }

        System.err.println("CoChangeMiner: " + totalCommits + " commits processados ("
                + skippedCommits + " ignorados por exceder " + maxFilesPerCommit + " arquivos).");

        // Gera arestas
        List<EdgeInfo> edges = new ArrayList<>();
        for (Map.Entry<String, Map<String, Integer>> outer : coChangeCount.entrySet()) {
            String a = outer.getKey();
            for (Map.Entry<String, Integer> inner : outer.getValue().entrySet()) {
                String b = inner.getKey();
                int count = inner.getValue();

                if (count < minCoChanges) continue;

                int commitsA = commitCount.getOrDefault(a, 1);
                int commitsB = commitCount.getOrDefault(b, 1);
                double weight = (double) count / Math.max(commitsA, commitsB);

                edges.add(new EdgeInfo(a, b, RelationType.CO_CHANGE, weight, count,
                        Math.max(commitsA, commitsB)));
            }
        }

        System.err.println("CoChangeMiner: " + edges.size() + " relações CO_CHANGE geradas.");
        return edges;
    }

    /**
     * Obtém os FQNs dos arquivos .java modificados em um commit.
     */
    private List<String> getModifiedFqns(Repository repo, RevCommit commit,
                                          Map<String, String> pathToFqn) throws IOException {
        List<String> fqns = new ArrayList<>();

        try (DiffFormatter df = new DiffFormatter(DisabledOutputStream.INSTANCE);
             ObjectReader reader = repo.newObjectReader()) {
            df.setRepository(repo);
            df.setDetectRenames(true);

            AbstractTreeIterator parentIterator;
            if (commit.getParentCount() > 0) {
                RevCommit parent = commit.getParent(0);
                try (RevWalk rw = new RevWalk(repo)) {
                    parent = rw.parseCommit(parent.getId());
                }
                CanonicalTreeParser parser = new CanonicalTreeParser();
                parser.reset(reader, parent.getTree().getId());
                parentIterator = parser;
            } else {
                parentIterator = new EmptyTreeIterator();
            }

            CanonicalTreeParser commitIterator = new CanonicalTreeParser();
            commitIterator.reset(reader, commit.getTree().getId());

            List<DiffEntry> diffs = df.scan(parentIterator, commitIterator);

            Set<String> seen = new HashSet<>();
            for (DiffEntry diff : diffs) {
                String path = diff.getChangeType() == DiffEntry.ChangeType.DELETE
                        ? diff.getOldPath() : diff.getNewPath();

                if (path.endsWith(".java")) {
                    String fqn = pathToFqn.get(path);
                    if (fqn != null && seen.add(fqn)) {
                        fqns.add(fqn);
                    }
                }
            }
        }

        return fqns;
    }

    /**
     * Constrói um mapa de caminhos relativos (ao repo root) → FQN usando o
     * filePath já conhecido de cada NodeInfo (que é relativo ao projectDir).
     */
    private Map<String, String> buildPathToFqnMap(File repoRoot, File projectDir,
                                                   Map<String, NodeInfo> nodeMap) {
        Map<String, String> pathToFqn = new HashMap<>();
        String projectRelPath = repoRoot.toPath().relativize(projectDir.toPath()).toString();

        for (Map.Entry<String, NodeInfo> entry : nodeMap.entrySet()) {
            String fqn = entry.getKey();
            String filePath = entry.getValue().getFilePath();
            if (filePath == null) continue;

            // filePath é relativo ao projectDir; precisamos do caminho relativo ao repoRoot
            String repoRelPath;
            if (projectRelPath.isEmpty()) {
                repoRelPath = filePath;
            } else {
                repoRelPath = projectRelPath + "/" + filePath;
            }

            // Normaliza separadores para o formato do Git (sempre /)
            pathToFqn.put(repoRelPath.replace('\\', '/'), fqn);
        }

        System.err.println("CoChangeMiner: " + pathToFqn.size() + " de " + nodeMap.size()
                + " FQNs mapeados para caminhos Git.");
        return pathToFqn;
    }

    /**
     * Procura o diretório .git caminhando para cima a partir do diretório do projeto.
     */
    private File findGitDir(File dir) {
        File current = dir.getAbsoluteFile();
        while (current != null) {
            File gitDir = new File(current, ".git");
            if (gitDir.exists() && gitDir.isDirectory()) {
                return gitDir;
            }
            current = current.getParentFile();
        }
        return null;
    }
}
