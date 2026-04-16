from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font, PatternFill

from src.output.metrics_snapshot import MetricsSnapshot
from src.output.output_interface import OutputInterface
from src.tracking.cycle_result import CycleResult
from src.tracking.task_event import TaskEvent

# Cor de destaque para a zona gargalo (amarelo-âmbar)
_BOTTLENECK_FILL = PatternFill(start_color="FFD966", end_color="FFD966", fill_type="solid")
_HEADER_FONT     = Font(bold=True)

# Mapeamento direto para evitar ternário aninhado em _write_cycles
_ORDER_LABEL: dict[bool | None, str] = {True: "Sim", False: "Não", None: "—"}


class ExcelExporter(OutputInterface):
    """Exporta os dados da sessão para um ficheiro .xlsx no fim da sessão.

    Gera quatro folhas: Resumo, Métricas por Zona, Ciclos e Eventos.
    A zona gargalo é destacada a amarelo na folha de métricas.

    write() é chamado uma vez no fim — não é para uso online como o DashboardWriter.
    """

    def __init__(self, output_dir: Path, session_start: datetime) -> None:
        raise NotImplementedError

    def add_event(self, event: TaskEvent) -> None:
        """Acumula TaskEvents durante a sessão para exportar no fim."""
        raise NotImplementedError

    def add_cycle_result(self, cycle_result: CycleResult) -> None:
        """Regista se as zonas do ciclo foram visitadas na sequência correta."""
        raise NotImplementedError

    def write(self, snapshot: MetricsSnapshot) -> None:
        """Gera o ficheiro Excel com todas as folhas."""
        raise NotImplementedError

    def _write_summary(self, writer: pd.ExcelWriter, snapshot: MetricsSnapshot) -> None:
        """Folha 'Resumo': métricas globais da sessão numa única tabela de dois campos."""
        raise NotImplementedError

    def _write_zone_metrics(self, writer: pd.ExcelWriter, snapshot: MetricsSnapshot) -> None:
        """Folha 'Métricas por Zona': estatísticas por zona com gargalo destacado a amarelo."""
        raise NotImplementedError

    def _write_cycles(self, writer: pd.ExcelWriter) -> None:
        """Folha 'Ciclos': uma linha por ciclo com início, fim, duração e sequência correta."""
        raise NotImplementedError

    def _write_events(self, writer: pd.ExcelWriter) -> None:
        """Folha 'Eventos': uma linha por TaskEvent, incluindo tarefas forçadas por timeout."""
        raise NotImplementedError

    def _bold_headers(self, writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame) -> None:
        """Aplica bold à linha de cabeçalho da folha indicada."""
        raise NotImplementedError

    def _highlight_bottleneck(
        self,
        writer: pd.ExcelWriter,
        sheet_name: str,
        df: pd.DataFrame,
        bottleneck: str | None,
    ) -> None:
        """Destaca a amarelo todas as células da linha correspondente à zona gargalo."""
        raise NotImplementedError
