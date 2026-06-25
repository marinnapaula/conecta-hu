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
            match = re.search(r'RelOSsPendentes(\d{4})(\d{2})(\d{2})', os.path.basename(arq))
            if not match: continue
            data_ref = pd.Timestamp(f"{match.group(1)}-{match.group(2)}-{match.group(3)}")
            
            # Leitura
            if arq.lower().endswith('.csv'):
                df = pd.read_csv(arq, sep=None, engine='python', header=None, dtype=str)
            else:
                df = pd.read_excel(arq, header=None, dtype=str, engine='openpyxl' if arq.endswith('x') else 'xlrd')
            
            # Achar cabeçalho
            idx = df[df.apply(lambda row: row.astype(str).str.contains('O.S.', case=False).any(), axis=1)].index[0]
            df = df.iloc[idx:].reset_index(drop=True)
            df.columns = df.iloc[0].str.strip().str.upper()
            df = df.iloc[1:]

            c_os = next((c for c in df.columns if 'O.S.' in c), None)
            c_abert = next((c for c in df.columns if 'ABERTURA' in c), None)

            if c_os and c_abert:
                df['DT_ABERTURA'] = pd.to_datetime(df[c_abert].str.split(',').str[-1], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['DT_ABERTURA'])
                df['DT_SNAP'] = data_ref
                df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
                # Criar faixa aqui no motor
                df['FAIXA_DIAS'] = pd.cut(df['DIAS_ABERTO'], bins=[-1, 5, 15, 30, 60, 99999], 
                                          labels=["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias", "Mais de 60 dias"])
                lista_dfs.append(df[['DT_SNAP', 'FAIXA_DIAS', 'DIAS_ABERTO', c_os]])
        except: continue
            
    return pd.concat(lista_dfs, ignore_index=True) if lista_dfs else pd.DataFrame()
