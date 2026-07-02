# Sprint 9 — Feature Store com Feast

**Status:** Concluída ✅
**Data:** 2026-07-01

---

## Objetivo

Centralizar as features num repositório versionado (Feast), eliminando o risco de dessincronização entre treino e serving — o mesmo contrato de features usado nos dois lugares.

---

## O que foi construído

| Arquivo | Mudança |
|---------|---------|
| `feature_store/feature_store.yaml` | Config do projeto Feast (offline=Parquet, online=SQLite) |
| `feature_store/features.py` | Entidade `transaction_id` + FeatureView `transaction_features` |
| `pipelines/materialize_features.py` | Prepara dados + aplica definições + materializa para online store |
| `tests/test_features.py` | 3 testes: colunas obrigatórias, IDs únicos, schema correto |
| `pyproject.toml` | Adicionado `feast>=0.36.0` (instalado: 0.64.0) |

---

## Arquitetura

```
creditcard.csv
      ↓
materialize_features.py
  [1] prepare_feast_data()  →  data/feast/transactions.parquet (offline store)
  [2] store.apply()         →  data/feast/registry.db
  [3] store.materialize()   →  data/feast/online_store.db (SQLite)

Consumidores:
  train.py          →  store.get_historical_features()  (offline)
  API /predict      →  store.get_online_features()      (online, ms)
  detect_drift.py   →  referência versionada
```

---

## Conceitos-chave

### Offline store vs Online store

| | Offline | Online |
|---|---|---|
| Armazenamento | Parquet / data lake | SQLite / Redis |
| Quem usa | `train.py` | API `/predict` |
| Volume | Histórico completo | Features mais recentes |
| Velocidade | Segundos/minutos | Milissegundos |

### Point-in-time correct join

Para cada linha de treino, o Feast busca somente features que existiam até aquele `event_timestamp` — nunca valores calculados depois. Isso evita **data leakage**: o modelo não aprende com informação do futuro.

Exemplo: transação às 10:00 → treino só pode usar features calculadas até 10:00. Uma feature atualizada às 10:05 não existia no momento real da decisão.

### Por que `transaction_id` e `event_timestamp` são obrigatórios

- `transaction_id`: chave de entidade — identifica "para quem" a feature pertence
- `event_timestamp`: marca o momento em que o valor era válido — habilita o point-in-time join

---

## Resultado da materialização

```
284.807 transações → data/feast/transactions.parquet
Materializando transaction_features (2025-07-01 → 2026-07-02) → SQLite
Feature Store pronto.
```

---

## Decisões técnicas

| Decisão | Motivo |
|---------|--------|
| SQLite como online store | Suficiente para dev local sem infraestrutura extra |
| Parquet como offline store | Padrão Feast local; migra para BigQuery/S3 no Sprint 12 |
| `entity_key_serialization_version: 3` | Versão recomendada pelo Feast 0.64 — evita warnings |
| `sys.path.insert` no pipeline | Scripts standalone não herdam `pythonpath` do pytest — necessário para importar `feature_store/` |

---

## Validação — Perguntas e Respostas

**P: Por que o parquet precisa de `transaction_id` e `event_timestamp`?**
R: `transaction_id` é a chave de entidade — o Feast precisa saber "para quem" a feature pertence. `event_timestamp` habilita joins históricos point-in-time corretos, evitando data leakage no treino.

**P: O que acontece se rodar `materialize_features.py` duas vezes?**
R: O online store sobrescreve pelo valor mais recente por chave de entidade — sem duplicação. O offline store (parquet) é regerado. Idempotente na prática.

**P: `get_historical_features()` vs `get_online_features()`**
R: Histórico (offline) → dataset de treino com join point-in-time correto. Online → features atuais em milissegundos para inferência em produção.

---

## Code Review — Nota: 7.0 / 10

**Positivo:** separação clara de responsabilidades, testes cobrindo schema e unicidade, YAML com serialização v3.

**Pontos de melhoria:**
- `pd.date_range` mais eficiente que list comprehension para 284k timestamps
- Script não verifica se parquet já existe antes de regenerar
- `feast>=0.36.0` sem upper bound — pode quebrar com próxima major

---

## Perguntas de Entrevista — Nota: 10 / 10

1. **Feature Stores por ambiente** — separar dev/staging/prod para evitar contaminação de storage físico. Compartilhar apenas contratos/definições versionadas.
2. **SQLite em produção** — inadequado: sem concorrência, sem replicação, sem HA. Usar Redis, DynamoDB, Bigtable ou Cassandra conforme stack e requisitos.
3. **Point-in-time correct join** — busca features válidas até o `event_timestamp` de cada linha. Evita data leakage (usar informação do futuro no treino). Exemplo: transação 10:00 não pode usar feature atualizada às 10:05.

---

## Próximo passo

**Sprint 10** — Kubernetes com Kind
Orquestrar os containers localmente em Kubernetes, preparando a infraestrutura para o deploy em GCP no Sprint 12.
