# Sprint 2 — Pipeline de Dados e Feature Engineering

**Status:** Concluída ✅  
**Data:** 2026-06-26

---

## Objetivo

Construir o pipeline de ingestão e feature engineering: baixar o dataset do Kaggle, transformar os dados brutos em features prontas para treino e logar tudo no MLflow.

---

## O que foi construído

### Arquivos criados

| Arquivo | Função |
|---------|--------|
| `pipelines/download_data.py` | Baixa o dataset do Kaggle e valida integridade com MD5 |
| `pipelines/feature_engineering.py` | Feature engineering + log de artefatos no MLflow |

### Dataset

- **Fonte:** Kaggle — `mlg-ulb/creditcardfraud`
- **Arquivo:** `creditcard.csv` — 143.8MB
- **MD5:** `e90efcb83d69faf99fcab8b0255024de`
- **Linhas:** 284.807 transações
- **Fraudes:** 492 (0.1727%) — dataset severamente desbalanceado

### Feature Engineering

| Decisão | Motivo |
|---------|--------|
| Remover `Time` | Não útil como está; seria útil como hora do dia (Sprint futura) |
| Escalar apenas `Amount` | V1-V28 já são componentes PCA — sem escala real |
| `stratify=y` no split | Dataset desbalanceado — garante proporção de fraudes em treino e teste |
| `fit` só no treino | Evita data leakage — scaler não pode aprender do conjunto de teste |
| Formato Parquet | Compressão + tipos preservados + compatível com Spark/BigQuery |

### Artefatos gerados

| Arquivo | Linhas |
|---------|--------|
| `data/processed/train.parquet` | 227.845 |
| `data/processed/test.parquet` | 56.962 |

### MLflow

- **Experimento:** `fraud-detection-feature-engineering`
- **Run:** `feature-engineering-v1`
- **Run ID:** `17bb3b6b86104c8b9be06b2643eb07b1`
- **Artefatos logados:** `processed/train.parquet`, `processed/test.parquet`

---

## Problemas encontrados e soluções

| Problema | Causa | Solução |
|----------|-------|---------|
| `ModuleNotFoundError: kaggle` | Dependência não estava no pyproject.toml | Adicionado `kaggle>=1.6.0` |
| `UnicodeEncodeError` nos prints | Windows CP1252 não suporta caracteres especiais | Substituído por ASCII puro |
| `AccessDenied` no MinIO | `.env` não carregado antes do boto3 | `load_dotenv()` adicionado antes dos imports do mlflow |
| `UnicodeEncodeError` emoji MLflow | MLflow usa emojis internamente | `PYTHONUTF8=1` via `os.environ.setdefault` |
| MD5 errado | Hash era do ZIP, não do CSV descompactado | Calculado MD5 do CSV real: `e90efcb83d69faf99fcab8b0255024de` |

---

## Validação — Perguntas e Respostas

**P: Por que `stratify=y` é importante em datasets desbalanceados?**  
R: Sem estratificação, o teste pode ter poucas ou nenhuma fraude, tornando a avaliação do modelo irreal. Com estratificação, treino e teste mantêm a mesma proporção de fraudes.

**P: Por que não fazer `fit` do StandardScaler nos dados de teste?**  
R: Causaria data leakage — o scaler aprenderia a média e desvio padrão do teste, contaminando a avaliação. O correto é `fit_transform` no treino e `transform` no teste.

**P: Por que usar `.env` em vez de hardcodar credenciais?**  
R: Segurança (não vazar credenciais no Git) e separabilidade de ambientes (dev/staging/prod têm chaves diferentes). Princípio 12-Factor App, fator III.

---

## Code Review — Nota: 8.0 / 10

**Pontos positivos:**
- Separação clara de responsabilidades por função
- `stratify=y` com comentário explicativo
- Sem data leakage (fit só no treino)
- Type hints em todas as funções
- `load_dotenv()` antes dos imports de MLflow

**Pontos de melhoria:**
- `sklearn Pipeline` não aproveitado como Pipeline real (sem o modelo dentro ainda)
- Sem fallback se MLflow estiver offline — erro difícil de interpretar
- `features` logado como lista Python (serializa como string)
- Sem testes unitários para as funções de transformação

---

## Perguntas de Entrevista — Nota: 9.5 / 10

1. **Data leakage** — exemplo de leakage temporal (média mensal usando dados futuros) — nível sênior
2. **Métricas em desbalanceamento** — PR-AUC vs ROC-AUC, recall em fraude — correto e bem fundamentado
3. **Parquet vs CSV** — armazenamento colunar, compressão, compatibilidade com ecossistema — completo
4. **StandardScaler em produção** — salvar scaler + versionar junto com modelo + schema — além do esperado

**Observação:** Na pergunta 2, PR-AUC deve ser a métrica **principal** em bases muito desbalanceadas, não secundária. ROC-AUC pode dar 0.97 para um modelo que não detecta fraude nenhuma.

---

## Próximo passo

**Sprint 3** — Treinamento de modelo + Experiment Tracking com MLflow  
- Treinar modelo de classificação usando os dados processados
- Logar hiperparâmetros, métricas e o modelo no MLflow
- Comparar múltiplos runs no MLflow UI
- Salvar o pipeline (scaler + modelo) como artefato único
