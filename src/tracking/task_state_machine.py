# TODO: implementar
#
# Máquina de estados que decide qual a tarefa em curso.
#
# Responsabilidade: receber, frame a frame, a zona onde as mãos estão
# e determinar quando uma tarefa começa, continua ou termina.
#
# Comportamento depende do tipo de zona (lido de settings.yaml):
#
# --- Zonas normais (one_hand) ---
#
#   IDLE → DWELLING:
#     quando qualquer mão entra numa zona; regista a zona e inicia
#     o dwell timer
#   DWELLING → TASK_IN_PROGRESS:
#     quando a mão permanece na zona durante o dwell time completo;
#     regista o timestamp de início real da tarefa
#   DWELLING → IDLE:
#     quando a mão sai antes do dwell time; descarta sem emitir evento
#   TASK_IN_PROGRESS → IDLE (normal):
#     quando a mão sai da zona; emite TaskEvent(was_forced=False)
#   TASK_IN_PROGRESS → IDLE (timeout):
#     quando a tarefa excede task_timeout_seconds sem a mão sair;
#     emite TaskEvent(was_forced=True) — indica interrupção ou falha
#     de deteção; a duração não é usada nas métricas de tarefa mas
#     sim nas métricas de interrupção
#
# --- Zonas two_hands (ex: Zona Assembly) ---
#
#   IDLE → WAITING_SECOND_HAND:
#     quando 1 mão entra na zona; aguarda a segunda — não inicia timer
#   WAITING_SECOND_HAND → DWELLING_TWO_HANDS:
#     quando a 2ª mão entra na mesma zona; inicia o dwell timer agora
#   WAITING_SECOND_HAND → IDLE:
#     quando a mão sai antes da segunda chegar; descarta
#   DWELLING_TWO_HANDS → TASK_IN_PROGRESS:
#     quando as duas mãos permanecem na zona durante o dwell time
#   DWELLING_TWO_HANDS → IDLE:
#     quando qualquer mão sai antes do dwell time; timer reseta
#   TASK_IN_PROGRESS → IDLE (normal):
#     quando qualquer mão sai; emite TaskEvent(was_forced=False)
#   TASK_IN_PROGRESS → IDLE (timeout):
#     emite TaskEvent(was_forced=True)
#
# Regra "uma tarefa de cada vez":
#   Enquanto estado != IDLE, entradas noutras zonas são ignoradas.
#   Exceção: em WAITING_SECOND_HAND, a outra mão pode sair livremente
#   para outras zonas — só a mão que está na two_hands zone é reservada.
#
# Configuração (settings.yaml):
#   tracking.dwell_time_seconds    — tempo mínimo para confirmar tarefa
#   tracking.task_timeout_seconds  — tempo máximo antes de forçar fecho
#   tracking.two_hands_zones       — lista de zonas que exigem duas mãos
