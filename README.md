# mlops-lab — Credit Card Fraud Detection

![Sprint](https://img.shields.io/badge/Sprint-11%2F12-blueviolet)
![CI](https://github.com/andreluizpedroso/residencia-mle-mlops/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![MLflow](https://img.shields.io/badge/MLflow-2.15-0194E2?logo=mlflow&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?logo=scikitlearn&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.2-150458?logo=pandas&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-S3--compatible-C72E49?logo=minio&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-v3.4-E6522C?logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-12.0-F46800?logo=grafana&logoColor=white)
![Evidently](https://img.shields.io/badge/Evidently-0.7-6A4C93?logoColor=white)
![Feast](https://img.shields.io/badge/Feast-0.64-FF6B35?logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Kind-326CE5?logo=kubernetes&logoColor=white)
![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.10-017CEE?logo=apacheairflow&logoColor=white)
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
┌──────────────────────────────────────────────────────────────────┐
│                        Docker Compose                            │
│                                                                  │
│  ┌───────────┐  ┌───────────┐  ┌──────────────────────────────┐ │
│  │ PostgreSQL│  │   MinIO   │  │       MLflow Server          │ │
│  │  :5432    │◄─│  :9000    │◄─│          :5000               │ │
│  │ (backend  │  │ (artifact │  │  (experiments + registry)    │ │
│  │  store)   │  │  store)   │  └──────────────────────────────┘ │
│  └───────────┘  └───────────┘              ▲                    │
│                                            │                    │
│  ┌─────────────────────────────────────────┴────────────────┐   │
│  │              FastAPI — Fraud Detection API  :8000         │   │
│  │  GET  /health    → status + modelo carregado             │   │
│  │  POST /predict   → { is_fraud, fraud_probability }       │   │
│  │  GET  /metrics   → métricas Prometheus                   │   │
│  └────────────────────────────┬─────────────────────────────┘   │
│                               │ scrape /metrics a cada 15s      │
│  ┌────────────────────────────▼───────────┐                     │
│  │         Prometheus  :9090              │                     │
│  │  (séries temporais: latência,          │                     │
│  │   throughput, taxa de fraude)          │                     │
│  └────────────────────────────┬───────────┘                     │
│                               │ PromQL                          │
│  ┌────────────────────────────▼───────────┐                     │
│  │         Grafana  :3000                 │                     │
│  │  (dashboard: req/s, p99, fraud rate)   │                     │
│  └────────────────────────────────────────┘                     │
└──────────────────────────────────────────────────────────────────┘
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
| 8 | Data Drift + Model Drift (Evidently AI) | ✅ Concluída |
| 9 | Feature Store (Feast) | ✅ Concluída |
| 10 | Kubernetes (Kind) — deploy declarativo, HPA, health probes | ✅ Concluída |
| 11 | Retraining automático (Airflow) — DAG semanal drift→retrain | ✅ Concluída |
| 12 | Migração para GCP (fase cloud) | ⏳ Próxima |

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

### 2. Subir a stack completa

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
```

---

## Interfaces disponíveis

| Interface | URL | Descrição |
|-----------|-----|-----------|
| MLflow UI | http://localhost:5000 | Experimentos, runs, métricas, Model Registry |
| MinIO Console | http://localhost:9001 | Artefatos: modelos, plots, arquivos |
| MinIO API (S3) | http://localhost:9000 | Endpoint S3-compatível usado pelo MLflow |
| API docs (Swagger) | http://localhost:8000/docs | Endpoints interativos com exemplo de payload |
| API Métricas | http://localhost:8000/metrics | Endpoint Prometheus (latência, throughput, fraude) |
| Prometheus | http://localhost:9090 | Banco de séries temporais — queries PromQL |
| Grafana | http://localhost:3000 | Dashboards operacionais e de negócio (`admin` / `admin`) |
| API via Kubernetes | http://localhost:8080 | Mesma API servida pelo cluster Kind (Sprint 10) |
| Airflow UI | http://localhost:8081 | DAGs, execuções e logs (`admin` / `admin`) (Sprint 11) |

---

## API de detecção de fraude

### `GET /health`

```json
{ "status": "ok", "model_loaded": true, "model_alias": "champion" }
```

### `POST /predict`

**Request:** transação com features `V1`–`V28` (componentes PCA) + `Amount` em valor bruto.

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"V1": -1.36, "V2": -0.07, ..., "Amount": 149.62}'
```

**Response:**

```json
{ "is_fraud": false, "fraud_probability": 0.0012, "model_alias": "champion" }
```

O modelo carregado é sempre o `fraud-detector@champion` do MLflow Model Registry. Para trocar o modelo em produção, basta mover o alias — sem redeploy de código.

---

## Observabilidade

O dashboard **Fraud Detection API** no Grafana (`Dashboards → MLOps`) exibe:

| Painel | O que mede |
|--------|------------|
| Requisições / segundo | Taxa de chegada de tráfego |
| Taxa de Erros 5xx | Proporção de respostas com erro de servidor |
| Taxa de Fraude Detectada | % de transações classificadas como fraude (métrica de negócio) |
| Latência p50 / p90 / p99 | Distribuição de tempo de resposta — p99 = pior caso do 1% mais lento |
| Requisições por endpoint | Volume separado por rota e status HTTP |
| Fraude vs Legítima | Tendência temporal das duas categorias de predição |

---

## Comandos

```bash
# Infraestrutura
make up           # Sobe a stack completa (MLflow + MinIO + API + Prometheus + Grafana)
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

# Kubernetes (Kind) — Sprint 10
make k8s-create   # cria cluster Kind local
make k8s-deploy   # build + load imagem + aplica manifests
make k8s-status   # status dos pods/svc/hpa
make k8s-delete   # remove o cluster

# Airflow — Sprint 11
make airflow-up   # sobe webserver + scheduler + postgres
make airflow-down # para o Airflow
```

---

## Estrutura do projeto

```
mlops-lab/
├── app/                        # FastAPI — model serving
│   ├── main.py                 #   lifespan, /health, /predict, /metrics
│   └── schemas.py              #   contratos Pydantic (Transaction, PredictionResponse)
├── pipelines/                  # Scripts standalone
│   ├── download_data.py        #   ingestão do dataset (Kaggle)
│   ├── feature_engineering.py  #   pré-processamento + split 80/20
│   ├── train.py                #   treinamento com sklearn Pipeline + MLflow tracking
│   ├── register_model.py       #   registro e promoção no Model Registry
│   ├── detect_drift.py         #   detecção de data drift com Evidently AI (Sprint 8)
│   └── materialize_features.py #   materialização de features no Feast (Sprint 9)
├── monitoring/                 # Observabilidade
│   ├── prometheus.yml          #   config de scrape (job: fraud-api → :8000/metrics)
│   └── grafana/
│       ├── provisioning/       #   datasource + dashboard provider (auto-carregados)
│       └── dashboards/         #   fraud_api.json — 6 painéis PromQL
├── tests/                      # pytest
│   ├── conftest.py             #   fixtures: FakeModel, api_client, fraud_api_client
│   ├── test_smoke.py           #   imports e versões mínimas
│   ├── test_api.py             #   testes de /health e /predict (sem MLflow real)
│   ├── test_drift.py           #   testes de detecção de drift (Sprint 8)
│   └── test_features.py        #   testes de materialização Feast (Sprint 9)
├── docker/                     # Containerização
│   ├── docker-compose.yml      #   stack principal: postgres+minio+mlflow+api+prometheus+grafana
│   ├── docker-compose-airflow.yml  # stack Airflow separada (Sprint 11)
│   ├── Dockerfile.mlflow       #   imagem customizada do MLflow
│   └── Dockerfile.api          #   imagem da FastAPI (uv sync --frozen)
├── feature_store/              # Feature Store (Feast) — Sprint 9
│   ├── feature_store.yaml      #   config do projeto (offline=Parquet, online=SQLite)
│   └── features.py             #   entidade + FeatureView (V1-V28, Amount)
├── deployment/                 # Kubernetes (Sprint 10)
│   ├── kind-cluster.yaml       #   cluster Kind com port-mapping :30800→:8080
│   └── k8s/                    #   manifests: namespace, configmap, secret, deploy, svc, hpa
├── airflow/                    # Apache Airflow (Sprint 11)
│   └── dags/
│       └── fraud_retraining_dag.py  # DAG semanal: drift→branch→retrain→register
├── docs/sprints/               # Documentação por sprint
│   └── sprint-01.md … sprint-11.md
├── .github/workflows/
│   └── ci.yml                  # CI: lint + mypy + pytest + docker build
├── data/                       # Dados gerados em runtime (gitignored)
├── pyproject.toml              # Dependências + config de ferramentas
├── uv.lock                     # Lockfile reproduzível
├── Makefile                    # Atalhos de dev
└── .env.example                # Template de variáveis de ambiente
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
