#!/usr/bin/env python
"""
Script unificado para integração de dados - versão funcional definitiva.
Combina métricas estruturais, dependências explícitas e co-mudanças em um dataset otimizado.
Inclui todas as correções e otimizações aplicadas.
"""

import pandas as pd
from pathlib import Path
import numpy as np
from itertools import combinations

# Diretórios
BASE_DIR = Path(__file__).parent.absolute()
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

METRICS_DIR = RAW_DATA_DIR / "metrics"
CO_CHANGES_DIR = RAW_DATA_DIR / "co_changes"
DEPENDENCIES_DIR = RAW_DATA_DIR / "dependencies"


def load_all_metrics():
    """Carrega e concatena todos os arquivos de métricas."""
    print("Carregando métricas estruturais...")

    all_metrics = []

    for metrics_file in METRICS_DIR.glob("*_metrics.csv"):
        repo_name = metrics_file.stem.replace("_metrics", "")

        try:
            df = pd.read_csv(metrics_file)
            df["Repositorio"] = repo_name
            all_metrics.append(df)
            print(f"  {repo_name}: {len(df)} classes")
        except Exception as e:
            print(f"  Erro ao carregar {metrics_file.name}: {e}")

    if not all_metrics:
        print("  Nenhuma métrica encontrada!")
        return pd.DataFrame()

    df_metrics = pd.concat(all_metrics, ignore_index=True)
    print(f"\nTotal de classes analisadas: {len(df_metrics)}")
    print(f"   Repositórios: {df_metrics['Repositorio'].nunique()}")

    return df_metrics


def load_all_co_changes():
    """Carrega apenas co-mudanças que realmente existem."""
    print("\nCarregando co-mudanças...")

    all_co_changes = []

    for co_change_file in CO_CHANGES_DIR.glob("*_co_changes.csv"):
        repo_name = co_change_file.stem.replace("_co_changes", "")

        try:
            df = pd.read_csv(co_change_file)
            if len(df) > 0:
                df["Repositorio"] = repo_name
                all_co_changes.append(df)
                print(f"  {repo_name}: {len(df)} co-mudanças")
            else:
                print(f"  {repo_name}: arquivo vazio")
        except Exception as e:
            print(f"  Erro ao carregar {co_change_file.name}: {e}")

    if not all_co_changes:
        print("  Nenhuma co-mudança encontrada!")
        return pd.DataFrame()

    df_co_changes = pd.concat(all_co_changes, ignore_index=True)
    print(f"Total de co-mudanças: {len(df_co_changes)}")

    return df_co_changes


def load_all_dependencies():
    """Carrega dependências explícitas."""
    print("\nCarregando dependências explícitas...")

    all_dependencies = []

    for dep_file in DEPENDENCIES_DIR.glob("*_dependencies.csv"):
        repo_name = dep_file.stem.replace("_dependencies", "")

        try:
            df = pd.read_csv(dep_file)
            if len(df) > 0:
                df["Repositorio"] = repo_name
                all_dependencies.append(df)
                print(f"  {repo_name}: {len(df)} dependências")
            else:
                print(f"  {repo_name}: arquivo vazio")
        except Exception as e:
            print(f"  Erro ao carregar {dep_file.name}: {e}")

    if not all_dependencies:
        print("  Nenhuma dependência encontrada!")
        return pd.DataFrame()

    df_dependencies = pd.concat(all_dependencies, ignore_index=True)
    print(f"Total de dependências: {len(df_dependencies)}")

    return df_dependencies


