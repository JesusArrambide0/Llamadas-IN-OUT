import streamlit as st
import pandas as pd

# Función para convertir tiempos tipo "0:00:12" a segundos
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

st.title("Dashboard de Llamadas Hospital")

# Leer archivo completo para limpiar columnas
try:
    df_temp = pd.read_excel("inandout.xlsx")
except FileNotFoundError:
    st.error("Archivo 'inandout.xlsx' no encontrado en el directorio actual.")
    st.stop()

# Limpiar espacios en nombres de columnas
df_temp.columns = df_temp.columns.str.strip()

# Columnas que necesitamos
columnas_necesarias = [
    "Agent Name", "Call Start Time", "Call End Time", "Duration",
    "Called Number", "Call Type", "Talk Time"
]

# Filtrar columnas que realmente existen en el archivo
columnas_existentes = [col for col in columnas_necesarias if col in df_temp.columns]

# Tomar solo las columnas que sí existen
df = df_temp[columnas_existentes].copy()

# Limpiar Talk Time (stripped)
df["Talk Time"] = df["Talk Time"].astype(str).str.strip()

# Clasificar llamadas internas y externas según Called Number
df["Tipo Número"] = df["Called Number"].astype(str).apply(
    lambda x: "Interno" if x.startswith("85494") else "Externo"
)

# Clasificar llamadas entrantes y salientes
df["Tipo Llamada"] = df["Call Type"].astype(str).str.lower().apply(
    lambda x: "Saliente" if "outbound" in x else "Entrante"
)

# Detectar llamadas salientes no contestadas (Talk Time = "0:00" o "0:00:00")
df["No Contestadas"] = ((df["Tipo Llamada"] == "Saliente") & 
                        (df["Talk Time"].isin(["0:00", "0:00:00", "00:00:00"])))

# Convertir Duration y Talk Time a segundos
df["Duración Segundos"] = df["Duration"].astype(str).apply(tiempo_a_segundos)
df["Talk Segundos"] = df["Talk Time"].apply(tiempo_a_segundos)

# Indicadores generales
total_entrantes = df[df["Tipo Llamada"] == "Entrante"].shape[0]
total_salientes = df[df["Tipo Llamada"] == "Saliente"].shape[0]
tiempo_entrantes = df[df["Tipo Llamada"] == "Entrante"]["Duración Segundos"].sum()
tiempo_salientes = df[df["Tipo Llamada"] == "Saliente"]["Duración Segundos"].sum()
total_no_contestadas = df["No Contestadas"].sum()

st.header("Indicadores Generales")
st.write(f"Llamadas Entrantes: **{total_entrantes}**")
st.write(f"Llamadas Salientes: **{total_salientes}**")
st.write(f"Tiempo total en llamadas Entrantes: **{tiempo_entrantes // 60} min**")
st.write(f"Tiempo total en llamadas Salientes: **{tiempo_salientes // 60} min**")
st.write(f"Llamadas Salientes no contestadas: **{total_no_contestadas}**")

# Indicadores por agente con filtro
st.header("Indicadores por Agente")
agentes = df["Agent Name"].unique()
agente_seleccionado = st.selectbox("Selecciona un agente para filtrar", options=agentes)

df_agente = df[df["Agent Name"] == agente_seleccionado]

llamadas_entrantes_agente = df_agente[df_agente["Tipo Llamada"] == "Entrante"].shape[0]
llamadas_salientes_agente = df_agente[df_agente["Tipo Llamada"] == "Saliente"].shape[0]
tiempo_entrantes_agente = df_agente[df_agente["Tipo Llamada"] == "Entrante"]["Duración Segundos"].sum()
tiempo_salientes_agente = df_agente[df_agente["Tipo Llamada"] == "Saliente"]["Duración Segundos"].sum()
no_contestadas_agente = df_agente["No Contestadas"].sum()

st.write(f"Agente: **{agente_seleccionado}**")
st.write(f"Llamadas Entrantes: **{llamadas_entrantes_agente}**")
st.write(f"Llamadas Salientes: **{llamadas_salientes_agente}**")
st.write(f"Tiempo en llamadas Entrantes: **{tiempo_entrantes_agente // 60} min**")
st.write(f"Tiempo en llamadas Salientes: **{tiempo_salientes_agente // 60} min**")
st.write(f"Llamadas Salientes no contestadas: **{no_contestadas_agente}**")
