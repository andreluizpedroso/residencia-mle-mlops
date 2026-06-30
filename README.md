# mlops-lab — Credit Card Fraud Detection

![Sprint](https://img.shields.io/badge/Sprint-7%2F12-blueviolet)
![CI](https://github.com/andreluizpedroso/residencia-mle-mlops/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![MLflow](https://img.shields.io/badge/MLflow-2.15-0194E2?logo=mlflow&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?logo=scikitlearn&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.2-150458?logo=pandas&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-S3--compatible-C72E49?logo=minio&logoColor=white)
![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?logo=uv&logoColor=white)
![Pytest](https://img.shields.io/badge/pytest-8.2-0A9EDC?logo=pytest&logoColor=white)
![Ruff](https://img.shields.io/badge/Ruff-lint%2Fformat-D7FF64?logo=ruff&logoColor=black)

Sistema end-to-end de detecção de fraude em cartão de crédito, construído durante a **Residência em Machine Learning Engineering** — um programa de 12 sprints para dominar MLOps na prática, do experimento local ao deploy em cloud.

---

## O problema

Transações fraudulentas representam menos de **0,17%** do dataset (284.807 transações, 492 fraudes). O desafio vai além da acurácia: um falso negativo (fraude não detectada) tem custo financeiro real para o cliente e para o banco. Um falso positivo (transação legítima bloqueada) prejudica a experiência do usuário. O sistema precisa equilibrar precisão e recall com rastreabilidade completa de cada decisão.

---

## Arquitetura local

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│  ┌───────────┐   ┌───────────┐   ┌───────────────────┐ │
│  │ PostgreSQL│   │   MinIO   │   │  MLflow Server    │ │
│  │  :5432    │◄──│  :9000    │◄──│     :5000         │ │
│  │ (backend  │   │ (artifact │   │ (experiments +    │ │
│  │  store)   │   │  store)   │   │  model registry)  │ │
│  └───────────┘   └───────────┘   └───────────────────┘ │
│                                          ▲              │
│  ┌────────────────────────────────────────────────────┐ │
│  │         FastAPI — Fraud Detection API  :8000       │ │
│  │  GET  /health   → status + modelo carregado        │ │
│  │  POST /predict  → { is_fraud, fraud_probability }  │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Progresso das Sprints

| Sprint | Tema | Status |
|--------|------|--------|
| 1 | Setup: ambiente, scaffold, stack local (MLflow + PostgreSQL + MinIO) | ✅ Concluída |
| 2 | Ingestão de dados, feature engineering | ✅ Concluída |
| 3 | Treinamento + Experiment Tracking (MLflow) | ✅ Concluída |
| 4 | Model Registry + versionamento com aliases | ✅ Concluída |
| 5 | FastAPI serving + Docker + correção de train/serve skew | ✅ Concluída |
| 6 | CI/CD com GitHub Actions + pytest | ✅ Concluída |
| 7 | Observabilidade: Prometheus + Grafana | ✅ Concluída |
| 8 | Data Drift + Model Drift (Evidently AI) | 🔜 Próxima |
| 8 | Data Drift + Model Drift (Evidently AI) | ⏳ Pendente |
| 9 | Feature Store (Feast) | ⏳ Pendente |
| 10 | Kubernetes (Kind) | ⏳ Pendente |
| 11 | Retraining automático (Airflow) | ⏳ Pendente |
| 12 | Migração para GCP (fase cloud) | ⏳ Pendente |

---

## Início rápido

### Pré-requisitos

- Docker + Docker Compose
- [uv](https://docs.astral.sh/uv/getting-started/installation/) instalado

### 1. Configurar ambiente

```bash
cp .env.example .env
uv sync --extra dev
```

### 2. Subir a stack local

```bash
docker compose -f docker/docker-compose.yml up -d
```

### 3. Baixar o dataset

```bash
# Requer conta no Kaggle e ~/.kaggle/kaggle.json configurado
uv run python pipelines/download_data.py
```

### 4. Executar o pipeline completo

```bash
# Feature engineering
uv run python pipelines/feature_engineering.py

# Treinamento + tracking no MLflow
uv run python pipelines/train.py

# Registrar e promover o melhor modelo
uv run python pipelines/register_model.py

# Servir a API (local, fora do Docker)
uv run uvicorn app.main:app --port 8000
```

---

## Interfaces disponíveis

| Interface | URL | Descrição |
|-----------|-----|-----------|
| MLflow UI | http://localhost:5000 | Experimentos, runs, métricas, Model Registry |
| MinIO Console | http://localhost:9001 | Artefatos: modelos, plots, arquivos |
| API docs (Swagger) | http://localhost:8000/docs | Endpoints interativos da API de fraude |
| API Métricas | http://localhost:8000/metrics | Endpoint Prometheus (latência, throughput, fraude) |
| Prometheus | http://localhost:9090 | Banco de séries temporais — queries PromQL |
| Grafana | http://localhost:3000 | Dashboards operacionais e de negócio (admin/admin) |

---

## API de detecção de fraude

### `GET /health`

```json
{
  "status": "ok",
  "model_loaded": true,
  "model_alias": "champion"
}
```

### `POST /predict`

**Request:** transação com features `V1`–`V28` (componentes PCA) + `Amount` em valor bruto (reais/dólares).

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"V1": -1.36, "V2": -0.07, ..., "Amount": 149.62}'
```

**Response:**

```json
{
  "is_fraud": false,
  "fraud_probability": 0.0012,
  "model_alias": "champion"
}
```

O modelo carregado é sempre o `fraud-detector@champion` do MLflow Model Registry. Para trocar o modelo em produção, basta mover o alias — sem redeploy de código.

---

## Comandos

```bash
# Infraestrutura
make up           # Sobe MLflow + PostgreSQL + MinIO
make down         # Para os containers
make logs         # Acompanha logs em tempo real
make ps           # Status dos containers

# Qualidade de código
make lint         # ruff check
make format       # ruff format
make check        # lint + mypy

# Testes
make test         # pytest
make test-cov     # pytest com relatório de cobertura

# Setup
make install      # uv sync --extra dev
make env          # cria .env a partir do .env.example
make help         # lista todos os comandos
```

---

## Estrutura do projeto

```
mlops-lab/
├── app/                   # FastAPI — model serving
│   ├── main.py            #   lifespan, /health, /predict
│   └── schemas.py         #   contratos Pydantic (Transaction, PredictionResponse)
├── pipelines/             # Scripts standalone
│   ├── download_data.py   #   ingestão do dataset (Kaggle)
│   ├── feature_engineering.py  # pré-processamento + split
│   ├── train.py           #   treinamento com sklearn Pipeline + MLflow tracking
│   └── register_model.py  #   registro e promoção no Model Registry
├── tests/                 # pytest
│   ├── conftest.py        #   fixtures: FakeModel, api_client
│   ├── test_smoke.py      #   imports e versões mínimas
│   └── test_api.py        #   testes de /health e /predict
├── docker/                # Containerização
│   ├── docker-compose.yml #   stack completa: postgres + minio + mlflow + api
│   ├── Dockerfile.mlflow  #   imagem customizada do MLflow
│   └── Dockerfile.api     #   imagem da FastAPI (uv sync --frozen)
├── docs/sprints/          # Documentação por sprint
│   ├── sprint-01.md ... sprint-06.md
├── .github/workflows/
│   └── ci.yml             # CI: lint + mypy + pytest + docker build
├── data/                  # Dados (gitignored)
│   ├── raw/               #   creditcard.csv original
│   └── processed/         #   train.parquet / test.parquet
├── pyproject.toml         # Dependências + config de ferramentas
├── uv.lock                # Lockfile reproduzível
├── Makefile               # Atalhos de dev
└── .env.example           # Template de variáveis de ambiente
```

---

## Modelo em produção

| Campo | Valor |
|-------|-------|
| Nome | `fraud-detector` |
| Versão atual | 2 |
| Algoritmo | `sklearn.Pipeline` (StandardScaler + RandomForestClassifier) |
| PR-AUC | 0.8681 |
| Recall (fraudes) | 80.6% |
| Precision (fraudes) | 91.9% |
| Alias | `@champion` |

O modelo é um `Pipeline` autocontido: recebe `Amount` em valor bruto e escala internamente, eliminando o risco de train/serve skew.

---

## CI/CD

Todo push e PR na `main` dispara automaticamente:

1. **Lint** — `ruff check`
2. **Type check** — `mypy app pipelines`
3. **Testes** — `pytest --cov` (8 testes, ~4s, sem infraestrutura externa)
4. **Docker build** — valida que `Dockerfile.api` compila sem erros

Status atual: ![CI](https://github.com/andreluizpedroso/residencia-mle-mlops/actions/workflows/ci.yml/badge.svg)