def create_dataset(df_metrics, df_co_changes, df_dependencies, sample_size=100000):
    """
    Cria dataset integrado com amostragem inteligente para evitar problemas de memória.
    """
    print(f"\nCRIANDO DATASET INTEGRADO")
    print(f"   Tamanho da amostra: {sample_size:,}")

    # Criar lista de datasets por repositório
    datasets_por_repo = []

    for repo in df_metrics["Repositorio"].unique():
        print(f"\n   Processando {repo}...")

        # Filtrar dados do repositório
        repo_metrics = df_metrics[df_metrics["Repositorio"] == repo].copy()
        repo_co_changes = (
            df_co_changes[df_co_changes["Repositorio"] == repo].copy()
            if not df_co_changes.empty
            else pd.DataFrame()
        )
        repo_dependencies = (
            df_dependencies[df_dependencies["Repositorio"] == repo].copy()
            if not df_dependencies.empty
            else pd.DataFrame()
        )

        if len(repo_metrics) < 2:
            print(
                f"       Muito poucas classes ({len(repo_metrics)}), pulando..."
            )
            continue

        # Gerar pares de classes
        classes = repo_metrics["Classe"].unique()

        # Limitar número de classes por repo para controlar memória
        if len(classes) > 50:
            classes = classes[:50]
            print(
                f"      Limitando a {len(classes)} classes para controlar memória"
            )

        # Criar todos os pares possíveis
        class_pairs = list(combinations(classes, 2))

        # Amostragem se necessário
        if len(class_pairs) > sample_size // len(df_metrics["Repositorio"].unique()):
            max_pairs = sample_size // len(df_metrics["Repositorio"].unique())
            class_pairs = list(
                np.random.choice(len(class_pairs), size=max_pairs, replace=False)
            )
            class_pairs = [list(combinations(classes, 2))for i in class_pairs]
            print(
                f"      Amostrando {len(class_pairs)} pares de {len(list(combinations(classes, 2)))}"
            )

        # Criar dataset do repositório
        repo_data = []
        for classe1, classe2 in class_pairs:
            row_data = {"Repositorio": repo, "Classe1": classe1, "Classe2": classe2}
            repo_data.append(row_data)

        if repo_data:
            repo_df = pd.DataFrame(repo_data)
            datasets_por_repo.append(repo_df)
            print(f"      {len(repo_df)} pares criados")

    if not datasets_por_repo:
        print("Nenhum dataset foi criado!")
        return pd.DataFrame()

    # Combinar todos os repositórios
    print(f"\nCombinando dados de {len(datasets_por_repo)} repositórios...")
    dataset = pd.concat(datasets_por_repo, ignore_index=True)

    print(f"   Dataset base: {len(dataset):,} pares de classes")

    # Adicionar métricas das classes
    print(f"    Adicionando métricas estruturais...")

    # Métricas para Classe1
    dataset = dataset.merge(
        df_metrics[["Repositorio", "Classe", "CBO", "DIT", "LCOM", "RFC"]],
        left_on=["Repositorio", "Classe1"],
        right_on=["Repositorio", "Classe"],
        how="left",
        suffixes=("", "_classe1"),
    ).drop("Classe", axis=1)

    dataset = dataset.rename(
        columns={
            "CBO": "CBO_classe1",
            "DIT": "DIT_classe1",
            "LCOM": "LCOM_classe1",
            "RFC": "RFC_classe1",
        }
    )

    # Métricas para Classe2
    dataset = dataset.merge(
        df_metrics[["Repositorio", "Classe", "CBO", "DIT", "LCOM", "RFC"]],
        left_on=["Repositorio", "Classe2"],
        right_on=["Repositorio", "Classe"],
        how="left",
        suffixes=("", "_classe2"),
    ).drop("Classe", axis=1)

    dataset = dataset.rename(
        columns={
            "CBO": "CBO_classe2",
            "DIT": "DIT_classe2",
            "LCOM": "LCOM_classe2",
            "RFC": "RFC_classe2",
        }
    )

    # Adicionar co-mudanças
    print(f"   Adicionando co-mudanças...")
    if not df_co_changes.empty:
        dataset = dataset.merge(
            df_co_changes[["Repositorio", "Classe1", "Classe2", "FrequenciaCoMudanca"]],
            on=["Repositorio", "Classe1", "Classe2"],
            how="left",
        )

    dataset["co_change_frequency"] = dataset.get("FrequenciaCoMudanca", 0).fillna(0)
    dataset["has_co_change"] = (dataset["co_change_frequency"] > 0).astype(int)
    dataset["log_co_frequency"] = np.log1p(dataset["co_change_frequency"])
    dataset["high_frequency"] = (dataset["co_change_frequency"] > 5).astype(int)

    # Adicionar dependências (target)
    print(f"   Adicionando dependências explícitas (target)...")
    if not df_dependencies.empty:
        dataset = dataset.merge(
            df_dependencies[["Repositorio", "Classe1", "Classe2"]].assign(
                has_dependency=1
            ),
            on=["Repositorio", "Classe1", "Classe2"],
            how="left",
        )

    dataset["has_dependency"] = dataset.get("has_dependency", 0).fillna(0).astype(int)

    # Feature engineering
    print(f"    Criando features derivadas...")

    # Diferenças entre métricas
    dataset["CBO_diff"] = abs(
        dataset["CBO_classe1"].fillna(0) - dataset["CBO_classe2"].fillna(0)
    )
    dataset["DIT_diff"] = abs(
        dataset["DIT_classe1"].fillna(0) - dataset["DIT_classe2"].fillna(0)
    )
    dataset["LCOM_diff"] = abs(
        dataset["LCOM_classe1"].fillna(0) - dataset["LCOM_classe2"].fillna(0)
    )
    dataset["RFC_diff"] = abs(
        dataset["RFC_classe1"].fillna(0) - dataset["RFC_classe2"].fillna(0)
    )

    # Somas de métricas
    dataset["CBO_sum"] = dataset["CBO_classe1"].fillna(0) + dataset[
        "CBO_classe2"
    ].fillna(0)
    dataset["RFC_sum"] = dataset["RFC_classe1"].fillna(0) + dataset[
        "RFC_classe2"
    ].fillna(0)

    # Limpar colunas temporárias
    cols_to_drop = [col for col in dataset.columns if "FrequenciaCoMudanca" in col]
    if cols_to_drop:
        dataset = dataset.drop(columns=cols_to_drop)

    # Substituir NaN por 0
    dataset = dataset.fillna(0)

    print(
        f"   Dataset final: {len(dataset):,} linhas, {len(dataset.columns)} colunas"
    )
    print(
        f"   Distribuição target: {dataset['has_dependency'].value_counts().to_dict()}"
    )

    # Análise das features
    feature_cols = [
        col
        for col in dataset.columns
        if col not in ["Repositorio", "Classe1", "Classe2", "has_dependency"]
    ]
    co_change_features = [
        col
        for col in feature_cols
        if "co_" in col.lower() or "frequency" in col.lower()
    ]
    structural_features = [
        col
        for col in feature_cols
        if any(metric in col.upper() for metric in ["CBO", "DIT", "LCOM", "RFC"])
    ]

    print(f"   Features co-mudança: {len(co_change_features)}")
    print(f"    Features estruturais: {len(structural_features)}")

    return dataset


