from __future__ import annotations

from abc import ABC, abstractmethod

from src.output.metrics_snapshot import MetricsSnapshot


class OutputInterface(ABC):
    """Contrato para qualquer destino de output (dashboard, Excel, etc.).

    O MetricsCalculator depende desta abstração — nunca das implementações
    concretas. Múltiplos outputs podem estar ativos em simultâneo sem o
    calculador saber quantos são (DIP + ISP).
    """

    @abstractmethod
    def write(self, snapshot: MetricsSnapshot) -> None:
        """Publica o snapshot atual das métricas."""
