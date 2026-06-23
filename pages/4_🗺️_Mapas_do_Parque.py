
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

st.set_page_config(page_title="Mapa do Parque | Conecta", page_icon="🗺️", layout="wide")

st.title("🗺️ Mapa do Parque Tecnológico")
st.markdown("**Monitoramento de Disponibilidade e Concentração de Falhas por Setor.**")
st.markdown("---")

@st.cache_data(ttl=600)
def carregar_dados(pasta_nome):
    caminho = os.path.join(os.getcwd(), "planilhas_gets", pasta_nome)
    arquivos = glob.glob(os.path.join(caminho, "*.xlsx"))
    if not arquivos: return pd.DataFrame()
    try:
        df = pd.read_excel(max(arquivos, key=os.path.getmtime), skiprows=5)
        df.columns = df.columns.str.strip().str.upper()
        return df
    except: return pd.DataFrame()

with st.spinner("Analisando parque tecnológico..."):
    df_inventario = carregar_dados("04.Inventário")
    df_pendentes = carregar_dados("02.OS_Pendentes")

if df_inventario.empty:
    st.warning("Base de inventário não encontrada. Aguarde a próxima extração do robô.")
else:
    # 1. CÁLCULO DE DISPONIBILIDADE
    total_ativos = len(df_inventario)
    
    # Filtra apenas OS Corretivas (equipamento quebrado) se a coluna existir
    if not df_pendentes.empty and 'TIPO DE MANUTENÇÃO' in df_pendentes.columns:
        df_quebrados = df_pendentes[df_pendentes['TIPO DE MANUTENÇÃO'].str.contains('CORRETIVA', na=False, case=False)]
        ativos_parados = len(df_quebrados)
    else:
        df_quebrados = df_pendentes
        ativos_parados = len(df_pendentes) if not df_pendentes.empty else 0

    disponibilidade = ((total_ativos - ativos_parados) / total_ativos) * 100 if total_ativos > 0 else 100

    # 2. INDICADORES VITAIS
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Equipamentos (Inventário)", f"{total_ativos:,}".replace(",", "."))
    col2.metric("Equipamentos Parados (Corretiva)", ativos_parados, delta="Ação Necessária" if ativos_parados > 0 else "Estável", delta_color="inverse")
    col3.metric("Taxa de Disponibilidade Geral", f"{disponibilidade:.1f}%", delta="Meta: 95%", delta_color="normal" if disponibilidade >= 95 else "inverse")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # 3. MAPA DE CALOR (TREEMAP)
    st.markdown("### 🔥 Mapa de Calor de Falhas por Setor")
    
    # Tenta achar a coluna de localização na planilha de pendentes
    col_local = 'LOCALIZAÇÃO FÍSICA' if 'LOCALIZAÇÃO FÍSICA' in df_quebrados.columns else 'LOCALIZAÇÃO'
    
    if not df_quebrados.empty and col_local in df_quebrados.columns:
        # Conta quantas falhas existem por setor
        df_calor = df_quebrados.groupby(col_local).size().reset_index(name='FALHAS')
        df_calor['HOSPITAL'] = 'HU-UNIVASF' # Raiz do gráfico
        
        fig = px.treemap(
            df_calor, 
            path=['HOSPITAL', col_local], 
            values='FALHAS',
            color='FALHAS',
            color_continuous_scale='Reds',
            title="Tamanho do bloco = Quantidade de O.S. Abertas no Setor"
        )
        fig.update_layout(margin=dict(t=30, l=0, r=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Para exibir o Mapa de Calor, a coluna de Localização precisa estar presente no relatório de O.S. Pendentes.")