def generate_all_class_pairs(df_metrics):
    """Gera todos os pares possíveis de classes por repositório."""
    all_pairs = []
    
    for repo in df_metrics["Repositorio"].unique():
        repo_classes = df_metrics[df_metrics["Repositorio"] == repo]["Classe"].unique()
        
        for i, classe1 in enumerate(repo_classes):
            for classe2 in repo_classes[i+1:]:
                all_pairs.append({
                    "Repositorio": repo,
                    "Classe1": classe1,
                    "Classe2": classe2
                })
    
    return pd.DataFrame(all_pairs)


def integrate_dataset(df_metrics, df_dependencies, df_co_changes):
    """
    Integra métricas, dependências e co-mudanças em um único dataset mestre.
    """
    print("\nIntegrando datasets...")

    # 1. Gerar todos os pares possíveis
    df_pairs = generate_all_class_pairs(df_metrics)

    # 2. Adicionar métricas da Classe1
    df_final = pd.merge(
        df_pairs,
        df_metrics[["Repositorio", "Classe", "CBO", "DIT", "LCOM", "RFC"]],
        left_on=["Repositorio", "Classe1"],
        right_on=["Repositorio", "Classe"],
        how="left",
    )
    df_final.rename(
        columns={"CBO": "CBO_C1", "DIT": "DIT_C1", "LCOM": "LCOM_C1", "RFC": "RFC_C1"},
        inplace=True,
    )
    df_final.drop(columns=["Classe"], inplace=True)

    # 3. Adicionar métricas da Classe2
    df_final = pd.merge(
        df_final,
        df_metrics[["Repositorio", "Classe", "CBO", "DIT", "LCOM", "RFC"]],
        left_on=["Repositorio", "Classe2"],
        right_on=["Repositorio", "Classe"],
        how="left",
    )
    df_final.rename(
        columns={"CBO": "CBO_C2", "DIT": "DIT_C2", "LCOM": "LCOM_C2", "RFC": "RFC_C2"},
        inplace=True,
    )
    df_final.drop(columns=["Classe"], inplace=True)

    # 4. Adicionar dependências explícitas (variável alvo)
    if not df_dependencies.empty:
        df_dependencies["DependenciaExplicita_temp"] = 1
        df_final = pd.merge(
            df_final,
            df_dependencies[
                ["Repositorio", "Classe1", "Classe2", "DependenciaExplicita_temp"]
            ],
            on=["Repositorio", "Classe1", "Classe2"],
            how="left",
        )
        df_final["DependenciaExplicita"] = (
            df_final["DependenciaExplicita_temp"].fillna(0).astype(int)
        )
        df_final.drop(columns=["DependenciaExplicita_temp"], inplace=True)
    else:
        df_final["DependenciaExplicita"] = 0

    # 5. Adicionar frequência de co-mudança
    if not df_co_changes.empty:
        df_final = pd.merge(
            df_final,
            df_co_changes[["Repositorio", "Classe1", "Classe2", "FrequenciaCoMudanca"]],
            on=["Repositorio", "Classe1", "Classe2"],
            how="left",
        )
        df_final["FrequenciaCoMudanca"] = (
            df_final["FrequenciaCoMudanca"].fillna(0).astype(int)
        )
    else:
        df_final["FrequenciaCoMudanca"] = 0

    # 6. Feature Engineering: criar feature binária de co-mudança forte
    df_final["CoMudancaForte"] = (df_final["FrequenciaCoMudanca"] > 5).astype(int)

    # 7. Remover linhas com valores nulos (se houver problemas no merge)
    df_final.dropna(inplace=True)

    print(f"\nDataset integrado com {len(df_final):,} pares de classes")

    return df_final


