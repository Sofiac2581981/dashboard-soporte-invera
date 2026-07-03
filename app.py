"""
Dashboard de Reporting de Soporte — Challenge Analista de Operaciones (Invera)
Autor: Mariano Caballero
Stack: Streamlit + Plotly + pandas

El dashboard esta organizado alrededor de las 5 preguntas que el lider del equipo
necesita responder de un vistazo. Cada bloque arranca con la pregunta que responde.
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------- #
# CONFIG GENERAL
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Soporte Operaciones — Invera",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta
AZUL = "#1f4e79"
GRIS = "#8896a6"
VERDE = "#2e8b57"
AMBAR = "#e0a100"
ROJO = "#c0392b"
PALETA_CAT = {
    "Bug": ROJO,
    "Accesos": VERDE,
    "Configuración": AMBAR,
    "Consulta operativa": AZUL,
}
PALETA_ESTADO = {
    "Cerrado": VERDE,
    "En progreso": AMBAR,
    "Escalado": ROJO,
    "Abierto": GRIS,
}

st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; padding-bottom: 2rem;}
      .pregunta {color:#1f4e79; font-weight:600; font-size:0.95rem;
                 border-left:4px solid #1f4e79; padding-left:10px; margin:8px 0 2px 0;}
      .alerta {background:#fdecea; border:1px solid #c0392b; border-radius:8px;
               padding:16px 20px; color:#611a15;}
      .alerta h3 {color:#c0392b; margin-top:0;}
      div[data-testid="stMetricValue"] {font-size:1.6rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# CARGA DE DATOS
# --------------------------------------------------------------------------- #
@st.cache_data
def cargar_datos() -> pd.DataFrame:
    """Lee el dataset desde el archivo que viaja junto al repo."""
    ruta = os.path.join(os.path.dirname(__file__), "challenge-dataset-tickets.xlsx")
    df = pd.read_excel(ruta, engine="openpyxl")

    # Tipado de fechas (por si vienen como texto)
    df["fecha_apertura"] = pd.to_datetime(df["fecha_apertura"])
    df["fecha_cierre"] = pd.to_datetime(df["fecha_cierre"], errors="coerce")

    # Flags derivados
    df["cerrado"] = df["estado"] == "Cerrado"
    df["sin_cerrar"] = ~df["cerrado"]
    df["escalado_bool"] = df["requirio_escalado"].astype(str).str.strip().str.lower().eq("sí")

    # Semana calendario (para la tendencia)
    df["semana"] = df["fecha_apertura"].dt.to_period("W").apply(lambda r: r.start_time.date())
    return df


df = cargar_datos()

# --------------------------------------------------------------------------- #
# SIDEBAR — FILTROS
# --------------------------------------------------------------------------- #
st.sidebar.title("🎫 Soporte Operaciones")
st.sidebar.caption("Challenge — Invera · Mariano Caballero")
st.sidebar.markdown("---")
st.sidebar.subheader("Filtros")

f_cat = st.sidebar.multiselect(
    "Categoría", sorted(df["categoria"].unique()), default=sorted(df["categoria"].unique())
)
f_prio = st.sidebar.multiselect(
    "Prioridad", ["Alta", "Media", "Baja"], default=["Alta", "Media", "Baja"]
)
f_cli = st.sidebar.multiselect(
    "Cliente", sorted(df["cliente"].unique()), default=sorted(df["cliente"].unique())
)

dff = df[
    df["categoria"].isin(f_cat)
    & df["prioridad"].isin(f_prio)
    & df["cliente"].isin(f_cli)
].copy()

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Mostrando **{len(dff)}** de {len(df)} tickets.\n\n"
    f"Período: {df['fecha_apertura'].min().date()} → {df['fecha_apertura'].max().date()}"
)

if dff.empty:
    st.warning("No hay tickets con los filtros seleccionados.")
    st.stop()

# --------------------------------------------------------------------------- #
# ENCABEZADO
# --------------------------------------------------------------------------- #
st.title("Reporting de Soporte — Equipo de Operaciones")
st.caption(
    "60 tickets de los últimos 2 meses. El tablero responde las 5 preguntas del líder "
    "del equipo. Usá los filtros de la izquierda para segmentar."
)

# --------------------------------------------------------------------------- #
# KPIs
# --------------------------------------------------------------------------- #
total = len(dff)
cerrados = int(dff["cerrado"].sum())
sin_cerrar = int(dff["sin_cerrar"].sum())
pct_cerr = cerrados / total * 100 if total else 0
tpr_med = dff["tiempo_primera_respuesta_hs"].median()
tres_med = dff.loc[dff["cerrado"], "tiempo_resolucion_hs"].median()
satisf = dff["satisfaccion_cliente"].mean()
pct_esc = dff["escalado_bool"].mean() * 100

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Tickets", total)
k2.metric("Cerrados", f"{pct_cerr:.0f}%", f"{sin_cerrar} sin cerrar", delta_color="off")
k3.metric("1ª respuesta (mediana)", f"{tpr_med:.0f} hs")
k4.metric("Resolución (mediana)", f"{tres_med:.0f} hs")
k5.metric("Satisfacción", f"{satisf:.2f} / 5")
k6.metric("Escalados", f"{pct_esc:.0f}%")

st.markdown("---")

# --------------------------------------------------------------------------- #
# PREGUNTA 1 — ESTADOS
# --------------------------------------------------------------------------- #
c1, c2 = st.columns([1, 1.3])

with c1:
    st.markdown('<div class="pregunta">1 · ¿Cuántos tickets hay y en qué estado están?</div>', unsafe_allow_html=True)
    est = dff["estado"].value_counts().reindex(
        ["Cerrado", "En progreso", "Escalado", "Abierto"]
    ).dropna()
    fig_est = px.pie(
        names=est.index, values=est.values, hole=0.55,
        color=est.index, color_discrete_map=PALETA_ESTADO,
    )
    fig_est.update_traces(textinfo="value+percent", textposition="inside")
    fig_est.update_layout(
        showlegend=True, height=330, margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", y=-0.1),
    )
    st.caption("Distribución por estado")
    st.plotly_chart(fig_est, use_container_width=True)

with c2:
    st.markdown('<div class="pregunta">2 · ¿Dónde están los cuellos de botella?</div>', unsafe_allow_html=True)
    res_cat = (
        dff[dff["cerrado"]]
        .groupby("categoria")["tiempo_resolucion_hs"]
        .median()
        .sort_values(ascending=True)
    )
    fig_cat = px.bar(
        x=res_cat.values, y=res_cat.index, orientation="h",
        color=res_cat.index, color_discrete_map=PALETA_CAT,
        labels={"x": "Horas de resolución (mediana)", "y": ""},
        text=[f"{v:.0f} hs" for v in res_cat.values],
    )
    fig_cat.update_traces(textposition="outside")
    fig_cat.update_layout(
        showlegend=False, height=330, margin=dict(t=10, b=10, l=10, r=40),
    )
    st.caption("Tiempo de resolución por categoría (horas, mediana)")
    st.plotly_chart(fig_cat, use_container_width=True)

# Segunda fila del cuello de botella: primera respuesta vs resolución por prioridad
c3, c4 = st.columns(2)

with c3:
    prio_order = ["Alta", "Media", "Baja"]
    tpr = dff.groupby("prioridad")["tiempo_primera_respuesta_hs"].median().reindex(prio_order)
    trs = dff[dff["cerrado"]].groupby("prioridad")["tiempo_resolucion_hs"].median().reindex(prio_order)
    fig_pr = go.Figure()
    fig_pr.add_bar(name="1ª respuesta", x=prio_order, y=tpr.values, marker_color=GRIS)
    fig_pr.add_bar(name="Resolución", x=prio_order, y=trs.values, marker_color=AZUL)
    fig_pr.update_layout(
        barmode="group", height=320, margin=dict(t=20, b=10, l=10, r=10),
        legend=dict(orientation="h", y=1.08),
        yaxis_title="Horas",
    )
    st.caption("Respuesta vs resolución por prioridad (horas, mediana)")
    st.plotly_chart(fig_pr, use_container_width=True)

with c4:
    bugs = dff[dff["categoria"] == "Bug"]
    if not bugs.empty and bugs["tipo_bug"].notna().any():
        tb = (
            bugs.dropna(subset=["tipo_bug"])
            .groupby("tipo_bug")["tiempo_resolucion_hs"]
            .mean()
            .sort_values(ascending=True)
        )
        fig_tb = px.bar(
            x=tb.values, y=tb.index, orientation="h",
            labels={"x": "Horas de resolución (promedio)", "y": ""},
            text=[f"{v:.0f}" for v in tb.values],
            color_discrete_sequence=[ROJO],
        )
        fig_tb.update_traces(textposition="outside")
        fig_tb.update_layout(
            showlegend=False, height=320, margin=dict(t=20, b=10, l=10, r=40),
        )
        st.caption("Bugs: resolución por subtipo (horas, promedio)")
        st.plotly_chart(fig_tb, use_container_width=True)
    else:
        st.info("No hay bugs con los filtros actuales.")

st.markdown("---")

# --------------------------------------------------------------------------- #
# PREGUNTA 3 — CLIENTES
# --------------------------------------------------------------------------- #
st.markdown('<div class="pregunta">3 · ¿Qué clientes concentran más carga y qué tan conformes están?</div>', unsafe_allow_html=True)

cli = (
    dff.groupby("cliente")
    .agg(
        tickets=("ticket_id", "count"),
        satisfaccion=("satisfaccion_cliente", "mean"),
        resolucion=("tiempo_resolucion_hs", "mean"),
        escalados=("escalado_bool", "sum"),
    )
    .reset_index()
    .sort_values("tickets", ascending=False)
)

c5, c6 = st.columns([1.4, 1])

with c5:
    fig_cli = px.scatter(
        cli, x="tickets", y="satisfaccion", size="resolucion", text="cliente",
        color="satisfaccion", color_continuous_scale=["#c0392b", "#e0a100", "#2e8b57"],
        range_color=[1, 5], size_max=45,
        labels={"tickets": "Carga (nº de tickets)", "satisfaccion": "Satisfacción media (1–5)"},
    )
    fig_cli.update_traces(textposition="top center")
    fig_cli.add_hline(y=satisf, line_dash="dot", line_color=GRIS,
                      annotation_text="Promedio global", annotation_position="right")
    fig_cli.update_layout(
        height=380, margin=dict(t=20, b=10, l=10, r=10),
        coloraxis_showscale=False,
    )
    st.caption("Carga vs satisfacción (tamaño = horas de resolución)")
    st.plotly_chart(fig_cli, use_container_width=True)

with c6:
    tabla = cli.copy()
    tabla["satisfaccion"] = tabla["satisfaccion"].round(2)
    tabla["resolucion"] = tabla["resolucion"].round(0)
    tabla.columns = ["Cliente", "Tickets", "Satisf.", "Resol. (hs)", "Escalados"]
    st.caption("Detalle por cliente (semáforo en satisfacción)")
    st.dataframe(
        tabla.style.background_gradient(subset=["Satisf."], cmap="RdYlGn", vmin=1, vmax=5),
        hide_index=True, use_container_width=True, height=380,
    )

st.markdown("---")

# --------------------------------------------------------------------------- #
# PREGUNTA 4 — VOLUMEN EN EL TIEMPO
# --------------------------------------------------------------------------- #
st.markdown('<div class="pregunta">4 · ¿El volumen está creciendo, bajando o estable?</div>', unsafe_allow_html=True)

vol = dff.groupby("semana").size().reset_index(name="tickets")
fig_vol = px.line(vol, x="semana", y="tickets", markers=True,
                  labels={"semana": "Semana (apertura)", "tickets": "Tickets abiertos"})
fig_vol.update_traces(line_color=AZUL, marker=dict(size=8))
prom = vol["tickets"].mean()
fig_vol.add_hline(y=prom, line_dash="dot", line_color=GRIS,
                  annotation_text=f"Promedio {prom:.1f}/sem", annotation_position="top left")
fig_vol.update_layout(height=320, margin=dict(t=20, b=10, l=10, r=10))
st.plotly_chart(fig_vol, use_container_width=True)
st.caption(
    "⚠️ Nota: la última semana está incompleta (el dataset corta el 12/06). "
    "Normalizado por semana, el volumen es estable en ~5–6 tickets."
)

st.markdown("---")

# --------------------------------------------------------------------------- #
# PREGUNTA 5 — ALERTA / QUÉ ATENDER MAÑANA
# --------------------------------------------------------------------------- #
st.markdown('<div class="pregunta">5 · ¿Qué es lo primero que el equipo debería atender mañana?</div>', unsafe_allow_html=True)

# Datos que alimentan la conclusion (sobre el dataset completo, no el filtrado,
# para que la alerta sea consistente aunque el usuario juegue con filtros)
abiertos = df[df["sin_cerrar"]].sort_values("fecha_apertura")
n_abiertos = len(abiertos)
n_escalados_abiertos = int((abiertos["estado"] == "Escalado").sum())
cli_peor = df.groupby("cliente")["satisfaccion_cliente"].mean().idxmin()
cli_peor_val = df.groupby("cliente")["satisfaccion_cliente"].mean().min()
pct_bug = (df["categoria"] == "Bug").mean() * 100
esc_bug = df[df["categoria"] == "Bug"]["escalado_bool"].mean() * 100

col_a, col_b = st.columns([1.1, 1])

with col_a:
    st.markdown(
        f"""
        <div class="alerta">
          <h3>🚨 Prioridades para mañana</h3>
          <ol>
            <li><b>Vaciar el backlog:</b> hay <b>{n_abiertos} tickets sin cerrar y los
                {n_abiertos} son Bugs de prioridad Alta</b>. Empezar por los
                <b>{n_escalados_abiertos} escalados</b> (Balanz y IOL).</li>
            <li><b>Atacar la raíz — los Bugs:</b> son el {pct_bug:.0f}% del volumen,
                escalan el {esc_bug:.0f}% de las veces y tienen la peor satisfacción (2.87).
                Es el cuello de botella estructural, no un pico puntual.</li>
            <li><b>Rescatar a {cli_peor}:</b> satisfacción {cli_peor_val:.2f}/5 (la más baja
                por lejos) y el peor tiempo de resolución. Cliente en riesgo — corresponde
                una llamada de gestión, no solo cerrar tickets.</li>
          </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_b:
    st.markdown("**Tickets sin cerrar (backlog actual)**")
    bl = abiertos[["ticket_id", "cliente", "prioridad", "estado", "asignado_a", "fecha_apertura"]].copy()
    bl["fecha_apertura"] = bl["fecha_apertura"].dt.date
    bl.columns = ["Ticket", "Cliente", "Prioridad", "Estado", "Asignado", "Apertura"]
    st.dataframe(bl, hide_index=True, use_container_width=True, height=300)

st.markdown("---")
st.caption(
    "Fuente: challenge-dataset-tickets.xlsx (60 tickets, abr–jun 2026). "
    "La sección 5 se calcula sobre el dataset completo para mantener la conclusión estable."
)
