# TODO: implementar
#
# Rastreia ciclos completos de montagem.
#
# Responsabilidade: a partir dos TaskEvents emitidos pela TaskStateMachine,
# detetar quando um ciclo completo foi realizado e registá-lo.
#
# O que é um ciclo:
#   A sequência completa de todas as zonas definidas, pela ordem configurada.
#   Ex: Zona A → Zona B → Zona C → Zona D (caixa de saída)
#   O ciclo termina quando a última zona (saída) é completada.
#
# Lógica:
#   - Mantém um registo das tarefas completadas no ciclo atual
#   - Quando a tarefa da zona de saída é completada → ciclo fechado
#   - Regista o ciclo com todos os seus tempos e emite evento de ciclo
#   - Reinicia para o próximo ciclo
#
# Nota: a ordem das zonas que define um ciclo é configurável em
# settings.yaml — não está hardcoded aqui.
