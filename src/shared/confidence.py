# Value object que representa a confiança de uma deteção.
#
# Responsabilidade: encapsular um valor de confiança e garantir
# que está sempre dentro do intervalo válido (0.0 a 1.0).
#
# Porquê não usar float diretamente?
#   Um float solto como 0.87 não comunica nada — podia ser uma
#   percentagem, um peso, uma probabilidade. Ao criar Confidence,
#   tornamos a intenção explícita e garantimos que o valor é válido
#   logo na criação, em vez de validar espalhado pelo código.
#
# Usado em:
#   - Keypoint: confiança de cada ponto de articulação
#   - HandDetection: confiança geral da deteção da mão
#   - ZoneEvent: confiança da deteção no momento do evento
#
# Lógica do __init__:
#   - Recebe value: float
#   - Se value < 0.0 ou value > 1.0 → lança ValueError com mensagem clara
#
# Métodos úteis:
#   - is_above(threshold: Confidence) → bool:
#       verifica se a confiança passa o threshold configurado
#       (evita comparar floats soltos pelo código)
#   - as_percentage() → float:
#       devolve o valor em percentagem (ex: 0.87 → 87.0)
#
# Imutável após criação (@dataclass frozen=True).
