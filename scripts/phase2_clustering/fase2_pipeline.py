"""
Pipeline completo da Fase 2 - Clustering e Análise de Padrões.

Executa todas as etapas em sequência:
1. Clustering batch (todos os projetos)
2. Análise comparativa entre projetos
3. Visualizações avançadas para projetos selecionados
4. Interpretação de clusters para top projetos

Uso:
    python fase2_pipeline.py [--skip-clustering] [--top N]
    
Opções:
    --skip-clustering: Pula etapa de clustering (usa resultados existentes)
    --top N: Gera visualizações para os N melhores projetos (padrão: 3)
"""
import sys
import subprocess
from pathlib import Path
import pandas as pd


def run_step(title: str, command: list, skip: bool = False):
    """Executa uma etapa do pipeline"""
    print("\n" + "="*80)
    print(f"ETAPA: {title}")
    print("="*80)
    
    if skip:
        print(f"⏭️  Pulando esta etapa...")
        return True
    
    try:
        result = subprocess.run(command, check=True, capture_output=False, text=True)
        print(f"\n✓ {title} concluído com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro em {title}")
        print(f"   Comando: {' '.join(command)}")
        print(f"   Código de saída: {e.returncode}")
        return False


def get_top_projects(n: int = 3):
    """Identifica os N projetos com melhor qualidade de clustering"""
    results_file = Path('data/processed/coupling_scores/clustering_results_consolidated.csv')
    
    if not results_file.exists():
        print("⚠️  Arquivo de resultados não encontrado. Usando projetos padrão.")
        return ['spring-framework', 'spring-boot', 'guava']
    
    df = pd.read_csv(results_file)
    
    # Para cada projeto, pega o melhor silhouette
    best_per_project = df.loc[df.groupby('project')['silhouette'].idxmax()]
    top_projects = best_per_project.nlargest(n, 'silhouette')['project'].tolist()
    
    print(f"\n📊 Top {n} projetos identificados:")
    for i, proj in enumerate(top_projects, 1):
        score = best_per_project[best_per_project['project'] == proj]['silhouette'].values[0]
        print(f"   {i}. {proj:25} (Silhouette: {score:.3f})")
    
    return top_projects


def main():
    skip_clustering = '--skip-clustering' in sys.argv
    
    # Determina número de projetos top
    top_n = 3
    if '--top' in sys.argv:
        idx = sys.argv.index('--top')
        if idx + 1 < len(sys.argv):
            try:
                top_n = int(sys.argv[idx + 1])
            except ValueError:
                print("⚠️  Valor inválido para --top, usando padrão (3)")
    
    print("\n" + "="*80)
    print("PIPELINE COMPLETO - FASE 2: CLUSTERING E PADRÕES")
    print("="*80)
    print(f"\nConfiguração:")
    print(f"  - Executar clustering: {'NÃO' if skip_clustering else 'SIM'}")
    print(f"  - Top projetos para análise detalhada: {top_n}")
    
    python = str(Path('.venv/bin/python'))
    
    # ETAPA 1: Clustering batch
    if not run_step(
        "1/4 - Clustering em Todos os Projetos",
        [python, 'run_clustering_all_projects.py'],
        skip=skip_clustering
    ):
        print("\n❌ Pipeline interrompido devido a erro.")
        return 1
    
    # ETAPA 2: Análise comparativa
    if not run_step(
        "2/4 - Análise Comparativa Entre Projetos",
        [python, 'cross_project_analysis.py']
    ):
        print("\n⚠️  Continuando apesar do erro...")
    
    # ETAPA 3: Visualizações avançadas para top projetos
    print("\n" + "="*80)
    print(f"ETAPA: 3/4 - Visualizações Avançadas (Top {top_n})")
    print("="*80)
    
    top_projects = get_top_projects(top_n)
    
    for i, project in enumerate(top_projects, 1):
        print(f"\n[{i}/{len(top_projects)}] Gerando visualizações: {project}")
        run_step(
            f"Visualizações - {project}",
            [python, 'visualize_clusters.py', project, 'dbscan']
        )
    
    # ETAPA 4: Interpretação detalhada
    print("\n" + "="*80)
    print(f"ETAPA: 4/4 - Interpretação de Clusters (Top {top_n})")
    print("="*80)
    
    for i, project in enumerate(top_projects, 1):
        print(f"\n[{i}/{len(top_projects)}] Interpretando clusters: {project}")
        run_step(
            f"Interpretação - {project}",
            [python, 'cluster_interpretation.py', project, 'dbscan']
        )
    
    # RESUMO FINAL
    print("\n" + "="*80)
    print("✓ PIPELINE COMPLETO CONCLUÍDO!")
    print("="*80)
    
    print("\n📁 Arquivos gerados:")
    print("   - data/processed/coupling_scores/clustering_results_consolidated.csv")
    print("   - results/clustering_executive_summary.txt")
    print("   - results/plots/clustering_comparison_heatmap.png")
    print("   - results/plots/clustering_distribution.png")
    
    for project in top_projects:
        print(f"   - data/processed/coupling_scores/{project}/*_distributions.png")
        print(f"   - data/processed/coupling_scores/{project}/*_heatmap.png")
        print(f"   - data/processed/coupling_scores/{project}/clustering_comparison.png")
        print(f"   - data/processed/coupling_scores/{project}/dbscan_analysis.txt")
    
    print("\n📝 Próximos passos sugeridos:")
    print("   1. Revisar: results/clustering_executive_summary.txt")
    print("   2. Analisar gráficos em: results/plots/")
    print("   3. Estudar clusters de projetos específicos em: data/processed/coupling_scores/<projeto>/")
    print("   4. Documentar insights para o TCC")
    
    return 0


if __name__ == '__main__':
    exit(main())
