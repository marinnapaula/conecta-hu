import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
import plotly.express as px
import os
import glob
import numpy as np
from datetime import datetime, timezone, timedelta
import re
from io import BytesIO

# Importações para construir o PDF nativo com Gráfico
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus import Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Importando a inteligência do motor
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
# 1. FUNÇÃO EXCLUSIVA DE GERAÇÃO DE PDF COM GANTT 
# =====================================================================
def gerar_pdf_relatorio(df, fig_grafico=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(letter), rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25
    )
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#154899'), spaceAfter=6)
    subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#32A347'), spaceAfter=15)
    header_style = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.white, alignment=1)
    cell_style = ParagraphStyle('TableCell', parent=styles['Normal'], fontSize=8, leading=10, alignment=0)
    
    story.append(Paragraph("<b>RELATÓRIO CONSOLIDADO DE MANUTENÇÃO PROGRAMADA</b>", title_style))
    story.append(Paragraph(f"Documento de Evidência para Auditoria | HU-UNIVASF<br/>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
    story.append(Spacer(1, 5))
    
    # INSERE A FOTO DO GRÁFICO NO PDF COM PROPORÇÃO INTELIGENTE
    if fig_grafico is not None:
        try:
            # Captura a altura real que o gráfico exige
            altura_real = fig_grafico.layout.height if fig_grafico.layout.height else 450
            
            # Tenta converter o Plotly para Imagem, dando bastante espaço (width 1200) para os nomes caberem
            img_bytes = fig_grafico.to_image(format="png", engine="kaleido", width=1200, height=altura_real)
            img_buffer = BytesIO(img_bytes)
            img_buffer.seek(0)
            
            # Calcula a proporção para não esmagar a imagem na folha
            proporcao = altura_real / 1200
            altura_pdf = 720 * proporcao
            
            # Limite máximo de altura para não quebrar a página do PDF
            if altura_pdf > 380: altura_pdf = 380
            
            img_pdf = RLImage(img_buffer, width=720, height=altura_pdf) 
            story.append(img_pdf)
            story.append(Spacer(1, 15))
        except Exception as e:
            erro_limpo = str(e).replace('<', '').replace('>', '')
            alerta = f"<font color='red'><b>Aviso: Não foi possível anexar o gráfico (Erro: {erro_limpo}).</b></font>"
            story.append(Paragraph(alerta, cell_style))
            story.append(Spacer(1, 10))
    
    headers_traduzidos = ["Nº O.S.", "Equipamento", "Nº Série", "Serviço", "Situação Atual", "Abertura / Prevista", "Conclusão Real"]
    headers_pdf = [Paragraph(f"<b>{h}</b>", header_style) for h in headers_traduzidos]
    dados_tabela = [headers_pdf]
    
    for _, row in df.iterrows():
        dados_tabela.append([
            Paragraph(str(row['O.S.']), cell_style),
            Paragraph(str(row['DESCRIÇÃO']), cell_style),
            Paragraph(str(row['N.º SÉRIE']), cell_style),
            Paragraph(str(row['Serviço']), cell_style),
            Paragraph(str(row['Status']), cell_style),
            Paragraph(str(row['Abertura / Prevista']), cell_style),
            Paragraph(str(row['Conclusão Real']), cell_style)
        ])
    
    t = Table(dados_tabela, colWidths=[65, 172, 85, 105, 125, 95, 95])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#154899')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d0d0d0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f7f9fa')]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

# =====================================================================
# 2. CONFIGURAÇÃO DA PÁGINA STREAMLIT
# =====================================================================
st.set_page_config(page_title="Calendário | Conecta", page_icon=":material/calendar_month:", layout="wide", initial_sidebar_state="collapsed")

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
    .logo-container { display: flex; align-items: center; justify-content: flex-end; height: 100%; padding-top: 15px; }
    </style>
""", unsafe_allow_html=True)

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
# 3. CARREGAMENTO DOS DADOS GLOBAIS
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

tab_calendario, tab_auditoria = st.tabs(["📅 Calendário Operacional", "📋 Auditoria"])

# ---------------------------------------------------------------------
# ABA 1: CALENDÁRIO OPERACIONAL (Mantido igual)
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
        cor_evento = '#A6ACAF' if status_atual == 'EXECUTADO' else ('#E74C3C' if status_atual == 'ATRASADO' else cores_servicos.get(tipo_servico, '#154899'))
        eventos_calendario.append({"title": f"[{codigo}] {tipo_servico}", "start": data, "color": cor_evento, "equipamento": equipamento, "marca": str(row.get('Marca', 'N/A')), "setor": str(row.get('U.S.', 'N/A')), "tipo_servico": tipo_servico, "status": status_atual})

    opcoes_calendario = {"headerToolbar": {"left": "today prev,next", "center": "title", "right": "dayGridMonth,timeGridWeek,listMonth"}, "initialView": "dayGridMonth", "locale": "pt-br", "buttonText": {"today": "Hoje", "month": "Mês", "week": "Semana", "list": "Lista"}}
    st.markdown("<h3 style='display:flex; align-items:center; gap:8px;'><span class='material-symbols-rounded'>event_note</span> Visão Mensal de Execução</h3>", unsafe_allow_html=True)
    if not df_filtrado.empty:
        calendario_gerado = calendar(events=eventos_calendario, options=opcoes_calendario)
        if calendario_gerado.get("eventClick"): modal_detalhes(calendario_gerado["eventClick"]["event"])
    else: st.info("Nenhuma manutenção encontrada.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h3 style='display:flex; align-items:center; gap:8px;'><span class='material-symbols-rounded'>list_alt</span> Lista Detalhada de Serviços</h3>", unsafe_allow_html=True)
    colunas_exibir = ['Status', 'Data Agendamento', 'Nome', 'ID', 'Tipo Equipamento', 'Marca', 'U.S.']
    colunas_presentes = [col for col in colunas_exibir if col in df_filtrado.columns]
    st.dataframe(df_filtrado[colunas_presentes], use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# ABA 2: AUDITORIA 
# ---------------------------------------------------------------------
with tab_auditoria:
    st.markdown("Rastreie as manutenções programadas inserindo diretamente os números de série ou patrimônios da lista da auditoria.")
    
    with st.container(border=True):
        c_b1, c_busca_sn = st.columns([1.5, 1.5])
        tipos_equip = set()
        if not df_enc.empty and 'TIPO EQUIP.' in df_enc.columns: tipos_equip.update(df_enc['TIPO EQUIP.'].dropna().unique())
        if not df_agenda.empty and 'Tipo Equipamento' in df_agenda.columns: tipos_equip.update(df_agenda['Tipo Equipamento'].dropna().unique())
        
        filtro_aud_eq = c_b1.multiselect("Filtrar por Tipo de Equipamento:", sorted(list(tipos_equip)), placeholder="Todos os tipos alvo da busca...")
        filtro_aud_sn = c_busca_sn.text_input("Número(s) de Série ou Patrimônio (Separe por vírgula):", placeholder="Cole aqui a lista de séries ou patrimônios... Ex: 59885V/00, HU-00923")

    if filtro_aud_sn or filtro_aud_eq:
        lista_auditoria = []
        padrao_sn = None
        
        if filtro_aud_sn:
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
            if termos_expandidos: padrao_sn = '|'.join([re.escape(t) for t in termos_expandidos])
    
        # 1. O.S. Encerradas
        if not df_enc.empty:
            df_enc_aud = df_enc.copy()
            c_os = next((c for c in ['O.S.', 'OS', 'N.º O.S.'] if c in df_enc_aud.columns), None)
            c_sn_enc = next((c for c in ['N. SÉRIE', 'N.º SÉRIE', 'Nº SÉRIE', 'SÉRIE'] if c in df_enc_aud.columns), None)
            c_ab = next((c for c in ['ABERTURA', 'DATA ABERTURA'] if c in df_enc_aud.columns), None)
            c_en = next((c for c in ['ENCERRAMENTO', 'DATA ENCERRAMENTO'] if c in df_enc_aud.columns), None)
            c_cl = next((c for c in ['CLASSE', 'TIPO MANUTENÇÃO'] if c in df_enc_aud.columns), None)
            c_desc_enc = next((c for c in ['TIPO EQUIP.', 'TIPO EQUIPAMENTO', 'DESCRIÇÃO', 'EQUIPAMENTO'] if c in df_enc_aud.columns), None)

            if c_desc_enc and filtro_aud_eq: df_enc_aud = df_enc_aud[df_enc_aud[c_desc_enc].isin(filtro_aud_eq)]
            if padrao_sn: 
                mask_sn = df_enc_aud[c_sn_enc].astype(str).str.contains(padrao_sn, case=False, na=False, regex=True) if c_sn_enc else False
                c_id_enc = next((c for c in ['IDENTIFICADOR', 'ID', 'PATRIMÔNIO', 'PATRIMONIO'] if c in df_enc_aud.columns), None)
                mask_id = df_enc_aud[c_id_enc].astype(str).str.contains(padrao_sn, case=False, na=False, regex=True) if c_id_enc else False
                df_enc_aud = df_enc_aud[mask_sn | mask_id]
            if c_cl and not df_enc_aud.empty: df_enc_aud = df_enc_aud[df_enc_aud[c_cl].astype(str).str.upper().str.contains('PREV|CALIB|MP|PROG|ROTINA|SEGURANÇA|INSPEÇÃO|TESTE|VALIDAÇÃO|QUALIFICAÇÃO')]
            if not df_enc_aud.empty and all([c_os, c_desc_enc, c_sn_enc, c_ab, c_en, c_cl]):
                df_enc_aud = df_enc_aud[[c_os, c_desc_enc, c_sn_enc, c_ab, c_en, c_cl]].copy()
                df_enc_aud.rename(columns={c_os: 'O.S.', c_desc_enc: 'DESCRIÇÃO', c_sn_enc: 'N.º SÉRIE', c_ab: 'Data_Inicio', c_en: 'Data_Fim', c_cl: 'Serviço'}, inplace=True)
                df_enc_aud['Status'] = '✔️ Executado'
                lista_auditoria.append(df_enc_aud)

        # 2. O.S. Pendentes
        if not df_pend_bruto.empty:
            df_p_aud = df_pend_bruto.copy()
            c_os_p = next((c for c in ['O.S.', 'OS', 'N.º O.S.'] if c in df_p_aud.columns), None)
            c_sn_p = next((c for c in ['N. SÉRIE', 'N.º SÉRIE', 'Nº SÉRIE', 'SÉRIE'] if c in df_p_aud.columns), None)
            c_ab_p = next((c for c in ['ABERTURA', 'DATA ABERTURA'] if c in df_p_aud.columns), None)
            c_cl_p = next((c for c in ['CLASSE', 'TIPO MANUTENÇÃO'] if c in df_p_aud.columns), None)
            c_est_p = next((c for c in ['ESTADO', 'STATUS', 'SITUAÇÃO'] if c in df_p_aud.columns), None)
            c_desc_p = next((c for c in ['TIPO EQUIP.', 'TIPO EQUIPAMENTO', 'DESCRIÇÃO', 'EQUIPAMENTO'] if c in df_p_aud.columns), None)

            if c_desc_p and filtro_aud_eq: df_p_aud = df_p_aud[df_p_aud[c_desc_p].isin(filtro_aud_eq)]
            if padrao_sn: 
                mask_sn = df_p_aud[c_sn_p].astype(str).str.contains(padrao_sn, case=False, na=False, regex=True) if c_sn_p else False
                c_id_p = next((c for c in ['IDENTIFICADOR', 'ID', 'PATRIMÔNIO', 'PATRIMONIO'] if c in df_p_aud.columns), None)
                mask_id = df_p_aud[c_id_p].astype(str).str.contains(padrao_sn, case=False, na=False, regex=True) if c_id_p else False
                df_p_aud = df_p_aud[mask_sn | mask_id]
            if c_cl_p and not df_p_aud.empty: df_p_aud = df_p_aud[df_p_aud[c_cl_p].astype(str).str.upper().str.contains('PREV|CALIB|MP|PROG|ROTINA|SEGURANÇA|INSPEÇÃO|TESTE|VALIDAÇÃO|QUALIFICAÇÃO')]
            if not df_p_aud.empty and all([c_os_p, c_desc_p, c_sn_p, c_ab_p, c_cl_p]):
                df_p_aud = df_p_aud[[c_os_p, c_desc_p, c_sn_p, c_ab_p, c_cl_p, c_est_p]].copy() if c_est_p else df_p_aud[[c_os_p, c_desc_p, c_sn_p, c_ab_p, c_cl_p]].copy()
                df_p_aud.rename(columns={c_os_p: 'O.S.', c_desc_p: 'DESCRIÇÃO', c_sn_p: 'N.º SÉRIE', c_ab_p: 'Data_Inicio', c_cl_p: 'Serviço'}, inplace=True)
                df_p_aud['Data_Fim'] = pd.Timestamp(datetime.today().date())
                df_p_aud['Status'] = '⚙️ Em Execução (' + df_p_aud[c_est_p].astype(str).str.strip().str.upper() + ')' if c_est_p else '⚙️ Em Execução'
                df_p_aud.drop(columns=[c_est_p], inplace=True, errors='ignore')
                lista_auditoria.append(df_p_aud)

        # 3. Agendamento MP
        if not df_agenda.empty:
            df_ag_aud = df_agenda.copy()
            df_ag_aud = df_ag_aud[df_ag_aud['Status'] != 'EXECUTADO']
            c_sn_ag = next((c for c in ['N° Série', 'Nº Série', 'N. Série', 'N.Série'] if c in df_ag_aud.columns), None)
            c_id_ag = next((c for c in ['ID', 'Identificador', 'Patrimônio', 'Patrimonio'] if c in df_ag_aud.columns), None)
            c_desc_ag = next((c for c in ['Tipo Equipamento', 'Tipo Equip.'] if c in df_ag_aud.columns), None)
            
            if c_desc_ag and filtro_aud_eq: df_ag_aud = df_ag_aud[df_ag_aud[c_desc_ag].isin(filtro_aud_eq)]
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

        # 4. Consolidação Geral e Ordenação
        if lista_auditoria:
            df_auditoria = pd.concat(lista_auditoria, ignore_index=True)
            df_auditoria['Data_Inicio'] = pd.to_datetime(df_auditoria['Data_Inicio'], errors='coerce').dt.normalize()
            df_auditoria['Data_Fim'] = pd.to_datetime(df_auditoria['Data_Fim'], errors='coerce').dt.normalize()
            df_auditoria = df_auditoria.dropna(subset=['Data_Inicio'])
            
            df_auditoria['Status_Legenda'] = df_auditoria['Status'].apply(lambda x: '⚙️ Em Execução' if 'Em Execução' in str(x) else x)
            df_auditoria['Data_Fim_Vis'] = df_auditoria['Data_Inicio'] + pd.Timedelta(days=15)
            df_auditoria['N.º SÉRIE'] = df_auditoria['N.º SÉRIE'].astype(str).str.replace(r'^nan$|^None$', 'N/I', regex=True)
            df_auditoria['Equip_ID'] = df_auditoria['DESCRIÇÃO'] + " (SN: " + df_auditoria['N.º SÉRIE'] + ")"

            # Filtros Extras
            with st.container(border=True):
                st.markdown("##### 🛠️ Controles de Exibição do Relatório")
                col_f1, col_f2, col_f3 = st.columns(3)
                status_disp = df_auditoria['Status_Legenda'].unique().tolist()
                filtro_status = col_f1.multiselect("Filtrar por Situação:", options=status_disp, default=status_disp)
                
                min_date = df_auditoria['Data_Inicio'].min().date() if not df_auditoria.empty else datetime.today().date()
                max_date = df_auditoria['Data_Inicio'].max().date() if not df_auditoria.empty else datetime.today().date()
                filtro_periodo = col_f2.date_input("Filtrar por Período de Abertura:", value=(min_date, max_date), min_value=min_date, max_value=max_date, format="DD/MM/YYYY")
                opcoes_ord = ["Data (Mais recente primeiro)", "Data (Mais antiga primeiro)", "Equipamento (A-Z)", "Situação Atual"]
                ordenacao = col_f3.selectbox("Ordenar Tabela e Gráfico por:", opcoes_ord)

            if filtro_status: df_auditoria = df_auditoria[df_auditoria['Status_Legenda'].isin(filtro_status)]
            if len(filtro_periodo) == 2:
                start_date, end_date = filtro_periodo
                df_auditoria = df_auditoria[(df_auditoria['Data_Inicio'].dt.date >= start_date) & (df_auditoria['Data_Inicio'].dt.date <= end_date)]
            
            if ordenacao == "Data (Mais recente primeiro)": df_auditoria = df_auditoria.sort_values('Data_Inicio', ascending=False)
            elif ordenacao == "Data (Mais antiga primeiro)": df_auditoria = df_auditoria.sort_values('Data_Inicio', ascending=True)
            elif ordenacao == "Equipamento (A-Z)": df_auditoria = df_auditoria.sort_values(['DESCRIÇÃO', 'Data_Inicio'], ascending=[True, False])
            elif ordenacao == "Situação Atual": df_auditoria = df_auditoria.sort_values(['Status_Legenda', 'Data_Inicio'], ascending=[True, False])

            if not df_auditoria.empty:
                with st.container(border=True):
                    st.markdown("##### ⏱️ Linha do Tempo de Intervenções ")
                    cores_status = {'✔️ Executado': '#70ad47', '⏳ Programado': '#154899', '⚠️ Atrasado': '#c00000', '⚙️ Em Execução': '#FF8C00'}
                    
                    fig_gantt = px.timeline(
                        df_auditoria, x_start="Data_Inicio", x_end="Data_Fim_Vis", y="Equip_ID", color="Status_Legenda", color_discrete_map=cores_status, hover_name="O.S.", hover_data={"Serviço": True, "Status": True, "Status_Legenda": False, "Data_Fim_Vis": False}
                    )
                    
                    # CORREÇÃO DA MARGEM: Removemos o l=0 (left) para que o Plotly não corte o texto dos equipamentos na foto do PDF.
                    # Ativamos o automargin=True no Eixo Y para ele expandir e caber a letra inteira.
                    fig_gantt.update_yaxes(autorange="reversed" if ordenacao != "Equipamento (A-Z)" else None, title="", automargin=True)
                    fig_gantt.update_xaxes(rangeslider_visible=False)
                    fig_gantt.update_layout(height=max(350, len(df_auditoria['Equip_ID'].unique()) * 50), margin=dict(t=20, b=10), font=dict(size=10))
                    
                    st.plotly_chart(fig_gantt, use_container_width=True)

                df_print = df_auditoria[['O.S.', 'DESCRIÇÃO', 'N.º SÉRIE', 'Serviço', 'Status', 'Data_Inicio', 'Data_Fim']].copy()
                df_print['Abertura / Prevista'] = df_print['Data_Inicio'].dt.strftime('%d/%m/%Y')
                df_print['Conclusão Real'] = np.select(
                    [df_print['O.S.'] == 'AGENDADO', df_print['Status'].str.contains('Execução')],
                    ['-', 'EM ABERTO'],
                    default=df_print['Data_Fim'].dt.strftime('%d/%m/%Y')
                )
                df_print.drop(columns=['Data_Fim', 'Data_Inicio'], inplace=True)
                df_print['Conclusão Real'] = df_print['Conclusão Real'].replace({'NaT': '-', 'nan': '-'})
                df_print = df_print[['O.S.', 'DESCRIÇÃO', 'N.º SÉRIE', 'Serviço', 'Status', 'Abertura / Prevista', 'Conclusão Real']]

                with st.container(border=True):
                    st.markdown("##### 📋 Documentação de Rastreabilidade Operacional")
                    
                    pdf_gerado = gerar_pdf_relatorio(df_print, fig_gantt)
                    
                    st.download_button(
                        label="📥 Baixar Relatório",
                        data=pdf_gerado,
                        file_name=f"Relatorio_Auditoria_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf"
                    )
                    st.write("")
                    st.table(df_print)
            else:
                st.warning("Nenhum histórico encontrado para os filtros de tempo e status selecionados.")
        else: 
            st.warning("Nenhum histórico encontrado para a lista informada.")
    else: 
        st.info("👈 Selecione o equipamento ou cole a lista de séries/patrimônios acima para gerar o relatório de auditoria.")
