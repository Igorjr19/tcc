import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# --- 1. SIMULAÇÃO DE CARREGAMENTO DE DADOS (ETAPAS 1.2 E 1.3) ---

def create_mock_data():
    """Cria dados simulados para as métricas estruturais (CBO, DIT, LCOM, RFC)."""
    data = {
        'Classe': ['User', 'UserRepository', 'AuthService', 'Logger', 'EmailSender', 
                   'ReportGenerator', 'PaymentService', 'NotificationService', 'AuditLog', 'Cache'],
        'CBO': [3, 5, 4, 1, 2, 6, 5, 3, 2, 4],
        'DIT': [1, 0, 1, 0, 0, 0, 1, 1, 0, 0],
        'LCOM': [0, 1, 3, 0, 1, 5, 2, 1, 0, 3],
        'RFC': [8, 12, 10, 3, 5, 15, 11, 7, 4, 9]
    }
    return pd.DataFrame(data)

def create_mock_co_change_data():
    """Cria dados simulados para a frequência de co-mudança (dependência lógica)
    e o rótulo de dependência estrutural (ground truth inicial)."""
    
    # Lista de tuplas: (Classe1, Classe2, FrequenciaDeComudanca, EstruturalmenteAcopladas)
    data = [
        # === PARES COM ACOPLAMENTO ESTRUTURAL EXPLÍCITO (Ground Truth Positivo) ===
        # Estes têm dependência direta no código
        ('User', 'UserRepository', 15, 1),
        ('UserRepository', 'AuthService', 8, 1),
        ('AuthService', 'User', 12, 1),
        ('PaymentService', 'NotificationService', 10, 1),
        ('AuthService', 'AuditLog', 9, 1),
        
        # === DEPENDÊNCIAS IMPLÍCITAS FORTES (Alto co-mudança, SEM acoplamento estrutural) ===
        # Estes são os casos interessantes que o ML deve detectar!
        ('User', 'EmailSender', 22, 0),  # User muda, EmailSender sempre muda junto (ex: notificações)
        ('PaymentService', 'AuditLog', 19, 0),  # Pagamentos sempre geram logs de auditoria
        ('ReportGenerator', 'Cache', 18, 0),  # Relatórios dependem de cache, mas sem import direto
        ('UserRepository', 'Cache', 16, 0),  # Repository usa cache implicitamente
        ('NotificationService', 'Logger', 14, 0),  # Notificações sempre logam, mas não há dependência direta
        
        # === DEPENDÊNCIAS IMPLÍCITAS MODERADAS (Casos limítrofes) ===
        ('User', 'Logger', 8, 0),  # Co-mudança moderada
        ('EmailSender', 'Logger', 7, 0),  # Co-mudança moderada
        ('ReportGenerator', 'Logger', 6, 0),  # No limite do threshold
        
        # === PARES INDEPENDENTES (Baixa ou nenhuma co-mudança) ===
        ('AuthService', 'EmailSender', 2, 0),  # Raramente mudam juntos
        ('User', 'Cache', 1, 0),  # Quase nunca mudam juntos
        ('PaymentService', 'Logger', 3, 0),  # Pouca co-mudança
        ('NotificationService', 'Cache', 1, 0),  # Independentes
        ('AuditLog', 'Cache', 0, 0),  # Totalmente independentes
        ('EmailSender', 'ReportGenerator', 2, 0),  # Baixa co-mudança
    ]
    
    return pd.DataFrame(data, columns=['Classe1', 'Classe2', 'FrequenciaDeComudanca', 'EstruturalmenteAcopladas'])

# Carregamento dos dados simulados
df_metrics = create_mock_data()
df_pairs_base = create_mock_co_change_data()


# --- 2. CRIAÇÃO DO DATASET DE PARES DE CLASSE COMPLETO ---

def generate_full_pair_dataset(df_metrics, df_pairs_base):
    """Gera o dataset final, combinando métricas e dados de acoplamento."""
    
    # 2.1. Combinação dos dados de co-mudança com as métricas da Classe1
    df_final = pd.merge(df_pairs_base, df_metrics, 
                        left_on='Classe1', right_on='Classe', how='left', suffixes=('', '_C1'))
    df_final.rename(columns={'CBO': 'CBO_C1', 'DIT': 'DIT_C1', 'LCOM': 'LCOM_C1', 'RFC': 'RFC_C1'}, inplace=True)
    df_final.drop(columns=['Classe'], inplace=True)

    # 2.2. Combinação com as métricas da Classe2
    df_final = pd.merge(df_final, df_metrics, 
                        left_on='Classe2', right_on='Classe', how='left', suffixes=('', '_C2'))
    df_final.rename(columns={'CBO': 'CBO_C2', 'DIT': 'DIT_C2', 'LCOM': 'LCOM_C2', 'RFC': 'RFC_C2'}, inplace=True)
    df_final.drop(columns=['Classe'], inplace=True)

    # 2.3. Criação do Rótulo (Target Variable 'Dependencia')
    df_final['Dependencia'] = df_final['EstruturalmenteAcopladas'].astype(int)
    
    # Adicionando uma coluna 'logica_forte' como feature para classes com alta co-mudança
    df_final['CoMudancaForte'] = (df_final['FrequenciaDeComudanca'] > 5).astype(int)
    
    # Seleção final das colunas (Features e Target)
    features = ['CBO_C1', 'DIT_C1', 'LCOM_C1', 'RFC_C1', 
                'CBO_C2', 'DIT_C2', 'LCOM_C2', 'RFC_C2', 
                'FrequenciaDeComudanca', 'CoMudancaForte']
    
    return df_final, features

