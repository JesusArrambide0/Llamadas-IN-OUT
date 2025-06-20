import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta
import re

# --- Funciones auxiliares ---
def talk_time_a_segundos(tiempo_str):
    try:
        if pd.isnull(tiempo_str):
            return 0
        if isinstance(tiempo_str, pd.Timedelta):
            return int(tiempo_str.total_seconds())
        partes = str(tiempo_str).split(':')
        if len(partes) == 3:
            h, m, s = partes
            return int(h)*3600 + int(m)*60 + int(float(s))
        elif len(partes) == 2:
            m, s = partes
            return int(m)*60 + int(float(s))
        else:
            return 0
    except Exception:
        return 0

def duration_to_seconds(d):
    if pd.isnull(d):
        return 0
    if isinstance(d, pd.Timedelta):
        return int(d.total_seconds())
    if isinstance(d, (int, float)):
        return int(d * 24 * 3600)
    if isinstance(d, str):
        return talk_time_a_segundos(d)
    return 0

def formatear_tiempo(segundos):
    return str(timedelta(seconds=int(segundos)))

def limpiar_texto(s):
    if isinstance(s, str):
        return re.sub(r'\s+', ' ', s).strip()
    return s

# --- Cargar archivo ---
st.title("📞 Dashboard de Llamadas Hospital")

try:
    df = pd.read_excel("inandout.xlsx")
except FileNotFoundError:
    st.error("Archivo 'inandout.xlsx' no encontrado en el directorio actual.")
    st.stop()

# --- Limpieza ---
df.columns = [col.strip().replace('"', '') for col in df.columns]
df["Call Type Limpio"] = df["Call Type"].astype(str).apply(limpiar_texto).str.lower()
df["Talk Time Limpio"] = df["Talk Time"].fillna("0:00:00").astype(str).apply(limpiar_texto)
df["Called Number"] = df["Called Number"].astype(str).str.strip()
df["Agent Name"] = df["Agent Name"].astype(str).str.strip()

# Procesar fechas
if "Call Start Time" in df.columns:
    df["Call Start Time"] = pd.to_datetime(df["Call Start Time"], errors="coerce")
    df = df.dropna(subset=["Call Start Time"])

# --- Filtro de fechas ---
st.sidebar.header("📅 Filtro de Fechas")
min_fecha = df["Call Start Time"].min().date()
max_fecha = df["Call Start Time"].max().date()
rango = st.sidebar.date_input("Selecciona rango de fechas:", value=(min_fecha, max_fecha), min_value=min_fecha, max_value=max_fecha)

if isinstance(rango, tuple) and len(rango) == 2:
    df = df[(df["Call Start Time"].dt.date >= rango[0]) & (df["Call Start Time"].dt.date <= rango[1])]

# --- Clasificación ---
df["Tipo Llamada"] = df["Call Type"].apply(lambda x: "Saliente" if "Outbound" in str(x) else "Entrante")
df["Tipo Número"] = df["Called Number"].apply(lambda x: "Interno" if x.startswith("85494") else "Externo")

# --- Duraciones ---
df["Duración Segundos"] = df["Duration"].apply(duration_to_seconds)
df["Talk Segundos"] = df["Talk Time"].apply(talk_time_a_segundos)

# --- Indicadores Generales ---
total_entrantes = df[df["Tipo Llamada"] == "Entrante"].shape[0]
total_salientes = df[df["Tipo Llamada"] == "Saliente"].shape[0]
tiempo_entrantes = df[df["Tipo Llamada"] == "Entrante"]["Duración Segundos"].sum()
tiempo_salientes = df[df["Tipo Llamada"] == "Saliente"]["Duración Segundos"].sum()

# Outbound on IPCC con tiempo 0
outbound_ipcc = df[df["Call Type Limpio"] == "outbound on ipcc"]
outbound_ipcc_0 = outbound_ipcc[outbound_ipcc["Talk Segundos"] == 0]
total_no_contestadas = len(outbound_ipcc_0)

# Mostrar métricas
st.header("📊 Indicadores Generales")
col1, col2, col3 = st.columns(3)
col1.metric("Llamadas Entrantes", total_entrantes)
col2.metric("Llamadas Salientes", total_salientes)
col3.metric("Outbound IPCC sin contestar", total_no_contestadas)

st.write(f"⏱️ Tiempo total en llamadas Entrantes: **{formatear_tiempo(tiempo_entrantes)}**")
st.write(f"⏱️ Tiempo total en llamadas Salientes: **{formatear_tiempo(tiempo_salientes)}**")

# Tabla resumen
porcentaje = (total_no_contestadas / len(outbound_ipcc) * 100) if len(outbound_ipcc) > 0 else 0
df_resumen_ipcc = pd.DataFrame({
    "Total Outbound on IPCC": [len(outbound_ipcc)],
    "Outbound on IPCC con tiempo 0": [total_no_contestadas],
    "Porcentaje (%)": [f"{porcentaje:.2f}%"]
})

st.write("### Resumen llamadas Outbound on IPCC con duración 0")
st.write(df_resumen_ipcc)

