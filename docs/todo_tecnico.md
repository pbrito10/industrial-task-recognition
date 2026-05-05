# TODO técnico — problemas a resolver

Este ficheiro lista problemas concretos ainda abertos no projeto. A ideia não é só dizer "fazer X", mas deixar claro **qual é o problema**, **porque importa**, **onde vive no código** e **quando podemos considerar que está resolvido**.

## 1. ROIs e número de zonas ainda têm limites e resíduos perigosos

### Problema

O número de zonas está quase todo configurável em `config/settings.yaml`, mas o editor interativo de ROIs ainda tem partes presas a pressupostos antigos:

- a janela do editor mostra `1-7 zona`, apesar de as zonas virem de `tracking.zones`;
- a seleção por teclado só aceita teclas `1` a `9`;
- se uma zona for removida do `settings.yaml` mas continuar em `config/rois.json`, o `ZoneClassifier` ainda pode detetá-la, porque carrega todas as ROIs guardadas no JSON.

Isto cria uma inconsistência: a config pode dizer que existem N zonas, mas o editor e o ficheiro de ROIs podem não acompanhar essa verdade.

### Porque importa

Se o layout da bancada mudar, o utilizador deve poder ajustar apenas a configuração e redesenhar as ROIs sem tocar no código. Com o estado atual:

- até 9 zonas, o sistema provavelmente funciona, mas a UI mostra texto errado;
- com 10 ou mais zonas, não há forma simples de selecionar todas pelo teclado;
- zonas antigas podem continuar "ativas" se ficarem no `rois.json`, gerando eventos inesperados, métricas para zonas fora da config ou ciclos marcados como fora de ordem.

### Ficheiros envolvidos

- `config/settings.yaml`
- `config/rois.json`
- `src/roi/roi_drawer.py`
- `src/roi/roi_collection.py`
- `src/tracking/zone_classifier.py`
- `main.py`

### Direção de solução

- Gerar o texto da janela do `RoiDrawer` a partir do número real de zonas.
- Substituir a seleção fixa `1` a `9` por uma navegação que suporte qualquer número razoável de zonas, por exemplo:
  - setas cima/baixo ou esquerda/direita para mudar a zona selecionada;
  - números apenas como atalho opcional para as primeiras 9 zonas.
- Ao carregar ou guardar ROIs, garantir que a coleção usada pelo sistema contém apenas zonas presentes em `tracking.zones`.
- Avisar claramente quando houver ROIs guardadas que já não existem na config.
- Manter a validação atual que impede correr o programa se faltar ROI para uma zona referenciada no ciclo.

### Critérios de conclusão

- Alterar `tracking.zones` para 5, 7, 9 ou 10 zonas não exige mudança de código.
- O editor permite selecionar e desenhar todas as zonas configuradas.
- `config/rois.json` não deixa zonas antigas interferirem no pipeline.
- Há testes unitários para:
  - seleção/navegação no `RoiDrawer`;
  - filtragem ou deteção de ROIs fora da config;
  - validação config vs ROIs.

## 2. Tempo de transição global não identifica onde se perde tempo

### Problema

Neste momento, o sistema calcula o tempo de transição como uma massa global:

```text
tempo total da sessão - tempo produtivo - tempo de interrupção
```

Isto diz quanto tempo foi gasto fora de tarefas produtivas, mas não diz **entre que zonas** esse tempo ocorreu.

Exemplo: saber que houve 20% de transição na sessão não permite distinguir se o problema está em `Porca -> Montagem`, `Montagem -> Rodas`, `Rodas -> Montagem` ou noutra deslocação.

### Porque importa

O objetivo do projeto é apoiar decisões sobre organização da bancada. Para isso, é mais útil saber quais deslocações físicas são lentas.

Medir transições individualmente permite responder a perguntas como:

- as caixas nas pontas da bancada obrigam a deslocações mais longas?
- a zona de montagem está bem posicionada?
- há uma peça específica que cria mais tempo morto?
- que percurso deve ser otimizado primeiro?

Sem esta granularidade, o tempo de transição global é pouco defensável como evidência operacional.

### Ficheiros envolvidos

- `monitor_process.py`
- `src/tracking/cycle_tracker.py`
- `src/tracking/task_event.py`
- `src/metrics/metrics_calculator.py`
- `src/output/excel_exporter.py`
- `src/output/metrics_snapshot.py`
- `dashboard/app.py`
- testes em `tests/metrics/`, `tests/tracking/` e `tests/output/`

### Direção de solução

Criar uma estrutura explícita para transições entre tarefas concluídas:

```text
origem: zona anterior concluída
destino: zona seguinte concluída
início: fim da tarefa anterior
fim: início da tarefa seguinte
duração: fim - início
ciclo: número do ciclo
```

Sempre que uma tarefa normal termina e existe uma tarefa normal anterior no mesmo ciclo, criar um registo de transição entre as duas.

Depois, exportar esses dados no Excel:

- folha `Transições`;
- folha `Transições por percurso`.

Colunas sugeridas para `Transições`:

