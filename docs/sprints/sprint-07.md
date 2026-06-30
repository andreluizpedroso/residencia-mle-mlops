# Sprint 7 — Observabilidade: Prometheus + Grafana

**Status:** Concluída ✅
**Data:** 2026-06-30

---

## Objetivo

Adicionar visibilidade operacional e de negócio à API: métricas de latência, throughput e taxa de fraude coletadas pelo Prometheus e visualizadas no Grafana — sem depender de logs manuais ou chamadas ad hoc.

---

## O que foi construído

### Arquivos criados / modificados

| Arquivo | Mudança |
|---------|---------|
| `app/main.py` | Instrumentação automática via `prometheus-fastapi-instrumentator` + `FRAUD_COUNTER` customizado |
| `monitoring/prometheus.yml` | Config de scrape: job `fraud-api` → `api:8000/metrics` a cada 15s |
| `monitoring/grafana/provisioning/datasources/prometheus.yml` | Prometheus como datasource default, provisionado automaticamente |
| `monitoring/grafana/provisioning/dashboards/dashboard.yml` | Provider: lê dashboards de `/etc/grafana/dashboards` |
| `monitoring/grafana/dashboards/fraud_api.json` | Dashboard com 6 painéis (req/s, erros, taxa fraude, latência, por endpoint, fraude vs legítima) |
| `docker/docker-compose.yml` | Novos serviços: `prometheus` (v3.4.0) e `grafana` (v12.0.1) |
| `pyproject.toml` | Deps: `prometheus-fastapi-instrumentator>=7.0.0`, `prometheus-client>=0.20.0` |

---

## Arquitetura da observabilidade

```
FastAPI /predict
  └── FRAUD_COUNTER.labels(result=...).inc()   ← métrica de negócio
  └── Instrumentator middleware                ← métricas automáticas

FastAPI /metrics  ←── Prometheus scrape a cada 15s
  └── http_requests_total{handler, method, status}
  └── http_request_duration_highr_seconds_bucket{le}
  └── fraud_api_predictions_total{result}

Prometheus TSDB (7d retenção)
  └── Grafana consulta via PromQL
        └── Dashboard: 6 painéis
```

---

## Métricas implementadas

### Automáticas (prometheus-fastapi-instrumentator)

| Métrica | Tipo | Labels | O que mede |
|---------|------|--------|------------|
| `http_requests_total` | Counter | `handler`, `method`, `status` | Contagem de requests por rota e status agrupado (2xx/4xx/5xx) |
| `http_request_duration_highr_seconds` | Histogram | — | Latência com 26 buckets (0.01s → 30s) para cálculo de percentis |
| `http_request_size_bytes` | Histogram | `handler` | Tamanho dos payloads recebidos |
| `http_response_size_bytes` | Histogram | `handler` | Tamanho das respostas enviadas |

### Customizada (negócio)

| Métrica | Tipo | Labels | O que mede |
|---------|------|--------|------------|
| `fraud_api_predictions_total` | Counter | `result` | Predições separadas por "fraud" ou "legitimate" |

---

## Dashboard Grafana — 6 painéis

| Painel | Tipo | Query PromQL |
|--------|------|--------------|
| Requisições / segundo | Stat | `sum(rate(http_requests_total[1m]))` |
| Taxa de Erros 5xx | Stat | `rate({status="5xx"}[1m]) / rate(total[1m])` |
| Taxa de Fraude Detectada | Stat | `rate({result="fraud"}[5m]) / rate(total[5m])` |
| Latência por Percentil (p50/p90/p99) | Time series | `histogram_quantile(0.99, rate(_bucket[5m]))` |
| Requisições por Endpoint e Status | Time series | `sum by (handler, status)(rate[1m])` |
| Volume Fraude vs Legítima | Time series | `rate({result="fraud/legitimate"}[5m])` |

---

## Decisões técnicas

