#!/usr/bin/env python
"""
Configuração centralizada de repositórios.
Define claramente quais repositórios são usados para TREINO e TESTE.

Este arquivo é importado por todos os scripts de extração e treinamento
para garantir consistência na metodologia de validação.
"""

TRAIN_REPOS = [
    "commons-text",
    "commons-io",
    "commons-lang",
    "commons-collections",
    "junit4",
    "mockito",
    "guava",
    "spring-boot",
    "dbeaver",
]

TEST_REPOS = [
    "spring-framework",
    "commons-math",
    "gson",
    "assertj-core",
]

REPO_METADATA = {
    "commons-text": {
        "url": "https://github.com/apache/commons-text.git",
    },
    "commons-io": {
        "url": "https://github.com/apache/commons-io.git",
    },
    "commons-lang": {
        "url": "https://github.com/apache/commons-lang.git",
    },
    "commons-collections": {
        "url": "https://github.com/apache/commons-collections.git",
    },
    "junit4": {
        "url": "https://github.com/junit-team/junit4.git",
    },
    "mockito": {
        "url": "https://github.com/mockito/mockito.git",
    },
    "guava": {
        "url": "https://github.com/google/guava.git",
    },
    "spring-boot": {
        "url": "https://github.com/spring-projects/spring-boot.git",
    },
    "dbeaver": {
        "url": "https://github.com/dbeaver/dbeaver.git",
    },
    "spring-framework": {
        "url": "https://github.com/spring-projects/spring-framework.git",
    },
    "commons-math": {
        "url": "https://github.com/apache/commons-math.git",
    },
    "gson": {
        "url": "https://github.com/google/gson.git",
    },
    "assertj-core": {
        "url": "https://github.com/assertj/assertj-core.git",
    },
}

def get_all_repos():
    """Retorna todos os repositórios (treino + teste)."""
    return TRAIN_REPOS + TEST_REPOS

def print_summary():
    """Imprime um resumo da configuração."""
    print("CONFIGURAÇÃO DE REPOSITÓRIOS")

    print(f"\nTREINO ({len(TRAIN_REPOS)} repositórios):")
    for repo in TRAIN_REPOS:
        info = REPO_METADATA.get(repo, {})
        print(f"  - {repo:25s}")

    print(f"\nTESTE ({len(TEST_REPOS)} repositórios):")
    for repo in TEST_REPOS:
        info = REPO_METADATA.get(repo, {})
        print(f"  - {repo:25s}")

    print(f"\nTOTAL: {len(get_all_repos())} repositórios")
    print(f"   Proporção: {len(TRAIN_REPOS)}:{len(TEST_REPOS)} (treino:teste)")
    print(
        f"   Percentual: {len(TRAIN_REPOS) / len(get_all_repos()) * 100:.0f}% treino, {len(TEST_REPOS) / len(get_all_repos()) * 100:.0f}% teste"
    )


if __name__ == "__main__":
    print_summary()