```text
Ciclo
Origem
Destino
Início
Fim
Duração (s)
```

Colunas sugeridas para `Transições por percurso`:

```text
Origem
Destino
Ocorrências
Mínimo (s)
Médio (s)
Máximo (s)
Desvio padrão (s)
```

Mais tarde, o dashboard pode mostrar os percursos mais lentos, mas primeiro é melhor garantir que o Excel fica correto e validável.

### Critérios de conclusão

- Cada transição entre duas tarefas normais consecutivas fica registada com origem, destino, início, fim, duração e ciclo.
- Timeouts/interrupções não entram como transições produtivas normais sem uma decisão explícita.
- O Excel inclui as folhas `Transições` e `Transições por percurso`.
- As métricas agregadas por percurso batem certo com os eventos brutos.
- Há testes unitários para:
  - criação de transições entre tarefas;
  - ignorar ou tratar corretamente timeouts;
  - exportação das duas folhas no Excel;
  - agregação por par origem/destino.

## 3. Regra variável da zona das rodas precisa de melhor modelação

### Problema

A zona `Rodas` não se comporta como uma etapa fixa do ciclo. O operador pode ir buscar entre 1 e 4 rodas, por isso a sequência correta não é simplesmente "uma presença em Rodas" nem "quatro presenças obrigatórias".

Foi aplicada uma tolerância pragmática na validação de ordem: quando `Rodas` aparece em `tracking.cycle_zone_order`, o sistema aceita entre 1 e 4 presenças, incluindo idas repetidas intercaladas com a zona seguinte, como `Rodas -> Montagem -> Rodas -> Montagem`. Isto resolve a análise imediata dos ciclos, mas ainda deixa uma questão de fundo: a configuração atual descreve uma lista linear de zonas, não uma sequência com cardinalidade variável por etapa.

### Porque importa

Esta regra está ligada ao processo físico e não devia ficar escondida como exceção no código. Se no futuro outra zona também tiver cardinalidade variável, ou se o limite das rodas mudar, a lógica deve ser configurável e fácil de explicar na validação.

Também convém decidir como representar estas presenças no Excel: uma única coluna `Rodas`, várias colunas `Rodas_1` a `Rodas_4`, ou uma coluna agregada com contagem e duração total.

### Ficheiros envolvidos

- `config/settings.yaml`
- `src/tracking/order_matching.py`
- `src/tracking/cycle_tracker.py`
- `src/output/excel_exporter.py`
- testes em `tests/tracking/` e `tests/output/`

### Direção de solução

- Evoluir `tracking.cycle_zone_order` para suportar etapas com cardinalidade, por exemplo `min_occurrences` e `max_occurrences`.
- Remover o hardcode da zona `Rodas` quando a regra estiver em configuração.
- Definir a visualização/exportação das ocorrências variáveis no relatório.
- Garantir que os relatórios continuam a refletir a configuração usada em cada sessão.

### Critérios de conclusão

- A regra 1 a 4 para `Rodas` é configurável sem mexer no código.
- O relatório mostra claramente quantas presenças em `Rodas` foram registadas por ciclo.
- Ciclos com 0 presenças em `Rodas` continuam a ser marcados como incompletos.
- Ciclos com mais de 4 presenças em `Rodas` são marcados como `Fora de ordem` ou outra classificação decidida explicitamente.
- Há testes que cobrem os limites 0, 1, 4 e 5 presenças.

## 4. Uniformizar a média de ciclo entre Dashboard e Excel

### Problema

O dashboard mostra `Tempo médio de ciclo` com base apenas nos ciclos em ordem,
enquanto o Excel apresenta a média de todos os ciclos fechados. Ambas as leituras
são defensáveis, mas o mesmo nome para métricas diferentes pode confundir uma
apresentação ou validação.

### Ficheiros envolvidos

- `src/output/dashboard_writer.py`
- `src/output/excel_exporter.py`
- `dashboard/app.py`
- testes em `tests/output/`

### Critérios de conclusão

- Dashboard e Excel usam a mesma definição; ou
- os labels ficam explícitos, por exemplo `Tempo médio dos ciclos em ordem` e
  `Tempo médio de todos os ciclos`.

## 5. Reduzir acoplamento do orquestrador de sessão

### Problema

`monitor_process.py` ainda constrói e coordena muitos componentes diretamente:
state machine, cycle tracker, métricas, CSV, Excel, dashboard, vídeo e display.
Isto funciona, mas torna futuras alterações mais propensas a mexer no mesmo
ficheiro central.

### Direção de solução

- Introduzir um objeto agregador de outputs ou `OutputBus`.
- Fazer `CycleTracker.record()` devolver um resultado explícito com ciclos
  fechados e evento ajustado, em vez de usar estado lateral como
  `last_event_started_new_cycle()`.
- Manter `monitor_process.py` focado em loop de frames e delegar efeitos.

### Critérios de conclusão

- Adicionar um novo output não exige alterar a lógica de processamento de frame.
- O fecho automático de ciclo anterior fica representado por um objeto de retorno
  explícito e testável.
