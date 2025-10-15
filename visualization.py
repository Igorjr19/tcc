#!/usr/bin/env python
"""
Script para visualização avançada dos resultados dos modelos ML.
Inclui matriz de confusão, feature importance, curvas ROC e análise detalhada.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle
from sklearn.metrics import (
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
    roc_auc_score,
    average_precision_score
)
from sklearn.model_selection import train_test_split
import warnings
import traceback

warnings.filterwarnings("ignore")

# Configuração de estilo
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Diretórios
BASE_DIR = Path(__file__).parent.absolute()
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "data" / "models"
RESULTS_DIR = BASE_DIR / "results"
PLOTS_DIR = RESULTS_DIR / "plots"

# Criar diretório de plots
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_models_and_data():
    """Carrega os modelos treinados e dados."""
                
    # Carregar modelos
    models_file = MODELS_DIR / "trained_models.pkl"
    if not models_file.exists():
                return None, None, None, None, None, None
    
    with open(models_file, "rb") as f:
        models_data = pickle.load(f)
    
    trained_models = models_data["models"]
    scaler = models_data["scaler"]
    feature_cols = models_data["feature_cols"]
    
        
    # Carregar dataset
    dataset_files = [
        "master_dataset.csv",
        "master_dataset_optimized.csv", 
        "balanced_dataset.csv",
        "simple_dataset.csv"
    ]
    
    df = None
    target_col = None
    
    for filename in dataset_files:
        dataset_path = PROCESSED_DATA_DIR / filename
        if dataset_path.exists():
            try:
                df = pd.read_csv(dataset_path)
                # Encontrar coluna target
                for possible_target in ["has_dependency", "DependenciaExplicita", "target"]:
                    if possible_target in df.columns:
                        target_col = possible_target
                        break
                
                if target_col:
                                                                                break
            except Exception:
                continue
    
    if df is None or target_col is None:
                return None, None, None, None, None, None
    
    return df, target_col, feature_cols, trained_models, scaler, models_data["results"]


def prepare_test_data(df, target_col, feature_cols, scaler):
    """Prepara os dados de teste para avaliação."""
        
    # Preparar features
    X = df[feature_cols].fillna(0)
    y = df[target_col]
    
    # Split (usar mesmo seed do treinamento)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Escalar dados de teste
    X_test_scaled = scaler.transform(X_test)
    
            
    return X_test_scaled, y_test, X_test.columns


def plot_confusion_matrices(models, X_test, y_test, save_dir):
    """Cria matrizes de confusão para todos os modelos."""
        
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    axes = axes.flatten()
    
    for idx, (name, model) in enumerate(models.items()):
        if idx >= 4:  # Limitar a 4 modelos
            break
            
        # Predições
        y_pred = model.predict(X_test)
        
        # Matriz de confusão
        cm = confusion_matrix(y_test, y_pred)
        
        # Plot
        ax = axes[idx]
        sns.heatmap(
            cm, 
            annot=True, 
            fmt='d', 
            cmap='Blues',
            ax=ax,
            xticklabels=['Sem Dependência', 'Com Dependência'],
            yticklabels=['Sem Dependência', 'Com Dependência']
        )
        ax.set_title(f'Matriz de Confusão - {name}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Predito')
        ax.set_ylabel('Real')
        
        # Adicionar métricas
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        ax.text(0.5, -0.15, f'Acc: {acc:.3f} | Prec: {prec:.3f} | Rec: {rec:.3f} | F1: {f1:.3f}',
               transform=ax.transAxes, ha='center', va='top', fontsize=10)
    
    # Remover subplots extras
    for idx in range(len(models), 4):
        fig.delaxes(axes[idx])
    
    plt.tight_layout()
    plt.savefig(save_dir / "confusion_matrices.png", dpi=300, bbox_inches='tight')
    plt.show()
    

def plot_feature_importance(models, feature_names, save_dir, top_n=20):
    """Plota feature importance para modelos que suportam."""
        
    # Modelos que têm feature importance
    importance_models = {}
    for name, model in models.items():
        if hasattr(model, 'feature_importances_'):
            importance_models[name] = model.feature_importances_
        elif hasattr(model, 'coef_') and len(model.coef_.shape) > 0:
            # Para modelos lineares, usar valor absoluto dos coeficientes
            importance_models[name] = np.abs(model.coef_[0])
    
    if not importance_models:
                return
    
    # Plot
    n_models = len(importance_models)
    fig, axes = plt.subplots(n_models, 1, figsize=(12, 6 * n_models))
    
    if n_models == 1:
        axes = [axes]
    
    for idx, (name, importances) in enumerate(importance_models.items()):
        # Criar DataFrame para facilitar ordenação
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False).head(top_n)
        
        # Plot
        ax = axes[idx]
        bars = ax.barh(range(len(importance_df)), importance_df['importance'], 
                      color=plt.cm.viridis(np.linspace(0, 1, len(importance_df))))
        
        ax.set_yticks(range(len(importance_df)))
        ax.set_yticklabels(importance_df['feature'], fontsize=10)
        ax.set_xlabel('Importância', fontsize=12)
        ax.set_title(f'Feature Importance - {name} (Top {top_n})', 
                    fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        
        # Adicionar valores nas barras
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + width * 0.01, bar.get_y() + bar.get_height()/2, 
                   f'{width:.4f}', ha='left', va='center', fontsize=9)
        
        # Inverter ordem para mostrar maior importância no topo
        ax.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(save_dir / "feature_importance.png", dpi=300, bbox_inches='tight')
    plt.show()
        
    # Salvar ranking de features em CSV
    for name, importances in importance_models.items():
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        csv_file = save_dir / f"feature_ranking_{name.lower()}.csv"
        importance_df.to_csv(csv_file, index=False)
        

def plot_roc_curves(models, X_test, y_test, save_dir):
    """Plota curvas ROC para todos os modelos."""
        
    plt.figure(figsize=(12, 8))
    
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for idx, (name, model) in enumerate(models.items()):
        if hasattr(model, 'predict_proba'):
            # Probabilidades
            y_proba = model.predict_proba(X_test)[:, 1]
            
            # Curva ROC
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            auc = roc_auc_score(y_test, y_proba)
            
            plt.plot(fpr, tpr, color=colors[idx % len(colors)], 
                    linewidth=2, label=f'{name} (AUC = {auc:.3f})')
    
    # Linha diagonal
    plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Chance Aleatória')
    
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Taxa de Falsos Positivos (1 - Especificidade)', fontsize=12)
    plt.ylabel('Taxa de Verdadeiros Positivos (Sensibilidade)', fontsize=12)
    plt.title('Curvas ROC - Comparação de Modelos', fontsize=14, fontweight='bold')
    plt.legend(loc="lower right", fontsize=11)
    plt.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_dir / "roc_curves.png", dpi=300, bbox_inches='tight')
    plt.show()
    

def plot_precision_recall_curves(models, X_test, y_test, save_dir):
    """Plota curvas Precision-Recall para todos os modelos."""
        
    plt.figure(figsize=(12, 8))
    
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for idx, (name, model) in enumerate(models.items()):
        if hasattr(model, 'predict_proba'):
            # Probabilidades
            y_proba = model.predict_proba(X_test)[:, 1]
            
            # Curva Precision-Recall
            precision, recall, _ = precision_recall_curve(y_test, y_proba)
            avg_precision = average_precision_score(y_test, y_proba)
            
            plt.plot(recall, precision, color=colors[idx % len(colors)], 
                    linewidth=2, label=f'{name} (AP = {avg_precision:.3f})')
    
    # Baseline
    baseline = sum(y_test) / len(y_test)
    plt.axhline(y=baseline, color='k', linestyle='--', 
               label=f'Baseline (Prevalência = {baseline:.3f})')
    
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Recall (Sensibilidade)', fontsize=12)
    plt.ylabel('Precision', fontsize=12)
    plt.title('Curvas Precision-Recall - Comparação de Modelos', fontsize=14, fontweight='bold')
    plt.legend(loc="lower left", fontsize=11)
    plt.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_dir / "precision_recall_curves.png", dpi=300, bbox_inches='tight')
    plt.show()
    

def create_model_comparison_table(results, save_dir):
    """Cria tabela comparativa detalhada dos modelos."""
        
    # Converter resultados para DataFrame
    df_results = pd.DataFrame(results).T
    df_results = df_results.sort_values('f1', ascending=False)
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('tight')
    ax.axis('off')
    
    # Formatear os dados para exibição
    formatted_data = []
    for model_name, row in df_results.iterrows():
        formatted_row = [
            model_name,
            f"{row['accuracy']:.4f}",
            f"{row['precision']:.4f}",
            f"{row['recall']:.4f}",
            f"{row['f1']:.4f}",
            f"{row['roc_auc']:.4f}",
            f"{row['avg_precision']:.4f}",
            f"{row['cv_f1_mean']:.3f} ± {row['cv_f1_std']:.3f}"
        ]
        formatted_data.append(formatted_row)
    
    # Headers
    headers = ['Modelo', 'Accuracy', 'Precision', 'Recall', 'F1-Score', 
              'ROC-AUC', 'Avg Precision', 'CV F1 (média ± std)']
    
    # Criar tabela
    table = ax.table(cellText=formatted_data, colLabels=headers,
                    cellLoc='center', loc='center')
    
    # Estilizar tabela
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    # Colorir header
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Colorir melhor modelo
    for i in range(len(headers)):
        table[(1, i)].set_facecolor('#E2EFDA')  # Verde claro para melhor modelo
    
    # Colorir demais linhas alternadamente
    for i in range(2, len(formatted_data) + 1):
        color = '#F2F2F2' if i % 2 == 0 else 'white'
        for j in range(len(headers)):
            table[(i, j)].set_facecolor(color)
    
    plt.title('Comparação Detalhada de Modelos ML', fontsize=16, fontweight='bold', pad=20)
    plt.savefig(save_dir / "model_comparison_table.png", dpi=300, bbox_inches='tight')
    plt.show()
    
def main():
    """Função principal."""
    try:
        df, target_col, feature_cols, models, scaler, results = load_models_and_data()
        if df is None:
            return
        
        X_test, y_test, feature_names = prepare_test_data(df, target_col, feature_cols, scaler)
        
        # Matrizes de confusão
        plot_confusion_matrices(models, X_test, y_test, PLOTS_DIR)
        
        # Feature importance
        plot_feature_importance(models, feature_names, PLOTS_DIR, top_n=15)
        
        # Curvas ROC
        plot_roc_curves(models, X_test, y_test, PLOTS_DIR)
        
        # Curvas Precision-Recall  
        plot_precision_recall_curves(models, X_test, y_test, PLOTS_DIR)
        
    except Exception as e:
        traceback.print_exc()


if __name__ == "__main__":
    main()
    