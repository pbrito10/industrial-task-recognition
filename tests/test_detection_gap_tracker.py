from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

from monitor_process import _DetectionGapTracker
from src.roi.roi_collection import RoiCollection
from src.shared.hand_side import HandSide
from tests.conftest import make_hand

_T0 = datetime(2024, 3, 15, 9, 30, 0)


class _FakeDebugLogger:
    def __init__(self) -> None:
        self.gaps = []

    def log_detection_gap(self, gap_start, relative, duration, hand_side=None) -> None:
        self.gaps.append({
            "gap_start": gap_start,
            "relative": relative,
            "duration": duration,
            "hand_side": hand_side,
        })


def _tracker(tmp_path):
    return _DetectionGapTracker(
        threshold_s=1.0,
        session_start=_T0,
        output_dir=tmp_path,
        cycle_number_fn=lambda: 2,
        rois=RoiCollection(),
        color_scheme=None,
    )


def _frame():
    return np.zeros((8, 8, 3), dtype=np.uint8)


def test_logs_right_hand_gap_while_left_remains_detected(tmp_path):
    tracker = _tracker(tmp_path)
    logger = _FakeDebugLogger()
    left = make_hand(side=HandSide.LEFT)
    right = make_hand(side=HandSide.RIGHT)

    tracker.update([left, right], _T0, _frame(), logger)
    tracker.update([left], _T0 + timedelta(seconds=0.2), _frame(), logger)
    tracker.update([left], _T0 + timedelta(seconds=1.5), _frame(), logger)

    assert logger.gaps == []

    tracker.update([left, right], _T0 + timedelta(seconds=2.4), _frame(), logger)

    assert len(logger.gaps) == 1
    assert logger.gaps[0]["hand_side"] == "right"
    assert logger.gaps[0]["gap_start"] == _T0 + timedelta(seconds=0.2)
    assert logger.gaps[0]["duration"] == timedelta(seconds=2.2)
    assert (tmp_path / "gap_right_ciclo_002.jpg").exists()


def test_does_not_open_gap_for_hand_that_was_never_seen(tmp_path):
    tracker = _tracker(tmp_path)
    logger = _FakeDebugLogger()
    left = make_hand(side=HandSide.LEFT)

    tracker.update([left], _T0, _frame(), logger)
    tracker.update([left], _T0 + timedelta(seconds=3), _frame(), logger)

    assert logger.gaps == []
    assert list(tmp_path.iterdir()) == []


def test_ignores_short_per_hand_gap(tmp_path):
    tracker = _tracker(tmp_path)
    logger = _FakeDebugLogger()
    left = make_hand(side=HandSide.LEFT)
    right = make_hand(side=HandSide.RIGHT)

    tracker.update([left, right], _T0, _frame(), logger)
    tracker.update([left], _T0 + timedelta(seconds=0.2), _frame(), logger)
    tracker.update([left, right], _T0 + timedelta(seconds=0.8), _frame(), logger)

    assert logger.gaps == []
    assert list(tmp_path.iterdir()) == []
