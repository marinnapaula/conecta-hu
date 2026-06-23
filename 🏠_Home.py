import streamlit as st

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA (TELA CHEIA)
# =====================================================================
st.set_page_config(
    page_title="Conecta HU-UNIVASF",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed" # Esconde a barra lateral na Home
)

# =====================================================================
# 2. INJEÇÃO DE CSS (GRADIENTE E BOTÕES QUADRADOS)
# =====================================================================
st.markdown("""
    <style>
    /* Ocultar elementos padrão do Streamlit para visual mais limpo */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Fundo Gradiente idêntico ao do Power BI */
    .stApp {
        background: linear-gradient(135deg, #A4E5D9 0%, #F6E885 50%, #F5B08C 100%);
    }

    /* Centralizar textos */
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
        height: 130px;
        width: 100%;
        color: #154899;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    /* Efeito de Hover (passar o mouse) */
    div[data-testid="stButton"] > button:hover {
        background: rgba(255, 255, 255, 0.9);
        transform: translateY(-5px);
        border-color: #154899;
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    
    /* Permite que o texto do botão quebre linha (\n) e centralize */
    div[data-testid="stButton"] > button > div > p {
        font-size: 15px;
        font-weight: 700;
        white-space: pre-wrap; 
        text-align: center;
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

st.markdown("<div class='center-title'>⚙️<br>CONECTA HU-UNIVASF</div>", unsafe_allow_html=True)

# =====================================================================
# 4. MENU DE NAVEGAÇÃO HORIZONTAL (7 CARDS)
# =====================================================================
# Criamos 7 colunas exatas para acomodar os botões da sua imagem
c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

# Os botões usam \n para colocar o ícone em cima e o texto embaixo
# A função st.switch_page faz a navegação invisível e instantânea para a pasta pages/

with c1:
    if st.button("📊\nDASHBOARD", use_container_width=True):
        st.switch_page("pages/2_📊_Dashboard_Geral.py")
        
with c2:
    if st.button("🕰️\nHISTÓRICO", use_container_width=True):
        st.switch_page("pages/5_🕰️_Historico.py")
        
with c3:
    if st.button("🚨\nOS PENDENTES", use_container_width=True):
        st.switch_page("pages/3_🚨_OS_Pendentes.py")
        
with c4:
    # Substituí a produtividade pelo nosso calendário turbinado
    if st.button("📅\nCALENDÁRIO", use_container_width=True):
        st.switch_page("pages/1_📅_Calendario.py")
        
with c5:
    if st.button("🗺️\nMAPA DE CALOR", use_container_width=True):
        st.switch_page("pages/4_🗺️_Mapa_do_Parque.py")
        
with c6:
    if st.button("⏳\nIDADE PARQUE", use_container_width=True):
        st.toast("Módulo em desenvolvimento! Em breve.", icon="🚧")
        
with c7:
    if st.button("🖥️\nMONITORAMENTO", use_container_width=True):
        st.toast("Módulo em desenvolvimento! Em breve.", icon="🚧")


# =====================================================================
# 5. RODAPÉ (TEXTO E LOGO INFERIOR)
# =====================================================================
st.markdown("<div class='center-subtitle'>ENGENHARIA CLÍNICA - HU-UNIVASF / HU BRASIL</div>", unsafe_allow_html=True)

col_v3, col_logo_bot, col_v4 = st.columns([4.2, 1.6, 4.2])
with col_logo_bot:
    try: st.image("logohubrasil.png", use_container_width=True)
    except: pass
