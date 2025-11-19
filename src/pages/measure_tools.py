import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.utils.project_manager import ProjectManager
import warnings

# Suprimir warnings
warnings.filterwarnings('ignore')

# Verificar scipy com fallback
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    st.warning("⚠️ Scipy não disponível. Algumas análises estatísticas serão limitadas.")


class MeasurePhaseManager:
    """Gerenciador centralizado da fase Measure"""
    
    def __init__(self, project_data: Dict):
        self.project_data = project_data
        self.project_id = project_data.get('id')
        self.project_manager = ProjectManager()
    
    def save_tool_data(self, tool_name: str, data: Dict, completed: bool = False) -> bool:
        """Salva dados de uma ferramenta com atualização de estado"""
        try:
            update_data = {
                f'measure.{tool_name}.data': data,
                f'measure.{tool_name}.completed': completed,
                f'measure.{tool_name}.updated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            success = self.project_manager.update_project(self.project_id, update_data)
            
            if success and 'current_project' in st.session_state:
                # Atualizar session_state imediatamente
                if 'measure' not in st.session_state.current_project:
                    st.session_state.current_project['measure'] = {}
                if tool_name not in st.session_state.current_project['measure']:
                    st.session_state.current_project['measure'][tool_name] = {}
                
                st.session_state.current_project['measure'][tool_name] = {
                    'data': data,
                    'completed': completed,
                    'updated_at': datetime.now().isoformat()
                }
            
            return success
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar dados: {str(e)}")
            return False
    
    def is_tool_completed(self, tool_name: str) -> bool:
        """Verifica se uma ferramenta foi concluída"""
        measure_data = self.project_data.get('measure', {})
        tool_data = measure_data.get(tool_name, {})
        return tool_data.get('completed', False) if isinstance(tool_data, dict) else False
    
    def get_tool_data(self, tool_name: str) -> Dict:
        """Recupera dados de uma ferramenta"""
        measure_data = self.project_data.get('measure', {})
        tool_data = measure_data.get(tool_name, {})
        return tool_data.get('data', {}) if isinstance(tool_data, dict) else {}


class DataCollectionPlanTool:
    """Ferramenta de Plano de Coleta de Dados"""
    
    def __init__(self, manager: MeasurePhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "data_collection_plan"
    
    def show(self):
        """Interface principal da ferramenta"""
        st.markdown("## 📊 Plano de Coleta de Dados")
        st.markdown("Defina **o que**, **como**, **quando** e **onde** coletar os dados do processo.")
        
        # Status da ferramenta
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ Plano de coleta finalizado")
        else:
            st.info("⏳ Plano em desenvolvimento")
        
        # Inicializar dados da sessão
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data if existing_data else {'variables': []}
        
        plan_data = st.session_state[session_key]
        
        # Interface de configuração
        self._show_objective_section(plan_data)
        self._show_variables_section(plan_data)
        self._show_method_schedule_section(plan_data)
        self._show_action_buttons(plan_data)
    
    def _show_objective_section(self, plan_data: Dict):
        """Seção do objetivo da coleta"""
        st.markdown("### 🎯 Objetivo da Coleta")
        collection_objective = st.text_area(
            "Objetivo Principal da Coleta *",
            value=plan_data.get('collection_objective', ''),
            placeholder="Ex: Medir a variabilidade do tempo de setup das máquinas para identificar oportunidades de melhoria...",
            height=100,
            key=f"collection_objective_{self.project_id}",
            help="Descreva claramente por que você está coletando esses dados"
        )
        plan_data['collection_objective'] = collection_objective
    
    def _show_variables_section(self, plan_data: Dict):
        """Seção de variáveis a medir"""
        st.markdown("### 📏 Variáveis a Medir")
        
        # Adicionar nova variável
        with st.expander("➕ Adicionar Nova Variável"):
            col1, col2 = st.columns(2)
            with col1:
                var_name = st.text_input("Nome da Variável *", key=f"var_name_{self.project_id}")
                var_type = st.selectbox(
                    "Tipo de Variável", 
                    ["Contínua", "Discreta", "Categórica"], 
                    key=f"var_type_{self.project_id}",
                    help="Contínua: valores decimais | Discreta: números inteiros | Categórica: categorias"
                )
            with col2:
                var_unit = st.text_input("Unidade de Medida", key=f"var_unit_{self.project_id}")
                var_target = st.text_input("Meta/Especificação", key=f"var_target_{self.project_id}")
            
            var_description = st.text_area(
                "Descrição/Como Medir",
                key=f"var_description_{self.project_id}",
                placeholder="Descreva como esta variável será medida..."
            )
            
            if st.button("➕ Adicionar Variável", key=f"add_var_{self.project_id}"):
                if var_name.strip():
                    plan_data['variables'].append({
                        'name': var_name.strip(),
                        'type': var_type,
                        'unit': var_unit,
                        'target': var_target,
                        'description': var_description
                    })
                    st.success(f"✅ Variável '{var_name}' adicionada!")
                    st.rerun()
                else:
                    st.error("❌ Nome da variável é obrigatório")
        
        # Mostrar variáveis existentes
        if plan_data['variables']:
            st.markdown("#### 📋 Variáveis Definidas")
            for i, var in enumerate(plan_data['variables']):
                with st.expander(f"**{var['name']}** ({var['type']})"):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**Tipo:** {var['type']}")
                        st.write(f"**Unidade:** {var['unit'] or 'Não especificada'}")
                        st.write(f"**Meta:** {var['target'] or 'Não especificada'}")
                        if var.get('description'):
                            st.write(f"**Descrição:** {var['description']}")
                    
                    with col2:
                        # Opções de edição futura
                        st.info("💡 Edição disponível em versões futuras")
                    
                    with col3:
                        if st.button("🗑️ Remover", key=f"remove_var_{i}_{self.project_id}"):
                            plan_data['variables'].pop(i)
                            st.success("✅ Variável removida!")
                            st.rerun()
        else:
            st.info("📝 Nenhuma variável definida ainda. Adicione pelo menos uma variável para continuar.")
    
    def _show_method_schedule_section(self, plan_data: Dict):
        """Seção de método e cronograma"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔧 Método de Coleta")
            collection_method = st.selectbox(
                "Método Principal *",
                ["Medição Direta", "Observação", "Sistema Automatizado", "Formulário", "Inspeção", "Amostragem"],
                index=0,
                key=f"collection_method_{self.project_id}",
                help="Como os dados serão coletados"
            )
            plan_data['collection_method'] = collection_method
            
            responsible_person = st.text_input(
                "Responsável pela Coleta *",
                value=plan_data.get('responsible_person', ''),
                key=f"responsible_person_{self.project_id}",
                help="Nome da pessoa responsável pela coleta"
            )
            plan_data['responsible_person'] = responsible_person
            
            collection_frequency = st.selectbox(
                "Frequência de Coleta",
                ["Contínua", "Diária", "Semanal", "Mensal", "Por Lote", "Por Evento"],
                key=f"collection_frequency_{self.project_id}"
            )
            plan_data['collection_frequency'] = collection_frequency
        
        with col2:
            st.markdown("### 📅 Cronograma")
            start_date = st.date_input(
                "Data de Início *",
                value=datetime.now().date(),
                key=f"start_date_{self.project_id}"
            )
            plan_data['start_date'] = start_date.isoformat()
            
            collection_duration = st.number_input(
                "Duração da Coleta (dias)",
                min_value=1,
                max_value=365,
                value=30,
                key=f"collection_duration_{self.project_id}"
            )
            plan_data['collection_duration'] = collection_duration
            
            sample_size = st.number_input(
                "Tamanho da Amostra Alvo",
                min_value=1,
                max_value=10000,
                value=100,
                key=f"sample_size_{self.project_id}",
                help="Número mínimo de observações necessárias"
            )
            plan_data['sample_size'] = sample_size
            
            # Calcular data fim
            end_date = datetime.strptime(plan_data['start_date'], '%Y-%m-%d') + timedelta(days=collection_duration)
            st.info(f"📅 **Data prevista de término:** {end_date.strftime('%d/%m/%Y')}")
    
    def _show_action_buttons(self, plan_data: Dict):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Plano", key=f"save_{self.tool_name}_{self.project_id}"):
                success = self.manager.save_tool_data(self.tool_name, plan_data, completed=False)
                if success:
                    st.success("💾 Plano de coleta salvo com sucesso!")
                else:
                    st.error("❌ Erro ao salvar plano")
        
        with col2:
            if st.button("✅ Finalizar Plano", key=f"complete_{self.tool_name}_{self.project_id}"):
                # Validação
                if self._validate_plan(plan_data):
                    success = self.manager.save_tool_data(self.tool_name, plan_data, completed=True)
                    if success:
                        st.success("✅ Plano de coleta finalizado com sucesso!")
                        st.balloons()
                        # Forçar atualização da interface
                        st.rerun()
                    else:
                        st.error("❌ Erro ao finalizar plano")
                else:
                    st.error("❌ Complete todos os campos obrigatórios")
    
    def _validate_plan(self, plan_data: Dict) -> bool:
        """Valida se o plano está completo"""
        required_fields = [
            ('collection_objective', 'Objetivo da coleta'),
            ('responsible_person', 'Responsável pela coleta')
        ]
        
        missing_fields = []
        
        for field, name in required_fields:
            if not plan_data.get(field, '').strip():
                missing_fields.append(name)
        
        if not plan_data.get('variables'):
            missing_fields.append('Pelo menos uma variável')
        
        if missing_fields:
            st.error(f"❌ Campos obrigatórios faltando: {', '.join(missing_fields)}")
            return False
        
        return True


class FileUploadTool:
    """Ferramenta de Upload e Análise de Dados - Versão Otimizada"""
    
    def __init__(self, manager: MeasurePhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "file_upload"
    
    def show(self):
        """Interface principal da ferramenta"""
        st.markdown("## 📁 Upload e Análise de Dados")
        st.markdown("Faça upload dos dados do processo para análise estatística.")
        
        # Verificar dados existentes
        existing_data = self.manager.project_manager.get_uploaded_data(self.project_id)
        upload_info = self.manager.project_manager.get_upload_info(self.project_id)
        is_completed = self.manager.is_tool_completed(self.tool_name)
        
        # Mostrar status
        if existing_data is not None and is_completed:
            st.success("✅ **Dados carregados e salvos no projeto**")
            self._show_existing_data_info(upload_info)
            
            # Opção para substituir dados
            if st.checkbox("🔄 Substituir dados existentes", key=f"replace_data_{self.project_id}"):
                st.warning("⚠️ **Atenção:** Isso substituirá os dados atuais e pode afetar análises já realizadas.")
                self._show_upload_interface()
            else:
                self._show_data_analysis(existing_data, upload_info)
        else:
            self._show_upload_interface()
    
    def _show_existing_data_info(self, upload_info: Dict):
        """Mostra informações dos dados existentes"""
        if upload_info:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📄 Arquivo", upload_info.get('filename', 'N/A'))
            
            with col2:
                shape = upload_info.get('shape', [0, 0])
                st.metric("📊 Dimensões", f"{shape[0]} × {shape[1]}")
            
            with col3:
                data_summary = upload_info.get('data_summary', {})
                st.metric("📈 Colunas Numéricas", data_summary.get('numeric_columns', 0))
            
            with col4:
                upload_date = upload_info.get('uploaded_at', '')[:10] if upload_info.get('uploaded_at') else 'N/A'
                st.metric("📅 Upload", upload_date)
    
    def _show_upload_interface(self):
        """Interface de upload"""
        st.markdown("### 📤 Upload de Arquivo")
        
        # Informações sobre formatos suportados
        with st.expander("ℹ️ Informações sobre Upload"):
            st.markdown("""
            **Formatos suportados:**
            - CSV (`.csv`) - Recomendado: UTF-8
            - Excel (`.xlsx`, `.xls`)
            
            **Dicas para melhor compatibilidade:**
            - Use nomes simples para colunas (sem caracteres especiais)
            - Evite células mescladas no Excel
            - Primeira linha deve conter os cabeçalhos
            - Para CSV, prefira separador vírgula (`,`)
            """)
        
        # Upload com chave única
        uploaded_file = st.file_uploader(
            "Escolha um arquivo de dados",
            type=['csv', 'xlsx', 'xls'],
            key=f"file_uploader_{self.project_id}",
            help="Arraste o arquivo aqui ou clique para selecionar"
        )
        
        if uploaded_file is not None:
            self._process_uploaded_file(uploaded_file)
    
    def _process_uploaded_file(self, uploaded_file):
        """Processa arquivo carregado"""
        try:
            with st.spinner("📊 Processando arquivo..."):
                # Mostrar informações do arquivo
                st.info(f"📄 **Arquivo:** {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
                
                # Ler arquivo baseado na extensão
                df = self._read_file(uploaded_file)
                
                if df is None:
                    return
                
                # Validações básicas
                if not self._validate_dataframe(df):
                    return
                
                # Salvar dados usando ProjectManager
                success = self.manager.project_manager.save_uploaded_data(
                    project_id=self.project_id,
                    dataframe=df,
                    filename=uploaded_file.name,
                    additional_info={
                        'file_size': uploaded_file.size,
                        'upload_method': 'streamlit_uploader',
                        'processing_timestamp': datetime.now().isoformat()
                    }
                )
                
                if success:
                    st.success(f"✅ **Arquivo processado com sucesso!**")
                    
                    # Mostrar resumo básico
                    self._show_upload_summary(df)
                    
                    # Marcar ferramenta como concluída
                    tool_success = self.manager.save_tool_data(
                        self.tool_name,
                        {
                            'filename': uploaded_file.name,
                            'upload_timestamp': datetime.now().isoformat(),
                            'rows': len(df),
                            'columns': len(df.columns)
                        },
                        completed=True
                    )
                    
                    if tool_success:
                        st.success("✅ Upload registrado no projeto!")
                    
                    # Mostrar análise dos dados
                    st.markdown("---")
                    self._show_data_analysis(df, self.manager.project_manager.get_upload_info(self.project_id))
                    
                else:
                    st.error("❌ Erro ao salvar dados no projeto")
                
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")
            self._show_troubleshooting_tips()
    
    def _read_file(self, uploaded_file) -> Optional[pd.DataFrame]:
        """Lê arquivo com tratamento robusto de erros"""
        try:
            if uploaded_file.name.endswith('.csv'):
                # Tentar diferentes encodings para CSV
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                
                for encoding in encodings:
                    try:
                        uploaded_file.seek(0)  # Reset file pointer
                        df = pd.read_csv(uploaded_file, encoding=encoding)
                        st.success(f"✅ CSV lido com encoding: {encoding}")
                        return df
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        st.warning(f"⚠️ Erro com encoding {encoding}: {str(e)}")
                        continue
                
                st.error("❌ Não foi possível ler o arquivo CSV com nenhum encoding testado")
                return None
                
            else:
                # Excel
                df = pd.read_excel(uploaded_file)
                st.success("✅ Arquivo Excel lido com sucesso")
                return df
                
        except Exception as e:
            st.error(f"❌ Erro na leitura do arquivo: {str(e)}")
            return None
    
    def _validate_dataframe(self, df: pd.DataFrame) -> bool:
        """Valida DataFrame básico"""
        if df.empty:
            st.error("❌ Arquivo está vazio")
            return False
        
        if len(df.columns) == 0:
            st.error("❌ Nenhuma coluna encontrada")
            return False
        
        if len(df) < 2:
            st.error("❌ Arquivo deve ter pelo menos 2 linhas de dados")
            return False
        
        return True
    
    def _show_upload_summary(self, df: pd.DataFrame):
        """Mostra resumo do upload"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Linhas", len(df))
        
        with col2:
            st.metric("📋 Colunas", len(df.columns))
        
        with col3:
            numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
            st.metric("📈 Numéricas", numeric_cols)
        
        with col4:
            missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            st.metric("❓ Dados Faltantes", f"{missing_pct:.1f}%")
    
    def _show_troubleshooting_tips(self):
        """Dicas para resolução de problemas"""
        st.markdown("### 🔧 Dicas para Resolução de Problemas")
        
        st.info("""
        **Se o upload falhou, tente:**
        
        1. **Para arquivos CSV:**
           - Salve com codificação UTF-8
           - Use vírgula como separador
           - Remova caracteres especiais dos cabeçalhos
        
        2. **Para arquivos Excel:**
           - Salve como .xlsx (formato mais recente)
           - Remova células mescladas
           - Certifique-se de que os dados começam na célula A1
        
        3. **Geral:**
           - Verifique se o arquivo não está corrompido
           - Reduza o tamanho se for muito grande (>50MB)
           - Remova colunas desnecessárias
        """)
    
    def _show_data_analysis(self, df: pd.DataFrame, upload_info: Optional[Dict] = None):
        """Mostra análise completa dos dados"""
        st.markdown("### 📊 Análise dos Dados Carregados")
        
        # Verificação de qualidade rápida
        self._show_quality_overview(df)
        
        # Tabs para análise detalhada
        tab1, tab2, tab3, tab4 = st.tabs([
            "👀 Visualização",
            "📈 Estatísticas",
            "📊 Gráficos",
            "🔍 Qualidade"
        ])
        
        with tab1:
            self._show_data_preview(df)
        
        with tab2:
            self._show_statistics_analysis(df)
        
        with tab3:
            self._show_charts_analysis(df)
        
        with tab4:
            self._show_quality_analysis(df)
    
    def _show_quality_overview(self, df: pd.DataFrame):
        """Overview rápido da qualidade"""
        col1, col2, col3, col4 = st.columns(4)
        
        # Dados faltantes
        missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        with col1:
            if missing_pct < 5:
                st.success(f"✅ Faltantes: {missing_pct:.1f}%")
            elif missing_pct < 15:
                st.warning(f"⚠️ Faltantes: {missing_pct:.1f}%")
            else:
                st.error(f"❌ Faltantes: {missing_pct:.1f}%")
        
        # Duplicatas
        duplicates_pct = (df.duplicated().sum() / len(df)) * 100
        with col2:
            if duplicates_pct < 1:
                st.success(f"✅ Duplicatas: {duplicates_pct:.1f}%")
            elif duplicates_pct < 5:
                st.warning(f"⚠️ Duplicatas: {duplicates_pct:.1f}%")
            else:
                st.error(f"❌ Duplicatas: {duplicates_pct:.1f}%")
        
        # Colunas numéricas
        numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
        with col3:
            if numeric_cols > 0:
                st.success(f"✅ Numéricas: {numeric_cols}")
            else:
                st.warning("⚠️ Nenhuma numérica")
        
        # Tamanho da amostra
        with col4:
            if len(df) >= 100:
                st.success(f"✅ Amostra: {len(df)}")
            elif len(df) >= 30:
                st.warning(f"⚠️ Amostra: {len(df)}")
            else:
                st.error(f"❌ Amostra pequena: {len(df)}")
    
    def _show_data_preview(self, df: pd.DataFrame):
        """Preview dos dados"""
        st.markdown("#### 📋 Primeiras Linhas")
        st.dataframe(df.head(10), use_container_width=True)
        
        if len(df) > 10:
            st.info(f"💡 Mostrando 10 de {len(df)} linhas totais")
        
        # Informações das colunas
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
    
    def _show_statistics_analysis(self, df: pd.DataFrame):
        """Análise estatística"""
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_columns:
            st.warning("⚠️ Nenhuma coluna numérica encontrada")
            return
        
        st.markdown("#### 📈 Estatísticas Descritivas")
        
        # Seleção de colunas
        selected_cols = st.multiselect(
            "Selecione colunas para análise:",
            numeric_columns,
            default=numeric_columns[:5],  # Máximo 5
            key=f"stats_cols_{self.project_id}"
        )
        
        if selected_cols:
            # Estatísticas básicas
            desc_stats = df[selected_cols].describe()
            st.dataframe(desc_stats, use_container_width=True)
            
            # Estatísticas adicionais (se scipy disponível)
            if SCIPY_AVAILABLE:
                st.markdown("**Estatísticas Avançadas:**")
                
                advanced_stats = []
                for col in selected_cols:
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        try:
                            advanced_stats.append({
                                'Coluna': col,
                                'Assimetria': stats.skew(col_data),
                                'Curtose': stats.kurtosis(col_data),
                                'CV (%)': (col_data.std() / col_data.mean() * 100) if col_data.mean() != 0 else 0
                            })
                        except:
                            pass
                
                if advanced_stats:
                    st.dataframe(pd.DataFrame(advanced_stats), use_container_width=True)
    
    def _show_charts_analysis(self, df: pd.DataFrame):
        """Análise com gráficos"""
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_columns:
            st.warning("⚠️ Nenhuma coluna numérica para gráficos")
            return
        
        chart_type = st.selectbox(
            "Tipo de Gráfico:",
            ["Histograma", "Box Plot", "Scatter Plot", "Série Temporal"],
            key=f"chart_type_{self.project_id}"
        )
        
        try:
            if chart_type == "Histograma":
                self._show_histogram(df, numeric_columns)
            elif chart_type == "Box Plot":
                self._show_boxplot(df, numeric_columns)
            elif chart_type == "Scatter Plot":
                self._show_scatterplot(df, numeric_columns)
            elif chart_type == "Série Temporal":
                self._show_timeseries(df, numeric_columns)
        except Exception as e:
            st.error(f"❌ Erro ao gerar gráfico: {str(e)}")
    
    def _show_histogram(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Histograma"""
        col_to_plot = st.selectbox("Coluna:", numeric_columns, key=f"hist_col_{self.project_id}")
        bins = st.slider("Número de bins:", 10, 100, 30, key=f"hist_bins_{self.project_id}")
        
        fig = px.histogram(df, x=col_to_plot, nbins=bins, title=f"Histograma - {col_to_plot}")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_boxplot(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Box plot"""
        cols_to_plot = st.multiselect(
            "Colunas:",
            numeric_columns,
            default=numeric_columns[:3],
            key=f"box_cols_{self.project_id}"
        )
        
        if cols_to_plot:
            fig = go.Figure()
            for col in cols_to_plot:
                fig.add_trace(go.Box(y=df[col], name=col))
            
            fig.update_layout(title="Box Plot Comparativo", height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    def _show_scatterplot(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Scatter plot"""
        if len(numeric_columns) < 2:
            st.warning("⚠️ Necessário pelo menos 2 colunas numéricas")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            x_col = st.selectbox("Eixo X:", numeric_columns, key=f"scatter_x_{self.project_id}")
        
        with col2:
            y_options = [col for col in numeric_columns if col != x_col]
            y_col = st.selectbox("Eixo Y:", y_options, key=f"scatter_y_{self.project_id}")
        
        fig = px.scatter(df, x=x_col, y=y_col, title=f"Scatter: {x_col} vs {y_col}")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_timeseries(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Série temporal"""
        time_col = st.selectbox("Variável:", numeric_columns, key=f"time_col_{self.project_id}")
        
        fig = px.line(x=range(len(df)), y=df[time_col], title=f"Série Temporal - {time_col}")
        fig.update_xaxes(title="Observação")
        fig.update_yaxes(title=time_col)
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_quality_analysis(self, df: pd.DataFrame):
        """Análise detalhada de qualidade"""
        st.markdown("#### 🔍 Análise de Qualidade dos Dados")
        
        # Resumo de problemas
        quality_issues = self._identify_quality_issues(df)
        
        if quality_issues:
            st.markdown("**⚠️ Problemas Identificados:**")
            quality_df = pd.DataFrame(quality_issues)
            st.dataframe(quality_df, use_container_width=True)
        else:
            st.success("✅ Nenhum problema significativo identificado")
        
        # Recomendações
        recommendations = self._generate_recommendations(df)
        
        if recommendations:
            st.markdown("#### 💡 Recomendações")
            for rec in recommendations:
                st.write(f"• {rec}")
    
    def _identify_quality_issues(self, df: pd.DataFrame) -> List[Dict]:
        """Identifica problemas de qualidade"""
        issues = []
        
        for col in df.columns:
            col_data = df[col]
            col_issues = []
            
            # Dados faltantes
            missing_pct = (col_data.isnull().sum() / len(df)) * 100
            if missing_pct > 10:
                col_issues.append(f"Dados faltantes: {missing_pct:.1f}%")
            
            # Cardinalidade
            unique_pct = (col_data.nunique() / len(df)) * 100
            if unique_pct > 95 and len(df) > 100:
                col_issues.append("Possível coluna ID (alta cardinalidade)")
            elif unique_pct < 5 and col_data.dtype == 'object':
                col_issues.append("Baixa variabilidade")
            
            # Outliers para colunas numéricas
            if pd.api.types.is_numeric_dtype(col_data) and len(col_data.dropna()) > 0:
                try:
                    Q1 = col_data.quantile(0.25)
                    Q3 = col_data.quantile(0.75)
                    IQR = Q3 - Q1
                    
                    if IQR > 0:
                        outliers = col_data[(col_data < Q1 - 1.5 * IQR) | (col_data > Q3 + 1.5 * IQR)]
                        outlier_pct = (len(outliers) / len(col_data.dropna())) * 100
                        
                        if outlier_pct > 5:
                            col_issues.append(f"Outliers: {outlier_pct:.1f}%")
                except:
                    pass
            
            if col_issues:
                issues.append({
                    'Coluna': col,
                    'Problemas': '; '.join(col_issues)
                })
        
        return issues
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Gera recomendações baseadas nos dados"""
        recommendations = []
        
        # Dados faltantes
        missing_cols = df.columns[df.isnull().any()].tolist()
        if missing_cols:
            recommendations.append(f"Considere estratégias para dados faltantes em: {', '.join(missing_cols[:3])}")
        
        # Amostra pequena
        if len(df) < 30:
            recommendations.append("Amostra pequena - considere coletar mais dados para análises robustas")
        
        # Colunas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            recommendations.append("Dados numéricos disponíveis - prossiga com análises estatísticas")
        
        # Duplicatas
        if df.duplicated().sum() > 0:
            recommendations.append("Remova registros duplicados se não forem intencionais")
        
        return recommendations


def show_measure_tools(project_data: Dict):
    """Função principal para mostrar as ferramentas da fase Measure - VERSÃO MELHORADA"""
    
    if not project_data:
        st.error("❌ Projeto não encontrado")
        return
    
    # Inicializar gerenciador
    manager = MeasurePhaseManager(project_data)
    
    # Cabeçalho da fase
    st.markdown("### 🔧 Ferramentas da Fase Measure")
    st.markdown("Colete e analise dados para estabelecer o baseline do processo.")
    
    # Definir ferramentas disponíveis
    tool_options = {
        "data_collection_plan": ("📊", "Plano de Coleta de Dados"),
        "file_upload": ("📁", "Upload e Análise de Dados"),
        "process_capability": ("📐", "Capacidade do Processo"),
        "msa": ("🎯", "MSA - Sistema de Medição"),
        "baseline_data": ("📈", "Baseline e Métricas CTQ")
    }
    
    # Verificar status atualizado das ferramentas
    if 'current_project' in st.session_state:
        current_measure_data = st.session_state.current_project.get('measure', {})
    else:
        current_measure_data = project_data.get('measure', {})
    
    # Criar lista com status atualizado
    tool_names_with_status = []
    tool_keys = list(tool_options.keys())
    
    for key, (icon, name) in tool_options.items():
        tool_data = current_measure_data.get(key, {})
        is_completed = tool_data.get('completed', False) if isinstance(tool_data, dict) else False
        status_icon = "✅" if is_completed else "⏳"
        tool_names_with_status.append(f"{status_icon} {icon} {name}")
    
    # Seletor de ferramenta
    selected_index = st.selectbox(
        "Selecione uma ferramenta para usar:",
        range(len(tool_names_with_status)),
        format_func=lambda x: tool_names_with_status[x],
        key=f"measure_tool_selector_{manager.project_id}",
        help="Escolha a ferramenta que deseja usar na fase Measure"
    )
    
    selected_tool = tool_keys[selected_index]
    
    st.divider()
    
    # Status na sidebar
    with st.sidebar:
        st.markdown("### 🔄 Status dos Dados")
        
        has_data = manager.project_manager.get_uploaded_data(manager.project_id) is not None
        upload_info = manager.project_manager.get_upload_info(manager.project_id)
        
        if has_data:
            st.success("✅ Dados disponíveis")
            if upload_info:
                st.caption(f"📄 {upload_info.get('filename', 'N/A')}")
                shape = upload_info.get('shape', [0, 0])
                st.caption(f"📊 {shape[0]} × {shape[1]}")
        else:
            st.warning("⚠️ Sem dados")
            st.caption("Use 'Upload e Análise'")
        
        if st.button("🔄 Sincronizar", key=f"sync_sidebar_{manager.project_id}"):
            success = manager.project_manager.ensure_project_sync(manager.project_id)
            if success:
                st.success("✅ Sincronizado!")
                st.rerun()
    
    # Mostrar ferramenta selecionada
    if selected_tool == "data_collection_plan":
        tool = DataCollectionPlanTool(manager)
        tool.show()
    elif selected_tool == "file_upload":
        tool = FileUploadTool(manager)
        tool.show()
    elif selected_tool == "process_capability":
        show_process_capability(project_data)  # Manter função existente
    elif selected_tool == "msa":
        show_msa_analysis(project_data)  # Manter função existente
    elif selected_tool == "baseline_data":
        show_baseline_metrics(project_data)  # Manter função existente
    
    # Progresso da fase
    st.divider()
    _show_measure_progress(manager, tool_options, current_measure_data)


def _show_measure_progress(manager: MeasurePhaseManager, tool_options: Dict, measure_data: Dict):
    """Mostra progresso da fase Measure"""
    st.markdown("### 📊 Progresso da Fase Measure")
    
    total_tools = len(tool_options)
    completed_tools = 0
    
    # Contar ferramentas concluídas
    for key in tool_options.keys():
        tool_data = measure_data.get(key, {})
        if isinstance(tool_data, dict) and tool_data.get('completed', False):
            completed_tools += 1
    
    # Status visual das ferramentas
    st.markdown("#### 📋 Status das Ferramentas")
    
    cols = st.columns(len(tool_options))
    
    for i, (key, (icon, name)) in enumerate(tool_options.items()):
        tool_data = measure_data.get(key, {})
        is_completed = tool_data.get('completed', False) if isinstance(tool_data, dict) else False
        
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
    
    # Mensagem de conclusão
    if progress == 100:
        st.success("🎉 **Parabéns! Fase Measure concluída com sucesso!**")
        st.info("✨ Você pode avançar para a fase **Analyze** usando a navegação das fases.")


def show_process_capability(project_data: Dict):
    """Análise de Capacidade do Processo - VERSÃO CORRIGIDA"""
    
    # Usar o manager como as outras ferramentas
    manager = MeasurePhaseManager(project_data)
    project_id = manager.project_id
    tool_name = "process_capability"
    
    st.markdown("## 📐 Análise de Capacidade do Processo")
    st.markdown("Avalie se o processo é capaz de atender às especificações definidas.")
    
    # Verificar se há dados
    df = manager.project_manager.get_uploaded_data(project_id)
    
    if df is None:
        st.warning("⚠️ **Dados não encontrados**")
        st.info("Primeiro faça upload dos dados na ferramenta **Upload e Análise de Dados**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📁 Ir para Upload", key=f"goto_upload_{project_id}"):
                st.info("💡 Selecione 'Upload e Análise de Dados' no menu acima")
        with col2:
            if st.button("🔄 Recarregar", key=f"reload_capability_{project_id}"):
                st.rerun()
        return
    
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_columns:
        st.error("❌ Nenhuma coluna numérica encontrada nos dados")
        st.info("💡 Certifique-se de que seus dados contêm variáveis numéricas para análise")
        return
    
    # Status da ferramenta
    is_completed = manager.is_tool_completed(tool_name)
    if is_completed:
        st.success("✅ **Análise de capacidade finalizada**")
        st.info("💡 Você pode refazer a análise ou visualizar os resultados salvos")
    else:
        st.info("⏳ **Análise em desenvolvimento**")
    
    # Inicializar dados da sessão
    session_key = f"{tool_name}_{project_id}"
    if session_key not in st.session_state:
        existing_data = manager.get_tool_data(tool_name)
        st.session_state[session_key] = existing_data if existing_data else {}
    
    capability_data = st.session_state[session_key]
    
    # Mostrar resultados salvos se existirem
    if capability_data and capability_data.get('analysis_completed'):
        st.markdown("### 📊 Resultados Salvos")
        _show_saved_capability_results(capability_data)
        st.divider()
        
        if st.checkbox("🔄 Refazer Análise", key=f"redo_capability_{project_id}"):
            st.info("Configure nova análise abaixo:")
        else:
            # Mostrar apenas botões de ação se análise já foi feita
            _show_capability_action_buttons(manager, tool_name, capability_data)
            return
    
    # Configuração da análise
    st.markdown("### ⚙️ Configuração da Análise")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_column = st.selectbox(
            "Variável para análise:",
            numeric_columns,
            key=f"capability_col_{project_id}",
            help="Selecione a variável crítica para qualidade (CTQ)"
        )
    
    with col2:
        spec_type = st.selectbox(
            "Tipo de Especificação:",
            ["Bilateral", "Superior apenas", "Inferior apenas"],
            key=f"capability_spec_type_{project_id}",
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
                "LSL (Limite Inferior de Especificação):",
                value=float(capability_data.get('lsl', mean_val - 3*std_val)),
                key=f"capability_lsl_{project_id}",
                help="Valor mínimo aceitável"
            )
        else:
            lsl = None
    
    with col4:
        if spec_type in ["Bilateral", "Superior apenas"]:
            usl = st.number_input(
                "USL (Limite Superior de Especificação):",
                value=float(capability_data.get('usl', mean_val + 3*std_val)),
                key=f"capability_usl_{project_id}",
                help="Valor máximo aceitável"
            )
        else:
            usl = None
    
    # Botão para executar análise
    if st.button("🔍 Analisar Capacidade", key=f"analyze_capability_{project_id}", type="primary"):
        
        with st.spinner("📊 Calculando índices de capacidade..."):
            # Calcular índices
            results = _calculate_capability_advanced(data_col, lsl, usl)
            
            if results is None:
                st.error("❌ Erro no cálculo dos índices")
                return
            
            # Determinar status da capacidade
            capability_status = _determine_capability_status(results.get('Cpk'))
            
            # Salvar resultados na sessão
            capability_data.update({
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
                'analysis_date': datetime.now().isoformat(),
                'analysis_completed': True
            })
            
            st.session_state[session_key] = capability_data
            
            # Mostrar resultados
            _show_capability_results(results, capability_status, data_col, lsl, usl, selected_column, mean_val, std_val)
    
    # Mostrar botões de ação se análise foi executada
    if capability_data.get('analysis_completed'):
        _show_capability_action_buttons(manager, tool_name, capability_data)


def _show_saved_capability_results(capability_data: Dict):
    """Mostra resultados salvos da análise de capacidade"""
    st.markdown(f"**Variável Analisada:** {capability_data.get('variable', 'N/A')}")
    st.markdown(f"**Data da Análise:** {capability_data.get('analysis_date', 'N/A')[:19]}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cp_val = capability_data.get('cp')
        if cp_val is not None:
            st.metric("Cp", f"{cp_val:.3f}")
        else:
            st.metric("Cp", "N/A")
    
    with col2:
        cpk_val = capability_data.get('cpk')
        if cpk_val is not None:
            st.metric("Cpk", f"{cpk_val:.3f}")
        else:
            st.metric("Cpk", "N/A")
    
    with col3:
        st.metric("Status", capability_data.get('capability_status', 'N/A'))
    
    with col4:
        defect_rate = capability_data.get('defect_rate')
        if defect_rate is not None:
            st.metric("Taxa de Defeitos", f"{defect_rate:.2f}%")
        else:
            st.metric("Taxa de Defeitos", "N/A")


def _show_capability_results(results: Dict, capability_status: str, data_col, lsl, usl, selected_column: str, mean_val: float, std_val: float):
    """Mostra resultados da análise de capacidade"""
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
        elif cpk_value >= 1.33:
            st.success("🟢 **Capaz:** Processo capaz (1.33 ≤ Cpk < 2.0)")
        elif cpk_value >= 1.0:
            st.warning("🟡 **Marginal:** Processo marginalmente capaz (1.0 ≤ Cpk < 1.33)")
        else:
            st.error("🔴 **Não Capaz:** Processo não capaz (Cpk < 1.0)")
    
    # Taxa de defeitos
    if results['defect_rate'] is not None:
        st.markdown(f"**Taxa de Defeitos Estimada:** {results['defect_rate']:.4f}%")
    
    # Gráfico de capacidade
    st.markdown("### 📊 Visualização da Capacidade")
    
    try:
        fig = go.Figure()
        
        # Histograma dos dados
        fig.add_trace(go.Histogram(
            x=data_col,
            nbinsx=30,
            name="Distribuição dos Dados",
            opacity=0.7,
            marker_color='lightblue'
        ))
        
        # Curva normal teórica (se scipy disponível)
        if SCIPY_AVAILABLE:
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
        
    except Exception as e:
        st.warning(f"⚠️ Erro ao gerar gráfico: {str(e)}")


def _show_capability_action_buttons(manager: MeasurePhaseManager, tool_name: str, capability_data: Dict):
    """Botões de ação para capacidade do processo"""
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Salvar Análise", key=f"save_{tool_name}_{manager.project_id}"):
            success = manager.save_tool_data(tool_name, capability_data, completed=False)
            if success:
                st.success("💾 Análise de capacidade salva com sucesso!")
            else:
                st.error("❌ Erro ao salvar análise")
    
    with col2:
        if st.button("✅ Finalizar Capacidade", key=f"complete_{tool_name}_{manager.project_id}"):
            # Validar se análise foi executada
            if capability_data.get('analysis_completed'):
                success = manager.save_tool_data(tool_name, capability_data, completed=True)
                if success:
                    st.success("✅ Análise de capacidade finalizada com sucesso!")
                    st.balloons()
                    # Forçar atualização da interface
                    st.rerun()
                else:
                    st.error("❌ Erro ao finalizar análise")
            else:
                st.error("❌ Execute a análise antes de finalizar")


def _determine_capability_status(cpk_value) -> str:
    """Determina o status da capacidade baseado no Cpk"""
    if cpk_value is None:
        return "Indeterminado"
    
    if cpk_value >= 2.0:
        return "Excelente"
    elif cpk_value >= 1.33:
        return "Capaz"
    elif cpk_value >= 1.0:
        return "Marginal"
    else:
        return "Não Capaz"


def _calculate_capability_advanced(data, lsl=None, usl=None):
    """Calcular índices de capacidade - VERSÃO MELHORADA"""
    try:
        if len(data) == 0:
            return None
        
        mean_val = data.mean()
        std_val = data.std()
        
        if std_val == 0:
            st.warning("⚠️ Desvio padrão é zero - não é possível calcular índices")
            return None
        
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
            results['Ppk'] = results['Cpk']  # Simplificado para esta versão
            
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
        st.error(f"❌ Erro no cálculo: {str(e)}")
        return None


def show_msa_analysis(project_data: Dict):
    """MSA - Análise do Sistema de Medição - VERSÃO CORRIGIDA"""
    
    # Usar o manager como as outras ferramentas
    manager = MeasurePhaseManager(project_data)
    project_id = manager.project_id
    tool_name = "msa"
    
    st.markdown("## 🎯 MSA - Sistema de Medição")
    
    # Status da ferramenta
    is_completed = manager.is_tool_completed(tool_name)
    if is_completed:
        st.success("✅ **MSA finalizado**")
    else:
        st.info("⏳ **MSA em desenvolvimento**")
    
    # Inicializar dados da sessão
    session_key = f"{tool_name}_{project_id}"
    if session_key not in st.session_state:
        existing_data = manager.get_tool_data(tool_name)
        st.session_state[session_key] = existing_data if existing_data else {}
    
    msa_data = st.session_state[session_key]
    
    # Mostrar resultados salvos se existirem
    if msa_data and msa_data.get('analysis_completed'):
        st.markdown("### 📊 Resultados do MSA")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("R&R (%)", f"{msa_data.get('rr_percent', 0):.1f}%")
        with col2:
            st.metric("Interpretação", msa_data.get('interpretation', 'N/A'))
        with col3:
            st.metric("Medições", msa_data.get('total_measurements', 0))
        
        st.divider()
        
        if not st.checkbox("🔄 Refazer MSA", key=f"redo_msa_{project_id}"):
            _show_msa_action_buttons(manager, tool_name, msa_data)
            return
    
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
        num_operators = st.number_input(
            "Operadores", 
            min_value=2, max_value=5, 
            value=msa_data.get('num_operators', 3), 
            key=f"msa_ops_{project_id}"
        )
    with col2:
        num_parts = st.number_input(
            "Peças", 
            min_value=5, max_value=20, 
            value=msa_data.get('num_parts', 10), 
            key=f"msa_parts_{project_id}"
        )
    with col3:
        num_trials = st.number_input(
            "Repetições", 
            min_value=2, max_value=5, 
            value=msa_data.get('num_trials', 3), 
            key=f"msa_trials_{project_id}"
        )
    
    # Gerar template
    if st.button("📥 Gerar Template MSA", key=f"gen_msa_template_{project_id}"):
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
            "text/csv",
            key=f"download_msa_template_{project_id}"
        )
    
    # Upload MSA
    msa_file = st.file_uploader(
        "Upload dados MSA", 
        type=['csv', 'xlsx'], 
        key=f"msa_file_upload_{project_id}"
    )
    
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
                    
                    if len(msa_df) == 0:
                        st.error("❌ Nenhuma medição válida encontrada")
                        return
                    
                    # Cálculo básico de R&R
                    total_var = msa_df['Medição'].var()
                    
                    if total_var == 0:
                        st.warning("⚠️ Variância total é zero")
                        return
                    
                    part_var = msa_df.groupby('Peça')['Medição'].mean().var()
                    rr_var = max(0, total_var - part_var)  # Evitar valores negativos
                    
                    rr_percent = (rr_var / total_var) * 100 if total_var > 0 else 0
                    
                    # Interpretação
                    if rr_percent < 10:
                        interpretation = "Excelente"
                    elif rr_percent < 30:
                        interpretation = "Aceitável"
                    else:
                        interpretation = "Inadequado"
                    
                    # Mostrar resultados
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
                    
                    # Salvar resultados
                    msa_data.update({
                        'num_operators': num_operators,
                        'num_parts': num_parts,
                        'num_trials': num_trials,
                        'total_measurements': len(msa_df),
                        'rr_percent': float(rr_percent),
                        'interpretation': interpretation,
                        'analysis_date': datetime.now().isoformat(),
                        'analysis_completed': True
                    })
                    
                    st.session_state[session_key] = msa_data
                    
                    # Mostrar botões de ação
                    _show_msa_action_buttons(manager, tool_name, msa_data)
                    
                except Exception as e:
                    st.error(f"❌ Erro na análise MSA: {str(e)}")
            else:
                st.error(f"❌ Colunas obrigatórias: {required_cols}")
                st.write("**Colunas encontradas:**", list(msa_df.columns))
                
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")


def _show_msa_action_buttons(manager: MeasurePhaseManager, tool_name: str, msa_data: Dict):
    """Botões de ação para MSA"""
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Salvar MSA", key=f"save_{tool_name}_{manager.project_id}"):
            success = manager.save_tool_data(tool_name, msa_data, completed=False)
            if success:
                st.success("💾 MSA salvo com sucesso!")
            else:
                st.error("❌ Erro ao salvar MSA")
    
    with col2:
        if st.button("✅ Finalizar MSA", key=f"complete_{tool_name}_{manager.project_id}"):
            if msa_data.get('analysis_completed'):
                success = manager.save_tool_data(tool_name, msa_data, completed=True)
                if success:
                    st.success("✅ MSA finalizado com sucesso!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Erro ao finalizar MSA")
            else:
                st.error("❌ Execute a análise MSA antes de finalizar")


def show_baseline_metrics(project_data: Dict):
    """Baseline e Métricas CTQ - VERSÃO CORRIGIDA"""
    
    # Usar o manager como as outras ferramentas
    manager = MeasurePhaseManager(project_data)
    project_id = manager.project_id
    tool_name = "baseline_data"
    
    st.markdown("## 📈 Baseline e Métricas CTQ")
    st.markdown("Defina as métricas críticas para qualidade e estabeleça o baseline do processo.")
    
    # Status da ferramenta
    is_completed = manager.is_tool_completed(tool_name)
    if is_completed:
        st.success("✅ **Baseline finalizado**")
    else:
        st.info("⏳ **Baseline em desenvolvimento**")
    
    # Inicializar dados da sessão
    session_key = f"{tool_name}_{project_id}"
    if session_key not in st.session_state:
        existing_data = manager.get_tool_data(tool_name)
        # Garantir estrutura correta para projetos antigos e novos
        if not existing_data:
            existing_data = {'ctq_metrics': []}
        elif 'ctq_metrics' not in existing_data:
            existing_data['ctq_metrics'] = []
        elif not isinstance(existing_data.get('ctq_metrics'), list):
            existing_data['ctq_metrics'] = []
        st.session_state[session_key] = existing_data
                                                                             
    
    baseline_data = st.session_state[session_key]
    if 'ctq_metrics' not in baseline_data or baseline_data['ctq_metrics'] is None:
    baseline_data['ctq_metrics'] = []
    st.session_state[session_key] = baseline_data    
    
    # Adicionar CTQ
    st.markdown("### 🎯 Métricas CTQ (Critical to Quality)")
    
    with st.expander("➕ Adicionar Nova Métrica CTQ"):
        col1, col2 = st.columns(2)
        with col1:
            ctq_name = st.text_input("Nome da Métrica *", key=f"baseline_ctq_name_{project_id}")
            ctq_baseline = st.number_input("Valor Baseline *", key=f"baseline_ctq_baseline_{project_id}")
        with col2:
            ctq_target = st.number_input("Meta *", key=f"baseline_ctq_target_{project_id}")
            ctq_unit = st.text_input("Unidade", key=f"baseline_ctq_unit_{project_id}")
        
        ctq_description = st.text_area(
            "Descrição/Como Medir",
            key=f"baseline_ctq_description_{project_id}",
            placeholder="Descreva como esta métrica é calculada ou medida..."
        )
        
        if st.button("➕ Adicionar CTQ", key=f"add_baseline_ctq_{project_id}"):
            if ctq_name.strip() and ctq_baseline is not None and ctq_target is not None:
                baseline_data['ctq_metrics'].append({
                    'name': ctq_name.strip(),
                    'baseline': float(ctq_baseline),
                    'target': float(ctq_target),
                    'unit': ctq_unit,
                    'description': ctq_description
                })
                st.session_state[session_key] = baseline_data
                st.success(f"✅ CTQ '{ctq_name}' adicionada!")
                st.rerun()
            else:
                st.error("❌ Preencha nome, baseline e meta")
    
    # Mostrar CTQs existentes
    if baseline_data['ctq_metrics']:
        st.markdown("#### 📊 Métricas CTQ Definidas")
        
        for i, ctq in enumerate(baseline_data['ctq_metrics']):
            with st.expander(f"**{ctq['name']}** - Baseline: {ctq['baseline']} {ctq['unit']}"):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**Baseline:** {ctq['baseline']} {ctq['unit']}")
                    st.write(f"**Meta:** {ctq['target']} {ctq['unit']}")
                    if ctq.get('description'):
                        st.write(f"**Descrição:** {ctq['description']}")
                    
                    # Calcular diferença
                    diff = ctq['target'] - ctq['baseline']
                    improvement = (abs(diff) / ctq['baseline'] * 100) if ctq['baseline'] != 0 else 0
                    st.write(f"**Melhoria Alvo:** {improvement:.1f}%")
                
                with col2:
                    # Visualização simples
                    if ctq['baseline'] != 0:
                        progress_val = min(1.0, ctq['target'] / ctq['baseline']) if ctq['baseline'] > 0 else 0
                        st.progress(progress_val)
                        st.caption("Progresso para meta")
                
                with col3:
                    if st.button("🗑️", key=f"remove_baseline_ctq_{i}_{project_id}"):
                        baseline_data['ctq_metrics'].pop(i)
                        st.session_state[session_key] = baseline_data
                        st.success("✅ CTQ removida!")
                        st.rerun()
    else:
        st.info("📝 Nenhuma métrica CTQ definida ainda. Adicione pelo menos uma para continuar.")
    
    # Informações adicionais do baseline
    st.markdown("### 📅 Informações do Baseline")
    
    col1, col2 = st.columns(2)
    with col1:
        baseline_period = st.text_input(
            "Período do Baseline *",
            value=baseline_data.get('baseline_period', ''),
            placeholder="Ex: Janeiro a Março 2024",
            key=f"baseline_period_input_{project_id}",
            help="Período de referência para os dados baseline"
        )
        baseline_data['baseline_period'] = baseline_period
        
    with col2:
        data_source = st.text_input(
            "Fonte dos Dados *",
            value=baseline_data.get('data_source', ''),
            placeholder="Ex: Sistema ERP, Planilhas de controle",
            key=f"baseline_data_source_{project_id}",
            help="De onde vêm os dados do baseline"
        )
        baseline_data['data_source'] = data_source
    
    baseline_notes = st.text_area(
        "Observações/Contexto",
        value=baseline_data.get('baseline_notes', ''),
        placeholder="Informações adicionais sobre o contexto do baseline...",
        key=f"baseline_notes_{project_id}"
    )
    baseline_data['baseline_notes'] = baseline_notes
    
    # Botões de ação
    _show_baseline_action_buttons(manager, tool_name, baseline_data)


def _show_baseline_action_buttons(manager: MeasurePhaseManager, tool_name: str, baseline_data: Dict):
    """Botões de ação para baseline"""
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Salvar Baseline", key=f"save_{tool_name}_{manager.project_id}"):
            success = manager.save_tool_data(tool_name, baseline_data, completed=False)
            if success:
                st.success("💾 Baseline salvo com sucesso!")
            else:
                st.error("❌ Erro ao salvar baseline")
    
    with col2:
        if st.button("✅ Finalizar Baseline", key=f"complete_{tool_name}_{manager.project_id}"):
            # Validação
            if _validate_baseline_data(baseline_data):
                success = manager.save_tool_data(tool_name, baseline_data, completed=True)
                if success:
                    st.success("✅ Baseline finalizado com sucesso!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Erro ao finalizar baseline")
            else:
                st.error("❌ Complete todos os campos obrigatórios")


def _validate_baseline_data(baseline_data: Dict) -> bool:
    """Valida dados do baseline"""
    # Verificar CTQs
    if not baseline_data.get('ctq_metrics'):
        st.error("❌ Adicione pelo menos uma métrica CTQ")
        return False
    
    # Verificar período
    if not baseline_data.get('baseline_period', '').strip():
        st.error("❌ Defina o período do baseline")
        return False
    
    # Verificar fonte
    if not baseline_data.get('data_source', '').strip():
        st.error("❌ Defina a fonte dos dados")
        return False
    
    return True

