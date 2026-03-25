# Detector falso para desenvolvimento e testes sem o modelo treinado.
#
# Responsabilidade: simular o output do YoloDetector com dados sintéticos,
# permitindo desenvolver e testar toda a pipeline sem o ficheiro .pt.
#
# Lógica:
#   - Lê o cycle_zone_order e as ROIs do settings.yaml e rois.json
#     para gerar um percurso realista pelas zonas configuradas —
#     não tem zonas hardcoded, acompanha automaticamente qualquer
#     alteração à configuração (Open/Closed)
#   - Simula uma mão a percorrer as zonas em sequência, permanecendo
#     em cada uma o tempo suficiente para cumprir o dwell time
#   - Gera HandDetection com KeypointCollection (21 pontos sintéticos),
#     BoundingBox e Confidence plausíveis para a zona atual
#   - Implementa a mesma DetectorInterface que YoloDetector — o resto
#     do sistema não nota a diferença (Liskov Substitution)
#
# Para testar a zona Assembly (two_hands), simula as duas mãos
# dentro da zona em simultâneo durante o tempo configurado.
#
# Quando o modelo estiver pronto, basta mudar use_mock: false no
# settings.yaml — nenhum outro ficheiro muda.
