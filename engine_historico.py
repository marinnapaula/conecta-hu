import pandas as pd
import glob
import os
import re

def extrair_data_do_nome(nome_arquivo):
    """
    Procura o padrão 'RelOSsPendentes' seguido de 8 dígitos (Ano, Mes, Dia).
    Ex: RelOSsPendentes20260624... -> 2026-06-24
    """
    match = re.search(r'RelOSsPendentes(\d{4})(\d{2})(\d{2})', nome_arquivo)
    if match:
        ano, mes, dia = match.groups()
        return pd.Timestamp(f"{ano}-{mes}-{dia}")
    return None

def obter_dados_historico():
    # Pasta onde estão os arquivos que você listou
    caminho_pasta = os.path.join(os.getcwd(), "planilhas_gets", "02.OS_Pendentes")
    arquivos = glob.glob(os.path.join(caminho_pasta, "RelOSsPendentes*.*"))
    
    if not arquivos: 
        return pd.DataFrame(), f"Nenhum arquivo encontrado em {caminho_pasta}"

    lista_dfs = []
    
    # Lista de log para você ver no teste o que ele está lendo
    log_leitura = []
    
    for arq in arquivos:
        nome_arq = os.path.basename(arq)
        try:
            # 1. Pega a data pelo nome do arquivo
            data_ref = extrair_data_do_nome(nome_arq)
            
            if data_ref:
                # 2. Lê o arquivo
                if arq.lower().endswith('.csv'):
                    df = pd.read_csv(arq, sep=None, engine='python', dtype=str, encoding='latin1')
                else:
                    df = pd.read_excel(arq, dtype=str)
                
                df.columns = df.columns.str.strip().str.upper()
                
                # Procura colunas de O.S. e Abertura
                c_os = next((c for c in ['O.S.', 'OS', 'N.º O.S.', 'Nº O.S.'] if c in df.columns), None)
                c_abert = next((c for c in ['ABERTURA', 'DATA ABERTURA'] if c in df.columns), None)
                
                if c_os and c_abert:
                    # Converte data abertura com limpeza
                    df['DT_ABERTURA'] = pd.to_datetime(df[c_abert].astype(str).str.split(',').str[-1], dayfirst=True, errors='coerce')
                    df = df.dropna(subset=['DT_ABERTURA'])
                    
                    df['DT_SNAP'] = data_ref
                    df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
                    
                    lista_dfs.append(df[['DT_SNAP', 'DIAS_ABERTO', c_os]])
                    log_leitura.append(f"✅ {nome_arq} -> Data: {data_ref.date()}")
            else:
                log_leitura.append(f"⚠️ {nome_arq} -> Data não identificada no nome.")
                
        except Exception as e:
            log_leitura.append(f"❌ {nome_arq} -> Erro: {e}")
            
    if not lista_dfs: 
        return pd.DataFrame(), "\n".join(log_leitura)
    
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    resultado = df_final.groupby('DT_SNAP').agg(
        Volume_Fila=('O.S.', 'count'),
        Media_Dias=('DIAS_ABERTO', 'mean')
    ).reset_index().sort_values('DT_SNAP')
    
    return resultado, "\n".join(log_leitura)
