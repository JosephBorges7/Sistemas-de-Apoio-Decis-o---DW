# Data Warehouse de Desempenho Educacional

## Objetivo do Projeto
O objetivo deste projeto é analisar o desempenho educacional cruzando dados fictícios do ENEM e IDEB com indicadores socioeconômicos (PIB per capita) em diferentes municípios, redes de ensino e regiões do Brasil. A estrutura foi construída utilizando uma **Arquitetura Medalhão**, atendendo integralmente ao escopo da disciplina de Sistemas de Apoio à Decisão (Bacharelado em Sistemas de Informação - IFBA).

## Domínio Escolhido
**Educação e Socioeconomia**: Análise de notas médias do ENEM, taxa de aprovação, indicador IDEB e o impacto do PIB per capita municipal no desempenho das escolas públicas vs privadas.

## Estrutura de Pastas e Dados
- **`seeds/`**: Arquivos originais que servem como "semente" para a simulação dos dados brutos.
- **`data/raw_fontes/`**: Pasta contendo os dados gerados para simular sistemas reais: `notas_enem.csv` (MEC), `ideb_escolas.json` (API), `dados_ibge.db` (Banco Relacional).
- **`data/bronze/`**: Dados brutos copiados sem alteração.
- **`data/silver/`**: Dados limpos, tratados (nulos, strings) e unificados num Dataframe via JOIN.
- **`data/gold/`**: Modelo dimensional em Star Schema armazenado em um banco SQLite final (`dw_educacao.db`).
- **`scripts/`**: Módulos do pipeline de Engenharia de Dados (`gerar_fontes_brutas.py`, `etl_bronze.py`, `etl_silver.py`, `etl_gold.py`).
- **`docs/diagrama/`**: Modelo relacional/dimensional (`esquema_estrela_educacao.md`).
- **`docs/relatorio/`**: Relatório final do projeto preenchido na estrutura Markdown exigida (`relatorio_final.md`).
- **`apresentacao/`**: Slides baseados em Marp (`slides.md`).

## Como rodar o Pipeline (ETL)
Os scripts foram desenhados para rodar de forma sequencial utilizando Python (Pandas + SQLite3). A partir da raiz do projeto, execute:

1. **Geração das Fontes**:
   *(Caso a pasta raw_fontes não exista ou precise ser gerada do zero)*
   ```bash
   python scripts/gerar_fontes_brutas.py
   ```
2. **Carga na Bronze**:
   ```bash
   python scripts/etl_bronze.py
   ```
3. **Tratamento e Integração na Silver**:
   ```bash
   python scripts/etl_silver.py
   ```
4. **Modelagem Star Schema na Gold**:
   ```bash
   python scripts/etl_gold.py
   ```
