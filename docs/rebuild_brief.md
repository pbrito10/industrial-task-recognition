# Brief de Reconstrucao do Projeto

Este documento resume o que e necessario saber para reescrever o sistema de raiz
mantendo o comportamento pretendido do repositório.

## Estado Atual do Repo

- Branch atual: `tdd-rewrite`.
- Esta branch e um esqueleto TDD: muitos metodos em `src/` levantam
  `NotImplementedError`.
- A implementacao funcional anterior esta em `develop`/`master`; usei essa branch
  como referencia de comportamento, sem alterar a branch atual.
- Os testes atuais existem, mas muitos ainda sao scaffolding com `pass`.
- `pytest` nao esta instalado no ambiente local `.venv`; `.venv/bin/python -m pytest`
  falha com `No module named pytest`.
- `MAP.md` e util, mas esta parcialmente desatualizado: referencia ficheiros como
  `event_logger.py` e `zone_event.py` que nao existem na branch atual.
- `AVALIACAO.md` tambem esta desatualizado quando diz que ha zero testes.

## Objetivo do Sistema

Sistema de visao computacional para uma bancada de montagem industrial.

O sistema deve:

1. Ler video de uma camera USB.
2. Corrigir lente/perspetiva quando houver calibracao.
3. Detetar ate duas maos por frame com MediaPipe.
4. Classificar cada mao numa ROI da bancada ou como fora de zona.
5. Confirmar tarefas apenas depois de dwell time com mao parada.
6. Medir tarefas, ciclos, ordem de execucao, gargalos e tempos improdutivos.
7. Mostrar o video anotado em tempo real.
8. Alimentar um dashboard Streamlit via JSON.
9. Exportar um Excel no fim da sessao.
10. Gerar CSV de debug com eventos frame a frame.

## Modos de Uso

Entrada principal:

```bash
python main.py
```

Menu:

- `1 - Testar camara`: pipeline `capture -> detector -> display`; mostra maos,
  esqueleto e FPS; nao grava metricas.
- `2 - Definir ROIs`: abre a camera e permite desenhar zonas com o rato; guarda em
  `config/rois.json`.
- `3 - Correr programa`: pipeline completo `capture -> detector -> monitor`, abre o
  dashboard Streamlit e exporta dados no fim.
- `0 - Sair`.

Scripts auxiliares:

- `calibration/calibrate_lens.py`: calibracao intrinseca com checkerboard; gera
  `calibration/data/lens_calibration.npz`.
- `calibration/calibrate_perspective.py`: escolhe quatro pontos de referencia;
  gera `calibration/data/perspective_calibration.npz`.
- `dashboard/app.py`: app Streamlit que le `dashboard/data/metrics.json`.

## Dependencias e Ambiente

Dependencias em `requirements.txt`:

- `mediapipe`
- `opencv-python` e `opencv-contrib-python`
- `numpy`
- `PyYAML`
- `pandas`
- `openpyxl`
- `streamlit`
- dependencias transitivas ja listadas no ficheiro.

Notas:

- O modelo MediaPipe esperado esta em `model/hand_landmarker.task`.
- Existe tambem `models/hand_landmarker.task`, mas `models/` esta no `.gitignore`;
  o caminho usado pela config e `model/hand_landmarker.task`.
- O codigo assume ambiente grafico OpenCV/X11 e forca `DISPLAY=:0` quando necessario,
  especialmente em SSH.
- O multiprocessing usa `spawn`, nao `fork`, para evitar problemas com OpenCV, X11 e
  estado herdado.

## Configuracao

Fonte principal: `config/settings.yaml`.

Campos importantes:

