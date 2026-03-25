# Value object que representa o resultado do processamento de um frame.
#
# Responsabilidade: encapsular tudo o que o FrameProcessor produz
# a partir de um único frame, em vez de devolver uma tupla anónima.
#
# Porquê não devolver uma tupla?
#   frame, zone_events, task_event = processor.process(frame)
#   Uma tupla não comunica o significado de cada posição — o chamador
#   depende da ordem e pode fazer unpacking errado silenciosamente.
#   FrameResult torna cada campo explícito e nomeado.
#
# Campos:
#   annotated_frame : np.ndarray         — frame original com anotações
#                                          desenhadas (ROIs, keypoints,
#                                          bounding boxes, zona ativa)
#   zone_events     : list[ZoneEvent]    — eventos ENTER/EXIT gerados
#                                          neste frame (pode ser vazia)
#   task_event      : TaskEvent | None   — tarefa concluída neste frame,
#                                          ou None se nenhuma terminou
#
# Na maioria dos frames zone_events estará vazia e task_event será None
# — só há eventos quando ocorre uma transição de zona ou conclusão
# de tarefa. O chamador (run_program.py) verifica e age em conformidade.
#
# Imutável após criação (@dataclass frozen=True).
