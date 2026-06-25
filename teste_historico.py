import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from engine_historico import obter_dados_historico

st.set_page_config(page_title="Histórico Completo", layout="wide")
st.title("🧪 Laboratório de Histórico")

if st.button("🚀 Processar Dados"):
    df_raw = obter_dados_historico()
    
    if not df_raw.empty:
        # --- PREPARAÇÃO DOS DADOS (PARA TODOS OS GRÁFICOS) ---
        # Dados para as Métricas e Gráficos de Linha
        df_linhas = df_raw.groupby('DT_SNAP').agg(
            Volume_Fila=('DT_SNAP', 'count'), 
            Media_Dias=('DIAS_ABERTO', 'mean')
        ).reset_index()

        # Dados para o Gráfico de Faixa (agrupado)
        df_faixa = df_raw.groupby(['DT_SNAP', 'FAIXA_DIAS']).size().reset_index(name='Volume')

        # --- 1. MÉTRICAS ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Snapshots", len(df_linhas))
        col2.metric("Última Data", df_raw['DT_SNAP'].max().strftime('%d/%m/%Y'))
        col3.metric("Média Geral de Dias", f"{df_raw['DIAS_ABERTO'].mean():.1f}")

        st.divider()

        # --- 2. NOVO GRÁFICO (ÁREA SOBREPOSTA) ---
        st.subheader("Gráfico de Backlog por Faixa")
        fig_faixa = go.Figure()
        faixas = ["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias", "Mais de 60 dias"]
        
        for f in faixas:
            subset = df_faixa[df_faixa['FAIXA_DIAS'] == f]
            fig_faixa.add_trace(go.Scatter(
                x=subset['DT_SNAP'], y=subset['Volume'], 
                fill='tozeroy', name=f, stackgroup=None
            ))
        fig_faixa.update_layout(hovermode="x unified")
        st.plotly_chart(fig_faixa, use_container_width=True)

        # --- 3. GRÁFICOS ORIGINAIS ---
        col_lin1, col_lin2 = st.columns(2)
        
        with col_lin1:
            st.subheader("Evolução do Volume da Fila")
            fig_vol = px.line(df_linhas, x='DT_SNAP', y='Volume_Fila', markers=True)
            st.plotly_chart(fig_vol, use_container_width=True)

        with col_lin2:
            st.subheader("Evolução da Média de Dias (TMA)")
            fig_tma = px.line(df_linhas, x='DT_SNAP', y='Media_Dias', markers=True)
            st.plotly_chart(fig_tma, use_container_width=True)

        # --- 4. TABELA ---
        st.subheader("Dados Processados")
        st.dataframe(df_raw, use_container_width=True)

    else:
        st.error("Nenhum dado processado.")

st.sidebar.markdown("---")
st.sidebar.write("### Instruções")
st.sidebar.write("Os arquivos devem estar em: `planilhas_gets/02.OS_Pendentes`")
