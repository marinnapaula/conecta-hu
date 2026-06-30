import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
import plotly.express as px
import os
import glob
import numpy as np
from datetime import datetime, timezone, timedelta

# Importando a inteligência do motor para puxar o histórico do passado
from motor_dados import carregar_mais_recente, carregar_os_encerradas

# =====================================================================
# 0. LÓGICA DE DETECÇÃO DO ARQUIVO MAIS RECENTE
# =====================================================================
pasta_alvo = os.path.join("planilhas_gets", "06. Agendamento MP")
arquivos_planilha = glob.glob(os.path.join(pasta_alvo, "*.xlsx")) + glob.glob(os.path.join(pasta_alvo, "*.csv"))

if arquivos_planilha:
    caminho_atual = max(arquivos_planilha, key=os.path.getmtime)
    timestamp = os.path.getmtime(caminho_atual)
    fuso_brasil = timezone(timedelta(hours=-3))
    data_cron = datetime.fromtimestamp(timestamp, fuso_brasil).strftime('%d/%m/%Y %H:%M')
else:
    caminho_atual = None
    data_cron = "Aguardando sincronização..."

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================================
st.set_page_config(
    page_title="Calendário | Conecta",
    page_icon=":material/calendar_month:",
    layout="wide",
    initial_sidebar_state="collapsed" # Deixei fechado por padrão para dar mais espaço à tela
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

    h1 { color: #154899 !important; font-weight: 800 !important; margin-bottom: 0px; padding-bottom: 5px; margin-top: -10px; }
    h2, h3 { color: #32A347 !important; font-weight: 700 !important; }
    hr { border-top: 2px solid #32A347; margin-top: 0px; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    .block-container { padding-top: 2rem !important; }
    
    /* ESSA É A CLASSE QUE FAZ O ALINHAMENTO PERFEITO DAS LOGOS */
    .logo-container {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        height: 100%;
        padding-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 3. CABEÇALHO PADRÃO (TÍTULO E LOGOS NA MESMA LINHA)
# =====================================================================
col_titulo, col_espaco, col_logo1, col_logo2 = st.columns([5.5, 1.5, 1.5, 1.5])

with col_titulo:
    st.markdown("<h1 style='display:flex; align-items:center; gap:12px;'><span class='material-symbols-rounded' style='font-size: 40px;'>calendar_month</span> Manutenção Programada</h1>", unsafe_allow_html=True)
    st.markdown("**Gestão, Acompanhamento e Auditoria de EMH | HU-UNIVASF**")

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
# 4. CARREGAMENTO DOS DADOS (AGENDAMENTO + HISTÓRICO)
# =====================================================================
@st.cache_data(ttl=600)
def carregar_dados_agenda(caminho_arquivo):
    if not caminho_arquivo:
        return pd.DataFrame(columns=['Situação', 'Status Alarme', 'Data Agendamento', 'Nome', 'ID', 'Tipo Equipamento', 'Marca', 'U.S.'])
    try: df = pd.read_excel(caminho_arquivo, skiprows=5)
    except: df = pd.read_csv(caminho_arquivo.replace('.xlsx', '.csv'), skiprows=5, sep=',')
        
    df['Data Agendamento'] = pd.to_datetime(df['Data Agendamento'], errors='coerce')
    df = df.dropna(subset=['Data Agendamento']).copy() 
    return df

@st.cache_data(ttl=600)
def carregar_historico_encerradas():
    return carregar_os_encerradas()

with st.spinner("Sincronizando calendário e base de auditoria..."):
    df_agenda = carregar_dados_agenda(caminho_atual)
    df_enc = carregar_historico_encerradas()

hoje = pd.to_datetime('today').normalize()

def calcular_status(row):
    situacao = str(row.get('Situação', '')).strip().upper()
    status_alarme = str(row.get('Status Alarme', '')).strip().upper()
    data_ag = pd.to_datetime(row['Data Agendamento']).normalize()

    if situacao == 'CANCELADO' or status_alarme == 'CANCELADO': return 'CANCELADO'
    elif situacao == 'EXECUTADO' or status_alarme == 'EXECUTADO': return 'EXECUTADO'
    elif data_ag < hoje: return 'ATRASADO'
    else: return 'NO PRAZO'

if not df_agenda.empty:
    df_agenda['Status'] = df_agenda.apply(calcular_status, axis=1)
    df_agenda = df_agenda[df_agenda['Status'] != 'CANCELADO']

# =====================================================================
# 5. ESTRUTURA DE ABAS
# =====================================================================
tab_calendario, tab_auditoria = st.tabs(["📅 Calendário Operacional", "📋 Auditoria VIGIOSP (Linha do Tempo)"])

# ---------------------------------------------------------------------
# ABA 1: CALENDÁRIO OPERACIONAL (O SEU CÓDIGO ORIGINAL)
# ---------------------------------------------------------------------
with tab_calendario:
    st.info(f"🕒 **Última Atualização da Base:** {data_cron}")
    
    # Filtro movido para dentro da aba para não sujar a VIGIOSP
    status_opcoes = ["NO PRAZO", "ATRASADO", "EXECUTADO"]
    status_selecionados = st.multiselect("Filtrar Visão do Calendário por Status:", options=status_opcoes, default=["NO PRAZO", "ATRASADO"])
    
    df_filtrado = df_agenda[df_agenda['Status'].isin(status_selecionados)] if not df_agenda.empty else pd.DataFrame()

    @st.dialog("Detalhes da Ordem de Serviço")
    def modal_detalhes(evento):
        props = evento.get('extendedProps', {})
        st.markdown(f"<h4 style='color: #154899; margin-top: -10px; margin-bottom: 20px;'>{evento.get('title')}</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; align-items:flex-start; gap:8px; margin-bottom: 12px; font-size: 15px;'><span class='material-symbols-rounded' style='color:#32A347; font-size:20px; margin-top: 2px;'>vital_signs</span> <div><b>Equipamento:</b><br>{props.get('equipamento')}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; align-items:center; gap:8px; margin-bottom: 15px; font-size: 15px;'><span class='material-symbols-rounded' style='color:#32A347; font-size:20px;'>sell</span> <b>Marca:</b> {props.get('marca')}</div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div style='display:flex; align-items:center; gap:8px; margin-bottom: 10px; font-size: 14px;'><span class='material-symbols-rounded' style='color:#154899; font-size:18px;'>event</span> <b>Data:</b> {evento.get('start')[:10]}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='display:flex; align-items:center; gap:8px; margin-bottom: 10px; font-size: 14px;'><span class='material-symbols-rounded' style='color:#154899; font-size:18px;'>engineering</span> <b>Serviço:</b> {props.get('tipo_servico')}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='display:flex; align-items:center; gap:8px; margin-bottom: 10px; font-size: 14px;'><span class='material-symbols-rounded' style='color:#32A347; font-size:18px;'>location_on</span> <b>Setor:</b> {props.get('setor')}</div>", unsafe_allow_html=True)
            status_os = props.get('status')
            cor_status = '#A6ACAF' if status_os == 'EXECUTADO' else ('#E74C3C' if status_os == 'ATRASADO' else '#154899')
            icone_status = 'check_circle' if status_os == 'EXECUTADO' else ('warning' if status_os == 'ATRASADO' else 'rule')
            st.markdown(f"<div style='display:flex; align-items:center; gap:8px; margin-bottom: 10px; font-size: 14px;'><span class='material-symbols-rounded' style='color:{cor_status}; font-size:18px;'>{icone_status}</span> <b style='color:{cor_status};'>Status: {status_os}</b></div>", unsafe_allow_html=True)

    eventos_calendario = []
    cores_servicos = {'PREVENTIVA': '#154899', 'CALIBRAÇÃO': '#32A347', 'SEGURANÇA ELÉTRICA': '#F8BB32', 'INSPEÇÃO E TESTE OPERACIONAL': '#17a2b8'}

    for index, row in df_filtrado.iterrows():
        tipo_servico = str(row['Nome']).strip().upper()
        data = row['Data Agendamento'].strftime("%Y-%m-%dT12:00:00") 
        equipamento = str(row['Tipo Equipamento'])
        codigo = str(row['ID']).split('|')[0] if pd.notna(row.get('ID')) else str(row.get('N° Série', 'S/N'))
        status_atual = row.get('Status', 'NO PRAZO')

        if status_atual == 'EXECUTADO': cor_evento = '#A6ACAF' 
        elif status_atual == 'ATRASADO': cor_evento = '#E74C3C' 
        else: cor_evento = cores_servicos.get(tipo_servico, '#154899') 
        
        eventos_calendario.append({
            "title": f"[{codigo}] {tipo_servico}", "start": data, "color": cor_evento,
            "equipamento": equipamento, "marca": str(row.get('Marca', 'N/A')),
            "setor": str(row.get('U.S.', 'N/A')), "tipo_servico": tipo_servico, "status": status_atual
        })

    opcoes_calendario = {
        "headerToolbar": {"left": "today prev,next", "center": "title", "right": "dayGridMonth,timeGridWeek,listMonth"},
        "initialView": "dayGridMonth", "locale": "pt-br",
        "buttonText": {"today": "Hoje", "month": "Mês", "week": "Semana", "list": "Lista"}
    }

    st.markdown("<h3 style='display:flex; align-items:center; gap:8px;'><span class='material-symbols-rounded'>event_note</span> Visão Mensal de Execução</h3>", unsafe_allow_html=True)
    if not df_filtrado.empty:
        calendario_gerado = calendar(events=eventos_calendario, options=opcoes_calendario)
        if calendario_gerado.get("eventClick"):
            evento_clicado = calendario_gerado["eventClick"]["event"]
            modal_detalhes(evento_clicado)
    else:
        st.info("Nenhuma manutenção encontrada para os filtros selecionados.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h3 style='display:flex; align-items:center; gap:8px;'><span class='material-symbols-rounded'>list_alt</span> Lista Detalhada de Serviços</h3>", unsafe_allow_html=True)
    colunas_exibir = ['Status', 'Data Agendamento', 'Nome', 'ID', 'Tipo Equipamento', 'Marca', 'U.S.']
    colunas_presentes = [col for col in colunas_exibir if col in df_filtrado.columns]
    st.dataframe(df_filtrado[colunas_presentes], use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# ABA 2: AUDITORIA VIGIOSP (GANTT E PDF)
# ---------------------------------------------------------------------
with tab_auditoria:
    st.markdown("Filtre o equipamento para rastrear as manutenções já executadas e as próximas projetadas no agendamento.")
    
    with st.container(border=True):
        c_busca1, c_busca2 = st.columns([2, 1])
        
        # Consolida lista de equipamentos unindo o passado (df_enc) e o futuro (df_agenda)
        eq_disp = set()
        if not df_enc.empty and 'DESCRIÇÃO' in df_enc.columns: eq_disp.update(df_enc['DESCRIÇÃO'].dropna().unique())
        if not df_agenda.empty and 'Tipo Equipamento' in df_agenda.columns: eq_disp.update(df_agenda['Tipo Equipamento'].dropna().unique())
        
        filtro_aud_eq = c_busca1.multiselect("Equipamento(s):", sorted(list(eq_disp)), placeholder="Busque os equipamentos alvo da auditoria...")
        filtro_aud_sn = c_busca2.text_input("Número de Série (Opcional):", placeholder="Busca exata...")

    if filtro_aud_eq or filtro_aud_sn:
        lista_auditoria = []
        
        # 1. Puxando o Passado (O.S. Encerradas)
        if not df_enc.empty:
            df_enc_aud = df_enc.copy()
            if filtro_aud_eq: df_enc_aud = df_enc_aud[df_enc_aud['DESCRIÇÃO'].isin(filtro_aud_eq)]
            if filtro_aud_sn: df_enc_aud = df_enc_aud[df_enc_aud['N.º SÉRIE'].astype(str).str.contains(filtro_aud_sn, case=False, na=False)]
            
            if not df_enc_aud.empty:
                df_enc_aud = df_enc_aud[['O.S.', 'DESCRIÇÃO', 'N.º SÉRIE', 'ABERTURA', 'ENCERRAMENTO', 'CLASSE']].copy()
                df_enc_aud.rename(columns={'ABERTURA': 'Data_Inicio', 'ENCERRAMENTO': 'Data_Fim', 'CLASSE': 'Serviço'}, inplace=True)
                df_enc_aud['Status'] = '✔️ Executado'
                lista_auditoria.append(df_enc_aud)

        # 2. Puxando o Futuro (Agendamento MP)
        if not df_agenda.empty:
            df_ag_aud = df_agenda.copy()
            if filtro_aud_eq: df_ag_aud = df_ag_aud[df_ag_aud['Tipo Equipamento'].isin(filtro_aud_eq)]
            if filtro_aud_sn: df_ag_aud = df_ag_aud[df_ag_aud['ID'].astype(str).str.contains(filtro_aud_sn, case=False, na=False)]
            
            if not df_ag_aud.empty:
                # O ID no agendamento costuma vir como "12345 | SN: ABCD". Vamos extrair só o SN para o relatório ficar bonito.
                df_ag_aud['N.º SÉRIE'] = df_ag_aud['ID'].astype(str).apply(lambda x: x.split('SN:')[-1].strip() if 'SN:' in x else x)
                
                df_ag_aud = df_ag_aud[['Tipo Equipamento', 'N.º SÉRIE', 'Data Agendamento', 'Nome', 'Status']].copy()
                df_ag_aud.rename(columns={'Tipo Equipamento': 'DESCRIÇÃO', 'Data Agendamento': 'Data_Inicio', 'Nome': 'Serviço'}, inplace=True)
                df_ag_aud['O.S.'] = 'AGENDADO'
                df_ag_aud['Data_Fim'] = df_ag_aud['Data_Inicio'] # No agendamento, projetamos conclusão pro mesmo dia
                
                # Traduz status do agendamento para o padrão visual
                df_ag_aud['Status'] = np.where(df_ag_aud['Status'] == 'ATRASADO', '⚠️ Atrasado', '⏳ Programado')
                lista_auditoria.append(df_ag_aud)

        # 3. Consolidação e Gráficos
        if lista_auditoria:
            df_auditoria = pd.concat(lista_auditoria, ignore_index=True)
            df_auditoria['Data_Inicio'] = pd.to_datetime(df_auditoria['Data_Inicio'], errors='coerce')
            df_auditoria['Data_Fim'] = pd.to_datetime(df_auditoria['Data_Fim'], errors='coerce')
            df_auditoria = df_auditoria.dropna(subset=['Data_Inicio']).sort_values('Data_Inicio', ascending=False)
            
            # Formata eixo Y para o Gantt
            df_auditoria['Equip_ID'] = df_auditoria['DESCRIÇÃO'] + " (SN: " + df_auditoria['N.º SÉRIE'].astype(str) + ")"

            # Gráfico Gantt
            with st.container(border=True):
                st.markdown("##### ⏱️ Linha do Tempo de Intervenções (Gantt)")
                cores_status = {'✔️ Executado': '#70ad47', '⏳ Programado': '#154899', '⚠️ Atrasado': '#c00000'}
                
                fig_gantt = px.timeline(
                    df_auditoria, x_start="Data_Inicio", x_end="Data_Fim", y="Equip_ID", color="Status",
                    color_discrete_map=cores_status, hover_name="O.S.", hover_data=["Serviço"]
                )
                fig_gantt.update_yaxes(autorange="reversed")
                fig_gantt.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig_gantt, use_container_width=True)

            # Relatório em Tabela (Pronto para Ctrl+P)
            with st.container(border=True):
                st.markdown("##### 📋 Relatório Consolidado de Engenharia Clínica")
                st.caption("Pressione **Ctrl + P** e escolha 'Salvar como PDF' para exportar esta visão.")
                
                df_print = df_auditoria[['O.S.', 'DESCRIÇÃO', 'N.º SÉRIE', 'Serviço', 'Status', 'Data_Inicio', 'Data_Fim']].copy()
                df_print['Data_Inicio'] = df_print['Data_Inicio'].dt.strftime('%d/%m/%Y')
                df_print['Data_Fim'] = np.where(df_print['O.S.'] == 'AGENDADO', '-', df_print['Data_Fim'].dt.strftime('%d/%m/%Y'))
                
                st.dataframe(
                    df_print, use_container_width=True, hide_index=True,
                    column_config={"O.S.": "Nº O.S.", "DESCRIÇÃO": "Equipamento", "N.º SÉRIE": "Nº Série", "Data_Inicio": "Abertura / Prevista", "Data_Fim": "Conclusão Real"}
                )
        else:
            st.warning("Nenhum histórico encontrado para os parâmetros informados.")
