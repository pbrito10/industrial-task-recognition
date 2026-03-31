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
#     capture_process.py → frame_queue → detection_process.py → detection_queue → display_process.py
#
#   MODO "Definir ROIs":
#     Corre no processo principal (não usa processos separados).
#     O RoiDrawer abre a câmara diretamente e gere a sessão interativa.
#
#   MODO "Correr Programa":
#     capture_process.py → frame_queue → detection_process.py → detection_queue → monitor_process.py
#
# ── O que flui entre blocos ──────────────────────────────────────────────────
#
#   frame_queue     : frame individual em RGB  (numpy array)
#   detection_queue : (frame RGB, lista de HandDetection)
#
# ═══════════════════════════════════════════════════════════════════════════════

import subprocess
import sys
import time
from multiprocessing import Event, Process, Queue, set_start_method
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).parent / "config" / "settings.yaml"
_ROI_PATH    = Path(__file__).parent / "config" / "rois.json"


# ── Wrappers dos processos ────────────────────────────────────────────────────
# Cada função importa o seu módulo e chama run().
# Os imports ficam aqui dentro porque cada processo filho começa do zero
# e deve importar só o que precisa.


def run_camera(frame_queue, stop_event, config):
    import capture_process
    capture_process.run(frame_queue, stop_event, config)


def run_detector(frame_queue, detection_queue, stop_event, config):
    import detection_process
    detection_process.run(frame_queue, detection_queue, stop_event, config)


def run_display(detection_queue, stop_event):
    import display_process
    display_process.run(detection_queue, stop_event)


def run_pipeline(detection_queue, stop_event, config, roi_path):
    import monitor_process
    monitor_process.run(detection_queue, stop_event, config, roi_path)




# ── Funções auxiliares de lançamento ─────────────────────────────────────────

def _start_processes(processos: dict) -> None:
    """Arranca cada processo com um breve intervalo e mostra o PID."""
    print("A arrancar processos...")
    for nome, processo in processos.items():
        processo.start()
        time.sleep(0.5)
        print(f"  [{nome}] iniciado (PID {processo.pid})")
    print("A correr. Carrega 'q' na janela para parar.\n")


def _wait_for_stop(stop_event) -> None:
    """Bloqueia até Ctrl+C ou até o stop_event ser ativado por outro processo."""
    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nCtrl+C — a parar...")
        stop_event.set()


def _terminate_processes(processos: dict) -> None:
    """Aguarda que cada processo termine; força terminação se necessário."""
    for processo in processos.values():
        processo.join(timeout=3)
        if processo.is_alive():
            processo.terminate()
    print("Processos terminados.")


def _launch(stop_event, **processos):
    """Orquestra o ciclo de vida dos processos: arrancar → aguardar → terminar."""
    _start_processes(processos)
    _wait_for_stop(stop_event)
    _terminate_processes(processos)


# ── Modos de funcionamento ────────────────────────────────────────────────────

def testar_camera(config):
    """
    Abre a câmara e mostra o feed com keypoints das mãos.
    Útil para verificar se a câmara e o MediaPipe estão a funcionar.

    Blocos: capture → detector → display
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
    Corre o pipeline completo de análise com tracking, métricas e dashboard.

    Blocos: capture → detector → monitor
    O dashboard Streamlit arranca como processo externo (subprocess) — não é um
    estágio do pipeline e não usa queues nem stop_event.
    """
    from src.roi.json_roi_repository import JsonRoiRepository

    if not JsonRoiRepository(path=_ROI_PATH).load().all():
        print("Nenhuma ROI definida. Usa a opção 2 primeiro.")
        return

    frame_queue     = Queue(maxsize=2)
    detection_queue = Queue(maxsize=5)
    stop_event      = Event()

    app_path       = Path(__file__).parent / "dashboard" / "app.py"
    dashboard_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(app_path)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _launch(
            stop_event,
            camera   = Process(target=run_camera,   name="camera",
                               args=(frame_queue, stop_event, config)),
            detector = Process(target=run_detector, name="detector",
                               args=(frame_queue, detection_queue, stop_event, config)),
            pipeline = Process(target=run_pipeline, name="pipeline",
                               args=(detection_queue, stop_event, config, str(_ROI_PATH))),
        )
    finally:
        dashboard_proc.terminate()


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
    # spawn: cada processo filho arranca limpo, sem herdar estado OpenCV/X11 do pai.
    # Necessário para que "Testar Câmara" funcione após "Definir ROIs" na mesma sessão.
    set_start_method("spawn")
    main()
