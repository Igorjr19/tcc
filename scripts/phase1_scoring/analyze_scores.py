"""
Script de análise rápida dos resultados de scoring.
Mostra estatísticas e identifica padrões nos scores calculados.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys


def analyze_project_scores(project_name: str):
    """Analisa os scores de um projeto específico"""
    
    scores_dir = Path(f"data/processed/coupling_scores/{project_name}")
    
    if not scores_dir.exists():
        print(f"❌ Projeto '{project_name}' não encontrado.")
        print(f"Execute primeiro: python calculate_all_scores.py")
        return
    
    print(f"\n{'='*80}")
    print(f"ANÁLISE: {project_name}")
    print(f"{'='*80}\n")
    
    # Carrega dados
    all_scores_path = scores_dir / "all_scores.csv"
    strong_couplings_path = scores_dir / "strong_couplings.csv"
    stats_path = scores_dir / "statistics.csv"
    
    if not all_scores_path.exists():
        print(f"❌ Arquivo de scores não encontrado: {all_scores_path}")
        return
    
    df_all = pd.read_csv(all_scores_path)
    df_stats = pd.read_csv(stats_path) if stats_path.exists() else None
    
    # Estatísticas gerais
    print("📊 ESTATÍSTICAS GERAIS\n")
    if df_stats is not None:
        print(f"   Total de classes: {df_stats['total_classes'].values[0]}")
        print(f"   Pares analisados: {df_stats['total_pairs'].values[0]:,}")
        print(f"   Acoplamentos fortes: {df_stats['strong_couplings'].values[0]:,} "
              f"({df_stats['strong_coupling_pct'].values[0]:.2f}%)")
    
    # Distribuição de scores
    print(f"\n📈 DISTRIBUIÇÃO DE SCORES\n")
    print(f"   Score Híbrido:")
    print(f"      Média: {df_all['hybrid_score'].mean():.3f}")
    print(f"      Mediana: {df_all['hybrid_score'].median():.3f}")
    print(f"      Desvio Padrão: {df_all['hybrid_score'].std():.3f}")
    print(f"      Min: {df_all['hybrid_score'].min():.3f}")
    print(f"      Max: {df_all['hybrid_score'].max():.3f}")
    
    print(f"\n   Score Estrutural:")
    print(f"      Média: {df_all['structural_score'].mean():.3f}")
    print(f"      Mediana: {df_all['structural_score'].median():.3f}")
    
    print(f"\n   Score Lógico:")
    print(f"      Média: {df_all['logical_score'].mean():.3f}")
    print(f"      Mediana: {df_all['logical_score'].median():.3f}")
    
    # Percentis
    print(f"\n📊 PERCENTIS (Score Híbrido)\n")
    for p in [25, 50, 75, 90, 95, 99]:
        value = np.percentile(df_all['hybrid_score'], p)
        print(f"   P{p}: {value:.3f}")
    
    # Análise de componentes
    print(f"\n🔍 ANÁLISE DE COMPONENTES\n")
    
    # Pares com apenas acoplamento estrutural
    only_structural = df_all[(df_all['structural_score'] > 0) & (df_all['logical_score'] == 0)]
    print(f"   Apenas estrutural: {len(only_structural)} ({len(only_structural)/len(df_all)*100:.1f}%)")
    
    # Pares com apenas acoplamento lógico
    only_logical = df_all[(df_all['structural_score'] == 0) & (df_all['logical_score'] > 0)]
    print(f"   Apenas lógico: {len(only_logical)} ({len(only_logical)/len(df_all)*100:.1f}%)")
    
    # Pares com ambos
    both = df_all[(df_all['structural_score'] > 0) & (df_all['logical_score'] > 0)]
    print(f"   Ambos (híbrido verdadeiro): {len(both)} ({len(both)/len(df_all)*100:.1f}%)")
    
    # Pares sem acoplamento
    none = df_all[(df_all['structural_score'] == 0) & (df_all['logical_score'] == 0)]
    print(f"   Sem acoplamento: {len(none)} ({len(none)/len(df_all)*100:.1f}%)")
    
    # Top acoplamentos
    if strong_couplings_path.exists():
        df_strong = pd.read_csv(strong_couplings_path)
        
        print(f"\n🔥 TOP 10 ACOPLAMENTOS MAIS FORTES\n")
        top10 = df_strong.nlargest(10, 'hybrid_score')
        
        for i, row in top10.iterrows():
            print(f"   {i+1}. {row['class_a']} ↔ {row['class_b']}")
            print(f"      Híbrido: {row['hybrid_score']:.3f} | "
                  f"Estrutural: {row['structural_score']:.3f} | "
                  f"Lógico: {row['logical_score']:.3f}")
            
            # Mostra se tem dependência direta
            if 'has_direct_dependency' in row and row['has_direct_dependency']:
                print(f"      ✓ Tem dependência estrutural direta")
            
            # Mostra commits se tiver
            if 'commits' in row and row['commits'] > 0:
                print(f"      ✓ Co-mudaram {int(row['commits'])} vezes")
            print()
    
    # Correlação entre componentes
    if len(both) > 0:
        correlation = df_all[['structural_score', 'logical_score']].corr().iloc[0, 1]
        print(f"\n📐 CORRELAÇÃO\n")
        print(f"   Estrutural vs Lógico: {correlation:.3f}")
        
        if correlation < 0.3:
            print(f"   → Componentes são complementares (baixa correlação)")
        elif correlation > 0.7:
            print(f"   → Componentes são redundantes (alta correlação)")
        else:
            print(f"   → Correlação moderada")


def compare_all_projects():
    """Compara estatísticas de todos os projetos"""
    
    consolidated_path = Path("data/processed/coupling_scores/consolidated_statistics.csv")
    
    if not consolidated_path.exists():
        print(f"❌ Arquivo consolidado não encontrado.")
        print(f"Execute primeiro: python calculate_all_scores.py")
        return
    
    df = pd.read_csv(consolidated_path)
    
    print(f"\n{'='*80}")
    print(f"COMPARAÇÃO ENTRE TODOS OS PROJETOS")
    print(f"{'='*80}\n")
    
    # Ordena por diferentes critérios
    print("📊 POR NÚMERO DE ACOPLAMENTOS FORTES\n")
    df_sorted = df.sort_values('strong_couplings', ascending=False)
    for i, row in df_sorted.head(10).iterrows():
        print(f"   {i+1}. {row['project']:25s} {int(row['strong_couplings']):6,} pares "
              f"({row['strong_coupling_pct']:5.2f}%)")
    
    print(f"\n📈 POR SCORE HÍBRIDO MÉDIO\n")
    df_sorted = df.sort_values('hybrid_mean', ascending=False)
    for i, row in df_sorted.head(10).iterrows():
        print(f"   {i+1}. {row['project']:25s} {row['hybrid_mean']:.3f}")
    
    print(f"\n🔧 POR SCORE ESTRUTURAL MÉDIO\n")
    df_sorted = df.sort_values('structural_mean', ascending=False)
    for i, row in df_sorted.head(10).iterrows():
        print(f"   {i+1}. {row['project']:25s} {row['structural_mean']:.3f}")
    
    print(f"\n🔄 POR SCORE LÓGICO MÉDIO\n")
    df_sorted = df.sort_values('logical_mean', ascending=False)
    for i, row in df_sorted.head(10).iterrows():
        print(f"   {i+1}. {row['project']:25s} {row['logical_mean']:.3f}")
    
    # Estatísticas gerais
    print(f"\n📊 ESTATÍSTICAS GERAIS (todos os projetos)\n")
    print(f"   Total de projetos: {len(df)}")
    print(f"   Total de classes: {df['total_classes'].sum():,}")
    print(f"   Total de pares: {df['total_pairs'].sum():,}")
    print(f"   Total de acoplamentos fortes: {df['strong_couplings'].sum():,}")
    print(f"   Percentual médio de acoplamentos fortes: {df['strong_coupling_pct'].mean():.2f}%")


def main():
    """Função principal"""
    
    if len(sys.argv) > 1:
        # Analisa projeto específico
        project = sys.argv[1]
        
        if project == "--all":
            compare_all_projects()
        else:
            analyze_project_scores(project)
    else:
        # Mostra comparação geral
        print("USO:")
        print("  python analyze_scores.py <projeto>    # Analisa projeto específico")
        print("  python analyze_scores.py --all         # Compara todos os projetos")
        print()
        compare_all_projects()


if __name__ == "__main__":
    main()
