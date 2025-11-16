import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List
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
    """Upload e Análise de Dados - VERSÃO SIMPLIFICADA"""
    
    project_id = project_data.get('id')
    
    st.markdown("## 📁 Upload e Análise de Dados")
    
    # Upload
    uploaded_file = st.file_uploader(
        "Escolha um arquivo",
        type=['csv', 'xlsx', 'xls'],
        key=f"file_upload_{project_id}"
    )
    
    if uploaded_file is not None:
        try:
            # Ler arquivo
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Salvar no session_state
            st.session_state[f'uploaded_data_{project_id}'] = df
            st.session_state[f'file_name_{project_id}'] = uploaded_file.name
            
            st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
            
            # Info básica
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Linhas", df.shape[0])
            with col2:
                st.metric("Colunas", df.shape[1])
            with col3:
                numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
                st.metric("Colunas Numéricas", numeric_cols)
            
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo: {str(e)}")
    
    # Análise dos dados carregados
    if f'uploaded_data_{project_id}' in st.session_state:
        df = st.session_state[f'uploaded_data_{project_id}']
        file_name = st.session_state[f'file_name_{project_id}']
        
        st.markdown("### 📊 Análise dos Dados")
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["👀 Dados", "📈 Estatísticas", "📊 Gráficos"])
        
        with tab1:
            st.dataframe(df.head(10), use_container_width=True)
        
        with tab2:
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if numeric_columns:
                selected_cols = st.multiselect(
                    "Selecione colunas:",
                    numeric_columns,
                    default=numeric_columns[:3],
                    key=f"selected_cols_{project_id}"
                )
                
                if selected_cols:
                    st.dataframe(df[selected_cols].describe(), use_container_width=True)
            else:
                st.warning("⚠️ Nenhuma coluna numérica encontrada")
        
        with tab3:
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if numeric_columns:
                chart_type = st.selectbox("Tipo de Gráfico", ["Histograma", "Box Plot", "Scatter"])
                
                if chart_type == "Histograma":
                    col_to_plot = st.selectbox("Coluna:", numeric_columns)
                    fig = px.histogram(df, x=col_to_plot, title=f"Histograma - {col_to_plot}")
                    st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "Box Plot":
                    cols_to_plot = st.multiselect("Colunas:", numeric_columns, default=numeric_columns[:2])
                    if cols_to_plot:
                        fig = go.Figure()
                        for col in cols_to_plot:
                            fig.add_trace(go.Box(y=df[col], name=col))
                        fig.update_layout(title="Box Plot")
                        st.plotly_chart(fig, use_container_width=True)
        
        # Salvar análise
        if st.button("💾 Salvar Análise", key=f"save_analysis_{project_id}"):
            analysis_data = {
                'file_name': file_name,
                'rows': df.shape[0],
                'columns': df.shape[1],
                'numeric_columns': len(df.select_dtypes(include=[np.number]).columns),
                'upload_date': datetime.now().isoformat()
            }
            
            _save_tool_data(project_id, 'file_upload', analysis_data, True)
            st.success("✅ Análise salva!")


