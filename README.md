# mlops-lab — Credit Card Fraud Detection

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
