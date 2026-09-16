**Instituto Federal de Educação, Ciência e Tecnologia da Bahia
Campus Feira de Santana
Bacharelado em Sistemas de Informação
Sistemas de Apoio à Decisão – Profª Rebeca Barros**

**Grupo:** Joseph Borges, Gabriel Cabral, Beatriz Freitas, Caio Guilherme
**Tema:** Desempenho Educacional (ENEM, IDEB e Fatores Socioeconômicos)

----------
# Relatório de Projeto

## 1. Problema de Negócio

O domínio escolhido abrange a performance do ensino nas escolas do Brasil, através das notas médias do Exame Nacional do Ensino Médio (ENEM) e do Índice de Desenvolvimento da Educação Básica (IDEB). O objetivo do Data Warehouse é investigar a relação do sucesso acadêmico com:
1. Variáveis socioeconômicas locais (PIB per capita do Município).
2. O fator de dependência administrativa (ensino em escola pública vs escola privada).
3. Desigualdades geográficas, identificando as melhores e piores localidades por região e estado.

O DW deverá responder perguntas como: "Existe relação direta entre investimento/PIB na região e as notas das escolas ali presentes?", "O gap entre escolas públicas e privadas tem diminuído?" e "Quais estados detêm os melhores indicadores?".

---

## 2. Fontes de Dados

### 2.1 Visão Geral

| Fonte | Tipo | Origem | Descrição |
|---|---|---|---|
| notas_enem.csv | Arquivo CSV | MEC/INEP | Histórico de notas médias obtidas pelas escolas no exame. |
| ideb_escolas.json | Arquivo JSON | MEC/INEP | Indicador de qualidade educacional e taxa de aprovação escolar. |
| dados_ibge.db | Banco Relacional | IBGE / Economia | Tabela contendo PIB e Metadados geográficos por código IBGE. |

### 2.2 Fonte 1

**Origem:** INEP / MEC (Dados Sintéticos)  
**Tipo:** Arquivo CSV  
**URL:** Local (`raw_fontes/notas_enem.csv`)  
**Data de obtenção:** Setembro de 2026  

Descrição:
Contém os registros anuais de notas do ENEM em formato CSV utilizando separador ponto-e-vírgula (`;`). Originalmente contém ruídos, nomes de colunas opacos (`NU_ANO`, `CO_MUNICIPIO_RESIDENCIA`) e alguns registros de nota nulos que requerem tratamento na esteira ETL.

### 2.3 Fonte 2

**Origem:** INEP / MEC (Dados Sintéticos)  
**Tipo:** Arquivo JSON  
**URL:** Local (`raw_fontes/ideb_escolas.json`)  
**Data de obtenção:** Setembro de 2026  

Descrição:
Estrutura aninhada (hierárquica) contendo uma lista de anos que abrigam escolas e seus respectivos `resultados` (IDEB e Taxa de Aprovação). Demonstra o cenário do consumo de dados via API REST.

### 2.4 Fonte 3

**Origem:** IBGE (Dados Sintéticos)  
**Tipo:** Banco de Dados Relacional (SQLite)  
**URL:** Local (`raw_fontes/dados_ibge.db`)  
**Data de obtenção:** Setembro de 2026  

Descrição:
Banco de dados contendo duas tabelas: `cad_municipio` e `pib_municipal`. Serve para simular um banco de dados transacional relacional governamental, e deve ser extraído via Queries SQL.

### 2.5 Integração entre as Fontes

As três fontes foram completamente integradas no script `etl_silver.py`. O cruzamento ocorreu majoritariamente através da chave composta pelo **Código IBGE do Município**, o **Ano** do censo, e o **Nome da Escola**. A integração forneceu uma visão horizontal robusta (escola + nota enem + ideb + pib do municipio correspondente).

---

## 3. Linhagem dos Dados (Data Lineage)

