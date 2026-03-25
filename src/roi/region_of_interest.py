# Value object que representa uma zona de trabalho (ROI) na bancada.
#
# Responsabilidade: encapsular os dados que definem uma zona retangular
# com tipos explícitos e fornecer operações sobre ela.
#
# Campos:
#   name         : str   — nome da zona definido pelo utilizador (ex: "Zona A").
#                          Mantido como str porque é um label livre definido
#                          pelo utilizador, não um conjunto fixo de valores.
#   top_left     : Point — canto superior esquerdo do retângulo
#                          (usa Point em vez de dois ints x1, y1 —
#                          ver shared/point.py)
#   bottom_right : Point — canto inferior direito do retângulo
#                          (usa Point em vez de dois ints x2, y2 —
#                          ver shared/point.py)
#
# Métodos úteis:
#   - contains(point: Point) → bool:
#       diz se um ponto (posição da mão) está dentro da zona.
#       Lógica: top_left.x <= point.x <= bottom_right.x
#               AND top_left.y <= point.y <= bottom_right.y
#       Usado pelo ZoneClassifier frame a frame.
#   - to_dict() → dict:
#       serialização para guardar em JSON.
#       Formato: {"name": "Zona A", "x1": 50, "y1": 80, "x2": 200, "y2": 250}
#       (guarda as coordenadas como ints simples para o JSON ser legível)
#   - from_dict(data: dict) → RegionOfInterest:
#       deserialização ao carregar o JSON — reconstrói os Point internamente
#
# Imutável após criação (@dataclass frozen=True).
# A imutabilidade garante que as zonas não mudam acidentalmente
# durante uma sessão de análise.
