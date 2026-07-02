# Sprint 10 — Kubernetes com Kind

**Status:** Concluída ✅
**Data:** 2026-07-02

---

## Objetivo

Orquestrar a API de fraude em Kubernetes local (Kind), introduzindo conceitos de deploy declarativo, health checks, escalabilidade automática (HPA) e isolamento por namespace — preparando o caminho para o GCP no Sprint 12.

---

## O que foi construído

| Arquivo | O que faz |
|---------|-----------|
| `deployment/kind-cluster.yaml` | Cluster Kind com port-mapping 30800 → localhost:8080 |
| `deployment/k8s/namespace.yaml` | Namespace `fraud-detection` — isolamento lógico |
| `deployment/k8s/api-configmap.yaml` | Variáveis de ambiente não-secretas (URLs do MLflow/MinIO) |
| `deployment/k8s/api-secret.yaml` | Credenciais MinIO — separadas do ConfigMap |
| `deployment/k8s/api-deployment.yaml` | 2 réplicas da API com readiness/liveness probes |
| `deployment/k8s/api-service.yaml` | NodePort 30800 → exposto em localhost:8080 |
| `deployment/k8s/api-hpa.yaml` | HPA: escala de 2 a 5 pods quando CPU > 70% |
| `Makefile` | Targets: `k8s-create`, `k8s-deploy`, `k8s-status`, `k8s-delete` |

---

## Arquitetura

```
localhost:8080
      ↓ port-mapping (Kind)
NodePort :30800
      ↓ kube-proxy
Service fraud-api (ClusterIP)
      ↓ label selector app=fraud-api
Pod 1 (fraud-api)   Pod 2 (fraud-api)
      ↓                   ↓
  /health → 200       /health → 200
  Modelo carregado do MLflow (host.docker.internal:5000)
```

---

## Comandos

```bash
# Criar cluster
make k8s-create

# Build da imagem + load no Kind + aplicar manifests
make k8s-deploy

# Verificar status
make k8s-status

# Testar
curl http://localhost:8080/health

# Remover cluster
make k8s-delete
```

---

## Conceitos-chave

### Deployment vs Docker Compose

| | Docker Compose | Kubernetes Deployment |
|---|---|---|
| Restart automático | sim | sim |
| Múltiplas réplicas | manual | declarativo (`replicas: 2`) |
| Rolling update | não | sim |
| Health checks | healthcheck | readiness + liveness probes |
| Escalabilidade automática | não | HPA |

### ReadinessProbe vs LivenessProbe

- **Readiness**: "o pod está pronto para receber tráfego?" — Kubernetes não envia requisições até passar
- **Liveness**: "o pod ainda está vivo?" — Kubernetes reinicia se falhar

### HPA (Horizontal Pod Autoscaler)

Monitora CPU dos pods e escala de 2 a 5 réplicas automaticamente quando a utilização média ultrapassa 70%.

### ConfigMap vs Secret

- **ConfigMap**: variáveis não-sensíveis (URLs, flags) — visível em texto plano
- **Secret**: credenciais — codificado em base64, com RBAC mais restrito

---

## Resultado do teste

```
# Pods rodando
NAME                         READY   STATUS    RESTARTS   AGE
fraud-api-6f4d469b48-8fz6j   1/1     Running   0          57s
fraud-api-6f4d469b48-fhtdw   1/1     Running   0          57s

# API respondendo
GET  http://localhost:8080/health
→ {"status":"ok","model_loaded":true,"model_alias":"champion"}

POST http://localhost:8080/predict
→ {"is_fraud":false,"fraud_probability":0.0,"model_alias":"champion"}
```

---

## Próximo passo

**Sprint 11** — Retraining automático com Airflow
