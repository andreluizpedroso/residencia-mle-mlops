# Sprint 6 — CI/CD com GitHub Actions + pytest

**Status:** Concluída ✅
**Data:** 2026-06-30

---

## Objetivo

Transformar verificação manual em verificação automática e obrigatória: todo push/PR na `main` dispara lint, type check, testes e build da imagem Docker, com feedback em menos de 2 minutos.

---

## O que foi construído

### Arquivos criados / modificados

| Arquivo | Mudança |
|---------|---------|
| `.github/workflows/ci.yml` | Novo — workflow de CI com dois jobs: quality e docker-build |
| `tests/test_api.py` | Novo — 5 testes de API com FakeModel (sem MLflow real) |
| `tests/conftest.py` | Atualizado — FakeModel, api_client, fraud_api_client fixtures |
| `pyproject.toml` | `httpx` em dev deps, `pythonpath=[.]`, `python_version=3.12`, per-file E402 ignores |
| `app/main.py` | `ml_models: dict[str, Any]`, remove type:ignore desnecessário |
| `pipelines/train.py` | `str(run.info.run_id)`, remove type:ignore desnecessários |
| `pipelines/download_data.py` | `Path.open()` em vez de `open()`, remove type:ignore redundante |
| `pipelines/feature_engineering.py` | Correções automáticas de lint (isort, f-strings vazias) |
| `pipelines/register_model.py` | Correções automáticas de lint (isort, f-strings vazias) |
| `uv.lock` | Atualizado com httpx e dependências de dev |

---

## Fluxo do CI

```
git push / PR aberto
  └── GitHub Actions dispara ci.yml
        ├── Job 1: quality (ubuntu-latest)
        │     ├── uv sync --frozen --extra dev
        │     ├── ruff check .         → lint
        │     ├── mypy app pipelines   → type check
        │     └── pytest --cov         → 8 testes, ~4s
        │           └── ✅ Success (50s)
        └── Job 2: docker-build (ubuntu-latest, precisa de quality)
              └── docker build -f docker/Dockerfile.api -t mlops-api:ci .
                    └── ✅ Success (27s)

Total: 1m 21s
```

---

## Estratégia de teste: FakeModel

Os testes da API rodam sem MLflow, MinIO ou PostgreSQL. O modelo real é substituído por um `FakeModel` via `monkeypatch` do pytest:

```python
class FakeModel:
    def predict_proba(self, X: object) -> np.ndarray:
        return np.array([[1 - self.fraud_probability, self.fraud_probability]])
```

`monkeypatch.setattr("app.main.mlflow.sklearn.load_model", lambda uri: FakeModel())` substitui o carregamento antes do `lifespan` rodar — a API sobe completa, mas com um modelo controlado.

**O que os testes validam:** contrato da API (schema, rotas, formato de resposta, validação Pydantic). **O que não validam:** qualidade do modelo real (isso é responsabilidade das métricas do MLflow: PR-AUC, recall etc.).

---

## Correções de qualidade detectadas ao preparar o CI

| Problema | Causa | Correção |
|----------|-------|----------|
| `mypy` quebrava com erro de sintaxe numpy | `python_version = "3.11"` mas interpretador real é 3.12 | Alinhado para `3.12` |
| E402 em 4 arquivos | `load_dotenv()` antes de imports mlflow/boto3 — intencional | `per-file-ignores` com comentário explicativo |
| `open()` em vez de `Path.open()` | PTH123 — best practice pathlib | Corrigido em `download_data.py` |
| F541 — f-strings sem `{}` | `f"texto"` em vez de `"texto"` | Corrigido automaticamente pelo `ruff --fix` |
| I001 — imports fora de ordem | isort não respeitado | Corrigido automaticamente pelo `ruff --fix` |
| `ml_models: dict[str, object]` | mypy não resolve `predict_proba` em `object` | Trocado para `dict[str, Any]` |
| `pythonpath` ausente no pytest | `import app` falhava no CI | `pythonpath = ["."]` no `pyproject.toml` |

---

## Decisões técnicas

| Decisão | Motivo |
|---------|--------|
| `uv sync --frozen` | Reprodutibilidade: CI e dev usam exatamente as versões do `uv.lock` |
| `needs: quality` no docker-build | Não faz sentido buildar imagem se os testes falharam |
| VMs separadas por job | Isolamento real: docker-build valida do zero, sem estado do job anterior |
| FakeModel com `monkeypatch` | Testes rápidos (~4s), sem dependência de infraestrutura externa |
| Dois jobs em vez de um | Permite identificar exatamente onde falhou: qualidade ou build |

---

## Resultado no GitHub Actions

```
Run #1 — feat(sprint-6): CI/CD com GitHub Actions, testes de API e lint limpo
Status: ✅ Success
Duration: 1m 21s
  Lint, type check & tests  →  50s ✅
  Build da imagem da API    →  27s ✅
```

---

## Validação — Perguntas e Respostas

**P: Por que `uv sync --frozen --extra dev` e não só `--frozen`?**
R: `--extra dev` instala as dependências do grupo `[dev]` (pytest, ruff, mypy, httpx). Sem isso, o CI instalaria apenas a aplicação, sem as ferramentas de qualidade — os checks falhariam por falta das ferramentas, não por bugs no código.

**P: `test_predict_legitimate_transaction` prova que o modelo real classifica a transação como legítima?**
R: Não. Prova que a API responde corretamente quando o modelo retorna probabilidade baixa. O FakeModel é controlado — testa contrato, schema, fluxo da rota e formato da resposta. A qualidade do modelo é responsabilidade das métricas do MLflow.

**P: Por que `docker-build` usa uma VM separada em vez da mesma do job `quality`?**
R: Isolamento — cada `runs-on: ubuntu-latest` é uma VM nova e limpa. O `docker-build` valida que a imagem constrói do zero, sem aproveitar cache ou arquivos gerados pelo job anterior. Mais confiável e mais próximo de um ambiente real de build.

---

## Code Review — Nota: 8.5 / 10

**Pontos positivos:** workflow simples e focado, `--frozen` garante reprodutibilidade, FakeModel bem projetado, monkeypatch no ponto exato de integração, cobertura dos caminhos de erro.

**Pontos de melhoria:**
- Branch protection não configurada — CI existe mas não bloqueia push direto na `main`
- Docker build sem cache de layers — lento em imagens maiores
- Badge de status do CI ausente no `README.md`

---

## Perguntas de Entrevista — Nota: 9.5 / 10

1. **8 minutos de CI** — separar por tipo (unit → PR → pre-deploy), cache de uv/deps, `pytest-xdist` para paralelização, execução seletiva por mudança de arquivo.
2. **"Passa no meu computador"** — reprodutibilidade: em ML, versões de mlflow/sklearn/pandas/Python/OS mudam comportamento. CI cria ambiente padronizado e prova que funciona fora de uma única máquina.
3. **Testar modelo real sem MLflow server** — model fixture local: artefato de teste versionado no repo, carregado via `load_model` apontando para caminho local. Testa contrato real do modelo sem infraestrutura.

---

## Próximo passo

**Sprint 7** — Observabilidade: Prometheus + Grafana
- Expor métricas da API: latência por endpoint, contagem de requisições, taxa de fraude detectada
- Endpoint `/metrics` para o Prometheus coletar
- Dashboard no Grafana com os principais indicadores operacionais
