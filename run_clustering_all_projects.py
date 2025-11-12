"""
Script para executar análise de clustering em todos os projetos processados.
Gera relatório consolidado comparando diferentes algoritmos e parâmetros.

Uso:
    python run_clustering_all_projects.py
"""
from pathlib import Path
import pandas as pd
from data_preparation_clustering import prepare_class_features
from clustering_analysis import run_dbscan, run_kmeans
from cluster_validation import evaluate_saved_labels
import warnings
warnings.filterwarnings('ignore')


def find_processed_projects():
    """Retorna lista de projetos com scores processados"""
    base = Path('data/processed/coupling_scores')
    projects = []
    for p in base.iterdir():
        if p.is_dir() and (p / 'all_scores.pkl').exists():
            projects.append(p.name)
    return sorted(projects)


def process_project(project_name: str):
    """
    Processa um projeto completo: prepara features, roda clustering, valida.
    """
    print(f"\n{'='*80}")
    print(f"PROCESSANDO PROJETO: {project_name}")
    print(f"{'='*80}\n")

    results = {'project': project_name}

    try:
        # 1. Preparar features
        print("1️⃣ Preparando features por classe...")
        prepare_class_features(project_name)

        # 2. DBSCAN
        print("\n2️⃣ Executando DBSCAN...")
        dbscan_result = run_dbscan(project_name, eps=0.5, min_samples=5, save_plots=True)
        results['dbscan_clusters'] = dbscan_result['n_clusters']
        results['dbscan_silhouette'] = dbscan_result['silhouette']

        # 3. KMeans (k=3, k=5, k=7)
        for k in [3, 5, 7]:
            print(f"\n3️⃣ Executando KMeans (k={k})...")
            kmeans_result = run_kmeans(project_name, k=k, save_plots=True)
            results[f'kmeans_{k}_silhouette'] = kmeans_result['silhouette']

        print(f"\n✓ {project_name} concluído com sucesso!")
        return results

    except Exception as e:
        print(f"\n✗ Erro ao processar {project_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    projects = find_processed_projects()
    print(f"Encontrados {len(projects)} projetos processados:")
    for p in projects:
        print(f"  - {p}")

    print(f"\n{'='*80}")
    print("INICIANDO ANÁLISE DE CLUSTERING")
    print(f"{'='*80}")

    all_results = []
    for i, project in enumerate(projects, 1):
        print(f"\n[{i}/{len(projects)}]")
        result = process_project(project)
        if result:
            all_results.append(result)

    # Salva resultados consolidados
    if all_results:
        df = pd.DataFrame(all_results)
        output_file = Path('data/processed/coupling_scores/clustering_results_consolidated.csv')
        df.to_csv(output_file, index=False)
        print(f"\n{'='*80}")
        print("RELATÓRIO CONSOLIDADO")
        print(f"{'='*80}\n")
        print(df.to_string(index=False))
        print(f"\n✓ Resultados salvos em: {output_file}")

        # Estatísticas gerais
        print(f"\n{'='*80}")
        print("ESTATÍSTICAS GERAIS")
        print(f"{'='*80}\n")
        print(f"Projetos processados: {len(all_results)}")
        print(f"\nDBSCAN:")
        print(f"  Clusters médios: {df['dbscan_clusters'].mean():.1f}")
        print(f"  Silhouette médio: {df['dbscan_silhouette'].mean():.3f}")
        print(f"\nKMeans (k=5):")
        print(f"  Silhouette médio: {df['kmeans_5_silhouette'].mean():.3f}")

        # Melhor projeto por silhouette
        best_dbscan = df.loc[df['dbscan_silhouette'].idxmax()]
        print(f"\n🏆 Melhor clustering DBSCAN:")
        print(f"   Projeto: {best_dbscan['project']}")
        print(f"   Silhouette: {best_dbscan['dbscan_silhouette']:.3f}")

        best_kmeans = df.loc[df['kmeans_5_silhouette'].idxmax()]
        print(f"\n🏆 Melhor clustering KMeans (k=5):")
        print(f"   Projeto: {best_kmeans['project']}")
        print(f"   Silhouette: {best_kmeans['kmeans_5_silhouette']:.3f}")


if __name__ == '__main__':
    main()
