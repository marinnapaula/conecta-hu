import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
import os
import glob
from datetime import datetime, timezone, timedelta

# =====================================================================
# 0. LÓGICA DE DETECÇÃO DO ARQUIVO MAIS RECENTE
# =====================================================================
pasta_alvo = "planilhas_gets"
arquivos_planilha = glob.glob(os.path.join(pasta_alvo, "*.xlsx")) + glob.glob(os.path.join(pasta_alvo, "*.csv"))

if arquivos_planilha:
    # Identifica o arquivo modificado mais recentemente
    caminho_atual = max(arquivos_planilha, key=os.path.getmtime)
    timestamp = os.path.getmtime(caminho_atual)
    
    # Ajuste de Fuso Horário cravado (UTC-3)
    fuso_brasil = timezone(timedelta(hours=-3))
    data_cron = datetime.fromtimestamp(timestamp, fuso_brasil).strftime('%d/%m/%Y %H:%M')
else:
    # Proteção caso a pasta esteja vazia durante o carregamento do servidor
    caminho_atual = None
    data_cron = "Aguardando sincronização..."

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================================
st.set_page_config(
    page_title="Calendário de Manutenção - EMH | STEC HU-UNIVASF",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# 2. POP-UP (MODAL) REFORMULADO PARA TEXTOS GRANDES
# =====================================================================
@st.dialog("Detalhes da Ordem de Serviço")
def modal_detalhes(evento):
    props = evento.get('extendedProps', {})
    
    st.markdown(f"<h4 style='color: #154899; margin-top: -10px; margin-bottom: 20px;'>{evento.get('title')}</h4>", unsafe_allow_html=True)
    
    # Equipamento ganha linha inteira para não esmagar o texto
    st.markdown(f"""
        <div style='display:flex; align-items:flex-start; gap:8px; margin-bottom: 12px; font-size: 15px;'>
            <span class='material-symbols-rounded' style='color:#32A347; font-size:20px; margin-top: 2px;'>vital_signs</span> 
            <div><b>Equipamento:</b><br>{props.get('equipamento')}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style='display:flex; align-items:center; gap:8px; margin-bottom: 15px; font-size: 15px;'>
            <span class='material-symbols-rounded' style='color:#32A347; font-size:20px;'>sell</span> 
            <b>Marca:</b> {props.get('marca')}
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)
    
    # Demais itens divididos nas colunas
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div style='display:flex; align-items:center; gap:8px; margin-bottom: 10px; font-size: 14px;'><span class='material-symbols-rounded' style='color:#154899; font-size:18px;'>event</span> <b>Data:</b> {evento.get('start')[:10]}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; align-items:center; gap:8px; margin-bottom: 10px; font-size: 14px;'><span class='material-symbols-rounded' style='color:#154899; font-size:18px;'>engineering</span> <b>Serviço:</b> {props.get('tipo_servico')}</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"<div style='display:flex; align-items:center; gap:8px; margin-bottom: 10px; font-size: 14px;'><span class='material-symbols-rounded' style='color:#32A347; font-size:18px;'>location_on</span> <b>Setor:</b> {props.get('setor')}</div>", unsafe_allow_html=True)
        
        # Cor do Status Inteligente
        status_os = props.get('status')
        cor_status = '#A6ACAF' if status_os == 'EXECUTADO' else ('#E74C3C' if status_os == 'ATRASADO' else '#154899')
        icone_status = 'check_circle' if status_os == 'EXECUTADO' else ('warning' if status_os == 'ATRASADO' else 'rule')
        
        st.markdown(f"<div style='display:flex; align-items:center; gap:8px; margin-bottom: 10px; font-size: 14px;'><span class='material-symbols-rounded' style='color:{cor_status}; font-size:18px;'>{icone_status}</span> <b style='color:{cor_status};'>Status: {status_os}</b></div>", unsafe_allow_html=True)

# =====================================================================
# 3. IDENTIDADE VISUAL E IMPORTAÇÃO
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

    h1 { color: #154899 !important; font-weight: 800 !important; }
    h2, h3 { color: #32A347 !important; font-weight: 700 !important; }
    hr { border-top: 2px solid #32A347; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    .block-container { padding-top: 3.5rem !important; }

    [data-testid="stSidebarCollapseButton"], 
    [data-testid="collapsedControl"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    [data-testid="stSidebarCollapseButton"] span[data-testid="stIconMaterial"],
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="collapsedControl"] span[data-testid="stIconMaterial"],
    [data-testid="collapsedControl"] svg {
        color: #154899 !important;
        fill: #154899 !important;
        font-size: 28px !important;
        width: 28px !important;
        height: 28px !important;
        transition: all 0.2s ease; 
    }

    [data-testid="stSidebarCollapseButton"]:hover span[data-testid="stIconMaterial"],
    [data-testid="stSidebarCollapseButton"]:hover svg,
    [data-testid="collapsedControl"]:hover span[data-testid="stIconMaterial"],
    [data-testid="collapsedControl"]:hover svg {
        color: #32A347 !important;
        fill: #32A347 !important;
        transform: scale(1.15); 
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 4. BARRA LATERAL (LOGOS E FILTROS)
# =====================================================================
with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        try: st.image("logohubrasil.png", use_container_width=True)
        except: pass
    with col2:
        try: st.image("logounivasf.png", use_container_width=True)
        except: pass
    
    # TAG DE ÚLTIMA ATUALIZAÇÃO
    st.info(f"🕒 Atualizado: {data_cron}")
    
    st.markdown("---")
    st.markdown("<h3 style='display:flex; align-items:center; gap:8px;'><span class='material-symbols-rounded'>filter_alt</span> Filtros Dinâmicos</h3>", unsafe_allow_html=True)
    
    status_opcoes = ["NO PRAZO", "ATRASADO", "EXECUTADO"]
    status_selecionados = st.multiselect(
        "Mostrar Agendamento com Status:", 
        options=status_opcoes, 
        default=["NO PRAZO", "ATRASADO"] 
    )

# =====================================================================
# 5. CARREGAMENTO DOS DADOS DO GETS DINÂMICO
# =====================================================================
@st.cache_data
def carregar_dados(caminho_arquivo):
    # Se o caminho for vazio, retorna um DataFrame zerado para o app não quebrar
    if not caminho_arquivo:
        return pd.DataFrame(columns=['Situação', 'Status Alarme', 'Data Agendamento', 'Nome', 'ID', 'Tipo Equipamento', 'Marca', 'U.S.'])
        
    try:
        df = pd.read_excel(caminho_arquivo, skiprows=5)
    except:
        df = pd.read_csv(caminho_arquivo.replace('.xlsx', '.csv'), skiprows=5, sep=',')
        
    df['Data Agendamento'] = pd.to_datetime(df['Data Agendamento'], errors='coerce')
    df = df.dropna(subset=['Data Agendamento']).copy() 
    return df

df_agenda = carregar_dados(caminho_atual)

# =====================================================================
# 6. MOTOR DE CÁLCULO DE STATUS
# =====================================================================
hoje = pd.to_datetime('today').normalize()

def calcular_status(row):
    situacao = str(row.get('Situação', '')).strip().upper()
    status_alarme = str(row.get('Status Alarme', '')).strip().upper()
    data_ag = pd.to_datetime(row['Data Agendamento']).normalize()

    if situacao == 'CANCELADO' or status_alarme == 'CANCELADO':
        return 'CANCELADO'
    elif situacao == 'EXECUTADO' or status_alarme == 'EXECUTADO':
        return 'EXECUTADO'
    elif data_ag < hoje:
        return 'ATRASADO'
    else:
        return 'NO PRAZO'

if not df_agenda.empty:
    df_agenda['Status'] = df_agenda.apply(calcular_status, axis=1)
    df_agenda = df_agenda[df_agenda['Status'] != 'CANCELADO']
    df_filtrado = df_agenda[df_agenda['Status'].isin(status_selecionados)]
else:
    df_filtrado = df_agenda.copy()

# =====================================================================
# 7. CABEÇALHO E CALENDÁRIO VISUAL
# =====================================================================
st.markdown("<h1 style='display:flex; align-items:center; gap:12px;'><span class='material-symbols-rounded' style='font-size: 40px;'>calendar_month</span> Manutenção Programada</h1>", unsafe_allow_html=True)
st.markdown("**Gestão e Acompanhamento de Manutenções de EMH | HU-UNIVASF**")
st.markdown("---")

eventos_calendario = []

cores_servicos = {
    'PREVENTIVA': '#154899',       
    'CALIBRAÇÃO': '#32A347',       
    'SEGURANÇA ELÉTRICA': '#F8BB32',
    'INSPEÇÃO E TESTE OPERACIONAL': '#17a2b8' 
}

for index, row in df_filtrado.iterrows():
    tipo_servico = str(row['Nome']).strip().upper()
    data = row['Data Agendamento'].strftime("%Y-%m-%dT12:00:00") 
    equipamento = str(row['Tipo Equipamento'])
    codigo = str(row['ID']).split('|')[0] if pd.notna(row.get('ID')) else str(row.get('N° Série', 'S/N'))
    
    status_atual = row.get('Status', 'NO PRAZO')

    if status_atual == 'EXECUTADO':
        cor_evento = '#A6ACAF' 
    elif status_atual == 'ATRASADO':
        cor_evento = '#E74C3C' 
    else:
        cor_evento = cores_servicos.get(tipo_servico, '#154899') 
    
    titulo = f"[{codigo}] {tipo_servico}"
    
    eventos_calendario.append({
        "title": titulo,
        "start": data,
        "color": cor_evento,
        "equipamento": equipamento,
        "marca": str(row.get('Marca', 'N/A')),
        "setor": str(row.get('U.S.', 'N/A')),
        "tipo_servico": tipo_servico,
        "status": status_atual
    })

opcoes_calendario = {
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,listMonth",
    },
    "initialView": "dayGridMonth", 
    "locale": "pt-br",             
    "buttonText": {
        "today": "Hoje", "month": "Mês", "week": "Semana", "list": "Lista"
    }
}

# =====================================================================
# 8. RENDERIZAÇÃO E CLICK
# =====================================================================
st.markdown("<h3 style='display:flex; align-items:center; gap:8px;'><span class='material-symbols-rounded'>event_note</span> Visão Mensal de Execução</h3>", unsafe_allow_html=True)

if not df_filtrado.empty:
    calendario_gerado = calendar(events=eventos_calendario, options=opcoes_calendario)

    if calendario_gerado.get("eventClick"):
        evento_clicado = calendario_gerado["eventClick"]["event"]
        modal_detalhes(evento_clicado)
else:
    st.info("Nenhuma manutenção encontrada para exibir no momento.")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<h3 style='display:flex; align-items:center; gap:8px;'><span class='material-symbols-rounded'>list_alt</span> Lista Detalhada de Serviços</h3>", unsafe_allow_html=True)

colunas_exibir = ['Status', 'Data Agendamento', 'Nome', 'ID', 'Tipo Equipamento', 'Marca', 'U.S.']
colunas_presentes = [col for col in colunas_exibir if col in df_filtrado.columns]

st.dataframe(df_filtrado[colunas_presentes], use_container_width=True)
