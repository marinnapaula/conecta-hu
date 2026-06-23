import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================================
st.set_page_config(page_title="Dashboard Geral | Conecta", page_icon="📊", layout="wide")

st.title("📊 Indicadores de Manutenção")
st.markdown("**Visão Macro da Engenharia Clínica - HU-UNIVASF | EBSERH**")
st.markdown("---")

# =====================================================================
# 2. MOTOR DE LEITURA DOS DADOS (Lendo do Robô)
# =====================================================================
@st.cache_data(ttl=3600) # Mantém os dados em cache por 1 hora para a página carregar rápido
def carregar_relatorio_recente(pasta_nome):
    """Busca o arquivo mais recente dentro da pasta especificada"""
    caminho_pasta = os.path.join(os.getcwd(), "planilhas_gets", pasta_nome)
    arquivos = glob.glob(os.path.join(caminho_pasta, "*.xlsx"))
    
    if not arquivos:
        return pd.DataFrame() # Retorna vazio se o robô ainda não baixou nada
        
    arquivo_mais_novo = max(arquivos, key=os.path.getmtime)
    
    try:
        # O padrão do GETS é ter um cabeçalho nas primeiras linhas
        df = pd.read_excel(arquivo_mais_novo, skiprows=5)
        # Padroniza os nomes das colunas para evitar erros de digitação
        df.columns = df.columns.str.strip().str.upper()
        return df
    except Exception as e:
        st.error(f"Erro ao ler {pasta_nome}: {e}")
        return pd.DataFrame()

# =====================================================================
# 3. CARREGANDO AS BASES
# =====================================================================
with st.spinner("Sincronizando dados com o servidor..."):
    df_pendentes = carregar_relatorio_recente("02.OS_Pendentes")
    df_encerradas = carregar_relatorio_recente("01.OS_Encerradas")

# =====================================================================
# 4. CÁLCULO DE KPIs MACRO
# =====================================================================
total_pendentes = len(df_pendentes) if not df_pendentes.empty else 0
total_encerradas = len(df_encerradas) if not df_encerradas.empty else 0

# (Placeholder para o TMA real que vamos calcular depois)
tma_geral = "16,19" 
tma_mc_12m = "19,41"

# =====================================================================
# 5. RENDERIZAÇÃO DOS CARTÕES (MÉTRICAS)
# =====================================================================
st.markdown("### Visão Geral de O.S")
col1, col2, col3, col4 = st.columns(4)

col1.metric(label="Total OS Pendentes", value=total_pendentes)
col2.metric(label="Total OS Encerradas (Mês)", value=total_encerradas)
col3.metric(label="TMA Geral 12 Meses", value=tma_geral, delta="-1.5 (Melhoria)", delta_color="inverse")
col4.metric(label="TMA MC 12 Meses", value=tma_mc_12m)

st.markdown("<br>", unsafe_allow_html=True)

# =====================================================================
# 6. GRÁFICOS INTERATIVOS COM PLOTLY
# =====================================================================
col_grafico1, col_grafico2 = st.columns(2)

with col_grafico1:
    st.markdown("#### O.S Pendentes x Estado")
    if not df_pendentes.empty and 'ESTADO' in df_pendentes.columns: # Ajuste o nome da coluna se necessário
        contagem_estado = df_pendentes['ESTADO'].value_counts().reset_index()
        contagem_estado.columns = ['Estado', 'Quantidade']
        
        # Gráfico de barras horizontais
        fig_estado = px.bar(contagem_estado, x='Quantidade', y='Estado', orientation='h', 
                            color='Estado', text='Quantidade')
        fig_estado.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_estado, use_container_width=True)
    else:
        st.info("A coluna 'ESTADO' não foi encontrada na planilha de pendentes.")

with col_grafico2:
    st.markdown("#### O.S Pendentes x Tipo de Manutenção")
    if not df_pendentes.empty and 'TIPO DE MANUTENÇÃO' in df_pendentes.columns:
        contagem_tipo = df_pendentes['TIPO DE MANUTENÇÃO'].value_counts().reset_index()
        contagem_tipo.columns = ['Tipo', 'Quantidade']
        
        # Gráfico de rosca (Donut Chart)
        fig_tipo = px.pie(contagem_tipo, values='Quantidade', names='Tipo', hole=0.4)
        fig_tipo.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_tipo, use_container_width=True)
    else:
        st.info("A coluna 'TIPO DE MANUTENÇÃO' não foi encontrada.")