> Fontes Brutas (CSV, JSON, Banco de Dados) 
> ➔ **ETL de Extração** 
> ➔ Camada **Bronze** (Preservação de formato original, sem filtros) 
> ➔ **ETL de Limpeza, Padronização e Merge** 
> ➔ Camada **Silver** (`desempenho_integrado.csv`) 
> ➔ **ETL de Modelagem** (Star Schema, Geração de chaves FK/PK) 
> ➔ Camada **Gold** (Arquivos CSV: Fato e Dimensões) 
> ➔ Consumo pelo **Dashboard Streamlit**.

---

## 4. Camada Bronze

### 4.1 Objetivo
Funcionar como um *Data Lake* primário. Garantir que os dados em sua forma bruta e inalterada existam para auditorias, permitindo um "time-travel" e uma re-extração futura caso a regra de negócio da Silver mude, sem onerar novamente as fontes externas.

### 4.2 Estrutura

| Tabela | Fonte | Registros |
|---|---|---:|
| notas_enem.csv | Fonte 1 (CSV) | 660 |
| ideb_escolas.json | Fonte 2 (JSON) | 660 (distribuídos) |
| dados_ibge.db | Fonte 3 (SQLite) | 45 municípios |

---

## 5. Camada Silver

### 5.1 Limpeza

| Problema | Tratamento |
|---|---|
| Valores de nota_media nulos na Fonte 1 | Registros descartados via `.dropna(subset=['nota_media_enem'])` (escolas não avaliadas) |
| Duplicatas geradas por cruzamento | Remoção com `drop_duplicates()` após a etapa final de join |

### 5.2 Padronização

| Campo | Transformação |
|---|---|
| CO_MUNICIPIO_RESIDENCIA | Cast forçado para `Integer` para parear exatamente com o Cod_IBGE |
| nome_escola | Uso de chave unificada durante a mescla |

### 5.3 Transformações

| Campo origem | Campo destino | Regra |
|---|---|---|
| NU_ANO (csv) / ano_censo (json) | ano | Uniformização do nome da coluna para simplificar |
| nome (da tb_municipio) | municipio | Para desambiguar com o "nome" da escola |

### 5.4 Integração

A integração se deu utilizando a biblioteca Pandas no Python. 
1. Fez-se um Merge do DataFrame do ENEM com o do IDEB utilizando `['ano', 'codigo_ibge', 'nome_escola']` garantindo que mantivéssemos as escolas que tinham ambas as informações cruzadas.
2. Em seguida, fez-se um `Left Join` com o DataFrame do IBGE via `['ano', 'codigo_ibge']` para atrelar os atributos estaduais, regionais e o PIB da cidade a cada registro de escola/ano.

### 5.5 Estrutura Silver

Foi exportado um arquivo chamado `desempenho_integrado.csv` contendo:
*ano, municipio, uf, regiao, codigo_ibge, nome_escola, rede, tipo, nota_media_enem, taxa_aprovacao, indicador_ideb, pib_per_capita*.

---

## 6. Camada Gold – Data Warehouse

### 6.1 Modelo Dimensional

Arquivos CSV gerados na pasta `gold/`:
- `fato_desempenho_educacional.csv` (Centro)
- `dim_tempo.csv` (Dimensão de data)
- `dim_escola.csv` (Dimensão organizacional)
- `dim_municipio.csv` (Dimensão geográfica)

### 6.2 Granularidade

A granularidade adotada na Tabela Fato é de **uma linha por Escola a cada Ano letivo avaliado**. Ou seja, a unidade mínima rastreável é o desempenho anual da instituição de ensino (Grão: Ano/Escola).

---

## 7. Processo ETL

### 7.1 Fluxo de Execução

