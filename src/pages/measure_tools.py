import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from src.utils.project_manager import ProjectManager
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def show_data_collection_plan(project_data: Dict):
    """Plano de Coleta de Dados"""
    
    project_id = project_data.get('id')
    project_manager = ProjectManager()
    
    st.markdown("## 📊 Plano de Coleta de Dados")
    st.markdown("Defina **o que**, **como**, **quando** e **onde** coletar os dados do processo.")
    
    # Inicializar dados no session_state
    plan_key = f"data_plan_{project_id}"
    if plan_key not in st.session_state:
        existing_data = project_data.get('measure', {}).get('data_collection_plan', {}).get('data', {})
        st.session_state[plan_key] = existing_data if existing_data else {}
    
    plan_data = st.session_state[plan_key]
    
    # Status atual
    is_completed = project_data.get('measure', {}).get('data_collection_plan', {}).get('completed', False)
    if is_completed:
        st.success("✅ Plano de coleta finalizado")
    else:
        st.info("⏳ Plano em desenvolvimento")
    
    # Seção 1: Objetivos da Coleta
    st.markdown("### 🎯 Objetivos da Coleta de Dados")
    
    collection_objective = st.text_area(
        "Objetivo Principal da Coleta *",
        value=plan_data.get('collection_objective', ''),
        placeholder="Ex: Medir a variabilidade do tempo de setup das máquinas...",
        height=80,
        key=f"collection_objective_{project_id}",
        help="Por que estamos coletando estes dados?"
    )
    
    # Seção 2: Variáveis a Medir
    st.markdown("### 📏 Variáveis a Serem Medidas")
    
    # Inicializar lista de variáveis
    if 'variables' not in plan_data or plan_data['variables'] is None:
        plan_data['variables'] = []
        st.session_state[plan_key] = plan_data
    
    # Adicionar nova variável
    with st.expander("➕ Adicionar Nova Variável"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            var_name = st.text_input("Nome da Variável *", placeholder="Ex: Tempo de Setup", key=f"var_name_{project_id}")
            var_type = st.selectbox("Tipo de Dados", options=["Contínua", "Discreta", "Categórica", "Binária"], key=f"var_type_{project_id}")
        
        with col2:
            var_unit = st.text_input("Unidade de Medida", placeholder="Ex: minutos, peças, %", key=f"var_unit_{project_id}")
            var_target = st.text_input("Valor Alvo/Especificação", placeholder="Ex: < 30 min, 0 defeitos", key=f"var_target_{project_id}")
        
        with col3:
            var_importance = st.selectbox("Importância", options=["Alta", "Média", "Baixa"], key=f"var_importance_{project_id}")
            var_frequency = st.selectbox("Frequência de Coleta", options=["Contínua", "Horária", "Diária", "Semanal", "Por Lote"], key=f"var_frequency_{project_id}")
        
        var_description = st.text_area("Descrição da Variável", placeholder="Como esta variável será medida?", height=60, key=f"var_description_{project_id}")
        
        if st.button("➕ Adicionar Variável", key=f"add_variable_{project_id}"):
            if var_name.strip():
                new_variable = {
                    'id': len(plan_data['variables']) + 1,
                    'name': var_name.strip(),
                    'type': var_type,
                    'unit': var_unit,
                    'target': var_target,
                    'importance': var_importance,
                    'frequency': var_frequency,
                    'description': var_description,
                    'created_at': datetime.now().isoformat()
                }
                
                plan_data['variables'].append(new_variable)
                st.session_state[plan_key] = plan_data
                st.success(f"✅ Variável '{var_name}' adicionada!")
                st.rerun()
            else:
                st.error("❌ Nome da variável é obrigatório")
    
    # Mostrar variáveis cadastradas
    if plan_data['variables'] and len(plan_data['variables']) > 0:
        st.markdown("#### 📋 Variáveis Cadastradas")
        
        for i, var in enumerate(plan_data['variables']):
            with st.expander(f"{var['name']} ({var['type']}) - Importância: {var['importance']}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Unidade:** {var.get('unit', 'N/A')}")
                    st.write(f"**Frequência:** {var['frequency']}")
                
                with col2:
                    st.write(f"**Alvo:** {var.get('target', 'N/A')}")
                    st.write(f"**Descrição:** {var.get('description', 'N/A')}")
                
                with col3:
                    if st.button("🗑️ Remover", key=f"remove_var_{i}_{project_id}"):
                        plan_data['variables'].pop(i)
                        st.session_state[plan_key] = plan_data
                        st.rerun()
    
    # Seção 3: Método de Coleta
    st.markdown("### 🔧 Método de Coleta")
    
    col1, col2 = st.columns(2)
    
    with col1:
        collection_method_options = ["Medição Direta", "Observação", "Sistema Automatizado", "Formulário/Checklist", "Sensor/Equipamento", "Amostragem"]
        current_method = plan_data.get('collection_method', 'Medição Direta')
        try:
            method_index = collection_method_options.index(current_method)
        except ValueError:
            method_index = 0
            
        collection_method = st.selectbox(
            "Método Principal *",
            options=collection_method_options,
            index=method_index,
            key=f"collection_method_{project_id}"
        )
        
        data_source = st.text_input(
            "Fonte dos Dados *",
            value=plan_data.get('data_source', ''),
            placeholder="Ex: Sistema ERP, Relatórios de produção...",
            key=f"data_source_{project_id}"
        )
    
    with col2:
        responsible_person = st.text_input(
            "Responsável pela Coleta *",
            value=plan_data.get('responsible_person', ''),
            placeholder="Nome do responsável",
            key=f"responsible_person_{project_id}"
        )
        
        collection_location = st.text_input(
            "Local da Coleta",
            value=plan_data.get('collection_location', ''),
            placeholder="Ex: Linha de produção 1, Setor de qualidade...",
            key=f"collection_location_{project_id}"
        )
    
    # Seção 4: Cronograma
    st.markdown("### 📅 Cronograma da Coleta")
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        try:
            start_date_value = datetime.fromisoformat(plan_data.get('start_date', datetime.now().isoformat())).date()
        except:
            start_date_value = datetime.now().date()
            
        start_date = st.date_input(
            "Data de Início *",
            value=start_date_value,
            key=f"start_date_{project_id}"
        )
    
    with col4:
        try:
            end_date_value = datetime.fromisoformat(plan_data.get('end_date', (datetime.now() + timedelta(days=30)).isoformat())).date()
        except:
            end_date_value = (datetime.now() + timedelta(days=30)).date()
            
        end_date = st.date_input(
            "Data de Fim *",
            value=end_date_value,
            key=f"end_date_{project_id}"
        )
    
    with col5:
        sample_size = st.number_input(
            "Tamanho da Amostra",
            value=int(plan_data.get('sample_size', 30)),
            min_value=1,
            step=1,
            key=f"sample_size_{project_id}",
            help="Quantidade mínima de dados a coletar"
        )
    
    # Seção 5: Considerações Especiais
    st.markdown("### ⚠️ Considerações Especiais")
    
    col6, col7 = st.columns(2)
    
    with col6:
        potential_issues = st.text_area(
            "Problemas Potenciais",
            value=plan_data.get('potential_issues', ''),
            placeholder="Que problemas podem ocorrer na coleta?",
            height=80,
            key=f"potential_issues_{project_id}"
        )
    
    with col7:
        mitigation_actions = st.text_area(
            "Ações de Mitigação",
            value=plan_data.get('mitigation_actions', ''),
            placeholder="Como prevenir/resolver os problemas?",
            height=80,
            key=f"mitigation_actions_{project_id}"
        )
    
    # Botões de ação
    st.divider()
    
    col8, col9, col10 = st.columns([2, 1, 1])
    
    with col9:
        save_plan = st.button("💾 Salvar Plano", use_container_width=True, key=f"save_plan_{project_id}")
    
    with col10:
        finalize_plan = st.button("✅ Finalizar Plano", use_container_width=True, type="primary", key=f"finalize_plan_{project_id}")
    
    # Processar ações
    if save_plan or finalize_plan:
        # Coletar dados atuais
        current_data = {
            'collection_objective': st.session_state.get(f"collection_objective_{project_id}", ''),
            'variables': plan_data.get('variables', []),
            'collection_method': st.session_state.get(f"collection_method_{project_id}", ''),
            'data_source': st.session_state.get(f"data_source_{project_id}", ''),
            'responsible_person': st.session_state.get(f"responsible_person_{project_id}", ''),
            'collection_location': st.session_state.get(f"collection_location_{project_id}", ''),
            'start_date': st.session_state.get(f"start_date_{project_id}", datetime.now().date()).isoformat(),
            'end_date': st.session_state.get(f"end_date_{project_id}", datetime.now().date()).isoformat(),
            'sample_size': st.session_state.get(f"sample_size_{project_id}", 30),
            'potential_issues': st.session_state.get(f"potential_issues_{project_id}", ''),
            'mitigation_actions': st.session_state.get(f"mitigation_actions_{project_id}", ''),
            'last_saved': datetime.now().isoformat()
        }
        
        # Validar campos obrigatórios se finalizando
        if finalize_plan:
            required_fields = [
                (current_data['collection_objective'], "Objetivo da Coleta"),
                (current_data['data_source'], "Fonte dos Dados"),
                (current_data['responsible_person'], "Responsável pela Coleta")
            ]
            
            missing_fields = [field_name for field_value, field_name in required_fields if not str(field_value).strip()]
            
            if missing_fields:
                st.error(f"❌ Campos obrigatórios: {', '.join(missing_fields)}")
                st.stop()
            
            if not current_data['variables'] or len(current_data['variables']) == 0:
                st.error("❌ Adicione pelo menos uma variável para medir")
                st.stop()
        
        # Salvar
        st.session_state[plan_key] = current_data
        
        # Salvar no Firebase
        update_data = {
            f'measure.data_collection_plan.data': current_data,
            f'measure.data_collection_plan.completed': finalize_plan,
            f'measure.data_collection_plan.updated_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        with st.spinner("💾 Salvando..."):
            try:
                success = project_manager.update_project(project_id, update_data)
                
                if success:
                    # Atualizar session_state do projeto
                    if 'current_project' in st.session_state:
                        if 'measure' not in st.session_state.current_project:
                            st.session_state.current_project['measure'] = {}
                        if 'data_collection_plan' not in st.session_state.current_project['measure']:
                            st.session_state.current_project['measure']['data_collection_plan'] = {}
                        
                        st.session_state.current_project['measure']['data_collection_plan']['data'] = current_data
                        st.session_state.current_project['measure']['data_collection_plan']['completed'] = finalize_plan
                    
                    if finalize_plan:
                        st.success("✅ Plano de coleta finalizado e salvo!")
                        st.balloons()
                        
                        # Mostrar resumo
                        st.markdown("### 📊 Resumo do Plano")
                        col_sum1, col_sum2, col_sum3 = st.columns(3)
                        
                        with col_sum1:
                            st.metric("Variáveis a Medir", len(current_data['variables']))
                        
                        with col_sum2:
                            try:
                                duration = (datetime.fromisoformat(current_data['end_date']) - datetime.fromisoformat(current_data['start_date'])).days
                                st.metric("Duração", f"{duration} dias")
                            except:
                                st.metric("Duração", "N/A")
                        
                        with col_sum3:
                            st.metric("Tamanho da Amostra", current_data['sample_size'])
                        
                    else:
                        st.success("💾 Plano salvo com sucesso!")
                
                else:
                    st.error("❌ Erro ao salvar no Firebase")
                    
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {str(e)}")


def show_file_upload_analysis(project_data: Dict):
    """Upload e Análise de Arquivos - VERSÃO CORRIGIDA"""
    
    project_id = project_data.get('id')
    
    st.markdown("## 📁 Upload e Análise de Dados")
    st.markdown("Faça upload dos seus dados e realize análises estatísticas básicas.")
    
    # Upload de arquivo
    st.markdown("### 📤 Upload de Arquivo")
    
    uploaded_file = st.file_uploader(
        "Escolha um arquivo",
        type=['csv', 'xlsx', 'xls', 'txt'],
        help="Formatos suportados: CSV, Excel (.xlsx, .xls), TXT",
        key=f"file_upload_{project_id}"
    )
    
    if uploaded_file is not None:
        try:
            # Ler arquivo baseado na extensão
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'csv':
                # Tentar diferentes separadores
                try:
                    df = pd.read_csv(uploaded_file, sep=',')
                except:
                    uploaded_file.seek(0)
                    try:
                        df = pd.read_csv(uploaded_file, sep=';')
                    except:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, sep='\t')
            
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file)
            
            elif file_extension == 'txt':
                try:
                    df = pd.read_csv(uploaded_file, sep='\t')
                except:
                    uploaded_file.seek(0)
                    try:
                        df = pd.read_csv(uploaded_file, sep=',')
                    except:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, sep=';')
            
            # CORREÇÃO: Processamento mais robusto dos dados
            st.info("🔄 Processando dados...")
            
            # Limpeza inicial dos dados
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Converter para string e limpar
                    df[col] = df[col].astype(str)
                    df[col] = df[col].str.strip()
                    
                    # Substituir valores vazios por NaN
                    df[col] = df[col].replace(['', 'nan', 'NaN', 'null', 'NULL'], np.nan)
            
            # Tentar conversão inteligente para numérico
            original_numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            converted_cols = []
            
            for col in df.columns:
                if col not in original_numeric_cols:
                    # Tentar conversão para numérico
                    try:
                        # Fazer uma cópia da coluna para teste
                        test_col = df[col].copy()
                        
                        # Se for object, tentar limpar e converter
                        if test_col.dtype == 'object':
                            # Remover caracteres não numéricos (exceto . , - +)
                            test_col = test_col.astype(str)
                            
                            # Substituir vírgula por ponto
                            test_col = test_col.str.replace(',', '.')
                            
                            # Remover espaços
                            test_col = test_col.str.strip()
                            
                            # Tentar converter para float
                            test_converted = pd.to_numeric(test_col, errors='coerce')
                            
                            # Se conseguiu converter pelo menos 50% dos dados não-nulos
                            non_null_original = test_col.notna().sum()
                            non_null_converted = test_converted.notna().sum()
                            
                            if non_null_original > 0 and (non_null_converted / non_null_original) >= 0.5:
                                df[col] = test_converted
                                converted_cols.append(col)
                                
                    except Exception as e:
                        # Se der erro, manter como estava
                        continue
            
            # Salvar dados no session_state
            st.session_state[f'uploaded_data_{project_id}'] = df
            st.session_state[f'file_name_{project_id}'] = uploaded_file.name
            
            st.success(f"✅ Arquivo '{uploaded_file.name}' carregado com sucesso!")
            
            if converted_cols:
                st.info(f"🔄 Colunas convertidas para numérico: {', '.join(converted_cols)}")
            
            # Informações básicas do arquivo
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Linhas", df.shape[0])
            
            with col2:
                st.metric("Colunas", df.shape[1])
            
            with col3:
                numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
                st.metric("Colunas Numéricas", numeric_cols)
            
            with col4:
                missing_values = df.isnull().sum().sum()
                st.metric("Valores Faltantes", missing_values)
            
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo: {str(e)}")
            st.info("💡 Verifique se o arquivo está no formato correto e não está corrompido.")
    
    # Análise dos dados carregados
    if f'uploaded_data_{project_id}' in st.session_state:
        df = st.session_state[f'uploaded_data_{project_id}']
        file_name = st.session_state.get(f'file_name_{project_id}', 'arquivo.csv')
        
        st.markdown("### 📊 Análise dos Dados")
        
        # DEBUG: Mostrar tipos de dados
        debug_mode = st.checkbox("🔍 Debug - Mostrar tipos de dados", key=f"debug_types_{project_id}")
        if debug_mode:
            st.write("**Tipos de dados por coluna:**")
            debug_info = []
            for col in df.columns:
                non_null_count = df[col].notna().sum()
                debug_info.append({
                    'Coluna': col,
                    'Tipo': str(df[col].dtype),
                    'Valores Não-Nulos': non_null_count,
                    'Amostra': str(df[col].dropna().iloc[0]) if non_null_count > 0 else 'N/A'
                })
            st.dataframe(pd.DataFrame(debug_info), use_container_width=True)
        
        # Tabs para diferentes análises
        tab1, tab2, tab3, tab4 = st.tabs(["👀 Visualizar", "📈 Estatísticas", "📊 Gráficos", "🔍 Qualidade"])
        
        with tab1:
            st.markdown("#### 📋 Preview dos Dados")
            
            col1, col2 = st.columns(2)
            
            with col1:
                show_rows = st.slider("Linhas a mostrar", 5, min(100, len(df)), 10, key=f"show_rows_{project_id}")
            
            with col2:
                show_info = st.checkbox("Mostrar informações das colunas", key=f"show_info_{project_id}")
            
            # Mostrar dados
            st.dataframe(df.head(show_rows), use_container_width=True)
            
            if show_info:
                st.markdown("#### ℹ️ Informações das Colunas")
                
                info_data = []
                for col in df.columns:
                    info_data.append({
                        'Coluna': col,
                        'Tipo': str(df[col].dtype),
                        'Valores Únicos': df[col].nunique(),
                        'Valores Nulos': df[col].isnull().sum(),
                        'Exemplo': str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else 'N/A'
                    })
                
                st.dataframe(pd.DataFrame(info_data), use_container_width=True)
        
        with tab2:
            st.markdown("#### 📊 Estatísticas Descritivas")
            
            # Detectar colunas numéricas
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if numeric_columns:
                st.success(f"✅ Encontradas {len(numeric_columns)} colunas numéricas: {', '.join(numeric_columns)}")
                
                # Filtrar colunas que têm dados válidos
                valid_numeric_columns = []
                for col in numeric_columns:
                    valid_data_count = df[col].dropna().shape[0]
                    if valid_data_count > 0:
                        valid_numeric_columns.append(col)
                
                if not valid_numeric_columns:
                    st.error("❌ As colunas numéricas não possuem dados válidos")
                    return
                
                selected_columns = st.multiselect(
                    "Selecione as colunas para análise:",
                    valid_numeric_columns,
                    default=valid_numeric_columns[:5] if len(valid_numeric_columns) >= 5 else valid_numeric_columns,
                    key=f"selected_cols_{project_id}"
                )
                
                if selected_columns:
                    try:
                        # CORREÇÃO: Filtrar apenas dados válidos para estatísticas
                        df_clean = df[selected_columns].copy()
                        
                        # Remover linhas onde todas as colunas selecionadas são NaN
                        df_clean = df_clean.dropna(how='all')
                        
                        if df_clean.empty:
                            st.error("❌ Não há dados válidos nas colunas selecionadas")
                            return
                        
                        st.info(f"📊 Calculando estatísticas para {len(df_clean)} linhas válidas")
                        
                        # Estatísticas descritivas básicas
                        stats_df = df_clean.describe()
                        st.dataframe(stats_df.round(4), use_container_width=True)
                        
                        # Estatísticas adicionais
                        st.markdown("#### 📈 Estatísticas Adicionais")
                        
                        additional_stats = []
                        for col in selected_columns:
                            data_col = df_clean[col].dropna()
                            
                            if len(data_col) > 0:
                                try:
                                    # Calcular moda de forma segura
                                    mode_values = data_col.mode()
                                    mode_val = mode_values.iloc[0] if len(mode_values) > 0 else np.nan
                                    
                                    # Calcular coeficiente de variação
                                    mean_val = data_col.mean()
                                    std_val = data_col.std()
                                    cv = (std_val / mean_val * 100) if mean_val != 0 and not np.isnan(mean_val) else 0
                                    
                                    # Calcular assimetria e curtose
                                    skewness = stats.skew(data_col) if len(data_col) > 2 else 0
                                    kurt = stats.kurtosis(data_col) if len(data_col) > 2 else 0
                                    
                                    additional_stats.append({
                                        'Coluna': col,
                                        'Mediana': f"{data_col.median():.4f}",
                                        'Moda': f"{mode_val:.4f}" if not np.isnan(mode_val) else 'N/A',
                                        'Variância': f"{data_col.var():.4f}",
                                        'Coef. Variação': f"{cv:.2f}%",
                                        'Assimetria': f"{skewness:.4f}",
                                        'Curtose': f"{kurt:.4f}",
                                        'Dados Válidos': len(data_col)
                                    })
                                except Exception as e:
                                    st.warning(f"⚠️ Erro ao calcular estatísticas para {col}: {str(e)}")
                        
                        if additional_stats:
                            st.dataframe(pd.DataFrame(additional_stats), use_container_width=True)
                        else:
                            st.error("❌ Não foi possível calcular estatísticas adicionais")
                            
                    except Exception as e:
                        st.error(f"❌ Erro ao calcular estatísticas: {str(e)}")
                        
                        # Tentar diagnóstico do problema
                        st.markdown("**🔍 Diagnóstico:**")
                        for col in selected_columns:
                            col_info = df[col].describe() if pd.api.types.is_numeric_dtype(df[col]) else "Não numérica"
                            st.write(f"- {col}: {col_info}")
                        
                else:
                    st.info("👆 Selecione pelo menos uma coluna para análise")
                    
            else:
                st.warning("⚠️ Nenhuma coluna numérica encontrada")
                
                # Oferecer conversão manual
                st.markdown("**🔧 Conversão Manual de Colunas**")
                
                all_columns = df.columns.tolist()
                cols_to_convert = st.multiselect(
                    "Selecione colunas para tentar converter para numérico:",
                    all_columns,
                    key=f"manual_convert_{project_id}"
                )
                
                if st.button("🔄 Tentar Conversão", key=f"try_convert_{project_id}") and cols_to_convert:
                    df_converted = df.copy()
                    conversion_results = []
                    
                    for col in cols_to_convert:
                        try:
                            original_data = df_converted[col].copy()
                            
                            # Tentar diferentes métodos de conversão
                            if original_data.dtype == 'object':
                                # Método 1: Conversão direta
                                try:
                                    converted = pd.to_numeric(original_data, errors='coerce')
                                    success_rate = converted.notna().sum() / original_data.notna().sum()
                                    
                                    if success_rate > 0.1:  # Se pelo menos 10% converteu
                                        df_converted[col] = converted
                                        conversion_results.append(f"✅ {col}: {success_rate:.1%} convertido")
                                        continue
                                except:
                                    pass
                                
                                # Método 2: Limpeza e conversão
                                try:
                                    cleaned = original_data.astype(str).str.strip()
                                    cleaned = cleaned.str.replace(',', '.')
                                    cleaned = cleaned.str.replace(r'[^\d.-]', '', regex=True)
                                    converted = pd.to_numeric(cleaned, errors='coerce')
                                    success_rate = converted.notna().sum() / original_data.notna().sum()
                                    
                                    if success_rate > 0.1:
                                        df_converted[col] = converted
                                        conversion_results.append(f"✅ {col}: {success_rate:.1%} convertido (com limpeza)")
                                        continue
                                except:
                                    pass
                            
                            conversion_results.append(f"❌ {col}: Não foi possível converter")
                            
                        except Exception as e:
                            conversion_results.append(f"❌ {col}: Erro - {str(e)}")
                    
                    # Mostrar resultados
                    for result in conversion_results:
                        if result.startswith("✅"):
                            st.success(result)
                        else:
                            st.warning(result)
                    
                    # Atualizar DataFrame se houve conversões bem-sucedidas
                    new_numeric_cols = df_converted.select_dtypes(include=[np.number]).columns.tolist()
                    if len(new_numeric_cols) > len(numeric_columns):
                        st.session_state[f'uploaded_data_{project_id}'] = df_converted
                        st.success("🔄 DataFrame atualizado! Recarregue a página para ver as mudanças.")
                        st.rerun()
        
        with tab3:
            st.markdown("#### 📊 Visualizações")
            
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if numeric_columns:
                chart_type = st.selectbox(
                    "Tipo de Gráfico:",
                    ["Histograma", "Box Plot", "Linha do Tempo", "Scatter Plot", "Correlação"],
                    key=f"chart_type_{project_id}"
                )
                
                try:
                    if chart_type == "Histograma":
                        col_to_plot = st.selectbox("Coluna:", numeric_columns, key=f"hist_col_{project_id}")
                        
                        # Filtrar dados válidos
                        valid_data = df[col_to_plot].dropna()
                        if len(valid_data) > 0:
                            fig = px.histogram(x=valid_data, nbins=30, title=f"Histograma - {col_to_plot}")
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("⚠️ Não há dados válidos para plotar")
                    
                    elif chart_type == "Box Plot":
                        cols_to_plot = st.multiselect("Colunas:", numeric_columns, default=numeric_columns[:3], key=f"box_cols_{project_id}")
                        
                        if cols_to_plot:
                            fig = go.Figure()
                            for col in cols_to_plot:
                                valid_data = df[col].dropna()
                                if len(valid_data) > 0:
                                    fig.add_trace(go.Box(y=valid_data, name=col))
                            
                            fig.update_layout(title="Box Plot - Comparação", height=400)
                            st.plotly_chart(fig, use_container_width=True)
                    
                    elif chart_type == "Linha do Tempo":
                        y_col = st.selectbox("Eixo Y:", numeric_columns, key=f"line_y_{project_id}")
                        
                        valid_data = df[y_col].dropna()
                        if len(valid_data) > 0:
                            fig = px.line(x=range(len(valid_data)), y=valid_data, title=f"Série Temporal - {y_col}")
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("⚠️ Não há dados válidos para plotar")
                    
                    elif chart_type == "Scatter Plot":
                        if len(numeric_columns) >= 2:
                            col1, col2 = st.columns(2)
                            with col1:
                                x_col = st.selectbox("Eixo X:", numeric_columns, key=f"scatter_x_{project_id}")
                            with col2:
                                available_y_cols = [col for col in numeric_columns if col != x_col]
                                if available_y_cols:
                                    y_col = st.selectbox("Eixo Y:", available_y_cols, key=f"scatter_y_{project_id}")
                                    
                                    # Filtrar dados válidos para ambas as colunas
                                    df_scatter = df[[x_col, y_col]].dropna()
                                    if len(df_scatter) > 0:
                                        fig = px.scatter(df_scatter, x=x_col, y=y_col, title=f"Scatter Plot - {x_col} vs {y_col}")
                                        fig.update_layout(height=400)
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.warning("⚠️ Não há dados válidos para plotar")
                        else:
                            st.warning("⚠️ Necessário pelo menos 2 colunas numéricas para scatter plot")
                    
                    elif chart_type == "Correlação":
                        if len(numeric_columns) >= 2:
                            # Filtrar apenas dados válidos
                            df_corr = df[numeric_columns].dropna()
                            if len(df_corr) > 1:
                                corr_matrix = df_corr.corr()
                                
                                fig = px.imshow(corr_matrix, 
                                              text_auto=True, 
                                              aspect="auto",
                                              title="Matriz de Correlação",
                                              color_continuous_scale='RdBu_r')
                                fig.update_layout(height=400)
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("⚠️ Dados insuficientes para correlação")
                        else:
                            st.warning("⚠️ Necessário pelo menos 2 colunas numéricas para correlação")
                            
                except Exception as e:
                    st.error(f"❌ Erro ao criar gráfico: {str(e)}")
            else:
                st.warning("⚠️ Nenhuma coluna numérica encontrada para visualização")
        
        with tab4:
            st.markdown("#### 🔍 Análise de Qualidade dos Dados")
            
            # Valores faltantes
            st.markdown("##### 🕳️ Valores Faltantes")
            missing_data = df.isnull().sum()
            missing_percent = (missing_data / len(df)) * 100
            
            missing_df = pd.DataFrame({
                'Coluna': missing_data.index,
                'Valores Faltantes': missing_data.values,
                'Percentual (%)': missing_percent.values
            })
            
            missing_df = missing_df[missing_df['Valores Faltantes'] > 0]
            
            if not missing_df.empty:
                st.dataframe(missing_df, use_container_width=True)
                
                try:
                    fig = px.bar(missing_df, x='Coluna', y='Percentual (%)', 
                               title="Percentual de Valores Faltantes por Coluna")
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"⚠️ Erro ao criar gráfico: {str(e)}")
            else:
                st.success("✅ Nenhum valor faltante encontrado!")
            
            # Outliers
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_columns:
                st.markdown("##### 🎯 Detecção de Outliers (Método IQR)")
                
                outlier_col = st.selectbox("Selecione coluna para análise de outliers:", numeric_columns, key=f"outlier_col_{project_id}")
                
                try:
                    data_col = df[outlier_col].dropna()
                    
                    if len(data_col) > 0:
                        Q1 = data_col.quantile(0.25)
                        Q3 = data_col.quantile(0.75)
                        IQR = Q3 - Q1
                        
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        
                        outliers = data_col[(data_col < lower_bound) | (data_col > upper_bound)]
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total de Outliers", len(outliers))
                        
                        with col2:
                            st.metric("Limite Inferior", f"{lower_bound:.2f}")
                        
                        with col3:
                            st.metric("Limite Superior", f"{upper_bound:.2f}")
                        
                        if len(outliers) > 0:
                            st.warning(f"⚠️ {len(outliers)} outliers detectados")
                            
                            try:
                                fig = go.Figure()
                                fig.add_trace(go.Box(y=data_col, name=outlier_col, boxpoints='outliers'))
                                fig.update_layout(title=f"Box Plot - {outlier_col}", height=300)
                                st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.warning(f"⚠️ Erro ao criar box plot: {str(e)}")
                        else:
                            st.success("✅ Nenhum outlier detectado!")
                    else:
                        st.warning("⚠️ Coluna não possui dados válidos")
                        
                except Exception as e:
                    st.error(f"❌ Erro na análise de outliers: {str(e)}")
        
        # Botão para salvar análise
        st.divider()
        
        if st.button("💾 Salvar Análise de Dados", key=f"save_analysis_{project_id}", use_container_width=True):
            try:
                numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
                
                analysis_summary = {
                    'file_name': file_name,
                    'upload_date': datetime.now().isoformat(),
                    'rows': int(df.shape[0]),
                    'columns': int(df.shape[1]),
                    'numeric_columns': len(numeric_columns),
                    'missing_values': int(df.isnull().sum().sum()),
                    'column_info': [
                        {
                            'name': col,
                            'type': str(df[col].dtype),
                            'unique_values': int(df[col].nunique()),
                            'null_values': int(df[col].isnull().sum())
                        }
                        for col in df.columns
                    ]
                }
                
                update_data = {
                    f'measure.baseline_data.data': analysis_summary,
                    f'measure.baseline_data.completed': True,
                    f'measure.baseline_data.updated_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                project_manager = ProjectManager()
                
                with st.spinner("💾 Salvando análise..."):
                    success = project_manager.update_project(project_id, update_data)
                    
                    if success:
                        st.success("✅ Análise de dados salva com sucesso!")
                        st.balloons()
                    else:
                        st.error("❌ Erro ao salvar análise")
                        
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {str(e)}")



def show_process_capability(project_data: Dict):
    """Análise de Capacidade do Processo"""
    
    project_id = project_data.get('id')
    
    st.markdown("## 📐 Análise de Capacidade do Processo")
    st.markdown("Avalie se o processo é capaz de atender às especificações.")
    
    # Verificar se há dados carregados
    if f'uploaded_data_{project_id}' not in st.session_state:
        st.warning("⚠️ Primeiro faça upload dos dados na seção 'Upload e Análise de Dados'")
        return
    
    df = st.session_state[f'uploaded_data_{project_id}']
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_columns:
        st.error("❌ Nenhuma coluna numérica encontrada nos dados")
        return
    
    # Seleção da variável para análise
    st.markdown("### 🎯 Configuração da Análise")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_column = st.selectbox(
            "Selecione a variável para análise:",
            numeric_columns,
            key=f"capability_column_{project_id}"
        )
    
    with col2:
        analysis_type = st.selectbox(
            "Tipo de Especificação:",
            ["Bilateral (LSL e USL)", "Unilateral Superior (USL)", "Unilateral Inferior (LSL)"],
            key=f"spec_type_{project_id}"
        )
    
    # Configurar limites de especificação
    st.markdown("### 📏 Limites de Especificação")
    
    try:
        data_col = df[selected_column].dropna()
        
        if len(data_col) == 0:
            st.error("❌ A coluna selecionada não possui dados válidos")
            return
            
        data_min, data_max = data_col.min(), data_col.max()
        data_mean = data_col.mean()
        data_std = data_col.std()
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            if analysis_type in ["Bilateral (LSL e USL)", "Unilateral Inferior (LSL)"]:
                lsl = st.number_input(
                    "LSL (Limite Inferior de Especificação)",
                    value=float(data_min - data_std),
                    key=f"lsl_{project_id}",
                    help="Valor mínimo aceitável"
                )
            else:
                lsl = None
        
        with col4:
            if analysis_type in ["Bilateral (LSL e USL)", "Unilateral Superior (USL)"]:
                usl = st.number_input(
                    "USL (Limite Superior de Especificação)",
                    value=float(data_max + data_std),
                    key=f"usl_{project_id}",
                    help="Valor máximo aceitável"
                )
            else:
                usl = None
        
        with col5:
            target = st.number_input(
                "Valor Alvo (Target)",
                value=float(data_mean),
                key=f"target_{project_id}",
                help="Valor ideal do processo"
            )
        
        # Realizar análise de capacidade
        if st.button("🔍 Realizar Análise de Capacidade", key=f"run_capability_{project_id}"):
            
            # Calcular índices de capacidade
            results = calculate_capability_indices(data_col, lsl, usl, target)
            
            # Mostrar resultados
            st.markdown("### 📊 Resultados da Análise")
            
            # Métricas principais
            col6, col7, col8, col9 = st.columns(4)
            
            with col6:
                cp_value = results['Cp']
                st.metric("Cp", f"{cp_value:.3f}" if cp_value is not None else "N/A")
            
            with col7:
                cpk_value = results['Cpk']
                st.metric("Cpk", f"{cpk_value:.3f}" if cpk_value is not None else "N/A")
            
            with col8:
                pp_value = results['Pp']
                st.metric("Pp", f"{pp_value:.3f}" if pp_value is not None else "N/A")
            
            with col9:
                ppk_value = results['Ppk']
                st.metric("Ppk", f"{ppk_value:.3f}" if ppk_value is not None else "N/A")
            
            # Interpretação
            st.markdown("### 🎯 Interpretação dos Resultados")
            
            interpretation = "N/A"
            if cpk_value is not None:
                if cpk_value >= 1.33:
                    st.success("✅ **Processo Capaz** - Cpk ≥ 1.33")
                    interpretation = "Excelente"
                elif cpk_value >= 1.0:
                    st.warning("⚠️ **Processo Marginalmente Capaz** - 1.0 ≤ Cpk < 1.33")
                    interpretation = "Aceitável"
                else:
                    st.error("❌ **Processo Não Capaz** - Cpk < 1.0")
                    interpretation = "Inadequado"
            
            # Gráfico de capacidade
            st.markdown("### 📈 Gráfico de Capacidade")
            
            try:
                fig = create_capability_chart(data_col, lsl, usl, target, results)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"❌ Erro ao criar gráfico: {str(e)}")
            
            # Estatísticas detalhadas
            st.markdown("### 📋 Estatísticas Detalhadas")
            
            detailed_stats = pd.DataFrame({
                'Estatística': ['Média', 'Desvio Padrão', 'Mínimo', 'Máximo', 'Mediana', 'Q1', 'Q3'],
                'Valor': [
                    f"{data_mean:.4f}",
                    f"{data_std:.4f}",
                    f"{data_min:.4f}",
                    f"{data_max:.4f}",
                    f"{data_col.median():.4f}",
                    f"{data_col.quantile(0.25):.4f}",
                    f"{data_col.quantile(0.75):.4f}"
                ]
            })
            
            col10, col11 = st.columns(2)
            
            with col10:
                st.dataframe(detailed_stats, use_container_width=True)
            
            with col11:
                # Percentual dentro das especificações
                within_spec_pct = None
                
                if lsl is not None and usl is not None:
                    within_spec = ((data_col >= lsl) & (data_col <= usl)).sum()
                    within_spec_pct = (within_spec / len(data_col)) * 100
                    
                    st.metric("Dentro das Especificações", f"{within_spec_pct:.1f}%")
                    st.metric("Fora das Especificações", f"{100 - within_spec_pct:.1f}%")
                
                elif lsl is not None:
                    above_lsl = (data_col >= lsl).sum()
                    above_lsl_pct = (above_lsl / len(data_col)) * 100
                    st.metric("Acima do LSL", f"{above_lsl_pct:.1f}%")
                
                elif usl is not None:
                    below_usl = (data_col <= usl).sum()
                    below_usl_pct = (below_usl / len(data_col)) * 100
                    st.metric("Abaixo do USL", f"{below_usl_pct:.1f}%")
            
            # Salvar resultados
            capability_results = {
                'variable': selected_column,
                'analysis_type': analysis_type,
                'lsl': float(lsl) if lsl is not None else None,
                'usl': float(usl) if usl is not None else None,
                'target': float(target),
                'sample_size': len(data_col),
                'mean': float(data_mean),
                'std': float(data_std),
                'cp': float(cp_value) if cp_value is not None else None,
                'cpk': float(cpk_value) if cpk_value is not None else None,
                'pp': float(pp_value) if pp_value is not None else None,
                'ppk': float(ppk_value) if ppk_value is not None else None,
                'interpretation': interpretation,
                'within_spec_pct': float(within_spec_pct) if within_spec_pct is not None else None,
                'analysis_date': datetime.now().isoformat()
            }
            
            # Salvar no session_state
            st.session_state[f'capability_results_{project_id}'] = capability_results
            
            if st.button("💾 Salvar Análise de Capacidade", key=f"save_capability_{project_id}"):
                # Salvar no Firebase
                update_data = {
                    f'measure.process_capability.data': capability_results,
                    f'measure.process_capability.completed': True,
                    f'measure.process_capability.updated_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                project_manager = ProjectManager()
                
                with st.spinner("💾 Salvando..."):
                    try:
                        success = project_manager.update_project(project_id, update_data)
                        
                        if success:
                            st.success("✅ Análise de capacidade salva!")
                            st.balloons()
                        else:
                            st.error("❌ Erro ao salvar")
                            
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
                        
    except Exception as e:
        st.error(f"❌ Erro na análise: {str(e)}")


def calculate_capability_indices(data, lsl=None, usl=None, target=None):
    """Calcula índices de capacidade do processo"""
    
    try:
        mean = data.mean()
        std = data.std()
        
        results = {
            'Cp': None,
            'Cpk': None, 
            'Pp': None,
            'Ppk': None
        }
        
        # Cp e Pp (capacidade potencial)
        if lsl is not None and usl is not None and std > 0:
            results['Cp'] = (usl - lsl) / (6 * std)
            results['Pp'] = results['Cp']  # Para este caso simplificado
        
        # Cpk e Ppk (capacidade real)
        if std > 0:
            if lsl is not None and usl is not None:
                cpu = (usl - mean) / (3 * std)
                cpl = (mean - lsl) / (3 * std)
                results['Cpk'] = min(cpu, cpl)
                results['Ppk'] = results['Cpk']  # Para este caso simplificado
            
            elif usl is not None:
                results['Cpk'] = (usl - mean) / (3 * std)
                results['Ppk'] = results['Cpk']
            
            elif lsl is not None:
                results['Cpk'] = (mean - lsl) / (3 * std)
                results['Ppk'] = results['Cpk']
        
        return results
        
    except Exception as e:
        st.error(f"❌ Erro no cálculo dos índices: {str(e)}")
        return {'Cp': None, 'Cpk': None, 'Pp': None, 'Ppk': None}


def create_capability_chart(data, lsl=None, usl=None, target=None, results=None):
    """Cria gráfico de capacidade do processo"""
    
    try:
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Histograma com Especificações', 'Gráfico de Controle Individual'),
            vertical_spacing=0.1
        )
        
        # Histograma
        fig.add_trace(
            go.Histogram(x=data, nbinsx=30, name='Dados', opacity=0.7),
            row=1, col=1
        )
        
        # Linhas de especificação
        if lsl is not None:
            fig.add_vline(x=lsl, line_dash="dash", line_color="red", 
                         annotation_text="LSL", row=1, col=1)
        
        if usl is not None:
            fig.add_vline(x=usl, line_dash="dash", line_color="red", 
                         annotation_text="USL", row=1, col=1)
        
        if target is not None:
            fig.add_vline(x=target, line_dash="dot", line_color="green", 
                         annotation_text="Target", row=1, col=1)
        
        # Gráfico de controle individual
        fig.add_trace(
            go.Scatter(x=list(range(len(data))), y=data, mode='lines+markers', 
                      name='Valores Individuais', line=dict(color='blue')),
            row=2, col=1
        )
        
        # Linha da média
        mean_line = data.mean()
        fig.add_hline(y=mean_line, line_dash="solid", line_color="green", 
                     annotation_text="Média", row=2, col=1)
        
        # Limites de controle (±3σ)
        if data.std() > 0:
            ucl = mean_line + 3 * data.std()
            lcl = mean_line - 3 * data.std()
            
            fig.add_hline(y=ucl, line_dash="dash", line_color="orange", 
                         annotation_text="UCL", row=2, col=1)
            fig.add_hline(y=lcl, line_dash="dash", line_color="orange", 
                         annotation_text="LCL", row=2, col=1)
        
        fig.update_layout(height=600, title_text="Análise de Capacidade do Processo")
        
        return fig
        
    except Exception as e:
        st.error(f"❌ Erro ao criar gráfico: {str(e)}")
        return go.Figure()


