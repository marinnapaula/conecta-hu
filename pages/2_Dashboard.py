# =====================================================================
# TAB 2: CENTRAL OPERACIONAL DE O.S. PENDENTES (MÓDULO FILTRO + DRILL-DOWN)
# =====================================================================
with tab_fila:
    if not df_pend.empty:
        df_p = df_pend.copy()
        
        col_os = get_col(df_p, ['O.S.', 'OS', 'Nº O.S.', 'OS_KEY'])
        col_abertura = get_col(df_p, ['ABERTURA', 'DATA ABERTURA'])
        col_critico = get_col(df_p, ['EQUIPAMENTO CRÍTICO', 'EQUIPAMENTO CRITICO'])
        col_parado = get_col(df_p, ['EQUIPAMENTO PARADO', 'PARADO'])
        col_local = get_col(df_p, ['LOCALIZAÇÃO FÍSICA', 'LOCALIZAÇÃO', 'LOCALIZACAO_INVENTARIO'])
        col_serie = get_col(df_p, ['N. SÉRIE', 'N.º SÉRIE', 'SÉRIE'])
        col_tipo = get_col(df_p, ['TIPO EQUIPAMENTO', 'EQUIPAMENTO', 'DESCRIÇÃO'])
        col_estado = get_col(df_p, ['ESTADO', 'ESTADO DA O.S.'])
        col_executor = get_col(df_p, ['EXECUTOR', 'RESPONSÁVEL'])
        
        if col_abertura:
            df_p[col_abertura] = pd.to_datetime(df_p[col_abertura], errors='coerce')
            hoje = pd.Timestamp(datetime.today().date())
            df_p['DIAS_EM_ABERTO'] = (hoje - df_p[col_abertura]).dt.days
        else:
            df_p['DIAS_EM_ABERTO'] = 0
            
        cond_fila = [df_p['DIAS_EM_ABERTO'] <= 5, df_p['DIAS_EM_ABERTO'] <= 15, df_p['DIAS_EM_ABERTO'] <= 30, df_p['DIAS_EM_ABERTO'] <= 60]
        df_p['FAIXA_DIAS'] = np.select(cond_fila, ["0 a 5 dias", "6 a 15 dias", "16 a 30 dias", "31 a 60 dias"], default="Mais de 60 dias")
        
        if col_critico: df_p[col_critico] = df_p[col_critico].astype(str).str.upper().str.strip()
        if col_parado: df_p[col_parado] = df_p[col_parado].astype(str).str.upper().str.strip()

        total_f = len(df_p)
        parados_f = len(df_p[df_p[col_parado] == 'SIM']) if col_parado else 0
        criticos_f = len(df_p[df_p[col_critico] == 'SIM']) if col_critico else 0
        tma_f = df_p['DIAS_EM_ABERTO'].mean() if total_f > 0 else 0

        f_c1, f_c2, f_c3, f_c4 = st.columns(4)
        f_c1.metric("O.S. em Fila de Espera", total_f)
        f_c2.metric("Ativos Totalmente Parados", parados_f, "Gargalo Assistencial", delta_color="inverse" if parados_f > 0 else "normal")
        f_c3.metric("Equipamentos Críticos na Fila", criticos_f, "Prioridade de Despacho", delta_color="inverse" if criticos_f > 0 else "normal")
        f_c4.metric("Tempo Médio de Fila Atual", f"{tma_f:.1f} Dias", "Atraso médio das O.S.")

        st.markdown("<br><h3 style='color: #154899;'>🎛️ Painel de Filtros Operacionais</h3>", unsafe_allow_html=True)

        with st.container(border=True):
            r1, r2, r3, r4 = st.columns(4)
            f_num_os = r1.text_input("Número da O.S.", placeholder="Digite o código...")
            f_num_serie = r2.text_input("Número de Série", placeholder="Digite o S/N...")
            f_faixa_dias = r3.multiselect("Faixa de Dias (Atraso)", sorted(df_p['FAIXA_DIAS'].unique()))
            f_local_fisico = r4.multiselect("Localização Física (Setor)", sorted(df_p[col_local].dropna().unique()) if col_local else [])
            
            r5, r6, r7, r8 = st.columns(4)
            f_tipo_equip = r5.multiselect("Tipo de Equipamento", sorted(df_p[col_tipo].dropna().unique()) if col_tipo else [])
            f_estado_os = r6.multiselect("Estado (Status do Chamado)", sorted(df_p[col_estado].dropna().unique()) if col_estado else [])
            f_eq_parado = r7.selectbox("Equipamento Parado?", ["Todos", "SIM", "NÃO"])
            f_eq_critico = r8.selectbox("Equipamento Crítico?", ["Todos", "SIM", "NÃO"])

        df_f = df_p.copy()
        if f_num_os and col_os: df_f = df_f[df_f[col_os].astype(str).str.contains(f_num_os, case=False, na=False)]
        if f_num_serie and col_serie: df_f = df_f[df_f[col_serie].astype(str).str.contains(f_num_serie, case=False, na=False)]
        if f_faixa_dias: df_f = df_f[df_f['FAIXA_DIAS'].isin(f_faixa_dias)]
        if f_local_fisico and col_local: df_f = df_f[df_f[col_local].isin(f_local_fisico)]
        if f_tipo_equip and col_tipo: df_f = df_f[df_f[col_tipo].isin(f_tipo_equip)]
        if f_estado_os and col_estado: df_f = df_f[df_f[col_estado].isin(f_estado_os)]
        if f_eq_parado != "Todos" and col_parado: df_f = df_f[df_f[col_parado] == f_eq_parado]
        if f_eq_critico != "Todos" and col_critico: df_f = df_f[df_f[col_critico] == f_eq_critico]

        df_f = df_f.sort_values(by='DIAS_EM_ABERTO', ascending=False)

        st.markdown(f"**Registros Filtrados:** {len(df_f)} ordens pendentes localizadas.")
        colunas_grade = [c for c in [col_os, col_tipo, col_serie, col_local, 'DIAS_EM_ABERTO', col_estado, col_executor] if c in df_f.columns]
        st.dataframe(
            df_f[colunas_grade],
            use_container_width=True, hide_index=True, height=240,
            column_config={
                "DIAS_EM_ABERTO": st.column_config.ProgressColumn("Tempo de Espera", format="%d dias", min_value=0, max_value=int(df_p['DIAS_EM_ABERTO'].max()) if len(df_p) > 0 else 100),
                col_os: st.column_config.TextColumn("Nº O.S.")
            }
        )

        st.markdown("---")

        # =================================================================
        # FICHA TÉCNICA DRILL-DOWN + INTEGRAÇÃO BLINDADA COM ATIVIDADES
        # =================================================================
        st.markdown("<h3 style='color: #154899;'>🗂️ Central de Investigação da O.S. (Drill-Down)</h3>", unsafe_allow_html=True)
        
        if not df_f.empty and col_os:
            lista_os_str = df_f[col_os].astype(str).unique()
            os_alvo = st.selectbox("Escolha uma Ordem de Serviço da lista para abrir a ficha completa:", options=lista_os_str)
            
            if os_alvo:
                dados_linha = df_f[df_f[col_os].astype(str) == os_alvo].iloc[0]
                
                with st.container(border=True):
                    f_col_t, f_col_b1, f_col_b2 = st.columns([2, 1, 1])
                    nome_eq = dados_linha.get(col_tipo, 'Não Informado')
                    f_col_t.markdown(f"#### Ficha de Atendimento - O.S. № {os_alvo}")
                    f_col_t.markdown(f"**Equipamento:** {nome_eq} | **Chave Ativo:** {dados_linha.get('EQUIP_KEY', 'N/A')}")
                    
                    p_status = "🔴 PARADO (Crítico)" if str(dados_linha.get(col_parado, '')).upper() == 'SIM' else "🟢 EM OPERAÇÃO"
                    c_status = "⚠️ ALTA CRITICIDADE" if str(dados_linha.get(col_critico, '')).upper() == 'SIM' else "ℹ️ CRITICIDADE NORMAL"
                    
                    f_col_b1.markdown(f"**Estado Físico:**<br>`{p_status}`", unsafe_allow_html=True)
                    f_col_b2.markdown(f"**Severidade:**<br>`{c_status}`", unsafe_allow_html=True)
                    
                    st.divider()
                    
                    d1, d2, d3 = st.columns(3)
                    dt_ab = dados_linha.get(col_abertura)
                    dt_ab_str = dt_ab.strftime('%d/%m/%Y') if pd.notnull(dt_ab) else 'N/I'
                    
                    col_tr = get_col(df_f, ['DT. ÚLTIMA TRANSIÇÃO', 'ÚLTIMA TRANSIÇÃO'])
                    dt_tr = dados_linha.get(col_tr)
                    dt_tr_str = pd.to_datetime(dt_tr).strftime('%d/%m/%Y') if pd.notnull(dt_tr) else 'N/I'
                    
                    d1.markdown(f"**📅 Abertura:** {dt_ab_str}")
                    d1.markdown(f"**⏳ Dias na Fila:** {dados_linha.get('DIAS_EM_ABERTO', 0)} dias")
                    d2.markdown(f"**📍 Setor Atual:** {dados_linha.get(col_local, 'N/I')}")
                    d2.markdown(f"**🔢 Série:** {dados_linha.get(col_serie, 'N/I')}")
                    d3.markdown(f"**⚙️ Estado GETS:** {dados_linha.get(col_estado, 'N/I')}")
                    d3.markdown(f"**👷 Responsável:** {dados_linha.get(col_executor, 'Não Alocado')}")
                    
                    st.markdown("<br><h5 style='color: #32A347;'>🛠️ Linha do Tempo e Detalhamento Técnico (Atividades)</h5>", unsafe_allow_html=True)
                    
                    if not df_atividades.empty:
                        df_at_temp = df_atividades.copy()
                        df_at_temp.columns = df_at_temp.columns.str.strip().str.upper()
                        col_os_at = get_col(df_at_temp, ['O.S.', 'OS', 'Nº O.S.', 'OS_KEY'])
                        
                        if col_os_at:
                            # CRÍTICO: Compara as chaves forçando string limpa de ambos os lados para não dar erro
                            os_busca = str(os_alvo).replace('.0', '').strip()
                            df_at_temp['_CHAVE_BUSCA'] = df_at_temp[col_os_at].astype(str).str.replace('.0', '', regex=False).str.strip()
                            
                            df_historico_os = df_at_temp[df_at_temp['_CHAVE_BUSCA'] == os_busca]
                            
                            if not df_historico_os.empty:
                                # Procura pelas colunas de data, técnico e atividade
                                col_data_act = get_col(df_historico_os, ['DATA', 'DATA DA EXECUÇÃO', 'DATA EXECUÇÃO', 'DT EXECUÇÃO', 'DATA ATENDIMENTO'])
                                col_desc_act = get_col(df_historico_os, ['ATIVIDADE', 'DESCRIÇÃO', 'HISTÓRICO', 'DESCRICAO'])
                                col_exec_act = get_col(df_historico_os, ['TÉCNICO', 'EXECUTOR', 'RESPONSÁVEL', 'TECNICO', 'RESPONSAVEL'])
                                
                                cols_print_act = [c for c in [col_data_act, col_exec_act, col_desc_act] if c]
                                df_print_act = df_historico_os[cols_print_act].copy()
                                
                                if col_data_act:
                                    df_print_act[col_data_act] = pd.to_datetime(df_print_act[col_data_act], errors='coerce')
                                    df_print_act = df_print_act.sort_values(by=col_data_act, ascending=False)
                                    df_print_act[col_data_act] = df_print_act[col_data_act].dt.strftime('%d/%m/%Y %H:%M')
                                    
                                st.dataframe(df_print_act, use_container_width=True, hide_index=True)
                            else:
                                st.info("Esta O.S. está na fila aguardando o primeiro apontamento técnico.")
                                st.caption(f"(Console: Carregamos {len(df_atividades)} logs na memória, mas não houve 'match' para a O.S. {os_busca})")
                        else:
                            st.warning("Coluna 'O.S.' não localizada nos arquivos de Atividades.")
                    else:
                        st.info("Nenhum log disponível. Certifique-se de que a pasta '03.Atividades' contenha as planilhas.")
        else:
            st.warning("Ajuste os critérios de busca nos filtros para carregar as fichas técnicas.")
    else:
        st.success("Fila zerada no momento!")
