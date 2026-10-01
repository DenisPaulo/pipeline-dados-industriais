# Dados

Duas fontes alimentam o pipeline. **Nenhum dado é versionado** (`data/raw/` e a maior parte de `data/processed/` estão no `.gitignore`): tudo é baixado ou gerado na hora, e o pipeline recria os arquivos a cada execução.

| Pasta | Conteúdo | Versionada? |
|---|---|---|
| `data/raw/ai4i/` | `ai4i2020.csv`, exatamente como veio do UCI | Não |
| `data/raw/simulado/` | `leituras_simuladas.csv`, gerado com semente fixa | Não |
| `data/processed/bruto/` | Camada bruta em Parquet, particionada em `data=AAAA-MM-DD/maquina_id=.../` | Não |
| `data/processed/limpo/` | `leituras`, `falhas` e `descartadas` em Parquet (após a limpeza) | Não |
| `data/processed/relatorio.json` | Relatório da limpeza (linhas e motivos de descarte) | Não |

## 1. AI4I 2020 Predictive Maintenance Dataset

Conjunto **sintético** (Stephan Matzka) que reproduz o comportamento de dados reais de manutenção preditiva de uma máquina de usinagem: 10.000 registros com temperatura do ar e do processo, rotação, torque, desgaste da ferramenta e indicação de falha (com o modo: `TWF`, `HDF`, `PWF`, `OSF`, `RNF`).

O pipeline baixa o `.zip` oficial direto do UCI (mesmo método do projeto [manutencao-preditiva-ia](https://github.com/DenisPaulo/manutencao-preditiva-ia)) e extrai o CSV, só na primeira vez:

```
https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip
```

Download manual (alternativa): baixe o `.zip` pelo link acima e coloque o `ai4i2020.csv` em `data/raw/ai4i/`.

**Adaptação feita pelo pipeline.** O AI4I não tem identificador de máquina nem horário. Para exercitar um modelo relacional e séries temporais, cada registro (coluna `UDI`) é atribuído a uma de 10 "máquinas virtuais" (`AI4I-01` a `AI4I-10`) em rodízio, com uma leitura a cada 10 minutos a partir de 2020-01-01. Isso é uma decisão **didática**: não tem significado físico, e as análises por máquina nos dados AI4I não representam máquinas reais.

### Licença e citação

- **Fonte:** UCI Machine Learning Repository, AI4I 2020 Predictive Maintenance Dataset (id 601)
- **Autor:** Stephan Matzka
- **Licença:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **DOI:** [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C)

> AI4I 2020 Predictive Maintenance Dataset [Dataset]. (2020). UCI Machine Learning Repository. https://doi.org/10.24432/C5HS5C

Artigo introdutório:

> S. Matzka, "Explainable Artificial Intelligence for Predictive Maintenance Applications," *2020 Third International Conference on Artificial Intelligence for Industries (AI4I)*, 2020, pp. 69–74. doi: 10.1109/AI4I49448.2020.00023

## 2. Leituras simuladas

`python -m pipeline.simulador` (ou a etapa de ingestão) gera séries por máquina (`SIM-01` a `SIM-08`, 7 dias, uma leitura a cada 5 minutos), com **semente fixa** (`PIPELINE_SEMENTE`, padrão 42): a mesma semente produz exatamente o mesmo arquivo.

Cada série tem ciclo diário de temperatura, ruído, desgaste de ferramenta com trocas e falhas calculadas por regras físicas simplificadas. Depois, o gerador **injeta problemas de qualidade de propósito** para testar a limpeza:

- valores **nulos** (células vazias);
- **outliers** (zero, saturação, temperatura em °C no lugar de K, valores negativos);
- **texto inválido** no lugar de número (`ERRO`);
- **linhas duplicadas** (mesma máquina e instante).
