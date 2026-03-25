# Opção "Testar câmara".
#
# Responsabilidade: abrir a câmara USB e mostrar o feed em tempo real
# numa janela OpenCV, para o utilizador verificar que está a funcionar
# e enquadrar a bancada antes de definir ROIs ou correr o programa.
#
# Lógica:
#   - Abre a câmara (índice configurável no settings.yaml)
#   - Mostra frames em loop numa janela "Teste de Câmara"
#   - Escreve no canto o FPS atual e resolução
#   - Termina quando o utilizador prime 'q'
#
# Não guarda nada. Não tem efeitos secundários.
