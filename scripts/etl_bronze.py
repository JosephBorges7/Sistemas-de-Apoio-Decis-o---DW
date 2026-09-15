import os
import shutil

def main():
    print("Iniciando extração para a camada Bronze...")
    
    os.makedirs(os.path.join('data', 'bronze'), exist_ok=True)
    
    fontes = [
        (os.path.join('data', 'raw_fontes'), 'notas_enem.csv'),
        (os.path.join('data', 'raw_fontes'), 'ideb_escolas.json'),
        (os.path.join('data', 'raw_fontes'), 'dados_ibge.db')
    ]
    
    for folder, file in fontes:
        origem = os.path.join(folder, file)
        destino = os.path.join('data', 'bronze', file)
        
        if os.path.exists(origem):
            shutil.copy2(origem, destino)
            print(f"[{file}] extraído com sucesso para a camada bronze.")
        else:
            print(f"Erro: Arquivo {origem} não encontrado. Por favor, rode gerar_fontes_brutas.py primeiro.")

    print("Carga na camada Bronze finalizada.")

if __name__ == "__main__":
    main()
