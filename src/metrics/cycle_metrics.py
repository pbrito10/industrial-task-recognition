# TODO: implementar
#
# Agrega e mantém as métricas dos ciclos completos.
#
# Responsabilidade: para os ciclos completos observados, guardar
# os tempos totais e calcular estatísticas sobre eles.
#
# Lógica:
#   - Mantém internamente uma lista de timedelta (tempos totais de ciclo).
#     Usa timedelta em vez de float (segundos) — ver metrics/task_metrics.py
#     para a justificação detalhada.
#   - add(duration: timedelta): regista um novo tempo de ciclo
#   - minimum() → timedelta
#   - average() → timedelta
#   - maximum() → timedelta
#   - std_deviation() → timedelta:
#       desvio padrão dos tempos de ciclo — métrica importante para
#       comparar layouts. Um layout com média igual mas desvio menor
#       é preferível porque o processo é mais previsível e estável.
#       Devolve timedelta(0) se count() < 2.
#   - count() → int: número de ciclos completos registados
#
# Separado de TaskMetrics por Single Responsibility:
#   As métricas de ciclo têm semântica diferente — um ciclo engloba
#   múltiplas tarefas e pode incluir tempos de transição (mão em
#   trânsito entre zonas). Misturar as duas no mesmo objeto tornaria
#   a classe responsável por demasiadas coisas.
