"""Ferramenta 4 — Análise de Sessão.

Lê o CSV de debug gerado pelo DebugLogger e produz uma tabela onde cada linha
é um ciclo e cada coluna é uma ocorrência de zona do cycle_zone_order.

Células:
  "12.3s"            — zona concluída normalmente
  "TIMEOUT→OK 12.3s" — houve timeout mas o operador voltou e completou
  "TIMEOUT"          — timeout sem recuperação
  "—"                — zona não visitada

Colunas extras:
  Ordem correta — Sim/Não (sequência dos TASK_COMPLETE vs expected_order)
  Resultado do sistema — Em ordem, Sequência incompleta ou Fora de ordem
  Problema detetado — explicação automática da comparação de sequência
  Classificação manual / Observações — colunas vazias para validação humana
  Duração total — soma das durações dos TASK_COMPLETE do ciclo

Uso:
  python -m analysis.session_analysis <debug_csv>
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml

from src.output.session_config_snapshot import expected_order_from_snapshot, snapshot_path_for_csv
from src.shared.event_type import EventType
from src.tracking.order_matching import RESULT_IN_ORDER, diagnose_order, matches_order

_SETTINGS_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"

# Valores de célula — definidos uma vez para evitar magic strings duplicadas
_CELL_TIMEOUT_OK = "TIMEOUT→OK"
_CELL_TIMEOUT    = "TIMEOUT"
_CELL_ABSENT     = "—"


def _load_expected_order() -> list[str]:
    with open(_SETTINGS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)["tracking"]["cycle_zone_order"]


def _load_expected_order_for_csv(csv_path: Path) -> list[str]:
    snapshot_order = expected_order_from_snapshot(csv_path)
    if snapshot_order is not None:
        return snapshot_order
    return _load_expected_order()


def _col_names(expected_order: list[str]) -> list[str]:
    """Gera nomes únicos para zonas repetidas (ex: Montagem → Montagem_1, Montagem_2...)."""
    totals: dict[str, int] = {}
    for zone in expected_order:
        totals[zone] = totals.get(zone, 0) + 1

    count: dict[str, int] = {}
    names = []
    for zone in expected_order:
        count[zone] = count.get(zone, 0) + 1
        names.append(f"{zone}_{count[zone]}" if totals[zone] > 1 else zone)
    return names


def _cell_value(had_timeout: bool, completed: bool, duration_s: float | None) -> str:
    if completed:
        return f"{_CELL_TIMEOUT_OK} {duration_s:.1f}s" if had_timeout else f"{duration_s:.1f}s"
    return _CELL_TIMEOUT if had_timeout else _CELL_ABSENT


def _index_events_by_zone(
    group: pd.DataFrame,
) -> tuple[dict[str, list[tuple]], dict[str, list[str]]]:
    """Separa e indexa TASK_COMPLETE e TASK_TIMEOUT por zona, ordenados cronologicamente."""
    completes_by_zone: dict[str, list[tuple]] = defaultdict(list)
    timeouts_by_zone:  dict[str, list[str]]   = defaultdict(list)

    for _, row in (
        group[group["event_type"] == EventType.TASK_COMPLETE.value]
        .sort_values("timestamp_iso")
        .iterrows()
    ):
        completes_by_zone[row["zone"]].append((row["timestamp_iso"], float(row["duration_s"])))

    for _, row in (
        group[group["event_type"] == EventType.TASK_TIMEOUT.value]
        .sort_values("timestamp_iso")
        .iterrows()
    ):
        timeouts_by_zone[row["zone"]].append(row["timestamp_iso"])

    return completes_by_zone, timeouts_by_zone


def _remaining_timeouts(
    completes_by_zone: dict[str, list[tuple]],
    timeouts_by_zone:  dict[str, list[str]],
    expected_order:    list[str],
) -> dict[str, int]:
    """Conta timeouts sem complete correspondente por zona (ocorreram após o último complete)."""
    result: dict[str, int] = {}
    for zone in set(expected_order):
        completes = completes_by_zone[zone]
        timeouts  = timeouts_by_zone[zone]
        last_c_ts = completes[-1][0] if completes else ""
        result[zone] = sum(1 for t in timeouts if t > last_c_ts)
    return result


def _build_row(
    group:          pd.DataFrame,
    expected_order: list[str],
    col_names:      list[str],
) -> dict:
    """Constrói a linha da tabela para um ciclo."""
    completes_by_zone, timeouts_by_zone = _index_events_by_zone(group)
    remaining = _remaining_timeouts(completes_by_zone, timeouts_by_zone, expected_order)
    remaining_ptr = dict(remaining)

    complete_ptr: dict[str, int] = defaultdict(int)
    result: dict[str, str] = {}

    for zone, col in zip(expected_order, col_names):
        c_idx     = complete_ptr[zone]
        completes = completes_by_zone[zone]
        timeouts  = timeouts_by_zone[zone]

        if c_idx < len(completes):
            c_ts, c_dur = completes[c_idx]
            complete_ptr[zone] += 1
            prev_ts     = completes[c_idx - 1][0] if c_idx > 0 else ""
            had_timeout = any(prev_ts < t_ts < c_ts for t_ts in timeouts)
            result[col] = _cell_value(had_timeout, True, c_dur)
        else:
            if remaining_ptr.get(zone, 0) > 0:
                remaining_ptr[zone] -= 1
                result[col] = _CELL_TIMEOUT
            else:
                result[col] = _CELL_ABSENT

    # Ordem: sequência real dos TASK_COMPLETE vs expected_order
    complete_rows = (
        group[group["event_type"] == EventType.TASK_COMPLETE.value]
        .sort_values("timestamp_iso")
    )
    actual_seq    = list(complete_rows["zone"])
    result["Ordem correta"] = "Sim" if matches_order(actual_seq, expected_order) else "Não"

    diagnosis = diagnose_order(actual_seq, expected_order)
    result["Resultado do sistema"] = diagnosis.result
    result["Problema detetado"] = diagnosis.problem
    result["Classificação manual"] = ""
    result["Observações"] = ""

    total_s = complete_rows["duration_s"].astype(float).sum() if not complete_rows.empty else 0.0
    result["Duração total (s)"] = round(total_s, 2)

    return result


def build_table(csv_path: Path) -> pd.DataFrame:
    """Lê o CSV e devolve o DataFrame com uma linha por ciclo."""
    expected_order = _load_expected_order_for_csv(csv_path)
    cols           = _col_names(expected_order)

    df = pd.read_csv(csv_path)
    task_df = (
        df[df["event_type"].isin([EventType.TASK_COMPLETE.value, EventType.TASK_TIMEOUT.value])]
        .dropna(subset=["cycle_number"])
        .copy()
    )
    task_df["cycle_number"] = task_df["cycle_number"].astype(int)

    rows = []
    for cycle_num, group in task_df.groupby("cycle_number"):
        row = {"Ciclo": int(cycle_num)}
        row.update(_build_row(group, expected_order, cols))
        rows.append(row)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).set_index("Ciclo")


def _save_table(table: pd.DataFrame, csv_path: Path) -> Path:
    output = csv_path.with_name(csv_path.stem + "_anomalias.xlsx")
    table.to_excel(output)
    return output


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m analysis.session_analysis <debug_csv>")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Ficheiro não encontrado: {csv_path}")
        sys.exit(1)

    table  = build_table(csv_path)
    output = _save_table(table, csv_path)

    if not snapshot_path_for_csv(csv_path).exists():
        print("Aviso: snapshot de configuração da sessão não encontrado; usada a config atual.")

    total    = len(table)
    corretos = (table["Resultado do sistema"] == RESULT_IN_ORDER).sum()
    print(f"Tabela guardada: {output}")
    print(f"Total: {total} ciclos  |  Em ordem: {corretos}  |  A rever: {total - corretos}")


if __name__ == "__main__":
    main()
