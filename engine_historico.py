import pandas as pd
import glob
import os
import re

def extrair_data_nome(nome_arquivo):
    """Extrai estritamente o padrão YYYYMMDD do nome do arquivo."""
    match = re.search(r'RelOSsPendentes(\d{4})(\d{2})(\d{2})', nome_arquivo)
    if match:
        ano, mes, dia = match.groups()
        return pd.Timestamp(f"{ano}-{mes}-{dia}")
    return None

def obter_dados_historico():
    # Caminho exato dos arquivos
    caminho_pasta = os.path.join(os.getcwd(), "planilhas_gets", "02.OS_Pendentes")
    arquivos = glob.glob(os.path.join(caminho_pasta, "RelOSsPendentes*.*"))
    
    lista_dfs = []
    log_leitura = []
    
    for arq in arquivos:
        # Pula arquivos que não sejam Excel ou CSV
        if not arq.lower().endswith(('.xlsx', '.xls', '.csv')): continue
        
        # 1. Tenta extrair a data pelo NOME
        data_ref = extrair_data_nome(os.path.basename(arq))
        
        # SE NÃO TIVER DATA NO NOME, PULA O ARQUIVO (NÃO USA DATA DE HOJE)
        if data_ref is None:
            log_leitura.append(f"❌ {os.path.basename(arq)} -> Ignorado (Data não encontrada no nome)")
            continue

        try:
            # 2. Leitura
            if arq.lower().endswith('.csv'):
                df = pd.read_csv(arq, sep=None, engine='python', dtype=str, encoding='latin1')
            else:
                # Tenta ler xlsx/xls (se der erro de xlrd, o try/except captura)
                try:
                    df = pd.read_excel(arq, dtype=str)
                except Exception as e:
                    log_leitura.append(f"❌ {os.path.basename(arq)} -> Erro ao ler Excel: {e}")
                    continue
                
            df.columns = df.columns.str.strip().str.upper()
            
            c_os = next((c for c in ['O.S.', 'OS', 'N.º O.S.'] if c in df.columns), None)
            c_abert = next((c for c in ['ABERTURA', 'DATA ABERTURA'] if c in df.columns), None)
            
            if c_os and c_abert:
                # Converte abertura (limpeza simples)
                df['DT_ABERTURA'] = pd.to_datetime(df[c_abert].astype(str).str.split(',').str[-1], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['DT_ABERTURA'])
                
                df['DT_SNAP'] = data_ref
                df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
                
                lista_dfs.append(df[['DT_SNAP', 'DIAS_ABERTO', c_os]])
                log_leitura.append(f"✅ {os.path.basename(arq)} -> Processado: {data_ref.date()}")
            else:
                log_leitura.append(f"❌ {os.path.basename(arq)} -> Colunas não encontradas.")
                
        except Exception as e:
            log_leitura.append(f"❌ {os.path.basename(arq)} -> Erro inesperado: {e}")
            
    if not lista_dfs: 
        return pd.DataFrame(), "\n".join(log_leitura)
    
    df_final = pd.concat(lista_dfs, ignore_index=True)
    resultado = df_final.groupby('DT_SNAP').agg(
        Volume_Fila=('O.S.', 'count') if 'O.S.' in df_final.columns else ('OS_ID', 'count'),
        Media_Dias=('DIAS_ABERTO', 'mean')
    ).reset_index().sort_values('DT_SNAP')
    
    return resultado, "\n".join(log_leitura)