| Decisão | Motivo |
|---------|--------|
| Modelo **pull** do Prometheus | A API não precisa saber quem a monitora; se o Prometheus cair, a API continua funcionando |
| `excluded_handlers=["/metrics"]` | Evita que scrapes do Prometheus gerem ruído artificial em `http_requests_total` |
| `Counter` em vez de `Gauge` para predições | Predições são eventos acumulados — Counter nunca diminui, compatível com `rate()` |
| Labels `{result="fraud"/"legitimate"}` | Uma série com label > dois counters separados: permite `sum by (result)` e proporções |
| Namespace `fraud_api_` no metric name | Evita colisão com outras métricas no mesmo Prometheus |
| Provisioning automático do Grafana | Datasource e dashboard carregados sem ação manual, reproduzível via `docker compose up` |
| Versões fixadas nos serviços Docker | `prom/prometheus:v3.4.0`, `grafana/grafana:12.0.1` — evita quebras com `latest` |
| Retenção de 7 dias (`--storage.tsdb.retention.time=7d`) | Suficiente para análise operacional; dados históricos longos requerem remote storage (Thanos/Mimir) |

---

## Validação — Perguntas e Respostas

**P: O que acontece no Grafana se a API ficar down por 30 segundos?**
R: O Prometheus não consegue coletar `/metrics` e não recebe dados retroativamente. O Grafana mostra lacunas nos gráficos (linha interrompida, "no data" ou queda para zero, dependendo do painel).

**P: Por que `Counter` e não `Gauge` para contar predições?**
R: Predições são eventos acumulados — o valor só cresce. `Gauge` serve para valores que sobem e descem (memória, workers, fila). Usar `Gauge` para predições poderia distorcer o `rate()` se o valor fosse incorretamente decrementado.

**P: A query de taxa de fraude pode retornar `NaN` nas primeiras requisições. Por quê?**
R: `rate()` com janela `[5m]` precisa de pontos suficientes na janela para calcular uma taxa confiável. Se o denominador ainda for zero (sem dados), a divisão resulta em `NaN`. Estabiliza após alguns scrapes com tráfego real.

---

## Code Review — Nota: 8.5 / 10

**Pontos positivos:** excluded_handlers sem poluição, namespace correto no metric name, labels semânticos, provisioning automático, versões fixadas nos serviços, noValue configurado nos painéis.

**Pontos de melhoria:**
- Sem alertas configurados (Prometheus Alertmanager ou Grafana alerts) — observar é bom, alertar é melhor
- `GF_SECURITY_ADMIN_PASSWORD: admin` como default — aceitável para dev local, mas deve vir de secret em produção
- Dashboard sem anotações de deploy para correlacionar mudanças de modelo com variações nas métricas

---

## Perguntas de Entrevista — Nota: 9.5 / 10

1. **Taxa de fraude disparou para 35%** — investigar em sequência: artefato de medição (volume, erros, restart, model_alias), depois bug (deploy, latência, respostas repetidas), depois fenômeno real (feature distribution, IPs concentrados vs drift distribuído).
2. **Latência do `predict_proba()` isolada** — novo `Histogram("fraud_api_model_inference_seconds")` medindo só o bloco de inferência com `time.perf_counter()`, sem alterar as métricas existentes.
3. **Dados do mês passado** — Prometheus retém 7 dias; buscar em logs, data lake ou banco de eventos. Para o futuro: retenção maior ou remote storage (Thanos, Cortex/Mimir).

---

## Interfaces disponíveis após Sprint 7

| Interface | URL |
|-----------|-----|
| API Swagger | http://localhost:8000/docs |
| API Métricas | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin) |

---

## Próximo passo

**Sprint 8** — Data Drift + Model Drift com Evidently AI
- Detectar quando a distribuição dos dados de entrada muda em relação ao treino
- Detectar quando as predições do modelo começam a se desviar do esperado
- Gerar relatórios de drift periódicos integrados ao pipeline
