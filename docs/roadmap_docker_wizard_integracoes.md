# Roadmap: Docker, Wizard e Integrações

Este documento regista a direção discutida depois da apresentação do projeto:
estabilizar primeiro o ambiente de execução, depois tornar a configuração de
bancadas mais flexível e só a seguir avançar para integrações industriais como
base de dados, Grafana, MQTT e balanças.

A regra principal é evitar mudar demasiadas coisas ao mesmo tempo. Cada fase
deve deixar o projeto num estado executável e validável.

## Objetivo Geral

Evoluir o protótipo atual para uma aplicação mais fácil de instalar noutras
bancadas, mais integrada com sistemas externos e mais preparada para validar a
tarefa real do operador.

O estado atual já produz:

- CSV de debug por sessão;
- Excel final;
- vídeo anotado;
- métricas em dashboard Streamlit;
- configuração por `config/settings.yaml`;
- ROIs em `config/rois.json`.

A evolução prevista deve manter estes outputs como apoio à validação, mesmo que
sejam adicionados novos destinos de dados.

## Fase 1: Dockerizar o Projeto Atual

Primeiro passo recomendado: correr o sistema atual dentro de Docker, mantendo a
arquitetura praticamente igual.

Nesta fase, o objetivo não é transformar já o projeto em microserviços. O
objetivo é garantir que o mesmo código corre de forma repetível em qualquer
máquina/bancada.

### Entregáveis

- `Dockerfile` para a aplicação Python.
- `docker-compose.yml` para correr o projeto localmente.
- Volumes para dados que devem viver fora da imagem:
  - `config/`;
  - `output/`;
  - `model/`;
  - `calibration/`.
- Acesso à câmara, por exemplo `/dev/video0`.
- Instruções para correr:
  - testes;
  - `python main.py`;
  - modo de operação com câmara.

### Pontos de Atenção

O projeto usa OpenCV e janelas gráficas (`cv2.imshow`). Em Docker, isto exige
decidir como a interface visual será exposta:

- X11/Wayland da máquina host;
- execução headless para testes;
- eventual separação futura entre processamento e visualização.

Também é importante medir se a gravação de vídeo e o acesso à câmara dentro do
container afetam a latência.

### Critério de Conclusão

A fase fica concluída quando for possível:

- correr a suite de testes dentro do container;
- iniciar o menu principal dentro do container;
- aceder à câmara;
- executar uma sessão real;
- gerar os mesmos outputs que hoje são gerados fora de Docker.

## Fase 2: Integrar o Wizard

Depois de Docker estar estável, integrar o wizard que está noutra branch.

O wizard deve ser tratado como ferramenta de configuração da bancada, não como
substituto imediato do pipeline. A configuração gerada por ele deve alimentar os
mesmos ficheiros/estruturas que o sistema já usa.

### Objetivo do Wizard

Permitir configurar bancadas diferentes sem alterar código.

Deve apoiar, pelo menos:

- seleção ou criação de uma bancada;
- definição das zonas físicas;
- configuração da ordem esperada do ciclo;
- definição da zona de saída;
- definição das zonas que exigem duas mãos;
- configuração da zona de montagem;
- mapeamento entre peça anterior e etiqueta de montagem;
- desenho ou validação das ROIs;
- validação final antes de correr o pipeline.

### Relação com Configuração Atual

O wizard deve produzir ou atualizar:

- `config/settings.yaml`;
- `config/rois.json`;
- possivelmente perfis por bancada no futuro.

Uma evolução provável é organizar configurações por bancada:

```text
config/
  benches/
    bancada_01/
      settings.yaml
      rois.json
      calibration/
    bancada_02/
      settings.yaml
      rois.json
      calibration/
```

Esta reorganização deve ser feita apenas quando o wizard exigir esse modelo.
Enquanto não for necessário, é preferível manter a estrutura simples.

### Critério de Conclusão

A fase fica concluída quando uma bancada puder ser configurada pelo wizard e uma
sessão real puder ser executada com essa configuração sem edição manual de
código.

## Fase 3: Preparar Dados para Base de Dados

Só depois de Docker e wizard estarem estáveis faz sentido evoluir os outputs.

A base de dados deve entrar em paralelo com CSV e Excel, não como substituição
imediata. CSV e Excel continuam úteis para auditoria, validação académica e
debug local.

### Dados a Persistir

Tabelas ou entidades prováveis:

```text
sessions
task_events
cycle_results
detection_gaps
zone_transitions
frame_stats
scale_events
pickup_confirmations
```

O primeiro objetivo deve ser persistir os eventos que já existem:

- início/fim de tarefas;
- timeouts;
- rejeições por dwell/stillness;
- gaps de deteção;
- ciclos completos;
- classificação dos ciclos.

Depois podem entrar métricas agregadas e eventos das balanças.

### Critério de Conclusão

A fase fica concluída quando os dados essenciais de uma sessão ficam disponíveis
na base de dados e batem certo com o CSV/Excel gerados na mesma sessão.

## Fase 4: Grafana em Vez de Streamlit

Grafana deve consumir a base de dados, não ficheiros locais.

O Streamlit pode continuar temporariamente enquanto a migração não estiver
validada. A troca deve acontecer quando o Grafana já conseguir responder às
perguntas principais da operação.

