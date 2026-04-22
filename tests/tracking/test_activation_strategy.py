from tests.conftest import make_hand
from src.tracking.activation_strategy import TimeDwellStrategy, StillnessDwellStrategy
from src.shared.hand_side import HandSide


def test_time_dwell_always_active():
    strategy = TimeDwellStrategy()
    hand = make_hand()
    assert strategy.is_active(hand, None) is True
    assert strategy.is_active(hand, hand) is True


def test_stillness_no_previous_returns_false():
    strategy = StillnessDwellStrategy(velocity_threshold_px_per_frame=5.0)
    assert strategy.is_active(make_hand(wrist=(50, 50)), None) is False


def test_stillness_hand_not_moved():
    strategy = StillnessDwellStrategy(velocity_threshold_px_per_frame=5.0)
    hand = make_hand(wrist=(50, 50))
    prev = make_hand(wrist=(51, 50))  # distância = 1 px < 5
    assert strategy.is_active(hand, prev) is True


def test_stillness_hand_moved_too_much():
    strategy = StillnessDwellStrategy(velocity_threshold_px_per_frame=5.0)
    hand = make_hand(wrist=(50, 50))
    prev = make_hand(wrist=(60, 50))  # distância = 10 px > 5
    assert strategy.is_active(hand, prev) is False


def test_stillness_exactly_at_threshold():
    # distância == threshold → ainda conta como parada (< é estrito no código)
    strategy = StillnessDwellStrategy(velocity_threshold_px_per_frame=5.0)
    hand = make_hand(wrist=(50, 50))
    prev = make_hand(wrist=(55, 50))  # distância = 5.0, não passa o < 5.0
    assert strategy.is_active(hand, prev) is False
