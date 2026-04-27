# Estado do Projeto — 27 Abril 2026

## Ponto de Continuidade — mudança para PC do CITIN

### Estado confirmado antes da troca
- Diretório de trabalho usado nesta sessão: `/home/pedrobrito/Projeto2`
- Branch atual: `develop`
- Ambiente Python correto: `.venv/bin/python`
- Suite completa validada na venv: `235 passed in 1.16s`
- Último commit observado antes desta nota: `336b834 fix e estruturação`

### O que ficou decidido
- A validação do programa será feita contra **ground truth manual externo**, não contra a lógica interna do programa.
- A avaliação será dividida em duas fases:
  1. **Percentagem de acerto global**: comparar ciclo real (`Correto` / `Anomalia`) com resultado do programa (`Correto` / `Anomalia`).
  2. **Diagnóstico dos erros**: analisar falsos positivos e falsos negativos para perceber se vieram de perda de mão, ROI/câmara, timeout indevido ou lógica de ciclo.
- Se o operador fez o ciclo corretamente mas o programa perdeu a mão e marcou anomalia, isso conta como **erro do programa** na Fase 1.
- A causa desse erro só é explicada depois, na Fase 2.
- Não foi criada categoria formal `Indeterminada`, para manter a metodologia simples.

### Documento novo de metodologia
- Criado `docs/metodologia_validacao.md`
- Inclui:
  - objetivo da validação;
  - matriz de confusão;
  - fórmula de percentagem de acerto;
  - plano de aplicação;
  - tabela manual sugerida;
  - diagnóstico das causas dos erros;
  - texto pronto para adaptar ao relatório.

### Revisão Clean Code / SOLID / OCP concluída
Foram corrigidos os pontos levantados, exceto o ponto sobre a Ferramenta 4 usar a config atual para analisar CSVs antigos, que ficou **propositadamente em aberto** para debate posterior.

Alterações principais:
- Regra de ordem extraída para `src/tracking/order_matching.py`
- `CycleTracker` e `analysis/session_analysis.py` usam a mesma função `matches_order`
- `MetricsSnapshot` passou a ser snapshot real por valor, com `TaskMetricSnapshot` e `CycleMetricSnapshot`
- `CycleResult` passou a guardar `start_time` e `end_time`
- `ExcelExporter` deixou de reconstruir ciclos a partir de eventos em aberto
- Validação inicial do `settings.yaml` adicionada em `src/shared/app_config.py`
- `Camera` separou carga de calibração de lente e perspetiva em métodos privados
- Cores das ROIs deixaram de depender de nomes hardcoded como `"Montagem"` e `"Saida"`
- `MediapipeDetector` deixou de importar MediaPipe no topo do módulo; import passou a ser lazy para não bloquear testes unitários
- Ferramenta 4 corrigida: removido bloco markdown acidental no fim de `analysis/session_analysis.py`

### Testes
- Comando usado:
```bash
.venv/bin/python -m pytest -q
```
- Resultado:
```text
235 passed in 1.16s
```

### Para retomar no PC do CITIN
1. Abrir o projeto via VS Code SSH.
2. Confirmar branch:
```bash
git branch --show-current
```
3. Confirmar venv:
```bash
.venv/bin/python -m pytest -q
```
4. Ler:
   - `ultimasessao.md`
   - `docs/metodologia_validacao.md`
5. Próxima conversa recomendada:
   - discutir o ponto em aberto: como lidar com análise de CSVs antigos quando o `cycle_zone_order` atual muda.

---

# Estado do Projeto — 22 Abril 2026

## O que foi feito nesta sessão

### Dashboard simplificado
- Removidas as secções de métricas por zona e gráficos — o dashboard é agora um monitor operacional enxuto
- Classificação de ciclos reduzida a binário: **Ciclos corretos** vs **Anomalias** (orientador)
- Tempo médio de ciclo passa a contar apenas ciclos corretos (`sequence_in_order=True`)

