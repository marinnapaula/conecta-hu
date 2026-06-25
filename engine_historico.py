import pandas as pd
import glob
import os
import re
from datetime import datetime

def extrair_data_nome(nome_arquivo):
    """Extrai a data no formato YYYYMMDD do nome do arquivo."""
    # Procura por 8 dígitos seguidos (ex: 20251201...)
    match = re.search(r'(\d{4})(\d{2})(\d{2})', nome_arquivo)
    if match:
        ano, mes, dia = match.groups()
        return pd.Timestamp(f"{ano}-{mes}-{dia}")
    return None

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
        if os.path.exists(caminho):
            # Busca .csv e .xlsx e .xls
            arquivos.extend(glob.glob(os.path.join(caminho, "*.*")))
    
    if not arquivos: return pd.DataFrame(), "Nenhum arquivo encontrado."

    lista_dfs = []
    
    for arq in arquivos:
        if not (arq.lower().endswith(('.csv', '.xlsx', '.xls'))): continue
            
        try:
            # 1. Tenta extrair data do NOME (o mais confiável agora)
            data_ref = extrair_data_nome(os.path.basename(arq))
            
            # Se não achar no nome, usa o sistema (fallback)
            if data_ref is None:
                data_ref = pd.to_datetime(os.path.getmtime(arq), unit='s').normalize()

            # 2. Leitura do arquivo
            if arq.lower().endswith('.csv'):
                df = pd.read_csv(arq, sep=',', encoding='utf-8', dtype=str, low_memory=False)
                if len(df.columns) < 3: 
                    df = pd.read_csv(arq, sep=';', encoding='latin1', dtype=str, low_memory=False)
            else:
                df = pd.read_excel(arq, dtype=str)
                
            df.columns = df.columns.str.strip().str.upper()
            
            # Padroniza nomes de colunas de O.S. e Abertura
            c_os = next((c for c in ['O.S.', 'OS', 'N.º O.S.', 'Nº O.S.'] if c in df.columns), None)
            c_abert = next((c for c in ['ABERTURA', 'DATA ABERTURA', 'DATA DE ABERTURA'] if c in df.columns), None)
            
            if c_os and c_abert:
                # Usa a data extraída do nome do arquivo como snapshot
                df['DT_SNAP'] = data_ref
                df['DT_ABERTURA'] = df[c_abert].apply(limpar_data_extenso)
                
                df = df.dropna(subset=['DT_SNAP', 'DT_ABERTURA'])
                df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
                
                # Armazena apenas o necessário para o gráfico
                lista_dfs.append(df[['DT_SNAP', 'DIAS_ABERTO', c_os]])
                
        except Exception as e:
            continue
            
    if not lista_dfs: return pd.DataFrame(), "Arquivos lidos, mas estrutura não compatível."
    
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    # Agrupa para o gráfico
    resultado = df_final.groupby('DT_SNAP').agg(
        Volume_Fila=('O.S.', 'count'),
        Media_Dias=('DIAS_ABERTO', 'mean')
    ).reset_index().sort_values('DT_SNAP')
    
    return resultado, f"Sucesso! Processados {len(lista_dfs)} arquivos. Pontos no gráfico: {len(resultado)}"
