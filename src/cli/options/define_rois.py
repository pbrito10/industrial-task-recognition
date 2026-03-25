# Opção "Definir ROIs".
#
# Responsabilidade: permitir ao utilizador desenhar as zonas de trabalho
# (ROIs) diretamente sobre um frame da câmara, e guardá-las em disco.
#
# Lógica:
#   1. Captura um frame da câmara e mostra-o numa janela OpenCV
#   2. O utilizador desenha retângulos com o rato (click + arrastar)
#   3. Após cada retângulo, pede o nome da zona (ex: "Zona A")
#   4. As zonas são mostradas sobrepostas na imagem enquanto se desenham
#   5. Quando termina (tecla 's'), guarda todas as ROIs via RoiRepository
#
# As ROIs ficam guardadas em config/rois.json e são carregadas
# automaticamente na próxima sessão.
#
# Se já existirem ROIs guardadas, mostra-as primeiro e pergunta
# se quer manter, editar ou apagar.
