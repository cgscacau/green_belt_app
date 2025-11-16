import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List
from src.utils.project_manager import ProjectManager

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
        st.session_state[charter_key] = existing_data
    
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
                            st.metric("Benefício Anual", f"R$ {benefit:,.2f}")
                        
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
        st.info("🚧 Stakeholder Mapping - Em desenvolvimento")
    elif selected_tool == "voc":
        st.info("🚧 Voice of Customer - Em desenvolvimento")
    elif selected_tool == "sipoc":
        st.info("🚧 SIPOC Diagram - Em desenvolvimento")
    elif selected_tool == "timeline":
        st.info("🚧 Project Timeline - Em desenvolvimento")
    
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
