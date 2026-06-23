import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================================
st.set_page_config(page_title="OS Pendentes | Conecta", page_icon="🚨", layout="wide")

st.title("🚨 Monitoramento Detalhado - O.S. Pendentes")
st.markdown("**Acompanhamento tático do tempo de fila e criticidade dos equipamentos.**")
st.markdown("---")

# =====================================================================
# 2. FUNÇÃO DE LEITURA DOS DADOS
# =====================================================================
@st.cache_data(ttl=600) # Atualiza a cada 10 minutos se houver arquivo novo
def carregar_fpendencias():
    caminho = os.path.join(os.getcwd(), "planilhas_gets", "02.OS_Pendentes")
    arquivos = glob.glob(os.path.join(caminho, "*.xlsx"))
    
    if not arquivos:
        return pd.DataFrame()
        
    arq_recente = max(arquivos, key=os.path.getmtime)
    
    try:
        df = pd.read_excel(arq_recente, skiprows=5)
        df.columns = df.columns.str.strip().str.upper()
        
        # Converte a coluna de data de abertura para formato de data do Python
        # Ajuste o nome da coluna 'DATA DE ABERTURA' conforme o padrão exato do GETS
        if 'DATA ABERTURA' in df.columns:
            df['DATA ABERTURA'] = pd.to_datetime(df['DATA ABERTURA'], errors='coerce')
            # Calcula os dias em aberto
            hoje = pd.to_datetime(datetime.today().date())
            df['DIAS ABERTO'] = (hoje - df['DATA ABERTURA']).dt.days
            
        return df
    except Exception as e:
        st.error(f"Erro ao processar as O.S. Pendentes: {e}")
        return pd.DataFrame()

# =====================================================================
# 3. CARREGAMENTO E FILTROS LATERAIS (SIDEBAR)
# =====================================================================
df_pendentes = carregar_fpendencias()

if df_pendentes.empty:
    st.warning("Nenhum dado de O.S. Pendente encontrado. Verifique se o robô já executou a extração.")
else:
    st.sidebar.header("Filtros de Busca")
    
    # Filtro de Tipo de Manutenção (MC / MP)
    if 'TIPO DE MANUTENÇÃO' in df_pendentes.columns:
        tipos_manut = df_pendentes['TIPO DE MANUTENÇÃO'].dropna().unique()
        tipo_selecionado = st.sidebar.multiselect("Tipo de Manutenção", tipos_manut, default=tipos_manut)
        df_filtrado = df_pendentes[df_pendentes['TIPO DE MANUTENÇÃO'].isin(tipo_selecionado)]
    else:
        df_filtrado = df_pendentes
        
    # Filtro de Estado (Aguardando Peça, Em Execução, etc.)
    if 'ESTADO' in df_filtrado.columns:
        estados = df_filtrado['ESTADO'].dropna().unique()
        estado_selecionado = st.sidebar.multiselect("Status da OS", estados, default=estados)
        df_filtrado = df_filtrado[df_filtrado['ESTADO'].isin(estado_selecionado)]

# =====================================================================
# 4. EXIBIÇÃO DOS DADOS (TABELA INTERATIVA)
# =====================================================================
    st.markdown("### 📋 Fila de Atendimento")
    
    # Cria os cartões de resumo rápido acima da tabela
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Total de O.S. Exibidas", len(df_filtrado))
    
    if 'DIAS ABERTO' in df_filtrado.columns:
        media_dias = round(df_filtrado['DIAS ABERTO'].mean(), 1)
        os_criticas = len(df_filtrado[df_filtrado['DIAS ABERTO'] > 60]) # Considerando > 60 dias como crítico
        
        col_kpi2.metric("Média de Dias em Aberto", media_dias)
        col_kpi3.metric("O.S. Atrasadas (> 60 dias)", os_criticas, delta="Atenção", delta_color="inverse")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Exibe a tabela interativa do Streamlit (permite ordenar, buscar e baixar em CSV)
    # Selecionamos apenas as colunas mais importantes para não poluir a tela
    colunas_visiveis = ['OS', 'EQUIPAMENTO', 'N. SÉRIE', 'ESTADO', 'DIAS ABERTO']
    
    # Verifica quais colunas realmente existem no Excel do GETS para evitar erros
    colunas_reais = [col for col in colunas_visiveis if col in df_filtrado.columns]
    
    st.dataframe(
        df_filtrado[colunas_reais].sort_values(by='DIAS ABERTO', ascending=False) if 'DIAS ABERTO' in colunas_reais else df_filtrado,
        use_container_width=True,
        hide_index=True,
        height=500
    )
