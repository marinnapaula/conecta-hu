import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime

# =====================================================================
# 1. INGESTÃO DE DADOS (LEITURA DE ARQUIVOS)
# =====================================================================

def carregar_mais_recente(nome_pasta):
    """Lê sempre o arquivo mais recente de uma pasta do GETS."""
    pasta_alvo = os.path.join(os.getcwd(), "planilhas_gets", nome_pasta)
    arquivos = glob.glob(os.path.join(pasta_alvo, "*.xlsx")) + glob.glob(os.path.join(pasta_alvo, "*.csv"))
    
    if not arquivos:
        return pd.DataFrame()
        
    arq_recente = max(arquivos, key=os.path.getmtime)
    
    try:
        df = pd.read_excel(arq_recente, skiprows=5) if arq_recente.endswith('.xlsx') else pd.read_csv(arq_recente, skiprows=5)
        df.columns = df.columns.str.strip().str.upper()
        df['REPORT_CREATED_AT'] = pd.to_datetime(os.path.getmtime(arq_recente), unit='s')
        return df
    except:
        return pd.DataFrame()

def carregar_os_encerradas():
    """Lê TODA a pasta de OS Encerradas com LEITURA BLINDADA para arquivos antigos."""
    pasta_alvo = os.path.join(os.getcwd(), "planilhas_gets", "01.OS_Encerradas")
    arquivos = glob.glob(os.path.join(pasta_alvo, "*.xlsx")) + glob.glob(os.path.join(pasta_alvo, "*.csv"))
    
    if not arquivos: return pd.DataFrame()

    lista_dfs = []
    colunas_os_possiveis = ['N.º O.S.', 'Nº O.S.', 'N. O.S.', 'O.S.', 'OS', 'ORDEM DE SERVIÇO']
    
    for arq in arquivos:
        try:
            # 1ª Tentativa: Pular 5 linhas (Padrão mais comum)
            df_temp = pd.read_excel(arq, skiprows=5) if arq.endswith('.xlsx') else pd.read_csv(arq, skiprows=5)
            df_temp.columns = df_temp.columns.str.strip().str.upper()
            
            # Se não achou a coluna O.S., tenta pular 4 linhas
            if not any(c in df_temp.columns for c in colunas_os_possiveis):
                df_temp = pd.read_excel(arq, skiprows=4) if arq.endswith('.xlsx') else pd.read_csv(arq, skiprows=4)
                df_temp.columns = df_temp.columns.str.strip().str.upper()

            # Se ainda não achou, tenta pular 3 linhas
            if not any(c in df_temp.columns for c in colunas_os_possiveis):
                df_temp = pd.read_excel(arq, skiprows=3) if arq.endswith('.xlsx') else pd.read_csv(arq, skiprows=3)
                df_temp.columns = df_temp.columns.str.strip().str.upper()

            df_temp['REPORT_CREATED_AT'] = pd.to_datetime(os.path.getmtime(arq), unit='s')
            lista_dfs.append(df_temp)
        except: continue
            
    if not lista_dfs: return pd.DataFrame()
    df_final = pd.concat(lista_dfs, ignore_index=True)

    col_os = next((col for col in colunas_os_possiveis if col in df_final.columns), None)

    if col_os:
        df_final = df_final.dropna(subset=[col_os])
        df_final['OS_KEY'] = df_final[col_os].astype(str).str.replace('.0', '', regex=False).str.strip().str.upper()
    else: 
        return pd.DataFrame() 

    for col in ['ABERTURA', 'ENCERRAMENTO']:
        if col in df_final.columns:
            df_final[col] = pd.to_datetime(df_final[col], errors='coerce', dayfirst=True)

    # Filtra mantendo apenas O.S. a partir de 2023
    if 'ENCERRAMENTO' in df_final.columns:
        df_final = df_final[df_final['ENCERRAMENTO'].dt.year >= 2023]
        df_final = df_final.sort_values(by=['ENCERRAMENTO', 'REPORT_CREATED_AT'], ascending=[False, False])
    else:
        df_final = df_final.sort_values(by='REPORT_CREATED_AT', ascending=False)
        
    df_final = df_final.drop_duplicates(subset=['OS_KEY'], keep='first')
    return df_final

