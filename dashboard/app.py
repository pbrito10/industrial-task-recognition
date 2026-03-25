# Dashboard Streamlit — interface de visualização em tempo real.
#
# Responsabilidade: apresentar as métricas da sessão de forma visual
# e atualizada, lendo os dados escritos pelo DashboardWriter.
#
# Corre como processo separado: `streamlit run dashboard/app.py`
#
# Conteúdo do dashboard:
#
#   Secção 1 — Resumo da sessão (topo):
#     - Ciclos completos | Tempo médio de ciclo | Tarefa atual
#
#   Secção 2 — Decomposição do tempo (3 métricas em destaque):
#     - % Tempo produtivo    (tarefas was_forced=False)
#     - % Tempo de transição (entre zonas)
#     - % Tempo de interrupção (timeouts / pausas)
#     As três somam 100% — permitem ver de imediato onde o tempo é perdido.
#
#   Secção 3 — Métricas por zona (tabela):
#     | Zona | Mín | Médio | Máx | Desvio Padrão | Ocorrências |
#     A zona gargalo (maior tempo médio) é destacada.
#
#   Secção 4 — Gráficos:
#     - Barras: tempo médio por zona
#     - Barras empilhadas: decomposição % produtivo / transição / interrupção
#     - Linha: evolução do tempo de ciclo ao longo das repetições
#       (permite ver fadiga ou aprendizagem ao longo da sessão)
#
#   Secção 5 — Log de eventos recentes:
#     Últimas N tarefas concluídas com zona, duração, timestamp e flag
#     de interrupção — útil para debug em tempo real
#
# Lógica de atualização:
#   - Lê dashboard/data/metrics.json a cada N segundos
#     (N configurável em settings.yaml via dashboard.refresh_seconds)
#   - Se o ficheiro não existir ou estiver vazio, mostra mensagem
#     "A aguardar dados..." em vez de crashar
#   - Mostra timestamp da última atualização no rodapé
