import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
import plotly.express as px
import os
import glob
import numpy as np
from datetime import datetime, timezone, timedelta

# Importando a inteligência do motor para puxar o histórico, pendências e o inventário
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
    initial_sidebar_state="collapsed"
)

# =====================================================================
# 2. IDENTIDADE VISUAL E IMPORTAÇÃO (CSS)
# =====================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0');

    html, body, [class*="css"], [class*="st-"]  { font-family: 'Montserrat', sans-serif !important; }
    span[data-testid="stIconMaterial"] { font-family: "Material Symbols Rounded" !important; }

    h1 { color: #154899 !important; font-weight: 800 !important; margin-bottom: 0px; padding-bottom: 5px; margin-top: -10px; }
    h2, h3 { color: #32A347 !important; font-weight: 700 !important; }
    hr { border-top: 2px solid #32A347; margin-top: 0px; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    .block-container { padding-top: 2rem !important; }
    
    .logo-container {
        display: flex; align-items: center; justify-content: flex-end;
        height: 100%; padding-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 3. CABEÇALHO PADRÃO
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
# 4. CARREGAMENTO DOS DADOS (AGENDAMENTO + HISTÓRICO + INVENTÁRIO + PENDENTES)
# =====================================================================
@st.cache_data(ttl=600)
def carregar_dados_agenda(caminho_arquivo):
    if not caminho_arquivo: return pd.DataFrame(columns=['Situação', 'Status Alarme', 'Data Agendamento', 'Nome', 'ID', 'Tipo Equipamento', 'Marca', 'U.S.'])
    try: df = pd.read_excel(caminho_arquivo, skiprows=5)
    except: df = pd.read_csv(caminho_arquivo.replace('.xlsx', '.csv'), skiprows=5, sep=',')
    df['Data Agendamento'] = pd.to_datetime(df['Data Agendamento'], errors='coerce')
    return df.dropna(subset=['Data Agendamento']).copy() 

@st.cache_data(ttl=600)
def carregar_historico_encerradas(): return carregar_os_encerradas()

@st.cache_data(ttl=600)
def carregar_inventario(): return carregar_mais_recente("04.Inventário")

@st.cache_data(ttl=600)
def carregar_pendentes(): return carregar_mais_recente("02.OS_Pendentes")

with st.spinner("Sincronizando bancos de dados de auditoria..."):
    df_agenda = carregar_dados_agenda(caminho_atual)
    df_enc = carregar_historico_encerradas()
    df_inv = carregar_inventario()
    df_pend_bruto = carregar_pendentes()

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
# ABA 1: CALENDÁRIO OPERACIONAL
# ---------------------------------------------------------------------
with tab_calendario:
    st.info(f"🕒 **Última Atualização da Base:** {data_cron}")
    
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
# ABA 2: AUDITORIA VIGIOSP (SUPER BUSCA INTELIGENTE COM TRÊS VIAS)
# ---------------------------------------------------------------------
with tab_auditoria:
    st.markdown("Filtre o equipamento para rastrear as manutenções já executadas, as que estão em execução ativa e as próximas projetadas.")
    
    with st.container(border=True):
        c_busca1, c_busca2 = st.columns([1.5, 1.5])
        
        eq_disp = set()
        c_desc_enc = next((c for c in ['TIPO EQUIP.', 'TIPO EQUIPAMENTO', 'DESCRIÇÃO', 'EQUIPAMENTO'] if not df_enc.empty and c in df_enc.columns), None)
        if c_desc_enc: eq_disp.update(df_enc[c_desc_enc].dropna().unique())
        
        c_desc_ag = next((c for c in ['Tipo Equipamento', 'Tipo Equip.'] if not df_agenda.empty and c in df_agenda.columns), None)
        if c_desc_ag: eq_disp.update(df_agenda[c_desc_ag].dropna().unique())
        
        filtro_aud_eq = c_busca1.multiselect("Equipamento(s):", sorted(list(eq_disp)), placeholder="Busque os equipamentos alvo da auditoria...")
        filtro_aud_sn = c_busca2.text_input("Número(s) de Série ou Patrimônio (Separe por vírgula):", placeholder="Ex: 59885V/00, HU-00923, 9876...")

    if filtro_aud_eq or filtro_aud_sn:
        lista_auditoria = []
        padrao_sn = None
        
        if filtro_aud_sn:
            import re
            termos_iniciais = [s.strip() for s in filtro_aud_sn.split(',') if s.strip()]
            termos_expandidos = set(termos_iniciais)
            
            if not df_inv.empty:
                c_inv_sn = next((c for c in ['N.º SÉRIE', 'N. SÉRIE', 'Nº SÉRIE', 'SÉRIE'] if c in df_inv.columns), None)
                c_inv_id = next((c for c in ['IDENTIFICADOR', 'ID', 'PATRIMÔNIO', 'PATRIMONIO'] if c in df_inv.columns), None)
                
                if c_inv_sn and c_inv_id:
                    mask_inv = df_inv[c_inv_sn].astype(str).isin(termos_iniciais) | df_inv[c_inv_id].astype(str).isin(termos_iniciais)
                    termos_expandidos.update(df_inv.loc[mask_inv, c_inv_sn].dropna().astype(str).tolist())
                    termos_expandidos.update(df_inv.loc[mask_inv, c_inv_id].dropna().astype(str).tolist())
            
            termos_expandidos.discard('')
            termos_expandidos.discard('nan')
            termos_expandidos.discard('N/I')
            termos_expandidos.discard('None')
            
            if termos_expandidos:
                padrao_sn = '|'.join([re.escape(t) for t in termos_expandidos])
        
        # 1. VIA DO PASSADO: O.S. Encerradas (Filtrado estritamente por Programadas)
        if not df_enc.empty:
            df_enc_aud = df_enc.copy()
            c_os = next((c for c in ['O.S.', 'OS', 'N.º O.S.'] if c in df_enc_aud.columns), None)
            c_sn_enc = next((c for c in ['N. SÉRIE', 'N.º SÉRIE', 'Nº SÉRIE', 'SÉRIE'] if c in df_enc_aud.columns), None)
            c_ab = next((c for c in ['ABERTURA', 'DATA ABERTURA'] if c in df_enc_aud.columns), None)
            c_en = next((c for c in ['ENCERRAMENTO', 'DATA ENCERRAMENTO'] if c in df_enc_aud.columns), None)
            c_cl = next((c for c in ['CLASSE', 'TIPO MANUTENÇÃO'] if c in df_enc_aud.columns), None)

            if c_desc_enc and filtro_aud_eq: df_enc_aud = df_enc_aud[df_enc_aud[c_desc_enc].isin(filtro_aud_eq)]
            
            if padrao_sn: 
                mask_sn = df_enc_aud[c_sn_enc].astype(str).str.contains(padrao_sn, case=False, na=False, regex=True) if c_sn_enc else False
                c_id_enc = next((c for c in ['IDENTIFICADOR', 'ID', 'PATRIMÔNIO', 'PATRIMONIO'] if c in df_enc_aud.columns), None)
                mask_id = df_enc_aud[c_id_enc].astype(str).str.contains(padrao_sn, case=False, na=False, regex=True) if c_id_enc else False
                df_enc_aud = df_enc_aud[mask_sn | mask_id]
            
            if c_cl and not df_enc_aud.empty:
                df_enc_aud = df_enc_aud[df_enc_aud[c_cl].astype(str).str.upper().str.contains('PREV|CALIB|MP|PROG|ROTINA|SEGURANÇA|INSPEÇÃO|TESTE|VALIDAÇÃO|QUALIFICAÇÃO')]
            
            if not df_enc_aud.empty and all([c_os, c_desc_enc, c_sn_enc, c_ab, c_en, c_cl]):
                df_enc_aud = df_enc_aud[[c_os, c_desc_enc, c_sn_enc, c_ab, c_en, c_cl]].copy()
                df_enc_aud.rename(columns={c_os: 'O.S.', c_desc_enc: 'DESCRIÇÃO', c_sn_enc: 'N.º SÉRIE', c_ab: 'Data_Inicio', c_en: 'Data_Fim', c_cl: 'Serviço'}, inplace=True)
                df_enc_aud['Status'] = '✔️ Executado'
                lista_auditoria.append(df_enc_aud)

      # 2. VIA DO PRESENTE: O.S. Pendentes (Em Execução com Estado Interno do Sistema)
        if not df_pend_bruto.empty:
            df_p_aud = df_pend_bruto.copy()
            c_os_p = next((c for c in ['O.S.', 'OS', 'N.º O.S.'] if c in df_p_aud.columns), None)
            c_sn_p = next((c for c in ['N. SÉRIE', 'N.º SÉRIE', 'Nº SÉRIE', 'SÉRIE'] if c in df_p_aud.columns), None)
            c_ab_p = next((c for c in ['ABERTURA', 'DATA ABERTURA'] if c in df_p_aud.columns), None)
            c_cl_p = next((c for c in ['CLASSE', 'TIPO MANUTENÇÃO'] if c in df_p_aud.columns), None)
            c_est_p = next((c for c in ['ESTADO', 'STATUS', 'SITUAÇÃO'] if c in df_p_aud.columns), None)
            
            # CORREÇÃO: Busca inteligente da coluna de descrição ESPECÍFICA para a base de Pendentes
            c_desc_p = next((c for c in ['TIPO EQUIP.', 'TIPO EQUIPAMENTO', 'DESCRIÇÃO', 'EQUIPAMENTO'] if c in df_p_aud.columns), None)

            if c_desc_p and filtro_aud_eq: df_p_aud = df_p_aud[df_p_aud[c_desc_p].isin(filtro_aud_eq)]
            
            if padrao_sn: 
                mask_sn = df_p_aud[c_sn_p].astype(str).str.contains(padrao_sn, case=False, na=False, regex=True) if c_sn_p else False
                c_id_p = next((c for c in ['IDENTIFICADOR', 'ID', 'PATRIMÔNIO', 'PATRIMONIO'] if c in df_p_aud.columns), None)
                mask_id = df_p_aud[c_id_p].astype(str).str.contains(padrao_sn, case=False, na=False, regex=True) if c_id_p else False
                df_p_aud = df_p_aud[mask_sn | mask_id]
                
            if c_cl_p and not df_p_aud.empty:
                df_p_aud = df_p_aud[df_p_aud[c_cl_p].astype(str).str.upper().str.contains('PREV|CALIB|MP|PROG|ROTINA|SEGURANÇA|INSPEÇÃO|TESTE|VALIDAÇÃO|QUALIFICAÇÃO')]

            # Usa o c_desc_p para fatiar e renomear com segurança
            if not df_p_aud.empty and all([c_os_p, c_desc_p, c_sn_p, c_ab_p, c_cl_p]):
                df_p_aud = df_p_aud[[c_os_p, c_desc_p, c_sn_p, c_ab_p, c_cl_p, c_est_p]].copy() if c_est_p else df_p_aud[[c_os_p, c_desc_p, c_sn_p, c_ab_p, c_cl_p]].copy()
                df_p_aud.rename(columns={c_os_p: 'O.S.', c_desc_p: 'DESCRIÇÃO', c_sn_p: 'N.º SÉRIE', c_ab_p: 'Data_Inicio', c_cl_p: 'Serviço'}, inplace=True)
                df_p_aud['Data_Fim'] = pd.Timestamp(datetime.today().date())
                
                if c_est_p:
                    df_p_aud['Status'] = '⚙️ Em Execução (' + df_p_aud[c_est_p].astype(str).str.strip().str.upper() + ')'
                else:
                    df_p_aud['Status'] = '⚙️ Em Execução'
                    
                df_p_aud.drop(columns=[c_est_p], inplace=True, errors='ignore')
                lista_auditoria.append(df_p_aud)

        # 3. VIA DO FUTURO: Agendamento MP
        if not df_agenda.empty:
            df_ag_aud = df_agenda.copy()
            if c_desc_ag and filtro_aud_eq: df_ag_aud = df_ag_aud[df_ag_aud[c_desc_ag].isin(filtro_aud_eq)]
            
            c_sn_ag = next((c for c in ['N° Série', 'Nº Série', 'N. Série', 'N.Série'] if c in df_ag_aud.columns), None)
            c_id_ag = next((c for c in ['ID', 'Identificador', 'Patrimônio', 'Patrimonio'] if c in df_ag_aud.columns), None)
            
            if c_sn_ag: df_ag_aud['N.º SÉRIE'] = df_ag_aud[c_sn_ag].fillna('N/I').astype(str).str.strip()
            else: df_ag_aud['N.º SÉRIE'] = 'N/I'
                
            df_ag_aud['N.º SÉRIE'] = df_ag_aud['N.º SÉRIE'].replace({'nan': 'N/I', 'None': 'N/I', '': 'N/I'})
            
            if padrao_sn: 
                mask_sn = df_ag_aud['N.º SÉRIE'].astype(str).str.contains(padrao_sn, case=False, na=False, regex=True)
                mask_id = df_ag_aud[c_id_ag].astype(str).str.contains(padrao_sn, case=False, na=False, regex=True) if c_id_ag else False
                df_ag_aud = df_ag_aud[mask_sn | mask_id]
            
            c_data_ag = next((c for c in ['Data Agendamento', 'Data'] if c in df_ag_aud.columns), None)
            c_nome_ag = next((c for c in ['Nome', 'Serviço'] if c in df_ag_aud.columns), None)

            if not df_ag_aud.empty and c_desc_ag and c_data_ag and c_nome_ag:
                df_ag_aud = df_ag_aud[[c_desc_ag, 'N.º SÉRIE', c_data_ag, c_nome_ag, 'Status']].copy()
                df_ag_aud.rename(columns={c_desc_ag: 'DESCRIÇÃO', c_data_ag: 'Data_Inicio', c_nome_ag: 'Serviço'}, inplace=True)
                df_ag_aud['O.S.'] = 'AGENDADO'
                df_ag_aud['Data_Fim'] = df_ag_aud['Data_Inicio'] 
                df_ag_aud['Status'] = np.where(df_ag_aud['Status'] == 'ATRASADO', '⚠️ Atrasado', '⏳ Programado')
                lista_auditoria.append(df_ag_aud)

      # 3. Consolidação e Gráficos
        if lista_auditoria:
            df_auditoria = pd.concat(lista_auditoria, ignore_index=True)
            df_auditoria['Data_Inicio'] = pd.to_datetime(df_auditoria['Data_Inicio'], errors='coerce').dt.normalize()
            df_auditoria['Data_Fim'] = pd.to_datetime(df_auditoria['Data_Fim'], errors='coerce').dt.normalize()
            df_auditoria = df_auditoria.dropna(subset=['Data_Inicio']).sort_values(['DESCRIÇÃO', 'Data_Inicio'], ascending=[True, False])
            
            # Agrupa as variações de "Em Execução" para a legenda não estourar
            df_auditoria['Status_Legenda'] = df_auditoria['Status'].apply(lambda x: '⚙️ Em Execução' if 'Em Execução' in str(x) else x)
            
            df_auditoria['N.º SÉRIE'] = df_auditoria['N.º SÉRIE'].astype(str).str.replace(r'^nan$|^None$', 'N/I', regex=True)
            df_auditoria['Equip_ID'] = df_auditoria['DESCRIÇÃO'] + " (SN: " + df_auditoria['N.º SÉRIE'] + ")"

            # A MÁGICA VISUAL: Trocamos o Timeline (Barras) por Scatter (Pontos de Marco)
            with st.container(border=True):
                st.markdown("##### 📍 Linha do Tempo de Intervenções (Marcos de Manutenção)")
                
                cores_status = {'✔️ Executado': '#70ad47', '⏳ Programado': '#154899', '⚠️ Atrasado': '#c00000', '⚙️ Em Execução': '#FF8C00'}
                # Diferentes formatos visuais para cada status
                simbolos_status = {'✔️ Executado': 'circle', '⏳ Programado': 'diamond', '⚠️ Atrasado': 'x', '⚙️ Em Execução': 'star'}
                
                fig_gantt = px.scatter(
                    df_auditoria, 
                    x="Data_Inicio", 
                    y="Equip_ID", 
                    color="Status_Legenda", 
                    color_discrete_map=cores_status, 
                    symbol="Status_Legenda",
                    symbol_map=simbolos_status,
                    hover_name="O.S.", 
                    hover_data={"Status": True, "Serviço": True, "Status_Legenda": False, "Data_Inicio": "|%d/%m/%Y"} 
                )
                
                # Aumenta o tamanho dos ícones para ficarem bem visíveis na linha
                fig_gantt.update_traces(marker=dict(size=14, line=dict(width=1, color='DarkSlateGrey')))
                
                # Cria a "linha vazia" (Grid) bem suave guiando os olhos, invertendo o eixo Y
                fig_gantt.update_yaxes(autorange="reversed", showgrid=True, gridwidth=1, gridcolor='#e6e6e6', title="")
                fig_gantt.update_xaxes(rangeslider_visible=True, showgrid=True, gridwidth=1, gridcolor='#f0f0f0', title="")
                
                altura_grafico = max(400, len(df_auditoria['Equip_ID'].unique()) * 45)
                fig_gantt.update_layout(height=altura_grafico, margin=dict(l=0, r=0, t=10, b=0), legend_title_text="")
                st.plotly_chart(fig_gantt, use_container_width=True)

            with st.container(border=True):
                st.markdown("##### 📋 Relatório Consolidado de Engenharia Clínica")
                st.caption("Pressione **Ctrl + P** e escolha 'Salvar como PDF' para exportar esta visão combinada.")
                
                df_print = df_auditoria[['O.S.', 'DESCRIÇÃO', 'N.º SÉRIE', 'Serviço', 'Status', 'Data_Inicio', 'Data_Fim']].copy()
                df_print['Data_Inicio'] = df_print['Data_Inicio'].dt.strftime('%d/%m/%Y')
                
                df_print['Conclusão Real'] = np.select(
                    [df_print['O.S.'] == 'AGENDADO', df_print['Status'].str.contains('Execução')],
                    ['-', 'EM ABERTO'],
                    default=df_print['Data_Fim'].dt.strftime('%d/%m/%Y')
                )
                
                df_print.drop(columns=['Data_Fim'], inplace=True)
                df_print.rename(columns={'Data_Inicio': 'Abertura / Prevista'}, inplace=True)
                df_print['Conclusão Real'] = df_print['Conclusão Real'].replace({'NaT': '-', 'nan': '-'})
                
                st.dataframe(
                    df_print, use_container_width=True, hide_index=True,
                    column_config={"O.S.": "Nº O.S.", "DESCRIÇÃO": "Equipamento", "N.º SÉRIE": "Nº Série", "Status": "Situação Atual"}
                )
        else:
            st.warning("Nenhum histórico encontrado para os parâmetros informados.")
