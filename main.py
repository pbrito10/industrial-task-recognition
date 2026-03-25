# Ponto de entrada da aplicação — equivalente ao main() em C/Java.
# Responsabilidade única: inicializar e arrancar o menu.
# Não contém lógica de negócio.

from src.cli.menu import Menu


def main() -> None:
    menu = Menu()
    menu.run()


if __name__ == "__main__":
    main()
