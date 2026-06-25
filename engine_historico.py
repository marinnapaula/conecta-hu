import pandas as pd
import glob
import os
import re

def extrair_data_do_nome(nome_arquivo):
    match = re.search(r'RelOSsPendentes(\d{4})(\d{2})(\d{2})', nome_arquivo)
    if match:
        ano, mes, dia = match.groups()
        return pd.Timestamp(f"{ano}-{mes}-{dia}")
    return None

def categorizar_faixa(dias):
    if pd.isna(dias): return "Indefinido"
    if dias <= 5: return "0 a 5 dias"
    if dias <= 15: return "6 a 15 dias"
    if dias <= 30: return "16 a 30 dias"
    if dias <= 60: return "31 a 60 dias"
    return "Mais de 60 dias"

def obter_dados_historico():
    caminho_pasta = os.path.join(os.getcwd(), "planilhas_gets", "02.OS_Pendentes")
    arquivos = glob.glob(os.path.join(caminho_pasta, "RelOSsPendentes*.*"))
    
    lista_dfs = []
    
    for arq in arquivos:
        if not arq.lower().endswith(('.xlsx', '.xls', '.csv')): continue
        
        try:
            if arq.lower().endswith('.csv'):
                df = pd.read_csv(arq, sep=None, engine='python', dtype=str, encoding='latin1')
            else:
                df = pd.read_excel(arq, dtype=str)
                
            df.columns = df.columns.str.strip().str.upper()
            
            c_os = next((c for c in df.columns if 'O.S.' in c or 'OS' in c), None)
            c_abert = next((c for c in df.columns if 'ABERTURA' in c), None)
            
            if c_os and c_abert:
                # Limpeza de data
                df['DT_ABERTURA'] = pd.to_datetime(df[c_abert].astype(str).str.split(',').str[-1], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['DT_ABERTURA'])
                
                # Data do snapshot
                data_ref = extrair_data_do_nome(os.path.basename(arq))
                if data_ref:
                    df['DT_SNAP'] = data_ref
                    df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
                    df['FAIXA_DIAS'] = df['DIAS_ABERTO'].apply(categorizar_faixa)
                    lista_dfs.append(df[['DT_SNAP', 'FAIXA_DIAS', c_os]])
        except: continue
            
    if not lista_dfs: return pd.DataFrame(), "Sem dados"
    
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    # --- AQUI ESTÁ O SEGREDO DO GRÁFICO ---
    # Cria uma grade completa de Data + Faixa
    todas_datas = df_final['DT_SNAP'].unique()
    todas_faixas = ["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias", "Mais de 60 dias"]
    
    idx = pd.MultiIndex.from_product([todas_datas, todas_faixas], names=['DT_SNAP', 'FAIXA_DIAS'])
    
    # Conta e preenche com zero onde não tiver dado
    resultado = df_final.groupby(['DT_SNAP', 'FAIXA_DIAS']).size().reindex(idx, fill_value=0).reset_index(name='Volume')
    
    return resultado.sort_values('DT_SNAP'), "Sucesso!"