def analyze_dataset(df):
    """Analisa o dataset final e mostra estatísticas."""
    print("\n" + "=" * 70)
    print("ANÁLISE DO DATASET MESTRE")
    print("=" * 70)

    print(f"\nDimensões: {df.shape[0]:,} linhas × {df.shape[1]} colunas")

    print("\nDistribuição por Repositório:")
    repo_counts = df["Repositorio"].value_counts()
    for repo, count in repo_counts.items():
        print(f"  - {repo}: {count:,} pares")

    print("\nVariável Alvo (DependenciaExplicita):")
    target_dist = df["DependenciaExplicita"].value_counts()
    total = len(df)
    print(
        f"  - Sem dependência (0): {target_dist.get(0, 0):,} ({target_dist.get(0, 0) / total * 100:.2f}%)"
    )
    print(
        f"  - Com dependência (1): {target_dist.get(1, 0):,} ({target_dist.get(1, 0) / total * 100:.2f}%)"
    )

    if target_dist.get(1, 0) > 0:
        ratio = target_dist.get(0, 0) / target_dist.get(1, 0)
        print(f"  - Razão (Negativo/Positivo): {ratio:.2f}:1")

    print("\nCo-Mudanças:")
    print(f"  - Pares com co-mudança > 0: {(df['FrequenciaCoMudanca'] > 0).sum():,}")
    print(f"  - Pares com co-mudança forte (> 5): {df['CoMudancaForte'].sum():,}")
    print(f"  - Frequência média: {df['FrequenciaCoMudanca'].mean():.2f}")
    print(f"  - Frequência máxima: {df['FrequenciaCoMudanca'].max()}")

    print("\nEstatísticas das Métricas CK:")
    metrics_cols = ["CBO_C1", "DIT_C1", "LCOM_C1", "RFC_C1"]
    print(df[metrics_cols].describe().round(2))

    # Casos interessantes: alto acoplamento lógico SEM acoplamento estrutural
    interesting = df[
        (df["DependenciaExplicita"] == 0) & (df["FrequenciaCoMudanca"] > 5)
    ]

    if len(interesting) > 0:
        print(f"\nCasos Interessantes (dependências implícitas potenciais):")
        print(
            f"   {len(interesting):,} pares SEM dependência estrutural, mas COM alta co-mudança"
        )
        print(f"   Isso representa {len(interesting) / len(df) * 100:.2f}% do dataset")


def save_dataset(dataset, filename="master_dataset.csv"):
    """Salva o dataset processado."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = PROCESSED_DATA_DIR / filename
    dataset.to_csv(output_file, index=False)

    print(f"\nDataset salvo em: {output_file}")
    print(
        f"   Tamanho: {len(dataset):,} linhas, {len(dataset.columns)} colunas"
    )

    # Estatísticas do target
    positive_count = dataset["has_dependency"].sum()
    negative_count = len(dataset) - positive_count
    print(f"   Target:")
    print(f"      Positivos (tem dependência): {positive_count:,}")
    print(f"      Negativos (sem dependência): {negative_count:,}")
    print(f"      Proporção positivos: {positive_count / len(dataset):.2%}")

    return output_file


def main():
    """Função principal."""
    print("=" * 80)
    print("INTEGRAÇÃO DE DADOS - VERSÃO UNIFICADA")
    print("=" * 80)
    print(" Processamento otimizado com todas as correções aplicadas")
    print()

    # Carregar dados
    df_metrics = load_all_metrics()
    df_co_changes = load_all_co_changes()
    df_dependencies = load_all_dependencies()

    if df_metrics.empty:
        print("Não foi possível carregar métricas estruturais")
        print("   Execute 'python extract_all_data.py' primeiro")
        return

    # Criar dataset integrado
    dataset = create_dataset(df_metrics, df_co_changes, df_dependencies)

    if dataset.empty:
        print("Falha na criação do dataset")
        return

    # Salvar dataset
    output_file = save_dataset(dataset)

    print("\n" + "=" * 80)
    print("INTEGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
    print(f"Dataset disponível em: {output_file}")
    print("\nPróximo passo: Execute 'python training.py' para treinar modelos")
    print("=" * 80)


if __name__ == "__main__":
    main()
