import argparse
import os
import sys
from collections import defaultdict
from pydriller import Repository

# Implementação alternativa com GitPython (mais rápida)
try:
    import git

    GITPYTHON_AVAILABLE = True
except ImportError:
    GITPYTHON_AVAILABLE = False


def find_co_changes_fast(repo_path, max_commits=1000, verbose=False):
    """
    Versão otimizada usando GitPython diretamente.
    Muito mais rápido que PyDriller para grandes repositórios.

    Args:
        repo_path: Caminho para o repositório Git
        max_commits: Número máximo de commits a processar
        verbose: Mostrar progresso

    Returns:
        Dict com pares de arquivos e contagem de co-mudanças
    """
    if not GITPYTHON_AVAILABLE:
        if verbose:
            print("   GitPython não disponível, usando PyDriller")
        return find_co_changes(repo_path, max_commits, verbose)

    co_changes = defaultdict(int)

    try:
        repo = git.Repo(repo_path)
    except Exception as e:
        if verbose:
            print(f"  Erro ao abrir repositório com GitPython: {e}")
            print("  Tentando com PyDriller...")
        return find_co_changes(repo_path, max_commits, verbose)

    if verbose:
        print(f"  Analisando últimos {max_commits} commits com GitPython...")

    commit_count = 0

    # Iterar sobre commits
    for commit in repo.iter_commits("HEAD", max_count=max_commits):
        commit_count += 1

        if verbose and commit_count % 100 == 0:
            print(f"  Processados {commit_count} commits...")

        # Obter arquivos Java modificados neste commit
        modified_java_files = []

        try:
            # Comparar com o parent (se existir)
            if commit.parents:
                diffs = commit.parents[0].diff(commit)

                for diff in diffs:
                    # Pegar o caminho do arquivo (novo ou antigo)
                    file_path = diff.b_path if diff.b_path else diff.a_path

                    if file_path and file_path.endswith(".java"):
                        filename = os.path.basename(file_path)
                        modified_java_files.append(filename)
        except Exception:
            # Ignorar commits problemáticos
            continue

        # Criar pares de co-mudança
        if len(modified_java_files) > 1:
            for i in range(len(modified_java_files)):
                for j in range(i + 1, len(modified_java_files)):
                    file1 = modified_java_files[i]
                    file2 = modified_java_files[j]

                    # Ordem consistente
                    if file1 > file2:
                        file1, file2 = file2, file1

                    co_changes[(file1, file2)] += 1

    if verbose:
        print(
            f"  Analisados {commit_count} commits, encontrados {len(co_changes)} pares"
        )

    return co_changes


def find_co_changes(repo_path, max_commits=1000, verbose=False):
    """
    Mina um repositório Git para encontrar co-mudanças entre arquivos .java usando PyDriller.

    Args:
        repo_path (str): O caminho para o repositório Git.
        max_commits (int): Número máximo de commits a analisar (padrão: 1000)
        verbose (bool): Se True, mostra progresso

    Returns:
        defaultdict: Um dicionário com pares de arquivos e a contagem de co-mudanças.
    """
    co_changes = defaultdict(int)

    if verbose:
        print(f"  Analisando com PyDriller (até {max_commits} commits)...")

    # Itera sobre os commits do repositório (limitado para performance)
    commit_count = 0
    for commit in Repository(repo_path).traverse_commits():
        commit_count += 1

        # Limitar número de commits para não demorar muito
        if commit_count > max_commits:
            if verbose:
                print(f"   Limite de {max_commits} commits atingido")
            break

        # Mostrar progresso a cada 100 commits
        if verbose and commit_count % 100 == 0:
            print(f"  Processados {commit_count} commits...")

        modified_java_files = []
        for mod in commit.modified_files:
            if mod.filename.endswith(".java"):
                # Captura apenas o nome do arquivo para simplificar a análise.
                # Usar new_path se disponível, senão old_path (para arquivos deletados)
                file_path = mod.new_path if mod.new_path is not None else mod.old_path
                if file_path is not None:
                    modified_java_files.append(os.path.basename(file_path))

        # Cria pares de arquivos que foram modificados no mesmo commit.
        if len(modified_java_files) > 1:
            for i in range(len(modified_java_files)):
                for j in range(i + 1, len(modified_java_files)):
                    file1 = modified_java_files[i]
                    file2 = modified_java_files[j]

                    # Garante que a ordem dos arquivos no par seja consistente para a contagem.
                    if file1 > file2:
                        file1, file2 = file2, file1

                    co_changes[(file1, file2)] += 1

    if verbose:
        print(f"  Analisados {commit_count} commits")

    return co_changes


