# Sprint 1 — Setup do Ambiente e Fundamentos MLOps

**Data:** 2026-06-26
**Status:** Em andamento

---

## Objetivo

Construir a fundação de infraestrutura local sobre a qual todas as próximas sprints se apoiam: stack MLflow + PostgreSQL + MinIO rodando via Docker Compose, estrutura do projeto scaffolded, dependências configuradas.

## Problema de Negócio

**Detecção de Fraude em Cartão de Crédito**

Dataset: [Credit Card Fraud Detection — Kaggle](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
- 284.807 transações, 30 features (28 PCA + Time + Amount), target binário `Class`
- ~0.17% de fraudes — desbalanceamento severo
- Padrões de fraude evoluem → concept drift natural → retraining obrigatório

Escolha justificada por: desbalanceamento de classes, concept drift real, alto impacto de negócio, inferência em tempo real, drift de dados monitorável.

---

## Arquitetura

```
PostgreSQL (5432)  ← MLflow backend store (metadados: runs, métricas, params)
MinIO (9000/9001)  ← MLflow artifact store (S3-compatible: modelos, plots)
MLflow (5000)      ← Tracking server + Model Registry UI
```

**Padrão espelhado no GCP (Sprint 12):**
- PostgreSQL → Cloud SQL
- MinIO → GCS (só muda endpoint URL e credenciais)

---

## Decisões Arquiteturais

| Decisão | Escolha | Alternativa descartada | Motivo |
|---------|---------|----------------------|--------|
| Experiment Tracking | MLflow | W&B, Comet | Open source, self-hosted, sem vendor lock-in |
| Backend Store | PostgreSQL | SQLite | Concorrência, ACID, padrão produção |
| Artifact Store | MinIO | Filesystem local | S3-compatible, migração GCP trivial |
| Dependências | uv + pyproject.toml | pip + requirements.txt | Lock file, 10-100x mais rápido |
| Linting | ruff | flake8 + black | Uma ferramenta substitui várias |

---

## Arquivos Criados

```
mlops-lab/
├── .env.example              # Template de variáveis de ambiente
├── .gitattributes            # Normalização LF cross-platform
├── .gitignore                # Python + dados + modelos + .env
├── Makefile                  # make up/down/test/lint/format
├── README.md                 # Documentação inicial
├── pyproject.toml            # Dependências + config ruff/mypy/pytest
├── docker/
│   └── docker-compose.yml   # Stack: MLflow + PostgreSQL + MinIO
├── tests/
│   ├── conftest.py          # Fixtures pytest (sample_transaction)
│   └── test_smoke.py        # Smoke tests de ambiente
└── docs/sprints/
    └── sprint-01.md         # Este arquivo
```

---

## Conceitos Ensinados

- **Backend store vs artifact store** — separação por tipo de dado (metadados leves vs binários pesados)
- **Healthchecks e dependências declarativas** no Docker Compose — evitar race conditions
- **12-Factor App aplicado a ML** — config em env vars, backing services substituíveis, build ≠ run
- **Reprodutibilidade em ML** — 4 pilares: código (git hash), dados (versão), ambiente (lock file), aleatoriedade (random_state)
- **Erros comuns** — SQLite em produção, `latest` em imagens Docker, credenciais no código

---

## Perguntas de Validação

> *(Preenchido com as respostas do usuário)*

**1. Diferença entre backend store e artifact store no MLflow:**

*Resposta:*

**2. `service_completed_successfully` vs `service_healthy` no Docker Compose:**

*Resposta:*

**3. O que muda ao migrar de MinIO para GCS:**

*Resposta:*

**4. Por que separar deps de dev das de produção:**

*Resposta:*

---

## Code Review

> *(Preenchido ao final da sprint)*

**Nota:** —/10

**Pontos positivos:**

**Pontos de melhoria:**

---

## Perguntas de Entrevista

> *(Preenchido ao final da sprint)*
