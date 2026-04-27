from __future__ import annotations


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
