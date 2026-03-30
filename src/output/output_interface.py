# TODO: implementar
#
# Interface (classe abstrata) para os consumidores de output.
#
# Responsabilidade: definir o contrato mínimo para qualquer destino
# de output, seja dashboard ou Excel.
#
# Contrato:
#   - write(snapshot: MetricsSnapshot) → None:
#       recebe o snapshot atual das métricas (tipado, não dict genérico)
#       e regista/apresenta conforme a implementação concreta
#
# Porquê MetricsSnapshot em vez de dict?
#   Um dict genérico não comunica o contrato — qualquer implementação
#   teria de adivinhar as chaves. MetricsSnapshot torna explícito
#   exatamente o que cada output recebe. (ver output/metrics_snapshot.py)
#
# Princípio (Interface Segregation + Dependency Inversion):
#   O MetricsCalculator depende desta interface, não das implementações
#   concretas. Podem existir vários outputs ativos em simultâneo
#   (dashboard + Excel) sem o MetricsCalculator saber quantos são.
