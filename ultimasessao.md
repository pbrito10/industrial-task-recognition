# Estado do Projeto — 27 Abril 2026 — atualização mais recente

## Resumo rápido para retomar

- Diretório atual do projeto: `/home/pedrobrito/industrial-task-recognition`
- A suite completa está a passar:
```bash
.venv/bin/pytest
```
```text
256 passed
```
- O sistema já cria uma pasta por sessão em `output/sessions/<data_hora>/`.
- O vídeo anotado, CSV, Excel, snapshot de config/ROIs e frames de gap ficam dentro dessa pasta.
- O Excel deixou de declarar uma “verdade final” sobre anomalias: agora mostra o **resultado automático do sistema** e deixa espaço para validação manual.

## O que foi feito nesta última fase

### Organização dos outputs por sessão

Antes, `output/` ficava com CSVs, Excels e imagens soltos. Agora cada execução cria uma pasta própria:

```text
output/
  sessions/
    2026-04-27_17h02m24s/
      debug_2026-04-27_17h02.csv
      debug_2026-04-27_17h02_config.json
      sessao_2026-04-27_17h02.xlsx
      video/
        sessao_2026-04-27_17h02_annotated.mp4
      frames/
        gaps/
          gap_ciclo_002.jpg
```

Alterações principais:
- criado `src/output/session_output.py`;
- criado `src/output/video_recorder.py`;
- `DebugLogger`, `ExcelExporter`, snapshot de config e frames de gap escrevem dentro da pasta da sessão;
- `main.py` continua a encontrar CSVs antigos soltos em `output/`, para compatibilidade;
- `config/settings.yaml` ganhou:
  - `output.sessions_subdir`;
  - `output.record_video`;
  - `output.video_fps`.

### Gravação de vídeo dos testes

- O vídeo é gravado no `monitor_process.py`, depois de o frame receber as anotações.
- O vídeo inclui:
  - esqueleto/keypoints da mão;
  - ROIs desenhadas;
  - cores funcionais das zonas.
- A gravação é controlada por `output.record_video`.
- O FPS nominal do ficheiro é controlado por `output.video_fps`.

### Ensaios gravados 5 / 15 / 30 min

Foi adicionada a opção:

```text
4 — Correr ensaio gravado
```

Com durações:

```text
5 minutos
15 minutos
30 minutos
```

Ficou decidido deixar esta opção por agora, embora exista a hipótese de simplificar mais tarde e gravar sempre pela opção normal.

### Snapshot histórico da sessão

Para evitar analisar CSVs antigos com a config atual errada:

- cada sessão guarda `debug_*_config.json`;
- o snapshot contém config e ROIs usadas nessa sessão;
- `analysis/session_analysis.py` usa o `cycle_zone_order` histórico quando o snapshot existe;
- se não existir snapshot, avisa e usa a config atual.

Ficheiro novo:

```text
src/output/session_config_snapshot.py
```

### Cores das ROIs

Foi removida a lógica antiga por hash/nome, que fazia as zonas parecerem coloridas ao acaso.

Nova regra:

| Zona | Cor |
|---|---|
| zonas normais | preto |
| zona de início do ciclo | verde |
| zona de saída/output | azul |
| zona de assembly/montagem | laranja |

A zona de início vem de `tracking.cycle_zone_order[0]`.
A saída vem de `tracking.exit_zone`.
A montagem/assembly vem de `tracking.two_hands_zones`.

### Excel — folha Ciclos

Foi removida a lógica de “provavelmente completo” baseada em duração histórica.

Motivo: o tempo não prova que o ciclo foi correto. Um ciclo pode ter duração normal e mesmo assim ter saltado uma zona.

Agora a folha `Ciclos` mostra:

```text
Nº Ciclo
Início
Fim
Duração (s)
Resultado do sistema
Sequência registada
Problema detetado
Classificação manual
Observações
```

`Resultado do sistema` pode ser:

```text
Em ordem
Sequência incompleta
Fora de ordem
```

Exemplos de `Problema detetado`:

```text
Faltaram zonas esperadas: "Montagem".
```

```text
Esperava "Chassi", mas apareceu "Porca".
```

Isto deixa claro que o sistema faz uma comparação automática da sequência, e que a validação final é manual.

### Diagnóstico de sequência

