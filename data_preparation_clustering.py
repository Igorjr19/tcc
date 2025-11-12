"""
Prepara features por CLASSE a partir dos scores calculados (pickle) ou CSVs relevantes.
Gera um CSV com features agregadas por classe pronto para clustering.

Saídas (por projeto):
- data/processed/coupling_scores/<project>/class_features.csv
- data/processed/coupling_scores/<project>/class_features_scaled.pkl (StandardScaler + np.array)

Uso:
    from data_preparation_clustering import prepare_class_features
    prepare_class_features('spring-framework')
"""

from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from coupling_scoring import DependencyScore, CouplingScorer
import pickle
import warnings


def load_scores(project_name: str, base_dir: Path = Path('data/processed/coupling_scores')):
    project_dir = base_dir / project_name
    pickle_file = project_dir / 'all_scores.pkl'
    csv_file = project_dir / 'all_scores.csv'

    if pickle_file.exists():
        with open(pickle_file, 'rb') as f:
            scores = pickle.load(f)
        return scores
    elif csv_file.exists():
        # fallback: read CSV and create DependencyScore-like dicts
        df = pd.read_csv(csv_file)
        scores = []
        for _, r in df.iterrows():
            ds = DependencyScore(
                class_a=r['class_a'],
                class_b=r['class_b'],
                structural_score=r.get('structural_score', 0.0),
                logical_score=r.get('logical_score', 0.0),
                hybrid_score=r.get('hybrid_score', 0.0),
                is_strong_coupling=bool(r.get('is_strong_coupling', False)),
                metrics={k: r[k] for k in r.index if k not in ['class_a','class_b','structural_score','logical_score','hybrid_score','is_strong_coupling']}
            )
            scores.append(ds)
        return scores
    else:
        return None


