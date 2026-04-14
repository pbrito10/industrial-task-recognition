# Avaliação do Projeto

## Nota: 16/20

---

## O que está bem feito

**Arquitetura**
O pipeline multiprocessing com queues está correto — cada processo tem uma responsabilidade, a sincronização frame+deteção é explícita, e o drop-frame-antigo em vez de bloquear é a decisão certa para latência baixa.

**Design patterns**
Strategy (`ActivationStrategy`), Repository (`JsonRoiRepository`), State Machine (`TaskStateMachine` + sub-máquinas), value objects frozen — todos usados com propósito, não por cargo cult.

**SOLID aplicado**
DIP visível no `DetectorInterface`, OCP no `_machine_for_zone()`, SRP honrado após os refactors, `_DurationMetrics` eliminou duplicação real entre `TaskMetrics` e `CycleMetrics`.

**Detalhes técnicos certos**
- Lazy imports dentro de cada `run()` para compatibilidade com spawn
- Writes atómicos no `DashboardWriter` (temp + rename)
- `initUndistortRectifyMap` pré-calculado no construtor — `remap()` por frame sem recalcular
- `Camera.from_config()` factory isola o YAML do domínio
- Queue com drop do frame mais antigo em vez de bloquear

**`_matches_order`**
Algoritmo de ponteiro único correto, permite repetições consecutivas da mesma zona sem saltar. Boa lógica para o contexto real de montagem.

---

## O que melhorava

### 1. Testes — maior lacuna

Zero cobertura. `_matches_order`, `CycleTracker.record()`, `MetricsCalculator`, `RoiCollection.find_zone_for_point()` são todos testáveis sem câmara e sem MediaPipe. É onde os bugs se escondem e o primeiro lugar onde qualquer revisor vai olhar.

### 2. `CycleResult` não guarda timestamps

O `ExcelExporter._write_cycles()` reconstrói início e fim a partir dos `TaskEvent`s acumulados. A própria classe tem um comentário a reconhecer o problema. A correção é adicionar `start_time` e `end_time` ao `CycleResult` quando o ciclo fecha em `CycleTracker._close_cycle()`.

### 3. Cores de zona acopladas a nomes hardcoded

`_ZONE_COLOR_MAP` em `frame_annotator.py` tem `"Montagem"` e `"Saida"` hardcoded. Se o nome de uma zona mudar no `settings.yaml`, fica sem cor sem erro nenhum. As cores deviam vir da config ou ser geradas dinamicamente a partir do índice da zona.

### 4. Validação da config

O YAML é carregado como `dict` e acedido com `config["tracking"]["dwell_time_seconds"]` em todo o lado. Um tipo errado ou chave em falta explode no meio do pipeline. Um simples dataclass ou `TypedDict` validado no arranque em `main.py` apanhava isso cedo.

### 5. `Camera.__init__` faz demasiado

Abre o dispositivo, define resolução, lê dois ficheiros `.npz`, calcula mapas de undistortion, trata fallbacks de ficheiros antigos. Um `_load_calibration()` e `_load_perspective()` privados melhoravam a leitura e permitiam testar cada parte isoladamente.

### 6. `print()` para mensagens operacionais

`main.py` usa `print()` para `"A arrancar processos..."`, `"Processos terminados."`, etc. Para um sistema que corre em produção, `logging` com níveis (INFO, WARNING) é o padrão — permite redirecionar para ficheiro e filtrar por severidade sem tocar no código.

### 7. `MetricsSnapshot` contém objetos mutáveis

É um `frozen=True` dataclass, mas o `dict[str, TaskMetrics]` dentro é mutável — alguém pode chamar `.add()` num `TaskMetrics` depois do snapshot ser emitido. Semanticamente o snapshot devia ser um DTO com valores primitivos, não referências vivas para objetos de métricas.

### 8. Duplicação do fix `DISPLAY`

A mesma guarda `os.environ["DISPLAY"] = ":0"` aparece em `main.py`, `capture_process.py` e `display_process.py`. Uma função `_ensure_display()` num módulo partilhado ou centralizá-la num único ponto eliminava a repetição.

---

## Resumo

O projeto está acima da média académica — mostra compreensão real de separação de responsabilidades, não apenas código que funciona. O que falta é o que distingue um projeto bom de um muito bom: **testes automatizados** e **ausência de acoplamento oculto** (cores, timestamps, config crua).
