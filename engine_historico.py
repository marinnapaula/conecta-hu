import pandas as pd
import glob
import os
import re

def obter_dados_historico():
    caminho_pasta = os.path.join(os.getcwd(), "planilhas_gets", "02.OS_Pendentes")
    arquivos = glob.glob(os.path.join(caminho_pasta, "RelOSsPendentes*.*"))
    
    lista_dfs = []
    log = []

    for arq in arquivos:
        if not arq.lower().endswith(('.xlsx', '.xls', '.csv')): continue
        
        nome = os.path.basename(arq)
        data_ref = re.search(r'RelOSsPendentes(\d{4})(\d{2})(\d{2})', nome)
        if not data_ref:
            log.append(f"❌ {nome}: Data não achada no nome.")
            continue
        dt_snap = pd.Timestamp(f"{data_ref.group(1)}-{data_ref.group(2)}-{data_ref.group(3)}")

        try:
            # Tenta ler o arquivo
            if arq.lower().endswith('.csv'):
                df = pd.read_csv(arq, sep=None, engine='python', header=None, dtype=str)
            else:
                # Lê o Excel sem cabeçalho para caçar onde ele está
                df = pd.read_excel(arq, header=None, dtype=str, engine='openpyxl' if arq.endswith('x') else 'xlrd')

            # 1. Encontra a linha do cabeçalho (procura onde "O.S." aparece)
            header_idx = -1
            for i, row in df.iterrows():
                row_str = [str(x).strip().upper() for x in row]
                if any('O.S.' in s for s in row_str) and any('ABERTURA' in s for s in row_str):
                    header_idx = i
                    break
            
            if header_idx == -1:
                log.append(f"❌ {nome}: Cabeçalho não encontrado.")
                continue

            # 2. Refaz a leitura a partir da linha do cabeçalho encontrada
            if arq.lower().endswith('.csv'):
                df = pd.read_csv(arq, skiprows=header_idx, sep=None, engine='python', dtype=str)
            else:
                df = pd.read_excel(arq, skiprows=header_idx, dtype=str, engine='openpyxl' if arq.endswith('x') else 'xlrd')

            df.columns = df.columns.str.strip().str.upper()

            # 3. Extrai dados
            c_os = next((c for c in df.columns if 'O.S.' in c), None)
            c_abert = next((c for c in df.columns if 'ABERTURA' in c), None)

            df['DT_ABERTURA'] = pd.to_datetime(df[c_abert].astype(str).str.split(',').str[-1], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['DT_ABERTURA'])
            
            df['DT_SNAP'] = dt_snap
            df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
            
            lista_dfs.append(df[['DT_SNAP', 'DIAS_ABERTO', c_os]])
            log.append(f"✅ {nome}: OK")

        except Exception as e:
            log.append(f"❌ {nome}: {str(e)}")
            
    if not lista_dfs: return pd.DataFrame(), "\n".join(log)
    
    df_final = pd.concat(lista_dfs, ignore_index=True)
    res = df_final.groupby('DT_SNAP').agg(Volume_Fila=('DT_SNAP', 'count'), Media_Dias=('DIAS_ABERTO', 'mean')).reset_index()
    return res, "\n".join(log)
