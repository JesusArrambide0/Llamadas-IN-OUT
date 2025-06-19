import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

# Funciones auxiliares
def tiempo_a_segundos(tiempo_str):
    try:
        parts = tiempo_str.strip().split(':')
        if len(parts) == 3:
            h, m, s = parts
        elif len(parts) == 2:
            h = 0
            m, s = parts
        else:
            return 0
        return int(h)*3600 + int(m)*60 + int(s)
    except:
        return 0

def duration_to_seconds(d):
    if pd.isnull(d):
        return 0
    if isinstance(d, str):
        return tiempo_a_segundos(d)
    if isinstance(d, pd.Timedelta):
        return int(d.total_seconds())
    if isinstance(d, (int, float)):
        return int(d * 24 * 3600)
    return 0

def formatear_tiempo(segundos):
    return str(timedelta(seconds=int(segundos)))

st.title("📞 Dashboard de Llamadas Hospital")

# Cargar archivo
try:
    df = pd.read_excel("inandout.xlsx")
except FileNotFoundError:
    st.error("Archivo 'inandout.xlsx' no encontrado en el directorio actual.")
    st.stop()

# Limpieza de columnas (sin cambiar a minúsculas)
df.columns = [col.strip().replace('"', '') for col in df.columns]
df["Call Type"] = df["Call Type"].astype(str).str.strip()
df["Talk Time"] = df["Talk Time"].fillna("0:00:00").astype(str).str.strip()
df["Called Number"] = df["Called Number"].astype(str).str.strip()
df["Agent Name"] = df["Agent Name"].astype(str).str.strip()

# Procesar fechas
if "Call Start Time" in df.columns:
    df["Call Start Time"] = pd.to_datetime(df["Call Start Time"], errors="coerce")
    df = df.dropna(subset=["Call Start Time"])

# Filtro de fechas
st.sidebar.header("📅 Filtro de Fechas")
min_fecha = df["Call Start Time"].min().date()
max_fecha = df["Call Start Time"].max().date()
rango = st.sidebar.date_input("Selecciona rango de fechas:", value=(min_fecha, max_fecha), min_value=min_fecha, max_value=max_fecha)

if isinstance(rango, tuple) and len(rango) == 2:
    df = df[(df["Call Start Time"].dt.date >= rango[0]) & (df["Call Start Time"].dt.date <= rango[1])]

# Clasificación de llamadas
df["Tipo Llamada"] = df["Call Type"].apply(lambda x: "Saliente" if "Outbound" in x else "Entrante")
df["Tipo Número"] = df["Called Number"].apply(lambda x: "Interno" if x.startswith("85494") else "Externo")

# Conversión de duración
df["Duración Segundos"] = df["Duration"].apply(duration_to_seconds)
df["Talk Segundos"] = df["Talk Time"].apply(duration_to_seconds)

# Llamadas salientes no contestadas (condición exacta)
df["No Contestadas"] = (
    (df["Call Type"] == "Outbound on IPCC") &
    (df["Talk Time"] == "0:00:00")
)

# Indicadores generales
st.header("📊 Indicadores Generales")
total_entrantes = df[df["Tipo Llamada"] == "Entrante"].shape[0]
total_salientes = df[df["Tipo Llamada"] == "Saliente"].shape[0]
tiempo_entrantes = df[df["Tipo Llamada"] == "Entrante"]["Duración Segundos"].sum()
tiempo_salientes = df[df["Tipo Llamada"] == "Saliente"]["Duración Segundos"].sum()
total_no_contestadas = df["No Contestadas"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Llamadas Entrantes", total_entrantes)
col2.metric("Llamadas Salientes", total_salientes)
col3.metric("Salientes No Contestadas", total_no_contestadas)

st.write(f"⏱️ Tiempo total en llamadas Entrantes: **{formatear_tiempo(tiempo_entrantes)}**")
st.write(f"⏱️ Tiempo total en llamadas Salientes: **{formatear_tiempo(tiempo_salientes)}**")

# Visualizaciones
st.subheader("📈 Visualizaciones Generales")

# A. Tipo de llamada
conteo_tipo = df["Tipo Llamada"].value_counts().reset_index()
conteo_tipo.columns = ["Tipo Llamada", "Cantidad"]
fig_tipo = px.bar(conteo_tipo, x="Tipo Llamada", y="Cantidad", title="Cantidad de Llamadas por Tipo",
                  color="Tipo Llamada", text="Cantidad")
st.plotly_chart(fig_tipo)

# B. Por agente
conteo_agente = df.groupby("Agent Name").size().reset_index(name="Total Llamadas")
fig_agente = px.bar(conteo_agente.sort_values("Total Llamadas", ascending=False),
                    x="Agent Name", y="Total Llamadas", title="Total de llamadas por agente",
                    text="Total Llamadas")
fig_agente.update_layout(xaxis={'categoryorder': 'total descending'})
st.plotly_chart(fig_agente)

# C. Histograma duración
df_duracion_valida = df[df["Talk Segundos"] > 0]
if not df_duracion_valida.empty:
    fig_duracion = px.histogram(df_duracion_valida, 
                                x="Talk Segundos", nbins=30,
                                title="Distribución de Duración de Llamadas (en segundos)")
    st.plotly_chart(fig_duracion)
else:
    st.warning("No hay llamadas con duración positiva para graficar.")

# D. Llamadas por día
llamadas_diarias = df.groupby(df["Call Start Time"].dt.date).size().reset_index(name="Cantidad")
fig_diario = px.line(llamadas_diarias, x="Call Start Time", y="Cantidad",
                     title="Llamadas por Día", markers=True)
st.plotly_chart(fig_diario)

# Detalle por agente
st.header("👤 Indicadores por Agente")
agentes = sorted(df["Agent Name"].dropna().unique())
agente_seleccionado = st.selectbox("Selecciona un agente para filtrar", options=agentes)

df_agente = df[df["Agent Name"] == agente_seleccionado]
llamadas_entrantes_agente = df_agente[df_agente["Tipo Llamada"] == "Entrante"].shape[0]
llamadas_salientes_agente = df_agente[df_agente["Tipo Llamada"] == "Saliente"].shape[0]
tiempo_entrantes_agente = df_agente[df_agente["Tipo Llamada"] == "Entrante"]["Duración Segundos"].sum()
tiempo_salientes_agente = df_agente[df_agente["Tipo Llamada"] == "Saliente"]["Duración Segundos"].sum()
no_contestadas_agente = df_agente["No Contestadas"].sum()

st.write(f"**Agente:** {agente_seleccionado}")
st.write(f"📥 Llamadas Entrantes: **{llamadas_entrantes_agente}**")
st.write(f"📤 Llamadas Salientes: **{llamadas_salientes_agente}**")
st.write(f"⏱️ Tiempo en llamadas Entrantes: **{formatear_tiempo(tiempo_entrantes_agente)}**")
st.write(f"⏱️ Tiempo en llamadas Salientes: **{formatear_tiempo(tiempo_salientes_agente)}**")
st.write(f"❌ Llamadas Salientes no contestadas: **{no_contestadas_agente}**")
