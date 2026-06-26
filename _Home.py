
import streamlit as st
# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================================
st.set_page_config(
    page_title="Conecta HU-UNIVASF",
    page_icon=":material/home:", 
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# =====================================================================
# 2. INJEÇÃO DE CSS (PROPORÇÕES REFINADAS E FONTES)
# =====================================================================
st.markdown("""
    <style>
    /* Importação OBRIGATÓRIA para o ícone superior funcionar e fonte Montserrat */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0');

    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stApp {
        background: linear-gradient(135deg, #A4E5D9 0%, #F6E885 50%, #F5B08C 100%);
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Título principal mais elegante e proporcional */
    .center-title {
        text-align: center;
        color: #154899;
        font-weight: 800;
        font-family: 'Montserrat', sans-serif;
        font-size: 2.8rem; 
        margin-top: 5px;
        margin-bottom: 35px;
        line-height: 1.2;
    }
    
    .center-subtitle {
        text-align: center;
        color: #154899;
        font-weight: 500;
        letter-spacing: 1px;
        margin-top: 50px;
        margin-bottom: 30px;
        font-size: 1.1rem;
    }

    /* Cards Estilizados e Redimensionados */
    div[data-testid="stButton"] > button {
        background: rgba(255, 255, 255, 0.45);
        border: 2px solid rgba(255, 255, 255, 0.6);
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        height: 120px; /* Mais enxuto */
        width: 100%;
        color: #154899;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column; 
        align-items: center;
        justify-content: center;
        gap: 4px; /* Espaço sutil entre ícone e texto */
    }
    
    div[data-testid="stButton"] > button:hover {
        background: rgba(255, 255, 255, 0.95);
        transform: translateY(-4px);
        border-color: #154899;
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    
    /* Tamanho do ícone do botão equilibrado */
    div[data-testid="stButton"] > button span[data-testid="stIconMaterial"] {
        font-size: 38px !important; 
    }
    
    /* Fonte do botão mais moderna e legível */
    div[data-testid="stButton"] > button > div > p {
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin: 0;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 3. CABEÇALHO (LOGO SUPERIOR E TÍTULO)
# =====================================================================
st.markdown("<br>", unsafe_allow_html=True)
col_v1, col_logo_top, col_v2 = st.columns([4, 2, 4])
with col_logo_top:
    try: st.image("logounivasf.png", use_container_width=True)
    except: pass

# O ícone superior agora vai renderizar perfeitamente
st.markdown("<div class='center-title'><span class='material-symbols-rounded' style='font-size: 50px; color: #154899;'>settings_heart</span><br>CONECTA HU-UNIVASF</div>", unsafe_allow_html=True)

# =====================================================================
# 4. MENU DE NAVEGAÇÃO HORIZONTAL (7 CARDS)
# =====================================================================
c1, c2 = st.columns(2)

with c1:
    if st.button("CALENDÁRIO", icon=":material/calendar_month:", use_container_width=True):
        st.switch_page("pages/1_Calendario.py")
with c2:
    if st.button("DASHBOARD", icon=":material/bar_chart:", use_container_width=True):
        st.switch_page("pages/2_Dashboard.py")
           
# =====================================================================
# 5. RODAPÉ (TEXTO E LOGO INFERIOR)
# =====================================================================
st.markdown("<div class='center-subtitle'>ENGENHARIA CLÍNICA - HU-UNIVASF / HU BRASIL | V - 1.0 </div>", unsafe_allow_html=True)

col_v3, col_logo_bot, col_v4 = st.columns([4.2, 1.6, 4.2])
with col_logo_bot:
    try: st.image("logohubrasil.png", use_container_width=True)
    except: pass
