# Ferramenta interativa para desenhar ROIs sobre um frame da câmara.
#
# Responsabilidade: gerir a interação com o rato e teclado no OpenCV
# para deixar o utilizador desenhar retângulos e associá-los às zonas
# definidas em settings.yaml — sem input de texto, sem ambiguidade.
#
# Princípio de funcionamento:
#   As zonas disponíveis vêm do cycle_zone_order do settings.yaml.
#   O utilizador seleciona qual zona está a desenhar com as teclas
#   numéricas, e depois desenha o retângulo com o rato.
#   Os nomes das zonas nunca são escritos manualmente — vêm sempre
#   da configuração, garantindo consistência com o rois.json.
#
# Teclas:
#   1–9 → seleciona a zona correspondente ao índice no cycle_zone_order
#          (ex: tecla 1 = cycle_zone_order[0] = "Zona A")
#          a zona selecionada fica destacada no ecrã
#   's' → guardar todas as zonas desenhadas e sair
#   'z' → desfazer a última zona desenhada
#   'q' → sair sem guardar
#
# Interação com o rato (eventos OpenCV):
#   EVENT_LBUTTONDOWN → regista ponto de início do retângulo
#   EVENT_MOUSEMOVE   → enquanto botão pressionado, desenha retângulo
#                       temporário em tempo real (feedback visual)
#   EVENT_LBUTTONUP   → regista ponto final, cria RegionOfInterest
#                       com o nome da zona atualmente selecionada,
#                       adiciona à RoiCollection
#
# Visualização:
#   - Cada zona desenhada aparece com cor diferente e o seu nome
#   - A zona atualmente selecionada é mostrada no topo do ecrã
#   - Zonas já desenhadas ficam sempre visíveis enquanto se desenham novas
#   - Se uma zona já foi desenhada e o utilizador seleciona a mesma tecla,
#     substitui a zona existente (permite corrigir sem 'z')
#
# Não faz input de texto — os nomes vêm exclusivamente do settings.yaml.
# Isto garante que rois.json e settings.yaml ficam sempre sincronizados.
