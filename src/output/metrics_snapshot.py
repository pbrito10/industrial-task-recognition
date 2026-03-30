# TODO: implementar
#
# Value object que representa um snapshot das métricas num dado momento.
#
# Responsabilidade: transportar todas as métricas calculadas pelo
# MetricsCalculator de forma tipada — substitui o dict genérico que
# era passado pelo OutputInterface.
#
# Porquê não usar dict?
#   Um dict não comunica o que contém — o chamador não sabe que chaves
#   existem nem que tipos têm os valores. Um MetricsSnapshot deixa
#   explícito o contrato entre o MetricsCalculator e os consumidores
#   (DashboardWriter, ExcelExporter).
#
# Campos:
#   — Por tarefa (dict[str, TaskMetrics]):
#       chave: nome da zona; valor: TaskMetrics com min/méd/máx/desvio
#       Apenas tarefas com was_forced=False
#
#   — Ciclos (CycleMetrics):
#       min/méd/máx/desvio dos tempos de ciclo completo
#
#   — Decomposição do tempo (três timedelta que somam a duração da sessão):
#       productive_time    : tempo em tarefas was_forced=False
#       transition_time    : tempo entre zonas (sem zona ativa)
#       interruption_time  : tempo em tarefas was_forced=True
#
#   — productive_percentage  : float — % de tempo produtivo (0.0–100.0)
#   — transition_percentage  : float — % de tempo em transição
#   — interruption_percentage: float — % de tempo de interrupção
#
#   — bottleneck_zone: str | None — nome da zona com maior tempo médio;
#       None se ainda não há dados suficientes
#
#   — session_duration: timedelta — duração total da sessão até este momento
#   — captured_at: datetime — quando este snapshot foi gerado
#
# Imutável após criação (@dataclass frozen=True).
