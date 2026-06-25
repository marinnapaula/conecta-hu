import pandas as pd
import glob
import os
import datetime

def limpar_data_extenso(valor):
    """Remove o dia da semana e converte formato pt-br."""
    if pd.isna(valor) or str(valor).strip() == "": return None
    try:
        # Pega a parte após a vírgula (ex: "7 de maio de 2026")
        data_limpa = str(valor).split(',')[-1].strip()
        return pd.to_datetime(data_limpa, dayfirst=True, errors='coerce')
    except: return None

def obter_dados_historico():
    pastas = ["02.OS_Pendentes", "OS_Pendentes_Historico", "OS Pendentes Historico"]
    arquivos = []
    for p in pastas:
        caminho = os.path.join(os.getcwd(), "planilhas_gets", p)
        # Busca .csv e .xlsx
        arquivos.extend(glob.glob(os.path.join(caminho, "*.*")))
    
    if not arquivos: return pd.DataFrame(), "Nenhum arquivo encontrado."

    lista_dfs = []
    
    for arq in arquivos:
        if not (arq.endswith('.csv') or arq.endswith('.xlsx') or arq.endswith('.xls')):
            continue
            
        try:
            # Tenta identificar o formato
            if arq.endswith('.csv'):
                df = pd.read_csv(arq, sep=',', encoding='utf-8', dtype=str, low_memory=False)
                if len(df.columns) < 3: 
                    df = pd.read_csv(arq, sep=';', encoding='latin1', dtype=str, low_memory=False)
            else:
                df = pd.read_excel(arq, dtype=str)
                
            df.columns = df.columns.str.strip().str.upper()
            
            # Valida se temos o básico (O.S. e Abertura)
            c_os = next((c for c in ['O.S.', 'OS', 'N.º O.S.'] if c in df.columns), None)
            c_abert = next((c for c in ['ABERTURA', 'DATA ABERTURA'] if c in df.columns), None)
            
            if c_os and c_abert:
                # 1. Pega a data de modificação do arquivo no Windows
                mod_time = os.path.getmtime(arq)
                data_arquivo = pd.to_datetime(mod_time, unit='s')
                
                # 2. Cria a coluna de data internamente (Snapshot)
                df['DT_SNAP'] = data_arquivo
                df['DT_ABERTURA'] = df[c_abert].apply(limpar_data_extenso)
                
                df = df.dropna(subset=['DT_SNAP', 'DT_ABERTURA'])
                df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
                
                lista_dfs.append(df[['DT_SNAP', 'DIAS_ABERTO', c_os]])
        except Exception as e:
            print(f"Erro no arquivo {arq}: {e}")
            continue
            
    if not lista_dfs: return pd.DataFrame(), "Arquivos lidos, mas estrutura não compatível."
    
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    # Agrupa para o gráfico
    resultado = df_final.groupby('DT_SNAP').agg(
        Volume_Fila=('O.S.', 'count') if 'O.S.' in df_final.columns else ('OS_ID', 'count'),
        Media_Dias=('DIAS_ABERTO', 'mean')
    ).reset_index().sort_values('DT_SNAP')
    
    return resultado, "Sucesso! Dados processados com data de modificação do arquivo."
