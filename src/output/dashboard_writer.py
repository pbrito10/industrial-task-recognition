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
        self._output_path = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, snapshot: MetricsSnapshot) -> None:
        data      = self._serialize(snapshot)
        temp_path = self._output_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self._output_path)

    def _serialize(self, snapshot: MetricsSnapshot) -> dict:
        """Converte o snapshot para o dict JSON enviado ao Streamlit."""
        return {
            "captured_at":      snapshot.captured_at.isoformat(),
            "session_duration": snapshot.session_duration.total_seconds(),
            "task_metrics":     self._serialize_task_metrics(snapshot),
            "cycle_metrics":    self._serialize_cycle_metrics(snapshot),
            "time_breakdown": {
                "productive_pct":   round(snapshot.productive_percentage, 2),
                "transition_pct":   round(snapshot.transition_percentage, 2),
                "interruption_pct": round(snapshot.interruption_percentage, 2),
            },
            "bottleneck_zone": snapshot.bottleneck_zone,
        }

    def _serialize_task_metrics(self, snapshot: MetricsSnapshot) -> dict:
        """Serializa métricas por zona. Omite zonas sem ocorrências (count == 0)."""
        result = {}
        for zone_name, metrics in snapshot.task_metrics.items():
            if metrics.count() == 0:
                continue
            result[zone_name] = {
                "count":     metrics.count(),
                "min_s":     round(metrics.minimum().total_seconds(), 3),
                "avg_s":     round(metrics.average().total_seconds(), 3),
                "max_s":     round(metrics.maximum().total_seconds(), 3),
                "std_dev_s": round(metrics.std_deviation().total_seconds(), 3),
            }
        return result

    def _serialize_cycle_metrics(self, snapshot: MetricsSnapshot) -> dict:
        """Serializa métricas de ciclos. Devolve {"count": 0} se não há ciclos completos."""
        metrics = snapshot.cycle_metrics
        if metrics.count() == 0:
            return {"count": 0}

        correct_avg  = metrics.correct_average()
        avg_s        = round(correct_avg.total_seconds(), 3) if correct_avg else None

        return {
            "count":              metrics.count(),
            "min_s":              round(metrics.minimum().total_seconds(), 3),
            "avg_s":              avg_s,  # apenas ciclos corretos (sequence_in_order=True)
            "max_s":              round(metrics.maximum().total_seconds(), 3),
            "std_dev_s":          round(metrics.std_deviation().total_seconds(), 3),
            "count_in_order":          metrics.count_in_order(),
            "count_probably_complete": metrics.count_probably_complete(),
            "count_anomalies":         metrics.count_anomalies(),
        }