1. **gerar_fontes_brutas.py**: Script que gera os cenários de fontes simulando bancos de dados do governo.
2. **etl_bronze.py**: Captura esses dados brutos e joga na "pasta fria" (`bronze/`).
3. **etl_silver.py**: Transforma JSON e Bancos e CSVs em dataframes, padroniza, realiza merges e exporta dataset central único.
4. **etl_gold.py**: Carrega o dataset da silver, recorta as informações geográficas, de escola e de tempo para formar 3 tabelas de Dimensão, e cria uma tabela Fato guardando apenas FKs e medidas numéricas, exportando-as como arquivos CSV.

### 7.2 Scripts

| Ordem | Script | Entrada | Saída |
|---:|---|---|---|
| 1 | `gerar_fontes_brutas.py` | Sementes | CSV, JSON e .db em `raw_fontes/` |
| 2 | `etl_bronze.py` | `raw_fontes/*` | Cópia fiel em `bronze/` |
| 3 | `etl_silver.py` | `bronze/*` | `silver/desempenho_integrado.csv` |
| 4 | `etl_gold.py` | `silver/desempenho_integrado.csv` | Arquivos `.csv` em `gold/` |

---

## 8. Dashboard

### 8.1 Visão Geral

O Dashboard será construído utilizando uma ferramenta de visualização de dados (BI), conectando-se aos arquivos CSV gerados na camada Gold. O objetivo é servir como produto de Business Intelligence amigável para tomada de decisão. As especificações de cada painel que devem ser implementadas estão detalhadas abaixo.

### 8.2 Painel 1 - Visão Geral Nacional

**Objetivo:** Analisar a evolução da nota média do ENEM e do IDEB médio em todo o país, servindo como termômetro anual.

#### KPIs

| KPI | Definição | Fórmula |
|---|---|---|
| Média Nacional ENEM | Nota média global em dado ano | `mean(nota_media_enem)` agrupado por `ano_selecionado` |
| Média IDEB Nacional | Índice IDEB global no mesmo ano | `mean(indicador_ideb)` agrupado por `ano_selecionado` |



### 8.3 Painel 2 - Comparação Regional

**Objetivo:** Comparar a nota média e o IDEB por UF e Região.

#### KPIs

| KPI | Definição | Fórmula |
|---|---|---|
| UF Maior Nota | Qual estado lidera o ranking | `idxmax(mean(nota_media_enem))` |
| UF Menor Nota | Qual estado obteve a pior avaliação | `idxmin(mean(nota_media_enem))` |


### 8.4 Painel 3 - Rede Pública x Privada

**Objetivo:** Avaliar a desigualdade no sistema educacional evidenciada entre as dependências administrativas.

#### KPIs

| KPI | Definição | Fórmula |
|---|---|---|
| Gap de Nota | Diferença aritmética direta das médias das redes | `avg(nota_privada) - avg(nota_publica)` |
| Taxa de Aprovação | Percentual médio de alunos aprovados por tipo | `mean(taxa_aprovacao) by (rede)` |


---
----------

## 9. Divisão das Atividades

- ### Gabriel Cabral
	- Arquitetura base do projeto e geração das fontes de dados (`gerar_fontes_brutas.py`).
	- Implementação do script de extração da camada Bronze (`etl_bronze.py`).
	- Definição do Problema de Negócio e preenchimento das métricas das fontes no Relatório.

- ### Joseph Borges 
	- Programação em Python (`pandas`) do processo de limpeza e integração da camada Silver (`etl_silver.py`).
	- Tratamento de nulos, tipagem e cruzamento de dados (ENEM + IDEB + Municípios).
	- Desenho e documentação do Modelo Dimensional (`esquema_estrela_educacao.md`).

- ### Caio Guilherme
	- Conexão da ferramenta de BI aos arquivos CSV da camada Gold.
	- Criação do Dashboard interativo, elaboração das visualizações e extração de insights dos KPIs.
	
- ### Beatriz Freitas
	- Implementação da modelagem em Star Schema na camada Gold (`etl_gold.py`) exportando como CSV.
	- Revisão final de Qualidade, consolidação e preenchimento da documentação visual e técnica no Relatório Final.
