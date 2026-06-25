import pandas as pd
import glob
import os

def traduzir_meses_pt(data_str):
    """Converte '7 de maio de 2026' em '07/05/2026'."""
    if pd.isna(data_str): return None
    meses = {
        'janeiro': '01', 'fevereiro': '02', 'março': '03', 'marco': '03',
        'abril': '04', 'maio': '05', 'junho': '06', 'julho': '07',
        'agosto': '08', 'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
    }
    try:
        s = str(data_str).lower().strip()
        if ',' in s: s = s.split(',')[-1].strip() # Remove "quinta-feira,"
        
        partes = s.split() # ["7", "de", "maio", "de", "2026"]
        if len(partes) >= 3:
            dia = partes[0].zfill(2)
            mes = meses.get(partes[2], '01')
            ano = partes[-1]
            return f"{dia}/{mes}/{ano}"
        return s
    except: return None

def obter_dados_historico():
    # Pastas onde o histórico pode estar
    pastas = ["02.OS_Pendentes", "OS_Pendentes_Historico", "OS Pendentes Historico"]
    arquivos = []
    for p in pastas:
        caminho = os.path.join(os.getcwd(), "planilhas_gets", p)
        arquivos.extend(glob.glob(os.path.join(caminho, "*.csv")))
    
    if not arquivos: return pd.DataFrame(), "Nenhum arquivo .csv encontrado nas pastas."

    lista_dfs = []
    for arq in arquivos:
        try:
            df = pd.read_csv(arq, sep=',', encoding='utf-8', dtype=str)
            df.columns = df.columns.str.strip().str.upper()
            
            if 'O.S.' in df.columns and 'SNAPSHOT_DATE' in df.columns:
                # Tradução e conversão das datas
                df['DT_SNAP'] = pd.to_datetime(df['SNAPSHOT_DATE'].apply(traduzir_meses_pt), dayfirst=True, errors='coerce')
                df['DT_ABERTURA'] = pd.to_datetime(df['ABERTURA'].apply(traduzir_meses_pt), dayfirst=True, errors='coerce')
                
                df = df.dropna(subset=['DT_SNAP', 'DT_ABERTURA'])
                df['DIAS_ABERTO'] = (df['DT_SNAP'] - df['DT_ABERTURA']).dt.days
                
                lista_dfs.append(df[['DT_SNAP', 'DIAS_ABERTO', 'O.S.']])
        except Exception as e:
            continue
            
    if not lista_dfs: return pd.DataFrame(), "Arquivos lidos, mas colunas O.S. ou SNAPSHOT_DATE não encontradas."
    
    df_total = pd.concat(lista_dfs, ignore_index=True)
    # Agrupamento final para o gráfico
    df_grafico = df_total.groupby('DT_SNAP').agg(
        Volume_Fila=('O.S.', 'count'),
        Media_Dias=('DIAS_ABERTO', 'mean')
    ).reset_index().sort_values('DT_SNAP')
    
    return df_grafico, "Sucesso!"
