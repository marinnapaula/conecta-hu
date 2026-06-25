import streamlit as st
import plotly.express as px
from engine_historico import obter_dados_historico

st.title("🧪 Laboratório de Histórico")

if st.button("🚀 Processar"):
    df, msg = obter_dados_historico()
    
    if not df.empty:
        # Força conversão de data para o Plotly não confundir
        df['DT_SNAP'] = pd.to_datetime(df['DT_SNAP'])
        
        st.subheader("Gráfico de Backlog por Faixa")
        
        # O segredo do category_orders é alinhar com o que criamos no engine
        fig = px.area(
            df, 
            x='DT_SNAP', 
            y='Volume', 
            color='FAIXA_DIAS',
            category_orders={"FAIXA_DIAS": ["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias", "Mais de 60 dias"]}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(msg)
    
    if not df.empty:
        # Métricas rápidas
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Snapshots", len(df))
        col2.metric("Última Data", df['DT_SNAP'].max().strftime('%d/%m/%Y'))
        col3.metric("Média Geral de Dias", f"{df['Media_Dias'].mean():.1f}")

        # Gráfico de Volume
        st.subheader("Evolução do Volume da Fila")
        fig_vol = px.line(df, x='DT_SNAP', y='Volume_Fila', markers=True, title="Qtd de O.S. no Backlog")
        st.plotly_chart(fig_vol, use_container_width=True)

        # Gráfico de TMA
        st.subheader("Evolução da Média de Dias em Aberto (TMA)")
        fig_tma = px.line(df, x='DT_SNAP', y='Media_Dias', markers=True, title="Tempo Médio de Espera (Dias)")
        st.plotly_chart(fig_tma, use_container_width=True)

        # Tabela de Conferência
        st.subheader("Dados Processados (Tabela)")
        st.dataframe(df)
    else:
        st.error("O DataFrame retornou vazio. Verifique se os arquivos CSV estão na pasta correta.")

st.sidebar.markdown("---")
st.sidebar.write("### Instruções de Teste")
st.sidebar.write("1. Garanta que os CSVs estão em `planilhas_gets/02.OS_Pendentes`.")
st.sidebar.write("2. Clique no botão acima para processar.")
df, status = obter_dados_historico()

if not df.empty:
    st.subheader("Gráfico de Backlog por Faixa")
    # Gráfico de Área Empilhada
    fig = px.area(df, x='DT_SNAP', y='Volume', color='FAIXA_DIAS', 
                  category_orders={"FAIXA_DIAS": ["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias", "Mais de 60 dias"]})
    st.plotly_chart(fig, use_container_width=True)
