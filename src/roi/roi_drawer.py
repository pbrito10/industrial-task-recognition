from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

import cv2
import numpy as np

from src.roi.region_of_interest import RegionOfInterest
from src.roi.roi_collection import RoiCollection
from src.shared.point import Point
from src.video.camera import Camera

# ── Constantes visuais ──────────────────────────────────────────────────────

_WINDOW_NAME = "Definir ROIs  |  1-9 zona  |  Del apagar  |  s guardar  |  q sair"
_CORNER_RADIUS = 10
_MIN_ROI_PIXELS = 15
_FONT = cv2.FONT_HERSHEY_SIMPLEX
_FILL_ALPHA = 0.2

# Cores por índice de zona (BGR)
_ZONE_COLORS: list[tuple[int, int, int]] = [
    (50, 205, 50),
    (30, 144, 255),
    (0, 140, 255),
    (180, 105, 255),
    (0, 215, 255),
    (147, 20, 255),
    (0, 250, 154),
    (0, 165, 255),
    (255, 191, 0),
]

# Teclas que disparam "apagar zona selecionada"
_DELETE_KEYS = {127, 255, 65535}

# ── Sinal devolvido pelo teclado ─────────────────────────────────────────────

class _Signal(Enum):
    CONTINUE = "continue"
    SAVE = "save"
    QUIT = "quit"


# ── State objects (frozen, ≤2 vars cada) ─────────────────────────────────────

@dataclass(frozen=True)
class _IdleState:
    """Sem drag em curso. Pode ter um aviso pendente."""
    warning: str | None = None


@dataclass(frozen=True)
class _DrawingState:
    """Drag a criar nova ROI a partir de `start`."""
    start: Point


@dataclass(frozen=True)
class _MovingState:
    """Drag a mover a ROI guardada em `snapshot`."""
    snapshot: RegionOfInterest
    start: Point


@dataclass(frozen=True)
class _ResizingState:
    """Drag a redimensionar a ROI guardada em `snapshot` pelo canto `corner`."""
    snapshot: RegionOfInterest
    corner: int


_DragState = _IdleState | _DrawingState | _MovingState | _ResizingState


# ── Contentor de estado da sessão (2 vars cada) ───────────────────────────────

@dataclass
class _ZoneSelection:
    """Zona atualmente selecionada pelo utilizador (tecla 1-9)."""
    names: list[str]
    index: int | None = None


@dataclass
class _MouseState:
    """Posição atual do rato e operação de drag em curso."""
    position: Point | None = None
    drag: _DragState = field(default_factory=_IdleState)


@dataclass
class _SessionState:
    """Estado completo da sessão: zona selecionada + mouse."""
    selection: _ZoneSelection
    mouse: _MouseState = field(default_factory=_MouseState)


# ── Funções de geometria (puras, sem estado) ─────────────────────────────────

def _get_corners(roi: RegionOfInterest) -> list[Point]:
    """Devolve os 4 cantos no sentido horário: TL, TR, BR, BL."""
    return [
        roi.top_left,
        Point(x=roi.bottom_right.x, y=roi.top_left.y),
        roi.bottom_right,
        Point(x=roi.top_left.x, y=roi.bottom_right.y),
    ]


def _find_corner_at(roi: RegionOfInterest, point: Point) -> int | None:
    """Devolve o índice do canto mais próximo do ponto, ou None."""
    for index, corner in enumerate(_get_corners(roi)):
        if corner.distance_to(point) <= _CORNER_RADIUS:
            return index
    return None


# Mapeamento de canto → (novo TL, novo BR) dado o ponto arrastado
_CORNER_UPDATERS = {
    0: lambda tl, br, p: (p, br),
    1: lambda tl, br, p: (Point(x=tl.x, y=p.y), Point(x=p.x, y=br.y)),
    2: lambda tl, br, p: (tl, p),
    3: lambda tl, br, p: (Point(x=p.x, y=tl.y), Point(x=br.x, y=p.y)),
}