Foi criada lógica nova em:

```text
src/tracking/order_matching.py
```

Além de `matches_order()`, existe agora `diagnose_order()`, que devolve:

- resultado automático;
- problema detetado.

O `CycleTracker` deixou de tentar decidir anomalia por duração histórica.

### Dashboard

O dashboard deixou de mostrar “Anomalias” como se fosse verdade final.

Agora mostra:

```text
Ciclos em ordem
Ciclos a rever
```

### Documentação

Atualizados:

- `MAP.md`;
- `docs/metodologia_validacao.md`.

A metodologia passou a separar:

- resultado automático do sistema;
- classificação manual;
- falsos positivos/falsos negativos calculados depois da validação manual.

---

## MUITO IMPORTANTE — Tempo de transição atual não chega

**Lembrete forte para implementar a seguir: o tempo de transição que existe agora é global.**

Neste momento, o sistema calcula tempo de transição como uma massa geral:

```text
tempo total da sessão - tempo produtivo - tempo de interrupção
```

Isto quase não dá informação operacional. Saber que houve, por exemplo, 20% de transição na sessão não diz **onde** se está a perder tempo.

O que vai dar informação útil é medir **transições individuais entre zonas**, por percurso físico:

```text
Porca → Montagem
Montagem → Chassi Inferior
Chassi Inferior → Montagem
Montagem → Rodas
Rodas → Montagem
...
```

Motivo:

**As caixas das peças que estão nas pontas da bancada provavelmente geram deslocações diferentes das caixas que estão no meio.**

Se medirmos por percurso, conseguimos perceber:

- que deslocações são mais longas;
- que peças estão mal posicionadas;
- se as caixas nas pontas geram mais tempo morto;
- se a montagem central está bem localizada;
- onde reorganizar a bancada para reduzir deslocação.

### Como implementar depois

Criar eventos/métricas de transição entre tarefas:

```text
origem: zona anterior concluída
destino: zona seguinte concluída
início: fim da tarefa anterior
fim: início da tarefa seguinte
duração: fim - início
ciclo: número do ciclo
```

Exportar no Excel uma folha nova, por exemplo:

```text
Transições
```

Com colunas:

```text
Ciclo
Origem
Destino
Início
Fim
Duração (s)
```

E talvez uma folha agregada:

```text
Transições por percurso
```

Com:

```text
Origem
Destino
Ocorrências
Mínimo (s)
Médio (s)
Máximo (s)
Desvio padrão (s)
```

Isto é mais útil do que o tempo de transição global para defender conclusões sobre layout da bancada.

---

## O que falta fazer

### Validação prática com câmara real

- Correr uma sessão curta real.
- Confirmar que a pasta de sessão é criada corretamente.
- Confirmar que o CSV, Excel, snapshot, vídeo e frames de gap ficam no sítio certo.
- Confirmar que o vídeo MP4 abre e mostra mão + ROIs.
- Confirmar se `output.video_fps` está adequado ou se o vídeo fica acelerado/lento.
- Confirmar se as cores das ROIs estão visualmente claras:
  - preto = normal;
  - verde = início;
  - azul = saída;
  - laranja = montagem.

### Excel e validação manual

- Gerar um Excel novo depois destas alterações.
- Verificar a folha `Ciclos`.
- Confirmar se `Resultado do sistema`, `Sequência registada` e `Problema detetado` são fáceis de defender perante o professor.
- Preencher manualmente `Classificação manual` e `Observações` em alguns ciclos piloto.

### Tempo de transição individual

- Implementar métricas por deslocação entre zonas.
- Adicionar folha `Transições`.
- Adicionar folha agregada `Transições por percurso`.
- Rever se o dashboard deve mostrar os percursos mais lentos.

### Decisões pendentes

- Decidir se a opção `4 — Correr ensaio gravado` fica ou se o sistema deve apenas gravar sempre na opção `3`.
- Decidir se `output.video_fps: 10.0` é suficiente para validação visual.
- Confirmar se as coordenadas atuais de `config/rois.json` são definitivas.
- Eventualmente renomear `debug_*_anomalias.xlsx`, porque agora a análise é mais de validação/revisão do que “anomalias” automáticas.

---

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
- `CycleTracker` com validação automática por sequência esperada
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
