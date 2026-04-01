from __future__ import annotations

from pathlib import Path
from typing import Callable

from src.roi.roi_collection import RoiCollection
from src.wizard.workbench_config import WorkbenchConfig


class SetupWizard:
    """Gestão de perfis de bancada e configuração dos 6 passos.

    Menu principal:
      1. Ativar perfil existente
      2. Criar novo perfil
      3. Editar perfil ativo
      4. Apagar perfil

    Os 6 passos de configuração correm no terminal, exceto o passo 2
    (ROIs) que abre uma janela OpenCV.
    """

    def __init__(
        self,
        workbenches_dir: Path,
        active_path:     Path,
        camera_config:   dict,
    ) -> None:
        self._workbenches_dir = workbenches_dir
        self._active_path     = active_path
        self._camera_config   = camera_config

    # ------------------------------------------------------------------
    # Menu principal
    # ------------------------------------------------------------------

    def run(self) -> None:
        while True:
            active = WorkbenchConfig.active_name(self._active_path)
            profiles = WorkbenchConfig.list_profiles(self._workbenches_dir)

            print("\n=== Configurar Bancada ===")
            print(f"  Perfil ativo: {active or '(nenhum)'}\n")
            print("  1. Ativar perfil existente")
            print("  2. Criar novo perfil")
            print("  3. Editar perfil ativo")
            print("  4. Apagar perfil")
            print("  0. Voltar")

            raw = input("\n  > ").strip()

            if raw == "0":
                break
            elif raw == "1":
                self._menu_activate(profiles, active)
            elif raw == "2":
                self._menu_create(profiles)
            elif raw == "3":
                self._menu_edit(active)
            elif raw == "4":
                self._menu_delete(profiles, active)
            else:
                print("  Opção inválida.")

    # ------------------------------------------------------------------
    # Acções do menu
    # ------------------------------------------------------------------

    def _menu_activate(self, profiles: list[str], active: str | None) -> None:
        if not profiles:
            print("\n  Não existem perfis. Cria um primeiro (opção 2).")
            return

        print("\n  Perfis disponíveis:")
        for i, name in enumerate(profiles, 1):
            marker = " (ativo)" if name == active else ""
            print(f"    {i}. {name}{marker}")

        raw = input("\n  Número do perfil a ativar (Enter para cancelar): ").strip()
        if not raw:
            return

        idx = self._parse_index(raw, profiles)
        if idx is None:
            return

        WorkbenchConfig.set_active(profiles[idx], self._active_path)
        print(f"\n  Perfil '{profiles[idx]}' ativado.")

    def _menu_create(self, profiles: list[str]) -> None:
        print("\n  Nome do novo perfil (Enter para cancelar): ", end="")
        name = input().strip()
        if not name:
            return

        if name in profiles:
            print(f"  Já existe um perfil com o nome '{name}'.")
            return

        path = WorkbenchConfig.profile_path(self._workbenches_dir, name)
        self._run_steps(WorkbenchConfig([], [], [], "", ""), path, name)

        WorkbenchConfig.set_active(name, self._active_path)
        print(f"\n  Perfil '{name}' criado e ativado.")

    def _menu_edit(self, active: str | None) -> None:
        if active is None:
            print("\n  Nenhum perfil ativo. Ativa ou cria um primeiro.")
            return

        path = WorkbenchConfig.profile_path(self._workbenches_dir, active)
        current = WorkbenchConfig.load(path)
        self._run_steps(current, path, active)
        print(f"\n  Perfil '{active}' atualizado.")

    def _menu_delete(self, profiles: list[str], active: str | None) -> None:
        deletable = [p for p in profiles if p != active]

        if not deletable:
            print("\n  Não há perfis para apagar (não é possível apagar o perfil ativo).")
            return

        print("\n  Perfis que podem ser apagados:")
        for i, name in enumerate(deletable, 1):
            print(f"    {i}. {name}")

        raw = input("\n  Número do perfil a apagar (Enter para cancelar): ").strip()
        if not raw:
            return

        idx = self._parse_index(raw, deletable)
        if idx is None:
            return

        name = deletable[idx]
        confirm = input(f"  Tens a certeza que queres apagar '{name}'? (s/N): ").strip().lower()
        if confirm != "s":
            print("  Cancelado.")
            return

        WorkbenchConfig.profile_path(self._workbenches_dir, name).unlink()
        # Apaga também as ROIs associadas, se existirem
        roi_file = WorkbenchConfig.roi_path(self._workbenches_dir, name)
        if roi_file.exists():
            roi_file.unlink()
        print(f"  Perfil '{name}' apagado.")

    # ------------------------------------------------------------------
    # Os 6 passos de configuração
    # ------------------------------------------------------------------

    def _run_steps(self, current: WorkbenchConfig, save_path: Path, profile_name: str) -> WorkbenchConfig:
        print("\nPodes pressionar Enter em qualquer passo para manter o valor atual.")

        roi_path = WorkbenchConfig.roi_path(self._workbenches_dir, profile_name)

        zones           = self._step_zones(current.zones)
        rois            = self._step_draw_rois(zones, roi_path)
        two_hands_zones = self._step_two_hands(zones, current.two_hands_zones)
        cycle_order     = self._step_sequence(zones, current.cycle_zone_order)
        start_zone      = self._step_start_zone(zones, current.start_zone)
        exit_zone       = self._step_exit_zone(zones, current.exit_zone)

        config = WorkbenchConfig(zones, two_hands_zones, cycle_order, start_zone, exit_zone)
        config.save(save_path)

        if rois is not None:
            from src.roi.json_roi_repository import JsonRoiRepository
            JsonRoiRepository(path=roi_path).save(rois)

        return config

    # ------------------------------------------------------------------
    # Passo 1 — Zonas
    # ------------------------------------------------------------------

    def _step_zones(self, current: list[str]) -> list[str]:
        zones = list(current)
        print("\nPasso 1/6 — Zonas")
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

    def _step_draw_rois(self, zones: list[str], roi_path: Path) -> RoiCollection | None:
        from src.roi.json_roi_repository import JsonRoiRepository
        from src.roi.roi_drawer import RoiDrawer
        from src.video.camera import Camera

        print("\nPasso 2/6 — Desenhar ROIs")
        print("  Abre o editor visual. 's' para guardar, 'q' para sair sem guardar.")
        input("  Pressiona Enter para abrir a câmera...")

        camera_factory: Callable = lambda: Camera(
            index=self._camera_config["index"],
            width=self._camera_config["width"],
            height=self._camera_config["height"],
        )

        result = RoiDrawer(
            camera_factory=camera_factory,
            zone_names=zones,
        ).draw(JsonRoiRepository(path=roi_path).load())

        if result is None:
            print("  Saiu sem guardar — ROIs anteriores mantidas.")
        return result

    # ------------------------------------------------------------------
    # Passo 3 — Two-hands zones
    # ------------------------------------------------------------------

    def _step_two_hands(self, zones: list[str], current: list[str]) -> list[str]:
        selected = set(current) & set(zones)
        print("\nPasso 3/6 — Zonas com duas mãos")
        print("  Digita o número para ativar/desativar. Enter para continuar.\n")

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
        sequence = [z for z in current if z in zones]
        print("\nPasso 4/6 — Sequência do ciclo")
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
    # Passo 5 — Zona de início
    # ------------------------------------------------------------------

    def _step_start_zone(self, zones: list[str], current: str) -> str:
        current_valid = current if current in zones else ""
        print("\nPasso 5/6 — Zona de início")
        print("  Escolhe a zona que inicia o ciclo.")
        print("  Tarefas antes desta zona são descartadas. Enter para manter a atual.\n")
        return self._pick_zone(zones, current_valid)

    # ------------------------------------------------------------------
    # Passo 6 — Zona de saída
    # ------------------------------------------------------------------

    def _step_exit_zone(self, zones: list[str], current: str) -> str:
        current_valid = current if current in zones else ""
        print("\nPasso 6/6 — Zona de saída")
        print("  Escolhe a zona que fecha o ciclo. Enter para manter a atual.\n")
        return self._pick_zone(zones, current_valid, required_msg="É necessário escolher uma zona de saída.")

    # ------------------------------------------------------------------
    # Utilitário partilhado — escolher uma zona da lista
    # ------------------------------------------------------------------

    def _pick_zone(
        self,
        zones: list[str],
        current: str,
        required_msg: str = "É necessário escolher uma zona.",
    ) -> str:
        while True:
            for i, name in enumerate(zones, 1):
                marker = " (atual)" if name == current else ""
                print(f"  {i}. {name}{marker}")

            raw = input("\n  > ").strip()

            if raw == "":
                if current:
                    return current
                print(f"  {required_msg}")
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
