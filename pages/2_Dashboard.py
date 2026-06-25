import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
import os
# Importação do motor de inteligência central
from motor_dados import (
    carregar_mais_recente, 
    carregar_os_encerradas, 
    limpar_dimensao_equipamentos, 
    enriquecer_base_inventario
)

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E IDENTIDADE VISUAL (CSS MONTSERRAT)
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

    html, body, [class*="css"], [class*="st-"]  {
        font-family: 'Montserrat', sans-serif !important;
    }
    span[data-testid="stIconMaterial"] {
        font-family: "Material Symbols Rounded" !important;
    }
    h1 { color: #154899 !important; font-weight: 800 !important; margin-bottom: 0px; padding-bottom: 5px; }
    h2, h3, h4 { color: #32A347 !important; font-weight: 700 !important; }
    hr { border-top: 2px solid #32A347; margin-top: 0px; }
    .block-container { padding-top: 2rem !important; }
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
# 2. CABEÇALHO PADRÃO DO HOSPITAL
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
# 3. CARREGAMENTO DOS DADOS E CACHE INTEGRADO (INCLUINDO ATIVIDADES)
# =====================================================================
@st.cache_data(ttl=600)
def obter_dados_processados():
    df_inv_bruto = carregar_mais_recente("04.Inventário")
    df_pend_bruto = carregar_mais_recente("02.OS_Pendentes")
    df_enc_bruto = carregar_os_encerradas()
    
    # Ingestão da base de histórico de ações/trabalho dos técnicos
    df_atividades_bruto = carregar_mais_recente("03.Atividades_Recentes")
    if df_atividades_bruto.empty:
        df_atividades_bruto = carregar_mais_recente("Atividades_Recentes")
        
    df_inv_limpo = limpar_dimensao_equipamentos(df_inv_bruto)
    df_inv_final = enriquecer_base_inventario(df_inv_limpo, df_enc_bruto)
    
    return df_inv_final, df_pend_bruto, df_enc_bruto, df_atividades_bruto

with st.spinner("Sincronizando bancos de dados e logs de atividades..."):
    df_inv, df_pend_bruto, df_enc_bruto, df_atividades = obter_dados_processados()

# Função auxiliar de busca flexível de colunas por sinônimos do GETS
def get_col(df, options):
    if df is None or df.empty: return None
    for o in options:
        if o in df.columns: return o
    return None

# =====================================================================
# 4. BARRA LATERAL (FILTROS GLOBAIS DA DIRETORIA)
# =====================================================================
st.sidebar.markdown("<h2 style='text-align: center; color: #154899;'>Filtros Globais</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

locais_disponiveis = sorted(df_inv['LOCALIZAÇÃO FÍSICA'].dropna().unique()) if not df_inv.empty and 'LOCALIZAÇÃO FÍSICA' in df_inv.columns else []
tipos_disponiveis = sorted(df_inv['DESCRIÇÃO'].dropna().unique()) if not df_inv.empty and 'DESCRIÇÃO' in df_inv.columns else []

filtro_local = st.sidebar.multiselect("📍 Setor Geral", locais_disponiveis, placeholder="Todos os setores")
filtro_tipo = st.sidebar.multiselect("📟 Classe de Ativo", tipos_disponiveis, placeholder="Todos os tipos")

# Aplicação dos Filtros Globais na Memória
if filtro_local and not df_inv.empty: df_inv = df_inv[df_inv['LOCALIZAÇÃO FÍSICA'].isin(filtro_local)]
if filtro_tipo and not df_inv.empty: df_inv = df_inv[df_inv['DESCRIÇÃO'].isin(filtro_tipo)]

if not df_pend_bruto.empty:
    df_pend = df_pend_bruto.copy()
    c_loc_p = get_col(df_pend, ['LOCALIZAÇÃO FÍSICA', 'LOCALIZAÇÃO'])
    c_tip_p = get_col(df_pend, ['TIPO EQUIPAMENTO', 'EQUIPAMENTO', 'DESCRIÇÃO'])
    if filtro_local and c_loc_p: df_pend = df_pend[df_pend[c_loc_p].isin(filtro_local)]
    if filtro_tipo and c_tip_p:  df_pend = df_pend[df_pend[c_tip_p].isin(filtro_tipo)]
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
# 5. ESTRUTURA DE ABAS EXECUTIVAS
# =====================================================================
tab_parque, tab_fila, tab_produtividade, tab_financeiro = st.tabs([
    "🏥 Ciclo de Vida do Parque", 
    "📥 Acompanhamento de O.S. Pendentes", 
    "📊 Produtividade & TMA",
    "💰 Gestão Financeira & Ativos"
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
        c4.metric("Fora de Garantia", f"{(qtd_fora_garantia/total_ativos*100):.1f}%", f"{qtd_fora_garantia} equipamentos")

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
# TAB 2: CENTRAL OPERACIONAL DE O.S. PENDENTES (MÓDULO FILTRO + DRILL-DOWN)
# =====================================================================
with tab_fila:
    if not df_pend.empty:
        df_p = df_pend.copy()
        
        # 1. Mapeamento de Colunas Críticas do Backlog
        col_os = get_col(df_p, ['O.S.', 'OS', 'Nº O.S.', 'OS_KEY'])
        col_abertura = get_col(df_p, ['ABERTURA', 'DATA ABERTURA'])
        col_critico = get_col(df_p, ['EQUIPAMENTO CRÍTICO', 'EQUIPAMENTO CRITICO'])
        col_parado = get_col(df_p, ['EQUIPAMENTO PARADO', 'PARADO'])
        col_local = get_col(df_p, ['LOCALIZAÇÃO FÍSICA', 'LOCALIZAÇÃO', 'LOCALIZACAO_INVENTARIO'])
        col_serie = get_col(df_p, ['N. SÉRIE', 'N.º SÉRIE', 'SÉRIE'])
        col_tipo = get_col(df_p, ['TIPO EQUIPAMENTO', 'EQUIPAMENTO', 'DESCRIÇÃO'])
        col_estado = get_col(df_p, ['ESTADO', 'ESTADO DA O.S.'])
        col_executor = get_col(df_p, ['EXECUTOR', 'RESPONSÁVEL'])
        
        # Tratamento de datas e cálculo de SLA corrido
        if col_abertura:
            df_p[col_abertura] = pd.to_datetime(df_p[col_abertura], errors='coerce')
            hoje = pd.Timestamp(datetime.today().date())
            df_p['DIAS_EM_ABERTO'] = (hoje - df_p[col_abertura]).dt.days
        else:
            df_p['DIAS_EM_ABERTO'] = 0
            
        # Criação de Faixa de Dias (Envelhecimento da Fila)
        cond_fila = [df_p['DIAS_EM_ABERTO'] <= 5, df_p['DIAS_EM_ABERTO'] <= 15, df_p['DIAS_EM_ABERTO'] <= 30, df_p['DIAS_EM_ABERTO'] <= 60]
        df_p['FAIXA_DIAS'] = np.select(cond_fila, ["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias"], default="Mais de 60 dias")
        
        # Força strings limpas e padronizadas para os filtros lógicos
        if col_critico: df_p[col_critico] = df_p[col_critico].astype(str).str.upper().str.strip()
        if col_parado: df_p[col_parado] = df_p[col_parado].astype(str).str.upper().str.strip()

        # =================================================================
        # INDICADORES EXECUTIVOS DA FILA (MANTIDOS E FIÉIS AO SEU BI)
        # =================================================================
        total_f = len(df_p)
        parados_f = len(df_p[df_p[col_parado] == 'SIM']) if col_parado else 0
        criticos_f = len(df_p[df_p[col_critico] == 'SIM']) if col_critico else 0
        tma_f = df_p['DIAS_EM_ABERTO'].mean() if total_f > 0 else 0

        f_c1, f_c2, f_c3, f_c4 = st.columns(4)
        f_c1.metric("O.S. em Fila de Espera", total_f)
        f_c2.metric("Ativos Totalmente Parados", parados_f, "Gargalo Assistencial", delta_color="inverse" if parados_f > 0 else "normal")
        f_c3.metric("Equipamentos Críticos na Fila", criticos_f, "Prioridade de Despacho", delta_color="inverse" if criticos_f > 0 else "normal")
        f_c4.metric("Tempo Médio de Fila Atual", f"{tma_f:.1f} Dias", "Atraso médio das O.S.")

        st.markdown("<br><h3 style='color: #154899;'>🎛️ Painel de Filtros Operacionais</h3>", unsafe_allow_html=True)

        # =================================================================
        # BLOCO DE FILTROS ROBUSTOS SOLICITADOS
        # =================================================================
        with st.container(border=True):
            r1, r2, r3, r4 = st.columns(4)
            f_num_os = r1.text_input("Número da O.S.", placeholder="Digite o código...")
            f_num_serie = r2.text_input("Número de Série", placeholder="Digite o S/N...")
            f_faixa_dias = r3.multiselect("Faixa de Dias (Atraso)", sorted(df_p['FAIXA_DIAS'].unique()))
            f_local_fisico = r4.multiselect("Localização Física (Setor)", sorted(df_p[col_local].dropna().unique()) if col_local else [])
            
            r5, r6, r7, r8 = st.columns(4)
            f_tipo_equip = r5.multiselect("Tipo de Equipamento", sorted(df_p[col_tipo].dropna().unique()) if col_tipo else [])
            f_estado_os = r6.multiselect("Estado (Status do Chamado)", sorted(df_p[col_estado].dropna().unique()) if col_estado else [])
            f_eq_parado = r7.selectbox("Equipamento Parado?", ["Todos", "SIM", "NÃO"])
            f_eq_critico = r8.selectbox("Equipamento Crítico?", ["Todos", "SIM", "NÃO"])

        # Executa a filtragem cirúrgica na tabela temporária
        df_f = df_p.copy()
        if f_num_os and col_os:
            df_f = df_f[df_f[col_os].astype(str).str.contains(f_num_os, case=False, na=False)]
        if f_num_serie and col_serie:
            df_f = df_f[df_f[col_serie].astype(str).str.contains(f_num_serie, case=False, na=False)]
        if f_faixa_dias:
            df_f = df_f[df_f['FAIXA_DIAS'].isin(f_faixa_dias)]
        if f_local_fisico and col_local:
            df_f = df_f[df_f[col_local].isin(f_local_fisico)]
        if f_tipo_equip and col_tipo:
            df_f = df_f[df_f[col_tipo].isin(f_tipo_equip)]
        if f_estado_os and col_estado:
            df_f = df_f[df_f[col_estado].isin(f_estado_os)]
        if f_eq_parado != "Todos" and col_parado:
            df_f = df_f[df_f[col_parado] == f_eq_parado]
        if f_eq_critico != "Todos" and col_critico:
            df_f = df_f[df_f[col_critico] == f_eq_critico]

        df_f = df_f.sort_values(by='DIAS_EM_ABERTO', ascending=False)

        # =================================================================
        # GRADE DE RESULTADOS DA FILA
        # =================================================================
        st.markdown(f"**Registros Filtrados:** {len(df_f)} ordens pendentes localizadas.")
        
        colunas_grade = [c for c in [col_os, col_tipo, col_serie, col_local, 'DIAS_EM_ABERTO', col_estado, col_executor] if c in df_f.columns]
        
        st.dataframe(
            df_f[colunas_grade],
            use_container_width=True,
            hide_index=True,
            height=240,
            column_config={
                "DIAS_EM_ABERTO": st.column_config.ProgressColumn("Tempo de Espera", format="%d dias", min_value=0, max_value=int(df_p['DIAS_EM_ABERTO'].max()) if len(df_p) > 0 else 100),
                col_os: st.column_config.TextColumn("Nº O.S.")
            }
        )

        st.markdown("---")

        # =================================================================
        # FICHA TÉCNICA DRILL-DOWN + INTEGRAÇÃO COM ATIVIDADES_RECENTES
        # =================================================================
        st.markdown("<h3 style='color: #154899;'>🗂️ Central de Investigação da O.S. (Drill-Down)</h3>", unsafe_allow_html=True)
        
        if not df_f.empty and col_os:
            # Dropdown dinâmico alimentado pelo resultado filtrado acima
            lista_os_str = df_f[col_os].astype(str).unique()
            os_alvo = st.selectbox("Escolha uma Ordem de Serviço da lista para abrir a ficha completa:", options=lista_os_str)
            
            if os_alvo:
                # Isola a linha correspondente à OS selecionada
                dados_linha = df_f[df_f[col_os].astype(str) == os_alvo].iloc[0]
                
                with st.container(border=True):
                    # Cabeçalho da Ficha com Badges Estilizados
                    f_col_t, f_col_b1, f_col_b2 = st.columns([2, 1, 1])
                    nome_eq = dados_linha.get(col_tipo, 'Não Informado')
                    f_col_t.markdown(f"#### Ficha de Atendimento - O.S. № {os_alvo}")
                    f_col_t.markdown(f"**Equipamento:** {nome_eq} | **Chave Ativo:** {dados_linha.get('EQUIP_KEY', 'N/A')}")
                    
                    p_status = "🔴 PARADO (Crítico)" if str(dados_linha.get(col_parado, '')).upper() == 'SIM' else "🟢 EM OPERAÇÃO"
                    c_status = "⚠️ ALTA CRITICIDADE" if str(dados_linha.get(col_critico, '')).upper() == 'SIM' else "ℹ️ CRITICIDADE NORMAL"
                    
                    f_col_b1.markdown(f"**Estado Físico do Ativo:**<br>`{p_status}`", unsafe_allow_html=True)
                    f_col_b2.markdown(f"**Severidade de Gestão:**<br>`{c_status}`", unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # Detalhamento de Informações Cadastrais
                    d1, d2, d3 = st.columns(3)
                    dt_ab = dados_linha.get(col_abertura)
                    dt_ab_str = dt_ab.strftime('%d/%m/%Y') if pd.notnull(dt_ab) else 'N/I'
                    
                    col_tr = get_col(df_f, ['DT. ÚLTIMA TRANSIÇÃO', 'ÚLTIMA TRANSIÇÃO'])
                    dt_tr = dados_linha.get(col_tr)
                    dt_tr_str = pd.to_datetime(dt_tr).strftime('%d/%m/%Y') if pd.notnull(dt_tr) else 'N/I'
                    
                    d1.markdown(f"**📅 Abertura do Chamado:** {dt_ab_str}")
                    d1.markdown(f"**⏳ Dias Consecutivos na Fila:** {dados_linha.get('DIAS_EM_ABERTO', 0)} dias")
                    
                    d2.markdown(f"**📍 Setor Hospitalar Atual:** {dados_linha.get(col_local, 'N/I')}")
                    d2.markdown(f"**🔢 Identificação de Série:** {dados_linha.get(col_serie, 'N/I')}")
                    
                    d3.markdown(f"**⚙️ Estado Interno GETS:** {dados_linha.get(col_estado, 'N/I')}")
                    d3.markdown(f"**👷 Técnico Responsável:** {dados_linha.get(col_executor, 'Não Alocado')}")
                    
                    st.markdown("<br><h5 style='color: #32A347;'>🛠️ Linha do Tempo e Detalhamento Técnico (Atividades Recentes)</h5>", unsafe_allow_html=True)
                    
                    # Busca e renderização das sub-atividades atreladas à O.S. na tabela Atividades_Recentes
                    if not df_atividades.empty:
                        df_at_temp = df_atividades.copy()
                        df_at_temp.columns = df_at_temp.columns.str.strip().str.upper()
                        
                        col_os_at = get_col(df_at_temp, ['O.S.', 'OS', 'OS_KEY'])
                        
                        if col_os_at:
                            # Filtra as linhas de logs de trabalho exclusivas dessa O.S.
                            df_historico_os = df_at_temp[df_at_temp[col_os_at].astype(str).str.replace('.0', '', regex=False).str.strip() == str(os_alvo)]
                            
                            if not df_historico_os.empty:
                                # Organiza colunas amigáveis de histórico para exibição
                                col_data_act = get_col(df_historico_os, ['DATA', 'SNAPSHOT_DT', 'REPORT_CREATED_AT'])
                                col_desc_act = get_col(df_historico_os, ['ATIVIDADE', 'DESCRIÇÃO', 'HISTÓRICO'])
                                col_exec_act = get_col(df_historico_os, ['EXECUTOR', 'TÉCNICO', 'RESPONSÁVEL'])
                                
                                cols_print_act = [c for c in [col_data_act, col_exec_act, col_desc_act] if c]
                                
                                df_print_act = df_historico_os[cols_print_act].copy()
                                if col_data_act:
                                    df_print_act[col_data_act] = pd.to_datetime(df_print_act[col_data_act], errors='coerce')
                                    df_print_act = df_print_act.sort_values(by=col_data_act, ascending=False)
                                    
                                st.dataframe(df_print_act, use_container_width=True, hide_index=True)
                            else:
                                st.info("Esta O.S. está na fila de triagem aguardando o primeiro apontamento técnico ou início de atividade.")
                        else:
                            st.warning("Coluna identificadora de O.S. não localizada no arquivo de Atividades.")
                    else:
                        st.info("Nenhum log ou histórico de ações disponível para cruzamento na pasta Atividades_Recentes.")
        else:
            st.warning("Ajuste os critérios de busca nos filtros para carregar as fichas técnicas.")
    else:
        st.success("Fila zerada no momento!")

# =====================================================================
# TAB 3: PRODUTIVIDADE E TMA
# =====================================================================
with tab_produtividade:
    if not df_enc.empty:
        df_e = df_enc.copy()
        total_entregas = len(df_e)
        
        if 'ABERTURA' in df_e.columns and 'ENCERRAMENTO' in df_e.columns:
            df_e['ABERTURA'] = pd.to_datetime(df_e['ABERTURA'], errors='coerce')
            df_e['ENCERRAMENTO'] = pd.to_datetime(df_e['ENCERRAMENTO'], errors='coerce')
            df_e['DURACAO'] = (df_e['ENCERRAMENTO'] - df_e['ABERTURA']).dt.days
            tma_geral = df_e['DURACAO'].mean()
        else:
            df_e['DURACAO'] = 0
            tma_geral = 0
            
        p1, p2, p3 = st.columns(3)
        p1.metric("Total de Entregas (Filtrado)", f"{total_entregas:,}".replace(",", "."))
        p2.metric("TMA Geral do Atendimento", f"{tma_geral:.1f} dias", "Tempo médio de fechamento")
        p3.metric("Velocidade Média Estimada", f"{int(total_entregas / 12 if total_entregas > 12 else total_entregas)} /mês")

        st.markdown("<br>", unsafe_allow_html=True)
        if 'AnoMes' in df_e.columns:
            st.markdown("##### Histórico Mensal de Conclusão de O.S.")
            df_mensal = df_e.groupby('AnoMes').size().reset_index(name='Entregas')
            df_mensal = df_mensal.sort_values(by='AnoMes')
            fig_mensal = px.line(df_mensal, x='AnoMes', y='Entregas', text='Entregas', markers=True, color_discrete_sequence=['#154899'])
            fig_mensal.update_traces(textposition="top center")
            fig_mensal.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320)
            st.plotly_chart(fig_mensal, use_container_width=True)

# =====================================================================
# TAB 4: GESTÃO FINANCEIRA & ATIVOS
# =====================================================================
with tab_financeiro:
    if not df_inv.empty:
        df_fin = df_inv.copy()
        for col in ['VALOR (R$)', 'CUSTO PEÇA (R$)', 'CUSTO SERVIÇO EXTERNO (R$)']:
            if col in df_fin.columns: df_fin[col] = pd.to_numeric(df_fin[col], errors='coerce').fillna(0)
            else: df_fin[col] = 0.0
                
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
            st.markdown("##### 📊 Valor Patrimonial Acumulado por Tipo de Equipamento")
            col_desc = get_col(df_fin_ativos, ['DESCRIÇÃO', 'TIPO EQUIPAMENTO'])
            if col_desc:
                df_val_tipo = df_fin_ativos.groupby(col_desc)['VALOR (R$)'].sum().reset_index(name='Total_Valor')
                df_val_tipo = df_val_tipo.sort_values(by='Total_Valor', ascending=False).head(10)
                fig_val_tipo = px.bar(df_val_tipo, x='Total_Valor', y=col_desc, orientation='h', text='Total_Valor', color_discrete_sequence=['#154899'])
                fig_val_tipo.update_traces(texttemplate='R$ %{text:,.2s}', textposition='outside')
                fig_val_tipo.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=20, b=20), height=350)
                st.plotly_chart(fig_val_tipo, use_container_width=True)
                
        with fin_g2:
            st.markdown("##### 📈 Curva Histórica de Investimentos em Aquisições")
            if 'AQUISIÇÃO' in df_fin_ativos.columns:
                df_invest_tempo = df_fin_ativos.copy()
                df_invest_tempo['Ano_Aquisicao'] = df_invest_tempo['AQUISIÇÃO'].dt.year
                df_invest_tempo = df_invest_tempo[df_invest_tempo['Ano_Aquisicao'].notna() & (df_invest_tempo['Ano_Aquisicao'] >= 2010)]
                df_curva = df_invest_tempo.groupby('Ano_Aquisicao')['VALOR (R$)'].sum().reset_index(name='Investimento')
                fig_curva = px.area(df_curva, x='Ano_Aquisicao', y='Investimento', markers=True, color_discrete_sequence=['#32A347'])
                fig_curva.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350)
                st.plotly_chart(fig_curva, use_container_width=True)
