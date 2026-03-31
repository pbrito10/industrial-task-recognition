from __future__ import annotations

from abc import ABC, abstractmethod

from src.detection.hand_detection import HandDetection


class ActivationStrategy(ABC):
    """Decide se o dwell timer deve avançar num dado frame.

    Recebe a deteção atual e a anterior (ou None se for o primeiro frame
    na zona) — sem estado interno, o que facilita reutilização entre mãos.

    Trocar a estratégia muda o critério de confirmação sem tocar na
    state machine (OCP + Strategy pattern).
    """

    @abstractmethod
    def is_active(
        self,
        detection: HandDetection,
        previous: HandDetection | None,
    ) -> bool:
        """True se a condição de ativação está cumprida neste frame."""


class TimeDwellStrategy(ActivationStrategy):
    """Estratégia de fallback: o timer avança sempre que a mão está na zona.

    Equivale ao dwell time clássico sem qualquer filtro de movimento.
    Útil para comparação ou zonas onde o movimento não é relevante.
    """

    def is_active(self, detection: HandDetection, previous: HandDetection | None) -> bool:
        return True


class StillnessDwellStrategy(ActivationStrategy):
    """O timer só avança quando a mão está suficientemente parada.

    Resolve a ambiguidade entre uma passagem lenta e uma tarefa rápida:
    uma passagem nunca para completamente, uma tarefa sim.

    O threshold é em píxeis por frame — valores típicos entre 3 e 8 px,
    dependendo da resolução e da distância da câmara à bancada.
    """

    def __init__(self, velocity_threshold_px: float) -> None:
        self._threshold = velocity_threshold_px

    def is_active(self, detection: HandDetection, previous: HandDetection | None) -> bool:
        if previous is None:
            # Primeiro frame na zona — sem dado anterior para calcular velocidade
            return False

        current_wrist  = detection.wrist().position
        previous_wrist = previous.wrist().position
        velocity       = current_wrist.distance_to(previous_wrist)

        return velocity < self._threshold
