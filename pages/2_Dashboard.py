import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
from datetime import datetime

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
# 4. MOTOR DE LEITURA E CÁLCULOS
# =====================================================================
@st.cache_data(ttl=600)
def carregar_dados(pasta_nome):
    caminho = os.path.join(os.getcwd(), "planilhas_gets", pasta_nome)
    arquivos = glob.glob(os.path.join(caminho, "*.xlsx"))
    if not arquivos: return pd.DataFrame()
    try:
        df = pd.read_excel(max(arquivos, key=os.path.getmtime), skiprows=5)
        df.columns = df.columns.str.strip().str.upper()
        return df
    except: return pd.DataFrame()

with st.spinner("Atualizando painel com os dados mais recentes..."):
    df_inv = carregar_dados("04.Inventário")
    df_pend = carregar_dados("02.OS_Pendentes")
    df_enc = carregar_dados("01.OS_Encerradas")

total_equipamentos = len(df_inv) if not df_inv.empty else 0
os_abertas = len(df_pend) if not df_pend.empty else 0
os_encerradas_mes = len(df_enc) if not df_enc.empty else 0

corretivas_abertas = 0
if not df_pend.empty and 'TIPO DE MANUTENÇÃO' in df_pend.columns:
    corretivas_abertas = len(df_pend[df_pend['TIPO DE MANUTENÇÃO'].str.contains('CORRETIVA', na=False, case=False)])
else:
    corretivas_abertas = os_abertas 

disponibilidade = ((total_equipamentos - corretivas_abertas) / total_equipamentos * 100) if total_equipamentos > 0 else 100

# =====================================================================
# 5. CARDS DE INDICADORES
# =====================================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total de Equipamentos", value=f"{total_equipamentos:,}".replace(",", "."))
with col2:
    st.metric(label="Disponibilidade do Parque", value=f"{disponibilidade:.1f}%", delta="Meta: 95%", delta_color="normal" if disponibilidade >= 95 else "inverse")
with col3:
    st.metric(label="O.S. Abertas (Fila)", value=os_abertas, delta=f"{corretivas_abertas} Corretivas", delta_color="inverse")
with col4:
    st.metric(label="O.S. Encerradas (Mês)", value=os_encerradas_mes, delta="Produtividade", delta_color="normal")

st.markdown("<br>", unsafe_allow_html=True)

# =====================================================================
# 6. GRÁFICOS (PLOTLY)
# =====================================================================
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.markdown("<h4 style='display:flex; align-items:center; gap:8px; color: #154899;'><span class='material-symbols-rounded'>account_tree</span> Top 10 Setores (Gargalos)</h4>", unsafe_allow_html=True)
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
    st.markdown("<h4 style='display:flex; align-items:center; gap:8px; color: #154899;'><span class='material-symbols-rounded'>donut_large</span> Distribuição por Status</h4>", unsafe_allow_html=True)
    if not df_pend.empty and 'ESTADO' in df_pend.columns:
        df_status = df_pend['ESTADO'].value_counts().reset_index()
        df_status.columns = ['Status', 'Quantidade']
        fig_status = px.pie(df_status, values='Quantidade', names='Status', hole=0.45, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_status.update_traces(textposition='inside', textinfo='percent+label')
        fig_status.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=380, showlegend=False)
        st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.info("Aguardando coluna de status para gerar o gráfico.")
