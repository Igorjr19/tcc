"""
Análise comparativa entre projetos - identifica padrões comuns
e diferenças entre projetos.

Uso:
    python cross_project_analysis.py
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def load_consolidated_results():
    """Carrega resultados consolidados do clustering"""
    file = Path('data/processed/coupling_scores/clustering_results_consolidated.csv')
    if not file.exists():
        print("❌ Arquivo consolidado não encontrado. Execute run_clustering_all_projects.py primeiro.")
        return None
    return pd.read_csv(file)


def analyze_best_algorithms():
    """Identifica qual algoritmo teve melhor desempenho"""
    df = load_consolidated_results()
    if df is None:
        return
    
    print("\n" + "="*80)
    print("ANÁLISE: MELHOR ALGORITMO POR PROJETO")
    print("="*80 + "\n")
    
    # O CSV tem formato: project, dbscan_clusters, dbscan_silhouette, kmeans_3_silhouette, ...
    # Precisamos converter para formato long
    best_per_project = []
    for _, row in df.iterrows():
        project = row['project']
        
        # Compara todos os métodos
        methods_scores = {
            'dbscan': row['dbscan_silhouette'],
            'kmeans_3': row['kmeans_3_silhouette'],
            'kmeans_5': row['kmeans_5_silhouette'],
            'kmeans_7': row['kmeans_7_silhouette']
        }
        
        best_method = max(methods_scores, key=methods_scores.get)
        best_silhouette = methods_scores[best_method]
        n_clusters = row['dbscan_clusters'] if best_method == 'dbscan' else int(best_method.split('_')[1])
        
        best_per_project.append({
            'project': project,
            'best_method': best_method,
            'best_silhouette': best_silhouette,
            'n_clusters': n_clusters
        })
    
    best_df = pd.DataFrame(best_per_project).sort_values('best_silhouette', ascending=False)
    
    print(best_df.to_string(index=False))
    
    # Estatísticas gerais
    print("\n" + "-"*80)
    print("RESUMO:")
    print(f"  - DBSCAN foi melhor em: {sum(best_df['best_method'] == 'dbscan')} projetos")
    print(f"  - KMeans foi melhor em: {sum(best_df['best_method'].str.startswith('kmeans'))} projetos")
    print(f"  - Silhouette médio do melhor: {best_df['best_silhouette'].mean():.3f}")
    
    return best_df


def analyze_cluster_patterns():
    """Analisa padrões de número de clusters"""
    df = load_consolidated_results()
    if df is None:
        return
    
    print("\n" + "="*80)
    print("ANÁLISE: PADRÕES DE CLUSTERS")
    print("="*80 + "\n")
    
    # DBSCAN - quantos clusters surgem naturalmente?
    print("📊 DBSCAN (detecção automática):")
    print(f"  - Clusters médio: {df['dbscan_clusters'].mean():.1f}")
    print(f"  - Min/Max: {df['dbscan_clusters'].min()} / {df['dbscan_clusters'].max()}")
    print(f"  - Silhouette médio: {df['dbscan_silhouette'].mean():.3f}")
    
    # KMeans - qual k é melhor?
    for k in [3, 5, 7]:
        col = f'kmeans_{k}_silhouette'
        print(f"\n📊 KMeans (k={k}):")
        print(f"  - Silhouette médio: {df[col].mean():.3f}")
        print(f"  - Melhor que DBSCAN em: {sum(df[col] > df['dbscan_silhouette'])} projetos")


def plot_comparison_heatmap():
    """Cria heatmap comparando métodos por projeto"""
    df = load_consolidated_results()
    if df is None:
        return
    
    # Criar formato long para pivot
    data_long = []
    for _, row in df.iterrows():
        data_long.extend([
            {'project': row['project'], 'method': 'dbscan', 'silhouette': row['dbscan_silhouette']},
            {'project': row['project'], 'method': 'kmeans_3', 'silhouette': row['kmeans_3_silhouette']},
            {'project': row['project'], 'method': 'kmeans_5', 'silhouette': row['kmeans_5_silhouette']},
            {'project': row['project'], 'method': 'kmeans_7', 'silhouette': row['kmeans_7_silhouette']}
        ])
    df_long = pd.DataFrame(data_long)
    
    # Pivot: projetos vs métodos
    pivot = df_long.pivot(index='project', columns='method', values='silhouette')
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt='.3f', cmap='RdYlGn', center=0.5,
                vmin=0, vmax=1, cbar_kws={'label': 'Silhouette Score'})
    plt.title('Comparação de Métodos de Clustering por Projeto', fontsize=14)
    plt.xlabel('Método')
    plt.ylabel('Projeto')
    plt.tight_layout()
    
    output = Path('results/plots/clustering_comparison_heatmap.png')
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"\n✓ Heatmap salvo: {output}")


def plot_cluster_size_distribution():
    """Plota distribuição do número de clusters"""
    df = load_consolidated_results()
    if df is None:
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Distribuição DBSCAN
    axes[0].bar(range(len(df)), df['dbscan_clusters'], color='steelblue', alpha=0.7)
    axes[0].set_xticks(range(len(df)))
    axes[0].set_xticklabels(df['project'], rotation=45, ha='right')
    axes[0].set_ylabel('Número de Clusters')
    axes[0].set_title('DBSCAN - Clusters Detectados')
    axes[0].grid(axis='y', alpha=0.3)
    
    # Comparação silhouette
    methods_data = {
        'DBSCAN': df['dbscan_silhouette'],
        'KMeans k=3': df['kmeans_3_silhouette'],
        'KMeans k=5': df['kmeans_5_silhouette'],
        'KMeans k=7': df['kmeans_7_silhouette']
    }
    method_colors = ['steelblue', 'orange', 'green', 'red']
    
    for (label, data), color in zip(methods_data.items(), method_colors):
        axes[1].plot(range(len(df)), data, 
                    marker='o', label=label,
                    color=color, alpha=0.7)
    
    axes[1].set_xticks(range(len(df)))
    axes[1].set_xticklabels(df['project'], rotation=45, ha='right')
    axes[1].set_ylabel('Silhouette Score')
    axes[1].set_title('Comparação de Qualidade dos Clusters')
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    
    output = Path('results/plots/clustering_distribution.png')
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✓ Gráfico de distribuição salvo: {output}")


def generate_executive_summary():
    """Gera relatório executivo em texto"""
    df = load_consolidated_results()
    if df is None:
        return
    
    output = Path('results/clustering_executive_summary.txt')
    output.parent.mkdir(parents=True, exist_ok=True)
    
    # Converte para formato long para análise
    data_long = []
    for _, row in df.iterrows():
        data_long.extend([
            {'project': row['project'], 'method': 'dbscan', 'silhouette': row['dbscan_silhouette'], 'n_clusters': row['dbscan_clusters']},
            {'project': row['project'], 'method': 'kmeans_3', 'silhouette': row['kmeans_3_silhouette'], 'n_clusters': 3},
            {'project': row['project'], 'method': 'kmeans_5', 'silhouette': row['kmeans_5_silhouette'], 'n_clusters': 5},
            {'project': row['project'], 'method': 'kmeans_7', 'silhouette': row['kmeans_7_silhouette'], 'n_clusters': 7}
        ])
    df_long = pd.DataFrame(data_long)
    
    with open(output, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("RELATÓRIO EXECUTIVO - ANÁLISE DE CLUSTERING\n")
        f.write("=" * 80 + "\n\n")
        
        # Visão geral
        f.write("1. VISÃO GERAL\n")
        f.write("-" * 80 + "\n")
        f.write(f"   Projetos analisados: {df['project'].nunique()}\n")
        f.write(f"   Métodos aplicados: 4 (DBSCAN, KMeans k=3,5,7)\n")
        f.write(f"   Total de experimentos: {len(df_long)}\n\n")
        
        # Melhor desempenho
        f.write("2. MELHORES RESULTADOS\n")
        f.write("-" * 80 + "\n")
        top5 = df_long.nlargest(5, 'silhouette')
        for idx, row in top5.iterrows():
            f.write(f"   {row['project']:25} | {row['method']:12} | "
                   f"Silhouette: {row['silhouette']:.3f} | Clusters: {row['n_clusters']}\n")
        f.write("\n")
        
        # Piores resultados
        f.write("3. RESULTADOS COM DESAFIOS\n")
        f.write("-" * 80 + "\n")
        bottom5 = df_long.nsmallest(5, 'silhouette')
        for idx, row in bottom5.iterrows():
            f.write(f"   {row['project']:25} | {row['method']:12} | "
                   f"Silhouette: {row['silhouette']:.3f} | Clusters: {row['n_clusters']}\n")
        f.write("\n")
        
        # DBSCAN vs KMeans
        f.write("4. COMPARAÇÃO: DBSCAN vs KMeans\n")
        f.write("-" * 80 + "\n")
        dbscan_avg = df_long[df_long['method'] == 'dbscan']['silhouette'].mean()
        kmeans_avg = df_long[df_long['method'].str.startswith('kmeans')]['silhouette'].mean()
        f.write(f"   DBSCAN média:  {dbscan_avg:.3f}\n")
        f.write(f"   KMeans média:  {kmeans_avg:.3f}\n")
        winner = "DBSCAN" if dbscan_avg > kmeans_avg else "KMeans"
        f.write(f"   Vencedor:      {winner}\n\n")
        
        # Recomendações
        f.write("5. RECOMENDAÇÕES\n")
        f.write("-" * 80 + "\n")
        
        best_overall = df_long.loc[df_long['silhouette'].idxmax()]
        f.write(f"   ✓ Melhor configuração geral: {best_overall['method']} "
               f"(Silhouette: {best_overall['silhouette']:.3f})\n")
        
        dbscan_df = df_long[df_long['method'] == 'dbscan']
        dbscan_good = sum(dbscan_df['silhouette'] > 0.5)
        f.write(f"   ✓ DBSCAN teve boa qualidade (>0.5) em {dbscan_good}/{len(df)} projetos\n")
        
        kmeans5_df = df_long[df_long['method'] == 'kmeans_5']
        if len(kmeans5_df) > 0:
            kmeans_good = sum(kmeans5_df['silhouette'] > 0.5)
            f.write(f"   ✓ KMeans (k=5) teve boa qualidade em {kmeans_good}/{len(df)} projetos\n")
        
        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write("FIM DO RELATÓRIO\n")
        f.write("=" * 80 + "\n")
    
    print(f"\n✓ Relatório executivo salvo: {output}")


def main():
    print("\n" + "="*80)
    print("ANÁLISE COMPARATIVA ENTRE PROJETOS")
    print("="*80)
    
    # 1. Melhor algoritmo
    analyze_best_algorithms()
    
    # 2. Padrões de clusters
    analyze_cluster_patterns()
    
    # 3. Visualizações
    print("\n" + "="*80)
    print("GERANDO VISUALIZAÇÕES")
    print("="*80)
    plot_comparison_heatmap()
    plot_cluster_size_distribution()
    
    # 4. Relatório executivo
    print("\n" + "="*80)
    print("GERANDO RELATÓRIO EXECUTIVO")
    print("="*80)
    generate_executive_summary()
    
    print("\n" + "="*80)
    print("✓ ANÁLISE COMPLETA CONCLUÍDA!")
    print("="*80)


if __name__ == '__main__':
    main()
