import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA (ÍCONE MATERIAL NATIVO)
# =====================================================================
st.set_page_config(
    page_title="Mapa do Parque | Conecta",
    page_icon=":material/map:",
    layout="wide",
    initial_sidebar_state="collapsed" # Oculto por padrão para focar no mapa
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
    h2, h3, h4 { color: #154899 !important; font-weight: 700 !important; }
    hr { border-top: 2px solid #32A347; margin-top: 0px; }
    .block-container { padding-top: 2rem !important; }
    
    /* Alinhamento simétrico perfeito para as duas logos corporativas */
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
# 3. CABEÇALHO PADRÃO (TÍTULO E LOGOS ALINHADOS NA MESMA LINHA)
# =====================================================================
col_titulo, col_espaco, col_logo1, col_logo2 = st.columns([5.5, 1.5, 1.5, 1.5])

with col_titulo:
    st.markdown("<h1 style='display:flex; align-items:center; gap:12px;'><span class='material-symbols-rounded' style='font-size: 40px;'>map</span> Mapa do Parque Tecnológico</h1>", unsafe_allow_html=True)
    st.markdown("**Monitoramento de Disponibilidade e Concentração de Falhas por Setor | HU-UNIVASF**")

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
# 4. FUNÇÃO DE LEITURA DOS DADOS (PROCESSO ATUALIZADO VIA ROBÔ)
# =====================================================================
@st.cache_data(ttl=600)
def carregar_dados(pasta_nome):
    caminho = os.path.join(os.getcwd(), "planilhas_gets", pasta_nome)
    arquivos = glob.glob(os.path.join(caminho, "*.xlsx"))
    if not arquivos: 
        return pd.DataFrame()
    try:
        df = pd.read_excel(max(arquivos, key=os.path.getmtime), skiprows=5)
        df.columns = df.columns.str.strip().str.upper()
        return df
    except: 
        return pd.DataFrame()

with st.spinner("Analisando distribuição geográfica do parque..."):
    df_inventario = carregar_dados("04.Inventário")
    df_pendentes = carregar_dados("02.OS_Pendentes")

# =====================================================================
# 5. CÁLCULO DOS INDICADORES DE SAÚDE DO PARQUE
# =====================================================================
if df_inventario.empty:
    st.warning("Base de inventário ativo não localizada. Certifique-se de que o robô executou a extração completa.")
else:
    total_ativos = len(df_inventario)
    
    # Filtra as OS abertas que de fato retiram a disponibilidade (Manutenções Corretivas)
    if not df_pendentes.empty and 'TIPO DE MANUTENÇÃO' in df_pendentes.columns:
        df_quebrados = df_pendentes[df_pendentes['TIPO DE MANUTENÇÃO'].str.contains('CORRETIVA', na=False, case=False)]
        ativos_parados = len(df_quebrados)
    else:
        df_quebrados = df_pendentes
        ativos_parados = len(df_pendentes) if not df_pendentes.empty else 0

    disponibilidade = ((total_ativos - ativos_parados) / total_ativos) * 100 if total_ativos > 0 else 100

    # Exibição dos Cards Superiores Estilizados
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Ativos (Inventário)", f"{total_ativos:,}".replace(",", "."))
    col2.metric("Equipamentos Parados (Corretiva)", ativos_parados, delta="Crítico" if ativos_parados > 0 else "Estável", delta_color="inverse")
    col3.metric("Taxa de Disponibilidade Global", f"{disponibilidade:.1f}%", delta="Meta: 95.0%", delta_color="normal" if disponibilidade >= 95 else "inverse")
    
    st.markdown("<br>", unsafe_allow_html=True)

# =====================================================================
# 6. MAPA DE CALOR INTERATIVO (TREEMAP GRÁFICO)
# =====================================================================
    st.markdown("<h3 style='display:flex; align-items:center; gap:8px;'><span class='material-symbols-rounded' style='color:#32A347;'>local_fire_department</span> Concentração de O.S. por Localização Física</h3>", unsafe_allow_html=True)
    
    col_local = 'LOCALIZAÇÃO FÍSICA' if 'LOCALIZAÇÃO FÍSICA' in df_quebrados.columns else ('LOCALIZAÇÃO' if 'LOCALIZAÇÃO' in df_quebrados.columns else None)
    
    if not df_quebrados.empty and col_local:
        # Consolidação volumétrica de falhas por setor
        df_calor = df_quebrados.groupby(col_local).size().reset_index(name='FALHAS')
        df_calor['HOSPITAL'] = 'HU-UNIVASF' 
        
        fig = px.treemap(
            df_calor, 
            path=['HOSPITAL', col_local], 
            values='FALHAS',
            color='FALHAS',
            color_continuous_scale='Reds',
            title=None
        )
        
        # Ajuste fino de layout do gráfico Plotly para casar com a UI limpa
        fig.update_layout(
            margin=dict(t=10, l=0, r=0, b=0), 
            height=520,
            font_family="Montserrat"
        )
        fig.update_traces(
            textinfo="label+value",
            hovertemplate="<b>Setor:</b> %{label}<br><b>O.S. Abertas:</b> %{value}"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Para geração do mapa de calor dinâmico, é necessária a presença da coluna de Localização nos relatórios.")