### Dashboards Esperados

- duração da sessão;
- número de ciclos;
- ciclos em ordem;
- ciclos a rever;
- tempo médio por tarefa;
- tarefa gargalo;
- percentagem de tempo produtivo, transição e interrupção;
- gaps de deteção por mão;
- evolução temporal de eventos;
- comparação entre bancadas ou sessões.

### Critério de Conclusão

A fase fica concluída quando o dashboard Grafana cobre pelo menos as métricas
atuais do Streamlit e permite consultar sessões passadas.

## Fase 5: MQTT e Integração com Sistemas Externos

MQTT deve ser usado para publicar eventos relevantes do sistema e para receber
eventos de outros projetos, como as balanças.

Não deve ser o primeiro passo porque depende de eventos bem modelados. Primeiro
é preciso saber exatamente que eventos fazem sentido publicar e consumir.

### Eventos a Publicar

Tópicos possíveis:

```text
industrial-task/session_started
industrial-task/session_finished
industrial-task/task_completed
industrial-task/task_timeout
industrial-task/cycle_completed
industrial-task/detection_gap
industrial-task/pickup_confirmed
```

Cada mensagem deve incluir identificadores mínimos:

- `session_id`;
- `cycle_number`;
- `timestamp`;
- `zone`;
- `analysis_label`, quando aplicável;
- `hand`, quando aplicável;
- `duration_s`, quando aplicável.

### Eventos a Consumir

Para as balanças, tópicos possíveis:

```text
scales/{scale_id}/weight
scales/{scale_id}/stable_weight
scales/{scale_id}/weight_delta
```

O formato exato deve alinhar com o broker e convenções da empresa.

### Critério de Conclusão

A fase fica concluída quando o sistema consegue publicar eventos de sessão e
receber eventos de balança num ambiente de teste, com logs suficientes para
validar a correlação temporal.

## Fase 6: Confirmação de Peça por Balança

A integração com balanças serve para confirmar se a peça foi realmente retirada
da zona correspondente.

A visão responde:

```text
o operador foi à zona da peça
```

A balança pode confirmar:

```text
o peso dessa zona diminuiu de forma compatível com a peça esperada
```

### Modelo de Configuração

Exemplo futuro:

```yaml
pieces:
  Porca:
    zone: "Porca"
    scale_id: "scale_porca"
    expected_delta_g: -5.0
    tolerance_g: 1.0
  Rodas:
    zone: "Rodas"
    scale_id: "scale_rodas"
    expected_delta_g: -12.0
    tolerance_g: 2.0
```

### Janela Temporal

Quando o sistema regista uma tarefa visual, pode procurar uma variação de peso
numa janela em torno dessa tarefa:

```text
task_start - margem_pre
task_end + margem_pos
```

Resultado possível:

```text
WEIGHT_CONFIRMED
WEIGHT_NOT_CONFIRMED
WEIGHT_AMBIGUOUS
VISUAL_ONLY
```

### Critério de Conclusão

A fase fica concluída quando um evento visual de recolha de peça consegue ser
classificado com base na evidência da balança.

## Questão Funcional: Ordem Rígida vs Checklist

Foi levantado um ponto importante: o trabalhador pode ir buscar todas as peças
primeiro e só depois montar.

Isto não significa necessariamente que o ciclo esteja errado. Significa que a
ordem observada pode ser diferente da ordem ideal/configurada.

Por isso, faz sentido separar duas perguntas:

```text
1. O ciclo respeitou a ordem esperada?
2. O ciclo teve todos os componentes necessários?
```

### Classificação Recomendada

Em vez de classificar tudo como apenas "em ordem" ou "fora de ordem", evoluir
para algo como:

```text
CYCLE_IN_ORDER
CYCLE_COMPLETE_OUT_OF_ORDER
CYCLE_INCOMPLETE
CYCLE_WITH_UNCONFIRMED_PICKUP
CYCLE_WITH_EXTRA_VISITS
CYCLE_ANOMALOUS
```

### Checklist de Ciclo

Uma checklist por ciclo poderia verificar:

- peça `Chassi Inferior` recolhida;
- peça `Porca` recolhida;
- peça `Rodas` recolhida no número aceitável;
- peça `Chassi Superior` recolhida;
- peça `Parafuso` recolhida;
- montagens realizadas;
- saída registada.

Com balanças, cada item pode ter dois níveis:

```text
visto pela câmara
confirmado por peso
```

### Critério de Conclusão

A fase fica concluída quando um ciclo completo fora da ordem esperada deixa de
ser automaticamente tratado como erro crítico e passa a ter classificação
própria.

## Ordem Recomendada

Ordem prática proposta:

1. Dockerizar o projeto atual.
2. Integrar o wizard.
3. Rever o modelo de eventos e checklist de ciclo.
4. Adicionar persistência em base de dados.
5. Criar dashboards Grafana.
6. Publicar/consumir MQTT.
7. Integrar balanças e confirmação de peça.

Esta ordem mantém o projeto controlável: primeiro estabiliza execução e
configuração, depois melhora o modelo de dados, e só então liga o sistema a
outros componentes industriais.

