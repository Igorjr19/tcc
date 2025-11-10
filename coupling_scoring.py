"""
Sistema de Scoring de Acoplamento
==================================
Combina métricas estruturais (CK metrics) e lógicas (co-changes) 
para calcular um score híbrido de acoplamento entre classes.

Baseado na dissertação de Gustavo Oliva que mostra que:
- 91% das dependências lógicas não têm contrapartida estrutural
- 95% das dependências estruturais não resultam em dependências lógicas
- Portanto, ambas as métricas são complementares, não redundantes
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DependencyScore:
    """Representa o score de dependência entre duas classes"""
    class_a: str
    class_b: str
    structural_score: float
    logical_score: float
    hybrid_score: float
    is_strong_coupling: bool
    metrics: Dict[str, float]


class CouplingScorer:
    """
    Calcula scores de acoplamento entre classes usando abordagem híbrida.
    """
    
    def __init__(self, 
                 structural_weight: float = 0.5,
                 logical_weight: float = 0.5,
                 coupling_threshold: float = 0.7):
        """
        Inicializa o scorer com pesos configuráveis.
        
        Args:
            structural_weight: Peso da componente estrutural (0-1)
            logical_weight: Peso da componente lógica (0-1)
            coupling_threshold: Limiar para considerar acoplamento forte (0-1)
        """
        if not np.isclose(structural_weight + logical_weight, 1.0):
            raise ValueError("A soma dos pesos deve ser 1.0")
        
        self.structural_weight = structural_weight
        self.logical_weight = logical_weight
        self.coupling_threshold = coupling_threshold
        
        self.metrics_df = None
        self.dependencies_df = None
        self.co_changes_df = None
        
    def load_data(self, 
                  metrics_path: str,
                  dependencies_path: Optional[str] = None,
                  co_changes_path: Optional[str] = None):
        """
        Carrega os dados de métricas, dependências e co-changes.
        
        Args:
            metrics_path: Caminho para o CSV com métricas CK
            dependencies_path: Caminho para o CSV com dependências estruturais
            co_changes_path: Caminho para o CSV com co-changes
        """
        self.metrics_df = pd.read_csv(metrics_path)
        
        # Normaliza nomes das colunas de métricas
        # Formato esperado: Classe,CBO,DIT,LCOM,RFC
        if 'Classe' in self.metrics_df.columns:
            self.metrics_df.rename(columns={
                'Classe': 'class',
                'CBO': 'cbo',
                'DIT': 'dit',
                'LCOM': 'lcom',
                'RFC': 'rfc'
            }, inplace=True)
        
        # Cria índice de métricas para busca O(1) ao invés de O(n)
        self.metrics_dict = self.metrics_df.set_index('class').to_dict('index')
        
        if dependencies_path:
            self.dependencies_df = pd.read_csv(dependencies_path)
            # Normaliza nomes das colunas de dependências
            # Formato esperado: Classe1,Classe2,DependenciaExplicita
            if 'Classe1' in self.dependencies_df.columns:
                self.dependencies_df.rename(columns={
                    'Classe1': 'source',
                    'Classe2': 'target',
                    'DependenciaExplicita': 'explicit'
                }, inplace=True)
            
            # Cria set de pares de dependências para busca O(1)
            # Usa itertuples ao invés de iterrows (50-100x mais rápido)
            self.dependencies_set = set()
            for row in self.dependencies_df.itertuples(index=False):
                self.dependencies_set.add((row.source, row.target))
                self.dependencies_set.add((row.target, row.source))  # bidirecional
            print(f"   → {len(self.dependencies_set)} pares indexados")
        
        if co_changes_path:
            self.co_changes_df = pd.read_csv(co_changes_path)
            # Normaliza nomes das colunas de co-changes
            # Formato esperado: Classe1,Classe2,FrequenciaCoMudanca
            if 'Classe1' in self.co_changes_df.columns:
                self.co_changes_df.rename(columns={
                    'Classe1': 'file1',
                    'Classe2': 'file2',
                    'FrequenciaCoMudanca': 'commits'
                }, inplace=True)
                
                # Calcula support e confidence se não existirem
                if 'support' not in self.co_changes_df.columns:
                    max_commits = self.co_changes_df['commits'].max()
                    self.co_changes_df['support'] = self.co_changes_df['commits'] / max_commits
                
                if 'confidence' not in self.co_changes_df.columns:
                    # Confidence = frequência relativa
                    self.co_changes_df['confidence'] = self.co_changes_df['support']
            
            # Cria dicionário de co-changes para busca O(1)
            # Usa itertuples ao invés de iterrows (50-100x mais rápido)
            self.co_changes_dict = {}
            for row in self.co_changes_df.itertuples(index=False):
                key1 = (row.file1, row.file2)
                key2 = (row.file2, row.file1)  # bidirecional
                data = {
                    'support': row.support,
                    'confidence': row.confidence,
                    'commits': row.commits
                }
                self.co_changes_dict[key1] = data
                self.co_changes_dict[key2] = data
            print(f"   → {len(self.co_changes_dict)} pares indexados")
            
        print(f"✓ Métricas carregadas: {len(self.metrics_df)} classes")
        if self.dependencies_df is not None:
            print(f"✓ Dependências carregadas: {len(self.dependencies_df)} pares")
        if self.co_changes_df is not None:
            print(f"✓ Co-changes carregados: {len(self.co_changes_df)} pares")
        print(f"✓ Índices otimizados criados para busca rápida")
    
    def calculate_structural_score(self, class_a: str, class_b: str) -> Tuple[float, Dict]:
        """
        Calcula score estrutural baseado em métricas CK.
        
        Utiliza:
        - CBO (Coupling Between Objects): acoplamento direto
        - RFC (Response For Class): complexidade de interação
        - DIT (Depth of Inheritance Tree): hierarquia
        - LCOM (Lack of Cohesion): coesão (inverso)
        
        Returns:
            Tuple[float, Dict]: Score normalizado (0-1) e dicionário com métricas
        """
        if not hasattr(self, 'metrics_dict'):
            raise ValueError("Dados não carregados. Use load_data() primeiro.")
        
        # Busca métricas usando dicionário (O(1) ao invés de O(n))
        metrics_a = self.metrics_dict.get(class_a)
        metrics_b = self.metrics_dict.get(class_b)
        
        if metrics_a is None or metrics_b is None:
            return 0.0, {}
        
        # Extrai métricas relevantes
        cbo_a = metrics_a.get('cbo', 0)
        cbo_b = metrics_b.get('cbo', 0)
        
        rfc_a = metrics_a.get('rfc', 0)
        rfc_b = metrics_b.get('rfc', 0)
        
        dit_a = metrics_a.get('dit', 0)
        dit_b = metrics_b.get('dit', 0)
        
        # Verifica se existe dependência estrutural direta usando set (O(1))
        has_dependency = False
        if hasattr(self, 'dependencies_set'):
            has_dependency = (class_a, class_b) in self.dependencies_set
        
        # Calcula score estrutural
        # Normaliza métricas (valores típicos: CBO 0-50, RFC 0-100, DIT 0-10)
        cbo_score = min((cbo_a + cbo_b) / 100.0, 1.0)
        rfc_score = min((rfc_a + rfc_b) / 200.0, 1.0)
        dit_score = min(abs(dit_a - dit_b) / 10.0, 1.0)  # Diferença na hierarquia
        
        # Score base das métricas (média ponderada)
        base_score = (cbo_score * 0.5 + rfc_score * 0.3 + dit_score * 0.2)
        
        # Boost se existe dependência direta
        if has_dependency:
            base_score = min(base_score * 1.5, 1.0)
        
        metrics_dict = {
            'cbo_a': cbo_a,
            'cbo_b': cbo_b,
            'rfc_a': rfc_a,
            'rfc_b': rfc_b,
            'dit_a': dit_a,
            'dit_b': dit_b,
            'has_direct_dependency': has_dependency
        }
        
        return base_score, metrics_dict
    
    def calculate_logical_score(self, class_a: str, class_b: str) -> Tuple[float, Dict]:
        """
        Calcula score lógico baseado em co-changes (mining do repositório).
        
        Utiliza:
        - Support: frequência de co-mudança
        - Confidence: probabilidade condicional
        - Número de commits em que co-mudaram
        
        Returns:
            Tuple[float, Dict]: Score normalizado (0-1) e dicionário com métricas
        """
        if not hasattr(self, 'co_changes_dict'):
            return 0.0, {'support': 0, 'confidence': 0, 'commits': 0}
        
        # Busca co-change usando dicionário (O(1) ao invés de O(n))
        co_change_data = self.co_changes_dict.get((class_a, class_b))
        
        if co_change_data is None:
            return 0.0, {'support': 0, 'confidence': 0, 'commits': 0}
        
        # Extrai métricas de co-change
        support = co_change_data.get('support', 0)
        confidence = co_change_data.get('confidence', 0)
        commits = co_change_data.get('commits', 0)
        
        # Score lógico: média ponderada de support e confidence
        # Support indica frequência, confidence indica força da relação
        logical_score = (support * 0.4 + confidence * 0.6)
        
        # Boost baseado no número de commits
        if commits > 10:
            logical_score = min(logical_score * 1.3, 1.0)
        elif commits > 5:
            logical_score = min(logical_score * 1.15, 1.0)
        
        metrics_dict = {
            'support': support,
            'confidence': confidence,
            'commits': commits
        }
        
        return logical_score, metrics_dict
    
    def calculate_hybrid_score(self, class_a: str, class_b: str) -> DependencyScore:
        """
        Calcula score híbrido combinando componentes estrutural e lógica.
        
        Args:
            class_a: Nome da primeira classe
            class_b: Nome da segunda classe
            
        Returns:
            DependencyScore: Objeto com todos os scores e métricas
        """
        # Calcula componentes
        structural_score, structural_metrics = self.calculate_structural_score(class_a, class_b)
        logical_score, logical_metrics = self.calculate_logical_score(class_a, class_b)
        
        # Score híbrido: média ponderada
        hybrid_score = (
            self.structural_weight * structural_score + 
            self.logical_weight * logical_score
        )
        
        # Determina se é acoplamento forte
        is_strong = hybrid_score >= self.coupling_threshold
        
        # Combina todas as métricas
        all_metrics = {
            **structural_metrics,
            **logical_metrics
        }
        
        return DependencyScore(
            class_a=class_a,
            class_b=class_b,
            structural_score=structural_score,
            logical_score=logical_score,
            hybrid_score=hybrid_score,
            is_strong_coupling=is_strong,
            metrics=all_metrics
        )
    
    def calculate_all_scores(self, class_list: Optional[List[str]] = None, 
                            max_classes: Optional[int] = None,
                            progress_interval: int = 1000) -> List[DependencyScore]:
        """
        Calcula scores para todas as combinações de classes.
        
        Args:
            class_list: Lista de classes para analisar. Se None, usa todas do dataset.
            max_classes: Limite máximo de classes (para amostras). Se None, usa todas.
            progress_interval: Intervalo de pares para mostrar progresso
            
        Returns:
            List[DependencyScore]: Lista com todos os scores calculados
        """
        if self.metrics_df is None:
            raise ValueError("Dados não carregados. Use load_data() primeiro.")
        
        if class_list is None:
            class_list = self.metrics_df['class'].unique().tolist()
        
        # Limita número de classes se especificado
        if max_classes and len(class_list) > max_classes:
            print(f"⚠️  Limitando análise a {max_classes} classes (de {len(class_list)} totais)")
            class_list = class_list[:max_classes]
        
        scores = []
        total_pairs = len(class_list) * (len(class_list) - 1) // 2
        
        print(f"Calculando scores para {len(class_list)} classes ({total_pairs:,} pares)...")
        
        # Importa tqdm se disponível
        try:
            from tqdm import tqdm
            use_tqdm = True
        except ImportError:
            use_tqdm = False
        
        pairs_processed = 0
        last_progress = 0
        
        if use_tqdm:
            # Usa barra de progresso
            with tqdm(total=total_pairs, desc="Processando", unit="pares") as pbar:
                for i, class_a in enumerate(class_list):
                    for class_b in class_list[i+1:]:
                        score = self.calculate_hybrid_score(class_a, class_b)
                        scores.append(score)
                        pairs_processed += 1
                        pbar.update(1)
        else:
            # Usa logs periódicos
            for i, class_a in enumerate(class_list):
                for class_b in class_list[i+1:]:
                    score = self.calculate_hybrid_score(class_a, class_b)
                    scores.append(score)
                    pairs_processed += 1
                    
                    # Mostra progresso a cada N pares
                    if pairs_processed - last_progress >= progress_interval:
                        progress_pct = (pairs_processed / total_pairs) * 100
                        print(f"   Progresso: {pairs_processed:,}/{total_pairs:,} pares ({progress_pct:.1f}%) - "
                              f"Classes processadas: {i+1}/{len(class_list)}")
                        last_progress = pairs_processed
        
        print(f"✓ {len(scores)} scores calculados")
        return scores
    
    def get_strongly_coupled_classes(self, 
                                    scores: List[DependencyScore],
                                    top_n: Optional[int] = None) -> pd.DataFrame:
        """
        Retorna as classes com acoplamento forte.
        
        Args:
            scores: Lista de scores calculados
            top_n: Se especificado, retorna apenas os top N pares mais acoplados
            
        Returns:
            DataFrame com pares fortemente acoplados ordenados por score
        """
        # Filtra acoplamentos fortes
        strong_couplings = [s for s in scores if s.is_strong_coupling]
        
        # Converte para DataFrame
        df = pd.DataFrame([
            {
                'class_a': s.class_a,
                'class_b': s.class_b,
                'hybrid_score': s.hybrid_score,
                'structural_score': s.structural_score,
                'logical_score': s.logical_score,
                **s.metrics
            }
            for s in strong_couplings
        ])
        
        # Ordena por score híbrido
        if not df.empty:
            df = df.sort_values('hybrid_score', ascending=False)
        
        if top_n:
            df = df.head(top_n)
        
        return df
    
    def export_scores(self, scores: List[DependencyScore], output_path: str, batch_size: int = 50000):
        """
        Exporta scores calculados para CSV em batches para economizar memória.
        
        Args:
            scores: Lista de scores para exportar
            output_path: Caminho do arquivo CSV de saída
            batch_size: Número de scores por batch (para economia de memória)
        """
        import csv
        from pathlib import Path
        
        # Cria diretório se não existir
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Se for pequeno, exporta diretamente
        if len(scores) < batch_size:
            df = pd.DataFrame([
                {
                    'class_a': s.class_a,
                    'class_b': s.class_b,
                    'hybrid_score': s.hybrid_score,
                    'structural_score': s.structural_score,
                    'logical_score': s.logical_score,
                    'is_strong_coupling': s.is_strong_coupling,
                    **s.metrics
                }
                for s in scores
            ])
            df.to_csv(output_path, index=False)
        else:
            # Exporta em batches para economizar memória
            first_batch = True
            for i in range(0, len(scores), batch_size):
                batch = scores[i:i+batch_size]
                df_batch = pd.DataFrame([
                    {
                        'class_a': s.class_a,
                        'class_b': s.class_b,
                        'hybrid_score': s.hybrid_score,
                        'structural_score': s.structural_score,
                        'logical_score': s.logical_score,
                        'is_strong_coupling': s.is_strong_coupling,
                        **s.metrics
                    }
                    for s in batch
                ])
                
                # Primeira vez: cria arquivo com header
                # Depois: append sem header
                df_batch.to_csv(
                    output_path, 
                    mode='w' if first_batch else 'a',
                    header=first_batch,
                    index=False
                )
                first_batch = False
                
                # Libera memória do batch
                del df_batch
        
        print(f"✓ Scores exportados para {output_path}")


def main():
    """Exemplo de uso do CouplingScorer"""
    
    # Configura caminhos (ajuste conforme sua estrutura)
    project_name = "spring-framework"  # exemplo
    
    metrics_path = f"data/raw/metrics/{project_name}_metrics.csv"
    dependencies_path = f"data/raw/dependencies/{project_name}_dependencies.csv"
    co_changes_path = f"data/raw/co_changes/{project_name}_co_changes.csv"
    
    # Inicializa scorer
    scorer = CouplingScorer(
        structural_weight=0.5,
        logical_weight=0.5,
        coupling_threshold=0.7
    )
    
    # Carrega dados
    try:
        scorer.load_data(
            metrics_path=metrics_path,
            dependencies_path=dependencies_path,
            co_changes_path=co_changes_path
        )
    except FileNotFoundError as e:
        print(f"❌ Erro ao carregar dados: {e}")
        print("Ajuste os caminhos dos arquivos no código.")
        return
    
    # Calcula scores para todas as classes
    scores = scorer.calculate_all_scores()
    
    # Obtém acoplamentos fortes
    strong_couplings = scorer.get_strongly_coupled_classes(scores, top_n=20)
    
    print("\n" + "="*80)
    print("TOP 20 ACOPLAMENTOS FORTES")
    print("="*80)
    print(strong_couplings[['class_a', 'class_b', 'hybrid_score', 
                             'structural_score', 'logical_score']].to_string(index=False))
    
    # Exporta resultados
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    scorer.export_scores(scores, f"data/processed/{project_name}_coupling_scores.csv")
    strong_couplings.to_csv(f"data/processed/{project_name}_strong_couplings.csv", index=False)
    
    # Estatísticas
    print("\n" + "="*80)
    print("ESTATÍSTICAS")
    print("="*80)
    print(f"Total de pares analisados: {len(scores)}")
    print(f"Acoplamentos fortes: {len(strong_couplings)} ({len(strong_couplings)/len(scores)*100:.1f}%)")
    print(f"Score híbrido médio: {np.mean([s.hybrid_score for s in scores]):.3f}")
    print(f"Score estrutural médio: {np.mean([s.structural_score for s in scores]):.3f}")
    print(f"Score lógico médio: {np.mean([s.logical_score for s in scores]):.3f}")


if __name__ == "__main__":
    main()