def carregar_todas_atividades(nome_pasta="03.Atividades"):
    """Lê todos os relatórios mensais de atividades e os empilha (Leitura Blindada)."""
    pasta_alvo = os.path.join(os.getcwd(), "planilhas_gets", nome_pasta)
    arquivos = glob.glob(os.path.join(pasta_alvo, "*.xlsx")) + glob.glob(os.path.join(pasta_alvo, "*.csv"))
    
    if not arquivos and nome_pasta == "03.Atividades":
        return carregar_todas_atividades("03.Atividades_Recentes")
        
    if not arquivos: return pd.DataFrame()
        
    lista_dfs = []
    colunas_os_possiveis = ['N.º O.S.', 'Nº O.S.', 'N. O.S.', 'O.S.', 'OS', 'ORDEM DE SERVIÇO']

    for arq in arquivos:
        try:
            df_temp = pd.read_excel(arq, skiprows=5) if arq.endswith('.xlsx') else pd.read_csv(arq, skiprows=5)
            df_temp.columns = df_temp.columns.str.strip().str.upper()
            
            if not any(c in df_temp.columns for c in colunas_os_possiveis):
                df_temp = pd.read_excel(arq, skiprows=4) if arq.endswith('.xlsx') else pd.read_csv(arq, skiprows=4)
                df_temp.columns = df_temp.columns.str.strip().str.upper()

            if not any(c in df_temp.columns for c in colunas_os_possiveis):
                df_temp = pd.read_excel(arq, skiprows=3) if arq.endswith('.xlsx') else pd.read_csv(arq, skiprows=3)
                df_temp.columns = df_temp.columns.str.strip().str.upper()

            lista_dfs.append(df_temp)
        except: continue
            
    if not lista_dfs: return pd.DataFrame()
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    col_os = next((col for col in colunas_os_possiveis if col in df_final.columns), None)
    
    if col_os:
        df_final = df_final.dropna(subset=[col_os])
        df_final['OS_KEY'] = df_final[col_os].astype(str).str.replace('.0', '', regex=False).str.strip().str.upper()
        
    df_final = df_final.drop_duplicates()
    return df_final

def gerar_curva_backlog():
    """Conta o volume diário de O.S. Pendentes lendo o histórico de arquivos."""
    pasta_alvo = os.path.join(os.getcwd(), "planilhas_gets", "02.OS_Pendentes")
    arquivos = glob.glob(os.path.join(pasta_alvo, "*.xlsx")) + glob.glob(os.path.join(pasta_alvo, "*.csv"))
    
    if not arquivos: return pd.DataFrame()
    lista_historico = []
    
    for arq in arquivos:
        try:
            dt_snap = pd.to_datetime(os.path.getmtime(arq), unit='s').normalize()
            df_temp = pd.read_excel(arq, skiprows=5) if arq.endswith('.xlsx') else pd.read_csv(arq, skiprows=5)
            df_temp.columns = df_temp.columns.str.strip().str.upper()
            col_os = next((c for c in ['N.º O.S.', 'Nº O.S.', 'O.S.', 'OS'] if c in df_temp.columns), None)
            if col_os:
                qtd_os = df_temp[col_os].dropna().count()
                lista_historico.append({'Data': dt_snap, 'Volume Fila': int(qtd_os)})
        except: continue
            
    if not lista_historico: return pd.DataFrame()
    df_hist = pd.DataFrame(lista_historico)
    df_hist = df_hist.groupby('Data')['Volume Fila'].max().reset_index().sort_values(by='Data')
    return df_hist

# =====================================================================
# 2. MOTOR DE TRATAMENTO E INTELIGÊNCIA (INVENTÁRIO)
# =====================================================================

def limpar_dimensao_equipamentos(df_inventario_bruto):
    """Limpeza, unificação de colunas e tratamento de datas numéricas."""
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
    """Cruza o Inventário com as OS Encerradas e calcula prazos, regras de carência de MP e garantia."""
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
