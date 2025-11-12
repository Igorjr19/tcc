"""
Visualizações avançadas para análise de clusters.
Gera heatmaps, scatter plots comparativos e gráficos de distribuição.

Uso:
    python visualize_clusters.py spring-framework
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec


def load_project_data(project_name: str):
    """Carrega features e labels de um projeto"""
    base = Path('data/processed/coupling_scores') / project_name
    features = pd.read_csv(base / 'class_features.csv')
    
    labels_files = {
        'dbscan': base / 'dbscan_labels.csv',
        'kmeans_5': base / 'kmeans_5_labels.csv',
    }
    
    labels_data = {}
    for method, file in labels_files.items():
        if file.exists():
            labels_df = pd.read_csv(file)
            labels_data[method] = labels_df
    
    return features, labels_data


def plot_cluster_distributions(project_name: str, method: str = 'dbscan'):
    """
    Cria visualizações de distribuição de features por cluster.
    """
    features, labels_data = load_project_data(project_name)
    
    if method not in labels_data:
        print(f"❌ Método {method} não encontrado para {project_name}")
        return
    
    df = features.merge(labels_data[method], on='class')
    
    # Remove ruído para visualização
    df_clean = df[df['label'] != -1].copy()
    
    if len(df_clean) == 0:
        print(f"⚠️  Nenhum cluster válido encontrado (apenas ruído)")
        return
    
    # Features para plotar
    feature_cols = ['avg_hybrid', 'avg_structural', 'avg_logical', 
                    'pct_strong', 'cbo', 'rfc', 'degree_pairs']
    
    n_features = len(feature_cols)
    n_cols = 3
    n_rows = (n_features + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, n_rows*4))
    axes = axes.flatten()
    
    for idx, col in enumerate(feature_cols):
        ax = axes[idx]
        df_clean.boxplot(column=col, by='label', ax=ax)
        ax.set_title(f'{col} por cluster')
        ax.set_xlabel('Cluster')
        ax.set_ylabel(col)
        plt.sca(ax)
        plt.xticks(rotation=0)
    
    # Remove eixos extras
    for idx in range(n_features, len(axes)):
        fig.delaxes(axes[idx])
    
    plt.suptitle(f'Distribuição de Features por Cluster - {project_name} ({method})', 
                 fontsize=16, y=1.00)
    plt.tight_layout()
    
    output = Path('data/processed/coupling_scores') / project_name / f'{method}_distributions.png'
    plt.savefig(output, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✓ Gráfico de distribuições salvo: {output}")


def plot_cluster_heatmap(project_name: str, method: str = 'dbscan'):
    """
    Cria heatmap de características médias por cluster.
    """
    features, labels_data = load_project_data(project_name)
    
    if method not in labels_data:
        print(f"❌ Método {method} não encontrado")
        return
    
    df = features.merge(labels_data[method], on='class')
    df_clean = df[df['label'] != -1].copy()
    
    if len(df_clean) == 0:
        print(f"⚠️  Nenhum cluster válido")
        return
    
    # Features numéricas
    feature_cols = ['avg_hybrid', 'avg_structural', 'avg_logical', 
                    'pct_strong', 'cbo', 'rfc', 'dit', 'degree_pairs']
    
    # Média por cluster
    cluster_means = df_clean.groupby('label')[feature_cols].mean()
    
    # Normaliza para 0-1 (por coluna)
    cluster_means_norm = (cluster_means - cluster_means.min()) / (cluster_means.max() - cluster_means.min() + 1e-10)
    
    plt.figure(figsize=(10, max(4, len(cluster_means)*0.6)))
    sns.heatmap(cluster_means_norm.T, annot=True, fmt='.2f', cmap='YlOrRd', 
                xticklabels=[f'C{i}' for i in cluster_means.index],
                yticklabels=feature_cols, cbar_kws={'label': 'Valor Normalizado'})
    plt.title(f'Heatmap de Características por Cluster - {project_name} ({method})')
    plt.xlabel('Cluster')
    plt.ylabel('Feature')
    plt.tight_layout()
    
    output = Path('data/processed/coupling_scores') / project_name / f'{method}_heatmap.png'
    plt.savefig(output, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✓ Heatmap salvo: {output}")


def plot_cluster_comparison(project_name: str):
    """
    Compara DBSCAN vs KMeans lado a lado via PCA.
    """
    import pickle
    base = Path('data/processed/coupling_scores') / project_name
    
    # Carrega features escaladas
    with open(base / 'class_features_scaled.pkl', 'rb') as f:
        data = pickle.load(f)
    X = data['features']
    classes = data['classes']
    
    # Carrega labels
    dbscan_df = pd.read_csv(base / 'dbscan_labels.csv')
    kmeans_df = pd.read_csv(base / 'kmeans_5_labels.csv')
    
    dbscan_map = dict(zip(dbscan_df['class'], dbscan_df['label']))
    kmeans_map = dict(zip(kmeans_df['class'], kmeans_df['label']))
    
    dbscan_labels = [dbscan_map.get(c, -1) for c in classes]
    kmeans_labels = [kmeans_map.get(c, -1) for c in classes]
    
    # PCA
    from sklearn.decomposition import PCA
    pca = PCA(n_components=2)
    Xp = pca.fit_transform(X)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # DBSCAN
    scatter1 = ax1.scatter(Xp[:,0], Xp[:,1], c=dbscan_labels, cmap='tab20', s=10, alpha=0.6)
    ax1.set_title('DBSCAN')
    ax1.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')
    ax1.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')
    plt.colorbar(scatter1, ax=ax1)
    
    # KMeans
    scatter2 = ax2.scatter(Xp[:,0], Xp[:,1], c=kmeans_labels, cmap='tab20', s=10, alpha=0.6)
    ax2.set_title('KMeans (k=5)')
    ax2.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')
    ax2.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')
    plt.colorbar(scatter2, ax=ax2)
    
    plt.suptitle(f'Comparação DBSCAN vs KMeans - {project_name}', fontsize=14)
    plt.tight_layout()
    
    output = base / 'clustering_comparison.png'
    plt.savefig(output, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✓ Comparação salva: {output}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python visualize_clusters.py <projeto> [método]")
        print("Método: dbscan (padrão), kmeans_5")
        sys.exit(1)
    
    project = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else 'dbscan'
    
    print(f"\n{'='*80}")
    print(f"GERANDO VISUALIZAÇÕES: {project}")
    print(f"{'='*80}\n")
    
    plot_cluster_distributions(project, method)
    plot_cluster_heatmap(project, method)
    plot_cluster_comparison(project)
    
    print(f"\n✓ Todas as visualizações geradas com sucesso!")


if __name__ == '__main__':
    main()
