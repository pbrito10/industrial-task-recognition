# Enum que representa qual das mãos foi detetada.
#
# Responsabilidade: substituir strings "left" / "right" por um tipo
# seguro que o Python valida em tempo de execução.
#
# Porquê não usar str?
#   Com strings, um typo como "lef" ou "Left" passaria despercebido
#   até aparecer um bug difícil de rastrear. Com um enum, o Python
#   lança um erro imediatamente se o valor não existir.
#   Além disso, o IDE consegue fazer autocomplete e detetar erros.
#
# Valores:
#   HandSide.LEFT  → mão esquerda
#   HandSide.RIGHT → mão direita
#
# Usado em:
#   - HandDetection: identifica qual mão foi detetada pelo YOLO
#   - ZoneEvent: regista qual mão gerou o evento de zona
#
# Nota sobre câmara top-down:
#   Com vista de cima, a distinção esquerda/direita depende de como
#   o modelo foi treinado. Se o modelo não distinguir, ambas as mãos
#   podem ser reportadas como HandSide.RIGHT — isso é tratado na
#   configuração do YoloDetector, não aqui.
