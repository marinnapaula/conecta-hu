import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
# Importação do motor de inteligência
from motor_dados import (
    carregar_mais_recente, 
    carregar_os_encerradas, 
    limpar_dimensao_equipamentos, 
    enriquecer_base_inventario
)

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E IDENTIDADE VISUAL (CSS)
# =====================================================================
st.set_page_config(
    page_title="Dashboard | Conecta",
    page_icon=":material/bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded" # Deixei expandido para mostrar os filtros
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
# 3. CARREGAMENTO DOS DADOS (CACHE)
# =====================================================================
@st.cache_data(ttl=600)
def obter_dados_processados():
    df_inv_bruto = carregar_mais_recente("04.Inventário")
    df_pend_bruto = carregar_mais_recente("02.OS_Pendentes")
    df_enc_bruto = carregar_os_encerradas()
    
    df_inv_limpo = limpar_dimensao_equipamentos(df_inv_bruto)
    df_inv_final = enriquecer_base_inventario(df_inv_limpo, df_enc_bruto)
    
    return df_inv_final, df_pend_bruto, df_enc_bruto

with st.spinner("Sincronizando banco de dados..."):
    df_inv, df_pend_bruto, df_enc_bruto = obter_dados_processados()

# =====================================================================
# 4. BARRA LATERAL (FILTROS CRUZADOS ESTILO POWER BI)
# =====================================================================
st.sidebar.markdown("<h2 style='text-align: center; color: #154899;'>Filtros Globais</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Função auxiliar de busca flexível de colunas
def get_col(df, options):
    for o in options:
        if o in df.columns: return o
    return None

# --- Extração de Listas Únicas para os Filtros ---
locais_disponiveis = []
tipos_disponiveis = []

if not df_inv.empty:
    if 'LOCALIZAÇÃO FÍSICA' in df_inv.columns:
        locais_disponiveis = sorted(df_inv['LOCALIZAÇÃO FÍSICA'].dropna().unique())
    if 'DESCRIÇÃO' in df_inv.columns:
        tipos_disponiveis = sorted(df_inv['DESCRIÇÃO'].dropna().unique())

# --- Widgets do Streamlit ---
filtro_local = st.sidebar.multiselect("📍 Setor / Localização", locais_disponiveis, placeholder="Todos os setores")
filtro_tipo = st.sidebar.multiselect("📟 Tipo de Equipamento", tipos_disponiveis, placeholder="Todos os tipos")

st.sidebar.markdown("---")
st.sidebar.markdown("**Filtro Exclusivo de Produtividade**")

# Filtro de Período (Extrai os meses de encerramento da base)
meses_disponiveis = []
if not df_enc_bruto.empty and 'ENCERRAMENTO' in df_enc_bruto.columns:
    df_enc_bruto['AnoMes'] = df_enc_bruto['ENCERRAMENTO'].dt.strftime('%Y-%m')
    meses_disponiveis = sorted(df_enc_bruto['AnoMes'].dropna().unique(), reverse=True)
    
filtro_periodo = st.sidebar.multiselect("📅 Mês de Encerramento", meses_disponiveis, placeholder="Todo o histórico")

# --- APLICAÇÃO DOS FILTROS (MÁQUINA DE CRUZAMENTO) ---
# 1. Filtra Inventário
if filtro_local and not df_inv.empty:
    df_inv = df_inv[df_inv['LOCALIZAÇÃO FÍSICA'].isin(filtro_local)]
if filtro_tipo and not df_inv.empty:
    df_inv = df_inv[df_inv['DESCRIÇÃO'].isin(filtro_tipo)]

# 2. Filtra Pendentes
if not df_pend_bruto.empty:
    df_pend = df_pend_bruto.copy()
    col_loc_p = get_col(df_pend, ['LOCALIZAÇÃO FÍSICA', 'LOCALIZAÇÃO'])
    col_tip_p = get_col(df_pend, ['TIPO EQUIPAMENTO', 'EQUIPAMENTO'])
    
    if filtro_local and col_loc_p: df_pend = df_pend[df_pend[col_loc_p].isin(filtro_local)]
    if filtro_tipo and col_tip_p:  df_pend = df_pend[df_pend[col_tip_p].isin(filtro_tipo)]
else:
    df_pend = pd.DataFrame()

# 3. Filtra Encerradas
if not df_enc_bruto.empty:
    df_enc = df_enc_bruto.copy()
    col_loc_e = get_col(df_enc, ['LOCALIZAÇÃO FÍSICA', 'LOCALIZAÇÃO'])
    col_tip_e = get_col(df_enc, ['TIPO EQUIPAMENTO', 'EQUIPAMENTO'])
    
    if filtro_local and col_loc_e: df_enc = df_enc[df_enc[col_loc_e].isin(filtro_local)]
    if filtro_tipo and col_tip_e:  df_enc = df_enc[df_enc[col_tip_e].isin(filtro_tipo)]
    if filtro_periodo:             df_enc = df_enc[df_enc['AnoMes'].isin(filtro_periodo)]
else:
    df_enc = pd.DataFrame()

# =====================================================================
# 5. ABAS DO PAINEL
# =====================================================================
tab_parque, tab_fila, tab_produtividade, tab_financeiro = st.tabs([
    "🏥 Ciclo de Vida do Parque", 
    "📥 Fila Operacional (Pendentes)", 
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
        
        qtd_mp_ok = len(df_ativos[df_ativos['Ordem Status MP'] == 6])
        pct_mp_ok = (qtd_mp_ok / total_ativos * 100) if total_ativos > 0 else 0
        
        qtd_mp_nr = len(df_ativos[df_ativos['Ordem Status MP'] == 1])
        qtd_vencido = len(df_ativos[df_ativos['Ordem Status MP'].isin([2, 3])])
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
            mapa_nomes = {6: "Em Dia (OK)", 5: "Vence em 3m", 4: "Vence em 45d", 3: "Vencido (+1a)", 2: "Crítico (+2a)", 1: "Nunca Realizado (NR)"}
            df_ativos['Status_Label'] = df_ativos['Ordem Status MP'].map(mapa_nomes)
            df_status_mp = df_ativos['Status_Label'].value_counts().reset_index()
            df_status_mp.columns = ['Status', 'Quantidade']
            
            fig_pie_mp = px.pie(df_status_mp, values='Quantidade', names='Status', hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
            fig_pie_mp.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, showlegend=True)
            st.plotly_chart(fig_pie_mp, use_container_width=True)
    else:
        st.info("Base de inventário vazia ou filtrada por completo.")

# =====================================================================
# TAB 2: CENTRO DE COMANDO OPERACIONAL (ACOMPANHAMENTO DE FILA)
# =====================================================================
with tab_fila:
    if not df_pend.empty:
        df_p = df_pend.copy()
        
        # 1. PREPARAÇÃO DAS COLUNAS E CÁLCULO DE TEMPO (Antes dos filtros)
        col_abertura = get_col(df_p, ['ABERTURA'])
        if col_abertura:
            df_p[col_abertura] = pd.to_datetime(df_p[col_abertura], errors='coerce')
            hoje = pd.Timestamp(datetime.today().date())
            df_p['DIAS_EM_ABERTO'] = (hoje - df_p[col_abertura]).dt.days
        else:
            df_p['DIAS_EM_ABERTO'] = 0

        # Cria a Faixa de Dias para usar no filtro
        condicoes = [df_p['DIAS_EM_ABERTO'] <= 5, df_p['DIAS_EM_ABERTO'] <= 15, df_p['DIAS_EM_ABERTO'] <= 30, df_p['DIAS_EM_ABERTO'] <= 60]
        df_p['FAIXA_DIAS'] = np.select(condicoes, ["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias"], default="Mais de 60 dias")

        # Garante a existência das colunas para os filtros não quebrarem
        col_os = get_col(df_p, ['O.S.', 'OS', 'Nº O.S.'])
        col_critico = get_col(df_p, ['EQUIPAMENTO CRÍTICO', 'EQUIPAMENTO CRITICO'])
        col_parado = get_col(df_p, ['EQUIPAMENTO PARADO', 'PARADO'])
        col_local = get_col(df_p, ['LOCALIZAÇÃO FÍSICA', 'LOCALIZAÇÃO', 'LOCALIZACAO_INVENTARIO'])
        col_serie = get_col(df_p, ['N. SÉRIE', 'N.º SÉRIE', 'SÉRIE'])
        col_tipo = get_col(df_p, ['TIPO EQUIPAMENTO', 'EQUIPAMENTO', 'DESCRIÇÃO'])
        col_estado = get_col(df_p, ['ESTADO', 'ESTADO DA O.S.'])
        col_executor = get_col(df_p, ['EXECUTOR', 'RESPONSÁVEL'])
        
        # Padroniza Sim/Não para evitar bugs de filtro
        if col_critico: df_p[col_critico] = df_p[col_critico].astype(str).str.upper().str.strip()
        if col_parado: df_p[col_parado] = df_p[col_parado].astype(str).str.upper().str.strip()

        # =================================================================
        # 2. PAINEL DE FILTROS ROBUSTOS
        # =================================================================
        st.markdown("### 🔎 Filtros Avançados de Busca")
        with st.expander("Clique aqui para expandir e filtrar a fila", expanded=True):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            
            # Filtros de Texto / Específicos
            filtro_os = f_col1.text_input("Nº da O.S.", placeholder="Ex: 261434")
            filtro_serie = f_col2.text_input("Nº de Série", placeholder="Ex: ARXF-0277")
            
            # Filtros de Seleção (Multi)
            opcoes_faixa = sorted(df_p['FAIXA_DIAS'].unique())
            filtro_faixa = f_col3.multiselect("Faixa de Dias (Atraso)", opcoes_faixa)
            
            opcoes_local = sorted(df_p[col_local].dropna().unique()) if col_local else []
            filtro_loc = f_col4.multiselect("Localização Física", opcoes_local)
            
            f_col5, f_col6, f_col7, f_col8 = st.columns(4)
            opcoes_tipo = sorted(df_p[col_tipo].dropna().unique()) if col_tipo else []
            filtro_tp = f_col5.multiselect("Tipo de Equipamento", opcoes_tipo)
            
            opcoes_estado = sorted(df_p[col_estado].dropna().unique()) if col_estado else []
            filtro_est = f_col6.multiselect("Estado da O.S.", opcoes_estado)

            # Filtros Críticos (Toggles / Select)
            filtro_parado = f_col7.selectbox("Equipamento Parado?", ["Todos", "SIM", "NÃO"])
            filtro_critico = f_col8.selectbox("Equipamento Crítico?", ["Todos", "SIM", "NÃO"])

        # =================================================================
        # 3. APLICAÇÃO DOS FILTROS (MÁQUINA DE BUSCA)
        # =================================================================
        df_filtrado = df_p.copy()
        
        if filtro_os and col_os:
            df_filtrado = df_filtrado[df_filtrado[col_os].astype(str).str.contains(filtro_os, case=False, na=False)]
        if filtro_serie and col_serie:
            df_filtrado = df_filtrado[df_filtrado[col_serie].astype(str).str.contains(filtro_serie, case=False, na=False)]
        if filtro_faixa:
            df_filtrado = df_filtrado[df_filtrado['FAIXA_DIAS'].isin(filtro_faixa)]
        if filtro_loc and col_local:
            df_filtrado = df_filtrado[df_filtrado[col_local].isin(filtro_loc)]
        if filtro_tp and col_tipo:
            df_filtrado = df_filtrado[df_filtrado[col_tipo].isin(filtro_tp)]
        if filtro_est and col_estado:
            df_filtrado = df_filtrado[df_filtrado[col_estado].isin(filtro_est)]
        if filtro_parado != "Todos" and col_parado:
            df_filtrado = df_filtrado[df_filtrado[col_parado] == filtro_parado]
        if filtro_critico != "Todos" and col_critico:
            df_filtrado = df_filtrado[df_filtrado[col_critico] == filtro_critico]

        # Ordena sempre do mais atrasado para o mais novo
        df_filtrado = df_filtrado.sort_values(by='DIAS_EM_ABERTO', ascending=False)

        # =================================================================
        # 4. TABELA DE RESULTADOS
        # =================================================================
        st.markdown(f"**Resultados encontrados:** {len(df_filtrado)} O.S. na fila com os filtros atuais.")
        
        colunas_visao = [c for c in [col_os, col_tipo, col_serie, col_local, 'DIAS_EM_ABERTO', col_estado, col_executor] if c in df_filtrado.columns]
        
        st.dataframe(
            df_filtrado[colunas_visao],
            use_container_width=True,
            hide_index=True,
            height=250, # Mantém a tabela compacta para caber a ficha embaixo
            column_config={
                "DIAS_EM_ABERTO": st.column_config.ProgressColumn("SLA (Dias Aberta)", format="%d dias", min_value=0, max_value=int(df_p['DIAS_EM_ABERTO'].max())),
                col_os: st.column_config.TextColumn("Nº O.S.")
            }
        )

        st.markdown("---")

        # =================================================================
        # 5. FICHA DETALHADA DA O.S. (DRILL-DOWN INTERATIVO)
        # =================================================================
        st.markdown("### 🗂️ Ficha de Detalhamento da O.S.")
        
        if not df_filtrado.empty and col_os:
            # Dropdown para o usuário escolher qual OS da tabela ele quer investigar
            os_selecionada = st.selectbox(
                "Selecione o Número da O.S. para abrir os detalhes completos:", 
                options=df_filtrado[col_os].astype(str).unique()
            )
            
            if os_selecionada:
                # Puxa os dados da linha exata selecionada
                dados_os = df_filtrado[df_filtrado[col_os].astype(str) == os_selecionada].iloc[0]
                
                # Monta um "Card" visual com container
                with st.container(border=True):
                    c_cab1, c_cab2, c_cab3 = st.columns([2, 1, 1])
                    
                    equipamento_nome = dados_os.get(col_tipo, 'N/I')
                    marca_modelo = dados_os.get('MM_KEY', dados_os.get('MARCA', '') + ' | ' + dados_os.get('MODELO', 'N/I'))
                    
                    c_cab1.markdown(f"#### O.S. {os_selecionada} - {equipamento_nome}")
                    c_cab1.markdown(f"**Marca/Modelo:** {marca_modelo}")
                    
                    # Badges de Alerta
                    parado_badge = "🔴 PARADO" if str(dados_os.get(col_parado, '')).upper() == 'SIM' else "🟢 FUNCIONANDO"
                    critico_badge = "⚠️ CRÍTICO" if str(dados_os.get(col_critico, '')).upper() == 'SIM' else "ℹ️ NORMAL"
                    
                    c_cab2.markdown(f"**Status Físico:**<br>{parado_badge}", unsafe_allow_html=True)
                    c_cab3.markdown(f"**Criticidade:**<br>{critico_badge}", unsafe_allow_html=True)
                    
                    st.divider()
                    
                    c_det1, c_det2, c_det3, c_det4 = st.columns(4)
                    
                    # Informações da Fila e Datas
                    data_abertura = dados_os.get(col_abertura)
                    data_abertura_str = data_abertura.strftime('%d/%m/%Y') if pd.notnull(data_abertura) else 'N/I'
                    
                    col_transicao = get_col(df_filtrado, ['DT. ÚLTIMA TRANSIÇÃO', 'ÚLTIMA TRANSIÇÃO'])
                    data_trans = dados_os.get(col_transicao)
                    data_trans_str = pd.to_datetime(data_trans).strftime('%d/%m/%Y') if pd.notnull(data_trans) else 'N/I'
                    
                    c_det1.markdown(f"**📅 Data de Abertura:**<br>{data_abertura_str}", unsafe_allow_html=True)
                    c_det1.markdown(f"**⏳ Tempo na Fila:**<br>{dados_os.get('DIAS_EM_ABERTO', 0)} dias", unsafe_allow_html=True)
                    
                    c_det2.markdown(f"**📍 Localização Atual:**<br>{dados_os.get(col_local, 'N/I')}", unsafe_allow_html=True)
                    c_det2.markdown(f"**🔢 Nº de Série:**<br>{dados_os.get(col_serie, 'N/I')}", unsafe_allow_html=True)
                    
                    c_det3.markdown(f"**⚙️ Estado da O.S.:**<br>{dados_os.get(col_estado, 'N/I')}", unsafe_allow_html=True)
                    c_det3.markdown(f"**🔄 Última Transição:**<br>{data_trans_str}", unsafe_allow_html=True)
                    
                    c_det4.markdown(f"**👷 Executor / Responsável:**<br>{dados_os.get(col_executor, 'Não Alocado')}", unsafe_allow_html=True)
                    c_det4.markdown(f"**🛠️ Classe:**<br>{dados_os.get(get_col(df_filtrado, ['CLASSE']), 'N/I')}", unsafe_allow_html=True)
        else:
            st.warning("Ajuste os filtros acima para encontrar Ordens de Serviço.")
            
    else:
        st.success("Não há Ordens de Serviço Pendentes carregadas no sistema.")
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
        p3.metric("Velocidade Média Estimada", f"{int(total_entregas / 12 if total_entregas > 12 else total_entregas)} /mês", "Baseado na seleção")

        st.markdown("<br>", unsafe_allow_html=True)
        
        if 'AnoMes' in df_e.columns:
            st.markdown("##### Histórico Mensal de Conclusão de O.S.")
            df_mensal = df_e.groupby('AnoMes').size().reset_index(name='Entregas')
            df_mensal = df_mensal.sort_values(by='AnoMes')
            
            fig_mensal = px.line(df_mensal, x='AnoMes', y='Entregas', text='Entregas', markers=True, color_discrete_sequence=['#154899'])
            fig_mensal.update_traces(textposition="top center")
            fig_mensal.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_mensal, use_container_width=True)
    else:
        st.info("Nenhuma entrega registrada para este cruzamento de filtros.")

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
        custo_pecas_total = df_fin_ativos['CUSTO PEÇA (R$)'].sum()
        custo_servicos_total = df_fin_ativos['CUSTO SERVIÇO EXTERNO (R$)'].sum()
        custo_manutencao_total = custo_pecas_total + custo_servicos_total
        ticket_medio_ativo = df_fin_ativos['VALOR (R$)'].mean() if len(df_fin_ativos) > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Investimento Total (Patrimônio)", f"R$ {patrimonio_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m2.metric("Custo Acumulado Manutenção", f"R$ {custo_manutencao_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m3.metric("Ticket Médio por Ativo", f"R$ {ticket_medio_ativo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m4.metric("Despesa com Serviços Externos", f"R$ {custo_servicos_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

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
                fig_val_tipo.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=20, b=20), height=350, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig_val_tipo, use_container_width=True)
                
        with fin_g2:
            st.markdown("##### 📈 Curva Histórica de Investimentos em Aquisições")
            if 'AQUISIÇÃO' in df_fin_ativos.columns:
                df_invest_tempo = df_fin_ativos.copy()
                df_invest_tempo['Ano_Aquisicao'] = df_invest_tempo['AQUISIÇÃO'].dt.year
                df_invest_tempo = df_invest_tempo[df_invest_tempo['Ano_Aquisicao'].notna() & (df_invest_tempo['Ano_Aquisicao'] >= 2010)]
                df_curva = df_invest_tempo.groupby('Ano_Aquisicao')['VALOR (R$)'].sum().reset_index(name='Investimento')
                df_curva = df_curva.sort_values(by='Ano_Aquisicao')
                
                fig_curva = px.area(df_curva, x='Ano_Aquisicao', y='Investimento', markers=True, color_discrete_sequence=['#32A347'])
                fig_curva.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350, xaxis_title="Ano de Compra", yaxis_title=None)
                st.plotly_chart(fig_curva, use_container_width=True)