def save_co_changes_to_csv(co_changes_data, output_file="co_changes.csv"):
    """
    Salva os dados de co-mudança em um arquivo CSV.

    Args:
        co_changes_data: Dicionário com pares de classes e contagem
        output_file: Nome do arquivo de saída
    """
    import csv

    if not co_changes_data:
        return False

    sorted_co_changes = sorted(
        co_changes_data.items(), key=lambda item: item[1], reverse=True
    )

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Classe1", "Classe2", "FrequenciaCoMudanca"])
        for pair, count in sorted_co_changes:
            writer.writerow([pair[0], pair[1], count])

    return True


def extract_co_changes(repo_path, max_commits=1000, verbose=False, use_fast=False):
    """
    Função principal para extrair co-mudanças.

    Args:
        repo_path: Caminho para o repositório
        max_commits: Número máximo de commits
        verbose: Mostrar progresso
        use_fast: Se True, força o uso do GitPython; se False, usa PyDriller preferencialmente

    Returns:
        Dict com pares de arquivos e contagem
    """
    if use_fast and GITPYTHON_AVAILABLE:
        if verbose:
            print("Usando GitPython (modo rápido)")
        return find_co_changes_fast(repo_path, max_commits, verbose)
    else:
        if verbose:
            print("Usando PyDriller (modo padrão)")
        return find_co_changes(repo_path, max_commits, verbose)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Minera um repositório Git para encontrar co-mudanças entre arquivos .java."
    )
    parser.add_argument("repo_path", type=str, help="O caminho para o repositório Git.")
    parser.add_argument(
        "--max-commits", type=int, default=1000, help="Máximo de commits a processar"
    )
    parser.add_argument(
        "--output", default="co_changes.csv", help="Arquivo de saída CSV"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Usar GitPython (mais rápido) em vez de PyDriller",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Mostrar progresso detalhado"
    )

    args = parser.parse_args()

    if not os.path.isdir(os.path.join(args.repo_path, ".git")):
        print(f"O caminho '{args.repo_path}' não parece ser um repositório Git.")
        sys.exit(1)

    print(f"Iniciando mineração do repositório: {args.repo_path}")

    # Decidir qual implementação usar
    if args.fast:
        print("Modo rápido solicitado (GitPython)")
        co_changes_data = extract_co_changes(
            args.repo_path, args.max_commits, args.verbose, use_fast=True
        )
    else:
        print("Usando PyDriller (padrão)")
        co_changes_data = extract_co_changes(
            args.repo_path, args.max_commits, args.verbose, use_fast=False
        )

    if not co_changes_data:
        print(" Nenhuma co-mudança encontrada.")
    else:
        print(f"\nEncontradas {len(co_changes_data)} pares de co-mudanças")

        # Salvar os dados em um arquivo CSV
        if save_co_changes_to_csv(co_changes_data, args.output):
            print(f"Dados salvos em: {args.output}")

            # Mostrar top 10
            print("\nTop 10 pares mais frequentes:")
            sorted_co_changes = sorted(
                co_changes_data.items(), key=lambda item: item[1], reverse=True
            )
            for i, (pair, count) in enumerate(sorted_co_changes[:10], 1):
                print(f"  {i:2d}. {pair[0]} <-> {pair[1]}: {count}x")
        else:
            print("Erro ao salvar CSV")