def _apply_corner_resize(
    snapshot: RegionOfInterest, corner: int, point: Point
) -> RegionOfInterest:
    """Cria nova ROI com o canto `corner` movido para `point`."""
    tl, br = _CORNER_UPDATERS[corner](snapshot.top_left, snapshot.bottom_right, point)
    return RegionOfInterest(
        name=snapshot.name,
        top_left=Point(x=min(tl.x, br.x), y=min(tl.y, br.y)),
        bottom_right=Point(x=max(tl.x, br.x), y=max(tl.y, br.y)),
    )


def _apply_move(
    snapshot: RegionOfInterest, drag_start: Point, current: Point
) -> RegionOfInterest:
    """Cria nova ROI deslocada pelo delta do rato."""
    dx = current.x - drag_start.x
    dy = current.y - drag_start.y
    return RegionOfInterest(
        name=snapshot.name,
        top_left=Point(x=snapshot.top_left.x + dx, y=snapshot.top_left.y + dy),
        bottom_right=Point(x=snapshot.bottom_right.x + dx, y=snapshot.bottom_right.y + dy),
    )


def _compute_drawing_roi(name: str, start: Point, end: Point) -> RegionOfInterest:
    """Cria ROI normalizada a partir dos dois pontos do drag."""
    return RegionOfInterest(
        name=name,
        top_left=Point(x=min(start.x, end.x), y=min(start.y, end.y)),
        bottom_right=Point(x=max(start.x, end.x), y=max(start.y, end.y)),
    )


def _has_minimum_size(roi: RegionOfInterest) -> bool:
    return (
        roi.bottom_right.x - roi.top_left.x >= _MIN_ROI_PIXELS
        and roi.bottom_right.y - roi.top_left.y >= _MIN_ROI_PIXELS
    )


# ── Funções de rendering (puras) ─────────────────────────────────────────────

def _zone_color(zone_names: list[str], name: str) -> tuple[int, int, int]:
    index = zone_names.index(name) if name in zone_names else 0
    return _ZONE_COLORS[index % len(_ZONE_COLORS)]


def _draw_roi(
    frame: np.ndarray,
    roi: RegionOfInterest,
    color: tuple[int, int, int],
    selected: bool,
) -> None:
    """Desenha ROI com preenchimento semi-transparente, contorno e label."""
    tl = (roi.top_left.x, roi.top_left.y)
    br = (roi.bottom_right.x, roi.bottom_right.y)

    overlay = frame.copy()
    cv2.rectangle(overlay, tl, br, color, -1)
    cv2.addWeighted(overlay, _FILL_ALPHA, frame, 1 - _FILL_ALPHA, 0, frame)
    cv2.rectangle(frame, tl, br, color, 2 if not selected else 3)

    cv2.putText(frame, roi.name, (tl[0] + 5, tl[1] + 20),
                _FONT, 0.6, color, 2)

    if not selected:
        return
    for corner in _get_corners(roi):
        cv2.circle(frame, (corner.x, corner.y), _CORNER_RADIUS, color, -1)


def _draw_preview(frame: np.ndarray, session: _SessionState) -> None:
    """Desenha o retângulo de preview durante drawing/moving/resizing."""
    current = session.mouse.position
    drag = session.mouse.drag

    if current is None:
        return

    if isinstance(drag, _DrawingState):
        roi = _compute_drawing_roi("preview", drag.start, current)
        cv2.rectangle(frame, (roi.top_left.x, roi.top_left.y),
                      (roi.bottom_right.x, roi.bottom_right.y), (200, 200, 200), 1)
        return

    if isinstance(drag, _MovingState):
        roi = _apply_move(drag.snapshot, drag.start, current)
    elif isinstance(drag, _ResizingState):
        roi = _apply_corner_resize(drag.snapshot, drag.corner, current)
    else:
        return

    color = _zone_color(session.selection.names, roi.name)
    _draw_roi(frame, roi, color, selected=True)


