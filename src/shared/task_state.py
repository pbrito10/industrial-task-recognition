# Enum que representa o estado atual da máquina de estados de tarefas.
#
# Responsabilidade: substituir strings de estado por um tipo seguro,
# tornando as transições explícitas e validadas pelo Python.
#
# Estados para zonas normais (one_hand):
#
#   IDLE
#     Nenhuma mão está em nenhuma zona ativa.
#
#   DWELLING
#     A mão entrou numa zona mas ainda não cumpriu o dwell time.
#     Se sair antes do dwell → volta a IDLE sem emitir TaskEvent.
#
#   TASK_IN_PROGRESS
#     Dwell time cumprido — tarefa confirmada como ativa.
#     Quando a mão sai → emite TaskEvent(was_forced=False) e volta a IDLE.
#     Se o task_timeout estourar → emite TaskEvent(was_forced=True) e volta a IDLE.
#
# Estados adicionais para zonas two_hands (ex: Zona Assembly):
#
#   WAITING_SECOND_HAND
#     Uma mão entrou na zona mas a segunda ainda não chegou.
#     O timer não arranca — a mão parada sozinha não conta.
#     Se a mão sair antes da segunda chegar → volta a IDLE.
#
#   DWELLING_TWO_HANDS
#     As duas mãos estão na zona — o dwell timer arranca agora.
#     Se qualquer mão sair antes do dwell → volta a IDLE, timer reseta.
#
# Fluxo normal (zona one_hand):
#   IDLE → DWELLING → TASK_IN_PROGRESS → IDLE  [TaskEvent was_forced=False]
#
# Fluxo com timeout (zona one_hand):
#   IDLE → DWELLING → TASK_IN_PROGRESS → IDLE  [TaskEvent was_forced=True]
#
# Fluxo normal (zona two_hands):
#   IDLE → WAITING_SECOND_HAND → DWELLING_TWO_HANDS → TASK_IN_PROGRESS
#        → IDLE  [TaskEvent was_forced=False]
#
# Nota: não existe estado TIMED_OUT separado — o timeout é uma transição
# forçada de TASK_IN_PROGRESS para IDLE, distinguida pelo was_forced no
# TaskEvent. Manter um estado extra só para timeout complicaria a máquina
# sem benefício real.
