# Sprint 8 — Data Drift com Evidently AI

**Status:** Concluída ✅  
**Data:** 2026-07-01

---

## Objetivo

Detectar automaticamente quando a distribuição dos dados de produção diverge dos dados de treino, gerando um relatório visual e métricas estruturadas para suporte à decisão de retreino.

---

## O que foi construído

| Arquivo | Mudança |
|---------|---------|
| `pipelines/detect_drift.py` | Script de detecção com `DataDriftPreset` + `DataSummaryPreset` |
| `tests/test_drift.py` | 3 testes: shape, drift intencional, chaves do relatório |
| `pyproject.toml` | Adicionado `evidently>=0.4.0` (instalado: 0.7.21) |
| `README.md` | Sprint 8 marcada como próxima → concluída |

---

## Arquitetura

```
creditcard.csv (referência, 10k amostras)
        +
simulate_current_data() (produção simulada, 2k amostras com drift em V1 e Amount)
        ↓
Evidently Report (DataDriftPreset + DataSummaryPreset)
        ↓
data/reports/drift_report.html  ← visualização no browser
data/reports/drift_report.json  ← métricas estruturadas
```

---

## Resultado do relatório

- **Features analisadas:** 29 (V1–V28 + Amount)
- **Features com drift:** 2 (V1 e Amount — drift intencional)
- **Share drifted:** 6.9%
- **Dataset drift detectado:** False (abaixo do limiar de 50%)
- **Teste estatístico:** Wasserstein distance (normed)

### Por que V1 e Amount driftaram

O código de simulação adicionou ruído intencional:
```python
current["Amount"] = current["Amount"] * rng.normal(loc=1.5, ...)  # +50% na média
current["V1"]     = current["V1"] + rng.normal(loc=0.5, ...)      # deslocado +0.5
```

No relatório HTML, as distribuições referência (cinza) e atual (vermelho) aparecem **separadas** para essas duas features, e **sobrepostas** para as 27 restantes.

---

## Como interpretar o relatório

| Coluna | Significado |
|--------|-------------|
| Reference Distribution | Histograma dos dados de treino |
| Current Distribution | Histograma dos dados de produção |
| Data Drift | Detected = distribuição mudou além do limiar |
| Stat Test | Algoritmo usado (Wasserstein distance para numéricas) |
| Drift Score | Quanto as distribuições divergem — maior = mais diferente |

Ao expandir uma feature, você vê `mean`, `std`, `min`, `max` lado a lado para referência e atual.

---

## Decisões técnicas

| Decisão | Motivo |
|---------|--------|
| `TypedDict` no retorno | Tipagem precisa — mypy sabe exatamente o que a função retorna |
| `reports_dir` como parâmetro | Permite passar `tmp_path` nos testes sem mock de filesystem |
| Evidently 0.7.x API (`evidently.core.report`) | Versão mais nova instalada pelo uv — API antiga (`evidently.report`) foi removida |
| `dataset_drift_detected = share > 0.5` | Convensão: mais de 50% das features driftando = drift sistêmico |
| Referência = amostra de 10k do CSV bruto | Modelo recebe Amount bruto — monitorar na mesma escala que a API recebe |

---

## O que o Evidently faz (e não faz)

O Evidently **só reporta** — não toma ação automaticamente. É o sensor de fumaça, não o bombeiro.

```
Evidently detecta drift
       ↓
Alerta dispara (Grafana / Slack)    ← futuro
       ↓
Time investiga manualmente
       ↓
Decide: retreinar ou não
       ↓
Sprint 11 (Airflow) automatiza o retreino
```

---

## Validação — Perguntas e Respostas

**P: 2 de 29 features driftaram. Retreina imediatamente?**  
R: Não. Drift é sinal de investigação, não ordem de retreino. Avaliar: importância das features, impacto em métricas de negócio (falsos negativos, taxa de fraude), e reclamações operacionais. Retreinar só se performance ou risco forem afetados.

**P: Diferença entre data drift e concept drift?**  
R: Data drift = distribuição das entradas mudou (Amount maior que no treino). Concept drift = relação entrada→saída mudou (mesmo padrão antes legítimo agora é fraude). Evidently detecta data drift bem; concept drift exige labels reais ao longo do tempo.

**P: Risco de usar dataset de 2023 como referência em 2025?**  
R: Referência desatualizada gera alertas falsos — comportamento legítimo evoluído parece "drift". Em produção, usar janela recente estável (ex: últimos 30 dias sem anomalias) como referência, com comparações históricas para contexto.

---

## Code Review — Nota: 7.5 / 10

**Positivo:** TypedDict no retorno, `reports_dir` como parâmetro, separação clara de responsabilidades, testes rápidos e funcionais.

**Pontos de melhoria:**
- Limiar `0.5` hardcoded — extrair para constante `DRIFT_THRESHOLD`
- `simulate_current_data` no módulo de produção — mover para `tests/` ou `scripts/`
- `print` em vez de `logging` estruturado
- Relatório não logado no MLflow — perde rastreabilidade histórica de drift

---

## Próximo passo

**Sprint 9** — Feature Store com Feast  
Centralizar as features de entrada num repositório versionado, separando a lógica de feature engineering do treinamento e do serving.
