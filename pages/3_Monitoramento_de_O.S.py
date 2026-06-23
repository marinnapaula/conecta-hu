import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime
import numpy as np

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA (ÍCONE MATERIAL NATIVO)
# =====================================================================
st.set_page_config(
    page_title="OS Pendentes | Conecta", 
    page_icon=":material/notifications_active:", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# 2. IDENTIDADE VISUAL E IMPORTAÇÃO (CSS)
# =====================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0');

    header {visibility: hidden;}
    footer {visibility: hidden;}

    html, body, [class*="css"], [class*="st-"]  {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    span[data-testid="stIconMaterial"] {
        font-family: "Material Symbols Rounded" !important;
    }

    h1 { color: #154899 !important; font-weight: 800 !important; margin-bottom: 0px; padding-bottom: 5px; margin-top: -10px; }
    h2, h3, h4 { color: #32A347 !important; font-weight: 700 !important; }
    hr { border-top: 2px solid #32A347; margin-top: 0px; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    .block-container { padding-top: 2rem !important; }
    
    /* Alinhamento simétrico perfeito para as duas logos corporativas */
    .logo-container {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        height: 100%;
        padding-top: 15px;
    }

    [data-testid="stSidebarCollapseButton"], 
    [data-testid="collapsedControl"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    [data-testid="stSidebarCollapseButton"] span[data-testid="stIconMaterial"],
    [data-testid="collapsedControl"] span[data-testid="stIconMaterial"] {
        color: #154899 !important;
        font-size: 28px !important;
        transition: all 0.2s ease; 
    }

    [data-testid="stSidebarCollapseButton"]:hover span[data-testid="stIconMaterial"],
    [data-testid="collapsedControl"]:hover span[data-testid="stIconMaterial"] {
        color: #32A347 !important;
        transform: scale(1.15); 
    }

    [data-testid="stMetricValue"] {
        color: #154899 !important;
        font-weight: 800 !important;
    }
    
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 3. CABEÇALHO PADRÃO (TÍTULO E LOGOS ALINHADOS NA MESMA LINHA)
# =====================================================================
col_titulo, col_espaco, col_logo1, col_logo2 = st.columns([5.5, 1.5, 1.5, 1.5])

with col_titulo:
    st.markdown("<h1 style='display:flex; align-items:center; gap:12px;'><span class='material-symbols-rounded' style='font-size: 40px;'>notifications_active</span> Monitoramento Tático</h1>", unsafe_allow_html=True)
    st.markdown("**Acompanhamento de tempo de fila e criticidade de O.S. Pendentes | HU-UNIVASF**")

with col_logo1:
    st.markdown("<div class='logo-container'>", unsafe_allow_html=True)
    try: st.image("logohubrasil.png", width=200) 
    except: pass
    st.markdown("</div>", unsafe_allow_html=True)
    
with col_logo2:
    st.markdown("<div class='logo-container'>", unsafe_allow_html=True)
    try: st.image("logounivasf.png", width=140) 
    except: pass
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# =====================================================================
# 4. FUNÇÃO DE LEITURA E TRATAMENTO DOS DADOS
# =====================================================================
@st.cache_data(ttl=600) 
def carregar_fpendencias():
    caminho = os.path.join(os.getcwd(), "planilhas_gets", "02.OS_Pendentes")
    arquivos = glob.glob(os.path.join(caminho, "*.xlsx"))
    
    if not arquivos:
        return pd.DataFrame()
        
    arq_recente = max(arquivos, key=os.path.getmtime)
    
    try:
        df = pd.read_excel(arq_recente, skiprows=5)
        df.columns = df.columns.str.strip().str.upper()
        
        if 'DATA ABERTURA' in df.columns:
            df['DATA ABERTURA'] = pd.to_datetime(df['DATA ABERTURA'], errors='coerce')
            hoje = pd.to_datetime(datetime.today().date())
            df['DIAS ABERTO'] = (hoje - df['DATA ABERTURA']).dt.days
            
            bins = [-1, 5, 15, 30, 60, float('inf')]
            labels = ['0 a 5 dias', '6 a 15 dias', '16 a 30 dias', '31 a 60 dias', 'Mais de 60 dias']
            df['FAIXA DE DIAS'] = pd.cut(df['DIAS ABERTO'], bins=bins, labels=labels)
            
        return df
    except Exception as e:
        st.error(f"Erro ao processar as O.S. Pendentes: {e}")
        return pd.DataFrame()

# =====================================================================
# 5. CARREGAMENTO E FILTROS LATERAIS (SIDEBAR COM ÍCONE MATERIAL)
# =====================================================================
df_pendentes = carregar_fpendencias()

if df_pendentes.empty:
    st.warning("Nenhum dado de O.S. Pendente encontrado. Verifique se o robô já executou a extração.")
else:
    st.sidebar.markdown("<h3 style='display:flex; align-items:center; gap:8px;'><span class='material-symbols-rounded'>filter_alt</span> Filtros de Busca</h3>", unsafe_allow_html=True)
    
    df_filtrado = df_pendentes.copy()
    
    # 1. Filtro: Faixa de Dias
    if 'FAIXA DE DIAS' in df_filtrado.columns:
        todas_faixas = ['0 a 5 dias', '6 a 15 dias', '16 a 30 dias', '31 a 60 dias', 'Mais de 60 dias']
        faixa_selecionada = st.sidebar.multiselect("Faixa de Dias", todas_faixas, default=todas_faixas)
        df_filtrado = df_filtrado[df_filtrado['FAIXA DE DIAS'].isin(faixa_selecionada)]
    
    # 2. Filtro: Tipo de Manutenção
    if 'TIPO DE MANUTENÇÃO' in df_filtrado.columns:
        tipos_manut = df_filtrado['TIPO DE MANUTENÇÃO'].dropna().unique()
        tipo_selecionado = st.sidebar.multiselect("Tipo de Manutenção", tipos_manut, default=tipos_manut)
        df_filtrado = df_filtrado[df_filtrado['TIPO DE MANUTENÇÃO'].isin(tipo_selecionado)]
        
    # 3. Filtro: Estado da OS
    if 'ESTADO' in df_filtrado.columns:
        estados = df_filtrado['ESTADO'].dropna().unique()
        estado_selecionado = st.sidebar.multiselect("Status da OS", estados, default=estados)
        df_filtrado = df_filtrado[df_filtrado['ESTADO'].isin(estado_selecionado)]

# =====================================================================
# 6. EXIBIÇÃO DOS DADOS (TABELA E MENUS VISUAIS)
# =====================================================================
    st.markdown("<h3 style='display:flex; align-items:center; gap:8px;'><span class='material-symbols-rounded'>list_alt</span> Fila de Atendimento</h3>", unsafe_allow_html=True)
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Total de O.S. Exibidas", len(df_filtrado))
    
    if 'DIAS ABERTO' in df_filtrado.columns:
        media_dias = round(df_filtrado['DIAS ABERTO'].mean(), 1) if not df_filtrado.empty else 0
        os_criticas = len(df_filtrado[df_filtrado['DIAS ABERTO'] > 60])
        
        col_kpi2.metric("Média de Dias em Aberto", media_dias)
        col_kpi3.metric("O.S. Atrasadas (> 60 dias)", os_criticas, delta="Atenção Crítica", delta_color="inverse")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    colunas_visiveis = ['OS', 'EQUIPAMENTO', 'N. SÉRIE', 'ESTADO', 'FAIXA DE DIAS', 'DIAS ABERTO']
    colunas_reais = [col for col in colunas_visiveis if col in df_filtrado.columns]
    
    st.dataframe(
        df_filtrado[colunas_reais].sort_values(by='DIAS ABERTO', ascending=False) if 'DIAS ABERTO' in colunas_reais else df_filtrado,
        use_container_width=True,
        hide_index=True,
        height=500
    )
