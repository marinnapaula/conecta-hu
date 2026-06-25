import streamlit as st
import pandas as pd
import plotly.express as px
import os
# Importando o cérebro que criamos!
from motor_dados import (
    carregar_mais_recente, 
    carregar_os_encerradas, 
    limpar_dimensao_equipamentos, 
    enriquecer_base_inventario
)

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================================
st.set_page_config(
    page_title="Dashboard | Conecta",
    page_icon=":material/bar_chart:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================================
# 2. IDENTIDADE VISUAL E IMPORTAÇÃO (CSS)
# =====================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0');

    html, body, [class*="css"], [class*="st-"]  {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    span[data-testid="stIconMaterial"] {
        font-family: "Material Symbols Rounded" !important;
    }

    h1 { color: #154899 !important; font-weight: 800 !important; margin-bottom: 0px; padding-bottom: 5px; }
    h2, h3, h4 { color: #32A347 !important; font-weight: 700 !important; }
    hr { border-top: 2px solid #32A347; margin-top: 0px; }
    .block-container { padding-top: 2rem !important; }
    
    .logo-container {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        height: 100%;
        padding-top: 15px;
    }
    
    [data-testid="stMetricValue"] {
        color: #154899 !important;
        font-weight: 800 !important;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 3. CABEÇALHO PADRÃO (TÍTULO E LOGOS NA MESMA LINHA)
# =====================================================================
col_titulo, col_espaco, col_logo1, col_logo2 = st.columns([5.5, 1.5, 1.5, 1.5])

with col_titulo:
    st.markdown("<h1 style='display:flex; align-items:center; gap:12px; margin-top: -10px;'><span class='material-symbols-rounded' style='font-size: 40px;'>bar_chart</span> Dashboard Executivo</h1>", unsafe_allow_html=True)
    st.markdown("**Visão Macro de Disponibilidade, Fila e Produtividade | HU-UNIVASF**")

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
# 4. MOTOR DE LEITURA E CÁLCULOS (MODULO 1)
# =====================================================================
# Usamos o cache do Streamlit para não processar a base toda vez que você clicar em algo
@st.cache_data(ttl=600)
def processar_dados_painel():
    # 1. Busca os arquivos brutos usando o motor
    df_inv_bruto = carregar_mais_recente("04.Inventário")
    df_pend = carregar_mais_recente("02.OS_Pendentes")
    df_enc = carregar_os_encerradas()
    
    # 2. Limpa e processa o Inventário com as MPs
    df_inv_limpo = limpar_dimensao_equipamentos(df_inv_bruto)
    df_inv = enriquecer_base_inventario(df_inv_limpo, df_enc)
    
    return df_inv, df_pend, df_enc

with st.spinner("Processando Inteligência do Parque Tecnológico..."):
    df_inv, df_pend, df_enc = processar_dados_painel()

# --- Cálculos do DAX Traduzidos ---
total_equipamentos = 0
pct_critico_idade = 0.0
qtd_critico_idade = 0
pct_mp_ok = 0.0
qtd_mp_ok = 0
qtd_atraso_critico = 0
qtd_mp_nr = 0

if not df_inv.empty:
    # A base do nosso filtro é a contagem de equipamentos ATIVOS
    df_ativos = df_inv[df_inv['STATUS_EQUIPAMENTO'] == 'ATIVO']
    total_equipamentos = len(df_ativos)

    if total_equipamentos > 0:
        # Equipamentos > 10 Anos
        qtd_critico_idade = len(df_ativos[df_ativos['Idade Equipamento Num'] > 10])
        pct_critico_idade = (qtd_critico_idade / total_equipamentos) * 100
        
        # Conformidade de MP (Ordem 6 = OK, Ordem 1 = NR, Ordem 2 e 3 = Vencidos > 1 ano)
        qtd_mp_ok = len(df_ativos[df_ativos['Ordem Status MP'] == 6])
        pct_mp_ok = (qtd_mp_ok / total_equipamentos) * 100
        
        qtd_mp_nr = len(df_ativos[df_ativos['Ordem Status MP'] == 1])
        qtd_mp_vencida_1a = len(df_ativos[df_ativos['Ordem Status MP'] == 3])
        qtd_mp_vencida_2a = len(df_ativos[df_ativos['Ordem Status MP'] == 2])
        qtd_atraso_critico = qtd_mp_vencida_1a + qtd_mp_vencida_2a

# =====================================================================
# 5. CARDS DE INDICADORES (SAÚDE DO PARQUE)
# =====================================================================
st.markdown("<h3 style='display:flex; align-items:center; gap:8px;'><span class='material-symbols-rounded'>health_and_safety</span> Saúde do Parque Tecnológico</h3>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Parque Ativo", 
        value=f"{total_equipamentos:,}".replace(",", ".")
    )
with col2:
    st.metric(
        label="Críticos (> 10 anos)", 
        value=f"{pct_critico_idade:.1f}%", 
        delta=f"{qtd_critico_idade} ativos antigos", 
        delta_color="inverse"
    )
with col3:
    st.metric(
        label="Conformidade de MP (OK)", 
        value=f"{pct_mp_ok:.1f}%",
        delta="Meta: 100%",
        delta_color="normal" if pct_mp_ok == 100 else "inverse"
    )
with col4:
    st.metric(
        label="Alerta: MP Atrasada (> 1 ano)", 
        value=qtd_atraso_critico,
        delta=f"{qtd_mp_nr} Nunca Realizadas",
        delta_color="inverse"
    )

st.markdown("<br><hr><br>", unsafe_allow_html=True)

# =====================================================================
# 6. GRÁFICOS (FILA DE O.S.)
# =====================================================================
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.markdown("<h4 style='display:flex; align-items:center; gap:8px; color: #154899;'><span class='material-symbols-rounded'>account_tree</span> Top 10 Setores (Gargalos na Fila)</h4>", unsafe_allow_html=True)
    if not df_pend.empty:
        col_local = 'LOCALIZAÇÃO FÍSICA' if 'LOCALIZAÇÃO FÍSICA' in df_pend.columns else ('LOCALIZAÇÃO' if 'LOCALIZAÇÃO' in df_pend.columns else None)
        if col_local:
            df_setor = df_pend[col_local].value_counts().head(10).reset_index()
            df_setor.columns = ['Setor', 'Quantidade']
            fig_setor = px.bar(df_setor, x='Quantidade', y='Setor', orientation='h', text='Quantidade', color_discrete_sequence=['#154899'])
            fig_setor.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=0, b=0), height=380)
            st.plotly_chart(fig_setor, use_container_width=True)
        else:
            st.info("Aguardando coluna de localização para gerar o gráfico.")
    else:
        st.success("Nenhuma OS pendente no momento!")

with col_graf2:
    st.markdown("<h4 style='display:flex; align-items:center; gap:8px; color: #154899;'><span class='material-symbols-rounded'>donut_large</span> Distribuição de Status (Fila)</h4>", unsafe_allow_html=True)
    if not df_pend.empty and 'ESTADO' in df_pend.columns:
        df_status = df_pend['ESTADO'].value_counts().reset_index()
        df_status.columns = ['Status', 'Quantidade']
        fig_status = px.pie(df_status, values='Quantidade', names='Status', hole=0.45, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_status.update_traces(textposition='inside', textinfo='percent+label')
        fig_status.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=380, showlegend=False)
        st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.info("Aguardando coluna de status para gerar o gráfico.")
