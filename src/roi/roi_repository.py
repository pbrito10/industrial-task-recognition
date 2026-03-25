# Interface (classe abstrata) para persistência de ROIs.
#
# Responsabilidade: definir o contrato de guardar e carregar ROIs,
# sem depender do formato de armazenamento concreto.
#
# Contrato:
#   - save(roi_collection: RoiCollection) → None
#   - load() → RoiCollection
#
# Princípio (Dependency Inversion): o código que usa ROIs depende
# desta interface. Se amanhã quiseres guardar em base de dados em
# vez de JSON, crias uma nova implementação sem tocar no resto.
