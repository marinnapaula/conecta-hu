import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime

# =====================================================================
# 1. FUNÇÃO AUXILIAR SUPREMA (LEITURA BLINDADA GETS)
# =====================================================================
def get_arquivos(pasta_alvo):
    """Pega todos os formatos possíveis de planilhas na pasta."""
    return glob.glob(os.path.join(pasta_alvo, "*.xlsx")) + \
           glob.glob(os.path.join(pasta_alvo, "*.xls")) + \
           glob.glob(os.path.join(pasta_alvo, "*.csv"))

def ler_arquivo_gets(caminho_arq, colunas_alvo):
    """Lê o arquivo testando várias linhas de cabeçalho, suportando .xls falso (HTML) e CSVs brasileiros."""
    for skip in [5, 4, 3, 0, 1, 2, 6, 7, 8]:
        try:
            df = pd.DataFrame()
            extensao = caminho_arq.lower()
            
            if extensao.endswith('.xlsx'):
                df = pd.read_excel(caminho_arq, skiprows=skip)
                
            elif extensao.endswith('.xls'):
                try:
                    df = pd.read_excel(caminho_arq, skiprows=skip)
                except:
                    try:
                        dfs = pd.read_html(caminho_arq, skiprows=skip, decimal=',', thousands='.')
                        if dfs: df = dfs[0]
                    except:
                        pass
            else:
                try:
                    df = pd.read_csv(caminho_arq, skiprows=skip, sep=';', encoding='latin1', low_memory=False)
                    if len(df.columns) <= 1: raise ValueError("Separador incorreto")
                except:
                    df = pd.read_csv(caminho_arq, skiprows=skip, sep=',', encoding='utf-8', low_memory=False)

            if not df.empty:
                df.columns = df.columns.astype(str).str.strip().str.upper()
                if any(c in df.columns for c in colunas_alvo):
                    return df
        except:
            continue
            
    return pd.DataFrame()

# =====================================================================
# 2. INGESTÃO DE DADOS E EMPILHAMENTO
# =====================================================================
MAPA_COLUNAS_UNIVERSAL = {
    'N.º O.S.': 'O.S.', 'Nº O.S.': 'O.S.', 'N. O.S.': 'O.S.', 'OS': 'O.S.', 'ORDEM DE SERVIÇO': 'O.S.', 'CHAMADO': 'O.S.', 'NÚMERO DA OS': 'O.S.', 'NÚMERO DA O.S.': 'O.S.',
    'DATA ABERTURA': 'ABERTURA', 'DATA DE ABERTURA': 'ABERTURA', 'CRIADO EM': 'ABERTURA', 'ABERTO EM': 'ABERTURA',
    'DATA ENCERRAMENTO': 'ENCERRAMENTO', 'DATA DE ENCERRAMENTO': 'ENCERRAMENTO', 'FECHAMENTO': 'ENCERRAMENTO', 'DATA CONCLUSÃO': 'ENCERRAMENTO', 'CONCLUÍDO EM': 'ENCERRAMENTO', 'DATA/HORA ENCERRAMENTO': 'ENCERRAMENTO',
    'TIPO MANUTENÇÃO': 'CLASSE', 'TIPO DA O.S.': 'CLASSE', 'TIPO DE MANUTENÇÃO': 'CLASSE',
    'PROGRAMA': 'PROGRAMA MP', 'TIPO DE PREVENTIVA': 'PROGRAMA MP',
    'LOCALIZAÇÃO': 'LOCALIZAÇÃO FÍSICA', 'SETOR': 'LOCALIZAÇÃO FÍSICA',
    'EQUIPAMENTO': 'DESCRIÇÃO', 'TIPO EQUIPAMENTO': 'DESCRIÇÃO', 'NOME DO EQUIPAMENTO': 'DESCRIÇÃO', 
    'EQUIPAMENTO CRÍTICO': 'CRITICO', 'EQUIPAMENTO CRITICO': 'CRITICO'
}
COLUNAS_BUSCA_OS = list(MAPA_COLUNAS_UNIVERSAL.keys()) + ['O.S.', 'CRITICO', 'SNAPSHOT_DATE', 'SNAPSHOT_DT']

