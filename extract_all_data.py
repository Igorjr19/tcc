#!/usr/bin/env python
"""
Script para executar análise completa em repositórios.
Extrai métricas estruturais e co-mudanças, separando dados de TREINO e TESTE.

Uso:
    python extract_all_data.py --mode train    # Apenas dados de treino
    python extract_all_data.py --mode test     # Apenas dados de teste
    python extract_all_data.py --mode all      # Todos os dados (padrão)
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Importar configuração centralizada
from data_integration import CO_CHANGES_DIR, DEPENDENCIES_DIR, METRICS_DIR
from repos_config import TRAIN_REPOS, TEST_REPOS, get_all_repos

# Diretório base do projeto
BASE_DIR = Path(__file__).parent.absolute()
REPOS_DIR = BASE_DIR / "data" / "repos"
DATA_DIR = BASE_DIR / "data"


def setup_directories():
    """Cria a estrutura de diretórios necessária."""
    print("Criando estrutura de diretórios...")
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    CO_CHANGES_DIR.mkdir(parents=True, exist_ok=True)
    DEPENDENCIES_DIR.mkdir(parents=True, exist_ok=True)
    print("Diretórios criados\n")


def find_maven_command():
    """Encontra o comando Maven disponível no sistema."""
    # Tentar mvn global
    try:
        subprocess.run(["mvn", "--version"], capture_output=True, check=True)
        return "mvn"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Tentar mvnw local
    structural_dir = BASE_DIR / "structural"
    mvnw = structural_dir / "mvnw"
    if mvnw.exists():
        return str(mvnw)

    return None


def extract_metrics(repo_name):
    """
    Extrai métricas estruturais usando o MetricExtractor Java.

    Args:
        repo_name: Nome do repositório
    """
    repo_path = REPOS_DIR / repo_name

    if not repo_path.exists():
        print(f" Repositório {repo_name} não encontrado em {repo_path}")
        return False

    print(f"Extraindo métricas estruturais de {repo_name}...")

    # Verificar se Maven está disponível
    maven_cmd = find_maven_command()
    if maven_cmd is None:
        print("   Maven não encontrado. Pulando extração de métricas.")
        return False

    # Compilar o projeto Java (se necessário)
    structural_dir = BASE_DIR / "structural"

    try:
        # Executar o MetricExtractor
        result = subprocess.run(
            [
                maven_cmd,
                "exec:java",
                "-Dexec.mainClass=app.MetricExtractor",
                f"-Dexec.args={repo_path}",
            ],
            cwd=structural_dir,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutos timeout
        )

        if result.returncode == 0:
            # Mover os CSVs gerados para o diretório apropriado
            metrics_file = structural_dir / "metrics.csv"
            dependencies_file = structural_dir / "dependencies.csv"

            if metrics_file.exists():
                metrics_file.rename(METRICS_DIR / f"{repo_name}_metrics.csv")
                print(f"  Métricas salvas em {repo_name}_metrics.csv")

            if dependencies_file.exists():
                dependencies_file.rename(
                    DEPENDENCIES_DIR / f"{repo_name}_dependencies.csv"
                )
                print(f"  Dependências salvas em {repo_name}_dependencies.csv")

            return True
        else:
            print(f"  Erro ao extrair métricas:")
            print(f"     {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print(f"  Timeout ao processar {repo_name}")
        return False
    except Exception as e:
        print(f"  Erro: {e}")
        return False


def extract_co_changes(repo_name):
    """
    Extrai co-mudanças usando o mining.py.

    Args:
        repo_name: Nome do repositório
    """
    repo_path = REPOS_DIR / repo_name

    if not repo_path.exists():
        print(f" Repositório {repo_name} não encontrado")
        return False

    print(f"Extraindo co-mudanças de {repo_name}...")

    try:
        # Importar as funções do mining.py
        sys.path.insert(0, str(BASE_DIR))
        from mining import extract_co_changes, save_co_changes_to_csv

        # Verificar se é um repositório Git válido
        if not (repo_path / ".git").exists():
            print(f"   {repo_name} não é um repositório Git válido")
            return False

        # Executar mineração (limitado a 500 commits para performance)
        # Usar GitPython (rápido) por padrão para extração em lote
        co_changes_data = extract_co_changes(
            str(repo_path), max_commits=500, verbose=True, use_fast=True
        )

        if not co_changes_data:
            print(f"   Nenhuma co-mudança encontrada em {repo_name}")
            return False

        # Salvar CSV
        output_file = CO_CHANGES_DIR / f"{repo_name}_co_changes.csv"
        if save_co_changes_to_csv(co_changes_data, str(output_file)):
            print(f"  Co-mudanças salvas em {repo_name}_co_changes.csv")
            return True
        else:
            print(f"   Erro ao salvar CSV")
            return False

    except Exception as e:
        print(f"  Erro: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Função principal."""
    # Parse argumentos
    parser = argparse.ArgumentParser(
        description="Extrair dados de repositórios (treino/teste)"
    )
    parser.add_argument(
        "--mode",
        choices=["train", "test", "all"],
        default="all",
        help="Modo de extração: train, test ou all (padrão: all)",
    )
    args = parser.parse_args()

    # Determinar quais repositórios processar
    if args.mode == "train":
        repos = TRAIN_REPOS
        print("EXTRAÇÃO DE DADOS - MODO: TREINO")
    elif args.mode == "test":
        repos = TEST_REPOS
        print("EXTRAÇÃO DE DADOS - MODO: TESTE")
    else:
        repos = get_all_repos()
        print("EXTRAÇÃO DE DADOS - MODO: TODOS")

    print("=" * 70)
    print(f"Repositórios: {len(repos)}")
    print("=" * 70)
    print()

    setup_directories()

    success_count = 0
    failed_repos = []

    for i, repo_name in enumerate(repos, 1):
        print(f"\n{'=' * 70}")
        print(f"[{i}/{len(repos)}] Processando: {repo_name}")
        print(f"{'=' * 70}\n")

        # Extrair métricas
        metrics_ok = extract_metrics(repo_name)

        # Extrair co-mudanças
        co_changes_ok = extract_co_changes(repo_name)

        if metrics_ok and co_changes_ok:
            success_count += 1
            print(f"{repo_name} processado com sucesso!")
        else:
            failed_repos.append(repo_name)
            print(f" {repo_name} processado parcialmente ou com erros")

    # Resumo final
    print("\n" + "=" * 70)
    print("RESUMO DA EXTRAÇÃO")
    print("=" * 70)
    print(f"Repositórios processados com sucesso: {success_count}/{len(repos)}")

    if failed_repos:
        print(f" Repositórios com problemas: {', '.join(failed_repos)}")

    print(f"\nDados salvos em:")
    print(f"   - Métricas: {METRICS_DIR}")
    print(f"   - Co-mudanças: {CO_CHANGES_DIR}")
    print(f"   - Dependências: {DEPENDENCIES_DIR}")
    print(
        "\nPróximo passo: Execute 'python data_integration.py' para integrar os dados"
    )


if __name__ == "__main__":
    main()
