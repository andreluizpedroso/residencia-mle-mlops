# Sprint 1 — Setup do Ambiente e Fundamentos MLOps

**Data:** 2026-06-26
**Status:** Concluída ✅

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

Backend store guarda metadados (runs, métricas, parâmetros, tags) — PostgreSQL. Artifact store guarda arquivos binários (modelos, plots, .pkl) — MinIO. Separação justificada: banco relacional é otimizado para writes frequentes e queries estruturadas; object storage é otimizado para arquivos grandes e acessos esporádicos.

**2. `service_completed_successfully` vs `service_healthy` no Docker Compose:**

`service_healthy`: daemon rodando e saudável (PostgreSQL, MinIO). `service_completed_successfully`: container executou uma tarefa e encerrou com sucesso (minio-init). Padrão equivalente ao Init Container do Kubernetes.

**3. O que muda ao migrar de MinIO para GCS:**

Remove `minio` e `minio-init` do docker-compose. Troca `MLFLOW_S3_ENDPOINT_URL` (removida), `AWS_ACCESS_KEY_ID/SECRET` → `GOOGLE_APPLICATION_CREDENTIALS`, `s3://` → `gs://` no `default-artifact-root`. PostgreSQL inalterado. Nenhuma linha de código de treinamento muda.

**4. Por que separar deps de dev das de produção:**

Imagem Docker de produção fica menor, mais rápida no build e deploy, e com menor superfície de ataque (cada pacote extra é um CVE potencial). `pytest`, `ruff`, `mypy` nunca precisam estar em produção.

---

## Code Review

**Nota: 7.5/10** (após correções aplicadas: 8.5/10)

**Pontos positivos:**
- Healthchecks e cadeia de dependências declarativa (`service_completed_successfully`)
- Volumes nomeados com separação `down` vs `down-v`
- `Dockerfile.mlflow` minimalista — extensão cirúrgica da imagem base
- `pyproject.toml` como source of truth, separação prod/dev
- `.gitattributes` para normalização de line endings cross-platform

**Pontos corrigidos após code review:**
- `minio/minio:latest` → pinado para `RELEASE.2025-09-07` (reprodutibilidade)
- `mc anonymous set public` removido (segurança)
- `.dockerignore` adicionado (não envia `.venv` ao Docker daemon)
- Comparação de versão por string → `packaging.Version` (corretude)

---

## Perguntas de Entrevista

**Nota geral: 8.5/10**

**Q1 — SQLite → PostgreSQL (8/10):** Problemas de concorrência e sequência de migração corretos. Gap: MLflow não tem migração nativa SQLite→Postgres, precisaria de `pgloader` ou ETL customizado.

**Q2 — Alembic (8.5/10):** Entendimento do risco de race condition. Gap: a solução técnica é `pg_try_advisory_lock` + migrações como step separado no pipeline de deploy, nunca responsabilidade do servidor.

**Q3 — Reprodutibilidade (9/10):** Resposta mais completa. Gap: MLflow captura git commit automaticamente (`mlflow.source.git.commit`); `mlflow.sklearn.log_model(pipeline)` serializa preprocessamento + modelo juntos eliminando drift de features.
