# Abstração da fonte de vídeo (câmara ou ficheiro).
#
# Responsabilidade: fornecer frames ao VideoProcessor, independentemente
# de virem de uma webcam USB ou de um ficheiro de vídeo gravado.
#
# Lógica:
#   - No __init__, abre o cv2.VideoCapture com o índice/path configurado
#   - read_frame() → frame (numpy array) | None:
#       devolve o próximo frame, ou None se a fonte terminou/falhou
#   - release(): liberta o recurso (sempre chamado no finally do processor)
#   - fps() → float: FPS da câmara/vídeo (para cálculos temporais)
#   - is_open() → bool
#
# O índice da câmara (ex: 0, 1, 2) é configurável em settings.yaml
# para suportar múltiplas câmaras USB.