def prepare_class_features(project_name: str, base_dir: Path = Path('data/processed/coupling_scores')) -> Path:
    """
    Gera features agregadas por classe para clustering.

    Features geradas (por classe):
    - cbo, rfc, dit, lcom (quando disponível nos arquivos de métricas)
    - degree_pairs: número de pares envolvendo a classe
    - avg_hybrid, max_hybrid, median_hybrid
    - avg_structural, avg_logical
    - count_strong (hybrid >= threshold)
    - pct_strong
    - sum_support, max_support, avg_commits

    Retorna o caminho do CSV gerado.
    """
    base_dir = Path(base_dir)
    project_dir = base_dir / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    print(f"Carregando scores para projeto: {project_name}")
    scores = load_scores(project_name, base_dir=base_dir)
    if scores is None:
        raise FileNotFoundError(f"Nenhum arquivo de scores encontrado para {project_name} em {project_dir}")

    print(f"Total de pares carregados: {len(scores):,}")

    # Carrega métricas por classe usando CouplingScorer (apenas para extrair métricas por classe)
    metrics_path = Path(f"data/raw/metrics/{project_name}_metrics.csv")
    metrics_dict = {}
    if metrics_path.exists():
        cs = CouplingScorer()
        cs.load_data(metrics_path=str(metrics_path))
        # CouplingScorer armazena metrics_dict em load_data
        metrics_dict = getattr(cs, 'metrics_dict', {})
        print(f"Métricas por classe carregadas: {len(metrics_dict)}")
    else:
        warnings.warn(f"Arquivo de métricas não encontrado: {metrics_path}. Campos CBO/RFC/DIT/LCOM podem faltar.")

    # Agregações por classe
    agg = defaultdict(lambda: {
        'degree_pairs': 0,
        'hybrid_sum': 0.0,
        'hybrid_max': 0.0,
        'hybrid_list': [],
        'structural_sum': 0.0,
        'logical_sum': 0.0,
        'count_strong': 0,
        'support_sum': 0.0,
        'support_max': 0.0,
        'commits_sum': 0,
    })

    # Threshold: utiliza threshold do primeiro scorer se existir, senão 0.7
    default_threshold = 0.7
    try:
        tmp_scorer = CouplingScorer()
        threshold = tmp_scorer.coupling_threshold
    except Exception:
        threshold = default_threshold

    for s in scores:
        a = s.class_a
        b = s.class_b
        # Atualiza a
        agg[a]['degree_pairs'] += 1
        agg[a]['hybrid_sum'] += s.hybrid_score
        agg[a]['hybrid_max'] = max(agg[a]['hybrid_max'], s.hybrid_score)
        agg[a]['hybrid_list'].append(s.hybrid_score)
        agg[a]['structural_sum'] += s.structural_score
        agg[a]['logical_sum'] += s.logical_score
        if s.is_strong_coupling:
            agg[a]['count_strong'] += 1
        support = s.metrics.get('support', 0) if s.metrics else 0
        commits = s.metrics.get('commits', 0) if s.metrics else 0
        agg[a]['support_sum'] += support
        agg[a]['support_max'] = max(agg[a]['support_max'], support)
        agg[a]['commits_sum'] += commits
        # Atualiza b
        agg[b]['degree_pairs'] += 1
        agg[b]['hybrid_sum'] += s.hybrid_score
        agg[b]['hybrid_max'] = max(agg[b]['hybrid_max'], s.hybrid_score)
        agg[b]['hybrid_list'].append(s.hybrid_score)
        agg[b]['structural_sum'] += s.structural_score
        agg[b]['logical_sum'] += s.logical_score
        if s.is_strong_coupling:
            agg[b]['count_strong'] += 1
        agg[b]['support_sum'] += support
        agg[b]['support_max'] = max(agg[b]['support_max'], support)
        agg[b]['commits_sum'] += commits

    # Monta DataFrame final
    rows = []
    for cls, vals in agg.items():
        degree = vals['degree_pairs']
        hybrid_avg = vals['hybrid_sum'] / degree if degree else 0.0
        structural_avg = vals['structural_sum'] / degree if degree else 0.0
        logical_avg = vals['logical_sum'] / degree if degree else 0.0
        hybrid_median = float(np.median(vals['hybrid_list'])) if vals['hybrid_list'] else 0.0
        count_strong = vals['count_strong']
        pct_strong = count_strong / degree if degree else 0.0

        # metrics por classe se existirem
        cbo = metrics_dict.get(cls, {}).get('cbo', np.nan)
        rfc = metrics_dict.get(cls, {}).get('rfc', np.nan)
        dit = metrics_dict.get(cls, {}).get('dit', np.nan)
        lcom = metrics_dict.get(cls, {}).get('lcom', np.nan)

        rows.append({
            'class': cls,
            'degree_pairs': degree,
            'avg_hybrid': hybrid_avg,
            'median_hybrid': hybrid_median,
            'max_hybrid': vals['hybrid_max'],
            'avg_structural': structural_avg,
            'avg_logical': logical_avg,
            'count_strong': count_strong,
            'pct_strong': pct_strong,
            'support_sum': vals['support_sum'],
            'support_max': vals['support_max'],
            'commits_sum': vals['commits_sum'],
            'cbo': cbo,
            'rfc': rfc,
            'dit': dit,
            'lcom': lcom,
        })

    df = pd.DataFrame(rows)
    # Preenchimento de NaNs
    df[['cbo','rfc','dit','lcom']] = df[['cbo','rfc','dit','lcom']].fillna(0)

    out_csv = project_dir / 'class_features.csv'
    df.to_csv(out_csv, index=False)
    print(f"✓ Features por classe salvas em: {out_csv} (n={len(df)})")

    # Normaliza features (exclui coluna 'class')
    feature_cols = [c for c in df.columns if c != 'class']
    scaler = StandardScaler()
    X = scaler.fit_transform(df[feature_cols].values)

    # Salva scaler + X
    scaled_file = project_dir / 'class_features_scaled.pkl'
    with open(scaled_file, 'wb') as f:
        pickle.dump({'scaler': scaler, 'features': X, 'columns': feature_cols, 'classes': df['class'].tolist()}, f)

    print(f"✓ Features escaladas salvas em: {scaled_file}")
    return out_csv
