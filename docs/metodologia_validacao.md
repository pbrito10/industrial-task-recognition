# Metodologia de Validação do Sistema

## Objetivo

O objetivo desta validação é medir a confiabilidade do programa na avaliação dos
ciclos de montagem. A avaliação deve comparar o resultado automático produzido
pelo sistema com uma referência externa, definida manualmente durante ou após a
sessão de teste.

A validação não deve assumir que um ciclo assinalado pelo programa está
automaticamente incorreto. Se o operador executou o ciclo corretamente, mas o
programa assinalou uma sequência incompleta ou fora de ordem por ter perdido a
mão, esse caso deve contar como erro do programa na avaliação global. A causa
desse erro é analisada apenas numa fase posterior.

## Fase 1: Percentagem de Acerto Global

Na primeira fase, cada ciclo é avaliado de forma binária:

- `Correto`: o operador executou o ciclo corretamente.
- `Anomalia`: o operador executou o ciclo de forma incorreta.

Esta classificação é feita manualmente, com base na observação direta, vídeo de
referência ou registo externo. Ela representa o ground truth da avaliação.

Depois, compara-se esta classificação manual com o resultado automático produzido
pelo programa:

- `Em ordem`: a sequência registada respeitou a ordem esperada.
- `A rever`: o sistema detetou sequência incompleta ou fora de ordem.

### Matriz de Confusão

| Real / Programa | Programa: Em ordem | Programa: A rever |
|---|---:|---:|
| Real: Correto | Verdadeiro Correto | Falso Positivo |
| Real: Anomalia | Falso Negativo | Verdadeiro Anomalia |

### Interpretação

- `Verdadeiro Correto`: o ciclo foi realmente correto e o programa indicou `Em ordem`.
- `Verdadeiro Anomalia`: o ciclo foi realmente anómalo e o programa indicou `A rever`.
- `Falso Positivo`: o ciclo foi realmente correto, mas o programa indicou `A rever`.
- `Falso Negativo`: o ciclo foi realmente anómalo, mas o programa indicou `Em ordem`.

### Métrica Principal

```text
Percentagem de acerto = ((Verdadeiros Corretos + Verdadeiras Anomalias) / Total de ciclos avaliados) * 100
```

Esta métrica responde à pergunta principal:

```text
O programa é confiável para distinguir ciclos corretos de ciclos anómalos?
```

## Fase 2: Diagnóstico dos Erros

Na segunda fase, analisam-se apenas os ciclos em que o programa errou, ou seja,
os falsos positivos e falsos negativos da Fase 1.

O objetivo desta fase não é recalcular a percentagem de acerto, mas explicar por
que razão o programa falhou.

### Categorias de Causa

| Tipo de erro | Possíveis causas |
|---|---|
| Falso positivo por falha de deteção | O operador fez corretamente, mas o sistema perdeu a mão, falhou a deteção ou registou um gap relevante. |
| Falso positivo por ROI/câmara | O operador fez corretamente, mas a mão ficou na fronteira da ROI, fora do enquadramento ideal ou a câmara estava mal posicionada. |
| Falso positivo por timeout indevido | O operador fez corretamente, mas o sistema interpretou uma permanência ou falha momentânea como timeout. |
| Falso negativo por anomalia não detetada | O operador saltou uma zona, trocou a ordem ou interrompeu o ciclo, mas o programa indicou `Em ordem`. |
| Falso negativo por tolerância excessiva | O ciclo foi anómalo, mas a lógica de validação aceitou a sequência ou duração como válida. |

Os ficheiros da pasta da sessão (`debug_*.csv`, Excel, vídeo anotado e frames em
`frames/gaps/`) devem ser usados nesta análise para justificar a causa provável
de cada erro.

## Plano de Aplicação

### 1. Preparação

Antes de iniciar os testes:

