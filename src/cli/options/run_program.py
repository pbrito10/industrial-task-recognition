# Opção "Correr programa".
#
# Responsabilidade: orquestrar a pipeline completa de análise.
#
# Lógica:
#   1. Verifica se existem ROIs definidas — se não, avisa e aborta
#   2. Carrega as ROIs guardadas e as configurações
#   3. Inicializa o detector (YoloDetector ou MockDetector consoante config)
#   4. Arranca o VideoProcessor que processa cada frame:
#        frame → deteção de mãos → classificação de zona → task tracker → métricas
#   5. Em paralelo, o DashboardWriter atualiza os dados do Streamlit
#   6. Quando termina (tecla 'q' ou fim do vídeo), exporta para Excel
#
# Este ficheiro é o "maestro": sabe a ordem das operações mas
# delega tudo às classes responsáveis. Não contém lógica de visão
# computacional nem de métricas.