def carregar_mais_recente(nome_pasta):
    pasta_alvo = os.path.join(os.getcwd(), "planilhas_gets", nome_pasta)
    arquivos = get_arquivos(pasta_alvo)
    
    if not arquivos: return pd.DataFrame()
    arq_recente = max(arquivos, key=os.path.getmtime)
    
    colunas = ['IDENTIFICADOR', 'ID', 'PATRIMÔNIO'] if "Invent" in nome_pasta else COLUNAS_BUSCA_OS
    df = ler_arquivo_gets(arq_recente, colunas)
    if not df.empty:
        df = df.rename(columns=MAPA_COLUNAS_UNIVERSAL)
        df['REPORT_CREATED_AT'] = pd.to_datetime(os.path.getmtime(arq_recente), unit='s')
    return df

def carregar_os_encerradas():
    pasta_01 = os.path.join(os.getcwd(), "planilhas_gets", "01.OS_Encerradas")
    pasta_05a = os.path.join(os.getcwd(), "planilhas_gets", "05. Atendimento de OS")
    pasta_05b = os.path.join(os.getcwd(), "planilhas_gets", "05.Atendimento_de_OS")
    
    arquivos = get_arquivos(pasta_01) + get_arquivos(pasta_05a) + get_arquivos(pasta_05b)
    arquivos = list(set(arquivos))
    
    if not arquivos: return pd.DataFrame()

    lista_dfs = []
    for arq in arquivos:
        df_temp = ler_arquivo_gets(arq, COLUNAS_BUSCA_OS)
        if not df_temp.empty:
            df_temp = df_temp.rename(columns=MAPA_COLUNAS_UNIVERSAL)
            df_temp['REPORT_CREATED_AT'] = pd.to_datetime(os.path.getmtime(arq), unit='s')
            lista_dfs.append(df_temp)
            
    if not lista_dfs: return pd.DataFrame()
    df_final = pd.concat(lista_dfs, ignore_index=True)

    if 'O.S.' in df_final.columns:
        df_final = df_final.dropna(subset=['O.S.'])
        df_final['OS_KEY'] = df_final['O.S.'].astype(str).str.replace('.0', '', regex=False).str.strip().str.upper()
    else: return pd.DataFrame() 

    for col in ['ABERTURA', 'ENCERRAMENTO']:
        if col in df_final.columns:
            datas_texto = pd.to_datetime(df_final[col], errors='coerce', dayfirst=True)
            numeros = pd.to_numeric(df_final[col], errors='coerce')
            datas_excel = pd.to_datetime(numeros, origin='1899-12-30', unit='D', errors='coerce')
            df_final[col] = datas_texto.fillna(datas_excel)

    if 'ENCERRAMENTO' in df_final.columns:
        df_final = df_final[df_final['ENCERRAMENTO'].dt.year >= 2020]
        df_final = df_final.sort_values(by=['ENCERRAMENTO', 'REPORT_CREATED_AT'], ascending=[False, False])
    else:
        df_final = df_final.sort_values(by='REPORT_CREATED_AT', ascending=False)
        
    df_final = df_final.drop_duplicates(subset=['OS_KEY'], keep='first')
    return df_final

