# TODO: implementar
#
# Classifica em que zona estão as mãos detetadas.
#
# Responsabilidade: receber as HandDetections de um frame e determinar
# em que ROI cada mão se encontra, consultando a RoiCollection.
#
# Lógica:
#   - Para cada HandDetection, obtém o ponto de referência:
#       → usa bounding_box.center() que devolve um Point
#         (ver detection/bounding_box.py e shared/point.py)
#       → alternativa configurável: hand_detection.wrist() se a bbox
#         não estiver disponível ou tiver baixa confiança
#   - Consulta roi_collection.find_zone_for_point(point: Point)
#   - Devolve uma lista de (HandDetection, RegionOfInterest | None)
#
# Se a mão não estiver em nenhuma zona, devolve None para essa mão
# (mão em trânsito entre zonas).
#
# Com duas mãos: pode haver situações em que ambas estão na mesma
# zona em simultâneo — isso é tratado pela TaskStateMachine, não aqui.
# Este classificador apenas reporta o que vê, sem interpretar.
