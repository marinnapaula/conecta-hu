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
    initial_sidebar_state="collapsed"
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
# 3. CARREGAMENTO E PROCESSAMENTO INTEGRADO DOS DADOS
# =====================================================================
with st.spinner("Consolidando bases e recalculando indicadores..."):
    # Executa as leituras via motores
    df_inv_bruto = carregar_mais_recente("04.Inventário")
    df_pend_bruto = carregar_mais_recente("02.OS_Pendentes")
    df_enc_bruto = carregar_os_encerradas()
    
    # Processa regras de negócio do Inventário
    df_inv_limpo = limpar_dimensao_equipamentos(df_inv_bruto)
    df_inv = enriquecer_base_inventario(df_inv_limpo, df_enc_bruto)

# Criação das abas executivas
tab_parque, tab_fila, tab_produtividade = st.tabs([
    "🏥 Ciclo de Vida do Parque", 
    "📥 Fila Operacional (Pendentes)", 
    "📊 Produtividade & TMA"
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

        # Cards de Indicadores
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Equipamentos Ativos", f"{total_ativos:,}".replace(",", "."))
        c2.metric("Críticos (> 10 anos)", f"{pct_critico_idade:.1f}%", f"{qtd_critico_idade} ativos antigos", delta_color="inverse")
        c3.metric("Conformidade de MP (OK)", f"{pct_mp_ok:.1f}%", "Meta: 100%")
        c4.metric("Fora de Garantia", f"{(qtd_fora_garantia/total_ativos*100):.1f}%", f"{qtd_fora_garantia} equipamentos")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráficos de Ciclo de Vida
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
            # Mapeamento do nome amigável para exibição baseado na ordem criada
            mapa_nomes = {6: "Em Dia (OK)", 5: "Vence em 3m", 4: "Vence em 45d", 3: "Vencido (+1a)", 2: "Crítico (+2a)", 1: "Nunca Realizado (NR)"}
            df_ativos['Status_Label'] = df_ativos['Ordem Status MP'].map(mapa_nomes)
            df_status_mp = df_ativos['Status_Label'].value_counts().reset_index()
            df_status_mp.columns = ['Status', 'Quantidade']
            
            fig_pie_mp = px.pie(df_status_mp, values='Quantidade', names='Status', hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
            fig_pie_mp.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, showlegend=True)
            st.plotly_chart(fig_pie_mp, use_container_width=True)
    else:
        st.info("Base de inventário não disponível.")

# =====================================================================
# TAB 2: FILA OPERACIONAL (PENDENTES)
# =====================================================================
with tab_fila:
    if not df_pend_bruto.empty:
        # Copia e limpa para evitar interferência de colunas semelhantes do GETS
        df_p = df_pend_bruto.copy()
        df_p.columns = df_p.columns.str.strip().str.upper()
        
        total_pendentes = len(df_p)
        
        # Mapeamento robusto de classes de OS
        col_classe = 'CLASSE' if 'CLASSE' in df_p.columns else None
        if col_classe:
            qtd_corretivas = len(df_p[df_p[col_classe].str.upper().str.strip().isin(['MC', 'MANUTENÇÃO CORRETIVA', 'CORRETIVA'])])
            qtd_programadas = len(df_p[df_p[col_classe].str.upper().str.strip().isin(['MP', 'MANUTENÇÃO PROGRAMADA', 'PREVENTIVA', 'CALIBRAÇÃO'])])
        else:
            qtd_corretivas = total_pendentes
            qtd_programadas = 0
            
        pct_corretiva = (qtd_corretivas / total_pendentes * 100) if total_pendentes > 0 else 0
        pct_programada = (qtd_programadas / total_pendentes * 100) if total_pendentes > 0 else 0
        
        # Cálculo de tempo de fila (DAX DATEDIFF)
        col_abertura = 'ABERTURA' if 'ABERTURA' in df_p.columns else None
        if col_abertura:
            df_p[col_abertura] = pd.to_datetime(df_p[col_abertura], errors='coerce')
            hoje = pd.Timestamp(datetime.today().date())
            df_p['DIAS_EM_ABERTO'] = (hoje - df_p[col_abertura]).dt.days
            tma_aberto = df_p['DIAS_EM_ABERTO'].mean()
        else:
            df_p['DIAS_EM_ABERTO'] = 0
            tma_aberto = 0

        # Cards da Fila
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("O.S. Pendentes (Total)", total_pendentes)
        f2.metric("Nº Corretivas (% Fila)", f"{qtd_corretivas} chamados", f"{pct_corretiva:.1f}% MC", delta_color="inverse")
        f3.metric("Nº Programadas (% Fila)", f"{qtd_programadas} chamados", f"{pct_programada:.1f}% MP")
        f4.metric("Tempo Médio OS Aberta", f"{tma_aberto:.1f} dias", "Idade média da fila", delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráficos da Fila
        gf1, gf2 = st.columns(2)
        with gf1:
            st.markdown("##### Envelhecimento da Fila (Faixa de Dias)")
            # Criação dinâmica das faixas estruturadas no DAX original
            condicoes = [df_p['DIAS_EM_ABERTO'] <= 5, df_p['DIAS_EM_ABERTO'] <= 15, df_p['DIAS_EM_ABERTO'] <= 30, df_p['DIAS_EM_ABERTO'] <= 60]
            df_p['Faixa_Fila'] = np.select(condicoes, ["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias"], default="Mais de 60 dias")
            df_p['Ordem_Faixa'] = np.select(condicoes, [1, 2, 3, 4], default=5)
            
            df_faixa_fila = df_p.groupby(['Faixa_Fila', 'Ordem_Faixa']).size().reset_index(name='Qtd')
            df_faixa_fila = df_faixa_fila.sort_values(by='Ordem_Faixa')
            
            fig_faixa_p = px.bar(df_faixa_fila, x='Faixa_Fila', y='Qtd', text='Qtd', color_discrete_sequence=['#32A347'])
            fig_faixa_p.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_faixa_p, use_container_width=True)
            
        with gf2:
            st.markdown("##### Distribuição por Estado Atual do Chamado")
            col_estado = 'ESTADO' if 'ESTADO' in df_p.columns else ('ESTADO DA O.S.' if 'ESTADO DA O.S.' in df_p.columns else None)
            if col_estado:
                df_estado = df_p[col_estado].value_counts().reset_index()
                df_estado.columns = ['Estado', 'Qtd']
                fig_est = px.pie(df_estado, values='Qtd', names='Estado', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_est.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300)
                st.plotly_chart(fig_est, use_container_width=True)
    else:
        st.success("Nenhuma ordem de serviço pendente ou travada na fila!")

# =====================================================================
# TAB 3: PRODUTIVIDADE E TMA
# =====================================================================
with tab_produtividade:
    if not df_enc_bruto.empty:
        df_e = df_enc_bruto.copy()
        df_e.columns = df_e.columns.str.strip().str.upper()
        
        total_entregas = len(df_e)
        
        # SLA e Cálculo de TMA Histórico
        if 'ABERTURA' in df_e.columns and 'ENCERRAMENTO' in df_e.columns:
            df_e['ABERTURA'] = pd.to_datetime(df_e['ABERTURA'], errors='coerce')
            df_e['ENCERRAMENTO'] = pd.to_datetime(df_e['ENCERRAMENTO'], errors='coerce')
            df_e['DURACAO'] = (df_e['ENCERRAMENTO'] - df_e['ABERTURA']).dt.days
            tma_geral = df_e['DURACAO'].mean()
        else:
            df_e['DURACAO'] = 0
            tma_geral = 0
            
        # Cards de Performance
        p1, p2, p3 = st.columns(3)
        p1.metric("Total de Entregas (Histórico)", f"{total_entregas:,}".replace(",", "."))
        p2.metric("TMA Geral do Atendimento", f"{tma_geral:.1f} dias", "Tempo médio de fechamento")
        p3.metric("Velocidade Média Estimada", f"{int(total_entregas / 12 if total_entregas > 12 else total_entregas)} /mês", "Entregas diluídas no tempo")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Histórico de Fechamento por Período
        if 'ENCERRAMENTO' in df_e.columns:
            st.markdown("##### Histórico Mensal de Conclusão de O.S.")
            df_e['AnoMes'] = df_e['ENCERRAMENTO'].dt.strftime('%Y-%m')
            df_mensal = df_e.groupby('AnoMes').size().reset_index(name='Entregas')
            df_mensal = df_mensal.sort_values(by='AnoMes')
            
            fig_mensal = px.line(df_mensal, x='AnoMes', y='Entregas', text='Entregas', markers=True, color_discrete_sequence=['#154899'])
            fig_mensal.update_traces(textposition="top center")
            fig_mensal.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_mensal, use_container_width=True)
    else:
        st.info("Aguardando relatórios consolidados de encerramento para calcular volumetria e TMA.")
