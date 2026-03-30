# TODO: implementar
#
# Exporta os dados da sessão para um ficheiro Excel.
#
# Responsabilidade: converter os eventos e métricas da sessão num
# ficheiro .xlsx estruturado, legível e partilhável.
#
# Estrutura do Excel gerado (uma folha por tipo de dados):
#
#   Folha "Resumo":
#     | Sessão | Data | Duração total | Ciclos completos |
#     | Tempo médio ciclo | Desvio padrão ciclo |
#     | % Tempo produtivo | % Tempo transição | % Tempo interrupção |
#     | Zona gargalo |
#
#   Folha "Métricas por Zona":
#     | Zona | Mínimo | Médio | Máximo | Desvio Padrão | Ocorrências |
#     Inclui apenas TaskEvents com was_forced=False.
#     A zona gargalo (maior tempo médio) é destacada a cor.
#
#   Folha "Ciclos":
#     | Nº Ciclo | Início | Fim | Duração Total |
#     Uma linha por ciclo completo — base para análise de evolução.
#
#   Folha "Eventos":
#     | Ciclo | Zona | Início | Fim | Duração | Forçado |
#     Uma linha por TaskEvent — registo completo incluindo interrupções.
#     A coluna "Forçado" indica was_forced para identificar interrupções.
#
# Lógica:
#   - Recebe o snapshot final de métricas e todos os TaskEvents
#   - Separa automaticamente was_forced=True para a coluna "Forçado"
#   - Usa pandas para construir os DataFrames
#   - Usa openpyxl para formatação (cabeçalhos a negrito, gargalo a cor)
#   - Nome do ficheiro inclui timestamp: "sessao_2026-03-25_14h30.xlsx"
#   - Guardado em output/ (criada automaticamente se não existir)