### Ferramenta 4 — Análise de Sessão (`analysis/session_analysis.py`)
- Tabela com uma linha por ciclo e uma coluna por ocorrência de zona do `cycle_zone_order`
- Células: duração em segundos / `TIMEOUT→OK Xs` / `TIMEOUT` / `—`
- Colunas extra: `Ordem correta`, `Estado`, `Duração total`
- Zonas repetidas (ex: Montagem × 5) geram colunas `Montagem_1` … `Montagem_5`
- Opção **4 — Analisar sessão** adicionada ao menu principal

### Detection Gap Logging
- Novo evento `DETECTION_GAP` no CSV: regista períodos sem deteção de mãos ≥ threshold
- Threshold configurável em `settings.yaml` (`detection_gap_threshold_s: 1.0`)
- Permite distinguir falha de deteção de abandono/interrupção real pela duração do gap
- Guarda o primeiro frame do gap como JPEG nomeado pelo ciclo: `gap_ciclo_002.jpg`
- Útil para verificação visual e para a ferramenta 4 cruzar com colunas "—"

### Revisão Clean Code / SOLID / OCP
- **Bug corrigido**: `_gap_tracker` era inicializado antes de `_cycle_tracker` → `AttributeError` em runtime
- **`EventType` enum completo**: substituídas todas as magic strings de eventos do CSV (`ZONE_ENTER`, `ZONE_EXIT`, `TASK_COMPLETE`, `TASK_TIMEOUT`, `CYCLE_COMPLETE`, `DETECTION_GAP`)
- **`sequence_in_order: bool`**: removido `None` — o `CycleTracker` passa agora `False` em vez de `None` para ciclos não corretos; semântica mais clara
- **`_empty_row()`** no `DebugLogger`: eliminada duplicação dos dicts de 14 colunas
- **Guard clause** em `cycle_tracker.py:record()`: removido `else` desnecessário
- **Constantes `_CELL_*`** em `session_analysis.py`: sem magic strings nas células da tabela
- **`_save_table()`** extraída: lógica de output não duplicada entre `main.py` e `session_analysis.py`
- **`_FORCED_LABEL`** em `excel_exporter.py`: renomeado e simplificado para `dict[bool, str]`
- Todos os testes atualizados: 227 a passar

## Estado atual da codebase

### Pipeline completo e funcional
```
Câmara → MediaPipe → ZoneClassifier → TaskStateMachine → CycleTracker → Métricas → Outputs
```
- `OneHandStateMachine` e `TwoHandsStateMachine` com `ActivationStrategy` injetável
- `CycleTracker` com deteção de anomalias por comparação de duração histórica
- `_DetectionGapTracker` integrado no pipeline

### Outputs por sessão
| Ficheiro | Conteúdo |
|---|---|
| `debug_*.csv` | Todos os eventos em tempo real (flush imediato) |
| `gap_ciclo_NNN.jpg` | Frame do momento de cada gap de deteção |
| `metrics.json` | Snapshot para o dashboard Streamlit |
| `sessao_*.xlsx` | Excel com 4 folhas no fim da sessão |
| `debug_*_anomalias.xlsx` | Tabela da Ferramenta 4 (gerada a pedido) |

### Ficheiros principais
```
main.py                          Menu + orquestração de processos
monitor_process.py               Pipeline de monitorização
dashboard/app.py                 Dashboard Streamlit
analysis/session_analysis.py     Ferramenta 4 — análise de anomalias
src/
  shared/        Value objects + EventType enum
  detection/     MediaPipe, Keypoints, BoundingBox
  tracking/      StateMachines, CycleTracker, ZoneClassifier
  metrics/       TaskMetrics, CycleMetrics, MetricsCalculator
  output/        DashboardWriter, ExcelExporter
  events/        DebugLogger
  roi/           RoiCollection, RoiDrawer, JsonRoiRepository
  video/         Camera, FrameAnnotator
```

## Limitações conhecidas e documentadas
1. Não distingue falha de deteção de zona saltada (mitigado pelo gap JPEG)
2. Matching de zonas repetidas na Ferramenta 4 é greedy — pode desalinhar em casos extremos
3. Último ciclo de cada sessão aparece sempre como anomalia (ciclo em aberto)
4. Gaps abaixo do threshold (< 1s) são silenciosos
