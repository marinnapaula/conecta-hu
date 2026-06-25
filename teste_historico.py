import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from engine_historico import obter_dados_historico

st.title("🧪 Laboratório de Histórico")

if st.button("🚀 Processar Dados"):
    df_raw = obter_dados_historico()
    
    if not df_raw.empty:
        # 1. Dados para Linhas
        df_linhas = df_raw.groupby('DT_SNAP').agg(Volume=('DT_SNAP', 'count'), Media=('DIAS_ABERTO', 'mean')).reset_index()
        
        # 2. Dados para Faixa (agrupado aqui, na hora de usar)
        df_faixa = df_raw.groupby(['DT_SNAP', 'FAIXA_DIAS']).size().reset_index(name='Volume')

        # Gráfico Área Sobreposta
        st.subheader("Gráfico de Backlog por Faixa")
        fig = go.Figure()
        faixas = ["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias", "Mais de 60 dias"]
        for f in faixas:
            subset = df_faixa[df_faixa['FAIXA_DIAS'] == f]
            fig.add_trace(go.Scatter(x=subset['DT_SNAP'], y=subset['Volume'], fill='tozeroy', name=f, stackgroup=None))
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas
        c1, c2 = st.columns(2)
        c1.metric("Volume Total", df_linhas['Volume'].sum())
        c2.metric("Média Geral", f"{df_linhas['Media'].mean():.1f} dias")
    else:
        st.error("Nenhum dado encontrado.")
