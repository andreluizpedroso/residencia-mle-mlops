# Sprint 5 — FastAPI Serving + Docker

**Status:** Concluída ✅
**Data:** 2026-06-30

---

## Objetivo

Servir o modelo `fraud-detector@champion` via REST API, com validação automática de schema e containerização — pronta para rodar tanto local quanto dentro do Docker Compose.

---

## Bug crítico encontrado e corrigido: train/serve skew

Antes de escrever a API, foi identificado que o `pipelines/train.py` da Sprint 3 treinava os classificadores em cima de `train.parquet`/`test.parquet` — arquivos onde `Amount` já havia sido escalado pelo `feature_engineering.py` da Sprint 2. Isso significa que o modelo registrado esperava receber `Amount` **já normalizado** (ex: `-0.35`), mas uma API real recebe `Amount` **bruto** (ex: `149.62`). O resultado seria previsões silenciosamente erradas — sem nenhum erro, sem warning — só percebido quando alguém notasse números estranhos em produção.

**Correção:** `pipelines/train.py` foi refatorado para:
- Carregar o CSV bruto diretamente (reproduzindo o split exato da Sprint 2: `test_size=0.2`, `random_state=42`, `stratify=y`)
- Embutir o `StandardScaler` (aplicado só em `Amount`) dentro de um `sklearn.Pipeline`, junto com o classificador, usando `ColumnTransformer`
- O artefato logado no MLflow agora é o `Pipeline` completo, não o classificador isolado — o pré-processamento viaja junto com o modelo

`pipelines/register_model.py` foi re-executado, criando a versão 2 de `fraud-detector` (agora do tipo `Pipeline`), promovida para `champion`. Métricas permaneceram quase idênticas às da Sprint 3, confirmando que o fix corrigiu a arquitetura sem alterar o comportamento do modelo.

---

## O que foi construído

### Arquivos criados / modificados

| Arquivo | Mudança |
|---------|---------|
| `pipelines/train.py` | Refatorado — Pipeline com `ColumnTransformer` embutido (corrige train/serve skew) |
| `app/schemas.py` | Novo — contratos Pydantic: `Transaction`, `PredictionResponse`, `HealthResponse` |
| `app/main.py` | Novo — FastAPI app, `lifespan` para carregar modelo, endpoints `/health` e `/predict` |
| `app/__init__.py` | Novo — torna `app` um pacote Python |
| `docker/Dockerfile.api` | Novo — imagem da API usando `uv sync --frozen` |
| `docker/Dockerfile.mlflow` | Corrigido — adicionado `curl` (healthcheck estava quebrado desde a Sprint 1) |
| `docker/docker-compose.yml` | Atualizado — novo serviço `api`, dependente de `mlflow: service_healthy` |

---

## Fluxo implementado

```
Cliente HTTP
  └── POST /predict { V1..V28, Amount bruto }
        └── Pydantic valida schema (campos obrigatórios, Amount >= 0)
              └── mlflow.sklearn.load_model("models:/fraud-detector@champion")
                    (carregado 1x no startup via lifespan, não por request)
                    └── Pipeline.predict_proba() — escala Amount internamente
                          └── { is_fraud, fraud_probability, model_alias }
```

---

## Bug "de bônus": healthcheck do MLflow

Durante os testes, o container `mlops_mlflow` estava marcado como `unhealthy` havia 6 horas (desde a Sprint 1) — sem que ninguém notasse, porque o serviço funcionava normalmente. Causa: a imagem `ghcr.io/mlflow/mlflow:v2.15.1` não tem `curl` instalado, e o healthcheck (`CMD curl -f .../health`) falhava silenciosamente. Isso só virou um problema real quando o novo serviço `api` precisou de `depends_on: mlflow: condition: service_healthy` para subir com segurança — o compose travou com `dependency failed to start`. Corrigido instalando `curl` no `Dockerfile.mlflow`.

---

## Decisões técnicas

