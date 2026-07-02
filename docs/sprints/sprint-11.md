# Sprint 11 — Retraining Automático com Airflow

**Status:** Concluída ✅
**Data:** 2026-07-02

---

## Objetivo

Automatizar o ciclo de detecção de drift → retreino → registro do modelo com Apache Airflow, eliminando a necessidade de execução manual dos scripts e adicionando observabilidade, retry e histórico de execuções.

---

## O que foi construído

| Arquivo | O que faz |
|---------|-----------|
| `airflow/dags/fraud_retraining_dag.py` | DAG semanal: drift → branch → retrain → register |
| `docker/docker-compose-airflow.yml` | Stack Airflow: webserver + scheduler + postgres |
| `Makefile` | Targets: `airflow-up`, `airflow-down` |

---

## Arquitetura do DAG

```
detect_drift
      ↓
should_retrain (branch)
      ↓                    ↓
retrain_model         skip_retraining
      ↓                    ↓
register_model            done
      ↓
    done
```

**Schedule:** toda segunda-feira às 02:00 UTC (`0 2 * * 1`)

---

## Tasks do DAG

| Task | Tipo | O que faz |
|------|------|-----------|
| `detect_drift` | PythonOperator | Roda `detect_drift.py`, publica resultado no XCom |
| `should_retrain` | BranchPythonOperator | Se share > 10% → retrain; senão → skip |
| `retrain_model` | BashOperator | Executa `pipelines/train.py` |
| `register_model` | BashOperator | Executa `pipelines/register_model.py` |
| `skip_retraining` | EmptyOperator | Caminho alternativo sem ação |
| `done` | EmptyOperator | Ponto de convergência final |

---

## Conceitos-chave

### XCom (Cross-Communication)

Mecanismo do Airflow para passar dados entre tasks. A task `detect_drift` faz `xcom_push` do resultado; `should_retrain` faz `xcom_pull` para ler o share de drift.

### BranchPythonOperator

Retorna o `task_id` da próxima task a executar. Tasks não selecionadas são marcadas como `skipped` (não como falha).

### trigger_rule="none_failed_min_one_success"

A task `done` executa se ao menos um caminho (retrain ou skip) completou com sucesso — sem essa regra, ela só executaria se todos os predecessores completassem.

### LocalExecutor

Executa tasks em paralelo usando processos locais (sem Celery/Redis). Suficiente para um scheduler com poucos DAGs.

---

## Stack Airflow

```
docker-compose-airflow.yml
├── airflow-db (PostgreSQL :5433)   ← metadata do Airflow (separado do MLflow)
├── airflow-init                    ← inicializa DB + cria usuário admin
├── airflow-scheduler               ← executa as tasks
└── airflow-webserver (:8081)       ← UI de monitoramento
```

**Acesso:** http://localhost:8081 (`admin` / `admin`)

### Volumes montados

- `airflow/dags/` → `/opt/airflow/dags/` — DAGs são lidos automaticamente
- Raiz do projeto → `/opt/airflow/project/` — scripts Python disponíveis para as tasks

---

## Comandos

```bash
# Subir Airflow
make airflow-up

# Acessar UI
open http://localhost:8081

# Parar
make airflow-down
```

---

## Próximo passo

**Sprint 12** — Migração para GCP
Substituir PostgreSQL local por Cloud SQL, MinIO por GCS, e fazer deploy no Cloud Run ou GKE.
