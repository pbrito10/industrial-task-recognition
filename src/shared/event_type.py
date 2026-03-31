from enum import Enum


class EventType(Enum):
    """Tipo de evento gerado quando uma mão entra ou sai de uma zona.

    Enum em vez de string pelas mesmas razões que HandSide — um conjunto
    fixo e conhecido de valores deve ser um tipo, não strings livres.

    Cada ENTER deve ter um EXIT correspondente, exceto se a sessão
    terminar com a mão ainda dentro da zona.
    """

    ENTER = "ENTER"
    EXIT  = "EXIT"
