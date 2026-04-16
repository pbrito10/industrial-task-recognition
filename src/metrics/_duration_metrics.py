from __future__ import annotations

import math
from datetime import timedelta


class _DurationMetrics:
    """Base para classes de métricas baseadas em coleções de durações.

    Encapsula armazenamento e estatísticas (mínimo, máximo, média, desvio padrão),
    eliminando duplicação entre TaskMetrics e CycleMetrics.

    Prefixo _ — privada ao package metrics, não para uso externo.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    def _add_duration(self, duration: timedelta) -> None:
        """Regista uma duração. Chamado pelas subclasses no seu add()."""
        raise NotImplementedError

    def count(self) -> int:
        """Número de ocorrências registadas."""
        raise NotImplementedError

    def minimum(self) -> timedelta:
        """Duração mínima observada. Requer count() > 0."""
        raise NotImplementedError

    def maximum(self) -> timedelta:
        """Duração máxima observada. Requer count() > 0."""
        raise NotImplementedError

    def average(self) -> timedelta:
        """Média aritmética das durações. Requer count() > 0."""
        raise NotImplementedError

    def std_deviation(self) -> timedelta:
        """Desvio padrão das durações. Devolve timedelta(0) se count() < 2."""
        raise NotImplementedError
