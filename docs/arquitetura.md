# Arquitetura do Projeto

Este documento é a referência técnica curta do projeto. A documentação histórica
e notas de sessão foram removidas para evitar contradições com o código atual.

## Fluxo de Dados

```text
Câmara BGR
  -> capture_process.py
       converte para RGB e publica frame_queue
  -> detection_process.py
       MediaPipe produz HandDetection
  -> monitor_process.py
       classifica zonas, valida tarefas, fecha ciclos e escreve outputs
  -> dashboard/app.py
       lê dashboard/data/metrics.json
```

Modo `Testar câmara` usa `display_process.py` no lugar de `monitor_process.py`.

## Processos Principais

| Ficheiro | Responsabilidade |
|---|---|
| `main.py` | Menu, valida configuração, lança processos e dashboard. |
| `capture_process.py` | Captura frames da câmara e mantém baixa latência descartando frames antigos. |
| `detection_process.py` | Executa o detector e sincroniza frame + deteções. |
| `display_process.py` | Mostra feed anotado no modo de teste. |
| `monitor_process.py` | Orquestra tracking, métricas, logging, Excel, dashboard e vídeo. |

## Pacotes

| Pacote | Responsabilidade |
|---|---|
| `src/detection/` | Modelo de deteção de mãos e implementação MediaPipe. |
| `src/roi/` | Zonas da bancada, coleção, persistência JSON e editor interativo. |
| `src/tracking/` | Classificação de zona, dwell/stillness, state machines, ciclos e ordem. |
| `src/metrics/` | Métricas por tarefa, ciclo, gargalo e decomposição de tempo. |
| `src/output/` | Snapshots, dashboard JSON, Excel, vídeo e layout de sessão. |
| `src/events/` | CSV de debug em tempo real. |
| `src/shared/` | Tipos partilhados como `Point`, `Confidence`, enums e config validada. |
| `src/video/` | Câmara OpenCV e desenho de overlays. |

## Tracking

`ZoneClassifier` usa `finger_mcp_centroid()` como ponto de referência. Esse ponto
é mais estável do que o pulso para zonas distantes e menos ruidoso do que as
pontas dos dedos durante grasping.

`TaskStateMachine` decide se uma zona usa uma mão ou duas mãos:

- zonas normais usam `OneHandStateMachine`;
- zonas em `tracking.two_hands_zones` usam `TwoHandsStateMachine`;
- `ActivationStrategy` define se o dwell avança por tempo simples ou stillness.

`CycleTracker` acumula `TaskEvent`s e fecha o ciclo quando:

- a `exit_zone` é concluída normalmente; ou
- uma nova primeira zona esperada aparece depois de já haver progresso, fechando
  o ciclo anterior como incompleto/a rever.

## Outputs

| Output | Escritor |
|---|---|
| CSV de debug | `DebugLogger` |
| Snapshot config/ROIs | `session_config_snapshot.py` |
| Dashboard JSON | `DashboardWriter` |
| Excel final | `ExcelExporter` |
| Vídeo anotado | `VideoRecorder` |

`DashboardWriter` usa escrita atómica com ficheiro temporário para impedir que
o Streamlit leia JSON parcial.

## Convenção de Comentários

- Classes e funções públicas devem ter docstring curta em português.
- Funções privadas só recebem docstring quando a intenção não é óbvia pelo nome.
- Comentários dentro do código devem explicar decisões ou regras de negócio, não
  repetir linha a linha o que o código já diz.

