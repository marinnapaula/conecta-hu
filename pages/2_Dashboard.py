import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import os

from motor_dados import (
    carregar_mais_recente, 
    carregar_os_encerradas, 
    limpar_dimensao_equipamentos, 
    enriquecer_base_inventario,
    carregar_todas_atividades,
    gerar_curva_backlog
)

# =====================================================================
# 1. CONFIGURAÇÃO VISUAL (MONTSERRAT & BRANDING)
# =====================================================================
st.set_page_config(
    page_title="Dashboard | Conecta",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0');

    html, body, [class*="css"], [class*="st-"]  { font-family: 'Montserrat', sans-serif !important; }
    span[data-testid="stIconMaterial"] { font-family: "Material Symbols Rounded" !important; }
    h1 { color: #154899 !important; font-weight: 800 !important; margin-bottom: 0px; padding-bottom: 5px; }
    h2, h3, h4 { color: #32A347 !important; font-weight: 700 !important; }
    hr { border-top: 2px solid #32A347; margin-top: 0px; }
    .block-container { padding-top: 2rem !important; }
    .logo-container { display: flex; align-items: center; justify-content: flex-end; height: 100%; padding-top: 15px; }
    [data-testid="stMetricValue"] { color: #154899 !important; font-weight: 800 !important; }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. CABEÇALHO PADRÃO
# =====================================================================
col_titulo, col_espaco, col_logo1, col_logo2 = st.columns([5.5, 1.5, 1.5, 1.5])

with col_titulo:
    st.markdown("<h1 style='display:flex; align-items:center; gap:12px; margin-top: -10px;'><span class='material-symbols-rounded' style='font-size: 40px;'>analytics</span> Portal Analítico de Engenharia</h1>", unsafe_allow_html=True)
    st.markdown("**Plataforma Unificada de Gestão de Ativos, Produtividade e SLA | HU-UNIVASF**")

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
# 3. MÁQUINA DE CARREGAMENTO (CACHE CONTROL)
# =====================================================================
@st.cache_data(ttl=600)
def obter_dados_processados():
    df_inv_bruto = carregar_mais_recente("04.Inventário")
    df_pend_bruto = carregar_mais_recente("02.OS_Pendentes")
    df_enc_bruto = carregar_os_encerradas()
    df_atividades_bruto = carregar_todas_atividades("03.Atividades")
    df_curva_fila = gerar_curva_backlog()
        
    df_inv_limpo = limpar_dimensao_equipamentos(df_inv_bruto)
    df_inv_final = enriquecer_base_inventario(df_inv_limpo, df_enc_bruto)
    
    return df_inv_final, df_pend_bruto, df_enc_bruto, df_atividades_bruto, df_curva_fila

with st.spinner("Sincronizando bancos de dados e logs de atividades..."):
    df_inv, df_pend_bruto, df_enc_bruto, df_atividades, df_curva_fila = obter_dados_processados()

def get_col(df, options):
    if df is None or df.empty: return None
    for o in options:
        if o in df.columns: return o
    return None

# =====================================================================
# 4. BARRA LATERAL (FILTROS GLOBAIS DA DIRETORIA E PREPARAÇÃO GLOBAL)
# =====================================================================
st.sidebar.markdown("<h2 style='text-align: center; color: #154899;'>Filtros Globais</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

locais_disponiveis = sorted(df_inv['LOCALIZAÇÃO FÍSICA'].dropna().unique()) if not df_inv.empty and 'LOCALIZAÇÃO FÍSICA' in df_inv.columns else []
tipos_disponiveis = sorted(df_inv['DESCRIÇÃO'].dropna().unique()) if not df_inv.empty and 'DESCRIÇÃO' in df_inv.columns else []

filtro_local = st.sidebar.multiselect("Localização", locais_disponiveis, placeholder="Todos os setores")
filtro_tipo = st.sidebar.multiselect("Tipo de Equipamento", tipos_disponiveis, placeholder="Todos os tipos")

if filtro_local and not df_inv.empty: df_inv = df_inv[df_inv['LOCALIZAÇÃO FÍSICA'].isin(filtro_local)]
if filtro_tipo and not df_inv.empty: df_inv = df_inv[df_inv['DESCRIÇÃO'].isin(filtro_tipo)]

if not df_pend_bruto.empty:
    df_pend = df_pend_bruto.copy()
    c_loc_p = get_col(df_pend, ['LOCALIZAÇÃO FÍSICA', 'LOCALIZAÇÃO'])
    c_tip_p = get_col(df_pend, ['TIPO EQUIPAMENTO', 'EQUIPAMENTO', 'DESCRIÇÃO'])
    if filtro_local and c_loc_p: df_pend = df_pend[df_pend[c_loc_p].isin(filtro_local)]
    if filtro_tipo and c_tip_p:  df_pend = df_pend[df_pend[c_tip_p].isin(filtro_tipo)]
    
    col_abertura_p = get_col(df_pend, ['ABERTURA', 'DATA ABERTURA'])
    if col_abertura_p:
        df_pend[col_abertura_p] = pd.to_datetime(df_pend[col_abertura_p], errors='coerce')
        df_pend['DIAS_EM_ABERTO'] = (pd.Timestamp(datetime.today().date()) - df_pend[col_abertura_p]).dt.days
    else:
        df_pend['DIAS_EM_ABERTO'] = 0
        
    cond_fila = [df_pend['DIAS_EM_ABERTO'] <= 5, df_pend['DIAS_EM_ABERTO'] <= 15, df_pend['DIAS_EM_ABERTO'] <= 30, df_pend['DIAS_EM_ABERTO'] <= 60]
    df_pend['FAIXA_DIAS'] = np.select(cond_fila, ["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias"], default="Mais de 60 dias")
    df_pend['ORDEM_FAIXA'] = np.select(cond_fila, [1, 2, 3, 4], default=5)
    
    col_classe_p = get_col(df_pend, ['CLASSE', 'TIPO MANUTENÇÃO', 'TIPO DA O.S.'])
    if col_classe_p:
        df_pend['TIPO_MANUT_CALC'] = df_pend[col_classe_p].astype(str).str.upper()
        df_pend['TIPO_MANUTENCAO'] = np.where(df_pend['TIPO_MANUT_CALC'].str.contains('PREV|CALIB|MP|PROG|ROTINA'), 'PROGRAMADA',
                                     np.where(df_pend['TIPO_MANUT_CALC'].str.contains('CORR|MC|QUEBRA'), 'CORRETIVA', 'OUTRAS'))
    else:
        df_pend['TIPO_MANUTENCAO'] = 'NÃO IDENTIFICADO'
else:
    df_pend = pd.DataFrame()

if not df_enc_bruto.empty:
    df_enc = df_enc_bruto.copy()
    c_loc_e = get_col(df_enc, ['LOCALIZAÇÃO FÍSICA', 'LOCALIZAÇÃO'])
    c_tip_e = get_col(df_enc, ['TIPO EQUIPAMENTO', 'EQUIPAMENTO', 'DESCRIÇÃO'])
    if filtro_local and c_loc_e: df_enc = df_enc[df_enc[c_loc_e].isin(filtro_local)]
    if filtro_tipo and c_tip_e:  df_enc = df_enc[df_enc[c_tip_e].isin(filtro_tipo)]
else:
    df_enc = pd.DataFrame()

# =====================================================================
# ESTRUTURA DE ABAS (AGORA COM 5 ABAS)
# =====================================================================
tab_parque, tab_fila, tab_indicadores, tab_produtividade, tab_financeiro = st.tabs([
    "Ciclo de Vida do Parque", 
    "Acompanhamento de O.S. Pendentes", 
    "Indicadores de Gestão",
    "Produtividade & Entregas",
    "Gestão Financeira & Ativos"
])

# =====================================================================
# TAB 1: CICLO DE VIDA DO PARQUE
# =====================================================================
with tab_parque:
    if not df_inv.empty:
        df_ativos = df_inv[df_inv['STATUS_EQUIPAMENTO'] == 'ATIVO']
        total_ativos = len(df_ativos)
        qtd_critico_idade = len(df_ativos[df_ativos['Idade Equipamento Num'] > 10])
        pct_critico_idade = (qtd_critico_idade / total_ativos * 100) if total_ativos > 0 else 0
        qtd_mp_ok = len(df_ativos[df_ativos['Ordem Status MP'].isin([6, 7])])
        pct_mp_ok = (qtd_mp_ok / total_ativos * 100) if total_ativos > 0 else 0
        qtd_fora_garantia = len(df_ativos[df_ativos['Status Garantia'] == 'Fora de Garantia'])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Equipamentos Ativos", f"{total_ativos:,}".replace(",", "."))
        c2.metric("Críticos (> 10 anos)", f"{pct_critico_idade:.1f}%", f"{qtd_critico_idade} ativos antigos", delta_color="inverse")
        c3.metric("Conformidade de MP (OK)", f"{pct_mp_ok:.1f}%", "Meta: 100%")
        c4.metric("Fora de Garantia", f"{(qtd_fora_garantia/total_ativos*100):.1f}%", f"{qtd_fora_garantia} ativos")

        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("##### Distribuição por Faixa de Idade")
            df_faixa = df_ativos.groupby(['Faixa de Idade', 'Ordem Faixa Idade']).size().reset_index(name='Qtd')
            df_faixa = df_faixa.sort_values(by='Ordem Faixa Idade')
            fig_faixa = px.bar(df_faixa, x='Faixa de Idade', y='Qtd', text='Qtd', color_discrete_sequence=['#154899'])
            fig_faixa.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_faixa, use_container_width=True)
            
        with g2:
            st.markdown("##### Status Geral das Manutenções Programadas")
            mapa_nomes = {7: "Novo ou Garantia", 6: "Em Dia (OK)", 5: "Vence em 3m", 4: "Vence em 45d", 3: "Vencido (+1a)", 2: "Crítico (+2a)", 1: "Nunca Realizado (NR)"}
            df_ativos['Status_Label'] = df_ativos['Ordem Status MP'].map(mapa_nomes)
            df_status_mp = df_ativos['Status_Label'].value_counts().reset_index()
            df_status_mp.columns = ['Status', 'Quantidade']
            fig_pie_mp = px.pie(df_status_mp, values='Quantidade', names='Status', hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
            fig_pie_mp.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300)
            st.plotly_chart(fig_pie_mp, use_container_width=True)

# =====================================================================
# TAB 2: CENTRAL OPERACIONAL DE O.S. PENDENTES
# =====================================================================
with tab_fila:
    if not df_pend.empty:
        df_p = df_pend.copy()
        col_os = get_col(df_p, ['N.º O.S.', 'Nº O.S.', 'O.S.', 'OS', 'OS_KEY'])
        col_abertura = get_col(df_p, ['ABERTURA', 'DATA ABERTURA'])
        col_critico = get_col(df_p, ['EQUIPAMENTO CRÍTICO', 'EQUIPAMENTO CRITICO'])
        col_parado = get_col(df_p, ['EQUIPAMENTO PARADO', 'PARADO'])
        col_local = get_col(df_p, ['LOCALIZAÇÃO FÍSICA', 'LOCALIZAÇÃO', 'LOCALIZACAO_INVENTARIO'])
        col_serie = get_col(df_p, ['N. SÉRIE', 'N.º SÉRIE', 'SÉRIE'])
        col_tipo = get_col(df_p, ['TIPO EQUIPAMENTO', 'EQUIPAMENTO', 'DESCRIÇÃO'])
        col_estado = get_col(df_p, ['ESTADO', 'ESTADO DA O.S.'])
        col_executor = get_col(df_p, ['EXECUTOR', 'RESPONSÁVEL'])
        
        if col_critico: df_p[col_critico] = df_p[col_critico].astype(str).str.upper().str.strip()
        if col_parado: df_p[col_parado] = df_p[col_parado].astype(str).str.upper().str.strip()

        st.markdown("<h3 style='color: #154899; margin-top: 15px;'> Fila de O.S Pendentes (Centro de Comando)</h3>", unsafe_allow_html=True)

        with st.container(border=True):
            r1, r2, r3, r4 = st.columns(4)
            f_num_os = r1.text_input("Número da O.S.", placeholder="Digite o número...")
            f_num_serie = r2.text_input("Número de Série", placeholder="Digite o S/N...")
            f_faixa_dias = r3.multiselect("Faixa de Dias", sorted(df_p['FAIXA_DIAS'].unique()))
            f_local_fisico = r4.multiselect("Localização Física", sorted(df_p[col_local].dropna().unique()) if col_local else [])
            
            r5, r6, r7, r8 = st.columns(4)
            f_tipo_equip = r5.multiselect("Tipo de Equipamento", sorted(df_p[col_tipo].dropna().unique()) if col_tipo else [])
            f_estado_os = r6.multiselect("Status da O.S.", sorted(df_p[col_estado].dropna().unique()) if col_estado else [])
            f_eq_parado = r7.selectbox("Equipamento Parado?", ["Todos", "SIM", "NÃO"])
            f_eq_critico = r8.selectbox("Equipamento Crítico?", ["Todos", "SIM", "NÃO"])

        df_f = df_p.copy()
        if f_num_os and col_os: df_f = df_f[df_f[col_os].astype(str).str.contains(f_num_os, case=False, na=False)]
        if f_num_serie and col_serie: df_f = df_f[df_f[col_serie].astype(str).str.contains(f_num_serie, case=False, na=False)]
        if f_faixa_dias: df_f = df_f[df_f['FAIXA_DIAS'].isin(f_faixa_dias)]
        if f_local_fisico and col_local: df_f = df_f[df_f[col_local].isin(f_local_fisico)]
        if f_tipo_equip and col_tipo: df_f = df_f[df_f[col_tipo].isin(f_tipo_equip)]
        if f_estado_os and col_estado: df_f = df_f[df_f[col_estado].isin(f_estado_os)]
        if f_eq_parado != "Todos" and col_parado: df_f = df_f[df_f[col_parado] == f_eq_parado]
        if f_eq_critico != "Todos" and col_critico: df_f = df_f[df_f[col_critico] == f_eq_critico]

        df_f = df_f.sort_values(by='DIAS_EM_ABERTO', ascending=False)

        st.markdown(f"**Registros Filtrados:** {len(df_f)} ordens pendentes localizadas.")
        colunas_grade = [c for c in [col_os, col_tipo, col_serie, col_local, 'DIAS_EM_ABERTO', col_estado, col_executor] if c in df_f.columns]
        st.dataframe(
            df_f[colunas_grade], use_container_width=True, hide_index=True, height=240,
            column_config={
                "DIAS_EM_ABERTO": st.column_config.ProgressColumn("Tempo de Espera", format="%d dias", min_value=0, max_value=int(df_p['DIAS_EM_ABERTO'].max()) if len(df_p) > 0 else 100),
                col_os: st.column_config.TextColumn("Nº O.S.")
            }
        )

        st.markdown("---")
        st.markdown("<h3 style='color: #154899;'>Detalhamento da O.S</h3>", unsafe_allow_html=True)
        
        if not df_f.empty and col_os:
            os_alvo = st.selectbox("Escolha uma Ordem de Serviço da lista para abrir a ficha completa:", options=df_f[col_os].astype(str).unique())
            
            if os_alvo:
                dados_linha = df_f[df_f[col_os].astype(str) == os_alvo].iloc[0]
                with st.container(border=True):
                    f_col_t, f_col_b1, f_col_b2 = st.columns([2, 1, 1])
                    f_col_t.markdown(f"#### Ficha de Atendimento - O.S. № {os_alvo}")
                    
                    num_serie_real = dados_linha.get(col_serie, 'N/I')
                    num_pat_real = dados_linha.get('PATRIMÔNIO', dados_linha.get('IDENTIFICADOR', 'N/I'))
                    f_col_t.markdown(f"**Equipamento:** {dados_linha.get(col_tipo, 'N/I')} | **Nº Série:** {num_serie_real} | **Patrimônio:** {num_pat_real}")
                    
                    p_status = "🔴 PARADO" if str(dados_linha.get(col_parado, '')).upper() == 'SIM' else "🟢 EM OPERAÇÃO"
                    c_status = "⚠️ ALTA CRITICIDADE" if str(dados_linha.get(col_critico, '')).upper() == 'SIM' else "ℹ️ CRITICIDADE NORMAL"
                    f_col_b1.markdown(f"**Disponibilidade:**<br>`{p_status}`", unsafe_allow_html=True)
                    f_col_b2.markdown(f"**Criticidade:**<br>`{c_status}`", unsafe_allow_html=True)
                    st.divider()
                    
                    d1, d2, d3 = st.columns(3)
                    dt_ab_str = dados_linha[col_abertura].strftime('%d/%m/%Y') if pd.notnull(dados_linha.get(col_abertura)) else 'N/I'
                    
                    d1.markdown(f"**📅 Abertura:** {dt_ab_str}")
                    d1.markdown(f"**⏳ Dias na Fila:** {dados_linha.get('DIAS_EM_ABERTO', 0)} dias")
                    d2.markdown(f"**📍 Localização:** {dados_linha.get(col_local, 'N/I')}")
                    d3.markdown(f"**⚙️ Status da O.S.:** {dados_linha.get(col_estado, 'N/I')}")
                    
                    st.markdown("<br><h5 style='color: #32A347;'>Detalhamento Técnico</h5>", unsafe_allow_html=True)
                    
                    if not df_atividades.empty:
                        df_at_temp = df_atividades.copy()
                        os_busca = str(os_alvo).replace('.0', '').strip()
                        
                        df_historico_os = df_at_temp[df_at_temp['OS_KEY'] == os_busca] if 'OS_KEY' in df_at_temp.columns else pd.DataFrame()
                        
                        if not df_historico_os.empty:
                            col_dt_inicio = get_col(df_historico_os, ['DATA INÍCIO', 'DATA INICIO', 'INÍCIO', 'INICIO', 'DATA DA EXECUÇÃO', 'DATA'])
                            col_atividade = get_col(df_historico_os, ['ATIVIDADE', 'ATIVIDADES', 'TIPO ATIVIDADE'])
                            col_servico = get_col(df_historico_os, ['SERVIÇO EXECUTADO', 'SERVICO EXECUTADO', 'SERVIÇO', 'DESCRIÇÃO', 'HISTÓRICO'])
                            col_exec_act = get_col(df_historico_os, ['EXECUTOR', 'TÉCNICO', 'RESPONSÁVEL', 'TECNICO'])
                            
                            cols_print_act = [c for c in [col_dt_inicio, col_exec_act, col_atividade, col_servico] if c]
                            df_print_act = df_historico_os[cols_print_act].copy()
                            
                            if col_dt_inicio:
                                df_print_act[col_dt_inicio] = pd.to_datetime(df_print_act[col_dt_inicio], errors='coerce')
                                df_print_act = df_print_act.sort_values(by=col_dt_inicio, ascending=False)
                                df_print_act[col_dt_inicio] = df_print_act[col_dt_inicio].dt.strftime('%d/%m/%Y %H:%M')
                                
                            config_colunas = {}
                            if col_dt_inicio: config_colunas[col_dt_inicio] = st.column_config.TextColumn("Atualização", width="medium")
                            if col_exec_act: config_colunas[col_exec_act] = st.column_config.TextColumn("Executor", width="medium")
                            if col_atividade: config_colunas[col_atividade] = st.column_config.TextColumn("Atividade", width="medium")
                            if col_servico: config_colunas[col_servico] = st.column_config.TextColumn("Serviço Executado", width="large")
                                
                            st.dataframe(df_print_act, use_container_width=True, hide_index=True, column_config=config_colunas)
                            
                            with st.expander("Ver textos de Serviços Executados completos"):
                                for _, lista_row in df_print_act.iterrows():
                                    t_ini = lista_row.get(col_dt_inicio, 'N/I')
                                    t_exec = lista_row.get(col_exec_act, 'N/I')
                                    t_txt = lista_row.get(col_servico, 'Sem descrição detalhada')
                                    st.markdown(f"**[{t_ini}] - Executor: {t_exec}**")
                                    st.info(t_txt)
                        else:
                            st.info("Esta O.S. está na fila aguardando o primeiro apontamento técnico.")
                    else:
                        st.info("Logs indisponíveis na pasta '03.Atividades'.")
        else:
            st.warning("Ajuste a busca para carregar as fichas técnicas.")

# =====================================================================
# TAB 3: INDICADORES (FOTOGRAFIA DO MOMENTO)
# =====================================================================
with tab_indicadores:
    tma_g_12 = 0; tma_mc_12 = 0; tma_mp_12 = 0
    if not df_enc.empty and 'ABERTURA' in df_enc.columns and 'ENCERRAMENTO' in df_enc.columns:
        df_e = df_enc.copy()
        df_e['DURACAO'] = (df_e['ENCERRAMENTO'] - df_e['ABERTURA']).dt.days
        hoje = pd.Timestamp(datetime.today().date())
        df_12m = df_e[df_e['ENCERRAMENTO'] >= (hoje - pd.DateOffset(months=12))]
        tma_g_12 = df_12m['DURACAO'].mean() if not df_12m.empty else 0
        
        col_classe_e = get_col(df_12m, ['CLASSE', 'TIPO MANUTENÇÃO', 'TIPO DA O.S.'])
        if col_classe_e:
            cond_mc = df_12m[col_classe_e].astype(str).str.upper().str.contains('CORR|MC|QUEBRA')
            tma_mc_12 = df_12m[cond_mc]['DURACAO'].mean() if not df_12m[cond_mc].empty else 0
            cond_mp = df_12m[col_classe_e].astype(str).str.upper().str.contains('PREV|CALIB|MP|PROG|ROTINA')
            tma_mp_12 = df_12m[cond_mp]['DURACAO'].mean() if not df_12m[cond_mp].empty else 0

    tot_pend = 0; tot_crit = 0; tm_aberta_geral = 0; tm_aberta_mc = 0
    if not df_pend.empty:
        tot_pend = len(df_pend)
        col_critico_ind = get_col(df_pend, ['EQUIPAMENTO CRÍTICO', 'EQUIPAMENTO CRITICO'])
        if col_critico_ind:
            tot_crit = len(df_pend[df_pend[col_critico_ind].astype(str).str.upper().str.strip() == 'SIM'])
        tm_aberta_geral = df_pend['DIAS_EM_ABERTO'].mean()
        df_pend_mc = df_pend[df_pend['TIPO_MANUTENCAO'] == 'CORRETIVA']
        tm_aberta_mc = df_pend_mc['DIAS_EM_ABERTO'].mean() if not df_pend_mc.empty else 0

    st.markdown("<h4 style='color: #32A347; margin-bottom: 5px; margin-top: 5px;'>Visão Geral de Desempenho e Fila</h4>", unsafe_allow_html=True)
    
    ind_c1, ind_c2, ind_c3, ind_c4, ind_c5 = st.columns(5)
    ind_c1.metric("TMA Geral", f"{tma_g_12:.1f} Dias", help="Tempo Médio de Atendimento Geral (Últimos 12 meses)")
    ind_c2.metric("TMA Corretiva", f"{tma_mc_12:.1f} Dias", help="Tempo Médio de Atendimento de O.S. Corretivas (Últimos 12 meses)")
    ind_c3.metric("TMA Programada", f"{tma_mp_12:.1f} Dias", help="Tempo Médio de Atendimento de O.S. Preventivas/Calibrações (Últimos 12 meses)")
    ind_c4.metric("O.S. Pendentes", f"{tot_pend}", f"{tot_crit} Críticas", delta_color="inverse" if tot_crit > 0 else "normal", help="Volume total de Ordens de Serviço abertas na fila")
    ind_c5.metric("Espera Média (Abertas)", f"{tm_aberta_geral:.1f} Dias", f"Corretivas: {tm_aberta_mc:.1f} d", delta_color="inverse" if tm_aberta_geral > 0 else "normal", help="Média de dias em aberto considerando as O.S. ainda na fila")

    st.markdown("---")
    
    if not df_pend.empty:
        col_estado_graf = get_col(df_pend, ['ESTADO', 'ESTADO DA O.S.'])
        col_os_graf = get_col(df_pend, ['N.º O.S.', 'Nº O.S.', 'O.S.', 'OS', 'OS_KEY'])
        
        if col_estado_graf and col_os_graf:
            c_esq, c_dir = st.columns([1.2, 1])
            with c_esq:
                with st.container(border=True):
                    st.markdown("##### Média de Dias em Aberto x Total de O.S. por Estado")
                    df_est = df_pend.groupby(col_estado_graf).agg(Total_OS=(col_os_graf, 'count'), Media_Dias=('DIAS_EM_ABERTO', 'mean')).reset_index()
                    df_est = df_est.sort_values('Total_OS', ascending=True)
                    fig_est = go.Figure()
                    fig_est.add_trace(go.Bar(y=df_est[col_estado_graf], x=df_est['Total_OS'], name='Total O.S.', orientation='h', marker_color='#70ad47'))
                    fig_est.add_trace(go.Bar(y=df_est[col_estado_graf], x=df_est['Media_Dias'], name='Média Dias em Aberto', orientation='h', marker_color='#44546a'))
                    fig_est.update_layout(barmode='group', height=500, margin=dict(l=0, r=0, t=20, b=0), legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5))
                    st.plotly_chart(fig_est, use_container_width=True)
            
            with c_dir:
                with st.container(border=True):
                    st.markdown("##### Total O.S. x Faixa de Dias")
                    df_faixa_g = df_pend.groupby(['FAIXA_DIAS', 'ORDEM_FAIXA']).size().reset_index(name='Total')
                    df_faixa_g = df_faixa_g.sort_values('ORDEM_FAIXA', ascending=False)
                    fig_faixa = px.bar(df_faixa_g, y='FAIXA_DIAS', x='Total', orientation='h', text='Total', color_discrete_sequence=['#70ad47'])
                    fig_faixa.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0), xaxis_title=None, yaxis_title=None)
                    st.plotly_chart(fig_faixa, use_container_width=True)
                    
                with st.container(border=True):
                    st.markdown("##### O.S. Pendente x Tipo de Manutenção")
                    df_tp = df_pend['TIPO_MANUTENCAO'].value_counts().reset_index()
                    df_tp.columns = ['Tipo', 'Total']
                    fig_tp = px.pie(df_tp, names='Tipo', values='Total', hole=0.5, color_discrete_sequence=['#44546a', '#70ad47', '#e6e6e6'])
                    fig_tp.update_traces(textposition='inside', textinfo='percent+label')
                    fig_tp.update_layout(height=230, margin=dict(l=0, r=0, t=10, b=0), showlegend=True)
                    st.plotly_chart(fig_tp, use_container_width=True)

# =====================================================================
# TAB 4: PRODUTIVIDADE & ENTREGAS (FLUXO HISTÓRICO)
# =====================================================================
with tab_produtividade:
    st.markdown("<h3 style='color: #154899; margin-top: 15px;'>Análise de Produtividade e Entregas Mensais</h3>", unsafe_allow_html=True)
    
    if not df_enc.empty:
        col_abertura_e = get_col(df_enc, ['ABERTURA', 'DATA ABERTURA'])
        col_encerra_e = get_col(df_enc, ['ENCERRAMENTO', 'DATA ENCERRAMENTO'])
        col_os_e = get_col(df_enc, ['OS_KEY', 'O.S.', 'OS'])
        col_classe_e = get_col(df_enc, ['CLASSE', 'TIPO MANUTENÇÃO', 'TIPO DA O.S.'])
        col_prog_e = get_col(df_enc, ['PROGRAMA MP', 'PROGRAMA', 'TIPO DE PREVENTIVA'])
        
        # Filtro Global de Ano para Produtividade
        df_enc['Ano_Encerramento'] = df_enc[col_encerra_e].dt.year
        anos_disp = sorted(df_enc['Ano_Encerramento'].dropna().unique().astype(int).tolist(), reverse=True)
        
        c_filtro_ano, _ = st.columns([1, 4])
        ano_filtro = c_filtro_ano.selectbox("Filtrar por Ano de Referência:", ["Todos os Anos"] + anos_disp)
        
        df_prod = df_enc.copy()
        if ano_filtro != "Todos os Anos":
            df_prod = df_prod[df_prod['Ano_Encerramento'] == ano_filtro]
        
        # LÓGICA DE DEMANDA VS PRODUÇÃO (Soma Abertas na base de Pendentes + Encerradas)
        lista_aberturas = []
        if col_abertura_e and col_os_e:
            lista_aberturas.append(df_enc[[col_os_e, col_abertura_e]].rename(columns={col_os_e: 'OS', col_abertura_e: 'DATA'}))
        
        col_abertura_p = get_col(df_pend, ['ABERTURA', 'DATA ABERTURA'])
        col_os_p = get_col(df_pend, ['OS_KEY', 'O.S.', 'OS', 'N.º O.S.'])
        if col_abertura_p and col_os_p and not df_pend.empty:
            lista_aberturas.append(df_pend[[col_os_p, col_abertura_p]].rename(columns={col_os_p: 'OS', col_abertura_p: 'DATA'}))
        
        if lista_aberturas:
            df_demanda_base = pd.concat(lista_aberturas).drop_duplicates('OS').dropna(subset=['DATA'])
            df_demanda_base['AnoMes'] = df_demanda_base['DATA'].dt.strftime('%Y-%m')
            df_demanda_agrup = df_demanda_base.groupby('AnoMes').size().reset_index(name='Demanda (Entradas)')
        else:
            df_demanda_agrup = pd.DataFrame(columns=['AnoMes', 'Demanda (Entradas)'])

        df_prod['AnoMes'] = df_prod[col_encerra_e].dt.strftime('%Y-%m')
        df_saida_agrup = df_prod.groupby('AnoMes').size().reset_index(name='Produção (Saídas)')
        
        df_balanco = pd.merge(df_demanda_agrup, df_saida_agrup, on='AnoMes', how='outer').fillna(0).sort_values('AnoMes')
        
        if ano_filtro != "Todos os Anos":
            df_balanco = df_balanco[df_balanco['AnoMes'].str.startswith(str(ano_filtro))]
        
        # 1º Gráfico: Entradas x Saídas (Barra Dupla)
        with st.container(border=True):
            st.markdown("##### Entradas (Demandas) x Saídas (Produção Total)")
            fig_balanco = go.Figure()
            fig_balanco.add_trace(go.Bar(x=df_balanco['AnoMes'], y=df_balanco['Demanda (Entradas)'], name='Demanda (Abertas)', marker_color='#70ad47'))
            fig_balanco.add_trace(go.Bar(x=df_balanco['AnoMes'], y=df_balanco['Produção (Saídas)'], name='Total Entregas', marker_color='#44546a'))
            fig_balanco.update_layout(barmode='group', height=350, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_balanco, use_container_width=True)
        
        # 2º Nível de Gráficos: Distribuições
        c_prod1, c_prod2 = st.columns(2)
        with c_prod1:
            with st.container(border=True):
                st.markdown("##### Distribuição de Entregas x Classe de Manutenção")
                if col_classe_e:
                    df_prod['Classe_Norm'] = np.where(df_prod[col_classe_e].astype(str).str.upper().str.contains('PREV|CALIB|MP|PROG|ROTINA'), 'Manutenção Programada',
                                             np.where(df_prod[col_classe_e].astype(str).str.upper().str.contains('CORR|MC|QUEBRA'), 'Manutenção Corretiva',
                                             np.where(df_prod[col_classe_e].astype(str).str.upper().str.contains('INSTAL'), 'Instalação', 'Outras')))
                                             
                    df_classe = df_prod.groupby(['AnoMes', 'Classe_Norm']).size().reset_index(name='Qtd')
                    fig_classe = px.bar(df_classe, x='AnoMes', y='Qtd', color='Classe_Norm', color_discrete_sequence=['#44546a', '#eeb022', '#70ad47', '#a6a6a6'])
                    fig_classe.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), legend_title_text=None, legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                    st.plotly_chart(fig_classe, use_container_width=True)
                else:
                    st.info("Coluna de Classe não localizada.")
                    
        with c_prod2:
            with st.container(border=True):
                st.markdown("##### Distribuição de Entregas x Tipo de Preventiva")
                if col_prog_e:
                    df_prev = df_prod[df_prod[col_prog_e].notna() & (df_prod[col_prog_e].astype(str).str.strip() != '')]
                    if not df_prev.empty:
                        df_prog = df_prev.groupby(['AnoMes', col_prog_e]).size().reset_index(name='Qtd')
                        fig_prog = px.bar(df_prog, x='AnoMes', y='Qtd', color=col_prog_e, color_discrete_sequence=px.colors.qualitative.Safe)
                        fig_prog.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), legend_title_text=None, legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                        st.plotly_chart(fig_prog, use_container_width=True)
                    else:
                        st.info("Não há entregas programadas registradas para o período.")
                else:
                    st.info("Coluna de Programa Preventivo não localizada nas Encerradas.")
    else:
        st.warning("Não há histórico de O.S. Encerradas para calcular a produtividade.")

