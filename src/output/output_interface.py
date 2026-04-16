from __future__ import annotations

from abc import ABC, abstractmethod

from src.output.metrics_snapshot import MetricsSnapshot


class OutputInterface(ABC):
    """Contrato para qualquer destino de output (dashboard, Excel, etc.).

    Permite que o mesmo MetricsSnapshot seja escrito em múltiplos destinos
    sem o orquestrador conhecer as implementações concretas.
    Implementações: DashboardWriter (JSON em tempo real), ExcelExporter (fim de sessão).
    """

    @abstractmethod
    def write(self, snapshot: MetricsSnapshot) -> None:
        """Publica o snapshot atual das métricas no destino concreto."""
