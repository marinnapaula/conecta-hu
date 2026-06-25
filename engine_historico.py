import pandas as pd
import glob
import os
import re

def extrair_data_nome(nome_arquivo):
    match = re.search(r'RelOSsPendentes(\d{4})(\d{2})(\d{2})', nome_arquivo)
    if match:
        ano, mes, dia = match.groups()
        return pd.Timestamp(f"{ano}-{mes}-{dia}")
    return None

def obter_dados_historico():
    caminho_pasta = os.path.join(os.getcwd(), "planilhas_gets", "02.OS_Pendentes")
    arquivos = glob.glob(os.path.join(caminho_pasta, "RelOSsPendentes*.*"))
    
    lista_dfs = []
    log_leitura = []
    
    for arq in arquivos:
        if not arq.lower().endswith(('.xlsx', '.xls')): continue
        
        nome_arq = os.path.basename(arq)
        data_ref = extrair_data_nome(nome_arq)
        
        try:
            # Escolhe o motor correto: xls precisa de xlrd, xlsx precisa de openpyxl
            engine = 'xlrd' if arq.lower().endswith('.xls') else 'openpyxl'
            
            # header=5 pula as 5 linhas vazias e lê a linha 6 como cabeçalho
            df = pd.read_excel(arq, header=5, engine=engine)
            df.columns = df.columns.str.strip().str.upper()
            
            # Procura qualquer coluna que contenha OS ou ABERTURA
            c_os = next((c for c in df.columns if 'O.S.' in c or 'OS' in c), None)
            c_abert = next((c for c in df.columns if 'ABERTURA' in c), None)
            
            if c_os and c_abert:
                df['DT_ABERTURA'] = pd.to_datetime(df[c_abert], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['DT_ABERTURA'])
                
                df['DT_SNAP'] = data_ref if data_ref else pd.to_datetime(os.path.getmtime(arq), unit='s')
                df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
                
                lista_dfs.append(df[['DT_SNAP', 'DIAS_ABERTO', c_os]])
                log_leitura.append(f"✅ {nome_arq} -> Lendo colunas: '{c_os}' e '{c_abert}'")
            else:
                log_leitura.append(f"❌ {nome_arq} -> Colunas não achadas. Achou: {list(df.columns)}")
                
        except Exception as e:
            log_leitura.append(f"❌ {nome_arq} -> Erro: {str(e)}")
            
    if not lista_dfs: return pd.DataFrame(), "\n".join(log_leitura)
    
    df_final = pd.concat(lista_dfs, ignore_index=True)
    resultado = df_final.groupby('DT_SNAP').agg(
        Volume_Fila=('O.S.', 'count') if 'O.S.' in df_final.columns else (df_final.columns[2], 'count'),
        Media_Dias=('DIAS_ABERTO', 'mean')
    ).reset_index().sort_values('DT_SNAP')
    
    return resultado, "\n".join(log_leitura)