def carregar_todas_atividades(nome_pasta="03.Atividades"):
    pasta_alvo = os.path.join(os.getcwd(), "planilhas_gets", nome_pasta)
    arquivos = get_arquivos(pasta_alvo)
    
    if not arquivos and nome_pasta == "03.Atividades":
        return carregar_todas_atividades("03.Atividades_Recentes")
        
    if not arquivos: return pd.DataFrame()
        
    lista_dfs = []
    colunas_busca_atividades = ['N.º O.S.', 'Nº O.S.', 'N. O.S.', 'O.S.', 'OS', 'ORDEM DE SERVIÇO', 'CHAMADO', 'NÚMERO DA OS']

    for arq in arquivos:
        df_temp = ler_arquivo_gets(arq, colunas_busca_atividades)
        if not df_temp.empty: 
            col_os_local = next((c for c in colunas_busca_atividades if c in df_temp.columns), None)
            if col_os_local: df_temp = df_temp.rename(columns={col_os_local: 'O.S.'})
            lista_dfs.append(df_temp)
            
    if not lista_dfs: return pd.DataFrame()
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    if 'O.S.' in df_final.columns:
        df_final = df_final.dropna(subset=['O.S.'])
        df_final['OS_KEY'] = df_final['O.S.'].astype(str).str.replace('.0', '', regex=False).str.strip().str.upper()
        
    df_final = df_final.drop_duplicates()
    return df_final

def gerar_curva_backlog():
    """MÁQUINA DO TEMPO: Lê a coluna interna SNAPSHOT_DATE de cada linha do histórico para calcular o backlog real."""
    pastas_busca = ["02.OS_Pendentes", "OS_Pendentes_Historico", "OS Pendentes Historico"]
    
    arquivos = []
    for p in pastas_busca:
        pasta_alvo = os.path.join(os.getcwd(), "planilhas_gets", p)
        arquivos.extend(get_arquivos(pasta_alvo))
        
    arquivos = list(set(arquivos))
    if not arquivos: return pd.DataFrame()
    
    lista_dfs = []
    for arq in arquivos:
        df_temp = ler_arquivo_gets(arq, COLUNAS_BUSCA_OS)
        if not df_temp.empty:
            df_temp = df_temp.rename(columns=MAPA_COLUNAS_UNIVERSAL)
            if 'O.S.' in df_temp.columns:
                df_temp = df_temp.dropna(subset=['O.S.']).copy()
                
                # Procura a coluna de snapshot gravada de forma nativa nas linhas pelo ETL
                c_snap = next((c for c in ['SNAPSHOT_DATE', 'SNAPSHOT_DT'] if c in df_temp.columns), None)
                if c_snap:
                    df_temp['DT_SNAP_REF'] = pd.to_datetime(df_temp[c_snap], errors='coerce').dt.normalize()
                else:
                    # Fallback robusto se for um arquivo bruto sem coluna interna
                    df_temp['DT_SNAP_REF'] = pd.to_datetime(os.path.getmtime(arq), unit='s').normalize()
                    
                lista_dfs.append(df_temp[['O.S.', 'ABERTURA', 'CRITICO', 'DT_SNAP_REF']])
                
    if not lista_dfs: return pd.DataFrame()
    df_total = pd.concat(lista_dfs, ignore_index=True)
    df_total = df_total.dropna(subset=['DT_SNAP_REF', 'ABERTURA'])
    
    # Tratamento blindado da coluna Abertura
    datas_texto = pd.to_datetime(df_total['ABERTURA'], errors='coerce', dayfirst=True)
    numeros = pd.to_numeric(df_total['ABERTURA'], errors='coerce')
    datas_excel = pd.to_datetime(numeros, origin='1899-12-30', unit='D', errors='coerce')
    df_total['ABERTURA_CLEAN'] = datas_texto.fillna(datas_excel)
    
    df_total = df_total.dropna(subset=['ABERTURA_CLEAN'])
    
    # Calcula os dias em aberto no exato dia em que o snapshot foi registrado!
    df_total['DIAS_ABERTO_HIST'] = (df_total['DT_SNAP_REF'] - df_total['ABERTURA_CLEAN']).dt.days
    df_total = df_total[df_total['DIAS_ABERTO_HIST'] >= 0]
    
    # Agrupa e reconstrói os pontos diários dos gráficos exatamente como o DAX
    linhas_historico = []
    for data_ref, group in df_total.groupby('DT_SNAP_REF'):
        qtd_os = len(group)
        criticas = len(group[group['CRITICO'].astype(str).str.upper().str.strip() == 'SIM'])
        tm_aberta = group['DIAS_ABERTO_HIST'].mean()
        
        f_0_5 = len(group[group['DIAS_ABERTO_HIST'] <= 5])
        f_6_15 = len(group[(group['DIAS_ABERTO_HIST'] > 5) & (group['DIAS_ABERTO_HIST'] <= 15)])
        f_16_30 = len(group[(group['DIAS_ABERTO_HIST'] > 15) & (group['DIAS_ABERTO_HIST'] <= 30)])
        f_31_60 = len(group[(group['DIAS_ABERTO_HIST'] > 30) & (group['DIAS_ABERTO_HIST'] <= 60)])
        f_60_mais = len(group[group['DIAS_ABERTO_HIST'] > 60])
        
        linhas_historico.append({
            'Data': data_ref, 'Volume Fila': int(qtd_os), 'Críticas': int(criticas),
            'Tempo Médio Aberta': tm_aberta, '0 a 5 dias': f_0_5, '6 a 15 dias': f_6_15,
            '16 a 30 dias': f_16_30, '31 a 60 dias': f_31_60, 'Mais de 60 dias': f_60_mais
        })
        
    if not linhas_historico: return pd.DataFrame()
    return pd.DataFrame(linhas_historico).sort_values('Data')

