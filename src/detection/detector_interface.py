# Interface (classe abstrata) para o detector de mãos.
#
# Responsabilidade: definir o contrato que qualquer detector tem de cumprir,
# sem depender de uma implementação concreta.
#
# Princípio (Dependency Inversion): o resto do sistema depende desta
# interface, não do YoloDetector diretamente. Assim, trocar o modelo
# ou usar o mock não exige alterar mais nenhum ficheiro.
#
# Contrato:
#   - detect(frame) → lista de HandDetection
#     Recebe um frame (numpy array do OpenCV) e devolve as mãos detetadas.
#
# Usa abc.ABC e @abstractmethod para forçar implementação nas subclasses.
