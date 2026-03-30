# TODO: implementar
#
# Escreve os dados de métricas para o dashboard Streamlit.
#
# Responsabilidade: atualizar os dados que o dashboard Streamlit lê,
# de forma que a interface reflita o estado atual da sessão.
#
# Como o Streamlit corre num processo separado, a comunicação é feita
# através de um ficheiro JSON partilhado (dashboard/data/metrics.json).
#
# Lógica:
#   - write(metrics_snapshot: dict) serializa o snapshot para JSON.
#     O snapshot inclui todas as métricas do MetricsCalculator:
#       - por tarefa: min, médio, máx, desvio padrão, ocorrências
#       - por ciclo: min, médio, máx, desvio padrão, total de ciclos
#       - global: % tempo produtivo, zona gargalo
#   - Escreve atomicamente em dashboard/data/metrics.json:
#       escreve num ficheiro temporário e faz rename, para evitar que
#       o Streamlit leia o ficheiro a meio de ser escrito (race condition)
#   - O Streamlit faz polling deste ficheiro com st.rerun() e atualiza
#     automaticamente
#
# Frequência de escrita: configurável em settings.yaml
# (dashboard.refresh_seconds). Não faz sentido escrever mais rápido
# do que o Streamlit consegue ler — por defeito 1 segundo.
