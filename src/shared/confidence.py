from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Confidence:
    """Valor de confiança de uma deteção, sempre no intervalo [0.0, 1.0].

    Substituir float solto por este tipo torna a intenção explícita
    e valida o intervalo logo na criação.
    """

    value: float

    def __post_init__(self) -> None:
        raise NotImplementedError

    def is_above(self, threshold: Confidence) -> bool:
        """Verifica se a confiança supera o threshold — evita comparar floats pelo código."""
        raise NotImplementedError

    def as_percentage(self) -> float:
        """Devolve o valor em percentagem (ex: 0.87 → 87.0)."""
        raise NotImplementedError
