# Sprint 12 — Migração para GCP (fase cloud)

**Status:** Concluída ✅ (conceitual/IaC-only — nada aplicado no GCP)
**Data:** 2026-07-06

---

## Objetivo

Explicar e escrever, em Terraform, exatamente o que muda ao migrar o stack local (Postgres, MinIO, containers Docker/Kind) para GCP (Cloud SQL, GCS, Cloud Run) — sem provisionar nenhum recurso real.

## Decisão de custo

O usuário optou explicitamente por não gastar com GCP. Cloud SQL não tem tier "always free" permanente (diferente de Cloud Run e GCS), então **todo o sprint ficou como exercício de arquitetura**: os `.tf` foram escritos e revisados linha a linha, mas `terraform apply` nunca foi executado. Se um dia for necessário rodar de verdade, a rota sem custo para o banco é self-hosting Postgres numa VM `e2-micro` (free tier), ou uso pontual do crédito de $300/90 dias de conta nova do GCP com teardown imediato.

---

## O que foi escrito

| Arquivo | O que faz |
|---------|-----------|
| `deployment/gcp/cloud_sql.tf` | Cloud SQL (Postgres) substituindo o container `postgres` do MLflow backend store |
| `deployment/gcp/gcs.tf` | Bucket GCS substituindo o container `minio` como artifact store |
| `deployment/gcp/cloud_run.tf` | Serviços Cloud Run (`mlflow`, `api`) substituindo os containers locais e os manifests de Kind do Sprint 10 |

---

## Mapeamento local → GCP

| Componente local | Componente GCP | O que muda |
|---|---|---|
| `postgres` (container) | Cloud SQL | Só host/credenciais — MLflow continua falando `postgresql://` puro |
| `minio` (container, S3-compatible) | GCS | Driver muda (`s3://` → `gs://`); credenciais somem, viram Application Default Credentials |
| Containers Docker / manifests Kind (Sprint 10) | Cloud Run | Escala por concorrência de requests (não CPU); precisa de Artifact Registry + VPC connector para alcançar o Cloud SQL |

---

## Conceitos-chave

### Application Default Credentials (ADC)

Mecanismo do GCP para autenticar automaticamente pela identidade do serviço (service account do Cloud Run), sem access key/secret explícitos — elimina a classe inteira de risco de "chave vazada em log ou imagem".

### IAM database authentication (Cloud SQL)

Alternativa a usuário/senha: o Cloud SQL aceita a identidade da service account e emite tokens OAuth de curta duração automaticamente — sem segredo estático para rotacionar.

### Cloud Run: escala por concorrência, não por CPU

Diferença central em relação ao HPA do Sprint 10 (`api-hpa.yaml`, que escala por `averageUtilization: 70` de CPU): no Cloud Run, o `scaling` de cada serviço reage a quantas requests simultâneas cada instância está processando.

### Cloud SQL Auth Proxy / VPC Access Connector

Cloud Run é serverless e não vive dentro de uma VPC por padrão — o `google_vpc_access_connector` é a ponte necessária para alcançar o Cloud SQL via IP privado, papel equivalente ao Auth Proxy localmente.

### Lifecycle rules no GCS

Substituem arquivamento manual: artefatos com +90 dias mudam de `STANDARD` para `NEARLINE` automaticamente — economia sem intervenção humana.

---

## Trade-off mais importante do sprint

**Cloud Run vs. reaproveitar os manifests k8s do Sprint 10 num GKE.** Cloud Run foi o alvo escolhido (free tier real, zero cluster para administrar), mas isso significa reescrever a orquestração do zero em vez de apontar o YAML existente para um cluster gerenciado. Numa empresa com investimento maduro em manifests k8s, GKE Autopilot tende a vencer por continuidade operacional — a escolha de Cloud Run aqui foi guiada pela restrição de custo/simplicidade do projeto, não por superioridade técnica geral.

---

## Próximo passo

Nenhum — este era o último sprint da residência (12/12). Modo agora é consolidação/revisão para fixação e entrevistas.
