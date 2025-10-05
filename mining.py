import argparse
import os
from collections import defaultdict
from pydriller import Repository

def find_co_changes(repo_path):
    """
    Mina um repositório Git para encontrar co-mudanças entre arquivos .java.

    Args:
        repo_path (str): O caminho para o repositório Git.

    Returns:
        defaultdict: Um dicionário com pares de arquivos e a contagem de co-mudanças.
    """
    co_changes = defaultdict(int)
    
    # Itera sobre todos os commits do repositório.
    # Você pode usar 'since' e 'to' para limitar o intervalo de datas, se necessário.
    for commit in Repository(repo_path).traverse_commits():
        modified_java_files = []
        for mod in commit.modified_files:
            if mod.filename.endswith(".java"):
                # Captura apenas o nome do arquivo para simplificar a análise.
                modified_java_files.append(os.path.basename(mod.new_path))

        # Cria pares de arquivos que foram modificados no mesmo commit.
        if len(modified_java_files) > 1:
            for i in range(len(modified_java_files)):
                for j in range(i + 1, len(modified_java_files)):
                    file1 = modified_java_files[i]
                    file2 = modified_java_files[j]
                    
                    # Garante que a ordem dos arquivos no par seja consistente para a contagem.
                    if file1 > file2:
                        file1, file2 = file2, file1
                    
                    co_changes[(file1, file2)] += 1
    
    return co_changes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mina um repositório Git para encontrar co-mudanças entre arquivos .java.")
    parser.add_argument("repo_path", type=str, help="O caminho para o repositório Git.")
    args = parser.parse_args()

    repo_path = args.repo_path

    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"Erro: O caminho '{repo_path}' não parece ser um repositório Git.")
    else:
        print(f"Iniciando a mineração do repositório em: {repo_path}")
        co_changes_data = find_co_changes(repo_path)

        if not co_changes_data:
            print("Nenhuma co-mudança encontrada.")
        else:
            print("\nCo-mudanças encontradas (pares de arquivos e sua frequência):")
            # Ordena os resultados pela frequência de co-mudança, do maior para o menor.
            sorted_co_changes = sorted(co_changes_data.items(), key=lambda item: item[1], reverse=True)
            for pair, count in sorted_co_changes:
                print(f"  {pair[0]} e {pair[1]}: {count} co-mudanças")
            
            # Você pode descomentar as linhas abaixo para salvar os dados em um arquivo CSV.
            # import csv
            # with open("co_changes.csv", "w", newline='') as f:
            #     writer = csv.writer(f)
            #     writer.writerow(["Classe1", "Classe2", "Frequencia"])
            #     for pair, count in sorted_co_changes:
            #         writer.writerow([pair[0], pair[1], count])
            # print("\nOs dados foram salvos em 'co_changes.csv'.")