# =====================================================================
# TAB 5: GESTÃO FINANCEIRA & ATIVOS
# =====================================================================
with tab_financeiro:
    if not df_inv.empty:
        df_fin = df_inv.copy()
        for col in ['VALOR (R$)', 'CUSTO PEÇA (R$)', 'CUSTO SERVIÇO EXTERNO (R$)']:
            df_fin[col] = pd.to_numeric(df_fin[col], errors='coerce').fillna(0) if col in df_fin.columns else 0.0
                
        df_fin_ativos = df_fin[df_fin['STATUS_EQUIPAMENTO'] == 'ATIVO']
        patrimonio_total = df_fin_ativos['VALOR (R$)'].sum()
        custo_manutencao_total = df_fin_ativos['CUSTO PEÇA (R$)'].sum() + df_fin_ativos['CUSTO SERVIÇO EXTERNO (R$)'].sum()
        ticket_medio_ativo = df_fin_ativos['VALOR (R$)'].mean() if len(df_fin_ativos) > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Investimento Total (Patrimônio)", f"R$ {patrimonio_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m2.metric("Custo Acumulado Manutenção", f"R$ {custo_manutencao_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m3.metric("Ticket Médio por Ativo", f"R$ {ticket_medio_ativo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m4.metric("Despesa com Serviços Externos", f"R$ {df_fin_ativos['CUSTO SERVIÇO EXTERNO (R$)'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("<br>", unsafe_allow_html=True)
        fin_g1, fin_g2 = st.columns(2)
        with fin_g1:
            st.markdown("##### 📊 Valor Patrimonial Acumulado por Tipo de Ativo")
            col_desc = get_col(df_fin_ativos, ['DESCRIÇÃO', 'TIPO EQUIPAMENTO'])
            if col_desc:
                df_val_tipo = df_fin_ativos.groupby(col_desc)['VALOR (R$)'].sum().reset_index(name='Total_Valor').sort_values(by='Total_Valor', ascending=False).head(10)
                fig_val_tipo = px.bar(df_val_tipo, x='Total_Valor', y=col_desc, orientation='h', text='Total_Valor', color_discrete_sequence=['#154899'])
                fig_val_tipo.update_traces(texttemplate='R$ %{text:,.2s}', textposition='outside')
                fig_val_tipo.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=20, b=20), height=350)
                st.plotly_chart(fig_val_tipo, use_container_width=True)
                
        with fin_g2:
            st.markdown("##### 📈 Curva Histórica de Investimentos em Aquisições")
            if 'AQUISIÇÃO' in df_fin_ativos.columns:
                df_invest_tempo = df_fin_ativos.copy()
                df_invest_tempo['Ano_Aquisicao'] = df_invest_tempo['AQUISIÇÃO'].dt.year
                df_curva = df_invest_tempo[df_invest_tempo['Ano_Aquisicao'].notna() & (df_invest_tempo['Ano_Aquisicao'] >= 2010)].groupby('Ano_Aquisicao')['VALOR (R$)'].sum().reset_index(name='Investimento')
                fig_curva = px.area(df_curva, x='Ano_Aquisicao', y='Investimento', markers=True, color_discrete_sequence=['#32A347'])
                fig_curva.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350)
                st.plotly_chart(fig_curva, use_container_width=True)
