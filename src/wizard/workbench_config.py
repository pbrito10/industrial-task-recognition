from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WorkbenchConfig:
    """Configuração de uma bancada de montagem: zonas, sequência e regras.

    Cada perfil é guardado em config/workbenches/<nome>.json.
    O perfil activo é indicado por config/active_workbench.txt.
    """

    zones:            list[str]
    two_hands_zones:  list[str]
    cycle_zone_order: list[str]
    start_zone:       str
    exit_zone:        str

    # ------------------------------------------------------------------
    # Carregar / guardar um perfil
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: Path) -> WorkbenchConfig:
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            zones=data["zones"],
            two_hands_zones=data["two_hands_zones"],
            cycle_zone_order=data["cycle_zone_order"],
            start_zone=data["start_zone"],
            exit_zone=data["exit_zone"],
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "zones":            self.zones,
            "two_hands_zones":  self.two_hands_zones,
            "cycle_zone_order": self.cycle_zone_order,
            "start_zone":       self.start_zone,
            "exit_zone":        self.exit_zone,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Gestão de perfis (pasta + ficheiro activo)
    # ------------------------------------------------------------------

    @staticmethod
    def profile_path(workbenches_dir: Path, name: str) -> Path:
        return workbenches_dir / f"{name}.json"

    @staticmethod
    def list_profiles(workbenches_dir: Path) -> list[str]:
        """Devolve os nomes dos perfis existentes, ordenados alfabeticamente."""
        if not workbenches_dir.exists():
            return []
        return sorted(p.stem for p in workbenches_dir.glob("*.json"))

    @staticmethod
    def active_name(active_path: Path) -> str | None:
        """Devolve o nome do perfil activo, ou None se não estiver definido."""
        if not active_path.exists():
            return None
        return active_path.read_text(encoding="utf-8").strip() or None

    @staticmethod
    def set_active(name: str, active_path: Path) -> None:
        active_path.parent.mkdir(parents=True, exist_ok=True)
        active_path.write_text(name, encoding="utf-8")

    @classmethod
    def load_active(cls, workbenches_dir: Path, active_path: Path) -> WorkbenchConfig:
        """Carrega o perfil activo. Lança erro claro se nada estiver configurado."""
        name = cls.active_name(active_path)
        if name is None:
            raise FileNotFoundError(
                "Nenhum perfil activo. Usa 'Configurar Bancada' para criar e activar um perfil."
            )
        path = cls.profile_path(workbenches_dir, name)
        if not path.exists():
            raise FileNotFoundError(
                f"Perfil '{name}' não encontrado. Usa 'Configurar Bancada' para reconfigurar."
            )
        return cls.load(path)
