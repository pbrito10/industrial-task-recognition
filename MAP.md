# Mapa do Projeto — Sistema de Reconhecimento Industrial

Sistema de visão computacional que deteta mãos numa bancada de montagem industrial,
reconhece em que zona de trabalho estão, e regista automaticamente o tempo de cada
tarefa, a ordem de execução e as métricas de produtividade — em tempo real e em Excel.

---

## Como usar

```
python main.py
```

| Opção | Para que serve |
|-------|---------------|
| 1 — Testar câmara | Abre a câmara e mostra o esqueleto das mãos. Usa para verificar se está tudo a funcionar antes de trabalhar. |
| 2 — Definir ROIs | Desenha as zonas de trabalho com o rato sobre o feed da câmara. **Faz isto primeiro** — sem ROIs o programa não corre. |
| 3 — Correr programa | Pipeline completo: deteta mãos, regista tarefas, abre o dashboard Streamlit e exporta Excel no fim. |

---

## Conceitos-chave

Antes de ver os ficheiros, convém perceber o vocabulário do sistema:

**ROI (Region of Interest)**
Retângulo desenhado sobre a câmara que representa uma zona física da bancada
(ex: "Porca", "Montagem"). O sistema deteta quando uma mão entra ou sai de cada ROI.

**Dwell time**
Tempo mínimo que a mão tem de estar parada dentro de uma ROI para o sistema confirmar
que está a trabalhar ali (e não só a passar). Configurável em `settings.yaml`.

**Tarefa (TaskEvent)**
Período desde que a mão confirmou entrada numa ROI (após dwell) até sair dela.
Cada tarefa tem zona, duração, número de ciclo e se foi fechada por timeout.

**Ciclo (CycleResult)**
Sequência completa de tarefas desde a primeira zona até à zona de saída ("Saida").
O sistema verifica se as zonas foram visitadas na ordem esperada.

**Gargalo**
A zona com maior tempo médio de tarefa — a que mais atrasa o ciclo.

**was_forced**
Se `True`, a tarefa foi encerrada pelo timeout (30 s) e não pela saída da mão.
Estas tarefas contam como "interrupções" e não entram nas métricas de produtividade.

---

## Fluxo de dados

```
Câmara (BGR)
  └─ capture_process      — converte para RGB, descarta frames antigos
       └─ frame_queue
            └─ detection_process   — MediaPipe deteta mãos → lista de HandDetection
                 └─ detection_queue
                      ├─ display_process      [Testar Câmara]
                      │    └─ janela OpenCV com esqueleto + FPS
                      │
                      └─ monitor_process      [Correr Programa]
                           ├─ ZoneClassifier       → (mão, zona | None) por frame
                           ├─ TaskStateMachine     → TaskEvent quando tarefa termina
                           ├─ CycleTracker         → CycleResult quando ciclo fecha
                           ├─ MetricsCalculator    → MetricsSnapshot atualizado
                           ├─ DebugLogger          → output/debug_*.csv  (tempo real)
                           ├─ DashboardWriter      → dashboard/data/metrics.json
                           │                               ↓
                           │                         Streamlit (dashboard/app.py)
                           └─ ExcelExporter        → output/sessao_*.xlsx  (no fim)
```

---

## Configuração rápida

Tudo o que se pode ajustar sem tocar no código está em **`config/settings.yaml`**:

| Parâmetro | O que controla |
|-----------|---------------|
| `camera.index` | Índice da câmara USB (0 = primeira) |
| `tracking.dwell_time_seconds` | Tempo mínimo parado na zona para confirmar tarefa |
| `tracking.task_timeout_seconds` | Tempo máximo numa tarefa antes de forçar fecho |
| `tracking.stillness_threshold_px` | Velocidade máxima do pulso para "mão parada" (px/frame) |
| `tracking.two_hands_zones` | Zonas que exigem as duas mãos em simultâneo (ex: `["Montagem"]`) |
| `tracking.cycle_zone_order` | Ordem esperada das zonas num ciclo completo |
| `tracking.exit_zone` | Zona cujo fecho encerra o ciclo (ex: `"Saida"`) |
| `dashboard.refresh_seconds` | Intervalo de atualização do dashboard |

As ROIs (coordenadas dos retângulos) ficam em **`config/rois.json`** — gerado pela opção 2 do menu.

---

## Referência de ficheiros

### Ponto de entrada

| Ficheiro | O que faz | Alterar aqui |
|----------|-----------|-------------|
| `main.py` | Menu, monta e lança os processos certos para cada modo | Adicionar opções ao menu, mudar tamanhos das queues |

### Processos da pipeline

Cada ficheiro tem uma função `run()` que corre num processo separado via multiprocessing.

| Ficheiro | Modo | Papel |
|----------|------|-------|
| `capture_process.py` | Ambos | Lê frames da câmara, converte BGR→RGB, envia para `frame_queue` |
| `detection_process.py` | Ambos | Corre o MediaPipe, envia `(frame, mãos)` para `detection_queue` |
| `display_process.py` | Testar câmara | Mostra a janela com keypoints e FPS |
| `monitor_process.py` | Correr programa | Orquestra todo o pipeline: zones → state machine → métricas → outputs |

