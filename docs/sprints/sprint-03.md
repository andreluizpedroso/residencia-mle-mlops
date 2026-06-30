# Sprint 3 — Treinamento de Modelo + Experiment Tracking

**Status:** Concluída ✅  
**Data:** 2026-06-30

---

## Objetivo

Treinar modelos de classificação para detecção de fraude e rastrear todos os experimentos no MLflow — parâmetros, métricas, artefatos e o modelo serializado.

---

## O que foi construído

### Arquivo criado

| Arquivo | Função |
|---------|--------|
| `pipelines/train.py` | Treina múltiplos classificadores e loga tudo no MLflow |

### Dependência adicionada

| Pacote | Motivo |
|--------|--------|
| `matplotlib>=3.9.0` | Geração da matriz de confusão como artefato visual |

---

## Modelos treinados

| Modelo | Hiperparâmetros principais |
|--------|---------------------------|
| Regressão Logística | `class_weight="balanced"`, `C=1.0`, `max_iter=1000` |
| Random Forest | `n_estimators=100`, `class_weight="balanced"`, `n_jobs=-1` |

Ambos treinados no experimento `fraud-detection-training`, cada um em um **run separado** no MLflow.

---

## Resultados

| Métrica | Regressão Logística | Random Forest |
|---------|--------------------:|-------------:|
| precision | 0.0589 | **0.9195** |
| recall | **0.9184** | 0.8163 |
| f1 | 0.1106 | **0.8649** |
| roc_auc | **0.9714** | 0.9673 |
| pr_auc | 0.7199 | **0.8664** |

**Conclusão:** Random Forest é o modelo mais sólido pelo PR-AUC (0.8664 vs 0.7199) e pelo equilíbrio precision/recall. A Regressão Logística tem recall superior mas precision de 5.9% — operacionalmente insustentável (94 falsos alarmes para cada fraude detectada).

---

## Artefatos gerados

| Artefato | Local (MinIO) |
|----------|--------------|
| Modelo serializado (LR) | `mlflow/artifacts/.../model/` |
| Modelo serializado (RF) | `mlflow/artifacts/.../model/` |
| `confusion_matrix_logistic_regression.png` | `mlflow/artifacts/.../plots/` |
| `confusion_matrix_random_forest.png` | `mlflow/artifacts/.../plots/` |

---

## Decisões técnicas

| Decisão | Motivo |
|---------|--------|
| `class_weight="balanced"` | Dataset com 0.17% de fraudes — sem isso, modelo ignora a classe minoritária |
| `matplotlib.use("Agg")` antes de qualquer import | Backend sem display — funciona em CI/CD e Docker sem X11 |
| `zero_division=0` nas métricas | Evita crash se modelo não prediz nenhum positivo (comum nas primeiras iterações) |
| `n_jobs=-1` no Random Forest | Usa todos os núcleos da CPU — treino ~6x mais rápido sem custo |
| MODELS como dicionário | Loop único no main() — adicionar novo modelo = uma linha |
| `with mlflow.start_run() as run` | Captura run_id de forma limpa sem depender de `mlflow.active_run()` |

---

## Warnings identificados (a corrigir na Sprint 4)

```
Model logged without a signature and input example.
```

Sem `input_example`, o MLflow não sabe o schema de entrada do modelo. Corrigido na Sprint 4 com Model Registry e assinatura explícita.

---

## Validação — Perguntas e Respostas

**P: Por que criar um run separado para cada modelo em vez de sobrescrever?**  
R: Para manter histórico, permitir comparação e garantir reprodutibilidade. Sobrescrever destrói o histórico de experimentos.

**P: Qual métrica priorizar para detecção de fraude e por quê?**  
R: Recall da classe Fraude é a métrica de negócio principal — o custo de um falso negativo (fraude não detectada) é maior que um falso positivo (alarme indevido). PR-AUC é a métrica técnica mais adequada para datasets desbalanceados.

**P: Por que `matplotlib.use("Agg")` precisa vir antes do `import pyplot`?**  
R: O `pyplot` inicializa o backend no momento do import. Depois disso, `use("Agg")` chega tarde demais.

---

## Code Review — Nota: 7.5 / 10

**Pontos positivos:** separação de funções, `Agg` antes do import, `zero_division=0`, `n_jobs=-1`, dicionário de modelos extensível.

**Pontos de melhoria:**
- Sem `input_example` no `log_model` → warning no MLflow (Sprint 4)
- `get_params()` pode gerar valores não-serializáveis em modelos mais complexos
- `PLOTS_DIR` global acoplado à função (dificulta testes unitários)
- Sem mensagem clara se `data/processed/` não existir

---

## Perguntas de Entrevista — Nota: 8.5 / 10

1. **Escolha de modelo** — correto priorizar recall, mas resposta omitiu o custo de precision=5.9% (94 falsos alarmes por fraude). A escolha técnica correta pelo PR-AUC é o Random Forest.

2. **PR-AUC vs ROC-AUC** — perfeita. ROC-AUC é enganosa em datasets desbalanceados por incluir os verdadeiros negativos, que são maioria. PR-AUC foca na classe positiva.

3. **Melhorar recall do RF** — excelente. Ajuste de limiar (threshold) como primeira opção é a abordagem correta — sem retreinar, sem mais dados.

---

## Próximo passo

**Sprint 4** — Model Registry + versionamento de artefatos  
- Registrar o melhor modelo no MLflow Model Registry
- Promover modelo para estágios: `Staging` → `Production`
- Adicionar `input_example` e signature para resolver o warning da Sprint 3
- Carregar modelo do registry para inferência (em vez de carregar o .pkl diretamente)
