# Ponto de entrada: menu + orquestração dos processos.
#
# Cada modo é uma composição de processos que comunicam via Queues:
#
#   Testar câmera:     capture → detector → display
#   Correr programa:   capture → detector → monitor  (+Streamlit como subprocess)
#   Configurar Bancada: corre no processo principal (wizard interativo)
#
# Os imports dos módulos de processo ficam dentro das funções run_*
# porque cada processo filho arranca limpo (spawn) e deve importar
# apenas o que precisa — herdar estado do pai causaria problemas com
# OpenCV e X11.

import subprocess
import sys
import time
from multiprocessing import Event, Process, Queue, set_start_method
from pathlib import Path

import yaml

_CONFIG_PATH     = Path(__file__).parent / "config" / "settings.yaml"
_WORKBENCHES_DIR = Path(__file__).parent / "config" / "workbenches"
_ACTIVE_PATH     = Path(__file__).parent / "config" / "active_workbench.txt"


def run_camera(frame_queue, stop_event, config):
    import capture_process
    capture_process.run(frame_queue, stop_event, config)


def run_detector(frame_queue, detection_queue, stop_event, config):
    import detection_process
    detection_process.run(frame_queue, detection_queue, stop_event, config)


def run_display(detection_queue, stop_event):
    import display_process
    display_process.run(detection_queue, stop_event)


def run_pipeline(detection_queue, stop_event, config, workbenches_dir, active_path, projection_queue=None):
    import monitor_process
    monitor_process.run(detection_queue, stop_event, config, workbenches_dir, active_path, projection_queue)


def run_projection(projection_queue, stop_event, config, workbenches_dir, active_path):
    import projection_process
    projection_process.run(projection_queue, stop_event, config, workbenches_dir, active_path)


def _start_processes(processos: dict) -> None:
    print("A arrancar processos...")
    for nome, processo in processos.items():
        processo.start()
        time.sleep(0.5)
        print(f"  [{nome}] iniciado (PID {processo.pid})")
    print("A correr. Carrega 'q' na janela para parar.\n")


def _wait_for_stop(stop_event) -> None:
    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nCtrl+C — a parar...")
        stop_event.set()


def _terminate_processes(processos: dict) -> None:
    for processo in processos.values():
        processo.join(timeout=3)
        if processo.is_alive():
            processo.terminate()
    print("Processos terminados.")


def _launch(stop_event, **processos):
    """Arranca os processos, aguarda o sinal de paragem e termina-os."""
    _start_processes(processos)
    _wait_for_stop(stop_event)
    _terminate_processes(processos)


def testar_camera(config):
    """Abre a câmera e mostra o feed com keypoints. Não grava nada."""
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


def correr_programa(config):
    """Pipeline completo com tracking, métricas, dashboard e exportação Excel.

    O Streamlit é lançado como subprocess independente — não usa queues nem
    stop_event. Lê o JSON escrito pelo DashboardWriter a cada refresh_seconds.
    É terminado no finally para não ficar órfão se o pipeline fechar com erro.
    """
    from src.roi.json_roi_repository import JsonRoiRepository

    from src.wizard.workbench_config import WorkbenchConfig

    active_name = WorkbenchConfig.active_name(_ACTIVE_PATH)
    if active_name is None:
        print("Bancada não configurada. Usa a opção 3 (Configurar Bancada) primeiro.")
        return

    roi_path = WorkbenchConfig.roi_path(_WORKBENCHES_DIR, active_name)
    if not JsonRoiRepository(path=roi_path).load().all():
        print("Nenhuma ROI definida. Usa a opção 3 (Configurar Bancada) primeiro.")
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

    proj_enabled    = config.get("projector", {}).get("enabled", False)
    projection_queue = Queue(maxsize=10) if proj_enabled else None

    processos = dict(
        camera   = Process(target=run_camera,   name="camera",
                           args=(frame_queue, stop_event, config)),
        detector = Process(target=run_detector, name="detector",
                           args=(frame_queue, detection_queue, stop_event, config)),
        pipeline = Process(target=run_pipeline, name="pipeline",
                           args=(detection_queue, stop_event, config,
                                 str(_WORKBENCHES_DIR), str(_ACTIVE_PATH), projection_queue)),
    )

    if proj_enabled:
        processos["projector"] = Process(
            target=run_projection, name="projector",
            args=(projection_queue, stop_event, config,
                  str(_WORKBENCHES_DIR), str(_ACTIVE_PATH)),
        )

    try:
        _launch(stop_event, **processos)
    finally:
        dashboard_proc.terminate()


def configurar_bancada(config):
    """Wizard interativo para configurar zonas, sequência e regras da bancada."""
    from src.wizard.setup_wizard import SetupWizard

    SetupWizard(
        workbenches_dir=_WORKBENCHES_DIR,
        active_path=_ACTIVE_PATH,
        camera_config=config["camera"],
        projector_config=config.get("projector"),
    ).run()


_OPCOES = {
    "1": ("Testar câmera",       testar_camera),
    "2": ("Correr programa",     correr_programa),
    "3": ("Configurar Bancada",  configurar_bancada),
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


if __name__ == "__main__":
    # spawn em vez de fork — necessário para que OpenCV e X11 não herdem
    # estado do processo pai, o que causaria falhas ao usar múltiplos modos
    # na mesma sessão (ex: Testar Câmera após Definir ROIs).
    set_start_method("spawn")
    main()
