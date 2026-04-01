from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WorkbenchConfig:
    """Configuração de uma bancada de montagem: zonas, sequência e regras.

    Lida a partir de workbench.json quando existe; recai no settings.yaml
    para retrocompatibilidade com instalações que ainda não correram o wizard.
    """

    zones:            list[str]
    two_hands_zones:  list[str]
    cycle_zone_order: list[str]
    start_zone:       str
    exit_zone:        str

    @classmethod
    def load(cls, workbench_path: Path, settings_path: Path) -> WorkbenchConfig:
        if workbench_path.exists():
            data = json.loads(workbench_path.read_text(encoding="utf-8"))
            return cls(
                zones=data["zones"],
                two_hands_zones=data["two_hands_zones"],
                cycle_zone_order=data["cycle_zone_order"],
                start_zone=data["start_zone"],
                exit_zone=data["exit_zone"],
            )

        # Fallback: lê a secção tracking do settings.yaml
        import yaml
        with open(settings_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        tracking = config["tracking"]
        return cls(
            zones=tracking["zones"],
            two_hands_zones=tracking.get("two_hands_zones", []),
            cycle_zone_order=tracking.get("cycle_zone_order", []),
            start_zone=tracking.get("start_zone", ""),
            exit_zone=tracking.get("exit_zone", ""),
        )

    def save(self, workbench_path: Path) -> None:
        workbench_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "zones":            self.zones,
            "two_hands_zones":  self.two_hands_zones,
            "cycle_zone_order": self.cycle_zone_order,
            "start_zone":       self.start_zone,
            "exit_zone":        self.exit_zone,
        }
        workbench_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
