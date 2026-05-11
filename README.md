# Sistema de Reconhecimento Industrial

Sistema de visão computacional para acompanhar uma bancada de montagem. O programa
deteta mãos, identifica a zona de trabalho usada pelo operador, mede tarefas e
ciclos, mostra métricas em tempo real no dashboard e exporta a sessão para Excel.

## Como Usar

```bash
python main.py
```

| Opção | Função |
|---|---|
| `1` | Testar câmara com esqueleto das mãos e FPS. |
| `2` | Definir ROIs da bancada com o rato. Deve ser feito antes de correr o pipeline. |
| `3` | Correr o pipeline completo com dashboard, vídeo anotado, CSV e Excel. |

## Docker com Câmara e GUI

Esta configuração corre o menu principal dentro do container, com acesso à
câmara USB e às janelas gráficas do OpenCV via X11.

Antes de arrancar, permite temporariamente que containers locais usem o ecrã:

```bash
xhost +local:root
```

Depois corre a aplicação:

```bash
docker compose run --rm --service-ports app
```

Se a câmara não for `/dev/video0`, indica o dispositivo:

```bash
VIDEO_DEVICE=/dev/video2 docker compose run --rm --service-ports app
```

Quando escolheres a opção `3`, o dashboard Streamlit fica disponível em:

```text
http://localhost:8501
```

No fim, podes fechar novamente o acesso X11:

```bash
xhost -local:root
```

## Outputs da Sessão

Cada execução cria uma pasta em:

```text
output/sessions/<data_hora>/
```

| Ficheiro/pasta | Conteúdo |
|---|---|
| `debug_*.csv` | Eventos em tempo real: entradas/saídas de zonas, tarefas, rejeições, gaps e ciclos. |
| `debug_*_config.json` | Configuração e ROIs usadas naquela sessão. |
| `sessao_*.xlsx` | Resumo, métricas por zona, ciclos e eventos. |
| `video/*_annotated.mp4` | Vídeo anotado com mãos e ROIs. |
| `frames/gaps/` | Frames guardados quando há gaps de deteção relevantes. |

O dashboard lê `dashboard/data/metrics.json`, gerado continuamente pelo pipeline.

## Conceitos

| Conceito | Significado |
|---|---|
| ROI | Retângulo que representa uma zona física da bancada. |
| Dwell time | Tempo mínimo que a mão tem de cumprir na zona antes de a tarefa ser validada. |
| Stillness | Critério de mão parada, medido pelo centróide MCP dos dedos. |
| TaskEvent | Tarefa validada ou fechada por timeout. |
| CycleResult | Resultado de um ciclo fechado, incluindo duração e sequência registada. |
| TASK_REJECTED | Tentativa descartada antes de virar tarefa completa. |
| DETECTION_GAP | Período relevante sem deteção de uma mão. |

## Configuração Principal

Os parâmetros editáveis estão em `config/settings.yaml`.

| Parâmetro | Função |
|---|---|
| `detection.min_detection_confidence` | Confiança mínima para aceitar deteções novas. |
| `detection.min_tracking_confidence` | Confiança mínima para tracking entre frames. |
| `tracking.dwell_time_seconds` | Tempo mínimo de validação da tarefa. |
| `tracking.task_timeout_seconds` | Tempo máximo antes de fechar tarefa por timeout. |
| `tracking.stillness_threshold_px` | Velocidade máxima do centróide MCP para considerar a mão parada. |
| `tracking.two_hands_zones` | Zonas que exigem duas mãos, como `Montagem`. |
| `tracking.two_hands_missing_tolerance_seconds` | Tolerância a oclusões curtas em zonas de duas mãos. |
| `tracking.assembly_zone` | Zona física de montagem que recebe nomes mais específicos na análise. |
| `tracking.assembly_task_labels` | Mapeia a peça anterior para nomes como `Montagem Porca`; montagem sem peça anterior conta como interrupção. |
| `tracking.cycle_zone_order` | Ordem esperada das zonas num ciclo. |
| `tracking.exit_zone` | Zona que fecha o ciclo quando concluída. |
| `output.record_video` | Liga/desliga gravação do vídeo anotado. |

As coordenadas das ROIs ficam em `config/rois.json`, gerado pela opção `2`.

## Documentação

| Documento | Propósito |
|---|---|
| `docs/arquitetura.md` | Fluxo do pipeline e responsabilidade dos módulos. |
| `docs/brief_cliente.md` | Visão funcional e âmbito do sistema. |
| `docs/metodologia_validacao.md` | Como validar o sistema contra ground truth manual. |
| `docs/todo_tecnico.md` | Dívida técnica e melhorias futuras ainda relevantes. |

## Testes

```bash
.venv/bin/python -m pytest
```

A suite cobre deteção, ROIs, tracking, métricas, outputs, vídeo, config e logging.
