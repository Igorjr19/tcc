#!/usr/bin/env python
"""
Script unificado para treinamento de modelos ML - versão funcional definitiva.
Inclui todas as correções e funciona com dataset completo ou apenas co-mudanças.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    roc_auc_score,
    f1_score,
    precision_score,
    recall_score,
    average_precision_score,
)
from imblearn.over_sampling import SMOTE
import pickle
import json
import warnings

warnings.filterwarnings("ignore")

# Diretórios
BASE_DIR = Path(__file__).parent.absolute()
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "data" / "models"
RESULTS_DIR = BASE_DIR / "results"

# Criar diretórios
MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset():
    """Carrega o dataset disponível (prioriza o mais completo)."""
    print("=" * 80)
    print("CARREGAMENTO DO DATASET")
    print("=" * 80)

    # Tentar carregar dataset completo primeiro
    dataset_files = [
        ("master_dataset.csv", "Dataset Completo (Todas as Features)"),
    ]

    for filename, description in dataset_files:
        dataset_path = PROCESSED_DATA_DIR / filename
        if dataset_path.exists():
            print(f"\nCarregando: {description}")
            print(f"   Arquivo: {dataset_path}")

            try:
                df = pd.read_csv(dataset_path)
                print(f"   Carregado com sucesso!")
                print(f"   Shape: {df.shape}")

                # Verificar se tem a coluna target
                target_col = None
                for possible_target in [
                    "has_dependency",
                    "DependenciaExplicita",
                ]:
                    if possible_target in df.columns:
                        target_col = possible_target
                        break

                if target_col:
                    print(
                        f"   Target ({target_col}): {df[target_col].value_counts().to_dict()}"
                    )

                    # Identificar tipo de features
                    feature_cols = [
                        col
                        for col in df.columns
                        if col
                        not in [
                            "Repositorio",
                            "Classe1",
                            "Classe2",
                            "class_a",
                            "class_b",
                            "repo_a",
                            "repo_b",
                            target_col,
                        ]
                    ]
                    co_change_features = [
                        col
                        for col in feature_cols
                        if any(
                            term in col.lower()
                            for term in ["co_", "frequency", "change"]
                        )
                    ]
                    structural_features = [
                        col
                        for col in feature_cols
                        if any(
                            metric in col.upper()
                            for metric in ["CBO", "DIT", "LCOM", "RFC"]
                        )
                    ]

                    print(f"   Features disponíveis: {len(feature_cols)}")
                    print(f"      Co-mudança: {len(co_change_features)}")
                    print(f"      Estruturais: {len(structural_features)}")

                    return df, target_col, feature_cols
                else:
                    print(f"   Coluna target não encontrada")
                    continue

            except Exception as e:
                print(f"   Erro ao carregar: {e}")
                continue

    print("\nNenhum dataset válido encontrado!")
    print("   Execute 'python data_integration.py' primeiro")
    return None, None, None


def prepare_features(df, target_col, feature_cols):
    """Prepara as features para treinamento."""
    print(f"\n PREPARAÇÃO DAS FEATURES")
    print(f"   Target: {target_col}")
    print(f"   Features: {len(feature_cols)}")

    # Separar X e y
    X = df[feature_cols].copy()
    y = df[target_col].copy()

    # Tratar valores NaN
    nan_counts = X.isnull().sum()
    if nan_counts.sum() > 0:
        print(f"   Tratando {nan_counts.sum()} valores NaN...")
        X = X.fillna(0)
    else:
        print(f"   Nenhum valor NaN encontrado")

    # Verificar tipos de dados
    print(f"   Tipos de dados:")
    for dtype, count in X.dtypes.value_counts().items():
        print(f"      {count} colunas {dtype}")

    return X, y


def train_models(X, y, feature_cols):
    """Treina múltiplos modelos de ML."""
    print(f"\nTREINAMENTO DOS MODELOS")
    print("-" * 60)

    # Split dos dados
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"   Split dos dados:")
    print(f"      Treino: {X_train.shape[0]:,} amostras")
    print(f"      Teste: {X_test.shape[0]:,} amostras")

    # Normalização
    print(f"   Normalizando features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Balanceamento com SMOTE
    print(f"   Balanceando dados com SMOTE...")
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)

    unique_train, counts_train = np.unique(y_train, return_counts=True)
    unique_balanced, counts_balanced = np.unique(y_train_balanced, return_counts=True)

    print(f"      Antes SMOTE: {dict(zip(unique_train, counts_train))}")
    print(f"      Após SMOTE: {dict(zip(unique_balanced, counts_balanced))}")

    # Modelos a treinar
    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=100, max_depth=6, random_state=42
        ),
        "LogisticRegression": LogisticRegression(random_state=42, max_iter=1000),
        "SVM": SVC(kernel="rbf", probability=True, random_state=42),
    }

    # Resultados
    results = {}
    trained_models = {}

    # Treinar cada modelo
    for name, model in models.items():
        print(f"\n   Treinando {name}...")

        try:
            # Treinar
            model.fit(X_train_balanced, y_train_balanced)

            # Predições
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = (
                model.predict_proba(X_test_scaled)[:, 1]
                if hasattr(model, "predict_proba")
                else None
            )

            # Métricas
            metrics = {
                "accuracy": model.score(X_test_scaled, y_test),
                "precision": precision_score(y_test, y_pred, zero_division=0),
                "recall": recall_score(y_test, y_pred, zero_division=0),
                "f1": f1_score(y_test, y_pred, zero_division=0),
            }

            if y_pred_proba is not None:
                metrics["roc_auc"] = roc_auc_score(y_test, y_pred_proba)
                metrics["avg_precision"] = average_precision_score(y_test, y_pred_proba)
            else:
                metrics["roc_auc"] = 0.0
                metrics["avg_precision"] = 0.0

            # Cross-validation
            try:
                cv_scores = cross_val_score(
                    model, X_train_balanced, y_train_balanced, cv=5, scoring="f1"
                )
                metrics["cv_f1_mean"] = cv_scores.mean()
                metrics["cv_f1_std"] = cv_scores.std()
            except:
                metrics["cv_f1_mean"] = 0.0
                metrics["cv_f1_std"] = 0.0

            # Store the metrics and trained model keyed by the model name
            results[name] = metrics
            trained_models[name] = model

            print(f"      Treinado com sucesso!")
            print(f"         F1-Score: {metrics['f1']:.4f}")
            print(f"         ROC-AUC: {metrics['roc_auc']:.4f}")

        except Exception as e:
            print(f"      Erro no treinamento: {e}")
            continue

    return results, trained_models, scaler, feature_cols


def save_results(results, trained_models, scaler, feature_cols):
    """Salva resultados e modelos."""
    print("\nSALVANDO RESULTADOS")

    # Salvar métricas em JSON
    metrics_only = results.copy()  # results já contém apenas as métricas

    results_file = RESULTS_DIR / "model_results.json"
    with open(results_file, "w") as f:
        json.dump(metrics_only, f, indent=2)
    print(f"   Métricas salvas em: {results_file}")

    # Salvar modelos e artefatos
    models_data = {
        "results": metrics_only,
        "models": trained_models,
        "scaler": scaler,
        "feature_cols": feature_cols,
    }

    models_file = MODELS_DIR / "trained_models.pkl"
    with open(models_file, "wb") as f:
        pickle.dump(models_data, f)
    print(f"   Modelos salvos em: {models_file}")

    # Salvar resultados em texto
    text_file = RESULTS_DIR / "model_comparison.txt"
    with open(text_file, "w") as f:
        f.write("COMPARAÇÃO DE MODELOS ML\\n")
        f.write("=" * 50 + "\\n\\n")

        # Ordenar por F1-score
        sorted_results = sorted(results.items(), key=lambda x: x[1]["f1"], reverse=True)

        for i, (name, metrics) in enumerate(sorted_results, 1):
            f.write(f"{i}. {name}:\\n")
            f.write(f"   Accuracy:     {metrics['accuracy']:.4f}\\n")
            f.write(f"   Precision:    {metrics['precision']:.4f}\\n")
            f.write(f"   Recall:       {metrics['recall']:.4f}\\n")
            f.write(f"   F1-Score:     {metrics['f1']:.4f}\\n")
            f.write(f"   ROC-AUC:      {metrics['roc_auc']:.4f}\\n")
            f.write(f"   Avg Precision: {metrics['avg_precision']:.4f}\\n")
            f.write(
                f"   CV F1:        {metrics['cv_f1_mean']:.4f} ± {metrics['cv_f1_std']:.4f}\\n\\n"
            )

    print(f"   Comparação salva em: {text_file}")

    return results_file, models_file, text_file


def print_detailed_results(results):
    """Imprime resultados detalhados."""
    print("\nRESULTADOS DETALHADOS")
    print("=" * 80)

    if not results:
        print("Nenhum modelo foi treinado com sucesso")
        return

    # Ordenar por F1-score
    sorted_results = sorted(results.items(), key=lambda x: x[1]["f1"], reverse=True)

    for i, (name, metrics) in enumerate(sorted_results, 1):
        print(f"\n{i}. {name}:")
        print(f"   Accuracy:     {metrics['accuracy']:.4f}")
        print(f"   Precision:    {metrics['precision']:.4f}")
        print(f"   Recall:       {metrics['recall']:.4f}")
        print(f"   F1-Score:     {metrics['f1']:.4f}")
        print(f"   ROC-AUC:      {metrics['roc_auc']:.4f}")
        print(f"   Avg Precision: {metrics['avg_precision']:.4f}")
        print(
            f"   CV F1:        {metrics['cv_f1_mean']:.4f} ± {metrics['cv_f1_std']:.4f}"
        )

    # Melhor modelo
    best_model = sorted_results[0]
    print(f"\nMELHOR MODELO: {best_model[0]}")
    print(f"   F1-Score: {best_model[1]['f1']:.4f}")
    print(f"   ROC-AUC: {best_model[1]['roc_auc']:.4f}")


def main():
    """Função principal."""
    try:
        # 1. Carregar dataset
        df, target_col, feature_cols = load_dataset()
        if df is None:
            return

        # 2. Preparar features
        X, y = prepare_features(df, target_col, feature_cols)

        # 3. Treinar modelos
        results, trained_models, scaler, feature_cols = train_models(X, y, feature_cols)

        if not results:
            print("Nenhum modelo foi treinado com sucesso")
            return

        # 4. Salvar resultados
        results_file, models_file, text_file = save_results(
            results, trained_models, scaler, feature_cols
        )

        # 5. Mostrar resultados
        print_detailed_results(results)

        print("\n" + "=" * 80)
        print("TREINAMENTO CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        print(f"Resultados: {results_file}")
        print(f"Modelos: {models_file}")
        print(f"Comparação: {text_file}")
        print("=" * 80)

    except Exception as e:
        print(f"\nErro durante treinamento: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
