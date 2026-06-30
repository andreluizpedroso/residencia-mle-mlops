# mlops-lab — Credit Card Fraud Detection

![Sprint](https://img.shields.io/badge/Sprint-5%2F12-blueviolet)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
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

Projeto end-to-end de MLOps construído durante a Residência em Machine Learning Engineering.

## Stack

| Componente | Tecnologia |
|------------|-----------|
| Experiment Tracking | MLflow |
| Backend Store | PostgreSQL |
| Artifact Store | MinIO (S3-compatible) |
| API | FastAPI |
| Orquestração | Airflow |
| Monitoramento | Prometheus + Grafana |
| Drift Detection | Evidently AI |
| Feature Store | Feast |
| Container | Docker + Kubernetes (Kind) |
| CI/CD | GitHub Actions |
| Cloud (fase final) | GCP |

## Início rápido

```bash
# 1. Copiar variáveis de ambiente
cp .env.example .env

# 2. Instalar dependências Python
uv sync --extra dev

# 3. Subir a stack local
make up

# 4. Acessar as UIs
# MLflow  → http://localhost:5000
# MinIO   → http://localhost:9001
```

## Comandos

```bash
make up        # Sobe MLflow + PostgreSQL + MinIO
make down      # Para os containers
make test      # Roda pytest
make lint      # Roda ruff check
make format    # Formata código com ruff
make check     # lint + mypy
make help      # Lista todos os comandos
```

## Estrutura

```
mlops-lab/
├── app/           # FastAPI — model serving
├── data/          # Dados (gitignored)
├── pipelines/     # Scripts de treinamento e ingestão
├── monitoring/    # Prometheus + Grafana configs
├── deployment/    # Kubernetes manifests
├── tests/         # pytest
├── docker/        # docker-compose.yml
├── airflow/       # DAGs de retraining
└── mlflow/        # MLflow server config
```
