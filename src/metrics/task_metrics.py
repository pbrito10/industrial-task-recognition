# Agrega e mantém as métricas de uma zona/tarefa específica.
#
# Responsabilidade: para uma zona (ex: "Zona A"), guardar todos os
# tempos registados e calcular estatísticas sobre eles.
#
# Lógica:
#   - Mantém internamente uma lista de timedelta (durações observadas).
#     Usa timedelta em vez de float (segundos) para ser consistente com
#     o TaskEvent — ver tracking/task_event.py.
#   - add(duration: timedelta): regista uma nova duração
#   - minimum() → timedelta:   menor tempo observado
#   - average() → timedelta:   média de todos os tempos
#   - maximum() → timedelta:   maior tempo observado
#   - std_deviation() → timedelta:
#       desvio padrão das durações — mede consistência do operador
#       nesta tarefa. Um desvio alto indica instabilidade na execução,
#       um desvio baixo indica tarefa bem automatizada.
#       Devolve timedelta(0) se count() < 2 (desvio indefinido).
#   - count() → int: número de vezes que a tarefa foi realizada
#
# O MetricsCalculator tem uma instância de TaskMetrics por cada zona
# definida na RoiCollection.
#
# Nota sobre timedelta vs float:
#   Ao usar timedelta, o código que consome estas métricas recebe
#   sempre uma duração tipada. Se precisar de segundos para exibir
#   no dashboard, converte com total_seconds() no sítio certo —
#   não espalhado por todo o código.
