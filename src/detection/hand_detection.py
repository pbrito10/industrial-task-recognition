# Value object que representa uma mão detetada num frame.
#
# Responsabilidade: agrupar todos os dados de uma deteção de mão
# de forma imutável e com tipos explícitos.
#
# Campos:
#   keypoints    : KeypointCollection — os 21 pontos de articulação
#                                       encapsulados numa first-class
#                                       collection (ver detection/keypoint_collection.py)
#                                       em vez de list[Keypoint] crua
#   bounding_box : BoundingBox        — retângulo envolvente da mão
#   confidence   : Confidence         — confiança geral da deteção
#                                       (ver shared/confidence.py)
#   hand_side    : HandSide           — qual mão foi detetada
#                                       (ver shared/hand_side.py)
#
# Métodos de conveniência (delegam para KeypointCollection):
#   - centroid() → Point:
#       centro geométrico dos 21 keypoints — delega em
#       keypoints.centroid() — atalho para não aceder à coleção
#       diretamente de fora
#   - wrist() → Keypoint:
#       atalho para keypoints.wrist() — ponto de referência comum
#       para determinar a zona quando a mão está sobre um componente
#
# Imutável após criação (@dataclass frozen=True).
