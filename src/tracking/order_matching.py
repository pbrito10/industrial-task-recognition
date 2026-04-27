from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

RESULT_IN_ORDER = "Em ordem"
RESULT_INCOMPLETE = "Sequência incompleta"
RESULT_OUT_OF_ORDER = "Fora de ordem"


@dataclass(frozen=True)
class OrderDiagnosis:
    result: str
    problem: str


def matches_order(actual: list[str], expected: list[str]) -> bool:
    """Verifica se a sequência real respeita a ordem esperada.

    Permite repetições consecutivas da mesma zona, mas não permite saltar zonas
    nem visitá-las fora de ordem.
    """
    if not expected:
        return True
    if not actual:
        return False

    ptr = 0
    entered_current = False

    for zone in actual:
        if zone == expected[ptr]:
            entered_current = True
            continue
        if entered_current and ptr + 1 < len(expected) and zone == expected[ptr + 1]:
            ptr += 1
            entered_current = True
            continue
        return False

    return entered_current and ptr == len(expected) - 1


def diagnose_order(actual: Sequence[str], expected: Sequence[str]) -> OrderDiagnosis:
    """Explica como a sequência registada se compara com a ordem esperada."""
    actual_list   = list(actual)
    expected_list = list(expected)

    if not expected_list:
        return OrderDiagnosis(RESULT_IN_ORDER, "Sem ordem esperada definida.")

    if not actual_list:
        return OrderDiagnosis(
            RESULT_INCOMPLETE,
            f"Não foram registadas zonas completas. Faltaram zonas esperadas: {_join_zones(expected_list)}.",
        )

    ptr             = 0
    entered_current = False
    missing: list[str] = []

    for zone in actual_list:
        if ptr >= len(expected_list):
            return OrderDiagnosis(
                RESULT_OUT_OF_ORDER,
                f'A sequência esperada já estava completa, mas apareceu "{zone}".',
            )

        if zone == expected_list[ptr]:
            entered_current = True
            continue

        search_start = ptr + 1 if entered_current else ptr
        next_index = _find_from(expected_list, zone, search_start)
        if next_index is not None:
            missing_start = ptr + 1 if entered_current else ptr
            missing.extend(expected_list[missing_start:next_index])
            ptr = next_index
            entered_current = True
            continue

        expected_zone = _next_expected_zone(expected_list, ptr, entered_current)
        return OrderDiagnosis(
            RESULT_OUT_OF_ORDER,
            f'Esperava "{expected_zone}", mas apareceu "{zone}".',
        )

    if ptr == len(expected_list) - 1 and entered_current and not missing:
        return OrderDiagnosis(RESULT_IN_ORDER, "Sem problema detetado.")

    missing_start = ptr + 1 if entered_current else ptr
    missing.extend(expected_list[missing_start:])
    return OrderDiagnosis(
        RESULT_INCOMPLETE,
        f"Faltaram zonas esperadas: {_join_zones(missing)}.",
    )


def _find_from(values: Sequence[str], target: str, start: int) -> int | None:
    for idx in range(start, len(values)):
        if values[idx] == target:
            return idx
    return None


def _next_expected_zone(expected: Sequence[str], ptr: int, entered_current: bool) -> str:
    if entered_current and ptr + 1 < len(expected):
        return expected[ptr + 1]
    return expected[ptr]


def _join_zones(zones: Sequence[str]) -> str:
    return ", ".join(f'"{zone}"' for zone in zones)
