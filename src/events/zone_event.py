# Value object que representa um evento de entrada ou saída de uma zona.
#
# Responsabilidade: transportar todos os dados de um único evento
# de forma imutável — é o "átomo" de informação do sistema.
#
# Um evento é gerado pelo FrameProcessor sempre que uma mão:
#   - Entra numa zona (ENTER) — após o dwell time ser cumprido
#   - Sai de uma zona (EXIT)  — quando a mão deixa de estar na zona
#   - Timeout               — quando a tarefa é forçada a fechar
#
# Campos:
#   timestamp     : datetime   — data e hora exata do evento
#   relative_time : timedelta  — tempo desde o início da sessão
#                                (renomeado de t_rel_s — OC: não abreviar)
#   event_type    : EventType  — ENTER ou EXIT (ver shared/event_type.py)
#   zone          : str        — nome da zona (label definido pelo utilizador)
#   hand          : HandSide   — qual mão gerou o evento (ver shared/hand_side.py)
#   position      : Point      — posição da mão no frame (ver shared/point.py)
#   confidence    : Confidence — confiança da deteção (ver shared/confidence.py)
#   frame_idx     : int        — índice do frame; int mantido porque é
#                                apenas um contador ordinal sem comportamento
#   was_forced    : bool       — True se o EXIT foi gerado por timeout e não
#                                pela mão a sair fisicamente da zona.
#                                Para eventos ENTER é sempre False.
#
# Imutável após criação (@dataclass frozen=True).