# =====================================================================
# 3. MOTOR DE TRATAMENTO E INTELIGÊNCIA (INVENTÁRIO)
# =====================================================================
def limpar_dimensao_equipamentos(df_inventario_bruto):
    if df_inventario_bruto.empty: return pd.DataFrame()
    df = df_inventario_bruto.copy()
    
    if 'EQUIP_KEY' not in df.columns:
        col_serie = next((c for c in ['N.º SÉRIE', 'N. SÉRIE', 'Nº SÉRIE', 'SÉRIE'] if c in df.columns), None)
        col_id = next((c for c in ['IDENTIFICADOR', 'ID'] if c in df.columns), None)
        
        def gerar_key(row):
            sn = str(row[col_serie]).strip().upper() if col_serie and pd.notna(row[col_serie]) else ''
            id_val = str(row[col_id]).strip().upper() if col_id and pd.notna(row[col_id]) else ''
            if sn and sn != 'NAN': return f"SN:{sn}"
            if id_val and id_val != 'NAN': return f"ID:{id_val}"
            return None
        df['EQUIP_KEY'] = df.apply(gerar_key, axis=1)

    df = df[df['EQUIP_KEY'].notna() & (df['EQUIP_KEY'].str.strip() != '')]
        
    mapeamento_colunas = {
        "N. SÉRIE": "N.º SÉRIE", "Nº SÉRIE": "N.º SÉRIE", "NUMERO DE SERIE": "N.º SÉRIE", "NÚMERO DE SÉRIE": "N.º SÉRIE",
        "Nº PATRIMÔNIO": "PATRIMÔNIO", "N. PATRIMÔNIO": "PATRIMÔNIO", "BAIXADO?": "BAIXADO", "DESATIVADO?": "DESATIVADO",
        "ID": "IDENTIFICADOR", "DESCRICAO": "DESCRIÇÃO", "TIPO EQUIPAMENTO": "DESCRIÇÃO", "TIPO EQUIP.": "DESCRIÇÃO",
        "LOCALIZACAO FISICA": "LOCALIZAÇÃO FÍSICA", "LOCALIZAÇÃO": "LOCALIZAÇÃO FÍSICA",
        "UNID. SAUDE": "UNID. SAÚDE", "UNIDADE DE SAÚDE": "UNID. SAÚDE", "U.S.": "UNID. SAÚDE", "ULTIMA MP": "ÚLTIMA MP"
    }
    df = df.rename(columns=mapeamento_colunas)
    
    def normalizar_sim_nao(valor):
        if pd.isna(valor): return "NÃO"
        if str(valor).strip().upper() in ["SIM", "S", "YES", "Y", "TRUE", "VERDADEIRO", "1"]: return "SIM"
        return "NÃO"
        
    if 'DESATIVADO' not in df.columns: df['DESATIVADO'] = "NÃO"
    if 'BAIXADO' not in df.columns: df['BAIXADO'] = "NÃO"
        
    df['DESATIVADO'] = df['DESATIVADO'].apply(normalizar_sim_nao)
    df['BAIXADO'] = df['BAIXADO'].apply(normalizar_sim_nao)
    
    def definir_status(row):
        if row['BAIXADO'] == 'SIM': return "BAIXADO"
        if row['DESATIVADO'] == 'SIM': return "DESATIVADO"
        return "ATIVO"
        
    df['STATUS_EQUIPAMENTO'] = df.apply(definir_status, axis=1)
    
    map_rank = {"ATIVO": 1, "DESATIVADO": 2, "BAIXADO": 3}
    df['STATUS_RANK'] = df['STATUS_EQUIPAMENTO'].map(map_rank)
    
    colunas_ordem = ['EQUIP_KEY', 'STATUS_RANK']
    ascendentes = [True, True]
    if 'REPORT_CREATED_AT' in df.columns:
        colunas_ordem.append('REPORT_CREATED_AT')
        ascendentes.append(False)
        
    df = df.sort_values(by=colunas_ordem, ascending=ascendentes)
    df = df.drop_duplicates(subset=['EQUIP_KEY'], keep='first')
    df = df.drop(columns=['STATUS_RANK'])
    
    if 'ÚLTIMA MP' in df.columns:
        datas_texto = pd.to_datetime(df['ÚLTIMA MP'], errors='coerce')
        numeros_excel = pd.to_numeric(df['ÚLTIMA MP'], errors='coerce')
        datas_excel = pd.to_datetime(numeros_excel, origin='1899-12-30', unit='D', errors='coerce')
        df['ÚLTIMA MP'] = datas_texto.fillna(datas_excel)
        
    return df