### Dashboard

| Ficheiro | O que faz |
|----------|-----------|
| `dashboard/app.py` | App Streamlit — lê `metrics.json` e apresenta as métricas em tempo real |
| `dashboard/data/metrics.json` | Gerado pelo `DashboardWriter` durante a sessão; não editar manualmente |

### Deteção de mãos (`src/detection/`)

| Ficheiro | O que faz |
|----------|-----------|
| `detector_interface.py` | Interface abstrata — permite trocar o detector sem mudar o resto |
| `mediapipe_detector.py` | Implementação com MediaPipe; converte landmarks normalizados para píxeis |
| `hand_detection.py` | Value object de uma mão detetada: keypoints, bounding box, confiança, lado |
| `keypoint_collection.py` | Os 21 landmarks da mão; expõe `finger_mcp_centroid()` para classificação de zona |
| `keypoint.py` | Um landmark individual: índice + Point + confiança |
| `bounding_box.py` | Retângulo calculado a partir dos extremos dos landmarks |

> Trocar o detector: implementa `DetectorInterface` numa nova classe e atualiza `detection_process.py`.

### Zonas de trabalho (`src/roi/`)

| Ficheiro | O que faz |
|----------|-----------|
| `region_of_interest.py` | Uma zona: nome + dois pontos + método `contains()` |
| `roi_collection.py` | Coleção de zonas com lookup O(1) por nome |
| `roi_repository.py` | Interface de persistência |
| `json_roi_repository.py` | Lê e escreve `rois.json` |
| `roi_drawer.py` | Sessão interativa de desenho de ROIs com o rato |

### Tracking e estado (`src/tracking/`)

| Ficheiro | O que faz |
|----------|-----------|
| `zone_classifier.py` | Frame a frame: diz em que zona está cada mão (ou None se em trânsito) |
| `activation_strategy.py` | Define quando o dwell timer avança: `StillnessDwellStrategy` (mão parada) ou `TimeDwellStrategy` (sempre) |
| `task_state_machine.py` | `OneHandStateMachine` e `TwoHandsStateMachine`; o `TaskStateMachine` orquestra qual usar conforme a zona |
| `task_event.py` | Value object de uma tarefa concluída: zona, start/end, duração, ciclo, `was_forced` |
| `cycle_tracker.py` | Acumula tarefas por ciclo; fecha o ciclo quando deteta a `exit_zone`; valida a ordem |
| `cycle_result.py` | Value object de um ciclo completo: duração, número, `order_ok`, sequência real |

> Mudar o critério de confirmação (ex: tempo fixo em vez de "mão parada"): `activation_strategy.py` + `settings.yaml`.
> Mudar o que é "ordem correta": `cycle_tracker.py` (`_matches_order()`) + `tracking.cycle_zone_order` em settings.

### Métricas (`src/metrics/`)

| Ficheiro | O que faz |
|----------|-----------|
| `task_metrics.py` | Min/avg/max/desvio padrão das durações de uma zona |
| `cycle_metrics.py` | Estatísticas de ciclos + contagem de ordem correta/incorreta |
| `metrics_calculator.py` | Recebe TaskEvents e CycleResults; separa produtivo/interrupção/transição; identifica o gargalo |

### Saída de dados (`src/output/`)

| Ficheiro | O que faz |
|----------|-----------|
| `output_interface.py` | Interface `write(snapshot)` — permite adicionar novos outputs sem mudar o pipeline |
| `metrics_snapshot.py` | Dataclass imutável com o estado completo das métricas num instante |
| `dashboard_writer.py` | Serializa o snapshot para JSON com escrita atómica (evita race condition com o Streamlit) |
| `excel_exporter.py` | Exporta Excel com 4 folhas: Resumo, Métricas por Zona, Ciclos, Eventos |

> Adicionar uma nova forma de exportação (ex: base de dados): implementa `OutputInterface` e regista em `monitor_process.py`.

### Logging de debug (`src/events/`)

| Ficheiro | O que faz |
|----------|-----------|
| `debug_logger.py` | CSV em tempo real com todos os eventos: ZONE_ENTER, ZONE_EXIT, TASK_COMPLETE, TASK_TIMEOUT, CYCLE_COMPLETE |
| `zone_event.py` | Value object de um evento de entrada/saída de zona |
| `event_logger.py` | Versão anterior — não está em uso ativo |

### Partilhados (`src/shared/`)

| Ficheiro | O que faz |
|----------|-----------|
| `point.py` | `Point(x, y)` em píxeis com `distance_to()` |
| `confidence.py` | Confiança da deteção (0–1) com validação |
| `hand_side.py` | `HandSide.LEFT / RIGHT` |
| `task_state.py` | Estados da máquina: IDLE → DWELLING → TASK_IN_PROGRESS (e variantes two-hands) |
| `event_type.py` | `EventType.ENTER / EXIT` — usado no CSV de debug |

### Vídeo (`src/video/`)

| Ficheiro | O que faz |
|----------|-----------|
| `camera.py` | Abre e lê frames da câmara via OpenCV |
| `frame_annotator.py` | Desenha esqueleto, keypoints, bounding boxes, ROIs e FPS sobre frames |
