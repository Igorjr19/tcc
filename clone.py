#!/usr/bin/env python
"""
Script para clonar repositórios Java open-source.
IMPORTANTE: Usa configuração centralizada de repos_config.py
"""

import subprocess
import sys

# Importar configuração centralizada (agora na mesma pasta)
from repos_config import TRAIN_REPOS, TEST_REPOS, REPO_METADATA

REPOS_DIR = "data/repos"

def clone_repos(repos, label="Repositórios"):
    """Clona uma lista de repositórios."""
    print(f"Clonando {label} ({len(repos)} projetos)")

    success = 0
    failed = []

    for i, repo_name in enumerate(repos, 1):
        # Buscar URL dos metadados
        repo_url = REPO_METADATA[repo_name]["url"]

        print(f"[{i}/{len(repos)}] {repo_name}")

        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, f"{REPOS_DIR}/{repo_name}"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                print(f"   Clonado com sucesso\n")
                success += 1
            else:
                if "already exists" in result.stderr.lower():
                    print(f"   Repositório já existe, pulando\n")
                    success += 1
                else:
                    print(f"    Erro ao clonar\n")
                    failed.append(repo_name)
        except subprocess.TimeoutExpired:
            print(f"   Timeout ao clonar\n")
            failed.append(repo_name)
        except Exception as e:
            print(f"   Erro: {e}\n")
            failed.append(repo_name)

    print(f"Resumo: {success}/{len(repos)} clonados com sucesso")
    if failed:
        print(f" Falhas: {', '.join(failed)}")

    return success, failed


def main():
    """Função principal."""
    print("CLONAGEM DE REPOSITÓRIOS - TREINO E TESTE")
    print(f"\nTotal: {len(TRAIN_REPOS)} para TREINO + {len(TEST_REPOS)} para TESTE")
    print(f"   = {len(TRAIN_REPOS) + len(TEST_REPOS)} repositórios\n")

    # Clonar repositórios de treino
    train_success, train_failed = clone_repos(TRAIN_REPOS, "TREINO")

    # Clonar repositórios de teste
    test_success, test_failed = clone_repos(TEST_REPOS, "TESTE")

    # Resumo final
    total_success = train_success + test_success
    total_repos = len(TRAIN_REPOS) + len(TEST_REPOS)

    print("RESUMO FINAL")
    print(f"Total clonado: {total_success}/{total_repos}")
    print(f"   - TREINO: {train_success}/{len(TRAIN_REPOS)}")
    print(f"   - TESTE:  {test_success}/{len(TEST_REPOS)}")

    if train_failed or test_failed:
        print(f"\n Repositórios com problemas:")
        if train_failed:
            print(f"   TREINO: {', '.join(train_failed)}")
        if test_failed:
            print(f"   TESTE: {', '.join(test_failed)}")

    print("\nPróximo passo: Execute 'python extract_all_data.py'")

    return 0 if not (train_failed or test_failed) else 1


if __name__ == "__main__":
    sys.exit(main())
