import streamlit as st

# =====================================================================
# 1. CONFIGURAÇÃO PRINCIPAL (DEVE SER A PRIMEIRA LINHA DO STREAMLIT)
# =====================================================================
# Isso define o título da aba do navegador e o layout de todo o site
st.set_page_config(
    page_title="Conecta HU-UNIVASF",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# 2. ESTILIZAÇÃO DA IDENTIDADE VISUAL
# =====================================================================
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #003366; /* Azul Escuro Institucional */
        font-weight: 800;
        text-align: center;
        margin-top: -2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666666;
        text-align: center;
        margin-bottom: 3rem;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 3. CABEÇALHO
# =====================================================================
st.markdown('<div class="main-header">CONECTA HU-UNIVASF</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Centro de Comando da Engenharia Clínica | EBSERH</div>', unsafe_allow_html=True)

st.markdown("---")

# =====================================================================
# 4. CORPO DA PÁGINA INICIAL
# =====================================================================
col1, col2 = st.columns([1.2, 1])

with col1:
    st.write("### 🚀 Bem-vinda ao novo portal!")
    st.write("""
    Esta é a nova arquitetura unificada do **Conecta HU-UNIVASF**. 
    
    Deixamos as limitações do *low-code* para trás. Agora, a nossa coleta de relatórios do GETS, 
    o processamento de indicadores (TMA, Horas, Custos) e a interface de monitoramento rodam de forma 100% autônoma e em tempo real.
    """)
    
    st.info("👈 **Utilize o menu lateral esquerdo para navegar entre os módulos do sistema.**")

with col2:
    st.write("### 📂 Navegação Rápida")
    st.markdown("""
    * **📅 Calendário EMH:** Gestão visual das manutenções programadas.
    * **📊 Dashboard Geral:** Indicadores macro e visão de saúde do contrato.
    * **🚨 OS Pendentes:** *(Em desenvolvimento)*
    * **🗺️ Mapa do Parque:** *(Em desenvolvimento)*
    """)

# =====================================================================
# 5. RODAPÉ
# =====================================================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("---")
st.caption("<center>Desenvolvido pela Engenharia Clínica - HU-UNIVASF / EBSERH | 2026</center>", unsafe_allow_html=True)
