# Resumo do Projeto para Cliente

## Visão Geral

O projeto consiste num sistema de apoio à monitorização de uma bancada de montagem industrial. O objetivo é observar o trabalho do operador durante a montagem de um produto, identificar as zonas da bancada utilizadas e transformar essa informação em dados úteis sobre produtividade, sequência de execução e tempos de trabalho.

O sistema deve funcionar como uma ferramenta de acompanhamento e análise do processo, ajudando a perceber onde o operador passa mais tempo, se a ordem de montagem está a ser cumprida e quais os pontos que podem estar a atrasar o ciclo.

## Objetivo Principal

Criar uma solução que permita medir automaticamente o processo de montagem numa bancada, sem exigir que o operador registe manualmente tempos, tarefas ou etapas.

O sistema deve permitir:

- acompanhar a execução de tarefas em tempo real;
- medir tempos por zona de trabalho;
- identificar ciclos completos de montagem;
- verificar se a sequência esperada foi respeitada;
- detetar interrupções ou permanências excessivas numa zona;
- apresentar métricas de produtividade de forma simples;
- guardar os resultados para análise posterior.

## Problema a Resolver

Atualmente, medir tempos de montagem, identificar gargalos e perceber desvios na sequência de trabalho pode depender de observação manual, cronómetros ou registos feitos depois da execução.

Esse processo é pouco prático, sujeito a erro humano e difícil de repetir de forma consistente.

Este projeto pretende automatizar essa recolha de informação, tornando a análise do processo mais objetiva, rápida e repetível.

## O Que o Sistema Deve Fazer

O sistema deve:

- observar uma bancada de montagem através de uma câmara;
- reconhecer as zonas de trabalho definidas na bancada;
- perceber quando o operador está a trabalhar numa dessas zonas;
- distinguir uma passagem rápida por uma zona de uma tarefa real;
- registar o início e fim de cada tarefa;
- calcular a duração das tarefas;
- agrupar tarefas em ciclos de montagem;
- identificar se o ciclo foi feito pela ordem esperada;
- destacar a zona que mais contribui para o tempo total do processo;
- separar tempo produtivo, tempo de transição e tempo de interrupção;
- apresentar indicadores em tempo real num painel visual;
- exportar os dados finais para análise;
- permitir configurar as zonas da bancada antes da utilização;
- funcionar sem obrigar o operador a interagir com o sistema durante a montagem.

## O Que o Sistema Não Deve Fazer

O sistema não deve:

- substituir o operador ou controlar fisicamente a bancada;
- tomar decisões automáticas sobre paragem de produção;
- avaliar a qualidade final do produto montado;
- identificar a identidade pessoal do operador;
- guardar dados biométricos do operador;
- depender de introdução manual de tempos durante a operação;
- exigir sensores físicos adicionais em cada zona da bancada;
- assumir que qualquer movimento perto de uma zona é uma tarefa válida;
- contar interrupções como tempo produtivo;
- aceitar uma configuração incompleta das zonas de trabalho;
- funcionar como sistema de segurança industrial;
- ser usado como ferramenta disciplinar individual sem enquadramento adequado;
- prometer precisão absoluta em ambientes com má iluminação, oclusões ou câmara mal posicionada.

## Utilizadores Esperados

Os principais utilizadores são:

- responsáveis de produção;
- equipas de melhoria contínua;
- professores ou avaliadores em contexto académico;
- técnicos que pretendam analisar tempos de montagem;
- operadores, apenas enquanto executam o processo monitorizado.

## Informação Que Deve Ser Apresentada

Durante ou após a sessão, o sistema deve apresentar:

- número de ciclos concluídos;
- tempo médio de ciclo;
- tempos por zona de trabalho;
- zona com maior tempo médio;
- percentagem de tempo produtivo;
- percentagem de tempo em transição;
- percentagem de tempo em interrupção;
- indicação de ciclos feitos na ordem correta;
- registo dos eventos relevantes da sessão;
- exportação dos resultados para ficheiro.

## Configuração Necessária Antes de Usar

Antes da utilização normal, deve ser possível:

- escolher ou confirmar a câmara;
- definir as zonas físicas da bancada;
- indicar quais as zonas que fazem parte do processo;
- indicar a ordem esperada das tarefas;
- definir qual a zona que termina um ciclo;
- ajustar tempos mínimos e máximos de reconhecimento;
- calibrar a imagem quando necessário.

## Condições de Funcionamento

Para funcionar corretamente, o sistema precisa de:

- uma câmara com visão clara da bancada;
- zonas de trabalho bem definidas e sem sobreposição confusa;
- iluminação estável;
- posicionamento fixo da câmara durante a sessão;
- operador visível enquanto executa as tarefas;
- configuração prévia das zonas antes de iniciar a monitorização;
- computador com capacidade suficiente para processar vídeo em tempo real.

## Resultados Esperados

No final de uma sessão, deve ser possível responder a perguntas como:

- quanto tempo durou a sessão;
- quantos ciclos foram concluídos;
- qual foi o tempo médio por ciclo;
- quais zonas foram mais demoradas;
- onde ocorreram interrupções;
- se a sequência de montagem foi respeitada;
- quanto tempo foi efetivamente produtivo;
- que dados podem ser analisados depois em folha de cálculo.

## Critérios de Sucesso

O projeto será considerado bem-sucedido se:

- permitir configurar uma bancada real;
- conseguir acompanhar uma sessão de montagem sem intervenção manual constante;
- gerar métricas compreensíveis para quem analisa o processo;
- distinguir tarefas reais de movimentos de passagem;
- identificar ciclos completos;
- exportar dados úteis para análise posterior;
- apresentar resultados em tempo real;
- for simples de demonstrar e explicar numa apresentação;
- deixar claro quais são as limitações do sistema.

## Fora do Âmbito Inicial

Não fazem parte do âmbito inicial:

- integração com sistemas ERP ou MES;
- base de dados centralizada;
- autenticação de utilizadores;
- histórico multiutilizador;
- análise automática da qualidade da montagem;
- reconhecimento de peças individuais;
- controlo de robots, atuadores ou equipamentos industriais;
- aplicação móvel;
- funcionamento em várias bancadas ao mesmo tempo;
- análise estatística avançada ou previsão de produtividade;
- instalação industrial certificada.

## Entregáveis Esperados

Os entregáveis principais são:

- sistema funcional de monitorização da bancada;
- painel visual com métricas da sessão;
- exportação dos resultados;
- configuração das zonas de trabalho;
- documentação de utilização;
- demonstração prática do funcionamento;
- explicação clara das limitações e próximos passos possíveis.

## Próximos Passos Possíveis

Depois da versão inicial, o projeto pode evoluir para:

- perfis diferentes por bancada;
- guia visual para indicar a próxima zona de trabalho;
- comparação entre sessões;
- relatórios automáticos;
- armazenamento histórico;
- integração com sistemas industriais;
- melhoria da calibração e robustez visual;
- dashboard mais completo para análise de produção.
