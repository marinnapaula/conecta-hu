import streamlit as st

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA (ÍCONE MATERIAL NATIVO)
# =====================================================================
st.set_page_config(
    page_title="Conecta HU-UNIVASF",
    page_icon=":material/home:", 
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# =====================================================================
# 2. INJEÇÃO DE CSS (CARDS QUADRADOS COM ÍCONES GRANDES)
# =====================================================================
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stApp {
        background: linear-gradient(135deg, #A4E5D9 0%, #F6E885 50%, #F5B08C 100%);
    }

    .center-title {
        text-align: center;
        color: #154899;
        font-weight: 800;
        font-family: 'Montserrat', sans-serif;
        font-size: 3.5rem;
        margin-top: 10px;
        margin-bottom: 40px;
    }
    
    .center-subtitle {
        text-align: center;
        color: #154899;
        font-weight: 500;
        letter-spacing: 1px;
        margin-top: 40px;
        margin-bottom: 30px;
    }

    /* Transformar os botões do Streamlit em Cards Estilizados */
    div[data-testid="stButton"] > button {
        background: rgba(255, 255, 255, 0.45);
        border: 2px solid rgba(255, 255, 255, 0.6);
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        height: 140px; /* Leve aumento para o ícone novo */
        width: 100%;
        color: #154899;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column; /* Empilha ícone e texto */
        align-items: center;
        justify-content: center;
        gap: 8px; /* Espaço entre ícone e texto */
    }
    
    div[data-testid="stButton"] > button:hover {
        background: rgba(255, 255, 255, 0.9);
        transform: translateY(-5px);
        border-color: #154899;
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    
    /* Aumentar o tamanho do ícone nativo do Material Symbols */
    div[data-testid="stButton"] > button span[data-testid="stIconMaterial"] {
        font-size: 45px !important;
    }
    
    /* Ajuste da fonte do texto do botão */
    div[data-testid="stButton"] > button > div > p {
        font-size: 14px;
        font-weight: 700;
        margin: 0;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 3. CABEÇALHO (LOGO SUPERIOR)
# =====================================================================
st.markdown("<br>", unsafe_allow_html=True)
col_v1, col_logo_top, col_v2 = st.columns([4, 2, 4])
with col_logo_top:
    try: st.image("logounivasf.png", use_container_width=True)
    except: pass

st.markdown("<div class='center-title'><span class='material-symbols-rounded' style='font-size: 60px;'>settings_heart</span><br>CONECTA HU-UNIVASF</div>", unsafe_allow_html=True)

# =====================================================================
# 4. MENU DE NAVEGAÇÃO HORIZONTAL (7 CARDS)
# =====================================================================
c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

# Usando ícones nativos do Material Symbols e as novas rotas sem emojis
with c1:
    if st.button("DASHBOARD", icon=":material/bar_chart:", use_container_width=True):
        st.switch_page("pages/2_Dashboard_Geral.py")
        
with c2:
    if st.button("HISTÓRICO", icon=":material/manage_search:", use_container_width=True):
        st.switch_page("pages/5_Historico.py")
        
with c3:
    if st.button("OS PENDENTES", icon=":material/notifications_active:", use_container_width=True):
        st.switch_page("pages/3_OS_Pendentes.py")
        
with c4:
    if st.button("CALENDÁRIO", icon=":material/calendar_month:", use_container_width=True):
        st.switch_page("pages/1_Calendario.py")
        
with c5:
    if st.button("MAPA DE CALOR", icon=":material/map:", use_container_width=True):
        st.switch_page("pages/4_Mapa_do_Parque.py")
        
with c6:
    if st.button("IDADE PARQUE", icon=":material/hourglass_top:", use_container_width=True):
        st.toast("Módulo em desenvolvimento! Em breve.", icon="🚧")
        
with c7:
    if st.button("MONITORAMENTO", icon=":material/monitor_heart:", use_container_width=True):
        st.toast("Módulo em desenvolvimento! Em breve.", icon="🚧")

# =====================================================================
# 5. RODAPÉ (TEXTO E LOGO INFERIOR)
# =====================================================================
st.markdown("<div class='center-subtitle'>ENGENHARIA CLÍNICA - HU-UNIVASF / HU BRASIL</div>", unsafe_allow_html=True)

col_v3, col_logo_bot, col_v4 = st.columns([4.2, 1.6, 4.2])
with col_logo_bot:
    try: st.image("logohubrasil.png", use_container_width=True)
    except: pass