def show_process_capability(project_data: Dict):
    """Análise de Capacidade do Processo - VERSÃO SIMPLIFICADA"""
    
    project_id = project_data.get('id')
    
    st.markdown("## 📐 Análise de Capacidade do Processo")
    
    # Verificar se há dados
    if f'uploaded_data_{project_id}' not in st.session_state:
        st.warning("⚠️ Primeiro faça upload dos dados")
        return
    
    df = st.session_state[f'uploaded_data_{project_id}']
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_columns:
        st.error("❌ Nenhuma coluna numérica encontrada")
        return
    
    # Configuração
    col1, col2 = st.columns(2)
    
    with col1:
        selected_column = st.selectbox("Variável para análise:", numeric_columns, key=f"cap_col_{project_id}")
    
    with col2:
        spec_type = st.selectbox("Tipo de Especificação:", ["Bilateral", "Superior", "Inferior"], key=f"spec_type_{project_id}")
    
    # Limites
    data_col = df[selected_column].dropna()
    if len(data_col) == 0:
        st.error("❌ Coluna sem dados válidos")
        return
    
    mean_val = data_col.mean()
    std_val = data_col.std()
    
    col3, col4 = st.columns(2)
    with col3:
        if spec_type in ["Bilateral", "Inferior"]:
            lsl = st.number_input("LSL", value=float(mean_val - 2*std_val), key=f"lsl_{project_id}")
        else:
            lsl = None
    
    with col4:
        if spec_type in ["Bilateral", "Superior"]:
            usl = st.number_input("USL", value=float(mean_val + 2*std_val), key=f"usl_{project_id}")
        else:
            usl = None
    
    if st.button("🔍 Analisar Capacidade", key=f"analyze_cap_{project_id}"):
        # Calcular índices
        results = _calculate_capability(data_col, lsl, usl)
        
        # Mostrar resultados
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cp", f"{results['Cp']:.3f}" if results['Cp'] else "N/A")
        with col2:
            st.metric("Cpk", f"{results['Cpk']:.3f}" if results['Cpk'] else "N/A")
        with col3:
            # Interpretação
            if results['Cpk']:
                if results['Cpk'] >= 1.33:
                    st.success("✅ Capaz")
                elif results['Cpk'] >= 1.0:
                    st.warning("⚠️ Marginal")
                else:
                    st.error("❌ Não Capaz")
        
        # Gráfico
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=data_col, nbinsx=30, name="Dados"))
        
        if lsl:
            fig.add_vline(x=lsl, line_dash="dash", line_color="red", annotation_text="LSL")
        if usl:
            fig.add_vline(x=usl, line_dash="dash", line_color="red", annotation_text="USL")
        
        fig.update_layout(title="Análise de Capacidade", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Salvar
        if st.button("💾 Salvar Capacidade", key=f"save_cap_{project_id}"):
            cap_data = {
                'variable': selected_column,
                'spec_type': spec_type,
                'lsl': float(lsl) if lsl else None,
                'usl': float(usl) if usl else None,
                'cp': float(results['Cp']) if results['Cp'] else None,
                'cpk': float(results['Cpk']) if results['Cpk'] else None,
                'analysis_date': datetime.now().isoformat()
            }
            
            _save_tool_data(project_id, 'capability', cap_data, True)
            st.success("✅ Capacidade salva!")


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
        existing_data = project_data.get('measure', {}).get('baseline', {}).get('data', {})
        st.session_state[baseline_key] = existing_data if existing_data else {'ctq_metrics': []}
    
    baseline_data = st.session_state[baseline_key]
    
    # Status
    is_completed = project_data.get('measure', {}).get('baseline', {}).get('completed', False)
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
            _save_tool_data(project_id, 'baseline', {
                'ctq_metrics': baseline_data['ctq_metrics'],
                'baseline_period': baseline_period,
                'data_source': data_source
            }, False)
            st.success("💾 Salvo!")
    
    with col2:
        if st.button("✅ Finalizar", key=f"complete_baseline_{project_id}"):
            if baseline_data['ctq_metrics'] and baseline_period.strip():
                _save_tool_data(project_id, 'baseline', {
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


def _calculate_capability(data, lsl=None, usl=None):
    """Calcular índices de capacidade"""
    try:
        mean_val = data.mean()
        std_val = data.std()
        
        results = {'Cp': None, 'Cpk': None}
        
        if lsl is not None and usl is not None and std_val > 0:
            results['Cp'] = (usl - lsl) / (6 * std_val)
            cpu = (usl - mean_val) / (3 * std_val)
            cpl = (mean_val - lsl) / (3 * std_val)
            results['Cpk'] = min(cpu, cpl)
        elif usl is not None and std_val > 0:
            results['Cpk'] = (usl - mean_val) / (3 * std_val)
        elif lsl is not None and std_val > 0:
            results['Cpk'] = (mean_val - lsl) / (3 * std_val)
        
        return results
    except:
        return {'Cp': None, 'Cpk': None}


def show_measure_tools(project_data: Dict):
    """Função principal para mostrar as ferramentas da fase Measure - VERSÃO CORRIGIDA"""
    
    if not project_data:
        st.error("❌ Projeto não encontrado")
        return
    
    project_id = project_data.get('id')
    
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
    
    # Selectbox para navegação
    tool_names_with_status = []
    tool_keys = list(tool_options.keys())
    
    for key, name in tool_options.items():
        tool_data = measure_data.get(key, {})
        is_completed = tool_data.get('completed', False) if isinstance(tool_data, dict) else False
        status_icon = "✅" if is_completed else "⏳"
        tool_names_with_status.append(f"{status_icon} {name}")
    
    selected_index = st.selectbox(
        "Selecione uma ferramenta:",
        range(len(tool_names_with_status)),
        format_func=lambda x: tool_names_with_status[x],
        key=f"measure_tool_selector_{project_id}"
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
    st.markdown("#### 📋 Status das Ferramentas:")
    cols = st.columns(len(tool_options))
    
    for i, (key, name) in enumerate(tool_options.items()):
        tool_data = updated_measure_data.get(key, {})
        is_completed = tool_data.get('completed', False) if isinstance(tool_data, dict) else False
        
        if is_completed:
            completed_tools += 1
        
        with cols[i]:
            if is_completed:
                st.success(f"✅ {name.split(' ', 1)[1]}")
            else:
                st.info(f"⏳ {name.split(' ', 1)[1]}")
    
    progress = (completed_tools / total_tools) * 100
    
    # Barra de progresso
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
    
    # Debug (opcional)
    if st.checkbox("🔍 Debug - Mostrar dados Measure", key=f"debug_measure_{project_id}"):
        st.json(updated_measure_data)
