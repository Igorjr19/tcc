"""
Análises de clustering para as features por classe.
Contém funções para rodar DBSCAN, KMeans e visualizar via PCA/t-SNE.

Uso:
    from clustering_analysis import run_dbscan, run_kmeans
    run_dbscan('spring-framework')
"""
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt


def load_scaled_features(project_name: str, base_dir: Path = Path('data/processed/coupling_scores')):
    file = base_dir / project_name / 'class_features_scaled.pkl'
    if not file.exists():
        raise FileNotFoundError(f"Arquivo de features escaladas não encontrado: {file}")
    with open(file, 'rb') as f:
        data = pickle.load(f)
    return data['features'], data['columns'], data['classes'], data['scaler']


def run_dbscan(project_name: str, eps: float = 0.5, min_samples: int = 5, save_plots: bool = True):
    X, cols, classes, scaler = load_scaled_features(project_name)
    print(f"Executando DBSCAN em {project_name} (n_samples={X.shape[0]})")
    model = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1)
    labels = model.fit_predict(X)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    print(f"Clusters encontrados: {n_clusters} (incluindo ruído: {list(set(labels))[:10]})")

    # Silhouette (apenas se houver >=2 clusters)
    sil = None
    if n_clusters >= 2:
        try:
            sil = silhouette_score(X[labels!=-1], labels[labels!=-1])
            print(f"Silhouette (sem ruído): {sil:.3f}")
        except Exception as e:
            print(f"Erro ao calcular silhouette: {e}")

    # Salva labels
    out_dir = Path('data/processed/coupling_scores') / project_name
    out_dir.mkdir(parents=True, exist_ok=True)
    labels_df = pd.DataFrame({'class': classes, 'label': labels})
    labels_df.to_csv(out_dir / 'dbscan_labels.csv', index=False)
    print(f"✓ Labels salvos: {out_dir / 'dbscan_labels.csv'}")

    # Visualização PCA 2D
    if save_plots:
        pca = PCA(n_components=2)
        Xp = pca.fit_transform(X)
        plt.figure(figsize=(8,6))
        scatter = plt.scatter(Xp[:,0], Xp[:,1], c=labels, cmap='tab20', s=10)
        plt.title(f'DBSCAN clusters ({project_name})')
        plt.xlabel('PC1')
        plt.ylabel('PC2')
        plt.colorbar()
        plt.tight_layout()
        plt.savefig(out_dir / 'dbscan_pca.png', dpi=200)
        plt.close()
        print(f"✓ Plot PCA salvo: {out_dir / 'dbscan_pca.png'}")

    return {'labels': labels, 'n_clusters': n_clusters, 'silhouette': sil}


def run_kmeans(project_name: str, k: int = 5, save_plots: bool = True):
    X, cols, classes, scaler = load_scaled_features(project_name)
    print(f"Executando KMeans (k={k}) em {project_name} (n_samples={X.shape[0]})")
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = model.fit_predict(X)

    out_dir = Path('data/processed/coupling_scores') / project_name
    out_dir.mkdir(parents=True, exist_ok=True)
    labels_df = pd.DataFrame({'class': classes, 'label': labels})
    labels_df.to_csv(out_dir / f'kmeans_{k}_labels.csv', index=False)
    print(f"✓ Labels salvos: {out_dir / f'kmeans_{k}_labels.csv'}")

    # Silhouette
    sil = None
    if len(set(labels)) >= 2:
        try:
            sil = silhouette_score(X, labels)
            print(f"Silhouette: {sil:.3f}")
        except Exception as e:
            print(f"Erro ao calcular silhouette: {e}")

    # Visualização
    if save_plots:
        pca = PCA(n_components=2)
        Xp = pca.fit_transform(X)
        import matplotlib.pyplot as plt
        plt.figure(figsize=(8,6))
        plt.scatter(Xp[:,0], Xp[:,1], c=labels, cmap='tab20', s=10)
        plt.title(f'KMeans (k={k}) - {project_name}')
        plt.xlabel('PC1')
        plt.ylabel('PC2')
        plt.colorbar()
        plt.tight_layout()
        plt.savefig(out_dir / f'kmeans_{k}_pca.png', dpi=200)
        plt.close()
        print(f"✓ Plot PCA salvo: {out_dir / f'kmeans_{k}_pca.png'}")

    return {'labels': labels, 'silhouette': sil}


def compute_tsne(project_name: str, perplexity: int = 30, n_iter: int = 1000):
    X, cols, classes, scaler = load_scaled_features(project_name)
    print(f"Executando t-SNE (n={X.shape[0]}) - pode demorar alguns minutos")
    tsne = TSNE(n_components=2, perplexity=perplexity, n_iter=n_iter, init='pca', learning_rate='auto')
    Xs = tsne.fit_transform(X)

    out_dir = Path('data/processed/coupling_scores') / project_name
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / 'tsne_embeddings.npy', Xs)
    print(f"✓ Embeddings t-SNE salvos: {out_dir / 'tsne_embeddings.npy'}")
    return Xs
