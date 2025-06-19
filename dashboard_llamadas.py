# ----------------------------------
# INDICADORES GENERALES
# ----------------------------------

st.header("📊 Indicadores Generales")

# Cálculo de métricas
total_entrantes = df[df["Tipo Llamada"] == "Entrante"].shape[0]
total_salientes = df[df["Tipo Llamada"] == "Saliente"].shape[0]
tiempo_entrantes = df[df["Tipo Llamada"] == "Entrante"]["Duración Segundos"].sum()
tiempo_salientes = df[df["Tipo Llamada"] == "Saliente"]["Duración Segundos"].sum()

# Nuevo cálculo exacto de no contestadas
outbound_ipcc = df[df["Call Type Limpio"] == "outbound on ipcc"]
outbound_ipcc_0 = outbound_ipcc[outbound_ipcc["Talk Segundos"] == 0]
total_no_contestadas = len(outbound_ipcc_0)  # nuevo valor confiable

# Mostrar métricas
col1, col2, col3 = st.columns(3)
col1.metric("Llamadas Entrantes", total_entrantes)
col2.metric("Llamadas Salientes", total_salientes)
col3.metric("Outbound IPCC sin contestar", total_no_contestadas)

st.write(f"⏱️ Tiempo total en llamadas Entrantes: **{formatear_tiempo(tiempo_entrantes)}**")
st.write(f"⏱️ Tiempo total en llamadas Salientes: **{formatear_tiempo(tiempo_salientes)}**")

# Mostrar tabla con resumen detallado de outbound IPCC con 0
df_resumen_ipcc = pd.DataFrame({
    "Total Outbound on IPCC": [len(outbound_ipcc)],
    "Outbound on IPCC con tiempo 0": [total_no_contestadas],
    "Porcentaje (%)": [total_no_contestadas / len(outbound_ipcc) * 100 if len(outbound_ipcc) > 0 else 0]
})

st.write("### Resumen llamadas Outbound on IPCC con duración 0")
st.write(df_resumen_ipcc)
