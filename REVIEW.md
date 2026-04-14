# Revisão técnica do projeto

Data da revisão: 2026-04-14

## Visão geral

O projeto está bem modularizado, com separação clara por domínio:
- `src/detection` (deteção de mãos)
- `src/tracking` (máquina de estados e ciclos)
- `src/metrics` (cálculo de métricas)
- `src/output` (dashboard + Excel)
- processos de orquestração em módulos de topo (`main.py`, `capture_process.py`, `detection_process.py`, `monitor_process.py`).

Isto facilita manutenção e evolução incremental.

## Pontos fortes

1. **Boa arquitetura de pipeline em processos isolados**
   - Captura, deteção e monitorização ficam desacoplados por `Queue`, reduzindo acoplamento.
   - Uso consistente de `stop_event` para encerramento coordenado.

2. **Boas decisões de latência em tempo real**
   - Em `capture_process.py`, descarte de frame antigo quando a fila está cheia evita backlog e mantém visualização atual.
   - Em `detection_process.py`, descarte quando consumidor está lento evita bloqueio global.

3. **Domínio modelado com clareza**
   - Máquina de estados separada entre zonas de uma mão e duas mãos.
   - `CycleTracker` e métricas desacoplados, o que torna regras de negócio explícitas.

4. **Saída robusta para dashboard**
   - Escrita atómica no `DashboardWriter` evita JSON parcial durante leitura do Streamlit.

## Problemas e riscos encontrados

### 1) Caminho de dados do dashboard estava hardcoded

**Problema:** `dashboard/app.py` carregava `metrics.json` por caminho fixo, ignorando `dashboard.data_path` em `config/settings.yaml`.

**Risco:** qualquer alteração de caminho na configuração não teria efeito no dashboard, causando inconsistência entre escrita e leitura.

**Correção aplicada:** o dashboard agora lê o caminho via configuração e passa esse `Path` para `_load_data`.

## Recomendações (sem alteração de código nesta revisão)

1. **Adicionar suíte mínima de testes unitários**
   - Começar por `src/tracking/cycle_tracker.py` (`_matches_order`) e `TaskStateMachine`.
   - Esses módulos concentram regras de negócio críticas e são bons candidatos a testes puros.

2. **Padronizar dependências em `requirements.txt`**
   - Há pacotes sem versão fixa (`pandas`, `openpyxl`, `streamlit`), o que pode causar variação de comportamento entre ambientes.

3. **Adicionar README principal**
   - Atualmente não há `README.md` na raiz.
   - Recomenda-se documentar:
     - pré-requisitos
     - setup
     - fluxo de execução (`main.py`)
     - troubleshooting (DISPLAY/SSH, permissões de câmara).

4. **Criar testes de integração leves para serialização de outputs**
   - Validar schema do JSON do dashboard e estrutura das folhas Excel.

## Conclusão

A base do projeto é sólida para um sistema de visão computacional em tempo real: boa separação por camadas, responsabilidades claras e preocupação explícita com latência. A principal correção desta revisão foi alinhar o dashboard com a configuração oficial de caminho dos dados.
