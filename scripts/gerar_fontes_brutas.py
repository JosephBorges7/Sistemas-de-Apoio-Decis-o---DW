import pandas as pd
import json
import sqlite3
import os

def main():
    print("Deconstruindo a base integrada para gerar fontes brutas realistas...")
    
    os.makedirs(os.path.join('data', 'raw_fontes'), exist_ok=True)
    
    # 1. Lendo os dados já fornecidos e integrados para servirem de semente
    try:
        df_silver = pd.read_csv(os.path.join('seeds', 'desempenho_integrado.csv'))
        df_escola = pd.read_csv(os.path.join('seeds', 'dim_escola.csv'))
        df_municipio = pd.read_csv(os.path.join('seeds', 'dim_municipio.csv'))
    except Exception as e:
        print(f"Erro ao ler bases. Certifique-se de que desempenho_integrado.csv existe. {e}")
        return

    # Juntar tudo para ter uma base mestre
    df_mestre = df_silver.copy()
    
    # =========================================================================
    # FONTE 1: CSV (Notas do ENEM)
    # Simulando um arquivo do INEP com colunas com nomes ruins e dados sujos
    # =========================================================================
    df_enem = df_mestre[['ano', 'codigo_ibge', 'nome_escola', 'nota_media_enem']].copy()
    df_enem.rename(columns={
        'ano': 'NU_ANO',
        'codigo_ibge': 'CO_MUNICIPIO_RESIDENCIA',
        'nome_escola': 'NO_ESCOLA',
        'nota_media_enem': 'MEDIA_OBJETIVAS'
    }, inplace=True)
    df_enem.to_csv(os.path.join('data', 'raw_fontes', 'notas_enem.csv'), index=False, sep=';')
    print("Fonte 1 (CSV) gerada: data/raw_fontes/notas_enem.csv")

    # =========================================================================
    # FONTE 2: JSON (IDEB e Metadados das Escolas)
    # Simulando um endpoint de API do MEC
    # =========================================================================
    # Precisamos da rede e tipo da escola, além do IDEB e taxa de aprovação
    df_ideb = df_mestre[['ano', 'codigo_ibge', 'nome_escola', 'rede', 'tipo', 'indicador_ideb', 'taxa_aprovacao']].copy()
    json_data = []
    for ano, group in df_ideb.groupby('ano'):
        ano_dict = {"ano_censo": int(ano), "escolas": []}
        for _, row in group.iterrows():
            # Inserir alguns nulos para forçar o tratamento no ETL
            ideb_val = row['indicador_ideb']
            taxa_val = row['taxa_aprovacao']
            if pd.isna(ideb_val): ideb_val = None
            if pd.isna(taxa_val): taxa_val = None
            
            ano_dict["escolas"].append({
                "cod_ibge": int(row['codigo_ibge']),
                "escola_nome": row['nome_escola'],
                "dependencia_adm": row['rede'],
                "tipo_ensino": row['tipo'],
                "resultados": {
                    "ideb": ideb_val,
                    "taxa_aprovacao": taxa_val
                }
            })
        json_data.append(ano_dict)
        
    with open(os.path.join('data', 'raw_fontes', 'ideb_escolas.json'), 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)
    print("Fonte 2 (JSON) gerada: data/raw_fontes/ideb_escolas.json")

    # =========================================================================
    # FONTE 3: Banco de Dados Relacional SQLite (Dados do IBGE)
    # Simulando um banco relacional do Ministério da Economia / IBGE
    # =========================================================================
    db_path = os.path.join('data', 'raw_fontes', 'dados_ibge.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    
    # Tabela 1: Cadastro de Municípios
    df_mun_db = df_municipio[['codigo_ibge', 'nome', 'uf', 'regiao']].copy()
    df_mun_db.to_sql('cad_municipio', conn, index=False)
    
    # Tabela 2: PIB per capita por Município e Ano
    df_pib = df_mestre[['ano', 'codigo_ibge', 'pib_per_capita']].drop_duplicates()
    df_pib.to_sql('pib_municipal', conn, index=False)
    
    conn.close()
    print("Fonte 3 (SQLite) gerada: data/raw_fontes/dados_ibge.db")

if __name__ == "__main__":
    main()
