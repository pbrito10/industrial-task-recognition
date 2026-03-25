# Implementação da persistência de ROIs em ficheiro JSON.
#
# Responsabilidade: guardar e carregar a RoiCollection de/para
# config/rois.json.
#
# Lógica de save():
#   - Converte cada RegionOfInterest para dict via to_dict()
#   - Serializa a lista para JSON com indentação legível
#   - Escreve em config/rois.json (path configurável)
#
# Lógica de load():
#   - Se o ficheiro não existir, devolve RoiCollection vazia
#   - Lê o JSON e reconstrói cada RegionOfInterest via from_dict()
#   - Devolve uma RoiCollection com todas as zonas
#
# Exemplo do ficheiro gerado:
# [
#   {"name": "Zona A", "x1": 50, "y1": 80, "x2": 200, "y2": 250},
#   {"name": "Zona B", "x1": 210, "y1": 80, "x2": 380, "y2": 250}
# ]
