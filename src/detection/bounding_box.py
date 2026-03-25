# Value object que representa a bounding box de uma mão detetada.
#
# Responsabilidade: encapsular o retângulo envolvente de uma deteção
# e fornecer métodos de conveniência sobre ele.
#
# Campos:
#   top_left     : Point — canto superior esquerdo (usa Point em vez de
#                          dois ints x1, y1 — ver shared/point.py)
#   bottom_right : Point — canto inferior direito (usa Point em vez de
#                          dois ints x2, y2 — ver shared/point.py)
#
# Porquê dois Point em vez de quatro ints?
#   x1, y1, x2, y2 são quatro ints soltos sem relação explícita entre si.
#   Ao agrupar em top_left e bottom_right comunicamos imediatamente que
#   temos dois pontos que definem um retângulo, não quatro números avulsos.
#
# Métodos úteis:
#   - center() → Point:
#       ponto central da bounding box — usado pelo ZoneClassifier para
#       determinar em que zona está a mão
#   - area() → int:
#       área em píxeis quadrados (largura × altura)
#   - contains(point: Point) → bool:
#       verifica se um ponto está dentro da bounding box
#
# Imutável após criação (@dataclass frozen=True).
