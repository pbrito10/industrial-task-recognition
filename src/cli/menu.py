from __future__ import annotations

from typing import Protocol


class MenuOption(Protocol):
    """Contrato que cada opção do menu tem de cumprir.

    O Menu não sabe o que cada opção faz — só sabe que tem um nome
    e que se pode executar. Adicionar uma nova opção não exige alterar Menu.
    """

    @property
    def name(self) -> str: ...

    def run(self) -> None: ...


class Menu:
    """Loop principal do menu — apresenta opções, lê escolha e delega execução.

    Recebe as opções por injeção para não depender de implementações concretas (DIP).
    """

    def __init__(self, options: list[MenuOption]) -> None:
        # Dict por índice para lookup O(1) e sem else nos branches
        self._options: dict[int, MenuOption] = {
            i + 1: option for i, option in enumerate(options)
        }

    def run(self) -> None:
        """Loop até o utilizador escolher sair (0)."""
        while True:
            self._show()
            choice = self._read_choice()
            if choice == 0:
                print("A sair...")
                return
            self._execute(choice)

    def _show(self) -> None:
        print("\n=== Sistema de Reconhecimento Industrial ===")
        for index, option in self._options.items():
            print(f"  {index}. {option.name}")
        print("  0. Sair")

    def _read_choice(self) -> int:
        """Lê a escolha do utilizador — devolve -1 se não for um número válido."""
        raw = input("Escolha: ").strip()
        if not raw.isdigit():
            return -1
        return int(raw)

    def _execute(self, choice: int) -> None:
        option = self._options.get(choice)
        if option is None:
            print(f"Opção '{choice}' não existe.")
            return
        option.run()
