import csv
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from tests.conftest import make_hand
from src.events.debug_logger import DebugLogger, _COLUMNS
from src.tracking.cycle_result import CycleResult
from src.tracking.task_event import TaskEvent

_SESSION_START = datetime(2024, 3, 15, 9, 30, 0)
_T0 = _SESSION_START


def _task_event(zone="Porca", duration_s=5.0, forced=False) -> TaskEvent:
    start = _T0
    end   = _T0 + timedelta(seconds=duration_s)
    return TaskEvent.create(zone, start, end, cycle_number=1, was_forced=forced)


def _cycle_result(duration_s=60.0, in_order=True) -> CycleResult:
    return CycleResult(
        start_time=_T0,
        end_time=_T0 + timedelta(seconds=duration_s),
        duration=timedelta(seconds=duration_s),
        cycle_number=1,
        sequence_in_order=in_order,
        actual_sequence=["Porca", "Saida"],
    )


@pytest.fixture
def logger(tmp_path):
    with DebugLogger(tmp_path, _SESSION_START) as log:
        yield log, tmp_path


def _read_csv(directory: Path) -> list[dict]:
    files = list(directory.glob("debug_*.csv"))
    assert len(files) == 1
    with open(files[0], newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# --- Criação e cabeçalho ---

def test_creates_csv_file(tmp_path):
    with DebugLogger(tmp_path, _SESSION_START):
        pass
    assert len(list(tmp_path.glob("debug_*.csv"))) == 1


def test_filename_contains_session_date(tmp_path):
    with DebugLogger(tmp_path, _SESSION_START):
        pass
    files = list(tmp_path.glob("debug_*.csv"))
    assert "2024-03-15" in files[0].name


def test_header_has_all_columns(tmp_path):
    with DebugLogger(tmp_path, _SESSION_START):
        pass
    rows = _read_csv(tmp_path)
    # csv.DictReader usa o header como chaves — se o ficheiro só tem o header, rows é vazio
    files = list(tmp_path.glob("debug_*.csv"))
    with open(files[0], newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
    assert header == _COLUMNS


# --- log_zone_enter ---

def test_log_zone_enter_event_type(logger):
    log, tmp_path = logger
    hand = make_hand(mcp=(50, 50))
    log.log_zone_enter(_T0, timedelta(seconds=1), "Porca", hand, frame_idx=10)
    rows = _read_csv(tmp_path)
    assert rows[0]["event_type"] == "ZONE_ENTER"


def test_log_zone_enter_fields(logger):
    log, tmp_path = logger
    hand = make_hand(mcp=(50, 50))
    log.log_zone_enter(_T0, timedelta(seconds=2.5), "Porca", hand, frame_idx=10)
    row = _read_csv(tmp_path)[0]
    assert row["zone"] == "Porca"
    assert row["x_px"] == "50"
    assert row["y_px"] == "50"
    assert row["frame_idx"] == "10"
    assert row["relative_time_s"] == "2.5"


# --- log_zone_exit ---

def test_log_zone_exit_event_type(logger):
    log, tmp_path = logger
    hand = make_hand(mcp=(80, 80))
    log.log_zone_exit(_T0, timedelta(seconds=3), "Montagem", hand, frame_idx=20)
    rows = _read_csv(tmp_path)
    assert rows[0]["event_type"] == "ZONE_EXIT"


# --- log_task_complete ---

def test_log_task_complete_event_type(logger):
    log, tmp_path = logger
    log.log_task_complete(_task_event("Porca", 5.0))
    row = _read_csv(tmp_path)[0]
    assert row["event_type"] == "TASK_COMPLETE"


def test_log_task_complete_duration(logger):
    log, tmp_path = logger
    log.log_task_complete(_task_event("Porca", 7.5))
    row = _read_csv(tmp_path)[0]
    assert float(row["duration_s"]) == pytest.approx(7.5)


def test_log_task_complete_zone(logger):
    log, tmp_path = logger
    log.log_task_complete(_task_event("Montagem", 3.0))
    row = _read_csv(tmp_path)[0]
    assert row["zone"] == "Montagem"


# --- log_task_timeout ---

def test_log_task_timeout_event_type(logger):
    log, tmp_path = logger
    log.log_task_timeout(_task_event("Rodas", forced=True))
    row = _read_csv(tmp_path)[0]
    assert row["event_type"] == "TASK_TIMEOUT"


# --- log_cycle_complete ---

def test_log_cycle_complete_event_type(logger):
    log, tmp_path = logger
    log.log_cycle_complete(_cycle_result())
    row = _read_csv(tmp_path)[0]
    assert row["event_type"] == "CYCLE_COMPLETE"


def test_log_cycle_complete_sequence_in_order_true(logger):
    log, tmp_path = logger
    log.log_cycle_complete(_cycle_result(in_order=True))
    row = _read_csv(tmp_path)[0]
    assert row["sequence_in_order"] == "true"


def test_log_cycle_complete_sequence_in_order_false(logger):
    log, tmp_path = logger
    log.log_cycle_complete(_cycle_result(in_order=False))
    row = _read_csv(tmp_path)[0]
    assert row["sequence_in_order"] == "false"


def test_log_cycle_complete_duration(logger):
    log, tmp_path = logger
    log.log_cycle_complete(_cycle_result(duration_s=45.0))
    row = _read_csv(tmp_path)[0]
    assert float(row["duration_s"]) == pytest.approx(45.0)


# --- Múltiplos eventos e flush ---

def test_multiple_events_written(logger):
    log, tmp_path = logger
    hand = make_hand(mcp=(50, 50))
    log.log_zone_enter(_T0, timedelta(0), "Porca", hand, 0)
    log.log_task_complete(_task_event())
    log.log_cycle_complete(_cycle_result())
    rows = _read_csv(tmp_path)
    assert len(rows) == 3


def test_file_readable_before_close(tmp_path):
    # flush imediato — dados visíveis sem fechar o ficheiro
    log = DebugLogger(tmp_path, _SESSION_START)
    hand = make_hand(mcp=(50, 50))
    log.log_zone_enter(_T0, timedelta(0), "Porca", hand, 0)
    rows = _read_csv(tmp_path)
    assert len(rows) == 1
    log.close()


# --- Context manager ---

def test_context_manager_closes_file(tmp_path):
    with DebugLogger(tmp_path, _SESSION_START) as log:
        pass
    assert log._file.closed
