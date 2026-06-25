import pandas as pd
import glob
import os
import re

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
                df = pd.read_excel(arq, dtype=str, engine='openpyxl' if arq.endswith('x') else 'xlrd')
                
            df.columns = df.columns.str.strip().str.upper()
            
            # Identifica colunas
            c_os = next((c for c in df.columns if 'O.S.' in c or 'OS' in c), None)
            c_abert = next((c for c in df.columns if 'ABERTURA' in c), None)
            
            if c_os and c_abert:
                # Converte abertura
                df['DT_ABERTURA'] = pd.to_datetime(df[c_abert].astype(str).str.split(',').str[-1], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['DT_ABERTURA'])
                
                # Extrai data do nome
                match = re.search(r'RelOSsPendentes(\d{4})(\d{2})(\d{2})', os.path.basename(arq))
                df['DT_SNAP'] = pd.Timestamp(f"{match.group(1)}-{match.group(2)}-{match.group(3)}") if match else pd.to_datetime(os.path.getmtime(arq), unit='s')
                
                df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
                lista_dfs.append(df[['DT_SNAP', 'DIAS_ABERTO', c_os]])
        except: continue
            
    if not lista_dfs: return pd.DataFrame(), "Sem dados"
    
    df_total = pd.concat(lista_dfs, ignore_index=True)
    
    # AGORA GARANTIMOS O NOME DAS COLUNAS:
    resultado = df_total.groupby('DT_SNAP').agg(
        Volume_Fila=('DT_SNAP', 'count'),
        Media_Dias=('DIAS_ABERTO', 'mean')
    ).reset_index()
    
    # Renomeia forçadamente para evitar o erro do "KeyError"
    resultado.columns = ['DT_SNAP', 'Volume_Fila', 'Media_Dias']
    
    return resultado, "Sucesso!"
