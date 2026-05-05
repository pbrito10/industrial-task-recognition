# Brief Funcional do Projeto

## Visão Geral

O sistema acompanha uma bancada de montagem industrial através de uma câmara.
Identifica as zonas usadas pelo operador, mede tarefas e ciclos, apresenta
métricas em tempo real e guarda os resultados para análise posterior.

## Objetivo

Automatizar a recolha de tempos e sequência de montagem, evitando cronómetros,
observação manual e registos feitos depois da execução.

## O Sistema Deve

- reconhecer zonas configuradas da bancada;
- distinguir passagem por uma zona de tarefa real;
- medir duração por tarefa e por ciclo;
- validar a sequência esperada do ciclo;
- separar tempo produtivo, transição e interrupção;
- destacar a zona gargalo;
- gerar CSV, Excel, dashboard e vídeo anotado;
- funcionar sem interação manual durante a montagem.

## O Sistema Não Deve

- controlar fisicamente a bancada;
- avaliar qualidade final do produto;
- identificar pessoalmente o operador;
- guardar dados biométricos;
- substituir validação humana em contexto crítico;
- funcionar como sistema de segurança industrial.

## Condições de Funcionamento

- câmara fixa com boa visibilidade da bancada;
- iluminação estável;
- ROIs bem desenhadas e sem ambiguidades graves;
- operador visível durante as tarefas;
- configuração validada antes da sessão.

## Entregáveis

- pipeline funcional de monitorização;
- dashboard em tempo real;
- Excel de sessão;
- CSV de debug;
- vídeo anotado;
- metodologia de validação;
- documentação técnica e funcional.

