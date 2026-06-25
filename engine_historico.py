import pandas as pd
import glob
import os

def limpar_data_extenso(valor):
    """Remove o dia da semana e converte formato pt-br."""
    if pd.isna(valor) or str(valor).strip() == "":
        return None
    try:
        # Se contiver vírgula, pega só a parte após a vírgula (ex: "7 de maio de 2026")
        data_limpa = str(valor).split(',')[-1].strip()
        # Converte para datetime reconhecendo o formato brasileiro
        return pd.to_datetime(data_limpa, dayfirst=True, errors='coerce')
    except:
        return None

def obter_dados_historico():
    # Caminhos específicos dos arquivos de histórico
    pastas = ["02.OS_Pendentes", "OS_Pendentes_Historico", "OS Pendentes Historico"]
    arquivos = []
    for p in pastas:
        caminho = os.path.join(os.getcwd(), "planilhas_gets", p)
        arquivos.extend(glob.glob(os.path.join(caminho, "*.csv")))
    
    lista_dfs = []
    
    for arq in arquivos:
        try:
            # Lê o CSV
            df = pd.read_csv(arq, sep=',', encoding='utf-8', low_memory=False)
            df.columns = df.columns.str.strip().str.upper()
            
            if 'O.S.' in df.columns and 'SNAPSHOT_DATE' in df.columns and 'ABERTURA' in df.columns:
                # Limpeza de datas
                df['DT_SNAP_REF'] = df['SNAPSHOT_DATE'].apply(limpar_data_extenso)
                df['ABERTURA_CLEAN'] = df['ABERTURA'].apply(limpar_data_extenso)
                
                # Filtra apenas linhas com datas válidas
                df = df.dropna(subset=['DT_SNAP_REF', 'ABERTURA_CLEAN'])
                
                # Calcula dias em aberto
                df['DIAS_ABERTO'] = (df['DT_SNAP_REF'] - df['ABERTURA_CLEAN']).dt.days
                
                lista_dfs.append(df[['DT_SNAP_REF', 'DIAS_ABERTO', 'O.S.']])
        except Exception as e:
            print(f"Erro ao ler arquivo {arq}: {e}")
            continue
            
    if not lista_dfs:
        return pd.DataFrame()
        
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    # Agrupa pelo dia do snapshot para o gráfico
    resultado = df_final.groupby('DT_SNAP_REF').agg(
        Volume_Fila=('O.S.', 'count'),
        Media_Dias=('DIAS_ABERTO', 'mean')
    ).reset_index()
    
    return resultado.sort_values('DT_SNAP_REF')
