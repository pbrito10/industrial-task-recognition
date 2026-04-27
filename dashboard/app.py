import json
import time
from pathlib import Path

import streamlit as st
import yaml

_SETTINGS_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"


# ── Carregamento de dados ─────────────────────────────────────────────────────

def _load_config() -> dict:
    with open(_SETTINGS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_data(data_path: Path) -> dict | None:
    """Lê o JSON escrito pelo DashboardWriter. Devolve None se ainda não existe."""
    if not data_path.exists():
        return None
    text = data_path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ── Formatação ────────────────────────────────────────────────────────────────

def _fmt_seconds(s: float) -> str:
    """Formata segundos em 'Xm XXs' ou 'X.Xs' consoante a magnitude."""
    if s >= 60:
        return f"{int(s // 60)}m {int(s % 60):02d}s"
    return f"{s:.1f}s"


# ── Secções do dashboard ──────────────────────────────────────────────────────

def _render_summary(data: dict) -> None:
    """Ciclos em ordem, ciclos a rever, tempo médio e duração da sessão."""
    st.subheader("Resumo da Sessão")

    cycles   = data["cycle_metrics"]
    duration = data["session_duration"]
    avg_s    = cycles.get("avg_s")
    count    = cycles.get("count", 0)

    # Resultado automático: em ordem vs. ciclos que precisam de validação manual.
    correct   = cycles.get("count_in_order", 0)
    to_review = cycles.get(
        "count_to_review",
        cycles.get("count_probably_complete", 0) + cycles.get("count_anomalies", 0),
    )

    avg_display = _fmt_seconds(avg_s) if avg_s else "—"

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total de ciclos",      count)
    c2.metric("Ciclos em ordem",      correct)
    c3.metric("Ciclos a rever",       to_review)
    c4.metric("Tempo médio de ciclo", avg_display)
    c5.metric("Duração da sessão",    _fmt_seconds(duration))


def _render_time_breakdown(data: dict) -> None:
    """Decomposição produtivo / transição / interrupção."""
    st.subheader("Decomposição do Tempo")

    bd = data["time_breakdown"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Produtivo",    f"{bd['productive_pct']:.1f} %")
    c2.metric("Transição",    f"{bd['transition_pct']:.1f} %")
    c3.metric("Interrupções", f"{bd['interruption_pct']:.1f} %")


def _render(data: dict) -> None:
    _render_summary(data)
    st.divider()
    _render_time_breakdown(data)

    captured = data.get("captured_at", "").replace("T", " ")
    st.caption(f"Última atualização: {captured}")


# ── Entrada ───────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Monitor Industrial",
        layout="wide",
    )
    st.title("Sistema de Reconhecimento Industrial")

    config    = _load_config()
    refresh   = config["dashboard"]["refresh_seconds"]
    data_path = Path(config["dashboard"]["data_path"])
    data      = _load_data(data_path)

    if data is None:
        st.info("A aguardar dados do pipeline...")
        time.sleep(refresh)
        st.rerun()

    _render(data)
    time.sleep(refresh)
    st.rerun()


main()
