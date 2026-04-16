from __future__ import annotations

import json
from pathlib import Path

from src.output.metrics_snapshot import MetricsSnapshot
from src.output.output_interface import OutputInterface


class DashboardWriter(OutputInterface):
    """Publica o snapshot de métricas no JSON lido pelo Streamlit.

    A escrita é feita em ficheiro temporário seguida de rename atómico.
    Sem isto, o Streamlit podia ler o ficheiro a meio de ser escrito
    e obter JSON inválido ou dados parciais.
    """

    def __init__(self, output_path: Path) -> None:
        raise NotImplementedError

    def write(self, snapshot: MetricsSnapshot) -> None:
        raise NotImplementedError

    def _serialize(self, snapshot: MetricsSnapshot) -> dict:
        """Converte o snapshot para o dict JSON enviado ao Streamlit."""
        raise NotImplementedError

    def _serialize_task_metrics(self, snapshot: MetricsSnapshot) -> dict:
        """Serializa métricas por zona. Omite zonas sem ocorrências (count == 0)."""
        raise NotImplementedError

    def _serialize_cycle_metrics(self, snapshot: MetricsSnapshot) -> dict:
        """Serializa métricas de ciclos. Devolve {"count": 0} se não há ciclos completos."""
        raise NotImplementedError
