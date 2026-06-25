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

def limpar_data_extenso(valor):
    if pd.isna(valor) or str(valor).strip() == "": return None
    try:
        data_limpa = str(valor).split(',')[-1].strip()
        return pd.to_datetime(data_limpa, dayfirst=True, errors='coerce')
    except: return None

def obter_dados_historico():
    caminho_pasta = os.path.join(os.getcwd(), "planilhas_gets", "02.OS_Pendentes")
    arquivos = glob.glob(os.path.join(caminho_pasta, "RelOSsPendentes*.*"))
    
    lista_dfs = []
    log_leitura = []
    
    for arq in arquivos:
        if not arq.lower().endswith(('.xlsx', '.xls', '.csv')): continue
        
        nome_arq = os.path.basename(arq)
        data_ref = extrair_data_nome(nome_arq)
        
        if data_ref is None:
            log_leitura.append(f"❌ {nome_arq} -> Data não encontrada no nome.")
            continue

        try:
            # Tenta ler (usando openpyxl para xlsx)
            if arq.lower().endswith('.csv'):
                df = pd.read_csv(arq, sep=None, engine='python', dtype=str, encoding='latin1')
            else:
                df = pd.read_excel(arq, dtype=str, engine='openpyxl')
                
            df.columns = df.columns.str.strip().str.upper()
            
            # BUSCA AGRESSIVA: Procura qualquer coluna que contenha OS ou ABERTURA
            c_os = next((c for c in df.columns if 'OS' in c), None)
            c_abert = next((c for c in df.columns if 'ABERTURA' in c), None)
            
            if c_os and c_abert:
                # Converte abertura
                df['DT_ABERTURA'] = df[c_abert].apply(limpar_data_extenso)
                df = df.dropna(subset=['DT_ABERTURA'])
                
                df['DT_SNAP'] = data_ref
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
        Volume_Fila=('OS_ID', 'count') if 'OS_ID' in df_final.columns else (df_final.columns[2], 'count'),
        Media_Dias=('DIAS_ABERTO', 'mean')
    ).reset_index().sort_values('DT_SNAP')
    
    return resultado, "\n".join(log_leitura)