# --- Visualizaciones ---
st.subheader("📈 Visualizaciones Generales")

# Tipo de llamada
conteo_tipo = df["Tipo Llamada"].value_counts().reset_index()
conteo_tipo.columns = ["Tipo Llamada", "Cantidad"]
fig_tipo = px.bar(conteo_tipo, x="Tipo Llamada", y="Cantidad", title="Cantidad de Llamadas por Tipo",
                  color="Tipo Llamada", text="Cantidad")
st.plotly_chart(fig_tipo)

# Por agente
conteo_agente = df.groupby("Agent Name").size().reset_index(name="Total Llamadas")
fig_agente = px.bar(conteo_agente.sort_values("Total Llamadas", ascending=False),
                    x="Agent Name", y="Total Llamadas", title="Total de llamadas por agente",
                    text="Total Llamadas")
fig_agente.update_layout(xaxis={'categoryorder': 'total descending'})
st.plotly_chart(fig_agente)

# Histograma duración
df_duracion_valida = df[df["Talk Segundos"] > 0]
if not df_duracion_valida.empty:
    fig_duracion = px.histogram(df_duracion_valida, 
                                x="Talk Segundos", nbins=30,
                                title="Distribución de Duración de Llamadas (en segundos)")
    st.plotly_chart(fig_duracion)
else:
    st.warning("No hay llamadas con duración positiva para graficar.")

# Llamadas por día
llamadas_diarias = df.groupby(df["Call Start Time"].dt.date).size().reset_index(name="Cantidad")
fig_diario = px.line(llamadas_diarias, x="Call Start Time", y="Cantidad",
                     title="Llamadas por Día", markers=True)
st.plotly_chart(fig_diario)

# --- Indicadores por agente ---
st.header("👤 Indicadores por Agente")
agentes = sorted(df["Agent Name"].dropna().unique())
agente_seleccionado = st.selectbox("Selecciona un agente para filtrar", options=agentes)

df_agente = df[df["Agent Name"] == agente_seleccionado]
llamadas_entrantes_agente = df_agente[df_agente["Tipo Llamada"] == "Entrante"].shape[0]
llamadas_salientes_agente = df_agente[df_agente["Tipo Llamada"] == "Saliente"].shape[0]
tiempo_entrantes_agente = df_agente[df_agente["Tipo Llamada"] == "Entrante"]["Duración Segundos"].sum()
tiempo_salientes_agente = df_agente[df_agente["Tipo Llamada"] == "Saliente"]["Duración Segundos"].sum()
no_contestadas_agente = df_agente[
    (df_agente["Call Type Limpio"] == "outbound on ipcc") & 
    (df_agente["Talk Segundos"] == 0)
].shape[0]

st.write(f"**Agente:** {agente_seleccionado}")
st.write(f"📥 Llamadas Entrantes: **{llamadas_entrantes_agente}**")
st.write(f"📤 Llamadas Salientes: **{llamadas_salientes_agente}**")
st.write(f"⏱️ Tiempo en llamadas Entrantes: **{formatear_tiempo(tiempo_entrantes_agente)}**")
st.write(f"⏱️ Tiempo en llamadas Salientes: **{formatear_tiempo(tiempo_salientes_agente)}**")
st.write(f"❌ Outbound IPCC sin contestar: **{no_contestadas_agente}**")

# --- Análisis por Área usando Directorio.xlsx ---
st.header("📍 Análisis de Origen/Destino según Directorio")

tabs = st.tabs(["📞 Llamadas", "📌 Origen/Destino"])

with tabs[1]:
    try:
        directorio = pd.read_excel("Directorio.xlsx")
    except FileNotFoundError:
        st.error("Archivo 'Directorio.xlsx' no encontrado en el directorio actual.")
        st.stop()

    # Normalizar columnas del directorio
    directorio.columns = [c.strip() for c in directorio.columns]
    if "Extensión" not in directorio.columns or "Área" not in directorio.columns:
        st.warning("El archivo 'Directorio.xlsx' debe tener columnas llamadas 'Extensión' y 'Área'.")
    else:
        # Asegurarse que sean texto para hacer match correcto
        directorio["Extensión"] = directorio["Extensión"].astype(str).str.strip()
        df["Called Number"] = df["Called Number"].astype(str).str.strip()

        # Unir las llamadas con el directorio
        df_ubicado = df.merge(directorio, how="left", left_on="Called Number", right_on="Extensión")
        df_ubicado["Área"] = df_ubicado["Área"].fillna("No identificado")

        # Contar llamadas por área y tipo
        resumen_area = df_ubicado.groupby(["Área", "Tipo Llamada"]).size().reset_index(name="Cantidad")

        # Visualización
        fig_area = px.bar(resumen_area,
                          x="Área", y="Cantidad", color="Tipo Llamada",
                          title="Llamadas por Área (según Directorio)",
                          text="Cantidad")
        fig_area.update_layout(xaxis={'categoryorder': 'total descending'})
        st.plotly_chart(fig_area)

        # Tabla detallada
        st.write("### Detalle de llamadas por Área")
        st.dataframe(resumen_area)

