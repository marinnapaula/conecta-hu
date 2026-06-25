import streamlit as st
import plotly.graph_objects as go
from engine_historico import obter_dados_historico

st.title("🧪 Laboratório de Histórico")

if st.button("🚀 Processar Dados"):
    df, msg = obter_dados_historico()
    
    if not df.empty:
        st.success("Dados processados com sucesso!")
        
        # Gráfico de Backlog por Faixa (Área Sobreposta)
        st.subheader("Gráfico de Backlog por Faixa (Área Sobreposta)")
        
        fig = go.Figure()
        faixas = ["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias", "Mais de 60 dias"]
        
        # Adicionamos cada faixa como uma camada (trace) independente
        for faixa in faixas:
            # Filtra o DataFrame apenas para a faixa atual
            df_faixa = df[df['FAIXA_DIAS'] == faixa]
            
            # Adiciona ao gráfico sem empilhamento (stackgroup=None)
            fig.add_trace(go.Scatter(
                x=df_faixa['DT_SNAP'], 
                y=df_faixa['Volume'],
                fill='tozeroy',  # Preenchimento até o eixo zero
                mode='lines',    # Apenas a linha da área
                name=faixa,
                stackgroup=None  # A mágica que impede o empilhamento
            ))

        # Ajustes visuais
        fig.update_layout(
            xaxis_title="Data",
            yaxis_title="Volume",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela de Conferência (opcional, para conferir os dados)
        with st.expander("Ver dados brutos"):
            st.dataframe(df)

    else:
        st.error(f"Não foi possível processar os dados: {msg}")

st.sidebar.markdown("---")
st.sidebar.write("### Instruções")
st.sidebar.write("Os arquivos devem estar em: `planilhas_gets/02.OS_Pendentes`")
