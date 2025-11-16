import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List
from src.utils.project_manager import ProjectManager, DataSyncManager
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def show_data_collection_plan(project_data: Dict):
    """Plano de Coleta de Dados"""
    
    project_id = project_data.get('id')
    project_manager = ProjectManager()
    
    st.markdown("## 📊 Plano de Coleta de Dados")
    st.markdown("Defina **o que**, **como**, **quando** e **onde** coletar os dados do processo.")
    
    # Inicializar dados
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
    
    # Objetivo da coleta
    st.markdown("### 🎯 Objetivo da Coleta")
    collection_objective = st.text_area(
        "Objetivo Principal da Coleta *",
        value=plan_data.get('collection_objective', ''),
        placeholder="Ex: Medir a variabilidade do tempo de setup das máquinas...",
        height=80,
        key=f"collection_objective_{project_id}"
    )
    
    # Variáveis a medir
    st.markdown("### 📏 Variáveis a Medir")
    
    if 'variables' not in plan_data:
        plan_data['variables'] = []
    
    # Adicionar variável
    with st.expander("➕ Adicionar Variável"):
        col1, col2 = st.columns(2)
        with col1:
            var_name = st.text_input("Nome da Variável", key=f"var_name_{project_id}")
            var_type = st.selectbox("Tipo", ["Contínua", "Discreta", "Categórica"], key=f"var_type_{project_id}")
        with col2:
            var_unit = st.text_input("Unidade", key=f"var_unit_{project_id}")
            var_target = st.text_input("Meta", key=f"var_target_{project_id}")
        
        if st.button("➕ Adicionar", key=f"add_var_{project_id}"):
            if var_name.strip():
                plan_data['variables'].append({
                    'name': var_name.strip(),
                    'type': var_type,
                    'unit': var_unit,
                    'target': var_target
                })
                st.session_state[plan_key] = plan_data
                st.rerun()
    
    # Mostrar variáveis
    if plan_data['variables']:
        for i, var in enumerate(plan_data['variables']):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{var['name']}** ({var['type']}) - {var['unit']} - Meta: {var['target']}")
            with col2:
                if st.button("🗑️", key=f"remove_var_{i}_{project_id}"):
                    plan_data['variables'].pop(i)
                    st.session_state[plan_key] = plan_data
                    st.rerun()
    
    # Método e cronograma
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔧 Método de Coleta")
        collection_method = st.selectbox(
            "Método Principal",
            ["Medição Direta", "Observação", "Sistema Automatizado", "Formulário"],
            key=f"collection_method_{project_id}"
        )
        responsible_person = st.text_input(
            "Responsável",
            value=plan_data.get('responsible_person', ''),
            key=f"responsible_person_{project_id}"
        )
    
    with col2:
        st.markdown("### 📅 Cronograma")
        start_date = st.date_input("Data Início", key=f"start_date_{project_id}")
        sample_size = st.number_input("Tamanho da Amostra", value=30, min_value=1, key=f"sample_size_{project_id}")
    
    # Botões
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Salvar", key=f"save_plan_{project_id}"):
            _save_tool_data(project_id, 'data_collection_plan', {
                'collection_objective': collection_objective,
                'variables': plan_data['variables'],
                'collection_method': collection_method,
                'responsible_person': responsible_person,
                'start_date': start_date.isoformat(),
                'sample_size': sample_size
            }, False)
            st.success("💾 Salvo!")
    
    with col2:
        if st.button("✅ Finalizar", key=f"complete_plan_{project_id}"):
            if collection_objective.strip() and plan_data['variables'] and responsible_person.strip():
                _save_tool_data(project_id, 'data_collection_plan', {
                    'collection_objective': collection_objective,
                    'variables': plan_data['variables'],
                    'collection_method': collection_method,
                    'responsible_person': responsible_person,
                    'start_date': start_date.isoformat(),
                    'sample_size': sample_size
                }, True)
                st.success("✅ Finalizado!")
                st.balloons()
            else:
                st.error("❌ Preencha todos os campos obrigatórios")