- `camera.index`: indice da camera USB.
- `camera.width`, `camera.height`: resolucao pedida.
- `camera.flip`: se `true`, aplica `cv2.flip(frame, -1)`, ou seja, 180 graus.
- `camera.calibration_path`: `.npz` com `K`, `dist` e opcionalmente `newcameramtx`.
- `camera.perspective_path`: `.npz` com `M` e `output_size`.
- `detection.model_path`: caminho do `.task` do MediaPipe.
- `detection.max_num_hands`: normalmente `2`.
- `detection.min_detection_confidence`: threshold de detecao.
- `detection.min_tracking_confidence`: threshold de tracking.
- `tracking.dwell_time_seconds`: tempo parado necessario para confirmar tarefa.
- `tracking.task_timeout_seconds`: tempo maximo antes de fechar tarefa por timeout.
- `tracking.stillness_threshold_px`: velocidade maxima do pulso em px/frame para
  considerar a mao parada.
- `tracking.zones`: nomes das zonas fisicas da bancada.
- `tracking.two_hands_zones`: zonas que requerem duas maos em simultaneo.
- `tracking.cycle_zone_order`: sequencia esperada de zonas num ciclo.
- `tracking.exit_zone`: zona que fecha o ciclo.
- `dashboard.data_path`: JSON gerado para o dashboard.
- `dashboard.refresh_seconds`: intervalo de refresh do dashboard.
- `output.excel_output_dir`: pasta de CSV debug e Excel.

Formato de `config/rois.json`:

```json
[
  {"name": "Porca", "x1": 15, "y1": 14, "x2": 122, "y2": 133}
]
```

As ROIs atuais sao:

- `Porca`
- `Chassi Inferior`
- `Rodas`
- `Chassi Superior`
- `Parafuso`
- `Montagem`
- `Saida`

## Pipeline de Dados

Fluxo principal:

```text
Camera BGR
  -> capture_process
       aplica camera.read_frame()
       converte BGR -> RGB
       publica em frame_queue
  -> detection_process
       MediaPipe HandLandmarker
       publica (frame_rgb, list[HandDetection]) em detection_queue
  -> display_process ou monitor_process
```

No modo completo:

```text
detection_queue
  -> ZoneClassifier
  -> TaskStateMachine
  -> CycleTracker
  -> MetricsCalculator
  -> DebugLogger CSV
  -> DashboardWriter JSON
  -> ExcelExporter XLSX
  -> janela OpenCV anotada
```

Regras de filas:

- `frame_queue` tem `maxsize=2`.
- `detection_queue` tem `maxsize=5`.
- Se `frame_queue` esta cheia, descarta o frame mais antigo para reduzir latencia.
- Se `detection_queue` esta cheia, descarta a deteccao atual em vez de bloquear.
- A deteccao e sempre enviada junto com o frame exato correspondente.

## Modelo de Dominio

### `Point`

`Point(x: int, y: int)` representa coordenadas em pixels.

Contrato:

- Imutavel (`dataclass(frozen=True)`).
- `distance_to(other)` devolve distancia euclidiana.

### `Confidence`

`Confidence(value: float)` representa confianca entre `0.0` e `1.0`.

Contrato:

- Valida no construtor: valores fora de `[0.0, 1.0]` levantam `ValueError`.
- `is_above(threshold)` usa `>=`.
- `as_percentage()` devolve `value * 100.0`.

### `HandSide`

Enum:

- `HandSide.LEFT = "left"`
- `HandSide.RIGHT = "right"`

### `Keypoint`

`Keypoint(index, position, confidence)`.

MediaPipe usa 21 landmarks:

- `0`: pulso.
- `1-4`: polegar.
- `5-8`: indicador.
- `9-12`: medio.
- `13-16`: anelar.
- `17-20`: mindinho.

### `KeypointCollection`

Colecao imutavel com exatamente 21 keypoints.

Contrato:

- Construtor valida `len(keypoints) == 21`.
- `wrist()` devolve indice `0`.
- `centroid()` devolve media inteira de todos os pontos.
- `finger_mcp_centroid()` usa indices `[5, 9, 13, 17]`.
- `fingertips()` usa indices `[4, 8, 12, 16, 20]`.
- `by_index(i)` aceita apenas `0 <= i < 21`; caso contrario `ValueError`.
- `all()` devolve copia da lista.

O `finger_mcp_centroid()` e o ponto de referencia para zonas: e mais estavel que
pontas dos dedos e mais representativo que o pulso.

### `BoundingBox`

