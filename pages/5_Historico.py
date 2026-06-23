import streamlit as st
import pandas as pd
import os
import glob

st.set_page_config(page_title="Histórico | Conecta", page_icon="🕰️", layout="wide")

st.title("🕰️ Histórico e Ficha do Equipamento")
st.markdown("**Rastreabilidade completa de manutenções, peças e agendamentos.**")
st.markdown("---")

@st.cache_data(ttl=600)
def carregar_dados(pasta_nome):
    caminho = os.path.join(os.getcwd(), "planilhas_gets", pasta_nome)
    arquivos = glob.glob(os.path.join(caminho, "*.xlsx"))
    if not arquivos: return pd.DataFrame()
    try:
        df = pd.read_excel(max(arquivos, key=os.path.getmtime), skiprows=5)
        df.columns = df.columns.str.strip().str.upper()
        # Garante que as colunas de busca sejam strings
        for col in ['N. SÉRIE', 'SÉRIE', 'PATRIMÔNIO', 'TAG']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
        return df
    except: return pd.DataFrame()

# =====================================================================
# MOTOR DE BUSCA
# =====================================================================
busca = st.text_input("🔍 Digite o Número de Série ou Patrimônio do Equipamento:", placeholder="Ex: T0500118")

if busca:
    busca = busca.strip().upper()
    with st.spinner(f"Vasculhando arquivos do GETS por '{busca}'..."):
        df_inv = carregar_dados("04.Inventário")
        df_encerradas = carregar_dados("01.OS_Encerradas")
        df_pendentes = carregar_dados("02.OS_Pendentes")
        
        # --- 1. DADOS CADASTRAIS (INVENTÁRIO) ---
        st.markdown("### 📋 Ficha Cadastral")
        achou_cadastral = False
        
        if not df_inv.empty:
            col_busca = 'N. SÉRIE' if 'N. SÉRIE' in df_inv.columns else 'SÉRIE'
            if col_busca in df_inv.columns:
                ficha = df_inv[df_inv[col_busca].str.contains(busca, na=False)]
                if not ficha.empty:
                    achou_cadastral = True
                    eqp = ficha.iloc[0]
                    col1, col2, col3 = st.columns(3)
                    col1.info(f"**Equipamento:** {eqp.get('EQUIPAMENTO', 'N/A')}")
                    col2.info(f"**Marca/Modelo:** {eqp.get('MARCA', 'N/A')} / {eqp.get('MODELO', 'N/A')}")
                    col3.info(f"**Localização:** {eqp.get('LOCALIZAÇÃO FÍSICA', 'N/A')}")
        
        if not achou_cadastral:
            st.warning("Equipamento não localizado no Inventário ativo. Buscando no histórico de O.S...")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- 2. GUIAS DE HISTÓRICO (TABS) ---
        tab1, tab2 = st.tabs(["🔴 O.S. Pendentes (Atuais)", "🟢 O.S. Encerradas (Histórico)"])
        
        with tab1:
            if not df_pendentes.empty:
                col_busca_pend = 'N. SÉRIE' if 'N. SÉRIE' in df_pendentes.columns else 'SÉRIE'
                if col_busca_pend in df_pendentes.columns:
                    pendentes_eqp = df_pendentes[df_pendentes[col_busca_pend].str.contains(busca, na=False)]
                    if not pendentes_eqp.empty:
                        st.error(f"⚠️ Atenção: Este equipamento possui {len(pendentes_eqp)} O.S. aberta(s)!")
                        st.dataframe(pendentes_eqp, use_container_width=True)
                    else:
                        st.success("Tudo certo! Nenhuma O.S. pendente para este equipamento no momento.")
                else:
                    st.write("Coluna de série não encontrada no relatório de pendentes.")
                    
        with tab2:
            if not df_encerradas.empty:
                col_busca_enc = 'N. SÉRIE' if 'N. SÉRIE' in df_encerradas.columns else 'SÉRIE'
                if col_busca_enc in df_encerradas.columns:
                    encerradas_eqp = df_encerradas[df_encerradas[col_busca_enc].str.contains(busca, na=False)]
                    if not encerradas_eqp.empty:
                        st.write(f"Encontramos **{len(encerradas_eqp)}** intervenções no histórico deste equipamento.")
                        # Ordena da mais recente para a mais antiga (assumindo que existe a coluna DATA)
                        col_ordem = 'DATA DE ABERTURA' if 'DATA DE ABERTURA' in encerradas_eqp.columns else encerradas_eqp.columns[0]
                        st.dataframe(encerradas_eqp.sort_values(by=col_ordem, ascending=False), use_container_width=True)
                    else:
                        st.info("Nenhuma manutenção corretiva ou preventiva encerrada localizada no histórico recente.")
