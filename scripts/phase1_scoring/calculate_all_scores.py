"""
Script para calcular scores de acoplamento para TODOS os projetos disponíveis.
"""

from coupling_scoring import CouplingScorer
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import pickle


def load_scores_from_pickle(project_name: str, output_dir: Path):
    """
    Carrega scores de um projeto a partir do arquivo pickle.
    
    Args:
        project_name: Nome do projeto
        output_dir: Diretório base de saída
        
    Returns:
        Lista de DependencyScore ou None se não existir
    """
    pickle_file = output_dir / project_name / "all_scores.pkl"
    if pickle_file.exists():
        with open(pickle_file, 'rb') as f:
            return pickle.load(f)
    return None


def process_project(project_name: str, output_dir: Path, max_classes: int = None, force_reprocess: bool = False) -> dict:
    """
    Processa um projeto completo e retorna estatísticas.
    
    Args:
        project_name: Nome do projeto
        output_dir: Diretório de saída
        max_classes: Número máximo de classes a processar (None = todas)
        force_reprocess: Se True, reprocessa mesmo se já existir
    
    Returns:
        dict com estatísticas do projeto ou None se houver erro
    """
    print(f"\n{'='*80}")
    print(f"PROCESSANDO: {project_name}")
    print(f"{'='*80}\n")
    
    # Verifica se já foi processado
    project_output_dir = output_dir / project_name
    statistics_file = project_output_dir / "statistics.csv"
    pickle_file = project_output_dir / "all_scores.pkl"
    
    if statistics_file.exists() and pickle_file.exists() and not force_reprocess:
        print(f"✓ Projeto já processado! Carregando estatísticas...")
        try:
            stats_df = pd.read_csv(statistics_file)
            stats = stats_df.to_dict('records')[0]
            print(f"   Classes: {stats['total_classes']}")
            print(f"   Pares: {stats['total_pairs']:,}")
            print(f"   Acoplamentos fortes: {stats['strong_couplings']}")
            return stats
        except Exception as e:
            print(f"⚠️  Erro ao carregar estatísticas: {e}. Reprocessando...")
    
    # Define caminhos
    metrics_path = f"data/raw/metrics/{project_name}_metrics.csv"
    dependencies_path = f"data/raw/dependencies/{project_name}_dependencies.csv"
    co_changes_path = f"data/raw/co_changes/{project_name}_co_changes.csv"
    
    # Verifica arquivos
    if not Path(metrics_path).exists():
        print(f"❌ Métricas não encontradas. Pulando projeto.")
        return None
    
    has_dependencies = Path(dependencies_path).exists()
    has_co_changes = Path(co_changes_path).exists()
    
    if not has_dependencies:
        dependencies_path = None
    if not has_co_changes:
        co_changes_path = None
    
    try:
        # Inicializa scorer
        scorer = CouplingScorer(
            structural_weight=0.5,
            logical_weight=0.5,
            coupling_threshold=0.7
        )
        
        # Carrega dados
        scorer.load_data(
            metrics_path=metrics_path,
            dependencies_path=dependencies_path,
            co_changes_path=co_changes_path
        )
        
        # Calcula scores para as classes do projeto
        print(f"\n⚙️  Calculando scores...")
        # Intervalo de progresso adaptativo baseado no tamanho
        num_classes = len(scorer.metrics_df) if max_classes is None else min(max_classes, len(scorer.metrics_df))
        progress_interval = max(10000, num_classes * 10)  # Mostra progresso a cada ~10K pares
        
        # Cria diretório de saída ANTES do processamento
        project_output_dir = output_dir / project_name
        project_output_dir.mkdir(parents=True, exist_ok=True)
        
        scores = scorer.calculate_all_scores(max_classes=max_classes, progress_interval=progress_interval)
        
        if not scores:
            print(f"❌ Nenhum score calculado.")
            return None
        
        # SALVA IMEDIATAMENTE após calcular
        print(f"\n💾 Salvando scores...")
        
        # Salva em formato pickle (mais rápido e compacto)
        import pickle
        with open(project_output_dir / "all_scores.pkl", 'wb') as f:
            pickle.dump(scores, f)
        print(f"✓ Scores salvos em formato pickle (rápido e compacto)")
        
        # Salva apenas scores não-zero em CSV (para análise manual)
        print(f"� Gerando CSV com scores relevantes...")
        relevant_scores = [s for s in scores if s.hybrid_score > 0]
        if relevant_scores:
            scorer.export_scores(relevant_scores, str(project_output_dir / "relevant_scores.csv"))
            print(f"✓ {len(relevant_scores):,} scores relevantes salvos em CSV")
        else:
            print(f"⚠️  Nenhum score relevante encontrado")
        
        # Obtém e exporta acoplamentos fortes
        print(f"🔍 Identificando acoplamentos fortes...")
        strong_couplings = scorer.get_strongly_coupled_classes(scores)
        
        if not strong_couplings.empty:
            strong_couplings.to_csv(
                project_output_dir / "strong_couplings.csv",
                index=False
            )
            print(f"✓ {len(strong_couplings)} acoplamentos fortes identificados")
        
        # Calcula estatísticas ANTES de liberar memória
        print(f"📊 Calculando estatísticas...")
        hybrid_scores = [s.hybrid_score for s in scores]
        structural_scores = [s.structural_score for s in scores]
        logical_scores = [s.logical_score for s in scores]
        
        stats = {
            'project': project_name,
            'total_classes': len(scorer.metrics_df),
            'total_pairs': len(scores),
            'strong_couplings': len(strong_couplings),
            'strong_coupling_pct': len(strong_couplings) / len(scores) * 100 if scores else 0,
            'hybrid_mean': np.mean(hybrid_scores),
            'hybrid_median': np.median(hybrid_scores),
            'hybrid_std': np.std(hybrid_scores),
            'hybrid_min': np.min(hybrid_scores),
            'hybrid_max': np.max(hybrid_scores),
            'structural_mean': np.mean(structural_scores),
            'logical_mean': np.mean(logical_scores),
            'has_dependencies': has_dependencies,
            'has_co_changes': has_co_changes
        }
        
        # Salva estatísticas do projeto
        stats_df = pd.DataFrame([stats])
        stats_df.to_csv(project_output_dir / "statistics.csv", index=False)
        print(f"✓ Estatísticas salvas")
        
        # Mostra resumo
        print(f"\n📊 RESUMO DO PROJETO:")
        print(f"   Total de classes: {stats['total_classes']}")
        print(f"   Pares analisados: {stats['total_pairs']:,}")
        print(f"   Acoplamentos fortes: {stats['strong_couplings']} ({stats['strong_coupling_pct']:.2f}%)")
        print(f"   Score híbrido médio: {stats['hybrid_mean']:.3f}")
        print(f"   Score estrutural médio: {stats['structural_mean']:.3f}")
        print(f"   Score lógico médio: {stats['logical_mean']:.3f}")
        
        # Libera memória
        del scores
        del hybrid_scores
        del structural_scores
        del logical_scores
        del scorer
        import gc
        gc.collect()
        print(f"✓ Memória liberada")
        
        return stats
        
    except Exception as e:
        print(f"❌ Erro ao processar projeto: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Processa todos os projetos disponíveis"""
    
    # Mostra informações de memória disponível (se psutil estiver instalado)
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"💾 MEMÓRIA DISPONÍVEL: {memory.available / (1024**3):.1f} GB de {memory.total / (1024**3):.1f} GB")
        print(f"   Uso atual: {memory.percent}%\n")
    except ImportError:
        pass
    
    # Configuração: limite de classes por projeto (None = sem limite)
    # Com otimização de índices, agora é viável processar TODAS as classes!
    # Exemplos: 100 classes = ~5K pares, 200 = ~20K pares, 500 = ~125K pares
    # ATENÇÃO: Projetos grandes (Spring) podem usar ~8-10GB de RAM durante o processamento
    
    # Adaptação automática baseada em memória disponível
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        if available_gb < 8:
            # Memória baixa: limita processamento
            MAX_CLASSES_PER_PROJECT = 1000
            print(f"⚠️  MEMÓRIA BAIXA ({available_gb:.1f}GB): Limitando a {MAX_CLASSES_PER_PROJECT} classes")
        else:
            # Memória suficiente: sem limites
            MAX_CLASSES_PER_PROJECT = None
    except ImportError:
        # Se não tiver psutil, usa limite conservador
        MAX_CLASSES_PER_PROJECT = 1000
        print(f"⚠️  psutil não instalado: Usando limite conservador de {MAX_CLASSES_PER_PROJECT} classes")
    
    if MAX_CLASSES_PER_PROJECT:
        print(f"⚠️  MODO LIMITADO: Processando no máximo {MAX_CLASSES_PER_PROJECT} classes por projeto")
        print(f"    Para processar todas as classes, defina MAX_CLASSES_PER_PROJECT = None\n")
    else:
        print(f"🚀 MODO COMPLETO: Processando TODAS as classes de cada projeto")
        print(f"   (Otimização com índices ativada para máxima performance)")
        print(f"   ⚠️  Projetos grandes podem usar até 10GB de RAM\n")
    
    # Lista de projetos
    projects = [
        "spring-framework",
        "spring-boot",
        "junit4",
        "mockito",
        "guava",
        "commons-lang",
        "commons-collections",
        "commons-io",
        "commons-text",
        "commons-math",
        "dbeaver",
        "assertj-core",
        "gson"
    ]
    
    # Diretório de saída
    output_dir = Path("data/processed/coupling_scores")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Processa cada projeto
    all_stats = []
    successful = 0
    failed = 0
    
    start_time = datetime.now()
    
    for i, project in enumerate(projects, 1):
        print(f"\n{'#'*80}")
        print(f"# PROJETO {i}/{len(projects)}")
        print(f"{'#'*80}")
        
        project_start = datetime.now()
        try:
            stats = process_project(
                project, 
                output_dir, 
                max_classes=MAX_CLASSES_PER_PROJECT,
                force_reprocess=False  # Não reprocessa se já existe
            )
            project_duration = (datetime.now() - project_start).total_seconds()
            
            if stats:
                all_stats.append(stats)
                successful += 1
                print(f"\n✓ {project} concluído em {project_duration:.1f}s")
            else:
                failed += 1
                print(f"\n✗ {project} falhou")
        except Exception as e:
            failed += 1
            print(f"\n✗ {project} falhou com erro: {e}")
            import traceback
            traceback.print_exc()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Salva estatísticas consolidadas
    if all_stats:
        consolidated_df = pd.DataFrame(all_stats)
        consolidated_df.to_csv(output_dir / "consolidated_statistics.csv", index=False)
        
        # Relatório final
        print(f"\n{'='*80}")
        print(f"RELATÓRIO FINAL")
        print(f"{'='*80}\n")
        print(f"⏱️  Tempo total: {duration:.1f}s")
        print(f"✓ Projetos processados com sucesso: {successful}")
        print(f"❌ Projetos com erro: {failed}")
        print(f"\n📊 COMPARAÇÃO ENTRE PROJETOS:\n")
        
        # Ordena por número de acoplamentos fortes
        consolidated_df_sorted = consolidated_df.sort_values('strong_couplings', ascending=False)
        
        print(consolidated_df_sorted[[
            'project', 
            'total_classes', 
            'strong_couplings',
            'strong_coupling_pct',
            'hybrid_mean'
        ]].to_string(index=False))
        
        print(f"\n✓ Resultados salvos em: {output_dir}")
        print(f"✓ Estatísticas consolidadas: {output_dir}/consolidated_statistics.csv")
        
        # Identifica projetos com maior acoplamento
        print(f"\n🔥 TOP 5 PROJETOS COM MAIS ACOPLAMENTOS FORTES:")
        for i, row in consolidated_df_sorted.head(5).iterrows():
            print(f"   {i+1}. {row['project']}: {row['strong_couplings']} pares ({row['strong_coupling_pct']:.1f}%)")
    
    else:
        print(f"\n❌ Nenhum projeto foi processado com sucesso.")


if __name__ == "__main__":
    main()