`BoundingBox(top_left, bottom_right)`.

Contrato:

- `center()` devolve media inteira dos cantos.
- `area()` devolve largura vezes altura.
- `contains(point)` e inclusivo nas bordas.

### `HandDetection`

Agrupa:

- `keypoints: KeypointCollection`
- `bounding_box: BoundingBox`
- `confidence: Confidence`
- `hand_side: HandSide`

Atalhos:

- `centroid()` delega em `keypoints.centroid()`.
- `wrist()` delega em `keypoints.wrist()`.
- `finger_mcp_centroid()` deve delegar em `keypoints.finger_mcp_centroid()`.

### `RegionOfInterest`

`RegionOfInterest(name, top_left, bottom_right)`.

Contrato:

- Retangulo inclusivo.
- `contains(point)` usa `x1 <= x <= x2` e `y1 <= y <= y2`.
- `to_dict()` serializa `name`, `x1`, `y1`, `x2`, `y2`.
- `from_dict()` reconstroi a ROI.

### `RoiCollection`

Colecao mutavel de ROIs.

Contrato:

- Guarda um dicionario `name -> ROI`.
- `add(roi)` adiciona ou substitui pelo nome.
- `remove(name)` nao falha se nao existir.
- `find_zone_for_point(point)` devolve a primeira ROI que contem o ponto, por ordem
  de insercao.
- `get(name)`, `contains(name)`, `is_empty()`, `all()`.

### `JsonRoiRepository`

Persistencia JSON.

Contrato:

- `load()` devolve `RoiCollection()` vazia se o ficheiro nao existir.
- `save(collection)` escreve JSON com indentacao e `ensure_ascii=False`.
- Deve criar diretorias pai se forem necessarias.

## Camera e Calibracao

`src/video/camera.py` encapsula `cv2.VideoCapture`.

Construcao:

1. Abre `cv2.VideoCapture(index)`.
2. Define `CAP_PROP_FRAME_WIDTH` e `CAP_PROP_FRAME_HEIGHT`.
3. Se existir `calibration_path`, carrega `K`, `dist` e `newcameramtx` ou usa `K`
   como fallback.
4. Pre-calcula mapas com `cv2.initUndistortRectifyMap`.
5. Se existir `perspective_path`, carrega `M` e `output_size`.

`read_frame()`:

1. Le frame BGR.
2. Se falhar, devolve `None`.
3. Aplica undistortion com `cv2.remap`.
4. Aplica `flip` se configurado.
5. Aplica `cv2.warpPerspective`.
6. Devolve frame BGR.

Ordem importante: lente -> flip -> perspetiva.

## Detector MediaPipe

`MediapipeDetector` implementa `DetectorInterface`.

Requisitos:

- Usar MediaPipe Tasks API `HandLandmarker`.
- `running_mode=VIDEO`.
- Timestamp deve ser monotonicamente crescente: `int(time.monotonic() * 1000)`.
- Entrada: frame RGB.
- Saida: `list[HandDetection]`.

Construcao:

- `BaseOptions(model_asset_path=model_path)`.
- `HandLandmarkerOptions` com:
  - `num_hands=max_num_hands`
  - `min_hand_detection_confidence=min_detection_confidence`
  - `min_hand_presence_confidence=min_detection_confidence`
  - `min_tracking_confidence=min_tracking_confidence`

Conversoes:

- Landmarks normalizados para pixel: `Point(int(x * width), int(y * height))`.
- A confianca global da mao e usada em todos os keypoints.
- Confianca da mao e `round(category.score, 4)`.
- `"Left"` mapeia para `HandSide.LEFT`; `"Right"` para `HandSide.RIGHT`.
- Bounding box e calculada pelos min/max dos 21 keypoints, com margem de `10px`,
  clampada ao frame.
- `release()` fecha o landmarker.

## Desenho de ROIs

`RoiDrawer` e interativo com OpenCV.

Controlos:

- `1-9`: selecionar zona pelo indice em `tracking.zones`.
- Rato: drag para desenhar retangulo.
- `Del`: apagar zona selecionada.
- `s`: guardar.
- `q`: sair sem guardar.

