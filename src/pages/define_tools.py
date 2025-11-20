import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List
from src.utils.project_manager import ProjectManager
from src.utils.formatters import format_currency, format_date_br

def show_project_charter(project_data: Dict):
    """Project Charter - VERSÃO COMPLETAMENTE REESCRITA"""
    
    project_manager = ProjectManager()
    project_id = project_data.get('id')
    
    st.markdown("## 📋 Project Charter")
    st.markdown("O Project Charter é o documento oficial que autoriza e define o projeto.")
    
    # Inicializar dados no session_state se não existirem
    charter_key = f"charter_data_{project_id}"
    if charter_key not in st.session_state:
        # Carregar dados existentes do projeto
        existing_data = project_data.get('define', {}).get('charter', {}).get('data', {})
        st.session_state[charter_key] = existing_data if existing_data else {}
    
    # Status atual
    is_completed = project_data.get('define', {}).get('charter', {}).get('completed', False)
    if is_completed:
        st.success("✅ Charter finalizado")
    else:
        st.info("⏳ Charter em desenvolvimento")
    
    # Usar dados do session_state
    charter_data = st.session_state[charter_key]
    
    # Seção 1: Definição do Projeto
    st.markdown("### 🎯 Definição do Projeto")
    
    col1, col2 = st.columns(2)
    
    with col1:
        problem_statement = st.text_area(
            "Declaração do Problema *",
            value=charter_data.get('problem_statement', ''),
            placeholder="Descreva claramente o problema que será resolvido...",
            height=100,
            key=f"problem_statement_{project_id}",
            help="O que está errado? Qual é o problema específico?"
        )
        
        scope_included = st.text_area(
            "Escopo - O que está INCLUÍDO",
            value=charter_data.get('scope_included', ''),
            placeholder="Processos, áreas, produtos incluídos...",
            height=80,
            key=f"scope_included_{project_id}"
        )
    
    with col2:
        goal_statement = st.text_area(
            "Declaração do Objetivo *",
            value=charter_data.get('goal_statement', ''),
            placeholder="O que queremos alcançar com este projeto...",
            height=100,
            key=f"goal_statement_{project_id}",
            help="Objetivo SMART do projeto"
        )
        
        scope_excluded = st.text_area(
            "Escopo - O que está EXCLUÍDO",
            value=charter_data.get('scope_excluded', ''),
            placeholder="O que NÃO será abordado neste projeto...",
            height=80,
            key=f"scope_excluded_{project_id}"
        )
    
    # Seção 2: Métricas e Benefícios
    st.markdown("### 📊 Métricas e Benefícios")
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        primary_metric = st.text_input(
            "Métrica Principal *",
            value=charter_data.get('primary_metric', ''),
            placeholder="Ex: Taxa de defeitos, Tempo de ciclo...",
            key=f"primary_metric_{project_id}",
            help="Principal indicador que será melhorado"
        )
    
    with col4:
        baseline_value = st.text_input(
            "Valor Atual (Baseline)",
            value=charter_data.get('baseline_value', ''),
            placeholder="Ex: 15%, 30 minutos, 50 defeitos/mês...",
            key=f"baseline_value_{project_id}",
            help="Situação atual da métrica"
        )
    
    with col5:
        target_value = st.text_input(
            "Meta (Target) *",
            value=charter_data.get('target_value', ''),
            placeholder="Ex: 5%, 20 minutos, 10 defeitos/mês...",
            key=f"target_value_{project_id}",
            help="Onde queremos chegar"
        )
    
    financial_benefit = st.number_input(
        "Benefício Financeiro Anual (R$)",
        value=float(charter_data.get('financial_benefit', 0)),
        min_value=0.0,
        step=1000.0,
        key=f"financial_benefit_{project_id}",
        help="Impacto financeiro esperado por ano"
    )
    
    # Seção 3: Cronograma
    st.markdown("### 📅 Cronograma")
    
    duration_options = ["3 meses", "4 meses", "5 meses", "6 meses", "Outro"]
    current_duration = charter_data.get('project_duration', '4 meses')
    
    try:
        duration_index = duration_options.index(current_duration)
    except ValueError:
        duration_index = 1
    
    project_duration = st.selectbox(
        "Duração Estimada",
        options=duration_options,
        index=duration_index,
        key=f"project_duration_{project_id}"
    )
    
    custom_duration = ""
    if project_duration == "Outro":
        custom_duration = st.text_input(
            "Especificar duração",
            value=charter_data.get('custom_duration', ''),
            placeholder="Ex: 8 semanas, 120 dias...",
            key=f"custom_duration_{project_id}"
        )
    
    # Seção 4: Equipe
    st.markdown("### 👥 Equipe do Projeto")
    
    col6, col7 = st.columns(2)
    
    with col6:
        project_leader = st.text_input(
            "Líder do Projeto (Green Belt) *",
            value=charter_data.get('project_leader', ''),
            placeholder="Nome do responsável pelo projeto",
            key=f"project_leader_{project_id}"
        )
        
        team_members = st.text_area(
            "Membros da Equipe",
            value=charter_data.get('team_members', ''),
            placeholder="Liste os membros da equipe (um por linha)",
            height=80,
            key=f"team_members_{project_id}"
        )
    
    with col7:
        sponsor = st.text_input(
            "Sponsor/Champion *",
            value=charter_data.get('sponsor', ''),
            placeholder="Nome do patrocinador do projeto",
            key=f"sponsor_{project_id}"
        )
        
        stakeholders = st.text_area(
            "Principais Stakeholders",
            value=charter_data.get('stakeholders', ''),
            placeholder="Pessoas impactadas pelo projeto (um por linha)",
            height=80,
            key=f"stakeholders_{project_id}"
        )
    
    # Seção 5: Riscos e Premissas
    st.markdown("### ⚠️ Riscos e Premissas")
    
    col8, col9 = st.columns(2)
    
    with col8:
        risks = st.text_area(
            "Principais Riscos",
            value=charter_data.get('risks', ''),
            placeholder="Liste os principais riscos do projeto...",
            height=100,
            key=f"risks_{project_id}"
        )
    
    with col9:
        assumptions = st.text_area(
            "Premissas",
            value=charter_data.get('assumptions', ''),
            placeholder="O que estamos assumindo como verdade...",
            height=100,
            key=f"assumptions_{project_id}"
        )
    
    # Botões de ação
    st.divider()
    
    col10, col11, col12 = st.columns([2, 1, 1])
    
    with col11:
        save_draft = st.button("💾 Salvar Rascunho", use_container_width=True, key=f"save_draft_{project_id}")
    
    with col12:
        complete_charter = st.button("✅ Finalizar Charter", use_container_width=True, type="primary", key=f"complete_charter_{project_id}")
    
    # Processar ações
    if save_draft or complete_charter:
        # Coletar todos os dados atuais dos campos
        current_data = {
            'problem_statement': st.session_state.get(f"problem_statement_{project_id}", ''),
            'goal_statement': st.session_state.get(f"goal_statement_{project_id}", ''),
            'scope_included': st.session_state.get(f"scope_included_{project_id}", ''),
            'scope_excluded': st.session_state.get(f"scope_excluded_{project_id}", ''),
            'primary_metric': st.session_state.get(f"primary_metric_{project_id}", ''),
            'baseline_value': st.session_state.get(f"baseline_value_{project_id}", ''),
            'target_value': st.session_state.get(f"target_value_{project_id}", ''),
            'financial_benefit': st.session_state.get(f"financial_benefit_{project_id}", 0),
            'project_duration': st.session_state.get(f"project_duration_{project_id}", '4 meses'),
            'custom_duration': st.session_state.get(f"custom_duration_{project_id}", ''),
            'project_leader': st.session_state.get(f"project_leader_{project_id}", ''),
            'sponsor': st.session_state.get(f"sponsor_{project_id}", ''),
            'team_members': st.session_state.get(f"team_members_{project_id}", ''),
            'stakeholders': st.session_state.get(f"stakeholders_{project_id}", ''),
            'risks': st.session_state.get(f"risks_{project_id}", ''),
            'assumptions': st.session_state.get(f"assumptions_{project_id}", ''),
            'last_saved': datetime.now().isoformat()
        }
        
        # Validar campos obrigatórios se estiver finalizando
        if complete_charter:
            required_fields = [
                (current_data['problem_statement'], "Declaração do Problema"),
                (current_data['goal_statement'], "Declaração do Objetivo"),
                (current_data['primary_metric'], "Métrica Principal"),
                (current_data['target_value'], "Meta (Target)"),
                (current_data['project_leader'], "Líder do Projeto"),
                (current_data['sponsor'], "Sponsor/Champion")
            ]
            
            missing_fields = [field_name for field_value, field_name in required_fields if not str(field_value).strip()]
            
            if missing_fields:
                st.error(f"❌ Campos obrigatórios não preenchidos: {', '.join(missing_fields)}")
                st.stop()
        
        # Salvar no session_state
        st.session_state[charter_key] = current_data
        
        # Preparar dados para Firebase
        update_data = {
            f'define.charter.data': current_data,
            f'define.charter.completed': complete_charter,
            f'define.charter.updated_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Tentar salvar no Firebase
        with st.spinner("💾 Salvando..."):
            try:
                success = project_manager.update_project(project_id, update_data)
                
                if success:
                    # Atualizar projeto no session_state
                    if 'current_project' in st.session_state:
                        if 'define' not in st.session_state.current_project:
                            st.session_state.current_project['define'] = {}
                        if 'charter' not in st.session_state.current_project['define']:
                            st.session_state.current_project['define']['charter'] = {}
                        
                        st.session_state.current_project['define']['charter']['data'] = current_data
                        st.session_state.current_project['define']['charter']['completed'] = complete_charter
                        st.session_state.current_project['define']['charter']['updated_at'] = datetime.now().isoformat()
                    
                    if complete_charter:
                        st.success("✅ Charter finalizado e salvo com sucesso!")
                        st.balloons()
                        
                        # Mostrar resumo
                        st.markdown("### 📊 Resumo do Charter")
                        col_sum1, col_sum2, col_sum3 = st.columns(3)
                        
                        with col_sum1:
                            st.metric("Métrica Principal", current_data['primary_metric'])
                        
                        with col_sum2:
                            baseline = current_data['baseline_value'] or 'N/A'
                            target = current_data['target_value'] or 'N/A'
                            st.metric("Meta", f"{baseline} → {target}")
                        
                        with col_sum3:
                            benefit = current_data['financial_benefit']
                            st.metric("Benefício Anual", format_currency(benefit))
                        
                    else:
                        st.success("💾 Rascunho salvo com sucesso!")
                        st.info("💡 Seus dados foram salvos. Continue editando ou finalize quando estiver pronto.")
                
                else:
                    st.error("❌ Erro ao salvar no Firebase, mas dados mantidos localmente")
                    
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {str(e)}")
                st.info("💾 Dados mantidos localmente nesta sessão")
    
    # Mostrar dados salvos para debug
    if st.checkbox("🔍 Mostrar dados salvos (debug)", key=f"debug_charter_{project_id}"):
        st.json(st.session_state.get(charter_key, {}))


def show_stakeholder_mapping(project_data: Dict):
    """Stakeholder Mapping - Mapeamento de Partes Interessadas"""
    
    project_manager = ProjectManager()
    project_id = project_data.get('id')
    
    st.markdown("## 👥 Stakeholder Mapping")
    st.markdown("Identifique e analise todas as partes interessadas que podem impactar ou ser impactadas pelo projeto.")
    
    # Inicializar dados no session_state
    stakeholder_key = f"stakeholder_data_{project_id}"
    if stakeholder_key not in st.session_state:
        existing_data = project_data.get('define', {}).get('stakeholders', {}).get('data', {})
        st.session_state[stakeholder_key] = existing_data if existing_data else {}
    
    # Status atual
    is_completed = project_data.get('define', {}).get('stakeholders', {}).get('completed', False)
    if is_completed:
        st.success("✅ Stakeholder Mapping finalizado")
    else:
        st.info("⏳ Stakeholder Mapping em desenvolvimento")
    
    stakeholder_data = st.session_state[stakeholder_key]
    
    # Seção 1: Lista de Stakeholders
    st.markdown("### 📝 Identificação dos Stakeholders")
    
    # Inicializar lista de stakeholders se não existir - CORREÇÃO AQUI
    if 'stakeholders' not in stakeholder_data or stakeholder_data['stakeholders'] is None:
        stakeholder_data['stakeholders'] = []
        st.session_state[stakeholder_key] = stakeholder_data  # Salvar a mudança
    
    # Adicionar novo stakeholder
    st.markdown("**Adicionar Novo Stakeholder:**")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        new_name = st.text_input("Nome/Grupo", key=f"new_stakeholder_name_{project_id}")
    
    with col2:
        influence_options = ["Alto", "Médio", "Baixo"]
        new_influence = st.selectbox("Influência", influence_options, key=f"new_influence_{project_id}")
    
    with col3:
        interest_options = ["Alto", "Médio", "Baixo"]
        new_interest = st.selectbox("Interesse", interest_options, key=f"new_interest_{project_id}")
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)  # Espaçamento
        if st.button("➕ Adicionar", key=f"add_stakeholder_{project_id}"):
            if new_name.strip():
                new_stakeholder = {
                    'name': new_name.strip(),
                    'influence': new_influence,
                    'interest': new_interest,
                    'role': '',
                    'expectations': '',
                    'communication_strategy': '',
                    'id': len(stakeholder_data['stakeholders'])
                }
                stakeholder_data['stakeholders'].append(new_stakeholder)
                st.session_state[stakeholder_key] = stakeholder_data  # Salvar mudança
                st.rerun()
    
    # Mostrar stakeholders existentes
    if stakeholder_data['stakeholders'] and len(stakeholder_data['stakeholders']) > 0:
        st.markdown("### 👥 Stakeholders Identificados")
        
        for i, stakeholder in enumerate(stakeholder_data['stakeholders']):
            with st.expander(f"**{stakeholder['name']}** - Influência: {stakeholder['influence']} | Interesse: {stakeholder['interest']}"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    stakeholder['role'] = st.text_input(
                        "Papel/Função",
                        value=stakeholder.get('role', ''),
                        key=f"role_{project_id}_{i}"
                    )
                    
                    stakeholder['expectations'] = st.text_area(
                        "Expectativas",
                        value=stakeholder.get('expectations', ''),
                        key=f"expectations_{project_id}_{i}",
                        height=80
                    )
                
                with col_b:
                    # Atualizar influência e interesse
                    stakeholder['influence'] = st.selectbox(
                        "Influência",
                        influence_options,
                        index=influence_options.index(stakeholder['influence']),
                        key=f"influence_{project_id}_{i}"
                    )
                    
                    stakeholder['interest'] = st.selectbox(
                        "Interesse",
                        interest_options,
                        index=interest_options.index(stakeholder['interest']),
                        key=f"interest_{project_id}_{i}"
                    )
                
                stakeholder['communication_strategy'] = st.text_area(
                    "Estratégia de Comunicação",
                    value=stakeholder.get('communication_strategy', ''),
                    key=f"communication_{project_id}_{i}",
                    height=60
                )
                
                if st.button(f"🗑️ Remover {stakeholder['name']}", key=f"remove_{project_id}_{i}"):
                    stakeholder_data['stakeholders'].pop(i)
                    st.session_state[stakeholder_key] = stakeholder_data  # Salvar mudança
                    st.rerun()
    
    # Matriz de Influência vs Interesse
    if stakeholder_data['stakeholders'] and len(stakeholder_data['stakeholders']) > 0:
        st.markdown("### 📊 Matriz Influência vs Interesse")
        
        # Preparar dados para o gráfico
        influence_map = {"Alto": 3, "Médio": 2, "Baixo": 1}
        interest_map = {"Alto": 3, "Médio": 2, "Baixo": 1}
        
        names = [s['name'] for s in stakeholder_data['stakeholders']]
        influences = [influence_map[s['influence']] for s in stakeholder_data['stakeholders']]
        interests = [interest_map[s['interest']] for s in stakeholder_data['stakeholders']]
        
        # Criar gráfico de dispersão
        fig = px.scatter(
            x=interests, y=influences, text=names,
            labels={'x': 'Interesse', 'y': 'Influência'},
            title="Matriz de Stakeholders"
        )
        
        fig.update_traces(textposition="top center", marker=dict(size=12))
        fig.update_xaxes(range=[0.5, 3.5], tickvals=[1, 2, 3], ticktext=['Baixo', 'Médio', 'Alto'])
        fig.update_yaxes(range=[0.5, 3.5], tickvals=[1, 2, 3], ticktext=['Baixo', 'Médio', 'Alto'])
        
        # Adicionar quadrantes
        fig.add_hline(y=2.5, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=2.5, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Adicionar anotações dos quadrantes
        fig.add_annotation(x=3.2, y=3.2, text="Gerenciar<br>de Perto", showarrow=False, font=dict(size=10))
        fig.add_annotation(x=1.2, y=3.2, text="Manter<br>Satisfeito", showarrow=False, font=dict(size=10))
        fig.add_annotation(x=3.2, y=1.2, text="Manter<br>Informado", showarrow=False, font=dict(size=10))
        fig.add_annotation(x=1.2, y=1.2, text="Monitorar", showarrow=False, font=dict(size=10))
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Botões de ação
    st.divider()
    col_save1, col_save2 = st.columns([1, 1])
    
    with col_save1:
        save_draft = st.button("💾 Salvar Rascunho", use_container_width=True, key=f"save_stakeholder_draft_{project_id}")
    
    with col_save2:
        complete_mapping = st.button("✅ Finalizar Mapping", use_container_width=True, type="primary", key=f"complete_stakeholder_{project_id}")
    
    # Processar ações
    if save_draft or complete_mapping:
        # Validação para finalizar
        if complete_mapping and len(stakeholder_data.get('stakeholders', [])) < 3:
            st.error("❌ Identifique pelo menos 3 stakeholders para finalizar o mapping")
            st.stop()
        
        # Salvar dados
        stakeholder_data['last_saved'] = datetime.now().isoformat()
        st.session_state[stakeholder_key] = stakeholder_data
        
        update_data = {
            f'define.stakeholders.data': stakeholder_data,
            f'define.stakeholders.completed': complete_mapping,
            f'define.stakeholders.updated_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        with st.spinner("💾 Salvando..."):
            try:
                success = project_manager.update_project(project_id, update_data)
                
                if success:
                    # Atualizar session_state
                    if 'current_project' in st.session_state:
                        if 'define' not in st.session_state.current_project:
                            st.session_state.current_project['define'] = {}
                        if 'stakeholders' not in st.session_state.current_project['define']:
                            st.session_state.current_project['define']['stakeholders'] = {}
                        
                        st.session_state.current_project['define']['stakeholders']['data'] = stakeholder_data
                        st.session_state.current_project['define']['stakeholders']['completed'] = complete_mapping
                    
                    if complete_mapping:
                        st.success("✅ Stakeholder Mapping finalizado com sucesso!")
                        st.balloons()
                    else:
                        st.success("💾 Rascunho salvo com sucesso!")
                
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {str(e)}")


def show_voice_of_customer(project_data: Dict):
    """Voice of Customer - Voz do Cliente"""
    
    project_manager = ProjectManager()
    project_id = project_data.get('id')
    
    st.markdown("## 🗣️ Voice of Customer (VoC)")
    st.markdown("Capture e analise as necessidades, expectativas e requisitos dos clientes.")
    
    # Inicializar dados
    voc_key = f"voc_data_{project_id}"
    if voc_key not in st.session_state:
        existing_data = project_data.get('define', {}).get('voc', {}).get('data', {})
        st.session_state[voc_key] = existing_data if existing_data else {}
    
    # Status atual
    is_completed = project_data.get('define', {}).get('voc', {}).get('completed', False)
    if is_completed:
        st.success("✅ Voice of Customer finalizado")
    else:
        st.info("⏳ Voice of Customer em desenvolvimento")
    
    voc_data = st.session_state[voc_key]
    
    # Seção 1: Métodos de Coleta
    st.markdown("### 📊 Métodos de Coleta de Dados")
    
    collection_methods = st.multiselect(
        "Métodos utilizados para coletar a voz do cliente:",
        ["Pesquisas/Surveys", "Entrevistas", "Focus Groups", "Observação Direta", 
         "Análise de Reclamações", "Feedback Online", "Dados Históricos", "Outros"],
        default=voc_data.get('collection_methods', []),
        key=f"collection_methods_{project_id}"
    )
    
    other_methods = ""
    if "Outros" in collection_methods:
        other_methods = st.text_input(
            "Especificar outros métodos:",
            value=voc_data.get('other_methods', ''),
            key=f"other_methods_{project_id}"
        )
    
    # Seção 2: Necessidades do Cliente
    st.markdown("### 🎯 Necessidades e Expectativas dos Clientes")
    
    # Inicializar lista de necessidades - CORREÇÃO AQUI
    if 'customer_needs' not in voc_data or voc_data['customer_needs'] is None:
        voc_data['customer_needs'] = []
        st.session_state[voc_key] = voc_data  # Salvar mudança
    
    # Adicionar nova necessidade
    st.markdown("**Adicionar Nova Necessidade:**")
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    
    with col1:
        new_need = st.text_input("Necessidade do Cliente", key=f"new_need_{project_id}")
    
    with col2:
        importance_options = ["Crítica", "Importante", "Desejável"]
        new_importance = st.selectbox("Importância", importance_options, key=f"new_importance_{project_id}")
    
    with col3:
        satisfaction_options = ["Muito Insatisfeito", "Insatisfeito", "Neutro", "Satisfeito", "Muito Satisfeito"]
        new_satisfaction = st.selectbox("Satisfação Atual", satisfaction_options, key=f"new_satisfaction_{project_id}")
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Adicionar", key=f"add_need_{project_id}"):
            if new_need.strip():
                new_customer_need = {
                    'need': new_need.strip(),
                    'importance': new_importance,
                    'satisfaction': new_satisfaction,
                    'frequency': '',
                    'impact': '',
                    'requirements': '',
                    'id': len(voc_data['customer_needs'])
                }
                voc_data['customer_needs'].append(new_customer_need)
                st.session_state[voc_key] = voc_data  # Salvar mudança
                st.rerun()
    
    # Mostrar necessidades existentes
    if voc_data['customer_needs'] and len(voc_data['customer_needs']) > 0:
        st.markdown("### 📋 Necessidades Identificadas")
        
        for i, need in enumerate(voc_data['customer_needs']):
            with st.expander(f"**{need['need']}** - {need['importance']} | {need['satisfaction']}"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    need['importance'] = st.selectbox(
                        "Importância",
                        importance_options,
                        index=importance_options.index(need['importance']),
                        key=f"importance_{project_id}_{i}"
                    )
                    
                    need['frequency'] = st.text_input(
                        "Frequência/Volume",
                        value=need.get('frequency', ''),
                        key=f"frequency_{project_id}_{i}",
                        placeholder="Ex: 80% dos clientes, 50 vezes por mês..."
                    )
                
                with col_b:
                    need['satisfaction'] = st.selectbox(
                        "Satisfação Atual",
                        satisfaction_options,
                        index=satisfaction_options.index(need['satisfaction']),
                        key=f"satisfaction_{project_id}_{i}"
                    )
                    
                    need['impact'] = st.text_input(
                        "Impacto no Negócio",
                        value=need.get('impact', ''),
                        key=f"impact_{project_id}_{i}",
                        placeholder="Ex: Perda de clientes, redução de vendas..."
                    )
                
                need['requirements'] = st.text_area(
                    "Requisitos Específicos",
                    value=need.get('requirements', ''),
                    key=f"requirements_{project_id}_{i}",
                    height=60,
                    placeholder="Como essa necessidade pode ser atendida?"
                )
                
                if st.button(f"🗑️ Remover", key=f"remove_need_{project_id}_{i}"):
                    voc_data['customer_needs'].pop(i)
                    st.session_state[voc_key] = voc_data  # Salvar mudança
                    st.rerun()
    
    # Seção 3: Análise e Priorização
    if voc_data['customer_needs'] and len(voc_data['customer_needs']) > 0:
        st.markdown("### 📊 Análise de Importância vs Satisfação")
        
        # Preparar dados para matriz
        importance_map = {"Crítica": 3, "Importante": 2, "Desejável": 1}
        satisfaction_map = {"Muito Insatisfeito": 1, "Insatisfeito": 2, "Neutro": 3, "Satisfeito": 4, "Muito Satisfeito": 5}
        
        needs_names = [n['need'] for n in voc_data['customer_needs']]
        importance_scores = [importance_map[n['importance']] for n in voc_data['customer_needs']]
        satisfaction_scores = [satisfaction_map[n['satisfaction']] for n in voc_data['customer_needs']]
        
        # Criar gráfico
        fig = px.scatter(
            x=satisfaction_scores, y=importance_scores, text=needs_names,
            labels={'x': 'Satisfação Atual', 'y': 'Importância'},
            title="Matriz Importância vs Satisfação"
        )
        
        fig.update_traces(textposition="top center", marker=dict(size=12))
        fig.update_xaxes(range=[0.5, 5.5], tickvals=[1, 2, 3, 4, 5], 
                        ticktext=['Muito Insatisfeito', 'Insatisfeito', 'Neutro', 'Satisfeito', 'Muito Satisfeito'])
        fig.update_yaxes(range=[0.5, 3.5], tickvals=[1, 2, 3], ticktext=['Desejável', 'Importante', 'Crítica'])
        
        # Adicionar linha de prioridade (alto impacto = baixa satisfação + alta importância)
        fig.add_vline(x=3, line_dash="dash", line_color="red", opacity=0.5)
        fig.add_hline(y=2.5, line_dash="dash", line_color="red", opacity=0.5)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Identificar prioridades
        priority_needs = [
            need for need in voc_data['customer_needs']
            if importance_map[need['importance']] >= 2 and satisfaction_map[need['satisfaction']] <= 3
        ]
        
        if priority_needs:
            st.markdown("### 🚨 Necessidades Prioritárias")
            st.info("Necessidades importantes/críticas com baixa satisfação atual:")
            for need in priority_needs:
                st.write(f"• **{need['need']}** - {need['importance']} | {need['satisfaction']}")
    
    # Seção 4: Insights e Conclusões
    st.markdown("### 💡 Insights e Conclusões")
    
    col_insights1, col_insights2 = st.columns(2)
    
    with col_insights1:
        key_insights = st.text_area(
            "Principais Insights",
            value=voc_data.get('key_insights', ''),
            key=f"key_insights_{project_id}",
            height=100,
            placeholder="Quais são os principais aprendizados sobre os clientes?"
        )
    
    with col_insights2:
        improvement_opportunities = st.text_area(
            "Oportunidades de Melhoria",
            value=voc_data.get('improvement_opportunities', ''),
            key=f"improvement_opportunities_{project_id}",
            height=100,
            placeholder="Onde podemos melhorar para atender melhor os clientes?"
        )
    
    # Botões de ação
    st.divider()
    col_save1, col_save2 = st.columns([1, 1])
    
    with col_save1:
        save_draft = st.button("💾 Salvar Rascunho", use_container_width=True, key=f"save_voc_draft_{project_id}")
    
    with col_save2:
        complete_voc = st.button("✅ Finalizar VoC", use_container_width=True, type="primary", key=f"complete_voc_{project_id}")
    
    # Processar ações
    if save_draft or complete_voc:
        # Coletar dados atuais
        current_data = {
            'collection_methods': st.session_state.get(f"collection_methods_{project_id}", []),
            'other_methods': st.session_state.get(f"other_methods_{project_id}", ''),
            'customer_needs': voc_data.get('customer_needs', []),
            'key_insights': st.session_state.get(f"key_insights_{project_id}", ''),
            'improvement_opportunities': st.session_state.get(f"improvement_opportunities_{project_id}", ''),
            'last_saved': datetime.now().isoformat()
        }
        
        # Validação para finalizar
        if complete_voc:
            if len(current_data['customer_needs']) < 3:
                st.error("❌ Identifique pelo menos 3 necessidades dos clientes para finalizar")
                st.stop()
            if not current_data['collection_methods']:
                st.error("❌ Selecione pelo menos um método de coleta de dados")
                st.stop()
        
        # Salvar dados
        st.session_state[voc_key] = current_data
        
        update_data = {
            f'define.voc.data': current_data,
            f'define.voc.completed': complete_voc,
            f'define.voc.updated_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        with st.spinner("💾 Salvando..."):
            try:
                success = project_manager.update_project(project_id, update_data)
                
                if success:
                    # Atualizar session_state
                    if 'current_project' in st.session_state:
                        if 'define' not in st.session_state.current_project:
                            st.session_state.current_project['define'] = {}
                        if 'voc' not in st.session_state.current_project['define']:
                            st.session_state.current_project['define']['voc'] = {}
                        
                        st.session_state.current_project['define']['voc']['data'] = current_data
                        st.session_state.current_project['define']['voc']['completed'] = complete_voc
                    
                    if complete_voc:
                        st.success("✅ Voice of Customer finalizado com sucesso!")
                        st.balloons()
                    else:
                        st.success("💾 Rascunho salvo com sucesso!")
                
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {str(e)}")


def show_sipoc_diagram(project_data: Dict):
    """SIPOC Diagram - Suppliers, Inputs, Process, Outputs, Customers"""
    
    project_manager = ProjectManager()
    project_id = project_data.get('id')
    
    st.markdown("## 📊 SIPOC Diagram")
    st.markdown("Mapeie o processo de alto nível identificando Fornecedores, Entradas, Processo, Saídas e Clientes.")
    
    # Inicializar dados
    sipoc_key = f"sipoc_data_{project_id}"
    if sipoc_key not in st.session_state:
        existing_data = project_data.get('define', {}).get('sipoc', {}).get('data', {})
        st.session_state[sipoc_key] = existing_data if existing_data else {}
    
    # Status atual
    is_completed = project_data.get('define', {}).get('sipoc', {}).get('completed', False)
    if is_completed:
        st.success("✅ SIPOC Diagram finalizado")
    else:
        st.info("⏳ SIPOC Diagram em desenvolvimento")
    
    sipoc_data = st.session_state[sipoc_key]
    
    # Inicializar estruturas de dados - CORREÇÃO AQUI
    for key in ['suppliers', 'inputs', 'process_steps', 'outputs', 'customers']:
        if key not in sipoc_data or sipoc_data[key] is None:
            sipoc_data[key] = []
    st.session_state[sipoc_key] = sipoc_data  # Salvar mudanças
    
    # Definição do processo principal
    st.markdown("### 🎯 Definição do Processo")
    
    process_name = st.text_input(
        "Nome do Processo Principal *",
        value=sipoc_data.get('process_name', ''),
        key=f"process_name_{project_id}",
        placeholder="Ex: Processo de Atendimento ao Cliente"
    )
    
    process_description = st.text_area(
        "Descrição do Processo",
        value=sipoc_data.get('process_description', ''),
        key=f"process_description_{project_id}",
        height=80,
        placeholder="Descreva brevemente o que este processo faz..."
    )
    
    st.divider()
    
    # Layout em abas para melhor organização
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏭 Suppliers", "📥 Inputs", "⚙️ Process", "📤 Outputs", "👥 Customers"])
    
    # Tab 1: Suppliers
    with tab1:
        st.markdown("### 🏭 Suppliers (Fornecedores)")
        st.markdown("Quem fornece as entradas para o processo?")
        
        # Adicionar supplier
        col1, col2 = st.columns([3, 1])
        with col1:
            new_supplier = st.text_input("Novo Fornecedor", key=f"new_supplier_{project_id}")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Adicionar", key=f"add_supplier_{project_id}"):
                if new_supplier.strip():
                    sipoc_data['suppliers'].append({
                        'name': new_supplier.strip(),
                        'type': 'Interno',
                        'description': '',
                        'id': len(sipoc_data['suppliers'])
                    })
                    st.session_state[sipoc_key] = sipoc_data
                    st.rerun()
        
        # Mostrar suppliers
        if sipoc_data['suppliers'] and len(sipoc_data['suppliers']) > 0:
            for i, supplier in enumerate(sipoc_data['suppliers']):
                with st.expander(f"**{supplier['name']}**"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        supplier['type'] = st.selectbox(
                            "Tipo",
                            ["Interno", "Externo", "Misto"],
                            index=["Interno", "Externo", "Misto"].index(supplier.get('type', 'Interno')),
                            key=f"supplier_type_{project_id}_{i}"
                        )
                    with col_b:
                        if st.button(f"🗑️ Remover", key=f"remove_supplier_{project_id}_{i}"):
                            sipoc_data['suppliers'].pop(i)
                            st.session_state[sipoc_key] = sipoc_data
                            st.rerun()
                    
                    supplier['description'] = st.text_area(
                        "Descrição/Observações",
                        value=supplier.get('description', ''),
                        key=f"supplier_desc_{project_id}_{i}",
                        height=60
                    )
    
    # Tab 2: Inputs
    with tab2:
        st.markdown("### 📥 Inputs (Entradas)")
        st.markdown("O que é necessário para executar o processo?")
        
        # Adicionar input
        col1, col2 = st.columns([3, 1])
        with col1:
            new_input = st.text_input("Nova Entrada", key=f"new_input_{project_id}")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Adicionar", key=f"add_input_{project_id}"):
                if new_input.strip():
                    sipoc_data['inputs'].append({
                        'name': new_input.strip(),
                        'type': 'Material',
                        'source': '',
                        'requirements': '',
                        'id': len(sipoc_data['inputs'])
                    })
                    st.session_state[sipoc_key] = sipoc_data
                    st.rerun()
        
        # Mostrar inputs
        if sipoc_data['inputs'] and len(sipoc_data['inputs']) > 0:
            for i, input_item in enumerate(sipoc_data['inputs']):
                with st.expander(f"**{input_item['name']}**"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        input_item['type'] = st.selectbox(
                            "Tipo",
                            ["Material", "Informação", "Serviço", "Recurso"],
                            index=["Material", "Informação", "Serviço", "Recurso"].index(input_item.get('type', 'Material')),
                            key=f"input_type_{project_id}_{i}"
                        )
                        
                        input_item['source'] = st.text_input(
                            "Fonte/Origem",
                            value=input_item.get('source', ''),
                            key=f"input_source_{project_id}_{i}"
                        )
                    
                    with col_b:
                        if st.button(f"🗑️ Remover", key=f"remove_input_{project_id}_{i}"):
                            sipoc_data['inputs'].pop(i)
                            st.session_state[sipoc_key] = sipoc_data
                            st.rerun()
                    
                    input_item['requirements'] = st.text_area(
                        "Requisitos/Especificações",
                        value=input_item.get('requirements', ''),
                        key=f"input_req_{project_id}_{i}",
                        height=60
                    )
    
    # Tab 3: Process
    with tab3:
        st.markdown("### ⚙️ Process (Processo)")
        st.markdown("Quais são os principais passos do processo?")
        
        # Adicionar step
        col1, col2 = st.columns([3, 1])
        with col1:
            new_step = st.text_input("Novo Passo", key=f"new_step_{project_id}")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Adicionar", key=f"add_step_{project_id}"):
                if new_step.strip():
                    sipoc_data['process_steps'].append({
                        'name': new_step.strip(),
                        'description': '',
                        'responsible': '',
                        'duration': '',
                        'order': len(sipoc_data['process_steps']) + 1,
                        'id': len(sipoc_data['process_steps'])
                    })
                    st.session_state[sipoc_key] = sipoc_data
                    st.rerun()
        
        # Mostrar steps
        if sipoc_data['process_steps'] and len(sipoc_data['process_steps']) > 0:
            for i, step in enumerate(sipoc_data['process_steps']):
                with st.expander(f"**{i+1}. {step['name']}**"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        step['responsible'] = st.text_input(
                            "Responsável",
                            value=step.get('responsible', ''),
                            key=f"step_responsible_{project_id}_{i}"
                        )
                    
                    with col_b:
                        step['duration'] = st.text_input(
                            "Duração Estimada",
                            value=step.get('duration', ''),
                            key=f"step_duration_{project_id}_{i}",
                            placeholder="Ex: 2 horas, 1 dia..."
                        )
                    
                    step['description'] = st.text_area(
                        "Descrição Detalhada",
                        value=step.get('description', ''),
                        key=f"step_desc_{project_id}_{i}",
                        height=60
                    )
                    
                    col_move, col_remove = st.columns(2)
                    with col_move:
                        if i > 0:
                            if st.button(f"⬆️ Mover para Cima", key=f"move_up_{project_id}_{i}"):
                                sipoc_data['process_steps'][i], sipoc_data['process_steps'][i-1] = sipoc_data['process_steps'][i-1], sipoc_data['process_steps'][i]
                                st.session_state[sipoc_key] = sipoc_data
                                st.rerun()
                        if i < len(sipoc_data['process_steps']) - 1:
                            if st.button(f"⬇️ Mover para Baixo", key=f"move_down_{project_id}_{i}"):
                                sipoc_data['process_steps'][i], sipoc_data['process_steps'][i+1] = sipoc_data['process_steps'][i+1], sipoc_data['process_steps'][i]
                                st.session_state[sipoc_key] = sipoc_data
                                st.rerun()
                    
                    with col_remove:
                        if st.button(f"🗑️ Remover", key=f"remove_step_{project_id}_{i}"):
                            sipoc_data['process_steps'].pop(i)
                            st.session_state[sipoc_key] = sipoc_data
                            st.rerun()
    
    # Tab 4: Outputs
    with tab4:
        st.markdown("### 📤 Outputs (Saídas)")
        st.markdown("O que o processo produz?")
        
        # Adicionar output
        col1, col2 = st.columns([3, 1])
        with col1:
            new_output = st.text_input("Nova Saída", key=f"new_output_{project_id}")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Adicionar", key=f"add_output_{project_id}"):
                if new_output.strip():
                    sipoc_data['outputs'].append({
                        'name': new_output.strip(),
                        'type': 'Produto',
                        'quality_criteria': '',
                        'destination': '',
                        'id': len(sipoc_data['outputs'])
                    })
                    st.session_state[sipoc_key] = sipoc_data
                    st.rerun()
        
        # Mostrar outputs
        if sipoc_data['outputs'] and len(sipoc_data['outputs']) > 0:
            for i, output in enumerate(sipoc_data['outputs']):
                with st.expander(f"**{output['name']}**"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        output['type'] = st.selectbox(
                            "Tipo",
                            ["Produto", "Serviço", "Informação", "Decisão"],
                            index=["Produto", "Serviço", "Informação", "Decisão"].index(output.get('type', 'Produto')),
                            key=f"output_type_{project_id}_{i}"
                        )
                        
                        output['destination'] = st.text_input(
                            "Destino",
                            value=output.get('destination', ''),
                            key=f"output_dest_{project_id}_{i}"
                        )
                    
                    with col_b:
                        if st.button(f"🗑️ Remover", key=f"remove_output_{project_id}_{i}"):
                            sipoc_data['outputs'].pop(i)
                            st.session_state[sipoc_key] = sipoc_data
                            st.rerun()
                    
                    output['quality_criteria'] = st.text_area(
                        "Critérios de Qualidade",
                        value=output.get('quality_criteria', ''),
                        key=f"output_quality_{project_id}_{i}",
                        height=60
                    )
    
    # Tab 5: Customers
    with tab5:
        st.markdown("### 👥 Customers (Clientes)")
        st.markdown("Quem recebe as saídas do processo?")
        
        # Adicionar customer
        col1, col2 = st.columns([3, 1])
        with col1:
            new_customer = st.text_input("Novo Cliente", key=f"new_customer_{project_id}")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Adicionar", key=f"add_customer_{project_id}"):
                if new_customer.strip():
                    sipoc_data['customers'].append({
                        'name': new_customer.strip(),
                        'type': 'Cliente Final',
                        'expectations': '',
                        'requirements': '',
                        'id': len(sipoc_data['customers'])
                    })
                    st.session_state[sipoc_key] = sipoc_data
                    st.rerun()
        
        # Mostrar customers
        if sipoc_data['customers'] and len(sipoc_data['customers']) > 0:
            for i, customer in enumerate(sipoc_data['customers']):
                with st.expander(f"**{customer['name']}**"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        customer['type'] = st.selectbox(
                            "Tipo",
                            ["Cliente Final", "Cliente Interno", "Processo Seguinte"],
                            index=["Cliente Final", "Cliente Interno", "Processo Seguinte"].index(customer.get('type', 'Cliente Final')),
                            key=f"customer_type_{project_id}_{i}"
                        )
                        
                        customer['expectations'] = st.text_area(
                            "Expectativas",
                            value=customer.get('expectations', ''),
                            key=f"customer_exp_{project_id}_{i}",
                            height=60
                        )
                    
                    with col_b:
                        if st.button(f"🗑️ Remover", key=f"remove_customer_{project_id}_{i}"):
                            sipoc_data['customers'].pop(i)
                            st.session_state[sipoc_key] = sipoc_data
                            st.rerun()
                        
                        customer['requirements'] = st.text_area(
                            "Requisitos",
                            value=customer.get('requirements', ''),
                            key=f"customer_req_{project_id}_{i}",
                            height=60
                        )
    
    # Visualização do SIPOC
    st.divider()
    st.markdown("### 📊 Visualização do SIPOC")
    
    if any([sipoc_data.get('suppliers', []), sipoc_data.get('inputs', []), 
            sipoc_data.get('process_steps', []), sipoc_data.get('outputs', []), 
            sipoc_data.get('customers', [])]):
        # Criar tabela visual
        col_s, col_i, col_p, col_o, col_c = st.columns(5)
        
        with col_s:
            st.markdown("**🏭 SUPPLIERS**")
            suppliers = sipoc_data.get('suppliers', [])
            for supplier in suppliers[:5]:  # Limitar a 5 para não ocupar muito espaço
                st.write(f"• {supplier['name']}")
            if len(suppliers) > 5:
                st.write(f"... e mais {len(suppliers) - 5}")
        
        with col_i:
            st.markdown("**📥 INPUTS**")
            inputs = sipoc_data.get('inputs', [])
            for input_item in inputs[:5]:
                st.write(f"• {input_item['name']}")
            if len(inputs) > 5:
                st.write(f"... e mais {len(inputs) - 5}")
        
        with col_p:
            st.markdown("**⚙️ PROCESS**")
            if process_name:
                st.write(f"**{process_name}**")
            steps = sipoc_data.get('process_steps', [])
            for i, step in enumerate(steps[:3]):
                st.write(f"{i+1}. {step['name']}")
            if len(steps) > 3:
                st.write(f"... e mais {len(steps) - 3} passos")
        
        with col_o:
            st.markdown("**📤 OUTPUTS**")
            outputs = sipoc_data.get('outputs', [])
            for output in outputs[:5]:
                st.write(f"• {output['name']}")
            if len(outputs) > 5:
                st.write(f"... e mais {len(outputs) - 5}")
        
        with col_c:
            st.markdown("**👥 CUSTOMERS**")
            customers = sipoc_data.get('customers', [])
            for customer in customers[:5]:
                st.write(f"• {customer['name']}")
            if len(customers) > 5:
                st.write(f"... e mais {len(customers) - 5}")
    
    # Botões de ação
    st.divider()
    col_save1, col_save2 = st.columns([1, 1])
    
    with col_save1:
        save_draft = st.button("💾 Salvar Rascunho", use_container_width=True, key=f"save_sipoc_draft_{project_id}")
    
    with col_save2:
        complete_sipoc = st.button("✅ Finalizar SIPOC", use_container_width=True, type="primary", key=f"complete_sipoc_{project_id}")
    
    # Processar ações
    if save_draft or complete_sipoc:
        # Coletar dados atuais
        current_data = {
            'process_name': st.session_state.get(f"process_name_{project_id}", ''),
            'process_description': st.session_state.get(f"process_description_{project_id}", ''),
            'suppliers': sipoc_data.get('suppliers', []),
            'inputs': sipoc_data.get('inputs', []),
            'process_steps': sipoc_data.get('process_steps', []),
            'outputs': sipoc_data.get('outputs', []),
            'customers': sipoc_data.get('customers', []),
            'last_saved': datetime.now().isoformat()
        }
        
        # Validação para finalizar
        if complete_sipoc:
            validations = [
                (current_data['process_name'], "Nome do Processo Principal"),
                (len(current_data['suppliers']) >= 1, "Pelo menos 1 Fornecedor"),
                (len(current_data['inputs']) >= 1, "Pelo menos 1 Entrada"),
                (len(current_data['process_steps']) >= 3, "Pelo menos 3 Passos do Processo"),
                (len(current_data['outputs']) >= 1, "Pelo menos 1 Saída"),
                (len(current_data['customers']) >= 1, "Pelo menos 1 Cliente")
            ]
            
            errors = []
            for condition, message in validations:
                if not condition:
                    errors.append(message)
            
            if errors:
                st.error(f"❌ Para finalizar o SIPOC, complete: {', '.join(errors)}")
                st.stop()
        
        # Salvar dados
        st.session_state[sipoc_key] = current_data
        
        update_data = {
            f'define.sipoc.data': current_data,
            f'define.sipoc.completed': complete_sipoc,
            f'define.sipoc.updated_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        with st.spinner("💾 Salvando..."):
            try:
                success = project_manager.update_project(project_id, update_data)
                
                if success:
                    # Atualizar session_state
                    if 'current_project' in st.session_state:
                        if 'define' not in st.session_state.current_project:
                            st.session_state.current_project['define'] = {}
                        if 'sipoc' not in st.session_state.current_project['define']:
                            st.session_state.current_project['define']['sipoc'] = {}
                        
                        st.session_state.current_project['define']['sipoc']['data'] = current_data
                        st.session_state.current_project['define']['sipoc']['completed'] = complete_sipoc
                    
                    if complete_sipoc:
                        st.success("✅ SIPOC Diagram finalizado com sucesso!")
                        st.balloons()
                    else:
                        st.success("💾 Rascunho salvo com sucesso!")
                
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {str(e)}")


def show_project_timeline(project_data: Dict):
    """Project Timeline - Cronograma do Projeto"""
    
    project_manager = ProjectManager()
    project_id = project_data.get('id')
    
    st.markdown("## 📅 Project Timeline")
    st.markdown("Defina o cronograma detalhado do projeto Six Sigma seguindo as fases DMAIC.")
    
    # Inicializar dados
    timeline_key = f"timeline_data_{project_id}"
    if timeline_key not in st.session_state:
        existing_data = project_data.get('define', {}).get('timeline', {}).get('data', {})
        st.session_state[timeline_key] = existing_data if existing_data else {}
    
    # Status atual
    is_completed = project_data.get('define', {}).get('timeline', {}).get('completed', False)
    if is_completed:
        st.success("✅ Project Timeline finalizado")
    else:
        st.info("⏳ Project Timeline em desenvolvimento")
    
    timeline_data = st.session_state[timeline_key]
    
    # Configurações do projeto
    st.markdown("### ⚙️ Configurações do Timeline")
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            start_date_value = datetime.strptime(timeline_data.get('start_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
        except:
            start_date_value = datetime.now().date()
            
        start_date = st.date_input(
            "Data de Início do Projeto *",
            value=start_date_value,
            key=f"start_date_{project_id}"
        )
    
    with col2:
        total_duration = st.number_input(
            "Duração Total (semanas) *",
            min_value=8,
            max_value=52,
            value=timeline_data.get('total_duration', 16),
            key=f"total_duration_{project_id}"
        )
    
    # Calcular data de fim
    end_date = start_date + timedelta(weeks=total_duration)
    st.info(f"📅 **Data de Conclusão Prevista:** {end_date.strftime('%d/%m/%Y')}")
    
    # Definição das fases DMAIC
    dmaic_phases = {
        'define': {
            'name': 'Define',
            'icon': '🎯',
            'description': 'Definir problema, objetivos e escopo',
            'default_duration': 2,
            'deliverables': ['Project Charter', 'Stakeholder Mapping', 'Voice of Customer', 'SIPOC', 'Timeline']
        },
        'measure': {
            'name': 'Measure',
            'icon': '📏',
            'description': 'Medir e coletar dados do estado atual',
            'default_duration': 4,
            'deliverables': ['Plan de Coleta de Dados', 'Sistema de Medição', 'Baseline dos Dados', 'Capability Study']
        },
        'analyze': {
            'name': 'Analyze',
            'icon': '🔍',
            'description': 'Analisar dados e identificar causas raiz',
            'default_duration': 4,
            'deliverables': ['Análise Estatística', 'Root Cause Analysis', 'Hypothesis Testing', 'Process Analysis']
        },
        'improve': {
            'name': 'Improve',
            'icon': '⚡',
            'description': 'Desenvolver e implementar soluções',
            'default_duration': 4,
            'deliverables': ['Soluções Propostas', 'Pilot Testing', 'Implementation Plan', 'Risk Assessment']
        },
        'control': {
            'name': 'Control',
            'icon': '🎮',
            'description': 'Controlar e sustentar melhorias',
            'default_duration': 2,
            'deliverables': ['Control Plan', 'Monitoring System', 'Training Materials', 'Project Closure']
        }
    }
    
    # Inicializar fases se não existirem - CORREÇÃO AQUI
    if 'phases' not in timeline_data or timeline_data['phases'] is None:
        timeline_data['phases'] = {}
        for phase_key, phase_info in dmaic_phases.items():
            timeline_data['phases'][phase_key] = {
                'duration': phase_info['default_duration'],
                'tasks': [],
                'status': 'not_started'
            }
        st.session_state[timeline_key] = timeline_data  # Salvar mudanças
    
    st.markdown("### 📊 Planejamento das Fases DMAIC")
    
    # Configurar duração das fases
    st.markdown("**Duração por Fase (semanas):**")
    phase_cols = st.columns(5)
    
    total_allocated = 0
    for i, (phase_key, phase_info) in enumerate(dmaic_phases.items()):
        with phase_cols[i]:
            duration = st.number_input(
                f"{phase_info['icon']} {phase_info['name']}",
                min_value=1,
                max_value=total_duration,
                value=timeline_data['phases'][phase_key]['duration'],
                key=f"phase_duration_{phase_key}_{project_id}"
            )
            timeline_data['phases'][phase_key]['duration'] = duration
            total_allocated += duration
    
    # Verificar se a duração total está correta
    if total_allocated != total_duration:
        if total_allocated > total_duration:
            st.error(f"❌ Total alocado ({total_allocated} semanas) excede a duração total ({total_duration} semanas)")
        else:
            st.warning(f"⚠️ Total alocado ({total_allocated} semanas) é menor que a duração total ({total_duration} semanas)")
    
    # Planejamento detalhado por fase
    st.markdown("### 📋 Detalhamento das Fases")
    
    current_start_date = start_date
    
    for phase_key, phase_info in dmaic_phases.items():
        phase_duration = timeline_data['phases'][phase_key]['duration']
        phase_end_date = current_start_date + timedelta(weeks=phase_duration)
        
        with st.expander(f"{phase_info['icon']} **{phase_info['name']}** ({current_start_date.strftime('%d/%m')} - {phase_end_date.strftime('%d/%m/%Y')})"):
            st.markdown(f"*{phase_info['description']}*")
            
            # Status da fase
            status_options = ["not_started", "in_progress", "completed"]
            status_labels = ["🔴 Não Iniciado", "🟡 Em Progresso", "🟢 Concluído"]
            
            current_status = timeline_data['phases'][phase_key].get('status', 'not_started')
            status_index = status_options.index(current_status)
            
            new_status = st.selectbox(
                "Status da Fase",
                status_options,
                index=status_index,
                format_func=lambda x: status_labels[status_options.index(x)],
                key=f"phase_status_{phase_key}_{project_id}"
            )
            timeline_data['phases'][phase_key]['status'] = new_status
            
            # Deliverables principais
            st.markdown("**📦 Principais Entregas:**")
            for deliverable in phase_info['deliverables']:
                st.write(f"• {deliverable}")
            
            # Tarefas customizadas
            st.markdown("**✅ Tarefas Específicas:**")
            
            # Inicializar tarefas se não existirem
            if 'tasks' not in timeline_data['phases'][phase_key] or timeline_data['phases'][phase_key]['tasks'] is None:
                timeline_data['phases'][phase_key]['tasks'] = []
            
            # Adicionar nova tarefa
            col_task1, col_task2, col_task3 = st.columns([3, 2, 1])
            
            with col_task1:
                new_task = st.text_input(
                    "Nova Tarefa",
                    key=f"new_task_{phase_key}_{project_id}",
                    placeholder="Ex: Coletar dados de vendas..."
                )
            
            with col_task2:
                task_duration = st.number_input(
                    "Duração (dias)",
                    min_value=1,
                    max_value=phase_duration * 7,
                    value=3,
                    key=f"task_duration_{phase_key}_{project_id}"
                )
            
            with col_task3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕", key=f"add_task_{phase_key}_{project_id}"):
                    if new_task.strip():
                        timeline_data['phases'][phase_key]['tasks'].append({
                            'name': new_task.strip(),
                            'duration': task_duration,
                            'status': 'pending',
                            'responsible': '',
                            'notes': '',
                            'id': len(timeline_data['phases'][phase_key]['tasks'])
                        })
                        st.session_state[timeline_key] = timeline_data
                        st.rerun()
            
            # Mostrar tarefas existentes
            tasks = timeline_data['phases'][phase_key].get('tasks', [])
            if tasks and len(tasks) > 0:
                for j, task in enumerate(tasks):
                    with st.container():
                        col_t1, col_t2, col_t3, col_t4 = st.columns([3, 2, 2, 1])
                        
                        with col_t1:
                            task['name'] = st.text_input(
                                "Tarefa",
                                value=task['name'],
                                key=f"task_name_{phase_key}_{project_id}_{j}"
                            )
                        
                        with col_t2:
                            task_status_options = ["pending", "in_progress", "completed"]
                            task_status_labels = ["⏳ Pendente", "🔄 Em Progresso", "✅ Concluída"]
                            
                            current_task_status = task.get('status', 'pending')
                            task_status_index = task_status_options.index(current_task_status)
                            
                            task['status'] = st.selectbox(
                                "Status",
                                task_status_options,
                                index=task_status_index,
                                format_func=lambda x: task_status_labels[task_status_options.index(x)],
                                key=f"task_status_{phase_key}_{project_id}_{j}"
                            )
                        
                        with col_t3:
                            task['responsible'] = st.text_input(
                                "Responsável",
                                value=task.get('responsible', ''),
                                key=f"task_responsible_{phase_key}_{project_id}_{j}"
                            )
                        
                        with col_t4:
                            if st.button("🗑️", key=f"remove_task_{phase_key}_{project_id}_{j}"):
                                timeline_data['phases'][phase_key]['tasks'].pop(j)
                                st.session_state[timeline_key] = timeline_data
                                st.rerun()
                        
                        # Notas da tarefa
                        task['notes'] = st.text_area(
                            "Notas/Observações",
                            value=task.get('notes', ''),
                            key=f"task_notes_{phase_key}_{project_id}_{j}",
                            height=50
                        )
                        
                        st.divider()
        
        current_start_date = phase_end_date
    
    # Visualização do Timeline
    st.markdown("### 📊 Visualização do Cronograma")
    
    if st.button("🔄 Gerar Gráfico de Gantt", key=f"generate_gantt_{project_id}"):
        # Preparar dados para o gráfico de Gantt
        gantt_data = []
        current_date = start_date
        
        for phase_key, phase_info in dmaic_phases.items():
            phase_duration = timeline_data['phases'][phase_key]['duration']
            phase_end = current_date + timedelta(weeks=phase_duration)
            
            gantt_data.append({
                'Task': f"{phase_info['icon']} {phase_info['name']}",
                'Start': current_date,
                'Finish': phase_end,
                'Type': 'Phase'
            })
            
            current_date = phase_end
        
        # Criar DataFrame
        df_gantt = pd.DataFrame(gantt_data)
        
        # Criar gráfico de Gantt
        fig = px.timeline(
            df_gantt,
            x_start="Start",
            x_end="Finish",
            y="Task",
            title="Cronograma do Projeto Six Sigma",
            color="Type"
        )
        
        fig.update_yaxes(categoryorder="total ascending")
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Resumo do progresso
    st.markdown("### 📈 Progresso Geral")
    
    completed_phases = sum(1 for phase in timeline_data['phases'].values() if phase.get('status') == 'completed')
    total_phases = len(dmaic_phases)
    progress_percentage = (completed_phases / total_phases) * 100
    
    col_prog1, col_prog2, col_prog3 = st.columns(3)
    
    with col_prog1:
        st.metric("Fases Concluídas", f"{completed_phases}/{total_phases}")
    
    with col_prog2:
        st.metric("Progresso", f"{progress_percentage:.1f}%")
    
    with col_prog3:
        days_elapsed = (datetime.now().date() - start_date).days
        total_days = total_duration * 7
        time_progress = min((days_elapsed / total_days) * 100, 100) if total_days > 0 else 0
        st.metric("Tempo Decorrido", f"{time_progress:.1f}%")
    
    # Barra de progresso
    st.progress(progress_percentage / 100)
    
    # Botões de ação
    st.divider()
    col_save1, col_save2 = st.columns([1, 1])
    
    with col_save1:
        save_draft = st.button("💾 Salvar Rascunho", use_container_width=True, key=f"save_timeline_draft_{project_id}")
    
    with col_save2:
        complete_timeline = st.button("✅ Finalizar Timeline", use_container_width=True, type="primary", key=f"complete_timeline_{project_id}")
    
    # Processar ações
    if save_draft or complete_timeline:
        # Coletar dados atuais
        current_data = {
            'start_date': st.session_state.get(f"start_date_{project_id}").strftime('%Y-%m-%d'),
            'total_duration': st.session_state.get(f"total_duration_{project_id}"),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'phases': timeline_data.get('phases', {}),
            'total_allocated': total_allocated,
            'last_saved': datetime.now().isoformat()
        }
        
        # Validação para finalizar
        if complete_timeline:
            if total_allocated != total_duration:
                st.error("❌ A soma das durações das fases deve ser igual à duração total do projeto")
                st.stop()
            
            # Verificar se pelo menos uma tarefa foi adicionada em cada fase
            phases_with_tasks = sum(1 for phase in timeline_data['phases'].values() 
                                  if len(phase.get('tasks', [])) > 0)
            if phases_with_tasks < 3:
                st.error("❌ Adicione pelo menos uma tarefa em pelo menos 3 fases para finalizar o timeline")
                st.stop()
        
        # Salvar dados
        st.session_state[timeline_key] = current_data
        
        update_data = {
            f'define.timeline.data': current_data,
            f'define.timeline.completed': complete_timeline,
            f'define.timeline.updated_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        with st.spinner("💾 Salvando..."):
            try:
                success = project_manager.update_project(project_id, update_data)
                
                if success:
                    # Atualizar session_state
                    if 'current_project' in st.session_state:
                        if 'define' not in st.session_state.current_project:
                            st.session_state.current_project['define'] = {}
                        if 'timeline' not in st.session_state.current_project['define']:
                            st.session_state.current_project['define']['timeline'] = {}
                        
                        st.session_state.current_project['define']['timeline']['data'] = current_data
                        st.session_state.current_project['define']['timeline']['completed'] = complete_timeline
                    
                    if complete_timeline:
                        st.success("✅ Project Timeline finalizado com sucesso!")
                        st.balloons()
                    else:
                        st.success("💾 Rascunho salvo com sucesso!")
                
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {str(e)}")


def show_define_tools(project_data: Dict):
    """Função principal para mostrar as ferramentas da fase Define"""
    
    if not project_data:
        st.error("❌ Projeto não encontrado")
        return
    
    # Menu de ferramentas
    st.markdown("### 🔧 Ferramentas da Fase Define")
    
    tool_options = {
        "charter": "📋 Project Charter",
        "stakeholders": "👥 Stakeholder Mapping", 
        "voc": "🗣️ Voice of Customer",
        "sipoc": "📊 SIPOC Diagram",
        "timeline": "📅 Project Timeline"
    }
    
    # Verificar status das ferramentas
    define_data = project_data.get('define', {})
    
    # Usar selectbox em vez de botões para evitar resets
    tool_names = list(tool_options.values())
    tool_keys = list(tool_options.keys())
    
    # Adicionar status aos nomes
    tool_names_with_status = []
    for key, name in tool_options.items():
        is_completed = define_data.get(key, {}).get('completed', False)
        status_icon = "✅" if is_completed else "⏳"
        tool_names_with_status.append(f"{status_icon} {name}")
    
    selected_index = st.selectbox(
        "Selecione uma ferramenta:",
        range(len(tool_names_with_status)),
        format_func=lambda x: tool_names_with_status[x],
        key=f"tool_selector_{project_data.get('id')}"
    )
    
    selected_tool = tool_keys[selected_index]
    
    st.divider()
    
    # Mostrar ferramenta selecionada
    if selected_tool == "charter":
        show_project_charter(project_data)
    elif selected_tool == "stakeholders":
        show_stakeholder_mapping(project_data)
    elif selected_tool == "voc":
        show_voice_of_customer(project_data)
    elif selected_tool == "sipoc":
        show_sipoc_diagram(project_data)
    elif selected_tool == "timeline":
        show_project_timeline(project_data)
    
    # Progresso geral da fase Define
    st.divider()
    st.markdown("### 📊 Progresso da Fase Define")
    
    total_tools = len(tool_options)
    completed_tools = sum(1 for tool_key in tool_options.keys() 
                        if define_data.get(tool_key, {}).get('completed', False))
    
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
        st.success("🎉 **Parabéns! Fase Define concluída com sucesso!**")
        st.info("✨ Você pode avançar para a fase **Measure** usando a navegação das fases.")
