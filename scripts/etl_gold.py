import os
import pandas as pd

def main():
    print("Iniciando processamento da camada Gold...")
    
    os.makedirs(os.path.join('data', 'gold'), exist_ok=True)
    gold_path = os.path.join('data', 'gold')
    
    # 1. Carregar os dados limpos da Silver
    silver_path = os.path.join('data', 'silver', 'desempenho_integrado.csv')
    if not os.path.exists(silver_path):
        print("Arquivo da camada Silver não encontrado.")
        return
        
    df_silver = pd.read_csv(silver_path)
    
    # 2. Criar Tabelas Dimensões a partir da Silver
    
    # 2.1 Dimensão Tempo
    anos_unicos = df_silver['ano'].dropna().unique()
    dim_tempo = pd.DataFrame({'ano': anos_unicos})
    dim_tempo['id_tempo'] = range(1, len(anos_unicos) + 1)
    dim_tempo['decada'] = (dim_tempo['ano'] // 10) * 10
    dim_tempo = dim_tempo[['id_tempo', 'ano', 'decada']]
    
    # 2.2 Dimensão Município
    # Extrair valores únicos
    df_mun = df_silver[['codigo_ibge', 'municipio', 'uf', 'regiao']].drop_duplicates().reset_index(drop=True)
    df_mun['id_municipio'] = df_mun.index + 1
    # Renomear para casar com o modelo planejado
    dim_municipio = df_mun.rename(columns={'municipio': 'nome'})
    dim_municipio = dim_municipio[['id_municipio', 'nome', 'uf', 'regiao', 'codigo_ibge']]
    
    # 2.3 Dimensão Escola
    df_esc = df_silver[['nome_escola', 'rede', 'tipo']].drop_duplicates().reset_index(drop=True)
    df_esc['id_escola'] = df_esc.index + 1
    dim_escola = df_esc.rename(columns={'nome_escola': 'nome'})
    dim_escola = dim_escola[['id_escola', 'nome', 'rede', 'tipo']]
    
    # 3. Criar a Tabela Fato
    # Fazer merge com dim_tempo
    fato = df_silver.merge(dim_tempo, on='ano', how='left')
    
    # Fazer merge com dim_municipio usando o código IBGE
    fato = fato.merge(dim_municipio[['id_municipio', 'codigo_ibge']], on='codigo_ibge', how='left')
    
    # Fazer merge com dim_escola
    fato = fato.merge(dim_escola[['id_escola', 'nome']], left_on='nome_escola', right_on='nome', how='left')
    
    # Selecionar as colunas da fato
    fato['id_fato'] = range(1, len(fato) + 1)
    
    cols_fato = [
        'id_fato', 
        'id_tempo', 
        'id_municipio', 
        'id_escola', 
        'nota_media_enem', 
        'taxa_aprovacao', 
        'indicador_ideb', 
        'pib_per_capita'
    ]
    fato = fato[cols_fato]
    
    # Renomear para as chaves estrangeiras
    fato = fato.rename(columns={
        'id_tempo': 'fk_tempo',
        'id_municipio': 'fk_municipio',
        'id_escola': 'fk_escola',
        'pib_per_capita': 'pib_per_capita_municipio'
    })
    
    # 4. Salvar em CSV
    dim_tempo.to_csv(os.path.join(gold_path, 'dim_tempo.csv'), index=False)
    dim_municipio.to_csv(os.path.join(gold_path, 'dim_municipio.csv'), index=False)
    dim_escola.to_csv(os.path.join(gold_path, 'dim_escola.csv'), index=False)
    fato.to_csv(os.path.join(gold_path, 'fato_desempenho_educacional.csv'), index=False)
    
    print(f"Camada Gold gerada com sucesso! Arquivos CSV salvos em {gold_path}")
    print(f"Dimensões criadas: Tempo ({len(dim_tempo)}), Município ({len(dim_municipio)}), Escola ({len(dim_escola)})")
    print(f"Tabela Fato criada com {len(fato)} registros.")

if __name__ == "__main__":
    main()
