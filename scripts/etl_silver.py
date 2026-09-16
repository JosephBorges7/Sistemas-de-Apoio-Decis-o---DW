import pandas as pd
import json
import sqlite3
import os

def main():
    print("Iniciando processamento da camada Silver...")
    os.makedirs(os.path.join('data', 'silver'), exist_ok=True)
    
    # ---------------------------------------------------------
    # 1. Leitura e Limpeza da Fonte 1: CSV (ENEM)
    # ---------------------------------------------------------
    csv_path = os.path.join('data', 'bronze', 'notas_enem.csv')
    if not os.path.exists(csv_path):
        print("Fontes bronze não encontradas. Rode etl_bronze.py antes.")
        return
        
    df_enem = pd.read_csv(csv_path, sep=';')
    # Padronização de nomes de colunas
    df_enem.rename(columns={
        'NU_ANO': 'ano',
        'CO_MUNICIPIO_RESIDENCIA': 'codigo_ibge',
        'NO_ESCOLA': 'nome_escola',
        'MEDIA_OBJETIVAS': 'nota_media_enem'
    }, inplace=True)
    
    # Tratamento de Nulos (Excluir registros sem nota)
    df_enem.dropna(subset=['nota_media_enem'], inplace=True)
    # Garantir tipagem
    df_enem['codigo_ibge'] = df_enem['codigo_ibge'].astype(int)
    
    print(f"-> Fonte 1 (CSV) processada: {len(df_enem)} registros.")

    # ---------------------------------------------------------
    # 2. Leitura e Limpeza da Fonte 2: JSON (IDEB)
    # ---------------------------------------------------------
    json_path = os.path.join('data', 'bronze', 'ideb_escolas.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        ideb_data = json.load(f)
        
    ideb_rows = []
    for ano_dict in ideb_data:
        ano = ano_dict['ano_censo']
        for escola in ano_dict['escolas']:
            ideb_rows.append({
                'ano': ano,
                'codigo_ibge': int(escola['cod_ibge']),
                'nome_escola': escola['escola_nome'],
                'rede': escola['dependencia_adm'],
                'tipo': escola['tipo_ensino'],
                'indicador_ideb': escola['resultados']['ideb'],
                'taxa_aprovacao': escola['resultados']['taxa_aprovacao']
            })
            
    df_ideb = pd.DataFrame(ideb_rows)
    
    print(f"-> Fonte 2 (JSON) processada: {len(df_ideb)} registros.")

    # ---------------------------------------------------------
    # 3. Leitura e Limpeza da Fonte 3: SQLite (IBGE)
    # ---------------------------------------------------------
    db_path = os.path.join('data', 'bronze', 'dados_ibge.db')
    conn = sqlite3.connect(db_path)
    
    df_municipios = pd.read_sql("SELECT * FROM cad_municipio", conn)
    df_pib = pd.read_sql("SELECT * FROM pib_municipal", conn)
    conn.close()
    
    # Integração das tabelas do banco de dados
    df_ibge = pd.merge(df_municipios, df_pib, on='codigo_ibge', how='left')
    print(f"-> Fonte 3 (SQLite) processada: {len(df_ibge)} registros (Município/Ano).")
    
    # ---------------------------------------------------------
    # 4. Integração de Todas as Fontes
    # ---------------------------------------------------------
    print("Realizando Merge das fontes...")
    
    # Merge ENEM + IDEB (usando ano e nome da escola como chave)
    df_silver = pd.merge(
        df_enem, 
        df_ideb, 
        on=['ano', 'codigo_ibge', 'nome_escola'], 
        how='inner' # Manter apenas escolas que tem ambos os dados
    )
    
    # Merge com dados do IBGE
    df_silver = pd.merge(
        df_silver,
        df_ibge,
        on=['ano', 'codigo_ibge'],
        how='left'
    )
    
    # Organizando as colunas da camada Silver
    cols_silver = [
        'ano', 'nome', 'uf', 'regiao', 'codigo_ibge', 
        'nome_escola', 'rede', 'tipo', 
        'nota_media_enem', 'taxa_aprovacao', 'indicador_ideb', 'pib_per_capita'
    ]
    # 'nome' no IBGE é o município. Renomear para município para manter a consistência 
    df_silver.rename(columns={'nome': 'municipio'}, inplace=True)
    
    # Garantir que a ordem está igual 
    cols_final = [
        'ano', 'municipio', 'uf', 'regiao', 'codigo_ibge', 
        'nome_escola', 'rede', 'tipo', 
        'nota_media_enem', 'taxa_aprovacao', 'indicador_ideb', 'pib_per_capita'
    ]
    df_silver = df_silver[cols_final]
    
    # Remover qualquer duplicata que tenha surgido no join
    df_silver.drop_duplicates(inplace=True)
    
    # ---------------------------------------------------------
    # 5. Salvar na Camada Silver
    # ---------------------------------------------------------
    output_path = os.path.join('data', 'silver', 'desempenho_integrado.csv')
    df_silver.to_csv(output_path, index=False)
    print(f"Camada Silver gerada com sucesso: {output_path} ({len(df_silver)} registros).")

if __name__ == "__main__":
    main()
