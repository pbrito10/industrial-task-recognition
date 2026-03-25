# Value object que representa um keypoint (articulação) da mão.
#
# Responsabilidade: encapsular a posição e confiança de um ponto
# de articulação detetado pelo modelo YOLOv26.
#
# Campos:
#   position   : Point      — posição em píxeis no frame (usa Point em vez
#                             de dois ints soltos x e y — ver shared/point.py)
#   confidence : Confidence — confiança deste keypoint específico
#                             (usa Confidence em vez de float — ver shared/confidence.py)
#   index      : int        — índice do ponto (0 a 20); int mantido porque é
#                             apenas um identificador ordinal sem comportamento
#
# Convenção dos 21 pontos (MediaPipe / YOLO Hand Pose):
#   0        : Pulso
#   1–4      : Polegar (base → ponta)
#   5–8      : Indicador
#   9–12     : Médio
#   13–16    : Anelar
#   17–20    : Mindinho
#
# Imutável após criação (@dataclass frozen=True).
