# ═══════════════════════════════════════════════════════════════════════════════
# Ponto de entrada da aplicação.
#
# Este ficheiro tem duas responsabilidades:
#   1. Mostrar o menu e reagir à escolha do utilizador
#   2. Montar os blocos (processos) certos para cada modo
#
# ── Arquitetura de blocos ────────────────────────────────────────────────────
#
#   Cada bloco é um ficheiro independente com uma função run().
#   Os blocos comunicam entre si através de Queues.
#   O stop_event é uma flag partilhada — qualquer bloco pode ativá-la
#   para sinalizar que todos devem parar.
#
#   MODO "Testar Câmara":
#     camera.py → frame_queue → detector.py → detection_queue → display.py
#
#   MODO "Definir ROIs":
#     Corre no processo principal (não usa processos separados).
#     O RoiDrawer abre a câmara diretamente e gere a sessão interativa.
#
#   MODO "Correr Programa":
#     camera.py → frame_queue → detector.py → detection_queue → pipeline.py
#
# ── O que flui entre blocos ──────────────────────────────────────────────────
#
#   frame_queue     : frame individual em RGB  (numpy array)
#   detection_queue : (frame RGB, lista de HandDetection)
#
# ═══════════════════════════════════════════════════════════════════════════════

import time
from multiprocessing import Event, Process, Queue
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).parent / "config" / "settings.yaml"
_ROI_PATH    = Path(__file__).parent / "config" / "rois.json"


# ── Wrappers dos processos ────────────────────────────────────────────────────
# Cada função importa o seu módulo e chama run().
# Os imports ficam aqui dentro porque cada processo filho começa do zero
# e deve importar só o que precisa.


def run_camera(frame_queue, stop_event, config):
    import camera
    camera.run(frame_queue, stop_event, config)


def run_detector(frame_queue, detection_queue, stop_event, config):
    import detector
    detector.run(frame_queue, detection_queue, stop_event, config)


def run_display(detection_queue, stop_event):
    import display
    display.run(detection_queue, stop_event)


def run_pipeline(detection_queue, stop_event, config, roi_path):
    import pipeline
    pipeline.run(detection_queue, stop_event, config, roi_path)


# ── Função auxiliar de lançamento ────────────────────────────────────────────

def _launch(stop_event, **processos):
    """Arranca os processos, aguarda e trata paragem (Ctrl+C ou 'q' na janela)."""
    print("A arrancar processos...")
    for nome, processo in processos.items():
        processo.start()
        time.sleep(0.5)
        print(f"  [{nome}] iniciado (PID {processo.pid})")

    print("A correr. Carrega 'q' na janela para parar.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCtrl+C — a parar...")
        stop_event.set()

    for processo in processos.values():
        processo.join(timeout=3)
        if processo.is_alive():
            processo.terminate()

    print("Processos terminados.")


# ── Modos de funcionamento ────────────────────────────────────────────────────

def testar_camera(config):
    """
    Abre a câmara e mostra o feed com keypoints das mãos.
    Útil para verificar se a câmara e o MediaPipe estão a funcionar.

    Blocos: camera → detector → display
    """
    frame_queue     = Queue(maxsize=2)
    detection_queue = Queue(maxsize=5)
    stop_event      = Event()

    _launch(
        stop_event,
        camera   = Process(target=run_camera,   name="camera",
                           args=(frame_queue, stop_event, config)),
        detector = Process(target=run_detector, name="detector",
                           args=(frame_queue, detection_queue, stop_event, config)),
        display  = Process(target=run_display,  name="display",
                           args=(detection_queue, stop_event)),
    )


def definir_rois(config):
    """
    Abre a câmara e permite desenhar as zonas de trabalho (ROIs) com o rato.
    Corre no processo principal — não precisa de processos separados porque
    é uma sessão interativa com início e fim definidos.

    Controlos: 1-9 selecionar zona | Del apagar | s guardar | q sair
    """
    from src.roi.json_roi_repository import JsonRoiRepository
    from src.roi.roi_drawer import RoiDrawer
    from src.video.camera import Camera

    camera_factory = lambda: Camera(
        index=config["camera"]["index"],
        width=config["camera"]["width"],
        height=config["camera"]["height"],
    )

    repository = JsonRoiRepository(path=_ROI_PATH)
    drawer     = RoiDrawer(
        camera_factory=camera_factory,
        zone_names=config["tracking"]["zones"],
    )

    result = drawer.draw(repository.load())

    if result is None:
        print("Saiu sem guardar — ROIs anteriores mantidas.")
        return

    repository.save(result)
    print(f"ROIs guardadas: {len(result.all())} zonas definidas.")


def correr_programa(config):
    """
    Corre o pipeline completo de análise.
    Mostra o feed com ROIs e keypoints. Futuramente incluirá tracking e métricas.

    Blocos: camera → detector → pipeline
    """
    from src.roi.json_roi_repository import JsonRoiRepository

    if not JsonRoiRepository(path=_ROI_PATH).load().all():
        print("Nenhuma ROI definida. Usa a opção 2 primeiro.")
        return

    frame_queue     = Queue(maxsize=2)
    detection_queue = Queue(maxsize=5)
    stop_event      = Event()

    _launch(
        stop_event,
        camera   = Process(target=run_camera,   name="camera",
                           args=(frame_queue, stop_event, config)),
        detector = Process(target=run_detector, name="detector",
                           args=(frame_queue, detection_queue, stop_event, config)),
        pipeline = Process(target=run_pipeline, name="pipeline",
                           args=(detection_queue, stop_event, config, str(_ROI_PATH))),
    )


# ── Menu ──────────────────────────────────────────────────────────────────────

_OPCOES = {
    "1": ("Testar câmara",   testar_camera),
    "2": ("Definir ROIs",    definir_rois),
    "3": ("Correr programa", correr_programa),
}


def main():
    with open(_CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    while True:
        print("\n=== Sistema de Reconhecimento Industrial ===")
        for key, (nome, _) in _OPCOES.items():
            print(f"  {key}. {nome}")
        print("  0. Sair")

        escolha = input("Escolha: ").strip()

        if escolha == "0":
            print("A sair...")
            break

        if escolha not in _OPCOES:
            print("Opção inválida.")
            continue

        _, funcao = _OPCOES[escolha]
        funcao(config)


# Guarda obrigatória para multiprocessing.
# Sem isto, cada processo filho tentaria re-executar o main() ao arrancar,
# criando um ciclo infinito de processos.
if __name__ == "__main__":
    main()