def _draw_ui_overlay(frame: np.ndarray, session: _SessionState) -> None:
    """Mostra zona selecionada e avisos no topo do frame."""
    if session.selection.index is not None:
        zone = session.selection.names[session.selection.index]
        color = _zone_color(session.selection.names, zone)
        cv2.putText(frame, f"Zona: {zone}", (10, 30), _FONT, 0.8, color, 2)

    # O aviso existe apenas no estado idle — aparece quando se tenta guardar sem todas as zonas
    warning = session.mouse.drag.warning if isinstance(session.mouse.drag, _IdleState) else None
    if warning:
        h = frame.shape[0]
        cv2.putText(frame, warning, (10, h - 15), _FONT, 0.6, (0, 0, 255), 2)


def _render(frame: np.ndarray, rois: RoiCollection, session: _SessionState) -> None:
    """Compõe o frame completo: ROIs, preview, UI overlay."""
    selected_name = (
        session.selection.names[session.selection.index]
        if session.selection.index is not None
        else None
    )

    for roi in rois.all():
        color = _zone_color(session.selection.names, roi.name)
        is_selected = roi.name == selected_name
        # Omite a ROI que está a ser editada (o snapshot no estado substitui-a)
        if is_selected and isinstance(session.mouse.drag, (_MovingState, _ResizingState)):
            continue
        _draw_roi(frame, roi, color, selected=is_selected)

    _draw_preview(frame, session)
    _draw_ui_overlay(frame, session)


# ── DrawingSession ────────────────────────────────────────────────────────────

# Mapeamento evento OpenCV → método handler
_MOUSE_HANDLERS = {
    cv2.EVENT_LBUTTONDOWN: "_on_mouse_down",
    cv2.EVENT_MOUSEMOVE: "_on_mouse_move",
    cv2.EVENT_LBUTTONUP: "_on_mouse_up",
}


