import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

_SETTINGS_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"
_DATA_PATH     = Path(__file__).parent / "data" / "metrics.json"


# ── Carregamento de dados ─────────────────────────────────────────────────────

def _load_config() -> dict:
    with open(_SETTINGS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_data() -> dict | None:
    """Lê o JSON escrito pelo DashboardWriter. Devolve None se ainda não existe."""
    if not _DATA_PATH.exists():
        return None
    text = _DATA_PATH.read_text(encoding="utf-8").strip()
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
    """Secção 1 — Ciclos, tempo médio de ciclo e duração da sessão."""
    st.subheader("Resumo da Sessão")

    cycles   = data["cycle_metrics"]
    duration = data["session_duration"]
    avg_s    = cycles.get("avg_s")

    c1, c2, c3 = st.columns(3)
    c1.metric("Ciclos completos",    cycles.get("count", 0))
    c2.metric("Tempo médio de ciclo", _fmt_seconds(avg_s) if avg_s else "—")
    c3.metric("Duração da sessão",   _fmt_seconds(duration))


def _render_time_breakdown(data: dict) -> None:
    """Secção 2 — Decomposição produtivo / transição / interrupção."""
    st.subheader("Decomposição do Tempo")

    bd = data["time_breakdown"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Produtivo",    f"{bd['productive_pct']:.1f} %")
    c2.metric("Transição",    f"{bd['transition_pct']:.1f} %")
    c3.metric("Interrupções", f"{bd['interruption_pct']:.1f} %")


def _render_zone_table(data: dict) -> None:
    """Secção 3 — Tabela de métricas por zona com gargalo destacado."""
    st.subheader("Métricas por Zona")

    task       = data.get("task_metrics", {})
    bottleneck = data.get("bottleneck_zone")

    if not task:
        st.info("Ainda sem tarefas confirmadas.")
        return

    rows = [
        {
            "Zona":          zone,
            "Ocorrências":   m["count"],
            "Mín (s)":       m["min_s"],
            "Médio (s)":     m["avg_s"],
            "Máx (s)":       m["max_s"],
            "Desvio Pad.":   m["std_dev_s"],
        }
        for zone, m in task.items()
    ]

    df = pd.DataFrame(rows).set_index("Zona")

    def _highlight(row):
        bg = "background-color: #ff4b4b33" if row.name == bottleneck else ""
        return [bg] * len(row)

    styled = (
        df.style
        .apply(_highlight, axis=1)
        .format("{:.3f}", subset=["Mín (s)", "Médio (s)", "Máx (s)", "Desvio Pad."])
    )
    st.dataframe(styled, use_container_width=True)

    if bottleneck:
        st.caption(f"Gargalo: {bottleneck} (maior tempo médio)")


def _render_charts(data: dict) -> None:
    """Secção 4 — Gráficos: tempo médio por zona e decomposição do tempo."""
    task = data.get("task_metrics", {})

    st.subheader("Gráficos")

    if not task:
        st.info("Ainda sem dados para graficar.")
        return

    col_left, col_right = st.columns(2)

    with col_left:
        st.caption("Tempo médio por zona (s)")
        df_avg = pd.DataFrame(
            {"Tempo médio (s)": {zone: m["avg_s"] for zone, m in task.items()}}
        )
        st.bar_chart(df_avg)

    with col_right:
        st.caption("Decomposição do tempo (%)")
        bd = data["time_breakdown"]
        df_bd = pd.DataFrame({
            "Tipo": ["Produtivo", "Transição", "Interrupções"],
            "% Tempo": [bd["productive_pct"], bd["transition_pct"], bd["interruption_pct"]],
        }).set_index("Tipo")
        st.bar_chart(df_bd)


def _render(data: dict) -> None:
    _render_summary(data)
    st.divider()
    _render_time_breakdown(data)
    st.divider()
    _render_zone_table(data)
    st.divider()
    _render_charts(data)

    captured = data.get("captured_at", "").replace("T", " ")
    st.caption(f"Última atualização: {captured}")


# ── Entrada ───────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Monitor Industrial",
        layout="wide",
    )
    st.title("Sistema de Reconhecimento Industrial")

    config  = _load_config()
    refresh = config["dashboard"]["refresh_seconds"]
    data    = _load_data()

    if data is None:
        st.info("A aguardar dados do pipeline...")
    else:
        _render(data)

    time.sleep(refresh)
    st.rerun()


main()
