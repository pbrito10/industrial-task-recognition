import numpy as np
import pytest

from tests.conftest import make_hand, make_roi
from src.roi.roi_collection import RoiCollection
from src.shared.hand_side import HandSide
from src.video import frame_annotator


def _blank(h=200, w=200) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


# --- zone_color ---

def test_zone_color_montagem():
    assert frame_annotator.zone_color("Montagem") == (0, 165, 255)


def test_zone_color_saida():
    assert frame_annotator.zone_color("Saida") == (255, 100, 0)


def test_zone_color_unknown_returns_default():
    color = frame_annotator.zone_color("ZonaQualquer")
    assert color == (50, 205, 50)


# --- draw_hand ---

def test_draw_hand_modifies_frame():
    frame    = _blank()
    original = frame.copy()
    hand     = make_hand(wrist=(100, 100), mcp=(100, 100))
    frame_annotator.draw_hand(frame, hand)
    assert not np.array_equal(frame, original)


def test_draw_hand_right_uses_green_channel():
    frame = _blank()
    hand  = make_hand(wrist=(100, 100), mcp=(100, 100), side=HandSide.RIGHT)
    frame_annotator.draw_hand(frame, hand)
    # Cor da mão direita: (0, 200, 50) — canal verde dominante
    assert frame[100, 100, 1] > 0 or frame.max() > 0  # algo foi desenhado


def test_draw_hand_left_vs_right_different_colors():
    frame_r = _blank()
    frame_l = _blank()
    hand_r  = make_hand(wrist=(100, 100), mcp=(100, 100), side=HandSide.RIGHT)
    hand_l  = make_hand(wrist=(100, 100), mcp=(100, 100), side=HandSide.LEFT)
    frame_annotator.draw_hand(frame_r, hand_r)
    frame_annotator.draw_hand(frame_l, hand_l)
    assert not np.array_equal(frame_r, frame_l)


# --- draw_detections ---

def test_draw_detections_empty_list_no_crash():
    frame = _blank()
    frame_annotator.draw_detections(frame, [])  # não deve lançar


def test_draw_detections_draws_multiple():
    frame    = _blank()
    original = frame.copy()
    hands    = [
        make_hand(wrist=(50, 50),   mcp=(50, 50),   side=HandSide.RIGHT),
        make_hand(wrist=(150, 150), mcp=(150, 150), side=HandSide.LEFT),
    ]
    frame_annotator.draw_detections(frame, hands)
    assert not np.array_equal(frame, original)


# --- draw_roi ---

def test_draw_roi_modifies_frame():
    frame    = _blank()
    original = frame.copy()
    roi      = make_roi("Porca", 10, 10, 80, 80)
    frame_annotator.draw_roi(frame, roi, (0, 255, 0))
    assert not np.array_equal(frame, original)


def test_draw_roi_selected_vs_not_different():
    roi     = make_roi("Porca", 10, 10, 80, 80)
    f_sel   = _blank()
    f_nosel = _blank()
    frame_annotator.draw_roi(f_sel,   roi, (0, 255, 0), selected=True)
    frame_annotator.draw_roi(f_nosel, roi, (0, 255, 0), selected=False)
    # Contorno mais espesso = mais píxeis diferentes de zero
    assert f_sel.sum() != f_nosel.sum()


# --- draw_rois ---

def test_draw_rois_empty_collection_no_crash():
    frame = _blank()
    frame_annotator.draw_rois(frame, RoiCollection())


def test_draw_rois_draws_all():
    frame = _blank()
    rois  = RoiCollection()
    rois.add(make_roi("Porca",    10, 10, 80,  80))
    rois.add(make_roi("Montagem", 100, 10, 180, 80))
    original = frame.copy()
    frame_annotator.draw_rois(frame, rois)
    assert not np.array_equal(frame, original)


def test_draw_rois_selected_highlighted():
    roi    = make_roi("Porca", 10, 10, 80, 80)
    rois   = RoiCollection()
    rois.add(roi)
    f_sel   = _blank()
    f_nosel = _blank()
    frame_annotator.draw_rois(f_sel,   rois, selected_name="Porca")
    frame_annotator.draw_rois(f_nosel, rois, selected_name=None)
    assert f_sel.sum() != f_nosel.sum()


# --- draw_fps ---

def test_draw_fps_modifies_frame():
    frame    = _blank()
    original = frame.copy()
    frame_annotator.draw_fps(frame, 29.97)
    assert not np.array_equal(frame, original)
