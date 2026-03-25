# Coleção de keypoints de uma mão (first-class collection — OC).
#
# Responsabilidade: encapsular a lista de 21 keypoints e fornecer
# operações sobre ela, em vez de expor a lista diretamente.
#
# Porquê não usar list[Keypoint] diretamente?
#   OC diz que coleções devem ser encapsuladas. Uma lista crua obriga
#   o código externo a iterar e indexar diretamente — a lógica de
#   "qual é o pulso?" ou "qual é o centroide?" fica espalhada por
#   todo o sistema. KeypointCollection centraliza essas operações.
#
# Lógica:
#   - Internamente mantém uma lista de exatamente 21 Keypoint
#   - No __init__, valida que recebeu 21 pontos — se não, lança erro
#     (o modelo deve sempre devolver 21 ou nenhum)
#
# Métodos:
#   - wrist() → Keypoint:
#       devolve keypoints[0] — o pulso, ponto de referência mais estável
#       para determinar a zona quando a mão está sobre um componente
#   - centroid() → Point:
#       média das posições dos 21 keypoints — centro geométrico da mão
#       mais robusto que o pulso quando a mão está em posições extremas
#   - fingertips() → list[Keypoint]:
#       devolve os 5 keypoints de ponta de dedo (índices 4,8,12,16,20)
#       útil para análise de gesto futura
#   - by_index(index: int) → Keypoint:
#       acesso por índice com validação (0–20)