class _DrawingSession:
    """Gere todo o estado mutável da sessão interativa de ROIs.

    Separa a lógica de interação do loop de câmara (SRP).
    2 variáveis: _rois (dados) e _session (estado de interação).
    """

    def __init__(self, zone_names: list[str], rois: RoiCollection) -> None:
        self._rois = rois
        self._session = _SessionState(selection=_ZoneSelection(names=zone_names))

    # ── API pública ──────────────────────────────────────────────────────────

    @property
    def rois(self) -> RoiCollection:
        return self._rois

    def render(self, frame: np.ndarray) -> None:
        """Delega o rendering ao módulo de funções puras."""
        _render(frame, self._rois, self._session)

    def handle_mouse(self, event: int, x: int, y: int, flags: int, param) -> None:
        handler_name = _MOUSE_HANDLERS.get(event)
        if handler_name is None:
            return
        self._session.mouse.position = Point(x=x, y=y)
        getattr(self, handler_name)(Point(x=x, y=y))

    def handle_key(self, key: int) -> _Signal:
        if key == ord('q'):
            return _Signal.QUIT
        if key == ord('s'):
            return self._try_save()
        if key in _DELETE_KEYS:
            self._delete_selected()
            return _Signal.CONTINUE
        if ord('1') <= key <= ord('9'):
            self._select_zone(key - ord('1'))
            return _Signal.CONTINUE
        return _Signal.CONTINUE

    # ── Mouse handlers ───────────────────────────────────────────────────────

    def _on_mouse_down(self, point: Point) -> None:
        selected_roi = self._selected_roi()
        if selected_roi is None:
            self._start_drawing(point)
            return

        corner = _find_corner_at(selected_roi, point)
        if corner is not None:
            self._start_resizing(selected_roi, corner)
            return

        if selected_roi.contains(point):
            self._start_moving(selected_roi, point)
            return

        self._start_drawing(point)

    def _on_mouse_move(self, point: Point) -> None:
        # position já foi atualizada antes de chamar este método
        pass

    def _on_mouse_up(self, point: Point) -> None:
        drag = self._session.mouse.drag
        if isinstance(drag, _DrawingState):
            self._finish_drawing(point)
        elif isinstance(drag, _MovingState):
            self._finish_moving(point)
        elif isinstance(drag, _ResizingState):
            self._finish_resizing(point)

    # ── Iniciar interações ───────────────────────────────────────────────────

    def _start_drawing(self, point: Point) -> None:
        if self._session.selection.index is None:
            return
        self._session.mouse.drag = _DrawingState(start=point)

    def _start_moving(self, roi: RegionOfInterest, point: Point) -> None:
        self._rois.remove(roi.name)
        self._session.mouse.drag = _MovingState(snapshot=roi, start=point)

    def _start_resizing(self, roi: RegionOfInterest, corner: int) -> None:
        self._rois.remove(roi.name)
        self._session.mouse.drag = _ResizingState(snapshot=roi, corner=corner)

    # ── Terminar interações ──────────────────────────────────────────────────

    def _finish_drawing(self, point: Point) -> None:
        drag = self._session.mouse.drag
        zone_name = self._selected_zone_name()
        if zone_name is None or not isinstance(drag, _DrawingState):
            self._to_idle()
            return
        roi = _compute_drawing_roi(zone_name, drag.start, point)
        if _has_minimum_size(roi):
            self._rois.add(roi)
        self._to_idle()

    def _finish_moving(self, point: Point) -> None:
        drag = self._session.mouse.drag
        if not isinstance(drag, _MovingState):
            self._to_idle()
            return
        self._rois.add(_apply_move(drag.snapshot, drag.start, point))
        self._to_idle()

    def _finish_resizing(self, point: Point) -> None:
        drag = self._session.mouse.drag
        if not isinstance(drag, _ResizingState):
            self._to_idle()
            return
        roi = _apply_corner_resize(drag.snapshot, drag.corner, point)
        if _has_minimum_size(roi):
            self._rois.add(roi)
        else:
            self._rois.add(drag.snapshot)  # restaura original se ficou pequeno demais
        self._to_idle()

    # ── Outros ──────────────────────────────────────────────────────────────

    def _select_zone(self, index: int) -> None:
        if index >= len(self._session.selection.names):
            return
        self._session.selection.index = index
        self._to_idle()

    def _delete_selected(self) -> None:
        name = self._selected_zone_name()
        if name is None:
            return
        self._rois.remove(name)
        self._to_idle()

    def _try_save(self) -> _Signal:
        missing = self._missing_zones()
        if missing:
            self._session.mouse.drag = _IdleState(warning=f"Faltam: {', '.join(missing)}")
            return _Signal.CONTINUE
        return _Signal.SAVE

    def _missing_zones(self) -> list[str]:
        return [
            name for name in self._session.selection.names
            if not self._rois.contains_zone(name)
        ]

    def _selected_zone_name(self) -> str | None:
        index = self._session.selection.index
        if index is None:
            return None
        return self._session.selection.names[index]

    def _selected_roi(self) -> RegionOfInterest | None:
        name = self._selected_zone_name()
        if name is None:
            return None
        return self._rois.get(name)

    def _to_idle(self) -> None:
        self._session.mouse.drag = _IdleState()


# ── RoiDrawer ────────────────────────────────────────────────────────────────

class RoiDrawer:
    """Ferramenta interativa para desenhar ROIs sobre o feed ao vivo da câmara.

    Devolve a RoiCollection atualizada ao guardar, ou None se o utilizador sair.
    """

    def __init__(
        self,
        camera_factory: Callable[[], Camera],
        zone_names: list[str],
    ) -> None:
        self._camera_factory = camera_factory
        self._zone_names = zone_names

    def draw(self, initial_rois: RoiCollection) -> RoiCollection | None:
        """Abre a sessão interativa. Devolve None se o utilizador sair sem guardar."""
        camera = self._camera_factory()
        session = _DrawingSession(self._zone_names, initial_rois)

        cv2.namedWindow(_WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(_WINDOW_NAME, session.handle_mouse)

        try:
            return self._run_loop(camera, session)
        finally:
            camera.release()
            cv2.destroyAllWindows()

    def _run_loop(
        self, camera: Camera, session: _DrawingSession
    ) -> RoiCollection | None:
        while True:
            frame = camera.read_frame()
            if frame is None:
                return None

            session.render(frame)
            cv2.imshow(_WINDOW_NAME, frame)

            signal = session.handle_key(cv2.waitKey(1))
            if signal == _Signal.QUIT:
                return None
            if signal == _Signal.SAVE:
                return session.rois
