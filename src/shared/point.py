# Value object que representa um ponto em coordenadas de píxeis.
#
# Responsabilidade: encapsular um par de coordenadas (x, y) que
# representa uma posição num frame de vídeo.
#
# Porquê não usar dois ints soltos?
#   Um ponto tem identidade própria — x e y não fazem sentido
#   separados. Ao encapsulá-los num objeto, evitamos passar pares
#   de ints avulsos pelo sistema e tornamos o código mais legível:
#   em vez de (342, 218) passa a ser Point(x=342, y=218).
#
# Usado em:
#   - Keypoint: posição de cada articulação da mão
#   - BoundingBox: cantos do retângulo (top_left e bottom_right)
#   - RegionOfInterest: cantos da zona (top_left e bottom_right)
#   - ZoneEvent: posição da mão no momento do evento
#
# Métodos úteis:
#   - distance_to(other: Point) → float:
#       distância euclidiana entre dois pontos (útil para filtros de ruído)
#
# Imutável após criação (@dataclass frozen=True).
