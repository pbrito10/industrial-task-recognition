# Menu principal da aplicação.
#
# Responsabilidade: apresentar as opções ao utilizador no terminal,
# ler a sua escolha e delegar a execução à opção correspondente.
#
# Lógica:
#   - Tem uma lista de opções disponíveis (cada uma é um objeto com nome e ação)
#   - Entra num loop: mostra o menu → lê input → executa a opção → repete
#   - O loop termina quando o utilizador escolhe "Sair"
#
# Exemplo de output no terminal:
#   === Sistema de Reconhecimento Industrial ===
#   1. Testar câmara
#   2. Definir ROIs
#   3. Correr programa
#   0. Sair
#   Escolha: _
#
# Princípio: este ficheiro não sabe O QUE cada opção faz,
# só sabe que as tem de mostrar e invocar. (Open/Closed)
