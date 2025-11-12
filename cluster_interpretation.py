"""
Análise exploratória dos clusters gerados.
Identifica características de cada cluster e gera relatórios.

Uso:
    python cluster_interpretation.py spring-framework dbscan
    python cluster_interpretation.py spring-framework kmeans_5
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np


def analyze_cluster(project_name: str, clustering_method: str = 'dbscan'):
    """
    Analisa características dos clusters identificados.
    
    Args:
        project_name: nome do projeto
        clustering_method: 'dbscan', 'kmeans_3', 'kmeans_5', 'kmeans_7'
    """
    base = Path('data/processed/coupling_scores') / project_name
    
    # Carrega features
    features_df = pd.read_csv(base / 'class_features.csv')
    
    # Carrega labels
    if clustering_method == 'dbscan':
        labels_file = base / 'dbscan_labels.csv'
    else:
        labels_file = base / f'{clustering_method}_labels.csv'
    
    if not labels_file.exists():
        print(f"❌ Arquivo de labels não encontrado: {labels_file}")
        return
    
    labels_df = pd.read_csv(labels_file)
    
    # Merge
    df = features_df.merge(labels_df, on='class')
    
    print(f"\n{'='*80}")
    print(f"ANÁLISE DE CLUSTERS: {project_name} - {clustering_method}")
    print(f"{'='*80}\n")
    
    # Distribuição de clusters
    cluster_counts = df['label'].value_counts().sort_index()
    print("📊 Distribuição de clusters:")
    for label, count in cluster_counts.items():
        cluster_name = "Ruído" if label == -1 else f"Cluster {label}"
        pct = count / len(df) * 100
        print(f"   {cluster_name}: {count} classes ({pct:.1f}%)")
    
    # Estatísticas por cluster
    print(f"\n📈 Estatísticas por cluster:\n")
    
    feature_cols = ['avg_hybrid', 'avg_structural', 'avg_logical', 'count_strong', 
                    'pct_strong', 'cbo', 'rfc', 'dit', 'degree_pairs']
    
    for label in sorted(df['label'].unique()):
        if label == -1:
            cluster_name = "Ruído"
        else:
            cluster_name = f"Cluster {label}"
        
        cluster_data = df[df['label'] == label]
        print(f"\n{cluster_name} (n={len(cluster_data)}):")
        print("-" * 60)
        
        for col in feature_cols:
            if col in cluster_data.columns:
                mean_val = cluster_data[col].mean()
                median_val = cluster_data[col].median()
                print(f"  {col:20s}: média={mean_val:8.3f}  mediana={median_val:8.3f}")
    
    # Identifica cluster de alto acoplamento
    print(f"\n{'='*80}")
    print("🔥 CLUSTERS DE ALTO ACOPLAMENTO")
    print(f"{'='*80}\n")
    
    cluster_stats = df.groupby('label').agg({
        'avg_hybrid': 'mean',
        'avg_structural': 'mean',
        'avg_logical': 'mean',
        'pct_strong': 'mean',
        'class': 'count'
    }).rename(columns={'class': 'n_classes'})
    
    cluster_stats = cluster_stats[cluster_stats.index != -1]  # Remove ruído
    
    if len(cluster_stats) > 0:
        # Ordena por avg_hybrid decrescente
        cluster_stats_sorted = cluster_stats.sort_values('avg_hybrid', ascending=False)
        print("Top 3 clusters por acoplamento híbrido médio:")
        for i, (label, row) in enumerate(cluster_stats_sorted.head(3).iterrows(), 1):
            print(f"\n{i}. Cluster {label}:")
            print(f"   Classes: {int(row['n_classes'])}")
            print(f"   Híbrido médio: {row['avg_hybrid']:.3f}")
            print(f"   Estrutural médio: {row['avg_structural']:.3f}")
            print(f"   Lógico médio: {row['avg_logical']:.3f}")
            print(f"   % acoplamento forte: {row['pct_strong']*100:.1f}%")
            
            # Top 5 classes deste cluster
            top_classes = df[df['label'] == label].nlargest(5, 'avg_hybrid')[['class', 'avg_hybrid', 'pct_strong']]
            print(f"\n   Top 5 classes deste cluster:")
            for _, cls in top_classes.iterrows():
                print(f"      - {cls['class'][:50]:50s} (hybrid={cls['avg_hybrid']:.3f}, strong={cls['pct_strong']*100:.1f}%)")
    
    # Salva relatório
    output_file = base / f'{clustering_method}_analysis.txt'
    with open(output_file, 'w') as f:
        f.write(f"Análise de Clusters: {project_name} - {clustering_method}\n")
        f.write("="*80 + "\n\n")
        f.write("Distribuição:\n")
        for label, count in cluster_counts.items():
            f.write(f"  Label {label}: {count} classes\n")
        f.write("\n")
        f.write(cluster_stats.to_string())
    
    print(f"\n✓ Relatório salvo em: {output_file}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python cluster_interpretation.py <projeto> [método]")
        print("Método: dbscan (padrão), kmeans_3, kmeans_5, kmeans_7")
        sys.exit(1)
    
    project = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else 'dbscan'
    analyze_cluster(project, method)