Regras:

- ROI minima: `15px` de largura e altura.
- Ao guardar, todas as zonas de `tracking.zones` devem estar desenhadas.
- Drag normaliza top-left/bottom-right com `min`/`max`.

## Classificacao de Zonas

`ZoneClassifier` e stateless.

Contrato:

- Recebe `list[HandDetection]`.
- Para cada deteccao calcula `detection.keypoints.finger_mcp_centroid()`.
- Procura a primeira ROI que contem esse ponto.
- Devolve `list[tuple[HandDetection, RegionOfInterest | None]]`.
- `None` significa mao em transito ou fora das ROIs.

## Estrategias de Ativacao

`ActivationStrategy` decide se o dwell timer avanca.

### `TimeDwellStrategy`

- `is_active(...)` devolve sempre `True`.
- Util para debug.

### `StillnessDwellStrategy`

- Recebe `velocity_threshold_px_per_frame`.
- Se `previous is None`, devolve `False`.
- Calcula distancia entre pulso atual e pulso anterior.
- Devolve `True` se distancia `< threshold`.
- Usa pulso (`wrist`) apenas para velocidade, nao para classificar zona.

## Maquina de Estados

Ha uma regra global: apenas uma tarefa ativa de cada vez.

### Estados

Enum `TaskState`:

- `IDLE`
- `DWELLING`
- `WAITING_SECOND_HAND`
- `DWELLING_TWO_HANDS`
- `TASK_IN_PROGRESS`

### `TaskEvent`

Campos:

- `zone_name`
- `start_time`
- `end_time`
- `duration`
- `cycle_number`
- `was_forced`

`TaskEvent.create(...)` deve:

- Validar `end_time > start_time`; se nao, `ValueError`.
- Calcular `duration = end_time - start_time`.
- Guardar todos os campos.

`was_forced=True` significa timeout; conta como interrupcao, nao como produtividade.

### `OneHandStateMachine`

Fluxo:

```text
IDLE -> DWELLING -> TASK_IN_PROGRESS -> IDLE
```

Regras:

- Em `IDLE`, fixa a primeira zona nao nula encontrada.
- Em `DWELLING`:
  - se a mao sair da zona antes do dwell, reset para `IDLE` sem evento;
  - se `strategy.is_active(...)` for falso, limpa `dwell_start` mas guarda deteccao
    atual como anterior;
  - se for verdadeiro e `dwell_start` estiver vazio, inicia dwell;
  - se `frame_time - dwell_start >= dwell_time`, passa para `TASK_IN_PROGRESS` e
    define `task_start = frame_time`.
- Em `TASK_IN_PROGRESS`:
  - se `frame_time - task_start >= task_timeout`, emite evento forcado;
  - se a mao sair da zona, emite evento normal;
  - caso contrario continua.

### `TwoHandsStateMachine`

Fluxo:

```text
IDLE -> WAITING_SECOND_HAND -> DWELLING_TWO_HANDS -> TASK_IN_PROGRESS -> IDLE
```

Regras:

- Em `IDLE`, fixa a primeira zona nao nula.
- Em `WAITING_SECOND_HAND`:
  - se nao houver nenhuma mao na zona, reset;
  - inicia `waiting_start` na primeira frame;
  - se a segunda mao nao chegar dentro de `dwell_time`, reset;
  - quando ha duas ou mais maos, passa para `DWELLING_TWO_HANDS`.
- Em `DWELLING_TWO_HANDS`:
  - se houver menos de duas maos, reset;
  - ambas as maos devem estar ativas/paradas ao mesmo tempo;
  - `previous` e guardado por `HandSide`;
  - se qualquer mao se mexer, limpa `dwell_start`;
  - apos dwell completo, entra em `TASK_IN_PROGRESS`.
- Em `TASK_IN_PROGRESS`:
  - timeout fecha evento forcado;
  - se ficar menos de duas maos na zona, fecha evento normal.

### `TaskStateMachine`

Orquestrador.

Regras:

- Enquanto existe maquina ativa, so ela recebe updates.
- Quando a maquina ativa volta a `IDLE`, `_active` e limpo.
- Zonas em `two_hands_zones` so ativam a maquina de duas maos quando ha pelo menos
  duas maos nessa zona.
- Zonas two-hands sao filtradas antes de ativar one-hand para evitar que uma mao
  sozinha em `Montagem` seja aceite como tarefa normal.
- `current_state()` devolve o estado da maquina ativa ou `IDLE`.

## Ciclos

`CycleTracker` acumula `TaskEvent`s ate a `exit_zone`.

Regras:

- Ciclo comeca no primeiro evento acumulado.
- Evento forcado (`was_forced=True`) entra no acumulador, mas nao fecha ciclo.
- A `exit_zone` so fecha ciclo se `was_forced=False`.
- `current_cycle_number()` comeca em `1` e incrementa apos cada ciclo fechado.
- `CycleResult.duration` e `ultimo.end_time - primeiro.start_time`.
- `actual_sequence` exclui eventos forcados.
- `sequence_in_order` valida `actual_sequence` contra `expected_order`.

`_matches_order(actual, expected)`:

- Se `expected` estiver vazio, pode devolver `True`.
- Se `actual` estiver vazio e `expected` nao, devolve `False`.
- Permite repeticoes consecutivas da zona atual.
- Permite avancar para a proxima zona esperada.
- Nao permite saltar zonas nem voltar atras.

Exemplos:

- `["Porca", "Montagem", "Chassi", "Saida"]` e valido.
- `["Porca", "Porca", "Montagem", "Chassi", "Saida"]` e valido.
- `["Porca", "Chassi", "Saida"]` e invalido.
- `["Montagem", "Porca", "Chassi", "Saida"]` e invalido.

## Metricas

### `_DurationMetrics`

Base privada para estatisticas de duracoes.

Contrato:

- Guarda lista de `timedelta`.
- `count()`
- `minimum()`
- `maximum()`
- `average()`
- `std_deviation()`

Desvio padrao:

- Se ha menos de dois valores, devolve `timedelta(0)`.
- Usa desvio padrao populacional: divide por `count`, nao por `count - 1`.

### `TaskMetrics`

- Uma instancia por zona.
- `add(duration)` chama `_add_duration`.
- So deve receber tarefas normais, nao timeouts.

### `CycleMetrics`

- Guarda duracoes de ciclos completos.
- Conta ciclos em ordem e fora de ordem.
- `count_out_of_order() == count() - count_in_order()`.

### `MetricsCalculator`

Entrada:

- `TaskEvent`
- `CycleResult`

Regras:

- Evento normal:
  - soma a `productive_time`;
  - cria metricas da zona se for desconhecida;
  - adiciona duracao em `TaskMetrics`.
- Evento forcado:
  - soma a `interruption_time`;
  - nao entra nas metricas por zona.
- `record_cycle(cycle_result)` adiciona duracao e `sequence_in_order`.
- `transition_time = session_duration - productive_time - interruption_time`,
  clampado a zero.
- Percentagens:
  - se duracao da sessao for zero: todas `0.0`;
  - produtivo e interrupcao calculados diretamente;
  - transicao e complemento para garantir soma de 100%.
- Gargalo: zona com maior media de tarefa; `None` se nao ha dados.

`MetricsSnapshot` transporta:

- `task_metrics`
- `cycle_metrics`
- `productive_time`
- `transition_time`
- `interruption_time`
- percentagens
- `bottleneck_zone`
- `session_duration`
- `captured_at`

## Outputs

### Debug CSV

`DebugLogger` cria `output/debug_YYYY-MM-DD_HHhMM.csv`.

Colunas:

- `timestamp_iso`
- `relative_time_s`
- `event_type`
- `zone`
- `hand`
- `x_px`
- `y_px`
- `confidence`
- `frame_idx`
- `duration_s`
- `cycle_number`
- `sequence_in_order`

Eventos:

- `ZONE_ENTER`
- `ZONE_EXIT`
- `TASK_COMPLETE`
- `TASK_TIMEOUT`
- `CYCLE_COMPLETE`

