# Mapa do Projeto — Sistema de Reconhecimento Industrial

## Para que serve cada ficheiro e onde ir para mudar o quê

---

## Ponto de entrada

| Ficheiro | O que faz |
|----------|-----------|
| `main.py` | Menu principal, monta os processos e lança os modos. **Alterar aqui**: menu, nomes de opções, ordem de lançamento dos processos, caminho de config/ROIs |

---

## Processos da pipeline

Cada ficheiro tem uma função `run()` que corre num processo separado.

| Ficheiro | Modo | Papel na pipeline |
|----------|------|-------------------|
| `capture_process.py` | Testar câmara / Correr programa | Lê frames da câmara, converte para RGB, envia para `frame_queue` |
| `detection_process.py` | Testar câmara / Correr programa | Lê frames do `frame_queue`, corre o detector MediaPipe, envia `(frame, mãos)` para `detection_queue` |
| `display_process.py` | **Testar câmara** | Recebe `(frame, mãos)` e mostra a janela com keypoints e FPS |
| `monitor_process.py` | **Correr programa** | Recebe `(frame, mãos)`, classifica zonas, atualiza a state machine, calcula métricas, mostra janela; exporta Excel e dashboard no fim |

**Alterar aqui:**
- Resolução / índice da câmara → `config/settings.yaml` (secção `camera`)
- Tamanho das queues → `main.py` (`Queue(maxsize=...)`)
- Lógica de visualização ao vivo → `display_process.py` ou `monitor_process.py`

---

## Dashboard (Streamlit)

| Ficheiro | O que faz |
|----------|-----------|
| `dashboard/app.py` | App Streamlit. Lê `dashboard/data/metrics.json` e apresenta métricas em tempo real |
| `dashboard/data/metrics.json` | Gerado pelo `DashboardWriter` durante a sessão. Não editar manualmente |
| `.streamlit/config.toml` | Configuração do Streamlit (headless, usage stats) |

**Alterar aqui:**
- Layout ou secções do dashboard → `dashboard/app.py`
- Intervalo de atualização → `config/settings.yaml` (secção `dashboard.refresh_seconds`)

---

## Configuração

| Ficheiro | O que faz |
|----------|-----------|
| `config/settings.yaml` | Todas as configurações da aplicação (câmara, tracking, dashboard, output) |
| `config/rois.json` | Zonas desenhadas pelo utilizador (gerado pela opção "Definir ROIs") |

**Alterar aqui:**
- Tempo de dwell → `tracking.dwell_time_seconds`
- Timeout de tarefa → `tracking.task_timeout_seconds`
- Ordem esperada de ciclo → `tracking.cycle_zone_order`
- Zona de saída do ciclo → `tracking.exit_zone`
- Zonas que exigem duas mãos → `tracking.two_hands_zones`
- Pasta de exportação Excel → `output.excel_output_dir`

---

## Deteção de mãos (`src/detection/`)

| Ficheiro | O que faz |
|----------|-----------|
| `detector_interface.py` | Interface abstrata `DetectorInterface` (OCP) |
| `mediapipe_detector.py` | Implementação com MediaPipe Hands — devolve lista de `HandDetection` |
| `hand_detection.py` | Value object com `hand_side`, `keypoints`, `bounding_box`, `confidence` |
| `keypoint_collection.py` | First-class collection dos 21 landmarks MediaPipe |
| `keypoint.py` | Um landmark: índice + `Point` |
| `bounding_box.py` | Retângulo com `top_left`, `bottom_right` e lógica de centróide |

**Alterar aqui:**
- Trocar o modelo de deteção → implementar nova classe que respeite `DetectorInterface` e atualizar `detection_process.py`
- Ajustar confiança mínima de deteção → `mediapipe_detector.py`

---

## Zonas de trabalho (`src/roi/`)

| Ficheiro | O que faz |
|----------|-----------|
| `region_of_interest.py` | Value object de uma zona: nome, `top_left`, `bottom_right`, método `contains()` |
| `roi_collection.py` | First-class collection das zonas (lookup O(1) por nome) |
| `roi_repository.py` | Interface abstrata de persistência |
| `json_roi_repository.py` | Lê/escreve `rois.json` |
| `roi_drawer.py` | Sessão interativa de desenho de ROIs com rato sobre a câmara |

**Alterar aqui:**
- Formato de persistência das ROIs → `json_roi_repository.py`
- Interface de desenho (controlos, visualização) → `roi_drawer.py`
- Lógica de "ponto está dentro da zona" → `region_of_interest.py` (`contains()`)

---

## Tracking e estado da tarefa (`src/tracking/`)

