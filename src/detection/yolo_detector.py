# Implementação do detector usando o modelo YOLOv26 custom.
#
# Responsabilidade: carregar o ficheiro .pt treinado e correr inferência
# em cada frame, devolvendo os resultados no formato padronizado.
#
# Lógica:
#   - No __init__, carrega o modelo a partir do path definido em settings.yaml
#   - O método detect() corre o modelo no frame recebido
#   - Converte o output raw do YOLO (tensores) em objetos HandDetection
#     com os 21 keypoints e a bounding box de cada mão
#   - Filtra deteções abaixo do threshold de confiança (configurável)
#
# Nota: este ficheiro só é instanciado quando o .pt estiver disponível.
# Enquanto o modelo está em treino, o sistema usa MockDetector.