| Decisão | Motivo |
|---------|--------|
| `lifespan` para carregar o modelo | Carrega 1x no startup, falha rápido se o modelo não existir, evita custo de I/O por requisição |
| Pydantic `Transaction` com `Amount: Field(..., ge=0)` | Validação de regra de negócio na borda do sistema, antes de qualquer lógica de predição |
| `Amount` em formato bruto na API | O Pipeline escala internamente — a API nunca repete lógica de pré-processamento |
| Aliases (`@champion`) em vez de número de versão fixo | Trocar o modelo em produção não exige redeploy de código, só mover o alias |
| `MLFLOW_TRACKING_URI` via env var com fallback `localhost` | 12-Factor App — mesmo código roda local e em container, só muda a env var injetada |
| `uv sync --frozen` no Dockerfile | Garante que o container usa exatamente as versões do `uv.lock`, sem "funciona no notebook, quebra em prod" |
| Cache de camadas Docker (manifests antes do código) | Evita reinstalar todas as dependências a cada mudança de código |

---

## Testes realizados

| Teste | Resultado |
|-------|-----------|
| `/health` local (uvicorn direto) | `{"status":"ok","model_loaded":true,"model_alias":"champion"}` |
| `/predict` local — transação legítima (exemplo do schema) | `{"is_fraud":false,"fraud_probability":0.0}` |
| `docker compose build api` + `up` | `mlops_api` sobe e fica `healthy` |
| `/health` containerizado | `{"status":"ok","model_loaded":true,"model_alias":"champion"}` |
| `/predict` containerizado — transação legítima | `{"is_fraud":false,"fraud_probability":0.0}` |
| `/predict` containerizado — padrão de fraude (PCA com alta variância) | `{"is_fraud":true,"fraud_probability":0.99}` |
| `/predict` com payload inválido (campos faltando + `Amount: -50`) | HTTP 422 com lista detalhada de erros de validação |

---

## Validação — Perguntas e Respostas

**P: Por que validamos `Amount >= 0` no Pydantic em vez de deixar o modelo lidar com qualquer valor?**
R: É uma regra de entrada da API, não responsabilidade do modelo. Um valor negativo não faz sentido de negócio — a API deve rejeitar cedo, com erro claro, em vez de deixar o modelo gerar uma previsão "válida" sobre um dado inválido.

**P: O que quebra se o modelo for carregado dentro de `predict()` a cada requisição, em vez de no `lifespan`?**
R: Quebra o estado controlado da aplicação — cada requisição passaria a depender de registry, rede, credenciais e disponibilidade do artefato, tornando a API imprevisível e dificultando health checks, rollback e observabilidade, além do custo de performance.

**P: Por que a env var `MLFLOW_TRACKING_URI` do `docker-compose.yml` sobrescreve o valor do `.env` mesmo com `load_dotenv()` rodando dentro do container?**
R: `load_dotenv()` usa `override=False` por padrão — não sobrescreve variáveis já presentes no ambiente do processo. Como o Docker Compose injeta a env var antes do Python iniciar, ela já existe no ambiente quando `load_dotenv()` roda, e prevalece sobre o `.env`.

---

## Code Review — Nota: 8.5 / 10

**Pontos positivos:** identificação e correção do bug de train/serve skew antes de produção, `lifespan` para carregamento único do modelo, separação schemas/lógica, aliases em vez de versão fixa, healthcheck real, cache de camadas Docker bem pensado.

**Pontos de melhoria:**
- Sem tratamento de erro explícito se `load_model()` falhar no startup (crash sem mensagem clara)
- `predict()` síncrono — aceitável para um modelo, mas bloqueia o event loop sob carga (revisitar na Sprint 7)
- Sem testes automatizados ainda (chega na Sprint 6)
- Threshold de `0.5` para `is_fraud` hardcoded — em fraude, normalmente é uma decisão de negócio calibrada (trade-off precision/recall)

---

## Perguntas de Entrevista — Nota: 9.5 / 10

1. **Modelo novo com feature que o schema não conhece** — assinatura do modelo + validação de schema na API + gate de compatibilidade antes de promover no Registry.
2. **`lifespan` vs variável global no módulo** — falha rápido no startup, ciclo de vida limpo para health check/logs/testes/shutdown, evita efeitos colaterais no import.
3. **Diagnóstico de p99 alto suspeitando de carregamento de modelo** — decompor latência por fase (parse → preprocessamento → inferência → resposta), checar se carregamento ocorre por request, manter modelo em memória por worker com troca de versão fora do caminho crítico.

---

## Próximo passo

**Sprint 6** — CI/CD com GitHub Actions + pytest
- Testes automatizados para `/health` e `/predict`
- Pipeline de CI: lint (`ruff`), type check (`mypy`), testes (`pytest`)
- Build e push automático da imagem Docker da API
- Gate de qualidade antes de merge na `main`
