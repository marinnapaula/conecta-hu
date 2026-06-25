import streamlit as st
import plotly.express as px
from engine_historico import obter_dados_historico

st.title("🧪 Laboratório de Histórico")

if st.button("🚀 Processar Dados"):
    df_raw, msg = obter_dados_historico()
    
    if not df_raw.empty:
        # 1. Preparar dados para Gráficos de Linha (Agrupado por Data)
        df_line = df_raw.groupby('DT_SNAP').agg(
            Volume_Fila=('DT_SNAP', 'count'),
            Media_Dias=('DIAS_ABERTO', 'mean')
        ).reset_index()

        # 2. Preparar dados para Gráfico de Faixa (Agrupado por Data e Faixa)
        df_faixa = df_raw.groupby(['DT_SNAP', 'FAIXA_DIAS']).size().reset_index(name='Volume')

        # --- EXIBIÇÃO ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Snapshots", len(df_line))
        col2.metric("Última Data", df_raw['DT_SNAP'].max().strftime('%d/%m/%Y'))
        col3.metric("Média Geral", f"{df_raw['DIAS_ABERTO'].mean():.1f} dias")

        st.subheader("Evolução do Volume")
        st.line_chart(df_line.set_index('DT_SNAP')[['Volume_Fila']])

        st.subheader("Evolução do TMA")
        st.line_chart(df_line.set_index('DT_SNAP')[['Media_Dias']])

        st.subheader("Gráfico de Backlog por Faixa")
        fig = px.area(df_faixa, x='DT_SNAP', y='Volume', color='FAIXA_DIAS',
                      category_orders={"FAIXA_DIAS": ["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias", "Mais de 60 dias"]})
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("Nenhum dado processado.")
