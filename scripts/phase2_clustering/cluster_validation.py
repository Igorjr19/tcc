"""
Métricas de validação de clustering e funções utilitárias.

Uso:
    from cluster_validation import evaluate_clustering
    evaluate_clustering('spring-framework', labels_array)
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score


def evaluate_clustering(features, labels):
    """
    Calcula métricas de validação de clustering.

    Args:
        features: array-like 2D (n_samples, n_features)
        labels: array-like 1D (n_samples)

    Returns:
        dict com silhouette, davies_bouldin, calinski_harabasz
    """
    labels = np.asarray(labels)
    X = np.asarray(features)
    results = {}

    # Silhouette exige >=2 clusters e menos do que n_samples
    unique_labels = set(labels)
    n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)

    if n_clusters >= 2:
        try:
            results['silhouette'] = silhouette_score(X[labels!=-1], labels[labels!=-1])
        except Exception:
            results['silhouette'] = None
    else:
        results['silhouette'] = None

    try:
        results['davies_bouldin'] = davies_bouldin_score(X[labels!=-1], labels[labels!=-1]) if n_clusters >= 2 else None
    except Exception:
        results['davies_bouldin'] = None

    try:
        results['calinski_harabasz'] = calinski_harabasz_score(X[labels!=-1], labels[labels!=-1]) if n_clusters >= 2 else None
    except Exception:
        results['calinski_harabasz'] = None

    return results


def load_features(project_name: str, base_dir: Path = Path('data/processed/coupling_scores')):
    scaled = base_dir / project_name / 'class_features_scaled.pkl'
    if not scaled.exists():
        raise FileNotFoundError(scaled)
    import pickle
    with open(scaled, 'rb') as f:
        data = pickle.load(f)
    return data['features'], data['columns'], data['classes']


def evaluate_saved_labels(project_name: str, label_file: str):
    base_dir = Path('data/processed/coupling_scores')
    X, cols, classes = load_features(project_name, base_dir=base_dir)
    df_labels = pd.read_csv(Path(base_dir) / project_name / label_file)
    # assume label_file tem coluna 'class' e 'label'
    # ordena labels na mesma ordem das classes salvas
    labels_map = dict(zip(df_labels['class'], df_labels['label']))
    labels = [labels_map.get(c, -1) for c in classes]
    return evaluate_clustering(X, labels)