Para `ZONE_ENTER`/`ZONE_EXIT`, a posicao registada e o `finger_mcp_centroid`.

### Dashboard JSON

`DashboardWriter` escreve atomicamente:

1. Serializa para dict.
2. Escreve em ficheiro temporario com sufixo `.tmp`.
3. Faz `replace()` para o caminho final.

Schema:

```json
{
  "captured_at": "2026-01-01T10:00:00.000000",
  "session_duration": 12.3,
  "task_metrics": {
    "Porca": {
      "count": 2,
      "min_s": 1.2,
      "avg_s": 1.5,
      "max_s": 1.8,
      "std_dev_s": 0.3
    }
  },
  "cycle_metrics": {
    "count": 0
  },
  "time_breakdown": {
    "productive_pct": 40.0,
    "transition_pct": 55.0,
    "interruption_pct": 5.0
  },
  "bottleneck_zone": "Montagem"
}
```

Zonas sem ocorrencias devem ser omitidas de `task_metrics`.

Se nao ha ciclos, `cycle_metrics` deve ser apenas `{"count": 0}`.

### Dashboard Streamlit

`dashboard/app.py`:

- Carrega `config/settings.yaml`.
- Le `dashboard.data_path`.
- Se nao houver JSON ou for invalido, mostra "A aguardar dados do pipeline...".
- Faz `st.rerun()` a cada `dashboard.refresh_seconds`.
- Mostra:
  - resumo da sessao;
  - decomposicao de tempo;
  - tabela por zona;
  - graficos de barras;
  - destaque visual do gargalo.

### Excel

`ExcelExporter` cria `output/sessao_YYYY-MM-DD_HHhMM.xlsx`.

Folhas:

- `Resumo`
- `Metricas por Zona`
- `Ciclos`
- `Eventos`

`Resumo`:

- Data
- Duracao total
- Ciclos completos
- Tempo medio ciclo
- Desvio padrao ciclo
- Percentagens produtivo/transicao/interrupcao
- Zona gargalo

`Metricas por Zona`:

- Zona
- Minimo
- Medio
- Maximo
- Desvio Padrao
- Ocorrencias
- Linha da zona gargalo destacada a amarelo.

`Ciclos`:

- Numero do ciclo
- Inicio
- Fim
- Duracao
- Sequencia correta

Atencao: na implementacao antiga, inicio/fim eram reconstruidos a partir dos
`TaskEvent`s porque `CycleResult` nao guarda timestamps absolutos.

`Eventos`:

- Ciclo
- Zona
- Inicio
- Fim
- Duracao
- Forcado

## Validacao no Arranque

Antes de correr o programa:

- Carregar ROIs.
- Se nao houver ROIs, pedir para usar opcao 2.
- Verificar que todas as zonas referenciadas por:
  - `tracking.exit_zone`
  - `tracking.two_hands_zones`
  - `tracking.cycle_zone_order`
  existem em `config/rois.json`.
- Imprimir todos os erros de uma vez e nao arrancar se houver inconsistencias.

## Criterios de Aceitacao para Reescrita

Um rewrite fiel deve passar estes criterios:

1. O menu principal funciona com os tres modos.
2. `Testar camara` mostra frame anotado com maos e FPS.
3. `Definir ROIs` permite criar, apagar e guardar todas as zonas configuradas.
4. O programa completo arranca camera, detector, monitor e dashboard.
5. Frames sao RGB no detector e BGR nas janelas OpenCV.
6. Deteccoes preservam sincronismo com o frame.
7. Classificacao de zona usa MCP centroid.
8. Uma mao em movimento nao completa dwell.
9. Uma mao parada durante dwell cria tarefa ao sair.
10. `Montagem` exige duas maos se estiver em `two_hands_zones`.
11. Timeout gera `was_forced=True`.
12. Tarefas forcadas contam como interrupcao, nao produtividade.
13. `Saida` fecha ciclo apenas quando nao forcada.
14. Sequencias fora de ordem sao marcadas como incorretas.
15. Dashboard JSON e sempre valido mesmo durante escrita.
16. Excel final tem as quatro folhas esperadas.
17. Debug CSV recebe eventos de zona, tarefa e ciclo.
18. Sem hardware, a logica pura deve ser testavel com deteccoes simuladas.

