import pandas as pd
import glob
import os

def limpar_data_excel(valor):
    """Trata datas vindas do Excel, sejam elas objetos de data ou strings."""
    if pd.isna(valor) or str(valor).strip() == "":
        return None
    
    # Se o Excel já enviou como data (objeto datetime)
    if isinstance(valor, (pd.Timestamp, datetime)):
        return valor
        
    try:
        # Se for string (ex: "quinta-feira, 7 de maio de 2026")
        s = str(valor).lower().strip()
        if ',' in s: s = s.split(',')[-1].strip()
        
        # Dicionário para tradução manual caso o Python não esteja em PT-BR
        meses = {
            'janeiro': '01', 'fevereiro': '02', 'março': '03', 'marco': '03',
            'abril': '04', 'maio': '05', 'junho': '06', 'julho': '07',
            'agosto': '08', 'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
        }
        
        partes = s.split()
        if len(partes) >= 3:
            dia = partes[0].zfill(2)
            mes = meses.get(partes[2], '01')
            ano = partes[-1]
            return pd.to_datetime(f"{dia}/{mes}/{ano}", dayfirst=True, errors='coerce')
        
        return pd.to_datetime(s, dayfirst=True, errors='coerce')
    except:
        return None

def obter_dados_historico():
    # 1. Busca por arquivos EXCEL (.xlsx e .xls)
    pastas = ["02.OS_Pendentes", "OS_Pendentes_Historico", "OS Pendentes Historico"]
    arquivos = []
    for p in pastas:
        caminho = os.path.join(os.getcwd(), "planilhas_gets", p)
        # Pega tanto .xls quanto .xlsx
        arquivos.extend(glob.glob(os.path.join(caminho, "*.xls*")))
    
    if not arquivos:
        return pd.DataFrame(), "Nenhum arquivo Excel (.xlsx ou .xls) encontrado nas pastas."

    lista_dfs = []
    colunas_os = ['O.S.', 'N.º O.S.', 'Nº O.S.', 'ORDEM DE SERVIÇO']
    colunas_snap = ['SNAPSHOT_DATE', 'SNAPSHOT_DT']
    colunas_abert = ['ABERTURA', 'DATA ABERTURA', 'DATA DE ABERTURA']

    for arq in arquivos:
        try:
            # Tenta ler o Excel (testando skiprows caso o cabeçalho não esteja na linha 0)
            df_temp = pd.DataFrame()
            for pular in [0, 1, 2, 3, 4, 5]:
                df_teste = pd.read_excel(arq, skiprows=pular)
                df_teste.columns = df_teste.columns.astype(str).str.strip().str.upper()
                
                # Verifica se encontrou as colunas principais
                tem_os = any(c in df_teste.columns for c in colunas_os)
                tem_snap = any(c in df_teste.columns for c in colunas_snap)
                
                if tem_os and tem_snap:
                    df_temp = df_teste
                    break
            
            if not df_temp.empty:
                # Padroniza nomes de colunas
                c_os = next(c for c in colunas_os if c in df_temp.columns)
                c_snap = next(c for c in colunas_snap if c in df_temp.columns)
                c_abert = next((c for c in colunas_abert if c in df_temp.columns), None)
                
                df_limpo = pd.DataFrame()
                df_limpo['OS_ID'] = df_temp[c_os].astype(str)
                df_limpo['DT_SNAP'] = df_temp[c_snap].apply(limpar_data_excel)
                
                if c_abert:
                    df_limpo['DT_ABERTURA'] = df_temp[c_abert].apply(limpar_data_excel)
                else:
                    # Se não houver data de abertura, usa a data do snapshot menos 1 dia (para não dar erro)
                    df_limpo['DT_ABERTURA'] = df_limpo['DT_SNAP'] - pd.Timedelta(days=1)

                df_limpo = df_limpo.dropna(subset=['DT_SNAP', 'DT_ABERTURA'])
                df_limpo['DIAS_ABERTO'] = (df_limpo['DT_SNAP'] - df_limpo['DT_ABERTURA']).dt.days
                
                lista_dfs.append(df_limpo[['DT_SNAP', 'DIAS_ABERTO', 'OS_ID']])
        except Exception as e:
            print(f"Erro ao ler {arq}: {e}")
            continue
            
    if not lista_dfs:
        return pd.DataFrame(), "Planilhas encontradas, mas as colunas 'O.S.' e 'SNAPSHOT_DATE' não foram localizadas dentro delas."
    
    df_total = pd.concat(lista_dfs, ignore_index=True)
    
    # Agrupamento para o gráfico
    df_grafico = df_total.groupby('DT_SNAP').agg(
        Volume_Fila=('OS_ID', 'count'),
        Media_Dias=('DIAS_ABERTO', 'mean')
    ).reset_index().sort_values('DT_SNAP')
    
    return df_grafico, "Sucesso! Dados carregados do Excel."
