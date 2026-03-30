# TODO: implementar
#
# Escreve eventos de zona num ficheiro CSV em tempo real durante a sessão.
#
# Responsabilidade: receber ZoneEvents e persistir cada um como uma linha
# no CSV imediatamente, sem esperar pelo fim da sessão.
#
# Isto permite debugar enquanto o programa corre — podes abrir o CSV
# num editor ou fazer `tail -f` no terminal e ver os eventos a aparecer.
#
# Colunas escritas (por esta ordem):
#   timestamp_iso | relative_time_s | event_type | zone | hand | x_px | y_px | confidence | frame_idx | was_forced
#
# A coluna was_forced permite identificar no CSV:
#   - was_forced=False → evento real (mão entrou/saiu fisicamente)
#   - was_forced=True  → evento forçado por timeout (pausa ou falha de deteção)
#
# Conversões feitas ao escrever (ZoneEvent → CSV):
#   - timestamp     : datetime  → str ISO 8601 com ms (ex: "2026-03-25T14:30:01.123")
#   - relative_time : timedelta → float em segundos   (ex: 12.45)
#   - event_type    : EventType → str do enum         (ex: "ENTER")
#   - hand          : HandSide  → str do enum         (ex: "left")
#   - position      : Point     → dois campos x_px e y_px separados
#                                 (o CSV é plano, não tem objetos aninhados)
#   - confidence    : Confidence → float              (ex: 0.87)
#   - was_forced    : bool       → "true" / "false"
#
# Lógica:
#   - No __init__, cria o ficheiro CSV e escreve o cabeçalho
#   - Nome do ficheiro inclui o timestamp de início da sessão
#     (ex: "events_2026-03-25_14h30.csv") para não sobrescrever sessões anteriores
#   - Ficheiro guardado na pasta configurada em settings.yaml
#   - log(event: ZoneEvent): escreve uma linha e faz flush imediato
#     (o flush garante que a linha aparece no ficheiro mesmo se o programa
#     fechar inesperadamente — sem flush o Python pode perder a linha num crash)
#   - close(): fecha o ficheiro de forma limpa
#
# Implementado como context manager (with EventLogger(...) as logger:)
# para garantir que o ficheiro é sempre fechado mesmo em caso de erro.
