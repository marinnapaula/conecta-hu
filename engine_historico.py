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
            # 1. Identificar data e ler arquivo
            match = re.search(r'RelOSsPendentes(\d{4})(\d{2})(\d{2})', os.path.basename(arq))
            if not match: continue
            data_ref = pd.Timestamp(f"{match.group(1)}-{match.group(2)}-{match.group(3)}")

            # 2. Leitura inteligente (pula linhas até achar o cabeçalho "O.S.")
            # Lê primeiro sem header para achar a linha correta
            df_preview = pd.read_excel(arq, header=None, engine='openpyxl' if arq.endswith('x') else 'xlrd') if not arq.endswith('.csv') else pd.read_csv(arq, header=None, sep=None, engine='python')
            header_idx = df_preview[df_preview.apply(lambda row: row.astype(str).str.contains('O.S.', case=False).any(), axis=1)].index[0]
            
            # Lê de verdade
            df = pd.read_excel(arq, skiprows=header_idx, engine='openpyxl' if arq.endswith('x') else 'xlrd') if not arq.endswith('.csv') else pd.read_csv(arq, skiprows=header_idx, sep=None, engine='python')
            df.columns = df.columns.str.strip().str.upper()

            # 3. Processamento
            c_abert = next((c for c in df.columns if 'ABERTURA' in c), None)
            c_os = next((c for c in df.columns if 'O.S.' in c or 'OS' in c), None)
            
            if c_os and c_abert:
                df['DT_ABERTURA'] = pd.to_datetime(df[c_abert], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['DT_ABERTURA'])
                
                df['DT_SNAP'] = data_ref
                df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
                
                # Faixa de dias
                df['FAIXA_DIAS'] = pd.cut(df['DIAS_ABERTO'], bins=[-1, 5, 15, 30, 60, 99999], 
                                          labels=["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias", "Mais de 60 dias"])
                
                lista_dfs.append(df[['DT_SNAP', 'DIAS_ABERTO', 'FAIXA_DIAS', c_os]])
        except: continue
            
    if not lista_dfs: return pd.DataFrame(), "Sem dados"
    
    return pd.concat(lista_dfs, ignore_index=True), "Sucesso"
