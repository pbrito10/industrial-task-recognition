# Coleção de ROIs (first-class collection — OC).
#
# Responsabilidade: encapsular a lista de zonas e fornecer
# operações sobre ela, em vez de passar listas cruas pelo sistema.
#
# Lógica:
#   - Internamente mantém uma lista de RegionOfInterest
#   - find_zone_for_point(point: Point) → RegionOfInterest | None:
#       itera as zonas e devolve a primeira cujo contains(point)
#       seja True — ou seja, a zona onde a mão está.
#       Usa Point em vez de dois ints (x, y) separados —
#       ver shared/point.py e roi/region_of_interest.py.
#   - is_empty() → bool
#   - add(roi: RegionOfInterest): adiciona uma zona
#   - remove(name: str): remove por nome
#   - all() → list[RegionOfInterest]: devolve todas as ROIs
#     (usado pelo RoiDrawer para as desenhar no frame)
#
# Ao encapsular a lista, evitamos que código externo faça loops
# sobre ela diretamente — a lógica de "qual zona contém este ponto"
# fica num único sítio (Single Responsibility).