def show_msa_analysis(project_data: Dict):
    """Análise do Sistema de Medição (MSA) - Versão Simplificada"""
    
    project_id = project_data.get('id')
    
    st.markdown("## 🎯 Análise do Sistema de Medição (MSA)")
    st.markdown("Avalie a repetibilidade e reprodutibilidade do sistema de medição.")
    
    # Explicação do MSA
    with st.expander("ℹ️ O que é MSA?"):
        st.markdown("""
        **Measurement System Analysis (MSA)** é uma metodologia estatística para avaliar a qualidade do sistema de medição.
        
        **Principais componentes:**
        - **Repetibilidade**: Variação quando o mesmo operador mede a mesma peça várias vezes
        - **Reprodutibilidade**: Variação entre diferentes operadores medindo a mesma peça
        - **R&R**: Repetibilidade e Reprodutibilidade combinadas
        
        **Critérios de aceitação:**
        - R&R < 10%: Sistema excelente
        - 10% ≤ R&R < 30%: Sistema aceitável
        - R&R ≥ 30%: Sistema inadequado
        """)
    
    # Configuração do estudo
    st.markdown("### ⚙️ Configuração do Estudo MSA")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_operators = st.number_input(
            "Número de Operadores",
            min_value=2,
            max_value=5,
            value=3,
            key=f"num_operators_{project_id}",
            help="Recomendado: 2-3 operadores"
        )
    
    with col2:
        num_parts = st.number_input(
            "Número de Peças",
            min_value=5,
            max_value=20,
            value=10,
            key=f"num_parts_{project_id}",
            help="Recomendado: 10 peças"
        )
    
    with col3:
        num_trials = st.number_input(
            "Número de Repetições",
            min_value=2,
            max_value=5,
            value=3,
            key=f"num_trials_{project_id}",
            help="Recomendado: 2-3 repetições"
        )
    
    # Template para coleta de dados
    st.markdown("### 📋 Template para Coleta de Dados")
    
    if st.button("📥 Gerar Template MSA", key=f"generate_template_{project_id}"):
        # Criar template
        template_data = []
        
        for operator in range(1, num_operators + 1):
            for part in range(1, num_parts + 1):
                for trial in range(1, num_trials + 1):
                    template_data.append({
                        'Operador': f'Operador_{operator}',
                        'Peça': f'Peça_{part}',
                        'Repetição': trial,
                        'Medição': ''  # Campo vazio para preenchimento
                    })
        
        template_df = pd.DataFrame(template_data)
        
        # Mostrar template
        st.dataframe(template_df.head(20), use_container_width=True)
        
        # Download do template
        csv_template = template_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Template CSV",
            data=csv_template,
            file_name=f"MSA_Template_{project_data.get('name', 'Projeto')}.csv",
            mime="text/csv",
            key=f"download_template_{project_id}"
        )
        
        st.info("💡 Preencha o campo 'Medição' com os valores coletados e faça upload do arquivo preenchido.")
    
    # Upload dos dados MSA
    st.markdown("### 📤 Upload dos Dados MSA")
    
    msa_file = st.file_uploader(
        "Upload do arquivo com dados MSA",
        type=['csv', 'xlsx', 'xls'],
        key=f"msa_upload_{project_id}",
        help="Use o template gerado acima ou um arquivo com colunas: Operador, Peça, Repetição, Medição"
    )
    
    if msa_file is not None:
        try:
            # Ler arquivo
            if msa_file.name.endswith('.csv'):
                msa_df = pd.read_csv(msa_file)
            else:
                msa_df = pd.read_excel(msa_file)
            
            # Validar estrutura
            required_columns = ['Operador', 'Peça', 'Repetição', 'Medição']
            missing_columns = [col for col in required_columns if col not in msa_df.columns]
            
            if missing_columns:
                st.error(f"❌ Colunas obrigatórias ausentes: {missing_columns}")
                return
            
            # Validar dados
            if msa_df['Medição'].isnull().any():
                st.warning("⚠️ Existem valores vazios na coluna 'Medição'")
                msa_df = msa_df.dropna(subset=['Medição'])
            
            # Converter Medição para numérico
            try:
                msa_df['Medição'] = pd.to_numeric(msa_df['Medição'])
            except:
                st.error("❌ A coluna 'Medição' deve conter apenas valores numéricos")
                return
            
            st.success(f"✅ Dados MSA carregados: {len(msa_df)} medições")
            
            # Realizar análise MSA
            st.markdown("### 📊 Análise MSA")
            
            try:
                msa_results = perform_msa_analysis(msa_df)
                
                # Mostrar resultados
                col4, col5, col6 = st.columns(3)
                
                with col4:
                    rr_pct = msa_results['rr_percent']
                    st.metric("R&R (%)", f"{rr_pct:.1f}%")
                    
                    if rr_pct < 10:
                        st.success("✅ Excelente")
                    elif rr_pct < 30:
                        st.warning("⚠️ Aceitável")
                    else:
                        st.error("❌ Inadequado")
                
                with col5:
                    st.metric("Repetibilidade (%)", f"{msa_results['repeatability_percent']:.1f}%")
                
                with col6:
                    st.metric("Reprodutibilidade (%)", f"{msa_results['reproducibility_percent']:.1f}%")
                
                # Gráficos MSA
                st.markdown("### 📈 Gráficos MSA")
                
                try:
                    fig_rr = create_msa_charts(msa_df, msa_results)
                    st.plotly_chart(fig_rr, use_container_width=True)
                except Exception as e:
                    st.warning(f"⚠️ Erro ao criar gráficos: {str(e)}")
                
                # Tabela ANOVA
                st.markdown("### 📋 Análise de Variância (ANOVA)")
                
                anova_df = pd.DataFrame({
                    'Fonte de Variação': ['Repetibilidade', 'Reprodutibilidade', 'R&R', 'Peças', 'Total'],
                    'Variância': [
                        msa_results['repeatability_var'],
                        msa_results['reproducibility_var'],
                        msa_results['rr_var'],
                        msa_results['part_var'],
                        msa_results['total_var']
                    ],
                    'Desvio Padrão': [
                        np.sqrt(max(0, msa_results['repeatability_var'])),
                        np.sqrt(max(0, msa_results['reproducibility_var'])),
                        np.sqrt(max(0, msa_results['rr_var'])),
                        np.sqrt(max(0, msa_results['part_var'])),
                        np.sqrt(max(0, msa_results['total_var']))
                    ],
                    '% Contribuição': [
                        msa_results['repeatability_percent'],
                        msa_results['reproducibility_percent'],
                        msa_results['rr_percent'],
                        msa_results['part_percent'],
                        100.0
                    ]
                })
                
                st.dataframe(anova_df, use_container_width=True)
                
                # Interpretação e recomendações
                st.markdown("### 🎯 Interpretação e Recomendações")
                
                interpretation = "N/A"
                if rr_pct < 10:
                    st.success("""
                    ✅ **Sistema de Medição Excelente**
                    
                    O sistema de medição é adequado para o processo. A variabilidade R&R é baixa e não compromete a análise do processo.
                    """)
                    interpretation = "Excelente"
                
                elif rr_pct < 30:
                    st.warning("""
                    ⚠️ **Sistema de Medição Aceitável**
                    
                    O sistema pode ser usado, mas considere melhorias:
                    - Treinamento adicional dos operadores
                    - Calibração mais frequente dos equipamentos
                    - Revisão dos procedimentos de medição
                    """)
                    interpretation = "Aceitável"
                
                else:
                    st.error("""
                    ❌ **Sistema de Medição Inadequado**
                    
                    O sistema precisa de melhorias significativas:
                    - Revisar completamente o procedimento de medição
                    - Substituir ou reparar equipamentos de medição
                    - Retreinar operadores
                    - Considerar automação da medição
                    """)
                    interpretation = "Inadequado"
                
                # Salvar resultados MSA
                if st.button("💾 Salvar Análise MSA", key=f"save_msa_{project_id}"):
                    msa_summary = {
                        'analysis_date': datetime.now().isoformat(),
                        'num_operators': int(num_operators),
                        'num_parts': int(num_parts),
                        'num_trials': int(num_trials),
                        'total_measurements': len(msa_df),
                        'rr_percent': float(msa_results['rr_percent']),
                        'repeatability_percent': float(msa_results['repeatability_percent']),
                        'reproducibility_percent': float(msa_results['reproducibility_percent']),
                        'part_percent': float(msa_results['part_percent']),
                        'interpretation': interpretation
                    }
                    
                    # Salvar no Firebase
                    update_data = {
                        f'measure.msa.data': msa_summary,
                        f'measure.msa.completed': True,
                        f'measure.msa.updated_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    project_manager = ProjectManager()
                    
                    with st.spinner("💾 Salvando..."):
                        try:
                            success = project_manager.update_project(project_id, update_data)
                            
                            if success:
                                st.success("✅ Análise MSA salva!")
                                st.balloons()
                            else:
                                st.error("❌ Erro ao salvar")
                                
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
                            
            except Exception as e:
                st.error(f"❌ Erro na análise MSA: {str(e)}")
                        
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")


def perform_msa_analysis(df):
    """Realiza análise MSA nos dados"""
    
    try:
        # Calcular médias por operador e peça
        part_means = df.groupby('Peça')['Medição'].mean()
        grand_mean = df['Medição'].mean()
        
        # Calcular variâncias com verificação de valores válidos
        # Repetibilidade (dentro do operador)
        repeatability_vars = df.groupby(['Operador', 'Peça'])['Medição'].var().dropna()
        repeatability_var = repeatability_vars.mean() if len(repeatability_vars) > 0 else 0
        
        # Reprodutibilidade (entre operadores)
        operator_part_means = df.groupby(['Operador', 'Peça'])['Medição'].mean().reset_index()
        reproducibility_vars = operator_part_means.groupby('Peça')['Medição'].var().dropna()
        reproducibility_var = reproducibility_vars.mean() if len(reproducibility_vars) > 0 else 0
        
        # Variância das peças
        part_var = part_means.var() if len(part_means) > 1 else 0
        
        # R&R
        rr_var = repeatability_var + reproducibility_var
        
        # Variância total
        total_var = df['Medição'].var()
        
        # Evitar divisão por zero
        if total_var <= 0:
            total_var = 1e-10
        
        # Converter para percentuais
        repeatability_percent = max(0, (repeatability_var / total_var) * 100)
        reproducibility_percent = max(0, (reproducibility_var / total_var) * 100)
        rr_percent = max(0, (rr_var / total_var) * 100)
        part_percent = max(0, (part_var / total_var) * 100)
        
        # Garantir que os percentuais não excedam 100%
        total_percent = repeatability_percent + reproducibility_percent + part_percent
        if total_percent > 100:
            factor = 100 / total_percent
            repeatability_percent *= factor
            reproducibility_percent *= factor
            part_percent *= factor
            rr_percent = repeatability_percent + reproducibility_percent
        
        return {
            'repeatability_var': max(0, repeatability_var),
            'reproducibility_var': max(0, reproducibility_var),
            'rr_var': max(0, rr_var),
            'part_var': max(0, part_var),
            'total_var': max(0, total_var),
            'repeatability_percent': repeatability_percent,
            'reproducibility_percent': reproducibility_percent,
            'rr_percent': rr_percent,
            'part_percent': part_percent
        }
        
    except Exception as e:
        st.error(f"❌ Erro na análise MSA: {str(e)}")
        # Retornar valores padrão em caso de erro
        return {
            'repeatability_var': 0,
            'reproducibility_var': 0,
            'rr_var': 0,
            'part_var': 0,
            'total_var': 1,
            'repeatability_percent': 0,
            'reproducibility_percent': 0,
            'rr_percent': 0,
            'part_percent': 100
        }


def create_msa_charts(df, results):
    """Cria gráficos para análise MSA"""
    
    try:
        # Gráfico de médias por operador e peça
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Médias por Operador e Peça', 'Ranges por Operador', 
                           'Distribuição dos Dados', 'Contribuição da Variância'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"type": "pie"}]]
        )
        
        # Gráfico 1: Médias por operador e peça
        for operator in df['Operador'].unique():
            operator_data = df[df['Operador'] == operator]
            means_by_part = operator_data.groupby('Peça')['Medição'].mean()
            
            fig.add_trace(
                go.Scatter(x=means_by_part.index, y=means_by_part.values, 
                          mode='lines+markers', name=str(operator)),
                row=1, col=1
            )
        
        # Gráfico 2: Ranges por operador
        ranges_by_operator = df.groupby(['Operador', 'Peça'])['Medição'].apply(lambda x: x.max() - x.min()).reset_index()
        
        for operator in ranges_by_operator['Operador'].unique():
            operator_ranges = ranges_by_operator[ranges_by_operator['Operador'] == operator]
            
            fig.add_trace(
                go.Scatter(x=operator_ranges['Peça'], y=operator_ranges['Medição'], 
                          mode='lines+markers', name=f"{operator} Range", showlegend=False),
                row=1, col=2
            )
        
        # Gráfico 3: Distribuição dos dados
        fig.add_trace(
            go.Histogram(x=df['Medição'], nbinsx=20, name='Distribuição', showlegend=False),
            row=2, col=1
        )
        
        # Gráfico 4: Pizza da contribuição da variância
        labels = ['Repetibilidade', 'Reprodutibilidade', 'Peças']
        values = [results['repeatability_percent'], 
                  results['reproducibility_percent'],
                  results['part_percent']]
        
        # Filtrar valores válidos
        valid_data = [(l, v) for l, v in zip(labels, values) if v > 0]
        if valid_data:
            valid_labels, valid_values = zip(*valid_data)
            
            fig.add_trace(
                go.Pie(labels=valid_labels, values=valid_values, name="Variância", showlegend=False),
                row=2, col=2
            )
        
        fig.update_layout(height=600, title_text="Análise MSA - Gráficos de Diagnóstico")
        
        return fig
        
    except Exception as e:
        st.warning(f"⚠️ Erro ao criar gráficos MSA: {str(e)}")
        return go.Figure()