def enriquecer_base_inventario(df_inventario, df_os_encerradas):
    if df_inventario.empty: return pd.DataFrame()
    df_inv = df_inventario.copy()
    hoje = pd.Timestamp(datetime.today().date())

    if 'AQUISIÇÃO' in df_inv.columns: df_inv['AQUISIÇÃO'] = pd.to_datetime(df_inv['AQUISIÇÃO'], errors='coerce')
    if 'GARANTIA' in df_inv.columns: df_inv['GARANTIA'] = pd.to_datetime(df_inv['GARANTIA'], errors='coerce')

    if not df_os_encerradas.empty:
        df_os = df_os_encerradas.copy()
        col_id_os = 'IDENTIFICADOR' if 'IDENTIFICADOR' in df_os.columns else 'ID'
        col_serie_os = next((c for c in ['N.º SÉRIE', 'N. SÉRIE', 'SÉRIE'] if c in df_os.columns), 'SÉRIE')
        col_prog_os = next((c for c in ['PROGRAMA MP', 'PROGRAMA'] if c in df_os.columns), 'PROGRAMA')
        col_data_os = 'ENCERRAMENTO'
        
        programas_interesse = ["PREVENTIVA", "CALIBRAÇÃO", "SEGURANÇA ELÉTRICA", "INSPEÇÃO E TESTE OPERACIONAL", "VALIDAÇÃO", "QUALIFICAÇÃO TÉRMICA"]
        
        if col_id_os in df_os.columns and col_serie_os in df_os.columns and col_prog_os in df_os.columns:
            df_os_filtrado = df_os[df_os[col_id_os].notna() & df_os[col_serie_os].notna() & df_os[col_prog_os].str.upper().str.strip().isin(programas_interesse)].copy()
            df_os_filtrado[col_data_os] = pd.to_datetime(df_os_filtrado[col_data_os], errors='coerce')
            
            df_max_datas = df_os_filtrado.groupby([col_id_os, col_serie_os, col_prog_os])[col_data_os].max().unstack(level=col_prog_os).reset_index()
            df_max_datas = df_max_datas.rename(columns={col_id_os: 'IDENTIFICADOR', col_serie_os: 'N.º SÉRIE'})
            df_inv = df_inv.merge(df_max_datas, on=['IDENTIFICADOR', 'N.º SÉRIE'], how='left')

    colunas_mps = ["PREVENTIVA", "CALIBRAÇÃO", "SEGURANÇA ELÉTRICA", "INSPEÇÃO E TESTE OPERACIONAL", "VALIDAÇÃO", "QUALIFICAÇÃO TÉRMICA"]
    for col in colunas_mps:
        if col not in df_inv.columns: df_inv[col] = pd.NaT
        else: df_inv[col] = pd.to_datetime(df_inv[col], errors='coerce')

    is_novo = (df_inv['AQUISIÇÃO'] >= (hoje - pd.DateOffset(months=6))) if 'AQUISIÇÃO' in df_inv.columns else pd.Series(False, index=df_inv.index)
    is_garantia = (df_inv['GARANTIA'] >= hoje) if 'GARANTIA' in df_inv.columns else pd.Series(False, index=df_inv.index)
    is_isento_nr = is_novo | is_garantia

    for tipo_mp in ['PREVENTIVA', 'CALIBRAÇÃO']:
        dias_desde = (hoje - df_inv[tipo_mp]).dt.days
        condicoes = [is_isento_nr & df_inv[tipo_mp].isna(), df_inv[tipo_mp].isna(), dias_desde > 730, dias_desde > 365, dias_desde >= 320, dias_desde >= 275]
        df_inv[f'Status {tipo_mp}'] = np.select(condicoes, ["Garantia/Novo", "NR", "+ 2a", "+ 1a", "em 45d", "em 3m"], default="OK")
        df_inv[f'Ordem Status {tipo_mp}'] = np.select(condicoes, [7, 1, 2, 3, 4, 5], default=6)

    if 'ÚLTIMA MP' in df_inv.columns:
        df_inv['ÚLTIMA MP'] = pd.to_datetime(df_inv['ÚLTIMA MP'], errors='coerce')
        dias_ultima_mp = (hoje - df_inv['ÚLTIMA MP']).dt.days
        cond_mp_geral = [is_isento_nr & df_inv['ÚLTIMA MP'].isna(), df_inv['ÚLTIMA MP'].isna(), dias_ultima_mp > 730, dias_ultima_mp > 365, dias_ultima_mp >= 320, dias_ultima_mp >= 275]
        df_inv['Ordem Status MP'] = np.select(cond_mp_geral, [7, 1, 2, 3, 4, 5], default=6)
    else:
        df_inv['Ordem Status MP'] = np.where(is_isento_nr, 7, 1)

    if 'AQUISIÇÃO' in df_inv.columns:
        df_inv['Idade Equipamento Num'] = np.round((hoje - df_inv['AQUISIÇÃO']).dt.days / 365.25, 2)
        df_inv['Faixa de Idade'] = np.select([df_inv['Idade Equipamento Num'] > 10, df_inv['Idade Equipamento Num'] >= 8, df_inv['Idade Equipamento Num'] >= 5, df_inv['Idade Equipamento Num'] >= 3], ["> 10 anos", "8 a 10 anos", "5 a 8 anos", "3 a 5 anos"], default="0 a 3 anos")
        df_inv['Ordem Faixa Idade'] = np.select([df_inv['Idade Equipamento Num'] > 10, df_inv['Idade Equipamento Num'] >= 8, df_inv['Idade Equipamento Num'] >= 5, df_inv['Idade Equipamento Num'] >= 3], [5, 4, 3, 2], default=1)
    else:
        df_inv['Idade Equipamento Num'] = 0
        df_inv['Faixa de Idade'] = "0 a 3 anos"
        df_inv['Ordem Faixa Idade'] = 1

    df_inv['Status Garantia'] = np.where(df_inv['GARANTIA'].isna() | (df_inv['GARANTIA'] < hoje), "Fora de Garantia", "Na Garantia") if 'GARANTIA' in df_inv.columns else "Fora de Garantia"
    return df_inv
