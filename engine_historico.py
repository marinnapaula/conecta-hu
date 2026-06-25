import pandas as pd
import glob
import os
import re

def extrair_data_do_nome(nome_arquivo):
    match = re.search(r'RelOSsPendentes(\d{4})(\d{2})(\d{2})', nome_arquivo)
    if match:
        ano, mes, dia = match.groups()
        return pd.Timestamp(f"{ano}-{mes}-{dia}")
    return None

def categorizar_faixa(dias):
    """Cria as categorias de faixa de dias."""
    if pd.isna(dias): return "Indefinido"
    if dias <= 5: return "0 a 5 dias"
    if dias <= 15: return "6 a 15 dias"
    if dias <= 30: return "16 a 30 dias"
    if dias <= 60: return "31 a 60 dias"
    return "Mais de 60 dias"

def obter_dados_historico():
    caminho_pasta = os.path.join(os.getcwd(), "planilhas_gets", "02.OS_Pendentes")
    arquivos = glob.glob(os.path.join(caminho_pasta, "RelOSsPendentes*.*"))
    
    lista_dfs = []
    
    for arq in arquivos:
        if not arq.lower().endswith(('.xlsx', '.xls', '.csv')): continue
        
        try:
            # Leitura segura convertendo nomes de colunas para string antes de filtrar
            if arq.lower().endswith('.csv'):
                df = pd.read_csv(arq, sep=None, engine='python', dtype=str, encoding='latin1')
            else:
                df = pd.read_excel(arq, dtype=str)
                
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Procura colunas com segurança (forçando conversão para string)
            c_os = next((c for c in df.columns if 'OS' in c), None)
            c_abert = next((c for c in df.columns if 'ABERTURA' in c), None)
            
            if c_os and c_abert:
                # Converte data abertura com limpeza
                df['DT_ABERTURA'] = pd.to_datetime(df[c_abert].astype(str).str.split(',').str[-1], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['DT_ABERTURA'])
                
                # Aplica data do Snapshot
                df['DT_SNAP'] = extrair_data_do_nome(os.path.basename(arq))
                df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
                
                # CRIA A FAIXA DE DIAS AQUI
                df['FAIXA_DIAS'] = df['DIAS_ABERTO'].apply(categorizar_faixa)
                
                lista_dfs.append(df[['DT_SNAP', 'FAIXA_DIAS', 'DIAS_ABERTO', c_os]])
        except Exception:
            continue
            
    if not lista_dfs: return pd.DataFrame(), "Sem dados"
    
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    # Agrupa por Data E por Faixa para o gráfico de áreas empilhadas
    resultado = df_final.groupby(['DT_SNAP', 'FAIXA_DIAS']).agg(
        Volume=('FAIXA_DIAS', 'count'),
        Media_Dias=('DIAS_ABERTO', 'mean')
    ).reset_index().sort_values('DT_SNAP')
    
    return resultado, "Sucesso!"
