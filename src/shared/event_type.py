# Enum que representa o tipo de evento de zona.
#
# Responsabilidade: substituir strings "ENTER" / "EXIT" por um tipo
# seguro, eliminando a possibilidade de erros de digitação.
#
# Porquê não usar str?
#   Igual ao HandSide — um conjunto fixo e conhecido de valores deve
#   ser um enum, não strings livres. Garante que só existem dois tipos
#   de evento possíveis e que o Python valida isso automaticamente.
#
# Valores:
#   EventType.ENTER → a mão entrou na zona (após dwell time cumprido)
#   EventType.EXIT  → a mão saiu da zona
#
# Usado em:
#   - ZoneEvent: classifica o tipo de evento registado
#   - FrameProcessor: emite o tipo correto ao detetar transições
#   - TaskStateMachine: reage de forma diferente a ENTER vs EXIT
#
# Relação entre os dois tipos:
#   Cada ENTER deve ter um EXIT correspondente (exceto se a sessão
#   terminar com a mão ainda dentro da zona). O EventLogger escreve
#   ambos no CSV para que seja possível calcular durações offline.
