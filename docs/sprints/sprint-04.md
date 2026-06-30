# Sprint 4 — Model Registry + Versionamento de Artefatos

**Status:** Concluída ✅  
**Data:** 2026-06-30

---

## Objetivo

Registrar o melhor modelo no MLflow Model Registry, versioná-lo com aliases e promovê-lo para produção de forma rastreável e reversível.

---

## O que foi construído

### Arquivos criados / modificados

| Arquivo | Mudança |
|---------|---------|
| `pipelines/register_model.py` | Novo — registra, promove e valida o modelo no registry |
| `pipelines/train.py` | Atualizado — adicionado `signature` e `input_example` ao `log_model` |

---

## Fluxo implementado

```
Experimento MLflow (Sprint 3)
  └── Runs ordenados por PR-AUC
        └── Melhor run (random_forest, pr_auc=0.8664)
              └── mlflow.register_model → fraud-detector versão 1
                    └── alias 'challenger' → validação técnica
                          └── alias 'champion' → modelo oficial
                                └── mlflow.sklearn.load_model("models:/fraud-detector@champion")
```

---

## Modelo registrado

| Campo | Valor |
|-------|-------|
| Nome | `fraud-detector` |
| Versão | 1 |
| Algoritmo | RandomForestClassifier |
| Run de origem | `ac623ce7361542daa525f8bbaefd381d` |
| PR-AUC | 0.8664 |
| Aliases | `challenger`, `champion` |
| Tag | `promoted_by: register_model.py` |

---

## Decisões técnicas

| Decisão | Motivo |
|---------|--------|
| Aliases em vez de stages | Stages deprecated desde MLflow 2.9 — aliases são a API moderna e compatível com MLflow 3.x |
| `challenger` antes de `champion` | Permite gate de aprovação: novo modelo fica como challenger até ser validado |
| `infer_signature` no train.py | Define schema de entrada/saída — resolve warning da Sprint 3 e habilita validação automática na Sprint 5 |
| `input_example = X_test.head(5)` | Exemplo real de transação — o MLflow documenta o formato esperado junto com o modelo |
| `promoted_by` tag | Rastreabilidade: saber qual script/pipeline promoveu o modelo |

---

## Padrão champion/challenger

| Alias | Papel |
|-------|-------|
| `champion` | Modelo oficial em produção — recebe 100% do tráfego |
| `challenger` | Modelo candidato — pode rodar em shadow mode para comparação |

Shadow mode: o challenger processa os mesmos dados que o champion, mas sem afetar o usuário. Após validação real, o alias `champion` é movido para o challenger sem redeployar código.

---

## Validação — Perguntas e Respostas

**P: Apenas PR-AUC é suficiente para decidir qual modelo vai para produção?**  
R: Não. Em produção, também se avalia recall, precision, custo operacional, estabilidade, tempo de inferência, drift dos dados e critérios de negócio. A métrica elege candidatos; a promoção exige validação técnica e humana.

**P: Por que `load_model("models:/fraud-detector@champion")` é melhor que `joblib.load("model.pkl")`?**  
R: O alias carrega o modelo oficial versionado com rastreabilidade completa (run, métricas, schema). O arquivo `.pkl` solto não tem garantia de versão, origem ou se é o modelo de produção correto.

**P: O que acontece com a versão 1 quando a versão 2 vira champion?**  
R: A versão 1 permanece no registry, imutável, com todos os artefatos preservados. O alias `champion` é movido para a versão 2. Rollback = mover o alias de volta. Sem redeployar código.

---

## Code Review — Nota: 8.0 / 10

**Pontos positivos:** separação de funções, aliases modernos, tags/descrição para governança, validação ao carregar do registry.

**Pontos de melhoria:**
- Sem polling de status após `register_model` (registro é assíncrono)
- Validação com `head(5)` quase nunca inclui uma fraude real
- `search_runs` não filtra por `status = 'FINISHED'` — pode pegar runs parciais

---

## Perguntas de Entrevista — Nota: 9.5 / 10

1. **Aprovação do Head de Produto** — registro como challenger + gate de aprovação humana + promoção do alias. Padrão correto de governance.
2. **Por que manter versões antigas** — rollback + reprodutibilidade de decisões passadas (requisito de compliance legal em sistemas financeiros).
3. **Champion/challenger em produção** — shadow mode: challenger processa em paralelo sem afetar usuário. Comparação em dados reais antes de promover.

---

## Próximo passo

**Sprint 5** — FastAPI serving  
- Criar endpoint `/predict` que carrega o modelo com `models:/fraud-detector@champion`
- Validar o schema de entrada usando a assinatura definida na Sprint 4
- Containerizar a API com Docker
- Testar com `curl` e `httpx`
