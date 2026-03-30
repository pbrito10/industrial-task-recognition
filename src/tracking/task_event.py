# TODO: implementar
#
# Value object que representa uma tarefa concluída (ou interrompida).
#
# Responsabilidade: transportar os dados de uma tarefa terminada
# entre a TaskStateMachine e os consumidores (métricas, dashboard, Excel).
#
# Campos:
#   zone_name    : str      — nome da zona onde a tarefa ocorreu (ex: "Zona A").
#                             Mantido como str porque corresponde ao name de
#                             um RegionOfInterest definido pelo utilizador.
#   start_time   : datetime — momento de início da tarefa.
#                             Usa datetime em vez de float (epoch) porque
#                             datetime já é um wrapper adequado da stdlib.
#   end_time     : datetime — momento de fim da tarefa.
#   duration     : timedelta — duração calculada (end_time - start_time).
#                              Usa timedelta em vez de float (segundos) porque
#                              timedelta comunica explicitamente que é uma
#                              duração, não um timestamp nem outro float.
#   cycle_number : int      — número do ciclo a que pertence esta tarefa.
#                             Mantido como int porque é apenas um contador
#                             ordinal sem comportamento a encapsular.
#   was_forced   : bool     — indica se a tarefa foi fechada por timeout
#                             (True) ou terminou normalmente com a mão a
#                             sair da zona (False).
#
#                             Quando True, a duração está provavelmente
#                             inflacionada (inclui tempo de pausa/interrupção)
#                             e não deve entrar nas métricas de tempo de tarefa.
#                             Em vez disso, entra nas métricas de interrupção
#                             do MetricsCalculator.
#
#                             No CSV, esta flag permite distinguir tarefas
#                             reais de interrupções durante a análise.
#
# Imutável após criação (@dataclass frozen=True).
