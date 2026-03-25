# Calcula as métricas agregadas a partir dos eventos registados.
#
# Responsabilidade: receber TaskEvents e produzir as métricas completas
# para dashboard e Excel.
#
# Recebe o timestamp de início da sessão no __init__ para calcular
# o tempo total da sessão — necessário para as percentagens de tempo.
#
# Métricas calculadas:
#
#   Por tarefa (cada zona) — só TaskEvents com was_forced=False:
#     - Tempo mínimo, médio, máximo e desvio padrão
#     - Número de ocorrências
#
#   Por ciclo:
#     - Tempo total mínimo, médio, máximo e desvio padrão
#     - Número total de ciclos completos
#
#   Decomposição do tempo da sessão (as três somam 100%):
#     - % tempo produtivo:
#         tempo total com was_forced=False / tempo total sessão × 100
#         tempo efetivamente gasto a realizar tarefas
#     - % tempo de transição:
#         tempo entre tarefas (mão em movimento, sem zona ativa) /
#         tempo total sessão × 100
#         calculado como: tempo total - tempo produtivo - tempo interrupção
#     - % tempo de interrupção:
#         tempo total de TaskEvents com was_forced=True /
#         tempo total sessão × 100
#         engloba pausas do operador e falhas de deteção
#
#   Gargalo (bottleneck):
#     zona com maior tempo médio entre as tarefas was_forced=False —
#     a etapa que mais atrasa o ciclo; destacada no dashboard e Excel
#
# Lógica:
#   - Acumula eventos à medida que chegam (online, não espera pelo fim)
#   - Separa automaticamente was_forced=True dos cálculos de tarefa
#   - snapshot() → dict com todas as métricas atuais:
#       chamado pelo DashboardWriter a cada refresh do Streamlit
#       e pelo ExcelExporter no fim da sessão