- calibrar ou confirmar a posição fixa da câmara;
- definir as ROIs finais da bancada;
- confirmar a ordem esperada em `cycle_zone_order`;
- testar a câmara com a opção `1`;
- correr um ensaio curto para confirmar se CSV, Excel, vídeo, frames de gap e dashboard são gerados corretamente.

### 2. Sessão Piloto

Executar uma sessão curta de aproximadamente 15 a 30 minutos.

Objetivo:

- verificar se as ROIs estão bem posicionadas;
- confirmar se a mão é detetada de forma estável;
- identificar problemas óbvios de iluminação, oclusão ou enquadramento;
- ajustar parâmetros antes da validação final.

Esta sessão não deve ser usada como resultado final, a menos que as condições
tenham sido mantidas iguais às da validação principal.

### 3. Sessão de Validação

Executar uma ou mais sessões com ciclos planeados.

Recomenda-se incluir:

- ciclos corretos;
- ciclos com zona saltada;
- ciclos com ordem trocada;
- ciclos com pausa prolongada;
- ciclos com saída/interrupção;
- ciclos em velocidade normal;
- ciclos executados mais rapidamente;
- ciclos com pequenas variações naturais do operador.

Durante a sessão, deve ser mantida uma tabela manual com:

| Ciclo | Classificação manual | Observações |
|---:|---|---|
| 1 | Correto | Execução normal |
| 2 | Anomalia | Saltou Rodas |
| 3 | Correto | Programa perdeu a mão na Montagem |
| 4 | Anomalia | Ordem trocada |

Nota: a coluna `Observações` não altera a classificação manual. Ela serve para
ajudar a explicar erros na Fase 2.

### 4. Recolha dos Outputs

No final de cada sessão, guardar:

- pasta completa em `output/sessions/<data_hora>/`;
- `debug_*.csv`;
- `sessao_*.xlsx`;
- `debug_*_anomalias.xlsx`, gerado pela opção `5`;
- vídeo anotado em `video/`;
- imagens `frames/gaps/gap_ciclo_*.jpg`;
- tabela manual de ground truth.

### 5. Cálculo da Percentagem de Acerto

Para cada ciclo, comparar:

- classificação manual (`Correto` ou `Anomalia`);
- resultado do sistema (`Em ordem` ou `A rever`).

Depois, preencher a matriz de confusão e calcular:

```text
Percentagem de acerto = (acertos / total de ciclos avaliados) * 100
```

Opcionalmente, calcular também:

```text
Taxa de falsos positivos = falsos positivos / ciclos realmente corretos
Taxa de falsos negativos = falsos negativos / ciclos realmente anómalos
```

### 6. Diagnóstico dos Erros

Para cada falso positivo e falso negativo:

- consultar o CSV de debug;
- verificar se houve `DETECTION_GAP`;
- consultar o vídeo anotado e as imagens `frames/gaps/gap_ciclo_*.jpg`;
- verificar a sequência real registada;
- verificar timeouts;
- comparar com as observações manuais.

O resultado desta fase deve indicar quantos erros foram causados por:

- falha de deteção da mão;
- problemas de ROI/câmara;
- timeout indevido;
- anomalia real não detetada;
- lógica de validação demasiado permissiva.

## Formulação para o Relatório

Uma formulação possível:

> A validação do sistema foi dividida em duas fases. Na primeira, foi calculada a
> percentagem de acerto global do programa, comparando a classificação automática
> de cada ciclo com uma anotação manual independente. Cada ciclo foi classificado
> manualmente como correto ou anómalo, e o resultado foi comparado com a saída do
> sistema através de uma matriz de confusão.

> Na segunda fase, os erros identificados na matriz de confusão foram analisados
> individualmente, com o objetivo de perceber a sua origem. Foram usados os
> ficheiros de debug, as imagens dos gaps de deteção e as observações manuais
> para distinguir falhas causadas por perda de deteção, problemas de ROI/câmara,
> timeouts indevidos ou limitações na lógica de validação do ciclo.

> Esta abordagem permitiu avaliar não só a confiabilidade global do programa,
> mas também as principais causas dos seus erros.
