import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
# Importamos as funções que você já tem prontas no seu motor
from motor_dados import carregar_os_encerradas, carregar_mais_recente

st.set_page_config(page_title="Laboratório de Calendário", layout="wide")
st.title("📅 Laboratório de Testes: Calendário de Engenharia")

# --- 1. CARREGAMENTO COMPLETO DE DADOS ---
@st.cache_data(ttl=600)
def buscar_dados_calendario():
    # Carrega encerradas e pendentes para cruzar no calendário
    df_encerradas = carregar_os_encerradas()
    df_pendentes = carregar_mais_recente("02.OS_Pendentes")
    return df_encerradas, df_pendentes

df_enc, df_pend = buscar_dados_calendario()

if df_enc.empty and df_pend.empty:
    st.error("Não encontramos dados nas pastas do GETS para alimentar o calendário.")
    st.stop()

# --- 2. SELEÇÃO DE PERÍODO ---
st.sidebar.header("Configurações do Calendário")
ano_atual = datetime.today().year
mes_atual = datetime.today().month

ano_sel = st.sidebar.selectbox("Selecione o Ano", sorted(list(set([ano_atual, 2025, 2026])), reverse=True))
meses_nome = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
mes_nome_sel = st.sidebar.selectbox("Selecione o Mês", meses_nome, index=mes_atual-1)
mes_sel = meses_nome.index(mes_nome_sel) + 1

# --- 3. PROCESSAMENTO DOS INDICADORES POR DIA ---
# Vamos descobrir quantas OS foram abertas, fechadas ou estão críticas em cada dia
dados_por_dia = {}

# Processando Aberturas (de todas as OS disponíveis)
for df_temp in [df_enc, df_pend]:
    if 'ABERTURA' in df_temp.columns and not df_temp.empty:
        df_valid = df_temp.dropna(subset=['ABERTURA'])
        df_filtrado = df_valid[(df_valid['ABERTURA'].dt.year == ano_sel) & (df_valid['ABERTURA'].dt.month == mes_sel)]
        for dia, group in df_filtrado.groupby(df_filtrado['ABERTURA'].dt.day):
            if dia not in dados_por_dia: dados_por_dia[dia] = {'abertas': 0, 'fechadas': 0, 'criticas': 0}
            dados_por_dia[dia]['abertas'] += len(group)

# Processando Encerramentos
if 'ENCERRAMENTO' in df_enc.columns and not df_enc.empty:
    df_valid_enc = df_enc.dropna(subset=['ENCERRAMENTO'])
    df_filtrado_enc = df_valid_enc[(df_valid_enc['ENCERRAMENTO'].dt.year == ano_sel) & (df_valid_enc['ENCERRAMENTO'].dt.month == mes_sel)]
    for dia, group in df_filtrado_enc.groupby(df_filtrado_enc['ENCERRAMENTO'].dt.day):
        if dia not in dados_por_dia: dados_por_dia[dia] = {'abertas': 0, 'fechadas': 0, 'criticas': 0}
        dados_por_dia[dia]['fechadas'] += len(group)

# --- 4. RENDERIZAÇÃO DA GRADE DO CALENDÁRIO ---
st.subheader(f"Visão Mensal - {mes_nome_sel} de {ano_sel}")

# Dias da semana no cabeçalho
dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
cols_header = st.columns(7)
for idx, col in enumerate(cols_header):
    col.markdown(f"<p style='text-align: center; font-weight: bold;'>{dias_semana[idx]}</p>", unsafe_allow_html=True)

# Pega a matriz de semanas do mês (onde 0 significa dia fora do mês)
matriz_mes = calendar.monthcalendar(ano_sel, mes_sel)

for semana in matriz_mes:
    cols_dia = st.columns(7)
    for idx, dia in enumerate(semana):
        with cols_dia[idx]:
            if dia == 0:
                # Espaço vazio para dias que não pertencem a este mês
                st.markdown("<div style='min-height: 100px; background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 5px;'></div>", unsafe_allow_html=True)
            else:
                # Busca indicadores calculados para o dia
                info = dados_por_dia.get(dia, {'abertas': 0, 'fechadas': 0, 'criticas': 0})
                
                # Monta o card visual do dia
                bg_color = "#ffffff"
                if info['abertas'] > info['fechadas'] and info['abertas'] > 0:
                    bg_color = "#fff3cd"  # Alerta amarelo se acumulou mais chamados abertos que fechados
                
                html_card = f"""
                <div style='min-height: 110px; background-color: {bg_color}; border: 1px solid #dee2e6; border-radius: 5px; padding: 5px; box-shadow: 1px 1px 3px rgba(0,0,0,0.05);'>
                    <span style='font-weight: bold; font-size: 14px; color: #495057;'>{dia}</span>
                    <div style='margin-top: 5px; font-size: 11px;'>
                        <span style='color: #dc3545;'>📥 Aberto: {info['abertas']}</span><br>
                        <span style='color: #28a745;'>📤 Fechado: {info['fechadas']}</span>
                    </div>
                </div>
                """
                st.markdown(html_card, unsafe_allow_html=True)
                
                # Botão invisível/pequeno para ver detalhes do dia se necessário
                if info['abertas'] > 0 or info['fechadas'] > 0:
                if st.button(f"🔍 Detalhes {dia}", key=f"btn_{dia}"):
                        st.session_state['dia_selecionado'] = dia

# --- 5. DETALHES DO DIA SELECIONADO ---
if 'dia_selecionado' in st.session_state:
    dia_sel = st.session_state['dia_selecionado']
    st.divider()
    st.subheader(f"📋 Ordens de Serviço do Dia {dia_sel}/{mes_sel}/{ano_sel}")
    
    # Aqui você pode filtrar o df_pend ou df_enc para mostrar a tabela exata das OS do dia
    st.info(f"Filtro ativado para exibir detalhes das manutenções do dia {dia_sel}.")