# Geração do Dataset Base
df_base, features = generate_full_pair_dataset(df_metrics, df_pairs_base)

# Separação de Features e Target
X = df_base[features]
y = df_base['Dependencia']

# Divisão em treino e teste (Holdout) para validação inicial (mantido como no código anterior)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

# Inicialização e Treinamento do Classificador (Random Forest)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print("--- Protótipo do Motor de Análise (Predição) ---")

# --- 3. APLICAÇÃO DO MODELO E ANÁLISE DE RESULTADOS ---

# Aplicaremos o modelo em TODO o dataset para demonstração
# (Em produção, usaríamos apenas dados novos/não vistos)
y_proba_full = model.predict_proba(X)
# Verifica se há probabilidades para ambas as classes
if y_proba_full.shape[1] == 2:
    y_proba = y_proba_full[:, 1]  # Probabilidade da classe positiva (Dependencia = 1)
else:
    y_proba = y_proba_full[:, 0]  # Apenas uma classe presente 

# Adicionando as probabilidades ao DataFrame completo para análise
df_results = df_base.copy()
df_results['Probabilidade_Dependencia'] = y_proba

# --- DEBUG: Análise do dataset completo ---
print("\n=== ANÁLISE DO DATASET COMPLETO ===")
print(f"Total de pares: {len(df_results)}")
print("\nDistribuição:")
print(f"  - Com acoplamento estrutural (Dependencia=1): {len(df_results[df_results['Dependencia']==1])}")
print(f"  - Sem acoplamento estrutural (Dependencia=0): {len(df_results[df_results['Dependencia']==0])}")

print("\n--- TOP 10 Pares com MAIOR probabilidade de dependência ---")
top_10 = df_results.nlargest(10, 'Probabilidade_Dependencia')
print(top_10[['Classe1', 'Classe2', 'FrequenciaDeComudanca', 'Dependencia', 'Probabilidade_Dependencia']].to_string())

# Análise específica dos pares sem acoplamento estrutural
pares_sem_acoplamento = df_results[df_results['Dependencia'] == 0].sort_values(by='Probabilidade_Dependencia', ascending=False)
print("\n--- TOP Pares SEM acoplamento estrutural (candidatos a dependência implícita) ---")
print(f"Total de pares sem acoplamento: {len(pares_sem_acoplamento)}")
if not pares_sem_acoplamento.empty:
    print(pares_sem_acoplamento.head(10)[['Classe1', 'Classe2', 'FrequenciaDeComudanca', 'Probabilidade_Dependencia']].to_string())

# --- 4. IDENTIFICAÇÃO DE DEPENDÊNCIAS IMPLÍCITAS (Descoberta) ---

# Critério: Classes NÃO acopladas estruturalmente (Dependencia == 0), 
# mas com alta probabilidade predita pelo ML (ex: > 60%)
THRESHOLD = 0.60

implicit_dependencies = df_results[
    (df_results['Dependencia'] == 0) & 
    (df_results['Probabilidade_Dependencia'] >= THRESHOLD)
].sort_values(by='Probabilidade_Dependencia', ascending=False)


print("\n=== DESCOBERTA DE DEPENDÊNCIAS LÓGICAS/IMPLÍCITAS ===")
if implicit_dependencies.empty:
    print("Nenhuma dependência implícita de alta confiança encontrada no conjunto de teste.")
else:
    print(f"Foram encontradas {len(implicit_dependencies)} potenciais dependências implícitas (Probabilidade > {THRESHOLD*100}%):")
    print("--------------------------------------------------------------------------------------------------------------------------------")
    print(implicit_dependencies[['Classe1', 'Classe2', 'FrequenciaDeComudanca', 'Probabilidade_Dependencia']])
    print("--------------------------------------------------------------------------------------------------------------------------------")
    print("\nEstes pares não possuem acoplamento estrutural explícito, mas o histórico de co-mudança e as métricas sugerem que devem ser revisados.")