## Testes a Escrever/Completar

Prioridade alta:

- `Point.distance_to`.
- `Confidence` validacao, `is_above`, percentagem.
- `BoundingBox`.
- `KeypointCollection`.
- `RegionOfInterest` e `RoiCollection`.
- `JsonRoiRepository` roundtrip.
- `ZoneClassifier` com ROIs sobrepostas e fora de zona.
- `ActivationStrategy`.
- `TaskEvent.create`, incluindo `end_time <= start_time`.
- `OneHandStateMachine` transicoes principais.
- `TwoHandsStateMachine` transicoes principais.
- `TaskStateMachine` filtragem two-hands.
- `_matches_order`.
- `CycleTracker.record`.
- `_DurationMetrics`, `TaskMetrics`, `CycleMetrics`.
- `MetricsCalculator`.
- `DashboardWriter`.
- `ExcelExporter` com ficheiro temporario.

Comandos esperados depois de instalar dependencias de teste:

```bash
.venv/bin/python -m pytest -q
```

## Branches e Extensoes Opcionais

`develop`/`master`:

- Base funcional do sistema descrito acima.

`feature/wizard-bancada`:

- Adiciona perfis de bancada.
- Introduz `WorkbenchConfig`.
- Usa `config/workbenches/<nome>.json`.
- Usa `config/active_workbench.txt`.
- Cada bancada pode ter ROIs proprias.
- Adiciona conceito de `start_zone`.
- Evolui metricas para separar ciclo atual, ciclos corretos e fora de ordem.

`feature/projector-guide`:

- Adiciona processo de projecao/guiamento visual.
- Usa homografia para mapear ROIs da camera para o projetor.
- Renderiza frame 1920x1080 com fundo preto.
- Destaca zona atual a verde.
- Desenha seta para proxima zona.
- Se operador esta fora das zonas, destaca proxima zona a amarelo.

Estas branches nao fazem parte da branch atual, mas sao importantes se o rewrite
quiser preservar evolucoes ja exploradas.

## Riscos e Melhorias Recomendadas

- A branch atual nao e executavel enquanto os stubs nao forem implementados.
- `requirements.txt` nao inclui `pytest`.
- `pandas`, `openpyxl` e `streamlit` estao sem versao fixa.
- `opencv-python` e `opencv-contrib-python` aparecem juntos; convem escolher um.
- `CycleResult` devia guardar `start_time` e `end_time` para nao reconstruir ciclos
  no Excel.
- `MetricsSnapshot` e frozen, mas contem objetos mutaveis (`TaskMetrics`,
  `CycleMetrics`).
- Cores de zonas estao hardcoded por nome em `frame_annotator.py`.
- A config e dict cru; deveria haver validacao tipada no arranque.
- `DISPLAY=:0` esta repetido em varios pontos.
- `Camera.__init__` mistura abertura de camera, calibracao, perspetiva e config.
- O dashboard depende de polling e `st.rerun`; simples, mas pode piscar em maquinas
  lentas.
- Nao ha testes end-to-end simulando uma sessao completa sem camera.

## Ordem Recomendada para Reimplementar

1. Modelos puros: `Point`, `Confidence`, keypoints, ROI, eventos.
2. Metricas puras e testes.
3. `CycleTracker` e `_matches_order`.
4. `ActivationStrategy`.
5. Maquinas de estado com testes simulados.
6. `ZoneClassifier`.
7. Persistencia de ROIs.
8. Outputs JSON/Excel/CSV.
9. Camera e calibracao.
10. Detector MediaPipe.
11. Processos multiprocessing.
12. Dashboard.
13. Teste manual com camera real.

Esta ordem maximiza feedback rapido porque as primeiras oito partes nao precisam de
camera, MediaPipe nem ambiente grafico.
