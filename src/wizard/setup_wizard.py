from __future__ import annotations

from pathlib import Path
from typing import Callable

from src.roi.roi_collection import RoiCollection
from src.wizard.workbench_config import WorkbenchConfig


class SetupWizard:
    """Guia o utilizador pela configuração completa de uma bancada em 5 passos.

    Os passos 1, 3, 4 e 5 correm no terminal.
    O passo 2 (ROIs) abre uma janela OpenCV — igual ao modo "Definir ROIs" existente.
    """

    def __init__(
        self,
        workbench_path: Path,
        roi_path:       Path,
        settings_path:  Path,
        camera_config:  dict,
    ) -> None:
        self._workbench_path = workbench_path
        self._roi_path       = roi_path
        self._settings_path  = settings_path
        self._camera_config  = camera_config

    def run(self) -> None:
        print("\n=== Configurar Bancada ===")
        print("Podes pressionar Enter em qualquer passo para manter o valor actual.\n")

        current = WorkbenchConfig.load(self._workbench_path, self._settings_path)

        zones           = self._step_zones(current.zones)
        rois            = self._step_draw_rois(zones)
        two_hands_zones = self._step_two_hands(zones, current.two_hands_zones)
        cycle_order     = self._step_sequence(zones, current.cycle_zone_order)
        exit_zone       = self._step_exit_zone(zones, current.exit_zone)

        WorkbenchConfig(zones, two_hands_zones, cycle_order, exit_zone).save(self._workbench_path)

        if rois is not None:
            from src.roi.json_roi_repository import JsonRoiRepository
            JsonRoiRepository(path=self._roi_path).save(rois)

        print("\nConfiguração guardada.")

    # ------------------------------------------------------------------
    # Passo 1 — Zonas
    # ------------------------------------------------------------------

    def _step_zones(self, current: list[str]) -> list[str]:
        zones = list(current)
        print("Passo 1/5 — Zonas")
        self._print_zones(zones)
        print("  [a <nome>] adicionar   [r <número>] remover   [Enter] continuar\n")

        while True:
            raw = input("  > ").strip()

            if raw == "":
                if not zones:
                    print("  É preciso pelo menos uma zona.")
                    continue
                break

            if raw.lower().startswith("a "):
                name = raw[2:].strip()
                if not name:
                    print("  Nome inválido.")
                elif name in zones:
                    print(f"  '{name}' já existe.")
                else:
                    zones.append(name)
                    self._print_zones(zones)

            elif raw.lower().startswith("r "):
                idx = self._parse_index(raw[2:], zones)
                if idx is None:
                    continue
                if len(zones) == 1:
                    print("  Não é possível remover a única zona.")
                else:
                    removed = zones.pop(idx)
                    print(f"  '{removed}' removida.")
                    self._print_zones(zones)
            else:
                print("  Comando não reconhecido.")

        return zones

    # ------------------------------------------------------------------
    # Passo 2 — Desenhar ROIs
    # ------------------------------------------------------------------

    def _step_draw_rois(self, zones: list[str]) -> RoiCollection | None:
        from src.roi.json_roi_repository import JsonRoiRepository
        from src.roi.roi_drawer import RoiDrawer
        from src.video.camera import Camera

        print("\nPasso 2/5 — Desenhar ROIs")
        print("  Abre o editor visual. 's' para guardar, 'q' para sair sem guardar.")
        input("  Pressiona Enter para abrir a câmara...")

        camera_factory: Callable = lambda: Camera(
            index=self._camera_config["index"],
            width=self._camera_config["width"],
            height=self._camera_config["height"],
        )

        result = RoiDrawer(
            camera_factory=camera_factory,
            zone_names=zones,
        ).draw(JsonRoiRepository(path=self._roi_path).load())

        if result is None:
            print("  Saiu sem guardar — ROIs anteriores mantidas.")
        return result

    # ------------------------------------------------------------------
    # Passo 3 — Two-hands zones
    # ------------------------------------------------------------------

    def _step_two_hands(self, zones: list[str], current: list[str]) -> list[str]:
        selected = set(current) & set(zones)  # descarta zonas que já não existem
        print("\nPasso 3/5 — Zonas com duas mãos")
        print("  Digita o número para activar/desactivar. Enter para continuar.\n")

        while True:
            self._print_toggles(zones, selected)
            raw = input("  > ").strip()

            if raw == "":
                break

            idx = self._parse_index(raw, zones)
            if idx is None:
                continue

            name = zones[idx]
            if name in selected:
                selected.discard(name)
            else:
                selected.add(name)

        return [z for z in zones if z in selected]

    # ------------------------------------------------------------------
    # Passo 4 — Sequência do ciclo
    # ------------------------------------------------------------------

    def _step_sequence(self, zones: list[str], current: list[str]) -> list[str]:
        # Remove zonas que já não existem mas mantém repetições válidas
        sequence = [z for z in current if z in zones]
        print("\nPasso 4/5 — Sequência do ciclo")
        print("  [número] adicionar zona   [x] remover última   [Enter] continuar\n")

        while True:
            self._print_sequence(zones, sequence)
            raw = input("  > ").strip()

            if raw == "":
                break

            if raw.lower() == "x":
                if sequence:
                    removed = sequence.pop()
                    print(f"  '{removed}' removida da sequência.")
                else:
                    print("  Sequência já está vazia.")
                continue

            idx = self._parse_index(raw, zones)
            if idx is None:
                continue

            sequence.append(zones[idx])

        return sequence

    # ------------------------------------------------------------------
    # Passo 5 — Zona de saída
    # ------------------------------------------------------------------

    def _step_exit_zone(self, zones: list[str], current: str) -> str:
        # Se a zona de saída actual já não existe, limpa
        current_valid = current if current in zones else ""
        print("\nPasso 5/5 — Zona de saída")
        print("  Escolhe a zona que fecha o ciclo. Enter para manter a actual.\n")

        while True:
            for i, name in enumerate(zones, 1):
                marker = " (actual)" if name == current_valid else ""
                print(f"  {i}. {name}{marker}")

            raw = input("\n  > ").strip()

            if raw == "":
                if current_valid:
                    return current_valid
                print("  É necessário escolher uma zona de saída.")
                continue

            idx = self._parse_index(raw, zones)
            if idx is None:
                continue

            return zones[idx]

    # ------------------------------------------------------------------
    # Utilitários de apresentação e parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _print_zones(zones: list[str]) -> None:
        if not zones:
            print("  (nenhuma zona definida)")
            return
        for i, name in enumerate(zones, 1):
            print(f"  {i}. {name}")

    @staticmethod
    def _print_toggles(zones: list[str], selected: set[str]) -> None:
        for i, name in enumerate(zones, 1):
            mark = "x" if name in selected else " "
            print(f"  {i}. [{mark}] {name}")

    @staticmethod
    def _print_sequence(zones: list[str], sequence: list[str]) -> None:
        seq_str = " → ".join(sequence) if sequence else "(vazia)"
        print(f"  Sequência: {seq_str}")
        print("  Zonas disponíveis:")
        for i, name in enumerate(zones, 1):
            print(f"    {i}. {name}")

    @staticmethod
    def _parse_index(raw: str, items: list) -> int | None:
        try:
            idx = int(raw) - 1
        except ValueError:
            print("  Número inválido.")
            return None
        if not (0 <= idx < len(items)):
            print(f"  Escolhe um número entre 1 e {len(items)}.")
            return None
        return idx
