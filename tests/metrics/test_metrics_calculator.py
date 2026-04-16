"""Testes para src/metrics/metrics_calculator.py"""
from datetime import datetime, timedelta
from src.metrics.metrics_calculator import MetricsCalculator
from src.tracking.task_event import TaskEvent
from src.tracking.cycle_result import CycleResult

T0    = datetime(2026, 1, 1, 10, 0, 0)
ZONES = ["Porca", "Montagem", "Saida"]


def _event(zone: str, start_s: float, end_s: float, forced: bool = False) -> TaskEvent:
    return TaskEvent.create(
        zone_name=zone,
        start_time=T0 + timedelta(seconds=start_s),
        end_time=T0 + timedelta(seconds=end_s),
        cycle_number=1,
        was_forced=forced,
    )


# -- snapshot sem dados -------------------------------------------------------

def test_snapshot_inicial_sem_ciclos():
    calc = MetricsCalculator(T0, ZONES)
    snap = calc.snapshot()
    assert snap.cycle_metrics.count() == 0

def test_snapshot_inicial_tempo_produtivo_zero():
    pass


# -- record -------------------------------------------------------------------

def test_record_normal_acumula_tempo_produtivo():
    pass

def test_record_forced_acumula_interrupcao():
    pass

def test_record_zona_desconhecida_nao_falha():
    # zona fora do settings.yaml deve ser aceite sem erro
    pass


# -- percentagens -------------------------------------------------------------

def test_percentagens_somam_100():
    pass

def test_sem_eventos_percentagens_sao_zero():
    pass


# -- bottleneck ---------------------------------------------------------------

def test_bottleneck_zona_com_maior_media():
    pass

def test_bottleneck_none_sem_dados():
    pass
