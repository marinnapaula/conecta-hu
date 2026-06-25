import pandas as pd
import glob
import os
import re

def limpar_data_extenso(valor):
    """Remove nomes de dias da semana e converte formato pt-br."""
    if pd.isna(valor) or str(valor).strip() == "": return None
    
    # 1. Transformar tudo em minúsculo e tirar espaços extras
    s = str(valor).lower().strip()
    
    # 2. Lista de dias da semana para remover totalmente
    dias = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo', 
            'segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sabado']
    
    # Remove qualquer menção de dia da semana
    for dia in dias:
        s = s.replace(dia, '').replace(',', '').strip()
    
    # 3. Tenta converter (agora a string está limpa, ex: "7 de maio de 2026")
    try:
        return pd.to_datetime(s, dayfirst=True, errors='coerce')
    except: 
        return None

def obter_dados_historico():
    pastas = ["02.OS_Pendentes", "OS_Pendentes_Historico", "OS Pendentes Historico"]
    arquivos = []
    for p in pastas:
        caminho = os.path.join(os.getcwd(), "planilhas_gets", p)
        if os.path.exists(caminho):
            arquivos.extend(glob.glob(os.path.join(caminho, "*.*")))
    
    if not arquivos: return pd.DataFrame(), "Nenhum arquivo encontrado."

    lista_dfs = []
    
    for arq in arquivos:
        if not (arq.lower().endswith(('.csv', '.xlsx', '.xls'))): continue
        try:
            # Identifica formato e lê
            if arq.lower().endswith('.csv'):
                df = pd.read_csv(arq, sep=',', encoding='utf-8', dtype=str, low_memory=False)
                if len(df.columns) < 3: 
                    df = pd.read_csv(arq, sep=';', encoding='latin1', dtype=str, low_memory=False)
            else:
                df = pd.read_excel(arq, dtype=str)
                
            df.columns = df.columns.str.strip().str.upper()
            
            c_os = next((c for c in ['O.S.', 'OS', 'N.º O.S.'] if c in df.columns), None)
            c_abert = next((c for c in ['ABERTURA', 'DATA ABERTURA'] if c in df.columns), None)
            
            if c_os and c_abert:
                # Extração de Data do Nome do Arquivo (8 dígitos)
                match = re.search(r'(\d{4})(\d{2})(\d{2})', os.path.basename(arq))
                if match:
                    ano, mes, dia = match.groups()
                    dt_snap = pd.Timestamp(f"{ano}-{mes}-{dia}")
                else:
                    dt_snap = pd.to_datetime(os.path.getmtime(arq), unit='s').normalize()
                
                df['DT_SNAP'] = dt_snap
                df['DT_ABERTURA'] = df[c_abert].apply(limpar_data_extenso)
                
                # DEBUG: Isso vai printar no terminal do Streamlit para você ver o que ele está lendo
                print(f"Lendo {os.path.basename(arq)} -> Data Snap: {dt_snap}")
                
                df = df.dropna(subset=['DT_SNAP', 'DT_ABERTURA'])
                df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
                
                lista_dfs.append(df[['DT_SNAP', 'DIAS_ABERTO', c_os]])
                
        except Exception as e:
            continue
            
    if not lista_dfs: return pd.DataFrame(), "Arquivos lidos, mas estrutura não compatível."
    
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    # Agrupa por Data
    resultado = df_final.groupby('DT_SNAP').agg(
        Volume_Fila=('O.S.', 'count') if 'O.S.' in df_final.columns else ('OS_ID', 'count'),
        Media_Dias=('DIAS_ABERTO', 'mean')
    ).reset_index().sort_values('DT_SNAP')
    
    return resultado, "Sucesso!"