| Ficheiro | O que faz |
|----------|-----------|
| `zone_classifier.py` | Recebe lista de `HandDetection`, devolve `(detection, zona | None)` para cada mão |
| `task_state_machine.py` | Três classes: `OneHandStateMachine`, `TwoHandsStateMachine`, `TaskStateMachine` (orquestrador). Gerem o ciclo IDLE → DWELLING → TASK_IN_PROGRESS → IDLE |
| `activation_strategy.py` | Estratégias de ativação: `TimeDwellStrategy` (tempo fixo) e `StillnessDwellStrategy` (mão parada) |
| `task_event.py` | Value object de uma tarefa concluída: zona, start/end, duração, ciclo, `was_forced` |
| `cycle_tracker.py` | Regista a sequência de zonas por ciclo; verifica ordem; emite `CycleResult` ao detetar a zona de saída |
| `cycle_result.py` | Value object de um ciclo completo: duração, número, `order_ok`, sequência real |

**Alterar aqui:**
- Algoritmo de ativação (ex: mudar de "stillness" para "tempo fixo") → `activation_strategy.py` e `config/settings.yaml`
- Lógica de transição de estados → `task_state_machine.py`
- Como se define o fim de um ciclo → `cycle_tracker.py` (`exit_zone` em settings)
- O que é "ordem correta" → `cycle_tracker.py` (`_matches_order()`) e `tracking.cycle_zone_order` em settings

---

## Métricas (`src/metrics/`)

| Ficheiro | O que faz |
|----------|-----------|
| `task_metrics.py` | Estatísticas de duração por zona (min/avg/max/std) |
| `cycle_metrics.py` | Estatísticas de ciclos + contagem de ordem correta/incorreta |
| `metrics_calculator.py` | Agrega `TaskEvent`s e `CycleResult`s; separa produtivo/interrupção/transição; calcula gargalo |

**Alterar aqui:**
- Definição de "zona gargalo" → `metrics_calculator.py` (`_bottleneck_zone()`)
- Fórmula de tempo de transição → `metrics_calculator.py` (`_transition_time()`)

---

## Saída de dados (`src/output/`)

| Ficheiro | O que faz |
|----------|-----------|
| `output_interface.py` | Interface abstrata `OutputInterface` com método `write(snapshot)` |
| `metrics_snapshot.py` | Dataclass imutável com o estado completo das métricas num instante |
| `dashboard_writer.py` | Serializa o snapshot para `dashboard/data/metrics.json` (escrita atómica) |
| `excel_exporter.py` | Exporta Excel com 4 folhas: Resumo, Métricas por Zona, Ciclos, Eventos |

**Alterar aqui:**
- Adicionar colunas ao Excel → `excel_exporter.py`
- Mudar o formato do JSON do dashboard → `dashboard_writer.py` (`_serialize()`)
- Adicionar nova forma de exportação → implementar `OutputInterface` e registar em `monitor_process.py`

---

## Logging de debug (`src/events/`)

| Ficheiro | O que faz |
|----------|-----------|
| `debug_logger.py` | Context manager que escreve CSV com eventos ZONE_ENTER, ZONE_EXIT, TASK_COMPLETE, TASK_TIMEOUT, CYCLE_COMPLETE |
| `event_logger.py` | Versão anterior (mantida por compatibilidade — não está em uso ativo) |
| `zone_event.py` | Value object de um evento de zona (entrada/saída) |

**Alterar aqui:**
- Colunas do CSV de debug → `debug_logger.py`
- Pasta de saída dos CSVs → `config/settings.yaml` (`output.excel_output_dir`) — o CSV vai para a mesma pasta

---

## Partilhados (`src/shared/`)

| Ficheiro | O que faz |
|----------|-----------|
| `point.py` | Value object `Point(x, y)` em píxeis |
| `confidence.py` | Value object para a confiança da deteção (0–1); `as_percentage()` |
| `hand_side.py` | Enum `HandSide.LEFT / RIGHT` |
| `task_state.py` | Enum dos estados da máquina: IDLE, DWELLING, WAITING_SECOND_HAND, DWELLING_TWO_HANDS, TASK_IN_PROGRESS |
| `event_type.py` | Enum dos tipos de evento para o CSV de debug |

---

## Vídeo (`src/video/`)

| Ficheiro | O que faz |
|----------|-----------|
| `camera.py` | Abre e lê frames da câmara via OpenCV |
| `frame_annotator.py` | Funções de desenho sobre frames: esqueleto, keypoints, bounding boxes, ROIs, FPS |

---

## Fluxo de dados resumido

```
câmara (BGR)
  └─ capture_process  → frame_queue (RGB)
       └─ detection_process  → detection_queue (frame RGB, [HandDetection])
            ├─ display_process   [Testar Câmara]
            └─ monitor_process   [Correr Programa]
                 ├─ ZoneClassifier → (detection, ROI | None)
                 ├─ TaskStateMachine → TaskEvent
                 ├─ CycleTracker → CycleResult
                 ├─ MetricsCalculator → MetricsSnapshot
                 ├─ DashboardWriter → dashboard/data/metrics.json → Streamlit
                 └─ ExcelExporter → output/*.xlsx
```