def show_measure_tools(project_data: Dict):
    """Função principal para mostrar as ferramentas da fase Measure"""
    
    if not project_data:
        st.error("❌ Projeto não encontrado")
        return
    
    # Menu de ferramentas
    st.markdown("### 🔧 Ferramentas da Fase Measure")
    
    tool_options = {
        "data_plan": "📊 Plano de Coleta de Dados",
        "file_upload": "📁 Upload e Análise de Dados", 
        "capability": "📐 Capacidade do Processo",
        "msa": "🎯 MSA - Sistema de Medição",
        "baseline": "📈 Baseline e Métricas CTQ"
    }
    
    # Verificar status das ferramentas
    measure_data = project_data.get('measure', {})
    
    # Usar selectbox para navegação
    tool_names_with_status = []
    tool_keys = list(tool_options.keys())
    
    for key, name in tool_options.items():
        is_completed = measure_data.get(key, {}).get('completed', False)
        status_icon = "✅" if is_completed else "⏳"
        tool_names_with_status.append(f"{status_icon} {name}")
    
    selected_index = st.selectbox(
        "Selecione uma ferramenta:",
        range(len(tool_names_with_status)),
        format_func=lambda x: tool_names_with_status[x],
        key=f"measure_tool_selector_{project_data.get('id')}"
    )
    
    selected_tool = tool_keys[selected_index]
    
    st.divider()
    
    # Mostrar ferramenta selecionada
    if selected_tool == "data_plan":
        show_data_collection_plan(project_data)
    elif selected_tool == "file_upload":
        show_file_upload_analysis(project_data)
    elif selected_tool == "capability":
        show_process_capability(project_data)
    elif selected_tool == "msa":
        show_msa_analysis(project_data)
    elif selected_tool == "baseline":
        st.info("🚧 Baseline e Métricas CTQ - Em desenvolvimento")
    
    # Progresso geral da fase Measure
    st.divider()
    st.markdown("### 📊 Progresso da Fase Measure")
    
    total_tools = len(tool_options)
    completed_tools = sum(1 for tool_key in tool_options.keys() 
                        if measure_data.get(tool_key, {}).get('completed', False))
    
    progress = (completed_tools / total_tools) * 100
    
    col_prog1, col_prog2 = st.columns([3, 1])
    
    with col_prog1:
        st.progress(progress / 100)
        st.caption(f"{completed_tools}/{total_tools} ferramentas concluídas ({progress:.1f}%)")
    
    with col_prog2:
        if progress == 100:
            st.success("🎉 Completo!")
        else:
            st.info(f"⏳ {progress:.0f}%")
    
    if progress == 100:
        st.success("🎉 **Parabéns! Fase Measure concluída com sucesso!**")
        st.info("✨ Você pode avançar para a fase **Analyze** usando a navegação das fases.")
