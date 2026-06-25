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
            # Identifica a data pelo nome (padrão RelOSsPendentesYYYYMMDD...)
            match = re.search(r'RelOSsPendentes(\d{4})(\d{2})(\d{2})', os.path.basename(arq))
            if not match: continue
            data_ref = pd.Timestamp(f"{match.group(1)}-{match.group(2)}-{match.group(3)}")

            # Leitura
            df = pd.read_excel(arq, dtype=str) if not arq.endswith('.csv') else pd.read_csv(arq, sep=None, engine='python', dtype=str)
            df.columns = df.columns.str.strip().str.upper()
            
            c_os = next((c for c in df.columns if 'O.S.' in c or 'OS' in c), None)
            c_abert = next((c for c in df.columns if 'ABERTURA' in c), None)
            
            if c_os and c_abert:
                df['DT_ABERTURA'] = pd.to_datetime(df[c_abert].astype(str).str.split(',').str[-1], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['DT_ABERTURA'])
                
                # Calcula dias e faixa
                dias = (data_ref - df['DT_ABERTURA']).dt.days
                df['FAIXA_DIAS'] = pd.cut(dias, bins=[-1, 5, 15, 30, 60, 99999], 
                                          labels=["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias", "Mais de 60 dias"])
                
                df['DT_SNAP'] = data_ref
                lista_dfs.append(df[['DT_SNAP', 'FAIXA_DIAS', c_os]])
        except: continue
            
    if not lista_dfs: return pd.DataFrame(), "Sem dados"
    
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    # CRIA A GRADE COMPLETA (Preenche buracos com zero)
    idx = pd.MultiIndex.from_product([df_final['DT_SNAP'].unique(), df_final['FAIXA_DIAS'].unique()], names=['DT_SNAP', 'FAIXA_DIAS'])
    df_agrupado = df_final.groupby(['DT_SNAP', 'FAIXA_DIAS']).size().reindex(idx, fill_value=0).reset_index(name='Volume')
    
    return df_agrupado.sort_values('DT_SNAP'), "Sucesso!"