def show_file_upload_analysis(project_data: Dict):
    """Upload e Análise de Dados - VERSÃO INTEGRADA COM FIREBASE"""
    
    project_id = project_data.get('id')
    project_manager = ProjectManager()
    sync_manager = DataSyncManager(project_id)
    
    st.markdown("## 📁 Upload e Análise de Dados")
    st.markdown("Faça upload dos dados do processo para análise estatística.")
    
    # Verificar se já existem dados carregados
    existing_data = project_manager.get_uploaded_data(project_id)
    upload_info = project_manager.get_upload_info(project_id)
    
    # Status do upload
    is_completed = project_data.get('measure', {}).get('file_upload', {}).get('completed', False)
    
    if existing_data is not None and is_completed:
        st.success("✅ **Dados já carregados e salvos no projeto**")
        
        # Mostrar informações do arquivo atual
        if upload_info:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📄 Arquivo", upload_info.get('filename', 'N/A'))
            
            with col2:
                shape = upload_info.get('shape', [0, 0])
                st.metric("📊 Dimensões", f"{shape[0]} × {shape[1]}")
            
            with col3:
                st.metric("📈 Colunas Numéricas", upload_info.get('data_summary', {}).get('numeric_columns', 0))
            
            with col4:
                upload_date = upload_info.get('uploaded_at', '')[:10] if upload_info.get('uploaded_at') else 'N/A'
                st.metric("📅 Upload", upload_date)
        
        # Opção para substituir dados
        if st.checkbox("🔄 Substituir dados existentes", key=f"replace_data_{project_id}"):
            st.warning("⚠️ **Atenção:** Isso substituirá os dados atuais e pode afetar análises já realizadas.")
            show_upload_interface = True
        else:
            show_upload_interface = False
            # Mostrar dados existentes
            _show_data_analysis(existing_data, project_id, upload_info)
    else:
        show_upload_interface = True
    
    # Interface de upload
    if show_upload_interface:
        st.markdown("### 📤 Upload de Arquivo")
        
        # Upload
        uploaded_file = st.file_uploader(
            "Escolha um arquivo de dados",
            type=['csv', 'xlsx', 'xls'],
            key=f"file_upload_{project_id}",
            help="Formatos suportados: CSV, Excel (.xlsx, .xls)"
        )
        
        if uploaded_file is not None:
            try:
                with st.spinner("Processando arquivo..."):
                    # Ler arquivo
                    if uploaded_file.name.endswith('.csv'):
                        # Tentar diferentes encodings para CSV
                        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                        df = None
                        
                        for encoding in encodings:
                            try:
                                df = pd.read_csv(uploaded_file, encoding=encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                        
                        if df is None:
                            st.error("❌ Erro de codificação. Tente salvar o CSV em UTF-8.")
                            return
                    else:
                        df = pd.read_excel(uploaded_file)
                
                # Validações básicas
                if df.empty:
                    st.error("❌ Arquivo vazio")
                    return
                
                if len(df.columns) == 0:
                    st.error("❌ Nenhuma coluna encontrada")
                    return
                
                # Salvar usando o ProjectManager
                success = project_manager.save_uploaded_data(
                    project_id=project_id,
                    dataframe=df,
                    filename=uploaded_file.name,
                    additional_info={
                        'file_size': uploaded_file.size,
                        'upload_method': 'streamlit_uploader'
                    }
                )
                
                if success:
                    st.success(f"✅ **Arquivo carregado com sucesso:** {uploaded_file.name}")
                    
                    # Mostrar informações básicas
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("📊 Linhas", df.shape[0])
                    
                    with col2:
                        st.metric("📋 Colunas", df.shape[1])
                    
                    with col3:
                        numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
                        st.metric("📈 Numéricas", numeric_cols)
                    
                    with col4:
                        categorical_cols = len(df.select_dtypes(include=['object']).columns)
                        st.metric("📝 Categóricas", categorical_cols)
                    
                    # Mostrar análise dos dados
                    _show_data_analysis(df, project_id, project_manager.get_upload_info(project_id))
                    
                    # Rerun para atualizar a interface
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar dados no projeto")
                
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {str(e)}")
                st.info("💡 **Dicas:**")
                st.write("• Verifique se o arquivo não está corrompido")
                st.write("• Para CSV, tente salvar com codificação UTF-8")
                st.write("• Verifique se há caracteres especiais nos nomes das colunas")


def _show_data_analysis(df: pd.DataFrame, project_id: str, upload_info: Dict = None):
    """Mostra análise dos dados carregados"""
    
    st.markdown("### 📊 Análise dos Dados Carregados")
    
    # Verificações de qualidade dos dados
    _show_data_quality_check(df)
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👀 Visualização", 
        "📈 Estatísticas", 
        "📊 Gráficos", 
        "🔍 Qualidade",
        "💾 Ações"
    ])
    
    with tab1:
        st.markdown("#### 📋 Primeiras 10 linhas")
        st.dataframe(df.head(10), use_container_width=True)
        
        if len(df) > 10:
            st.info(f"💡 Mostrando 10 de {len(df)} linhas. Use as outras abas para análise completa.")
        
        # Informações sobre colunas
        st.markdown("#### 📊 Informações das Colunas")
        
        col_info = []
        for col in df.columns:
            col_data = df[col]
            col_info.append({
                'Coluna': col,
                'Tipo': str(col_data.dtype),
                'Não Nulos': col_data.count(),
                'Nulos': col_data.isnull().sum(),
                '% Nulos': f"{(col_data.isnull().sum() / len(df) * 100):.1f}%",
                'Únicos': col_data.nunique()
            })
        
        col_info_df = pd.DataFrame(col_info)
        st.dataframe(col_info_df, use_container_width=True)
    
    with tab2:
        st.markdown("#### 📈 Estatísticas Descritivas")
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        if numeric_columns:
            st.markdown("**Variáveis Numéricas:**")
            
            # Seleção de colunas para análise
            selected_numeric = st.multiselect(
                "Selecione colunas numéricas:",
                numeric_columns,
                default=numeric_columns[:5],  # Máximo 5 para não sobrecarregar
                key=f"selected_numeric_{project_id}"
            )
            
            if selected_numeric:
                desc_stats = df[selected_numeric].describe()
                st.dataframe(desc_stats, use_container_width=True)
                
                # Estatísticas adicionais
                st.markdown("**Estatísticas Adicionais:**")
                additional_stats = []
                
                for col in selected_numeric:
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        additional_stats.append({
                            'Coluna': col,
                            'Assimetria': stats.skew(col_data),
                            'Curtose': stats.kurtosis(col_data),
                            'CV (%)': (col_data.std() / col_data.mean() * 100) if col_data.mean() != 0 else 0
                        })
                
                if additional_stats:
                    st.dataframe(pd.DataFrame(additional_stats), use_container_width=True)
        else:
            st.info("📊 Nenhuma coluna numérica encontrada")
        
        if categorical_columns:
            st.markdown("**Variáveis Categóricas:**")
            
            selected_categorical = st.selectbox(
                "Selecione uma coluna categórica:",
                categorical_columns,
                key=f"selected_categorical_{project_id}"
            )
            
            if selected_categorical:
                value_counts = df[selected_categorical].value_counts()
                st.write(f"**Distribuição de {selected_categorical}:**")
                
                # Criar DataFrame para melhor visualização
                freq_df = pd.DataFrame({
                    'Valor': value_counts.index,
                    'Frequência': value_counts.values,
                    'Percentual': (value_counts.values / len(df) * 100).round(1)
                })
                
                st.dataframe(freq_df, use_container_width=True)
    
    with tab3:
        st.markdown("#### 📊 Visualizações")
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_columns:
            st.warning("⚠️ Nenhuma coluna numérica para gráficos")
            return
        
        # Tipo de gráfico
        chart_type = st.selectbox(
            "Tipo de Gráfico:",
            ["Histograma", "Box Plot", "Scatter Plot", "Correlação", "Série Temporal"],
            key=f"chart_type_{project_id}"
        )
        
        if chart_type == "Histograma":
            col_to_plot = st.selectbox("Coluna:", numeric_columns, key=f"hist_col_{project_id}")
            
            bins = st.slider("Número de bins:", 10, 100, 30, key=f"hist_bins_{project_id}")
            
            fig = px.histogram(df, x=col_to_plot, nbins=bins, title=f"Histograma - {col_to_plot}")
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Box Plot":
            cols_to_plot = st.multiselect(
                "Colunas:", 
                numeric_columns, 
                default=numeric_columns[:3],
                key=f"box_cols_{project_id}"
            )
            
            if cols_to_plot:
                fig = go.Figure()
                for col in cols_to_plot:
                    fig.add_trace(go.Box(y=df[col], name=col))
                
                fig.update_layout(title="Box Plot Comparativo", height=500)
                st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Scatter Plot":
            if len(numeric_columns) >= 2:
                col1, col2 = st.columns(2)
                
                with col1:
                    x_col = st.selectbox("Eixo X:", numeric_columns, key=f"scatter_x_{project_id}")
                
                with col2:
                    y_options = [col for col in numeric_columns if col != x_col]
                    y_col = st.selectbox("Eixo Y:", y_options, key=f"scatter_y_{project_id}")
                
                fig = px.scatter(df, x=x_col, y=y_col, title=f"Scatter: {x_col} vs {y_col}")
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Necessário pelo menos 2 colunas numéricas")
        
        elif chart_type == "Correlação":
            if len(numeric_columns) >= 2:
                corr_cols = st.multiselect(
                    "Colunas para correlação:",
                    numeric_columns,
                    default=numeric_columns[:5],
                    key=f"corr_cols_{project_id}"
                )
                
                if len(corr_cols) >= 2:
                    corr_matrix = df[corr_cols].corr()
                    
                    fig = px.imshow(
                        corr_matrix,
                        text_auto=True,
                        aspect="auto",
                        title="Matriz de Correlação",
                        color_continuous_scale='RdBu_r'
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Necessário pelo menos 2 colunas numéricas")
        
        elif chart_type == "Série Temporal":
            time_col = st.selectbox("Coluna para série temporal:", numeric_columns, key=f"time_col_{project_id}")
            
            fig = px.line(x=range(len(df)), y=df[time_col], title=f"Série Temporal - {time_col}")
            fig.update_xaxes(title="Observação")
            fig.update_yaxes(title=time_col)
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown("#### 🔍 Análise de Qualidade dos Dados")
        _show_detailed_quality_analysis(df)
    
    with tab5:
        st.markdown("#### 💾 Ações com os Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Download dos dados processados
            if st.button("📥 Download CSV", key=f"download_csv_{project_id}"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Baixar arquivo CSV",
                    data=csv,
                    file_name=f"dados_processados_{project_id}.csv",
                    mime="text/csv"
                )
        
        with col2:
            # Informações sobre o upload
            if upload_info:
                st.info(f"📄 **Arquivo original:** {upload_info.get('filename', 'N/A')}")
                st.info(f"📅 **Data do upload:** {upload_info.get('uploaded_at', 'N/A')[:19]}")


def _show_data_quality_check(df: pd.DataFrame):
    """Verificação rápida da qualidade dos dados"""
    
    # Métricas de qualidade
    total_cells = df.shape[0] * df.shape[1]
    missing_cells = df.isnull().sum().sum()
    missing_percentage = (missing_cells / total_cells) * 100
    
    # Duplicatas
    duplicates = df.duplicated().sum()
    duplicate_percentage = (duplicates / len(df)) * 100
    
    # Status geral
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if missing_percentage < 5:
            st.success(f"✅ Dados Faltantes: {missing_percentage:.1f}%")
        elif missing_percentage < 15:
            st.warning(f"⚠️ Dados Faltantes: {missing_percentage:.1f}%")
        else:
            st.error(f"❌ Dados Faltantes: {missing_percentage:.1f}%")
    
    with col2:
        if duplicate_percentage < 1:
            st.success(f"✅ Duplicatas: {duplicate_percentage:.1f}%")
        elif duplicate_percentage < 5:
            st.warning(f"⚠️ Duplicatas: {duplicate_percentage:.1f}%")
        else:
            st.error(f"❌ Duplicatas: {duplicate_percentage:.1f}%")
    
    with col3:
        numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
        if numeric_cols > 0:
            st.success(f"✅ Colunas Numéricas: {numeric_cols}")
        else:
            st.warning("⚠️ Nenhuma coluna numérica")
    
    with col4:
        if len(df) >= 30:
            st.success(f"✅ Amostra: {len(df)} registros")
        elif len(df) >= 10:
            st.warning(f"⚠️ Amostra pequena: {len(df)}")
        else:
            st.error(f"❌ Amostra muito pequena: {len(df)}")


def _show_detailed_quality_analysis(df: pd.DataFrame):
    """Análise detalhada da qualidade dos dados"""
    
    st.markdown("##### 📊 Resumo de Qualidade")
    
    quality_issues = []
    
    # Análise por coluna
    for col in df.columns:
        col_data = df[col]
        issues = []
        
        # Dados faltantes
        missing_pct = (col_data.isnull().sum() / len(df)) * 100
        if missing_pct > 10:
            issues.append(f"Dados faltantes: {missing_pct:.1f}%")
        
        # Valores únicos (possível problema de cardinalidade)
        unique_pct = (col_data.nunique() / len(df)) * 100
        if unique_pct > 95:
            issues.append("Alta cardinalidade (possível ID)")
        elif unique_pct < 5 and col_data.dtype == 'object':
            issues.append("Baixa cardinalidade")
        
        # Para colunas numéricas
        if pd.api.types.is_numeric_dtype(col_data):
            # Outliers usando IQR
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            
            if IQR > 0:
                outliers = col_data[(col_data < Q1 - 1.5 * IQR) | (col_data > Q3 + 1.5 * IQR)]
                outlier_pct = (len(outliers) / len(col_data.dropna())) * 100
                
                if outlier_pct > 5:
                    issues.append(f"Outliers: {outlier_pct:.1f}%")
        
        if issues:
            quality_issues.append({
                'Coluna': col,
                'Problemas': '; '.join(issues)
            })
    
    if quality_issues:
        st.markdown("**⚠️ Problemas de Qualidade Identificados:**")
        quality_df = pd.DataFrame(quality_issues)
        st.dataframe(quality_df, use_container_width=True)
    else:
        st.success("✅ Nenhum problema significativo de qualidade identificado")
    
    # Recomendações
    st.markdown("##### 💡 Recomendações")
    
    recommendations = []
    
    missing_cols = [col for col in df.columns if df[col].isnull().sum() > 0]
    if missing_cols:
        recommendations.append("🔧 **Dados faltantes:** Considere estratégias de imputação ou remoção")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        recommendations.append("📊 **Análise estatística:** Dados numéricos disponíveis para análise avançada")
    
    if df.duplicated().sum() > 0:
        recommendations.append("🧹 **Duplicatas:** Remova registros duplicados se não forem intencionais")
    
    if len(df) < 30:
        recommendations.append("⚠️ **Amostra pequena:** Considere coletar mais dados para análises robustas")
    
    for rec in recommendations:
        st.write(rec)


def show_process_capability(project_data: Dict):
    """Análise de Capacidade do Processo - VERSÃO MELHORADA"""
    
    project_id = project_data.get('id')
    project_manager = ProjectManager()
    
    st.markdown("## 📐 Análise de Capacidade do Processo")
    st.markdown("Avalie se o processo é capaz de atender às especificações definidas.")
    
    # Verificar se há dados
    df = project_manager.get_uploaded_data(project_id)
    
    if df is None:
        st.warning("⚠️ **Dados não encontrados**")
        st.info("Primeiro faça upload dos dados na ferramenta **Upload e Análise de Dados**")
        
        if st.button("📁 Ir para Upload de Dados", key=f"goto_upload_{project_id}"):
            st.rerun()
        return
    
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_columns:
        st.error("❌ Nenhuma coluna numérica encontrada nos dados")
        return
    
    # Status
    is_completed = project_data.get('measure', {}).get('process_capability', {}).get('completed', False)
    if is_completed:
        st.success("✅ Análise de capacidade finalizada")
    else:
        st.info("⏳ Análise em desenvolvimento")
    
    # Configuração da análise
    st.markdown("### ⚙️ Configuração da Análise")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_column = st.selectbox(
            "Variável para análise:",
            numeric_columns,
            key=f"cap_col_{project_id}",
            help="Selecione a variável crítica para qualidade (CTQ)"
        )
    
    with col2:
        spec_type = st.selectbox(
            "Tipo de Especificação:",
            ["Bilateral", "Superior apenas", "Inferior apenas"],
            key=f"spec_type_{project_id}",
            help="Bilateral: LSL e USL | Superior: apenas USL | Inferior: apenas LSL"
        )
    
    # Dados da variável selecionada
    data_col = df[selected_column].dropna()
    
    if len(data_col) == 0:
        st.error("❌ Coluna selecionada não possui dados válidos")
        return
    
    # Estatísticas básicas
    mean_val = data_col.mean()
    std_val = data_col.std()
    
    st.markdown("### 📊 Estatísticas da Variável")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Média", f"{mean_val:.4f}")
    
    with col2:
        st.metric("Desvio Padrão", f"{std_val:.4f}")
    
    with col3:
        st.metric("Mínimo", f"{data_col.min():.4f}")
    
    with col4:
        st.metric("Máximo", f"{data_col.max():.4f}")
    
    # Definição dos limites de especificação
    st.markdown("### 🎯 Limites de Especificação")
    
    col3, col4 = st.columns(2)
    
    with col3:
        if spec_type in ["Bilateral", "Inferior apenas"]:
            lsl = st.number_input(
                "LSL (Limite Superior de Especificação):",
                value=float(mean_val - 3*std_val),
                key=f"lsl_{project_id}",
                help="Valor mínimo aceitável"
            )
        else:
            lsl = None
    
    with col4:
        if spec_type in ["Bilateral", "Superior apenas"]:
            usl = st.number_input(
                "USL (Limite Superior de Especificação):",
                value=float(mean_val + 3*std_val),
                key=f"usl_{project_id}",
                help="Valor máximo aceitável"
            )
        else:
            usl = None
    
    # Executar análise
    if st.button("🔍 Analisar Capacidade", key=f"analyze_cap_{project_id}", type="primary"):
        
        with st.spinner("Calculando índices de capacidade..."):
            # Calcular índices
            results = _calculate_capability_advanced(data_col, lsl, usl)
            
            # Mostrar resultados principais
            st.markdown("### 📈 Resultados da Análise")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if results['Cp'] is not None:
                    st.metric("Cp (Capacidade Potencial)", f"{results['Cp']:.3f}")
                else:
                    st.metric("Cp", "N/A")
            
            with col2:
                if results['Cpk'] is not None:
                    st.metric("Cpk (Capacidade Real)", f"{results['Cpk']:.3f}")
                else:
                    st.metric("Cpk", "N/A")
            
            with col3:
                if results['Pp'] is not None:
                    st.metric("Pp (Performance Potencial)", f"{results['Pp']:.3f}")
                else:
                    st.metric("Pp", "N/A")
            
            with col4:
                if results['Ppk'] is not None:
                    st.metric("Ppk (Performance Real)", f"{results['Ppk']:.3f}")
                else:
                    st.metric("Ppk", "N/A")
            
            # Interpretação dos resultados
            st.markdown("### 🎯 Interpretação dos Resultados")
            
            if results['Cpk'] is not None:
                cpk_value = results['Cpk']
                
                if cpk_value >= 2.0:
                    st.success("🟢 **Excelente:** Processo altamente capaz (Cpk ≥ 2.0)")
                    capability_status = "Excelente"
                elif cpk_value >= 1.33:
                    st.success("🟢 **Capaz:** Processo capaz (1.33 ≤ Cpk < 2.0)")
                    capability_status = "Capaz"
                elif cpk_value >= 1.0:
                    st.warning("🟡 **Marginal:** Processo marginalmente capaz (1.0 ≤ Cpk < 1.33)")
                    capability_status = "Marginal"
                else:
                    st.error("🔴 **Não Capaz:** Processo não capaz (Cpk < 1.0)")
                    capability_status = "Não Capaz"
            else:
                capability_status = "Indeterminado"
            
            # Gráfico de capacidade
            st.markdown("### 📊 Visualização da Capacidade")
            
            fig = go.Figure()
            
            # Histograma dos dados
            fig.add_trace(go.Histogram(
                x=data_col,
                nbinsx=30,
                name="Distribuição dos Dados",
                opacity=0.7,
                marker_color='lightblue'
            ))
            
            # Curva normal teórica
            x_range = np.linspace(data_col.min(), data_col.max(), 100)
            normal_curve = stats.norm.pdf(x_range, mean_val, std_val) * len(data_col) * (data_col.max() - data_col.min()) / 30
            
            fig.add_trace(go.Scatter(
                x=x_range,
                y=normal_curve,
                mode='lines',
                name='Distribuição Normal',
                line=dict(color='blue', width=2)
            ))
            
            # Limites de especificação
            if lsl is not None:
                fig.add_vline(
                    x=lsl,
                    line_dash="dash",
                    line_color="red",
                    line_width=3,
                    annotation_text="LSL"
                )
            
            if usl is not None:
                fig.add_vline(
                    x=usl,
                    line_dash="dash",
                    line_color="red",
                    line_width=3,
                    annotation_text="USL"
                )
            
            # Média do processo
            fig.add_vline(
                x=mean_val,
                line_dash="dot",
                line_color="green",
                line_width=2,
                annotation_text="Média"
            )
            
            fig.update_layout(
                title=f"Análise de Capacidade - {selected_column}",
                xaxis_title=selected_column,
                yaxis_title="Frequência",
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas detalhadas
            st.markdown("### 📋 Estatísticas Detalhadas")
            
            detailed_stats = {
                'Métrica': ['Média do Processo', 'Desvio Padrão', 'LSL', 'USL', 'Amplitude Spec.'],
                'Valor': [
                    f"{mean_val:.4f}",
                    f"{std_val:.4f}",
                    f"{lsl:.4f}" if lsl is not None else "N/A",
                    f"{usl:.4f}" if usl is not None else "N/A",
                    f"{usl - lsl:.4f}" if (lsl is not None and usl is not None) else "N/A"
                ]
            }
            
            if results['defect_rate'] is not None:
                detailed_stats['Métrica'].extend(['Taxa de Defeitos', 'PPM Defeitos'])
                detailed_stats['Valor'].extend([
                    f"{results['defect_rate']:.4f}%",
                    f"{results['defect_rate'] * 10000:.0f}"
                ])
            
            st.dataframe(pd.DataFrame(detailed_stats), use_container_width=True)
            
            # Recomendações
            st.markdown("### 💡 Recomendações")
            
            recommendations = []
            
            if results['Cpk'] is not None:
                if results['Cpk'] < 1.0:
                    recommendations.extend([
                        "🔧 **Melhoria urgente necessária** - Processo não capaz",
                        "📊 **Reduzir variabilidade** do processo",
                        "🎯 **Centralizar processo** se média estiver deslocada"
                    ])
                elif results['Cpk'] < 1.33:
                    recommendations.extend([
                        "⚠️ **Monitoramento próximo** recomendado",
                        "📈 **Considerar melhorias** para aumentar capacidade"
                    ])
                else:
                    recommendations.append("✅ **Manter controle atual** - Processo capaz")
            
            if results['Cp'] is not None and results['Cpk'] is not None:
                if results['Cp'] > results['Cpk'] + 0.1:
                    recommendations.append("🎯 **Centralizar processo** - Cp >> Cpk indica descentramento")
            
            for rec in recommendations:
                st.write(rec)
            
            # Salvar resultados
            if st.button("💾 Salvar Análise de Capacidade", key=f"save_cap_{project_id}"):
                cap_data = {
                    'variable': selected_column,
                    'spec_type': spec_type,
                    'lsl': float(lsl) if lsl is not None else None,
                    'usl': float(usl) if usl is not None else None,
                    'process_mean': float(mean_val),
                    'process_std': float(std_val),
                    'sample_size': int(len(data_col)),
                    'cp': float(results['Cp']) if results['Cp'] is not None else None,
                    'cpk': float(results['Cpk']) if results['Cpk'] is not None else None,
                    'pp': float(results['Pp']) if results['Pp'] is not None else None,
                    'ppk': float(results['Ppk']) if results['Ppk'] is not None else None,
                    'defect_rate': float(results['defect_rate']) if results['defect_rate'] is not None else None,
                    'capability_status': capability_status,
                    'analysis_date': datetime.now().isoformat()
                }
                
                success = _save_tool_data(project_id, 'process_capability', cap_data, True)
                if success:
                    st.success("✅ Análise de capacidade salva com sucesso!")
                    st.balloons()


def _calculate_capability_advanced(data, lsl=None, usl=None):
    """Calcular índices de capacidade avançados"""
    try:
        mean_val = data.mean()
        std_val = data.std()
        n = len(data)
        
        results = {
            'Cp': None, 'Cpk': None, 'Pp': None, 'Ppk': None,
            'defect_rate': None, 'sigma_level': None
        }
        
        # Cp e Cpk (baseados em desvio padrão within)
        if lsl is not None and usl is not None and std_val > 0:
            results['Cp'] = (usl - lsl) / (6 * std_val)
            cpu = (usl - mean_val) / (3 * std_val)
            cpl = (mean_val - lsl) / (3 * std_val)
            results['Cpk'] = min(cpu, cpl)
            
            # Pp e Ppk (baseados em desvio padrão total)
            results['Pp'] = (usl - lsl) / (6 * std_val)
            results['Ppk'] = results['Cpk']  # Simplificado
            
        elif usl is not None and std_val > 0:
            results['Cpk'] = (usl - mean_val) / (3 * std_val)
            results['Ppk'] = results['Cpk']
            
        elif lsl is not None and std_val > 0:
            results['Cpk'] = (mean_val - lsl) / (3 * std_val)
            results['Ppk'] = results['Cpk']
        
        # Taxa de defeitos
        if lsl is not None or usl is not None:
            defects = 0
            
            if lsl is not None:
                defects += sum(data < lsl)
            
            if usl is not None:
                defects += sum(data > usl)
            
            results['defect_rate'] = (defects / len(data)) * 100
        
        return results
        
    except Exception as e:
        st.error(f"Erro no cálculo: {str(e)}")
        return {'Cp': None, 'Cpk': None, 'Pp': None, 'Ppk': None, 'defect_rate': None}


# Manter as outras funções (MSA, baseline) como estavam
def show_msa_analysis(project_data: Dict):
    """MSA - Análise do Sistema de Medição - VERSÃO SIMPLIFICADA"""
    
    project_id = project_data.get('id')
    
    st.markdown("## 🎯 MSA - Sistema de Medição")
    
    st.info("""
    **MSA (Measurement System Analysis)**
    
    Avalia a qualidade do sistema de medição através de:
    - **Repetibilidade**: Variação do mesmo operador
    - **Reprodutibilidade**: Variação entre operadores
    - **R&R**: Combinação de ambos
    """)
    
    # Configuração básica
    col1, col2, col3 = st.columns(3)
    with col1:
        num_operators = st.number_input("Operadores", min_value=2, max_value=5, value=3, key=f"ops_{project_id}")
    with col2:
        num_parts = st.number_input("Peças", min_value=5, max_value=20, value=10, key=f"parts_{project_id}")
    with col3:
        num_trials = st.number_input("Repetições", min_value=2, max_value=5, value=3, key=f"trials_{project_id}")
    
    # Gerar template
    if st.button("📥 Gerar Template MSA", key=f"gen_template_{project_id}"):
        template_data = []
        for op in range(1, num_operators + 1):
            for part in range(1, num_parts + 1):
                for trial in range(1, num_trials + 1):
                    template_data.append({
                        'Operador': f'Op_{op}',
                        'Peça': f'Peça_{part}',
                        'Repetição': trial,
                        'Medição': ''
                    })
        
        template_df = pd.DataFrame(template_data)
        st.dataframe(template_df.head(15))
        
        csv = template_df.to_csv(index=False)
        st.download_button(
            "📥 Download Template",
            csv,
            f"MSA_Template_{project_data.get('name', 'Projeto')}.csv",
            "text/csv"
        )
    
    # Upload MSA
    msa_file = st.file_uploader("Upload dados MSA", type=['csv', 'xlsx'], key=f"msa_upload_{project_id}")
    
    if msa_file:
        try:
            if msa_file.name.endswith('.csv'):
                msa_df = pd.read_csv(msa_file)
            else:
                msa_df = pd.read_excel(msa_file)
            
            required_cols = ['Operador', 'Peça', 'Repetição', 'Medição']
            if all(col in msa_df.columns for col in required_cols):
                st.success(f"✅ Dados MSA carregados: {len(msa_df)} medições")
                
                # Análise MSA simplificada
                try:
                    msa_df['Medição'] = pd.to_numeric(msa_df['Medição'], errors='coerce')
                    msa_df = msa_df.dropna(subset=['Medição'])
                    
                    # Cálculo básico de R&R
                    total_var = msa_df['Medição'].var()
                    part_var = msa_df.groupby('Peça')['Medição'].mean().var()
                    rr_var = total_var - part_var
                    
                    rr_percent = (rr_var / total_var) * 100 if total_var > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("R&R (%)", f"{rr_percent:.1f}%")
                    with col2:
                        if rr_percent < 10:
                            st.success("✅ Excelente")
                        elif rr_percent < 30:
                            st.warning("⚠️ Aceitável")
                        else:
                            st.error("❌ Inadequado")
                    with col3:
                        st.metric("Medições", len(msa_df))
                    
                    # Salvar MSA
                    if st.button("💾 Salvar MSA", key=f"save_msa_{project_id}"):
                        msa_data = {
                            'num_operators': num_operators,
                            'num_parts': num_parts,
                            'num_trials': num_trials,
                            'total_measurements': len(msa_df),
                            'rr_percent': float(rr_percent),
                            'interpretation': 'Excelente' if rr_percent < 10 else ('Aceitável' if rr_percent < 30 else 'Inadequado'),
                            'analysis_date': datetime.now().isoformat()
                        }
                        
                        _save_tool_data(project_id, 'msa', msa_data, True)
                        st.success("✅ MSA salvo!")
                        
                except Exception as e:
                    st.error(f"❌ Erro na análise MSA: {str(e)}")
            else:
                st.error(f"❌ Colunas obrigatórias: {required_cols}")
                
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")


def show_baseline_metrics(project_data: Dict):
    """Baseline e Métricas CTQ"""
    
    project_id = project_data.get('id')
    
    st.markdown("## 📈 Baseline e Métricas CTQ")
    
    # Inicializar dados
    baseline_key = f"baseline_{project_id}"
    if baseline_key not in st.session_state:
        existing_data = project_data.get('measure', {}).get('baseline_data', {}).get('data', {})
        st.session_state[baseline_key] = existing_data if existing_data else {'ctq_metrics': []}
    
    baseline_data = st.session_state[baseline_key]
    
    # Status
    is_completed = project_data.get('measure', {}).get('baseline_data', {}).get('completed', False)
    if is_completed:
        st.success("✅ Baseline finalizado")
    else:
        st.info("⏳ Baseline em desenvolvimento")
    
    # Adicionar CTQ
    st.markdown("### 🎯 Métricas CTQ")
    
    with st.expander("➕ Adicionar Métrica CTQ"):
        col1, col2 = st.columns(2)
        with col1:
            ctq_name = st.text_input("Nome da Métrica", key=f"ctq_name_{project_id}")
            ctq_baseline = st.number_input("Valor Baseline", key=f"ctq_baseline_{project_id}")
        with col2:
            ctq_target = st.number_input("Meta", key=f"ctq_target_{project_id}")
            ctq_unit = st.text_input("Unidade", key=f"ctq_unit_{project_id}")
        
        if st.button("➕ Adicionar CTQ", key=f"add_ctq_{project_id}"):
            if ctq_name.strip():
                baseline_data['ctq_metrics'].append({
                    'name': ctq_name.strip(),
                    'baseline': ctq_baseline,
                    'target': ctq_target,
                    'unit': ctq_unit
                })
                st.session_state[baseline_key] = baseline_data
                st.rerun()
    
    # Mostrar CTQs
    if baseline_data['ctq_metrics']:
        for i, ctq in enumerate(baseline_data['ctq_metrics']):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.write(f"**{ctq['name']}**")
            with col2:
                st.write(f"Baseline: {ctq['baseline']} {ctq['unit']}")
            with col3:
                st.write(f"Meta: {ctq['target']} {ctq['unit']}")
            with col4:
                if st.button("🗑️", key=f"remove_ctq_{i}_{project_id}"):
                    baseline_data['ctq_metrics'].pop(i)
                    st.session_state[baseline_key] = baseline_data
                    st.rerun()
    
    # Período e fonte
    col1, col2 = st.columns(2)
    with col1:
        baseline_period = st.text_input(
            "Período do Baseline",
            value=baseline_data.get('baseline_period', ''),
            key=f"baseline_period_{project_id}"
        )
    with col2:
        data_source = st.text_input(
            "Fonte dos Dados",
            value=baseline_data.get('data_source', ''),
            key=f"baseline_source_{project_id}"
        )
    
    # Botões
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Salvar", key=f"save_baseline_{project_id}"):
            _save_tool_data(project_id, 'baseline_data', {
                'ctq_metrics': baseline_data['ctq_metrics'],
                'baseline_period': baseline_period,
                'data_source': data_source
            }, False)
            st.success("💾 Salvo!")
    
    with col2:
        if st.button("✅ Finalizar", key=f"complete_baseline_{project_id}"):
            if baseline_data['ctq_metrics'] and baseline_period.strip():
                _save_tool_data(project_id, 'baseline_data', {
                    'ctq_metrics': baseline_data['ctq_metrics'],
                    'baseline_period': baseline_period,
                    'data_source': data_source
                }, True)
                st.success("✅ Finalizado!")
                st.balloons()
            else:
                st.error("❌ Adicione pelo menos uma métrica CTQ e o período")


def _save_tool_data(project_id: str, tool_name: str, data: dict, completed: bool = False):
    """Função auxiliar para salvar dados das ferramentas"""
    try:
        project_manager = ProjectManager()
        
        update_data = {
            f'measure.{tool_name}.data': data,
            f'measure.{tool_name}.completed': completed,
            f'measure.{tool_name}.updated_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        success = project_manager.update_project(project_id, update_data)
        
        if success and 'current_project' in st.session_state:
            # Atualizar session_state
            if 'measure' not in st.session_state.current_project:
                st.session_state.current_project['measure'] = {}
            if tool_name not in st.session_state.current_project['measure']:
                st.session_state.current_project['measure'][tool_name] = {}
            
            st.session_state.current_project['measure'][tool_name]['data'] = data
            st.session_state.current_project['measure'][tool_name]['completed'] = completed
            st.session_state.current_project['measure'][tool_name]['updated_at'] = datetime.now().isoformat()
        
        return success
        
    except Exception as e:
        st.error(f"❌ Erro ao salvar: {str(e)}")
        return False


def show_measure_tools(project_data: Dict):
    """Função principal para mostrar as ferramentas da fase Measure - VERSÃO INTEGRADA"""
    
    if not project_data:
        st.error("❌ Projeto não encontrado")
        return
    
    project_id = project_data.get('id')
    
    # Inicializar gerenciador de sincronização
    sync_manager = DataSyncManager(project_id)
    
    # Menu de ferramentas
    st.markdown("### 🔧 Ferramentas da Fase Measure")
    st.markdown("Colete e analise dados para estabelecer o baseline do processo.")
    
    tool_options = {
        "data_collection_plan": ("📊", "Plano de Coleta de Dados"),
        "file_upload": ("📁", "Upload e Análise de Dados"), 
        "process_capability": ("📐", "Capacidade do Processo"),
        "msa": ("🎯", "MSA - Sistema de Medição"),
        "baseline_data": ("📈", "Baseline e Métricas CTQ")
    }
    
    # Verificar status das ferramentas
    measure_data = project_data.get('measure', {})
    
    # Criar lista de ferramentas com status
    tool_names_with_status = []
    tool_keys = list(tool_options.keys())
    
    for key, (icon, name) in tool_options.items():
        tool_data = measure_data.get(key, {})
        is_completed = tool_data.get('completed', False) if isinstance(tool_data, dict) else False
        status_icon = "✅" if is_completed else "⏳"
        tool_names_with_status.append(f"{status_icon} {icon} {name}")
    
    # Seletor de ferramenta
    selected_index = st.selectbox(
        "Selecione uma ferramenta para usar:",
        range(len(tool_names_with_status)),
        format_func=lambda x: tool_names_with_status[x],
        key=f"measure_tool_selector_{project_id}",
        help="Escolha a ferramenta que deseja usar na fase Measure"
    )
    
    selected_tool = tool_keys[selected_index]
    
    st.divider()
    
    # Mostrar status de sincronização na sidebar
    with st.sidebar:
        st.markdown("### 🔄 Status dos Dados")
        
        # Verificar se há dados carregados
        has_data = sync_manager.ensure_data_available(show_warnings=False)
        
        if has_data:
            st.success("✅ Dados disponíveis")
            upload_info = sync_manager.project_manager.get_upload_info(project_id)
            if upload_info:
                st.write(f"📄 {upload_info.get('filename', 'N/A')}")
                shape = upload_info.get('shape', [0, 0])
                st.write(f"📊 {shape[0]} × {shape[1]}")
        else:
            st.warning("⚠️ Sem dados carregados")
            st.info("Use 'Upload e Análise de Dados'")
    
    # Mostrar ferramenta selecionada
    if selected_tool == "data_collection_plan":
        show_data_collection_plan(project_data)
    elif selected_tool == "file_upload":
        show_file_upload_analysis(project_data)
    elif selected_tool == "process_capability":
        show_process_capability(project_data)
    elif selected_tool == "msa":
        show_msa_analysis(project_data)
    elif selected_tool == "baseline_data":
        show_baseline_metrics(project_data)
    
    # Progresso geral da fase Measure
    st.divider()
    st.markdown("### 📊 Progresso da Fase Measure")
    
    # Recarregar dados atualizados
    if 'current_project' in st.session_state:
        updated_measure_data = st.session_state.current_project.get('measure', {})
    else:
        updated_measure_data = measure_data
    
    total_tools = len(tool_options)
    completed_tools = 0
    
    # Status das ferramentas
    st.markdown("#### 📋 Status das Ferramentas")
    
    cols = st.columns(len(tool_options))
    
    for i, (key, (icon, name)) in enumerate(tool_options.items()):
        tool_data = updated_measure_data.get(key, {})
        is_completed = tool_data.get('completed', False) if isinstance(tool_data, dict) else False
        
        if is_completed:
            completed_tools += 1
        
        with cols[i]:
            if is_completed:
                st.success(f"✅ {name}")
            else:
                st.info(f"⏳ {name}")
    
    # Barra de progresso
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
    
    # Conclusão da fase
    if progress == 100:
        st.success("🎉 **Parabéns! Fase Measure concluída com sucesso!**")
        st.info("✨ Você pode avançar para a fase **Analyze** usando a navegação das fases.")
        
        # Resumo das principais métricas
        st.markdown("### 📈 Resumo das Principais Métricas")
        
        metrics_summary = []
        
        # Dados carregados
        upload_info = sync_manager.project_manager.get_upload_info(project_id)
        if upload_info:
            shape = upload_info.get('shape', [0, 0])
            metrics_summary.append(f"📊 **Dados:** {shape[0]} observações, {shape[1]} variáveis")
        
        # Baseline
        baseline_data = updated_measure_data.get('baseline_data', {}).get('data', {})
        if baseline_data.get('ctq_metrics'):
            ctq_count = len(baseline_data['ctq_metrics'])
            metrics_summary.append(f"🎯 **CTQs:** {ctq_count} métrica(s) crítica(s) definida(s)")
        
        # Capacidade
        capability_data = updated_measure_data.get('process_capability', {}).get('data', {})
        if capability_data.get('capability_status'):
            status = capability_data['capability_status']
            metrics_summary.append(f"📐 **Capacidade:** Processo {status}")
        
        # MSA
        msa_data = updated_measure_data.get('msa', {}).get('data', {})
        if msa_data.get('interpretation'):
            interpretation = msa_data['interpretation']
            metrics_summary.append(f"🎯 **MSA:** Sistema de medição {interpretation}")
        
        if metrics_summary:
            for metric in metrics_summary:
                st.write(metric)
        else:
            st.info("Complete as ferramentas para ver o resumo das métricas")
    
    # Debug opcional
    with st.expander("🔍 Debug - Dados da Fase Measure"):
        st.json(updated_measure_data)
