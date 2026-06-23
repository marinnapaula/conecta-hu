import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime
import numpy as np

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================================
st.set_page_config(page_title="OS Pendentes | Conecta", page_icon="🚨", layout="wide")

st.title("🚨 Monitoramento Detalhado - O.S. Pendentes")
st.markdown("**Acompanhamento tático do tempo de fila e criticidade dos equipamentos.**")
st.markdown("---")

# =====================================================================
# 2. FUNÇÃO DE LEITURA E TRATAMENTO DOS DADOS
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
        
        # Converte a data e calcula os dias em aberto
        if 'DATA ABERTURA' in df.columns:
            df['DATA ABERTURA'] = pd.to_datetime(df['DATA ABERTURA'], errors='coerce')
            hoje = pd.to_datetime(datetime.today().date())
            df['DIAS ABERTO'] = (hoje - df['DATA ABERTURA']).dt.days
            
            # --- O "PULO DO GATO": Classificação em Faixas de Dias ---
            bins = [-1, 5, 15, 30, 60, float('inf')]
            labels = ['0 a 5 dias', '6 a 15 dias', '16 a 30 dias', '31 a 60 dias', 'Mais de 60 dias']
            df['FAIXA DE DIAS'] = pd.cut(df['DIAS ABERTO'], bins=bins, labels=labels)
            # ---------------------------------------------------------
            
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
# 4. EXIBIÇÃO DOS DADOS (TABELA INTERATIVA)
# =====================================================================
    st.markdown("### 📋 Fila de Atendimento")
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Total de O.S. Exibidas", len(df_filtrado))
    
    if 'DIAS ABERTO' in df_filtrado.columns:
        media_dias = round(df_filtrado['DIAS ABERTO'].mean(), 1) if not df_filtrado.empty else 0
        os_criticas = len(df_filtrado[df_filtrado['DIAS ABERTO'] > 60])
        
        col_kpi2.metric("Média de Dias em Aberto", media_dias)
        col_kpi3.metric("O.S. Atrasadas (> 60 dias)", os_criticas, delta="Atenção", delta_color="inverse")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Colunas que farão sentido aparecer na tabela
    colunas_visiveis = ['OS', 'EQUIPAMENTO', 'N. SÉRIE', 'ESTADO', 'FAIXA DE DIAS', 'DIAS ABERTO']
    colunas_reais = [col for col in colunas_visiveis if col in df_filtrado.columns]
    
    st.dataframe(
        df_filtrado[colunas_reais].sort_values(by='DIAS ABERTO', ascending=False) if 'DIAS ABERTO' in colunas_reais else df_filtrado,
        use_container_width=True,
        hide_index=True,
        height=500
    )
