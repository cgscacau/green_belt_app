import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import warnings

# Suprimir warnings
warnings.filterwarnings('ignore')

# Import do ProjectManager com tratamento de erro
try:
    from src.utils.project_manager import ProjectManager
except ImportError:
    try:
        from utils.project_manager import ProjectManager
    except ImportError:
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from src.utils.project_manager import ProjectManager
        except ImportError:
            st.error("❌ Não foi possível importar ProjectManager. Verifique se o arquivo existe em src/utils/project_manager.py")
            st.stop()


class ImprovePhaseManager:
    """Gerenciador centralizado da fase Improve"""
    
    def __init__(self, project_data: Dict):
        self.project_data = project_data
        self.project_id = project_data.get('id')
        self.project_manager = ProjectManager()
    
    def save_tool_data(self, tool_name: str, data: Dict, completed: bool = False) -> bool:
        """Salva dados de uma ferramenta com atualização de estado"""
        try:
            update_data = {
                f'improve.{tool_name}.data': data,
                f'improve.{tool_name}.completed': completed,
                f'improve.{tool_name}.updated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            success = self.project_manager.update_project(self.project_id, update_data)
            
            if success and 'current_project' in st.session_state:
                # Atualizar session_state imediatamente
                if 'improve' not in st.session_state.current_project:
                    st.session_state.current_project['improve'] = {}
                if tool_name not in st.session_state.current_project['improve']:
                    st.session_state.current_project['improve'][tool_name] = {}
                
                st.session_state.current_project['improve'][tool_name] = {
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
        improve_data = self.project_data.get('improve', {})
        tool_data = improve_data.get(tool_name, {})
        return tool_data.get('completed', False) if isinstance(tool_data, dict) else False
    
    def get_tool_data(self, tool_name: str) -> Dict:
        """Recupera dados de uma ferramenta"""
        improve_data = self.project_data.get('improve', {})
        tool_data = improve_data.get(tool_name, {})
        return tool_data.get('data', {}) if isinstance(tool_data, dict) else {}
    
    def get_analyze_insights(self) -> Dict:
        """Recupera insights da fase Analyze para usar no Improve"""
        analyze_data = self.project_data.get('analyze', {})
        insights = {
            'root_causes': [],
            'statistical_findings': [],
            'priority_issues': []
        }
        
        # Causas raiz identificadas
        rca_data = analyze_data.get('root_cause_analysis', {}).get('data', {})
        if rca_data.get('root_cause_final'):
            insights['root_causes'].append(rca_data['root_cause_final'])
        
        # Análises estatísticas
        stats_data = analyze_data.get('statistical_analysis', {}).get('data', {})
        if stats_data.get('analysis_completed'):
            insights['statistical_findings'].append("Análise estatística concluída")
        
        return insights

    class SolutionDevelopmentTool:
    """Ferramenta para Desenvolvimento de Soluções"""
    
    def __init__(self, manager: ImprovePhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "solution_development"
    
    def show(self):
        """Interface principal da ferramenta"""
        st.markdown("## 💡 Desenvolvimento de Soluções")
        st.markdown("Desenvolva soluções inovadoras baseadas nas causas raiz identificadas na fase Analyze.")
        
        # Status da ferramenta
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ **Desenvolvimento de soluções finalizado**")
        else:
            st.info("⏳ **Desenvolvimento em progresso**")
        
        # Inicializar dados da sessão
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data if existing_data else {
                'solutions': [],
                'brainstorm_sessions': [],
                'selection_criteria': {}
            }
        
        solution_data = st.session_state[session_key]
        
        # Mostrar insights da fase Analyze
        self._show_analyze_insights()
        
        # Interface principal
        self._show_solution_tabs(solution_data)
        
        # Botões de ação
        self._show_action_buttons(solution_data)
    
    def _show_analyze_insights(self):
        """Mostra insights da fase Analyze"""
        st.markdown("### 🔍 Insights da Fase Analyze")
        
        insights = self.manager.get_analyze_insights()
        
        if insights['root_causes']:
            st.markdown("#### 🎯 Causas Raiz Identificadas")
            for i, cause in enumerate(insights['root_causes'], 1):
                st.info(f"**{i}.** {cause}")
        else:
            st.warning("⚠️ Nenhuma causa raiz identificada na fase Analyze")
            st.info("💡 **Dica:** Complete a análise de causa raiz antes de desenvolver soluções")
    
    def _show_solution_tabs(self, solution_data: Dict):
        """Mostra abas para desenvolvimento de soluções"""
        tab1, tab2, tab3, tab4 = st.tabs([
            "🧠 Brainstorming",
            "💡 Soluções",
            "⚖️ Avaliação",
            "🏆 Seleção Final"
        ])
        
        with tab1:
            self._show_brainstorming(solution_data)
        
        with tab2:
            self._show_solutions_management(solution_data)
        
        with tab3:
            self._show_solution_evaluation(solution_data)
        
        with tab4:
            self._show_solution_selection(solution_data)
    
    def _show_brainstorming(self, solution_data: Dict):
        """Interface de brainstorming"""
        st.markdown("#### 🧠 Sessões de Brainstorming")
        
        # Nova sessão de brainstorming
        with st.expander("➕ Nova Sessão de Brainstorming"):
            col1, col2 = st.columns(2)
            
            with col1:
                session_topic = st.text_input(
                    "Tópico da Sessão:",
                    key=f"brainstorm_topic_{self.project_id}",
                    placeholder="Ex: Soluções para reduzir tempo de setup"
                )
                
                session_method = st.selectbox(
                    "Método:",
                    ["Brainstorming Clássico", "Brainwriting", "Método 635", "Mind Mapping", "SCAMPER"],
                    key=f"brainstorm_method_{self.project_id}"
                )
            
            with col2:
                session_participants = st.text_area(
                    "Participantes:",
                    key=f"brainstorm_participants_{self.project_id}",
                    placeholder="Liste os participantes da sessão..."
                )
                
                session_duration = st.number_input(
                    "Duração (minutos):",
                    min_value=15,
                    max_value=180,
                    value=60,
                    key=f"brainstorm_duration_{self.project_id}"
                )
            
            session_ideas = st.text_area(
                "Ideias Geradas:",
                key=f"brainstorm_ideas_{self.project_id}",
                placeholder="Liste todas as ideias geradas (uma por linha)...",
                height=120
            )
            
            if st.button("💾 Salvar Sessão", key=f"save_brainstorm_{self.project_id}"):
                if session_topic.strip() and session_ideas.strip():
                    ideas_list = [idea.strip() for idea in session_ideas.split('\n') if idea.strip()]
                    
                    if 'brainstorm_sessions' not in solution_data:
                        solution_data['brainstorm_sessions'] = []
                    
                    solution_data['brainstorm_sessions'].append({
                        'topic': session_topic,
                        'method': session_method,
                        'participants': session_participants,
                        'duration': session_duration,
                        'ideas': ideas_list,
                        'date': datetime.now().isoformat(),
                        'total_ideas': len(ideas_list)
                    })
                    
                    st.success(f"✅ Sessão salva com {len(ideas_list)} ideias!")
                    st.rerun()
                else:
                    st.error("❌ Preencha tópico e ideias")
        
        # Mostrar sessões existentes
        if solution_data.get('brainstorm_sessions'):
            st.markdown("#### 📋 Sessões Realizadas")
            
            for i, session in enumerate(solution_data['brainstorm_sessions']):
                with st.expander(f"**{session['topic']}** - {session['total_ideas']} ideias ({session['date'][:10]})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Método:** {session['method']}")
                        st.write(f"**Duração:** {session['duration']} min")
                        st.write(f"**Total de Ideias:** {session['total_ideas']}")
                    
                    with col2:
                        if session['participants']:
                            st.write(f"**Participantes:** {session['participants']}")
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_brainstorm_{i}_{self.project_id}"):
                            solution_data['brainstorm_sessions'].pop(i)
                            st.rerun()
                    
                    # Mostrar ideias
                    st.write("**💡 Ideias Geradas:**")
                    for j, idea in enumerate(session['ideas'], 1):
                        col_idea1, col_idea2 = st.columns([4, 1])
                        with col_idea1:
                            st.write(f"{j}. {idea}")
                        with col_idea2:
                            if st.button("➡️ Converter", key=f"convert_idea_{i}_{j}_{self.project_id}"):
                                # Converter ideia em solução
                                if 'solutions' not in solution_data:
                                    solution_data['solutions'] = []
                                
                                solution_data['solutions'].append({
                                    'name': idea,
                                    'description': f"Solução originada do brainstorming: {session['topic']}",
                                    'type': 'Melhoria de Processo',
                                    'complexity': 'Média',
                                    'cost_estimate': 0,
                                    'implementation_time': 30,
                                    'expected_impact': 'Médio',
                                    'status': 'Proposta',
                                    'source': f"Brainstorm: {session['topic']}",
                                    'created_at': datetime.now().isoformat()
                                })
                                
                                st.success(f"✅ Ideia convertida em solução!")
                                st.rerun()

    def _show_solutions_management(self, solution_data: Dict):
        """Gerenciamento de soluções"""
        st.markdown("#### 💡 Catálogo de Soluções")
        
        # Adicionar nova solução
        with st.expander("➕ Adicionar Nova Solução"):
            col1, col2 = st.columns(2)
            
            with col1:
                sol_name = st.text_input(
                    "Nome da Solução:",
                    key=f"solution_name_{self.project_id}",
                    placeholder="Ex: Implementação de setup rápido (SMED)"
                )
                
                sol_type = st.selectbox(
                    "Tipo de Solução:",
                    ["Melhoria de Processo", "Tecnologia", "Treinamento", "Mudança Organizacional", 
                     "Automação", "Padronização", "Redesign", "Eliminação"],
                    key=f"solution_type_{self.project_id}"
                )
                
                sol_complexity = st.selectbox(
                    "Complexidade:",
                    ["Baixa", "Média", "Alta"],
                    key=f"solution_complexity_{self.project_id}"
                )
            
            with col2:
                sol_cost = st.number_input(
                    "Custo Estimado (R$):",
                    min_value=0.0,
                    value=0.0,
                    key=f"solution_cost_{self.project_id}"
                )
                
                sol_time = st.number_input(
                    "Tempo de Implementação (dias):",
                    min_value=1,
                    max_value=365,
                    value=30,
                    key=f"solution_time_{self.project_id}"
                )
                
                sol_impact = st.selectbox(
                    "Impacto Esperado:",
                    ["Baixo", "Médio", "Alto"],
                    key=f"solution_impact_{self.project_id}"
                )
            
            sol_description = st.text_area(
                "Descrição Detalhada:",
                key=f"solution_description_{self.project_id}",
                placeholder="Descreva como a solução funcionará e como resolverá o problema...",
                height=100
            )
            
            sol_requirements = st.text_area(
                "Recursos/Pré-requisitos:",
                key=f"solution_requirements_{self.project_id}",
                placeholder="Liste recursos necessários, aprovações, etc..."
            )
            
            if st.button("💡 Adicionar Solução", key=f"add_solution_{self.project_id}"):
                if sol_name.strip() and sol_description.strip():
                    if 'solutions' not in solution_data:
                        solution_data['solutions'] = []
                    
                    solution_data['solutions'].append({
                        'name': sol_name,
                        'description': sol_description,
                        'type': sol_type,
                        'complexity': sol_complexity,
                        'cost_estimate': float(sol_cost),
                        'implementation_time': int(sol_time),
                        'expected_impact': sol_impact,
                        'requirements': sol_requirements,
                        'status': 'Proposta',
                        'created_at': datetime.now().isoformat(),
                        'evaluation_score': 0
                    })
                    
                    st.success(f"✅ Solução '{sol_name}' adicionada!")
                    st.rerun()
                else:
                    st.error("❌ Preencha nome e descrição")
        
        # Mostrar soluções existentes
        if solution_data.get('solutions'):
            st.markdown("#### 📊 Soluções Propostas")
            
            # Filtros
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                type_filter = st.selectbox(
                    "Filtrar por Tipo:",
                    ["Todos"] + list(set([sol['type'] for sol in solution_data['solutions']])),
                    key=f"type_filter_{self.project_id}"
                )
            
            with col_filter2:
                complexity_filter = st.selectbox(
                    "Filtrar por Complexidade:",
                    ["Todos", "Baixa", "Média", "Alta"],
                    key=f"complexity_filter_{self.project_id}"
                )
            
            with col_filter3:
                impact_filter = st.selectbox(
                    "Filtrar por Impacto:",
                    ["Todos", "Baixo", "Médio", "Alto"],
                    key=f"impact_filter_{self.project_id}"
                )
            
            # Aplicar filtros
            filtered_solutions = solution_data['solutions']
            
            if type_filter != "Todos":
                filtered_solutions = [sol for sol in filtered_solutions if sol['type'] == type_filter]
            
            if complexity_filter != "Todos":
                filtered_solutions = [sol for sol in filtered_solutions if sol['complexity'] == complexity_filter]
            
            if impact_filter != "Todos":
                filtered_solutions = [sol for sol in filtered_solutions if sol['expected_impact'] == impact_filter]
            
            # Mostrar soluções filtradas com capacidade de edição
            for i, solution in enumerate(filtered_solutions):
                original_index = solution_data['solutions'].index(solution)
                
                with st.expander(f"**{solution['name']}** ({solution['type']}) - {solution['status']}"):
                    
                    # Modo de edição
                    edit_mode = st.checkbox(f"✏️ Editar", key=f"edit_mode_{original_index}_{self.project_id}")
                    
                    if edit_mode:
                        # Campos editáveis
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_name = st.text_input(
                                "Nome:",
                                value=solution.get('name', ''),
                                key=f"edit_name_{original_index}_{self.project_id}"
                            )
                            
                            new_type = st.selectbox(
                                "Tipo:",
                                ["Melhoria de Processo", "Tecnologia", "Treinamento", "Mudança Organizacional", 
                                 "Automação", "Padronização", "Redesign", "Eliminação"],
                                index=["Melhoria de Processo", "Tecnologia", "Treinamento", "Mudança Organizacional", 
                                       "Automação", "Padronização", "Redesign", "Eliminação"].index(solution.get('type', 'Melhoria de Processo')),
                                key=f"edit_type_{original_index}_{self.project_id}"
                            )
                            
                            new_complexity = st.selectbox(
                                "Complexidade:",
                                ["Baixa", "Média", "Alta"],
                                index=["Baixa", "Média", "Alta"].index(solution.get('complexity', 'Média')),
                                key=f"edit_complexity_{original_index}_{self.project_id}"
                            )
                        
                        with col2:
                            new_cost = st.number_input(
                                "Custo (R$):",
                                min_value=0.0,
                                value=float(solution.get('cost_estimate', 0)),
                                key=f"edit_cost_{original_index}_{self.project_id}"
                            )
                            
                            new_time = st.number_input(
                                "Tempo (dias):",
                                min_value=1,
                                max_value=365,
                                value=int(solution.get('implementation_time', 30)),
                                key=f"edit_time_{original_index}_{self.project_id}"
                            )
                            
                            new_impact = st.selectbox(
                                "Impacto:",
                                ["Baixo", "Médio", "Alto"],
                                index=["Baixo", "Médio", "Alto"].index(solution.get('expected_impact', 'Médio')),
                                key=f"edit_impact_{original_index}_{self.project_id}"
                            )
                        
                        new_description = st.text_area(
                            "Descrição:",
                            value=solution.get('description', ''),
                            key=f"edit_description_{original_index}_{self.project_id}",
                            height=100
                        )
                        
                        new_requirements = st.text_area(
                            "Recursos/Pré-requisitos:",
                            value=solution.get('requirements', ''),
                            key=f"edit_requirements_{original_index}_{self.project_id}",
                            height=80
                        )
                        
                        # Botões de ação para edição
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if st.button("💾 Salvar Alterações", key=f"save_edit_{original_index}_{self.project_id}"):
                                # Atualizar solução
                                solution_data['solutions'][original_index].update({
                                    'name': new_name,
                                    'type': new_type,
                                    'complexity': new_complexity,
                                    'cost_estimate': new_cost,
                                    'implementation_time': new_time,
                                    'expected_impact': new_impact,
                                    'description': new_description,
                                    'requirements': new_requirements,
                                    'updated_at': datetime.now().isoformat()
                                })
                                
                                st.success("✅ Solução atualizada!")
                                st.rerun()
                        
                        with col_btn2:
                            if st.button("❌ Cancelar", key=f"cancel_edit_{original_index}_{self.project_id}"):
                                st.rerun()
                    
                    else:
                        # Modo visualização
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write(f"**Descrição:** {solution.get('description', 'N/A')}")
                            if solution.get('requirements'):
                                st.write(f"**Recursos:** {solution['requirements']}")
                            if solution.get('source'):
                                st.write(f"**Origem:** {solution['source']}")
                        
                        with col2:
                            st.write(f"**Complexidade:** {solution['complexity']}")
                            st.write(f"**Impacto:** {solution['expected_impact']}")
                            st.write(f"**Custo:** R$ {solution['cost_estimate']:,.2f}")
                            st.write(f"**Tempo:** {solution['implementation_time']} dias")
                            
                            if solution.get('evaluation_score', 0) > 0:
                                st.write(f"**Score:** {solution['evaluation_score']:.1f}/10")
                        
                        with col3:
                            # Status
                            new_status = st.selectbox(
                                "Status:",
                                ["Proposta", "Em Avaliação", "Aprovada", "Rejeitada", "Implementando"],
                                index=["Proposta", "Em Avaliação", "Aprovada", "Rejeitada", "Implementando"].index(solution['status']),
                                key=f"solution_status_{original_index}_{self.project_id}"
                            )
                            
                            solution_data['solutions'][original_index]['status'] = new_status
                            
                            # Botão remover
                            if st.button("🗑️ Remover", key=f"remove_solution_{original_index}_{self.project_id}"):
                                solution_data['solutions'].pop(original_index)
                                st.success("✅ Solução removida!")
                                st.rerun()
            
            # Resumo estatístico
            if solution_data['solutions']:
                st.markdown("#### 📈 Resumo das Soluções")
                
                total_solutions = len(solution_data['solutions'])
                total_cost = sum(sol['cost_estimate'] for sol in solution_data['solutions'])
                avg_time = sum(sol['implementation_time'] for sol in solution_data['solutions']) / total_solutions
                
                col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                
                with col_stats1:
                    st.metric("Total de Soluções", total_solutions)
                
                with col_stats2:
                    st.metric("Custo Total", f"R$ {total_cost:,.2f}")
                
                with col_stats3:
                    st.metric("Tempo Médio", f"{avg_time:.0f} dias")
                
                with col_stats4:
                    approved = len([sol for sol in solution_data['solutions'] if sol['status'] == 'Aprovada'])
                    st.metric("Aprovadas", approved)
        else:
            st.info("📝 Nenhuma solução cadastrada ainda. Adicione soluções ou converta ideias do brainstorming.")

    def _show_solution_evaluation(self, solution_data: Dict):
        """Avaliação de soluções"""
        st.markdown("#### ⚖️ Avaliação de Soluções")
        
        if not solution_data.get('solutions'):
            st.info("💡 Adicione soluções primeiro para poder avaliá-las")
            return
        
        # Definir critérios de avaliação
        st.markdown("##### 📋 Critérios de Avaliação")
        
        if 'selection_criteria' not in solution_data:
            solution_data['selection_criteria'] = {}
        
        criteria = solution_data['selection_criteria']
        
        with st.expander("⚙️ Configurar Critérios"):
            col1, col2 = st.columns(2)
            
            with col1:
                criteria['feasibility_weight'] = st.slider(
                    "Peso - Viabilidade:",
                    0, 10, criteria.get('feasibility_weight', 8),
                    key=f"feasibility_weight_{self.project_id}"
                )
                
                criteria['cost_weight'] = st.slider(
                    "Peso - Custo:",
                    0, 10, criteria.get('cost_weight', 7),
                    key=f"cost_weight_{self.project_id}"
                )
                
                criteria['time_weight'] = st.slider(
                    "Peso - Tempo:",
                    0, 10, criteria.get('time_weight', 6),
                    key=f"time_weight_{self.project_id}"
                )
            
            with col2:
                criteria['impact_weight'] = st.slider(
                    "Peso - Impacto:",
                    0, 10, criteria.get('impact_weight', 9),
                    key=f"impact_weight_{self.project_id}"
                )
                
                criteria['risk_weight'] = st.slider(
                    "Peso - Risco:",
                    0, 10, criteria.get('risk_weight', 5),
                    key=f"risk_weight_{self.project_id}"
                )
                
                criteria['sustainability_weight'] = st.slider(
                    "Peso - Sustentabilidade:",
                    0, 10, criteria.get('sustainability_weight', 7),
                    key=f"sustainability_weight_{self.project_id}"
                )
        
        # Avaliar soluções
        st.markdown("##### 🎯 Avaliação Individual")
        
        for i, solution in enumerate(solution_data['solutions']):
            with st.expander(f"Avaliar: **{solution['name']}**"):
                st.write(f"**Descrição:** {solution['description']}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    feasibility = st.slider(
                        "Viabilidade (1-10):",
                        1, 10, solution.get('feasibility_score', 5),
                        key=f"feasibility_{i}_{self.project_id}",
                        help="Quão fácil é implementar esta solução?"
                    )
                    
                    impact = st.slider(
                        "Impacto (1-10):",
                        1, 10, solution.get('impact_score', 5),
                        key=f"impact_{i}_{self.project_id}",
                        help="Qual o impacto esperado no problema?"
                    )
                
                with col2:
                    cost_score = st.slider(
                        "Custo-Benefício (1-10):",
                        1, 10, solution.get('cost_score', 5),
                        key=f"cost_{i}_{self.project_id}",
                        help="Relação custo-benefício (10 = excelente custo-benefício)"
                    )
                    
                    time_score = st.slider(
                        "Rapidez (1-10):",
                        1, 10, solution.get('time_score', 5),
                        key=f"time_{i}_{self.project_id}",
                        help="Velocidade de implementação (10 = muito rápido)"
                    )
                
                with col3:
                    risk_score = st.slider(
                        "Baixo Risco (1-10):",
                        1, 10, solution.get('risk_score', 5),
                        key=f"risk_{i}_{self.project_id}",
                        help="Nível de risco (10 = muito baixo risco)"
                    )
                    
                    sustainability = st.slider(
                        "Sustentabilidade (1-10):",
                        1, 10, solution.get('sustainability_score', 5),
                        key=f"sustainability_{i}_{self.project_id}",
                        help="Durabilidade da solução no longo prazo"
                    )
                
                # Calcular score ponderado
                weighted_score = (
                    feasibility * criteria.get('feasibility_weight', 8) +
                    impact * criteria.get('impact_weight', 9) +
                    cost_score * criteria.get('cost_weight', 7) +
                    time_score * criteria.get('time_weight', 6) +
                    risk_score * criteria.get('risk_weight', 5) +
                    sustainability * criteria.get('sustainability_weight', 7)
                ) / (
                    criteria.get('feasibility_weight', 8) +
                    criteria.get('impact_weight', 9) +
                    criteria.get('cost_weight', 7) +
                    criteria.get('time_weight', 6) +
                    criteria.get('risk_weight', 5) +
                    criteria.get('sustainability_weight', 7)
                )
                
                # Salvar scores
                solution_data['solutions'][i].update({
                    'feasibility_score': feasibility,
                    'impact_score': impact,
                    'cost_score': cost_score,
                    'time_score': time_score,
                    'risk_score': risk_score,
                    'sustainability_score': sustainability,
                    'evaluation_score': weighted_score
                })
                
                # Mostrar score final
                col_score1, col_score2 = st.columns(2)
                
                with col_score1:
                    st.metric("Score Final", f"{weighted_score:.1f}/10")
                
                with col_score2:
                    if weighted_score >= 8:
                        st.success("🟢 Excelente")
                    elif weighted_score >= 6:
                        st.warning("🟡 Boa")
                    elif weighted_score >= 4:
                        st.info("🔵 Média")
                    else:
                        st.error("🔴 Baixa")
        
        # Ranking de soluções
        if solution_data['solutions'] and any(sol.get('evaluation_score', 0) > 0 for sol in solution_data['solutions']):
            st.markdown("##### 🏆 Ranking de Soluções")
            
            # Ordenar por score
            ranked_solutions = sorted(
                solution_data['solutions'],
                key=lambda x: x.get('evaluation_score', 0),
                reverse=True
            )
            
            ranking_data = []
            for i, sol in enumerate(ranked_solutions, 1):
                score = sol.get('evaluation_score', 0)
                if score > 0:
                    ranking_data.append({
                        'Posição': i,
                        'Solução': sol['name'],
                        'Score': f"{score:.1f}",
                        'Tipo': sol['type'],
                        'Custo': f"R$ {sol['cost_estimate']:,.2f}",
                        'Tempo': f"{sol['implementation_time']} dias",
                        'Status': sol['status']
                    })
            
            if ranking_data:
                ranking_df = pd.DataFrame(ranking_data)
                st.dataframe(ranking_df, use_container_width=True)
                
                # Gráfico de ranking
                fig = px.bar(
                    ranking_df.head(10),
                    x='Solução',
                    y='Score',
                    title="Top 10 Soluções por Score",
                    color='Score',
                    color_continuous_scale='Viridis'
                )
                fig.update_xaxes(tickangle=45)
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
    
    def _show_solution_selection(self, solution_data: Dict):
        """Seleção final de soluções"""
        st.markdown("#### 🏆 Seleção Final de Soluções")
        
        if not solution_data.get('solutions'):
            st.info("💡 Adicione e avalie soluções primeiro")
            return
        
        # Filtrar soluções avaliadas
        evaluated_solutions = [sol for sol in solution_data['solutions'] if sol.get('evaluation_score', 0) > 0]
        
        if not evaluated_solutions:
            st.warning("⚠️ Avalie as soluções primeiro na aba 'Avaliação'")
            return
        
        # Ordenar por score
        ranked_solutions = sorted(
            evaluated_solutions,
            key=lambda x: x.get('evaluation_score', 0),
            reverse=True
        )
        
        st.markdown("##### 📊 Matriz de Decisão")
        
        # Mostrar top soluções
        top_solutions = ranked_solutions[:5]  # Top 5
        
        for i, solution in enumerate(top_solutions, 1):
            score = solution.get('evaluation_score', 0)
            
            with st.expander(f"**#{i} - {solution['name']}** (Score: {score:.1f})"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Descrição:** {solution['description']}")
                    st.write(f"**Tipo:** {solution['type']}")
                    st.write(f"**Complexidade:** {solution['complexity']}")
                
                with col2:
                    st.write(f"**Custo:** R$ {solution['cost_estimate']:,.2f}")
                    st.write(f"**Tempo:** {solution['implementation_time']} dias")
                    st.write(f"**Impacto:** {solution['expected_impact']}")
                    
                    # Radar chart dos scores
                    categories = ['Viabilidade', 'Impacto', 'Custo-Benefício', 'Rapidez', 'Baixo Risco', 'Sustentabilidade']
                    values = [
                        solution.get('feasibility_score', 0),
                        solution.get('impact_score', 0),
                        solution.get('cost_score', 0),
                        solution.get('time_score', 0),
                        solution.get('risk_score', 0),
                        solution.get('sustainability_score', 0)
                    ]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        name=solution['name']
                    ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 10]
                            )),
                        showlegend=False,
                        height=300,
                        title=f"Perfil da Solução"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with col3:
                    # Ações
                    current_status = solution['status']
                    
                    if st.button("✅ Selecionar", key=f"select_solution_{i}_{self.project_id}"):
                        original_index = solution_data['solutions'].index(solution)
                        solution_data['solutions'][original_index]['status'] = 'Aprovada'
                        solution_data['solutions'][original_index]['selected_at'] = datetime.now().isoformat()
                        st.success("✅ Solução selecionada!")
                        st.rerun()
                    
                    if st.button("❌ Rejeitar", key=f"reject_solution_{i}_{self.project_id}"):
                        original_index = solution_data['solutions'].index(solution)
                        solution_data['solutions'][original_index]['status'] = 'Rejeitada'
                        st.warning("❌ Solução rejeitada")
                        st.rerun()
        
        # Resumo das soluções selecionadas
        selected_solutions = [sol for sol in solution_data['solutions'] if sol['status'] == 'Aprovada']
        
        if selected_solutions:
            st.markdown("##### 🎯 Soluções Selecionadas para Implementação")
            
            total_cost = sum(sol['cost_estimate'] for sol in selected_solutions)
            total_time = max(sol['implementation_time'] for sol in selected_solutions) if selected_solutions else 0
            avg_score = sum(sol.get('evaluation_score', 0) for sol in selected_solutions) / len(selected_solutions)
            
            col_sel1, col_sel2, col_sel3, col_sel4 = st.columns(4)
            
            with col_sel1:
                st.metric("Soluções Selecionadas", len(selected_solutions))
            
            with col_sel2:
                st.metric("Custo Total", f"R$ {total_cost:,.2f}")
            
            with col_sel3:
                st.metric("Tempo Máximo", f"{total_time} dias")
            
            with col_sel4:
                st.metric("Score Médio", f"{avg_score:.1f}")
            
            # Lista das selecionadas
            for i, solution in enumerate(selected_solutions, 1):
                st.success(f"**{i}.** {solution['name']} - R$ {solution['cost_estimate']:,.2f} - {solution['implementation_time']} dias")

    def _show_action_buttons(self, solution_data: Dict):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Desenvolvimento", key=f"save_{self.tool_name}_{self.project_id}"):
                success = self.manager.save_tool_data(self.tool_name, solution_data, completed=False)
                if success:
                    st.success("💾 Desenvolvimento de soluções salvo!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("✅ Finalizar Desenvolvimento", key=f"complete_{self.tool_name}_{self.project_id}"):
                if self._validate_solution_development(solution_data):
                    success = self.manager.save_tool_data(self.tool_name, solution_data, completed=True)
                    if success:
                        st.success("✅ Desenvolvimento de soluções finalizado!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao finalizar")
                else:
                    st.error("❌ Complete os requisitos mínimos")
    
    def _validate_solution_development(self, solution_data: Dict) -> bool:
        """Valida se o desenvolvimento está completo"""
        if not solution_data.get('solutions'):
            st.error("❌ Adicione pelo menos uma solução")
            return False
        
        approved = [sol for sol in solution_data['solutions'] if sol['status'] == 'Aprovada']
        if not approved:
            st.error("❌ Aprove pelo menos uma solução")
            return False
        
        return True

    
    def _show_action_buttons(self, solution_data: Dict):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Desenvolvimento", key=f"save_{self.tool_name}_{self.project_id}"):
                success = self.manager.save_tool_data(self.tool_name, solution_data, completed=False)
                if success:
                    st.success("💾 Desenvolvimento de soluções salvo!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("✅ Finalizar Desenvolvimento", key=f"complete_{self.tool_name}_{self.project_id}"):
                if self._validate_solution_development(solution_data):
                    success = self.manager.save_tool_data(self.tool_name, solution_data, completed=True)
                    if success:
                        st.success("✅ Desenvolvimento de soluções finalizado!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao finalizar")
                else:
                    st.error("❌ Complete os requisitos mínimos")
    
    def _validate_solution_development(self, solution_data: Dict) -> bool:
        """Valida se o desenvolvimento está completo"""
        # Verificar se há pelo menos uma solução
        if not solution_data.get('solutions'):
            st.error("❌ Adicione pelo menos uma solução")
            return False
        
        # Verificar se há pelo menos uma solução avaliada
        evaluated = [sol for sol in solution_data['solutions'] if sol.get('evaluation_score', 0) > 0]
        if not evaluated:
            st.error("❌ Avalie pelo menos uma solução")
            return False
        
        # Verificar se há pelo menos uma solução selecionada
        selected = [sol for sol in solution_data['solutions'] if sol['status'] == 'Aprovada']
        if not selected:
            st.error("❌ Selecione pelo menos uma solução para implementação")
            return False
        
        return True


class ActionPlanTool:
    """Ferramenta para Plano de Ação"""
    
    def __init__(self, manager: ImprovePhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "action_plan"
    
    def show(self):
        """Interface principal da ferramenta"""
        st.markdown("## 📋 Plano de Ação")
        st.markdown("Crie um plano detalhado para implementar as soluções selecionadas.")
        
        # Status da ferramenta
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ **Plano de ação finalizado**")
        else:
            st.info("⏳ **Plano em desenvolvimento**")
        
        # Verificar soluções selecionadas
        selected_solutions = self._get_selected_solutions()
        
        if not selected_solutions:
            st.warning("⚠️ **Nenhuma solução selecionada encontrada**")
            st.info("💡 Complete o 'Desenvolvimento de Soluções' primeiro")
            return
        
        # Inicializar dados da sessão
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data if existing_data else {
                'action_items': [],
                'timeline': {},
                'resources': {},
                'risks': []
            }
        
        action_data = st.session_state[session_key]
        
        # Mostrar soluções selecionadas
        self._show_selected_solutions(selected_solutions)
        
        # Interface principal
        self._show_action_plan_tabs(action_data, selected_solutions)
        
        # Botões de ação
        self._show_action_buttons(action_data)
    
    def _get_selected_solutions(self) -> List[Dict]:
        """Recupera soluções selecionadas"""
        solution_data = self.manager.get_tool_data('solution_development')
        solutions = solution_data.get('solutions', [])
        return [sol for sol in solutions if sol.get('status') == 'Aprovada']
    
    def _show_selected_solutions(self, selected_solutions: List[Dict]):
        """Mostra soluções selecionadas"""
        st.markdown("### 🎯 Soluções para Implementação")
        
        for i, solution in enumerate(selected_solutions, 1):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{i}.** {solution['name']}")
                st.caption(solution.get('description', '')[:100] + "...")
            
            with col2:
                st.write(f"💰 R$ {solution.get('cost_estimate', 0):,.2f}")
            
            with col3:
                st.write(f"⏱️ {solution.get('implementation_time', 0)} dias")
    
    def _show_action_plan_tabs(self, action_data: Dict, selected_solutions: List[Dict]):
        """Mostra abas do plano de ação"""
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📝 Itens de Ação",
            "📅 Cronograma",
            "👥 Recursos",
            "⚠️ Riscos",
            "📊 Resumo"
        ])
        
        with tab1:
            self._show_action_items(action_data, selected_solutions)
        
        with tab2:
            self._show_timeline(action_data)
        
        with tab3:
            self._show_resources(action_data)
        
        with tab4:
            self._show_risks(action_data)
        
        with tab5:
            self._show_action_summary(action_data)
    
    def _show_action_items(self, action_data: Dict, selected_solutions: List[Dict]):
        """Gerenciamento de itens de ação"""
        st.markdown("#### 📝 Itens de Ação")
        
        # Gerar itens automaticamente das soluções
        if st.button("🤖 Gerar Itens Automaticamente", key=f"auto_generate_{self.project_id}"):
            for solution in selected_solutions:
                # Verificar se já existe item para esta solução
                existing = any(
                    item.get('solution_name') == solution['name'] 
                    for item in action_data.get('action_items', [])
                )
                
                if not existing:
                    action_data['action_items'].append({
                        'id': len(action_data.get('action_items', [])) + 1,
                        'solution_name': solution['name'],
                        'title': f"Implementar {solution['name']}",
                        'description': solution.get('description', ''),
                        'responsible': '',
                        'start_date': datetime.now().date().isoformat(),
                        'end_date': (datetime.now().date() + timedelta(days=solution.get('implementation_time', 30))).isoformat(),
                        'status': 'Não Iniciado',
                        'priority': 'Média',
                        'dependencies': [],
                        'deliverables': [],
                        'progress': 0,
                        'created_at': datetime.now().isoformat()
                    })
            
            st.success(f"✅ {len(selected_solutions)} itens gerados automaticamente!")
            st.rerun()
        
        # Adicionar item manualmente
        with st.expander("➕ Adicionar Item de Ação Manual"):
            col1, col2 = st.columns(2)
            
            with col1:
                item_title = st.text_input(
                    "Título da Ação:",
                    key=f"action_title_{self.project_id}",
                    placeholder="Ex: Treinar operadores no novo procedimento"
                )
                
                item_responsible = st.text_input(
                    "Responsável:",
                    key=f"action_responsible_{self.project_id}",
                    placeholder="Nome do responsável"
                )
                
                item_priority = st.selectbox(
                    "Prioridade:",
                    ["Baixa", "Média", "Alta", "Crítica"],
                    index=1,
                    key=f"action_priority_{self.project_id}"
                )
            
            with col2:
                item_start = st.date_input(
                    "Data de Início:",
                    value=datetime.now().date(),
                    key=f"action_start_{self.project_id}"
                )
                
                item_duration = st.number_input(
                    "Duração (dias):",
                    min_value=1,
                    max_value=365,
                    value=7,
                    key=f"action_duration_{self.project_id}"
                )
                
                item_end = item_start + timedelta(days=item_duration)
                st.info(f"Data fim: {item_end.strftime('%d/%m/%Y')}")
            
            item_description = st.text_area(
                "Descrição Detalhada:",
                key=f"action_description_{self.project_id}",
                placeholder="Descreva o que deve ser feito...",
                height=80
            )
            
            item_deliverables = st.text_area(
                "Entregáveis (um por linha):",
                key=f"action_deliverables_{self.project_id}",
                placeholder="Lista dos entregáveis esperados..."
            )
            
            if st.button("📝 Adicionar Item", key=f"add_action_item_{self.project_id}"):
                if item_title.strip() and item_responsible.strip():
                    deliverables_list = [d.strip() for d in item_deliverables.split('\n') if d.strip()]
                    
                    action_data['action_items'].append({
                        'id': len(action_data.get('action_items', [])) + 1,
                        'title': item_title,
                        'description': item_description,
                        'responsible': item_responsible,
                        'start_date': item_start.isoformat(),
                        'end_date': item_end.isoformat(),
                        'status': 'Não Iniciado',
                        'priority': item_priority,
                        'dependencies': [],
                        'deliverables': deliverables_list,
                        'progress': 0,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Item '{item_title}' adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Preencha título e responsável")
        
        # Mostrar itens existentes
        if action_data.get('action_items'):
            st.markdown("#### 📊 Itens de Ação Cadastrados")
            
            # Filtros
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                status_filter = st.selectbox(
                    "Filtrar por Status:",
                    ["Todos", "Não Iniciado", "Em Progresso", "Concluído", "Atrasado"],
                    key=f"status_filter_{self.project_id}"
                )
            
            with col_f2:
                priority_filter = st.selectbox(
                    "Filtrar por Prioridade:",
                    ["Todas", "Crítica", "Alta", "Média", "Baixa"],
                    key=f"priority_filter_{self.project_id}"
                )
            
            with col_f3:
                responsible_filter = st.selectbox(
                    "Filtrar por Responsável:",
                    ["Todos"] + list(set([item['responsible'] for item in action_data['action_items'] if item.get('responsible')])),
                    key=f"responsible_filter_{self.project_id}"
                )
            
            # Aplicar filtros
            filtered_items = action_data['action_items']
            
            if status_filter != "Todos":
                filtered_items = [item for item in filtered_items if item.get('status') == status_filter]
            
            if priority_filter != "Todas":
                filtered_items = [item for item in filtered_items if item.get('priority') == priority_filter]
            
            if responsible_filter != "Todos":
                filtered_items = [item for item in filtered_items if item.get('responsible') == responsible_filter]
            
            # Mostrar itens
            for i, item in enumerate(filtered_items):
                original_index = action_data['action_items'].index(item)
                
                # Determinar cor baseada na prioridade
                priority_colors = {
                    'Crítica': '🔴',
                    'Alta': '🟠', 
                    'Média': '🟡',
                    'Baixa': '🟢'
                }
                
                priority_icon = priority_colors.get(item.get('priority', 'Média'), '🟡')
                
                with st.expander(f"{priority_icon} **{item['title']}** - {item.get('status', 'Não Iniciado')} ({item.get('responsible', 'Sem responsável')})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Descrição:** {item.get('description', 'N/A')}")
                        if item.get('solution_name'):
                            st.write(f"**Solução:** {item['solution_name']}")
                        
                        # Deliverables
                        if item.get('deliverables'):
                            st.write("**Entregáveis:**")
                            for deliverable in item['deliverables']:
                                st.write(f"• {deliverable}")
                    
                    with col2:
                        # Datas
                        start_date = datetime.fromisoformat(item['start_date']).date()
                        end_date = datetime.fromisoformat(item['end_date']).date()
                        
                        st.write(f"**Início:** {start_date.strftime('%d/%m/%Y')}")
                        st.write(f"**Fim:** {end_date.strftime('%d/%m/%Y')}")
                        st.write(f"**Duração:** {(end_date - start_date).days + 1} dias")
                        
                        # Status e progresso
                        new_status = st.selectbox(
                            "Status:",
                            ["Não Iniciado", "Em Progresso", "Concluído", "Atrasado"],
                            index=["Não Iniciado", "Em Progresso", "Concluído", "Atrasado"].index(item.get('status', 'Não Iniciado')),
                            key=f"item_status_{original_index}_{self.project_id}"
                        )
                        
                        action_data['action_items'][original_index]['status'] = new_status
                        
                        # Progresso
                        progress = st.slider(
                            "Progresso:",
                            0, 100, item.get('progress', 0),
                            key=f"item_progress_{original_index}_{self.project_id}",
                            format="%d%%"
                        )
                        
                        action_data['action_items'][original_index]['progress'] = progress
                    
                    with col3:
                        if st.button("🗑️ Remover", key=f"remove_item_{original_index}_{self.project_id}"):
                            action_data['action_items'].pop(original_index)
                            st.rerun()
                        
                        # Verificar atraso
                        if end_date < datetime.now().date() and new_status != 'Concluído':
                            st.error("⚠️ Atrasado")
        else:
            st.info("📝 Nenhum item de ação cadastrado. Use a geração automática ou adicione manualmente.")
    
    def _show_timeline(self, action_data: Dict):
        """Cronograma do projeto"""
        st.markdown("#### 📅 Cronograma de Implementação")
        
        if not action_data.get('action_items'):
            st.info("💡 Adicione itens de ação primeiro")
            return
        
        # Gráfico de Gantt simplificado
        items = action_data['action_items']
        
        # Preparar dados para o gráfico
        gantt_data = []
        
        for item in items:
            start_date = datetime.fromisoformat(item['start_date'])
            end_date = datetime.fromisoformat(item['end_date'])
            
            gantt_data.append({
                'Task': item['title'][:30] + "..." if len(item['title']) > 30 else item['title'],
                'Start': start_date,
                'Finish': end_date,
                'Resource': item.get('responsible', 'Não atribuído'),
                'Status': item.get('status', 'Não Iniciado'),
                'Progress': item.get('progress', 0)
            })
        
        if gantt_data:
            # Criar gráfico de barras horizontais como Gantt
            fig = go.Figure()
            
            colors = {
                'Não Iniciado': 'lightgray',
                'Em Progresso': 'orange', 
                'Concluído': 'green',
                'Atrasado': 'red'
            }
            
            for i, task in enumerate(gantt_data):
                fig.add_trace(go.Bar(
                    y=[task['Task']],
                    x=[(task['Finish'] - task['Start']).days],
                    base=[task['Start']],
                    orientation='h',
                    name=task['Status'],
                    marker_color=colors.get(task['Status'], 'blue'),
                    text=f"{task['Progress']}%",
                    textposition='inside',
                    showlegend=i == 0  # Mostrar legenda apenas para o primeiro item de cada status
                ))
            
            fig.update_layout(
                title="Cronograma de Implementação (Gráfico de Gantt)",
                xaxis_title="Data",
                yaxis_title="Tarefas",
                height=max(400, len(gantt_data) * 40),
                barmode='overlay'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas do cronograma
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_tasks = len(items)
                st.metric("Total de Tarefas", total_tasks)
            
            with col2:
                completed_tasks = len([item for item in items if item.get('status') == 'Concluído'])
                st.metric("Concluídas", completed_tasks)
            
            with col3:
                in_progress = len([item for item in items if item.get('status') == 'Em Progresso'])
                st.metric("Em Progresso", in_progress)
            
            with col4:
                overdue = len([item for item in items 
                              if datetime.fromisoformat(item['end_date']).date() < datetime.now().date() 
                              and item.get('status') != 'Concluído'])
                st.metric("Atrasadas", overdue)
            
            # Progresso geral
            if total_tasks > 0:
                overall_progress = sum(item.get('progress', 0) for item in items) / total_tasks
                st.progress(overall_progress / 100)
                st.caption(f"Progresso Geral: {overall_progress:.1f}%")
    
    def _show_resources(self, action_data: Dict):
        """Planejamento de recursos"""
        st.markdown("#### 👥 Planejamento de Recursos")
        
        # Recursos humanos
        st.markdown("##### 👤 Recursos Humanos")
        
        if 'resources' not in action_data:
            action_data['resources'] = {'human': [], 'material': [], 'financial': {}}
        
        # Adicionar recurso humano
        with st.expander("➕ Adicionar Recurso Humano"):
            col1, col2 = st.columns(2)
            
            with col1:
                person_name = st.text_input("Nome:", key=f"person_name_{self.project_id}")
                person_role = st.text_input("Função:", key=f"person_role_{self.project_id}")
                person_department = st.text_input("Departamento:", key=f"person_department_{self.project_id}")
            
            with col2:
                person_availability = st.slider(
                    "Disponibilidade (%):",
                    0, 100, 100,
                    key=f"person_availability_{self.project_id}"
                )
                
                person_hourly_cost = st.number_input(
                    "Custo/Hora (R$):",
                    min_value=0.0,
                    value=0.0,
                    key=f"person_cost_{self.project_id}"
                )
            
            person_skills = st.text_area(
                "Habilidades/Competências:",
                key=f"person_skills_{self.project_id}",
                placeholder="Liste as principais habilidades..."
            )
            
            if st.button("👤 Adicionar Pessoa", key=f"add_person_{self.project_id}"):
                if person_name.strip() and person_role.strip():
                    action_data['resources']['human'].append({
                        'name': person_name,
                        'role': person_role,
                        'department': person_department,
                        'availability': person_availability,
                        'hourly_cost': person_hourly_cost,
                        'skills': person_skills,
                        'assigned_tasks': []
                    })
                    
                    st.success(f"✅ {person_name} adicionado!")
                    st.rerun()
        
        # Mostrar recursos humanos
        if action_data['resources']['human']:
            for i, person in enumerate(action_data['resources']['human']):
                with st.expander(f"👤 {person['name']} - {person['role']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Departamento:** {person.get('department', 'N/A')}")
                        st.write(f"**Disponibilidade:** {person.get('availability', 0)}%")
                        if person.get('skills'):
                            st.write(f"**Habilidades:** {person['skills']}")
                    
                    with col2:
                        st.write(f"**Custo/Hora:** R$ {person.get('hourly_cost', 0):.2f}")
                        
                        # Atribuir tarefas
                        if action_data.get('action_items'):
                            available_tasks = [item['title'] for item in action_data['action_items']]
                            assigned_tasks = st.multiselect(
                                "Tarefas Atribuídas:",
                                available_tasks,
                                default=person.get('assigned_tasks', []),
                                key=f"person_tasks_{i}_{self.project_id}"
                            )
                            
                            action_data['resources']['human'][i]['assigned_tasks'] = assigned_tasks
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_person_{i}_{self.project_id}"):
                            action_data['resources']['human'].pop(i)
                            st.rerun()
        
        # Recursos materiais
        st.markdown("##### 📦 Recursos Materiais")
        
        with st.expander("➕ Adicionar Recurso Material"):
            col1, col2 = st.columns(2)
            
            with col1:
                material_name = st.text_input("Item:", key=f"material_name_{self.project_id}")
                material_quantity = st.number_input("Quantidade:", min_value=1, key=f"material_qty_{self.project_id}")
                material_unit = st.text_input("Unidade:", key=f"material_unit_{self.project_id}")
            
            with col2:
                material_cost = st.number_input("Custo Unitário (R$):", min_value=0.0, key=f"material_cost_{self.project_id}")
                material_supplier = st.text_input("Fornecedor:", key=f"material_supplier_{self.project_id}")
                material_delivery = st.date_input("Prazo de Entrega:", key=f"material_delivery_{self.project_id}")
            
            if st.button("📦 Adicionar Material", key=f"add_material_{self.project_id}"):
                if material_name.strip():
                    action_data['resources']['material'].append({
                        'name': material_name,
                        'quantity': material_quantity,
                        'unit': material_unit,
                        'unit_cost': material_cost,
                        'total_cost': material_quantity * material_cost,
                        'supplier': material_supplier,
                        'delivery_date': material_delivery.isoformat()
                    })
                    
                    st.success(f"✅ {material_name} adicionado!")
                    st.rerun()
        
        # Mostrar recursos materiais
        if action_data['resources']['material']:
            material_total = sum(item['total_cost'] for item in action_data['resources']['material'])
            st.write(f"**Custo Total de Materiais:** R$ {material_total:,.2f}")
            
            for i, material in enumerate(action_data['resources']['material']):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{material['name']}**")
                    st.caption(f"Fornecedor: {material.get('supplier', 'N/A')}")
                
                with col2:
                    st.write(f"{material['quantity']} {material.get('unit', 'un')}")
                
                with col3:
                    st.write(f"R$ {material['total_cost']:,.2f}")
                
                with col4:
                    if st.button("🗑️", key=f"remove_material_{i}_{self.project_id}"):
                        action_data['resources']['material'].pop(i)
                        st.rerun()
    
    def _show_risks(self, action_data: Dict):
        """Análise de riscos"""
        st.markdown("#### ⚠️ Análise de Riscos")
        
        # Adicionar novo risco
        with st.expander("➕ Adicionar Risco"):
            col1, col2 = st.columns(2)
            
            with col1:
                risk_name = st.text_input("Risco:", key=f"risk_name_{self.project_id}")
                risk_category = st.selectbox(
                    "Categoria:",
                    ["Técnico", "Recursos", "Cronograma", "Qualidade", "Financeiro", "Organizacional"],
                    key=f"risk_category_{self.project_id}"
                )
                
                risk_probability = st.selectbox(
                    "Probabilidade:",
                    ["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta"],
                    index=2,
                    key=f"risk_probability_{self.project_id}"
                )
            
            with col2:
                risk_impact = st.selectbox(
                    "Impacto:",
                    ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"],
                    index=2,
                    key=f"risk_impact_{self.project_id}"
                )
                
                risk_owner = st.text_input("Responsável:", key=f"risk_owner_{self.project_id}")
            
            risk_description = st.text_area(
                "Descrição do Risco:",
                key=f"risk_description_{self.project_id}",
                placeholder="Descreva o risco em detalhes..."
            )
            
            risk_mitigation = st.text_area(
                "Ações de Mitigação:",
                key=f"risk_mitigation_{self.project_id}",
                placeholder="Como prevenir ou reduzir este risco?"
            )
            
            if st.button("⚠️ Adicionar Risco", key=f"add_risk_{self.project_id}"):
                if risk_name.strip():
                    # Calcular score de risco
                    prob_scores = {"Muito Baixa": 1, "Baixa": 2, "Média": 3, "Alta": 4, "Muito Alta": 5}
                    impact_scores = {"Muito Baixo": 1, "Baixo": 2, "Médio": 3, "Alto": 4, "Muito Alto": 5}
                    
                    risk_score = prob_scores[risk_probability] * impact_scores[risk_impact]
                    
                    action_data['risks'].append({
                        'name': risk_name,
                        'category': risk_category,
                        'description': risk_description,
                        'probability': risk_probability,
                        'impact': risk_impact,
                        'score': risk_score,
                        'owner': risk_owner,
                        'mitigation': risk_mitigation,
                        'status': 'Identificado',
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Risco '{risk_name}' adicionado!")
                    st.rerun()
        
        # Mostrar riscos existentes
        if action_data.get('risks'):
            st.markdown("##### 📊 Matriz de Riscos")
            
            # Ordenar por score
            sorted_risks = sorted(action_data['risks'], key=lambda x: x.get('score', 0), reverse=True)
            
            for i, risk in enumerate(sorted_risks):
                original_index = action_data['risks'].index(risk)
                
                # Determinar cor baseada no score
                score = risk.get('score', 0)
                if score >= 15:
                    color = "🔴 Crítico"
                elif score >= 9:
                    color = "🟠 Alto"
                elif score >= 4:
                    color = "🟡 Médio"
                else:
                    color = "🟢 Baixo"
                
                with st.expander(f"{color} - **{risk['name']}** (Score: {score})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Categoria:** {risk['category']}")
                        st.write(f"**Descrição:** {risk.get('description', 'N/A')}")
                        st.write(f"**Responsável:** {risk.get('owner', 'Não atribuído')}")
                    
                    with col2:
                        st.write(f"**Probabilidade:** {risk['probability']}")
                        st.write(f"**Impacto:** {risk['impact']}")
                        
                        new_status = st.selectbox(
                            "Status:",
                            ["Identificado", "Em Monitoramento", "Mitigado", "Ocorrido"],
                            index=["Identificado", "Em Monitoramento", "Mitigado", "Ocorrido"].index(risk.get('status', 'Identificado')),
                            key=f"risk_status_{original_index}_{self.project_id}"
                        )
                        
                        action_data['risks'][original_index]['status'] = new_status
                        
                        if risk.get('mitigation'):
                            st.write(f"**Mitigação:** {risk['mitigation']}")
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_risk_{original_index}_{self.project_id}"):
                            action_data['risks'].pop(original_index)
                            st.rerun()
            
            # Gráfico de riscos
            if len(action_data['risks']) > 1:
                risk_categories = {}
                for risk in action_data['risks']:
                    category = risk.get('category', 'Outros')
                    if category not in risk_categories:
                        risk_categories[category] = 0
                    risk_categories[category] += 1
                
                fig = px.pie(
                    values=list(risk_categories.values()),
                    names=list(risk_categories.keys()),
                    title="Distribuição de Riscos por Categoria"
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def _show_action_summary(self, action_data: Dict):
        """Resumo do plano de ação"""
        st.markdown("#### 📊 Resumo do Plano de Ação")
        
        # Métricas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_actions = len(action_data.get('action_items', []))
            st.metric("Total de Ações", total_actions)
        
        with col2:
            total_people = len(action_data.get('resources', {}).get('human', []))
            st.metric("Recursos Humanos", total_people)
        
        with col3:
            material_cost = sum(item.get('total_cost', 0) for item in action_data.get('resources', {}).get('material', []))
            st.metric("Custo de Materiais", f"R$ {material_cost:,.2f}")
        
        with col4:
            total_risks = len(action_data.get('risks', []))
            st.metric("Riscos Identificados", total_risks)
        
        # Cronograma resumido
        if action_data.get('action_items'):
            st.markdown("##### 📅 Resumo do Cronograma")
            
            items = action_data['action_items']
            start_dates = [datetime.fromisoformat(item['start_date']) for item in items]
            end_dates = [datetime.fromisoformat(item['end_date']) for item in items]
            
            project_start = min(start_dates)
            project_end = max(end_dates)
            project_duration = (project_end - project_start).days + 1
            
            col_time1, col_time2, col_time3 = st.columns(3)
            
            with col_time1:
                st.write(f"**Início:** {project_start.strftime('%d/%m/%Y')}")
            
            with col_time2:
                st.write(f"**Fim:** {project_end.strftime('%d/%m/%Y')}")
            
            with col_time3:
                st.write(f"**Duração:** {project_duration} dias")
            
            # Progresso geral
            if items:
                overall_progress = sum(item.get('progress', 0) for item in items) / len(items)
                st.progress(overall_progress / 100)
                st.caption(f"Progresso Geral: {overall_progress:.1f}%")
        
        # Status das ações
        if action_data.get('action_items'):
            st.markdown("##### 📈 Status das Ações")
            
            status_count = {}
            for item in action_data['action_items']:
                status = item.get('status', 'Não Iniciado')
                status_count[status] = status_count.get(status, 0) + 1
            
            fig = px.bar(
                x=list(status_count.keys()),
                y=list(status_count.values()),
                title="Distribuição de Ações por Status",
                color=list(status_count.values()),
                color_continuous_scale='Viridis'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Principais riscos
        if action_data.get('risks'):
            st.markdown("##### ⚠️ Principais Riscos")
            
            high_risks = [risk for risk in action_data['risks'] if risk.get('score', 0) >= 9]
            
            if high_risks:
                for risk in high_risks[:3]:  # Top 3
                    st.error(f"🔴 **{risk['name']}** (Score: {risk.get('score', 0)}) - {risk.get('category', 'N/A')}")
            else:
                st.success("✅ Nenhum risco crítico identificado")
    
    def _show_action_buttons(self, action_data: Dict):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Plano", key=f"save_{self.tool_name}_{self.project_id}"):
                success = self.manager.save_tool_data(self.tool_name, action_data, completed=False)
                if success:
                    st.success("💾 Plano de ação salvo!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("✅ Finalizar Plano", key=f"complete_{self.tool_name}_{self.project_id}"):
                if self._validate_action_plan(action_data):
                    success = self.manager.save_tool_data(self.tool_name, action_data, completed=True)
                    if success:
                        st.success("✅ Plano de ação finalizado!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao finalizar")
                else:
                    st.error("❌ Complete os requisitos mínimos")
    
    def _validate_action_plan(self, action_data: Dict) -> bool:
        """Valida se o plano está completo"""
        # Verificar se há itens de ação
        if not action_data.get('action_items'):
            st.error("❌ Adicione pelo menos um item de ação")
            return False
        
        # Verificar se há responsáveis atribuídos
        items_without_responsible = [item for item in action_data['action_items'] if not item.get('responsible', '').strip()]
        if items_without_responsible:
            st.error(f"❌ {len(items_without_responsible)} item(ns) sem responsável")
            return False
        
        # Verificar se há recursos planejados
        if not action_data.get('resources', {}).get('human') and not action_data.get('resources', {}).get('material'):
            st.warning("⚠️ Nenhum recurso planejado")
        
        return True


class PilotImplementationTool:
    """Ferramenta para Implementação Piloto"""
    
    def __init__(self, manager: ImprovePhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "pilot_implementation"
    
    def show(self):
        """Interface principal da ferramenta"""
        st.markdown("## 🧪 Implementação Piloto")
        st.markdown("Execute um piloto controlado das soluções antes da implementação completa.")
        
        # Status da ferramenta
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ **Implementação piloto finalizada**")
        else:
            st.info("⏳ **Piloto em desenvolvimento**")
        
        # Verificar se há plano de ação
        action_plan = self.manager.get_tool_data('action_plan')
        if not action_plan.get('action_items'):
            st.warning("⚠️ **Plano de ação não encontrado**")
            st.info("💡 Complete o 'Plano de Ação' primeiro")
            return
        
        # Inicializar dados da sessão
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data if existing_data else {
                'pilot_scope': {},
                'pilot_plan': {},
                'measurements': [],
                'results': {},
                'lessons_learned': []
            }
        
        pilot_data = st.session_state[session_key]
        
        # Interface principal
        self._show_pilot_tabs(pilot_data, action_plan)
        
        # Botões de ação
        self._show_action_buttons(pilot_data)
    
    def _show_pilot_tabs(self, pilot_data: Dict, action_plan: Dict):
        """Mostra abas do piloto"""
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎯 Escopo do Piloto",
            "📋 Plano do Piloto", 
            "📊 Medições",
            "📈 Resultados",
            "🎓 Lições Aprendidas"
        ])
        
        with tab1:
            self._show_pilot_scope(pilot_data, action_plan)
        
        with tab2:
            self._show_pilot_plan(pilot_data)
        
        with tab3:
            self._show_measurements(pilot_data)
        
        with tab4:
            self._show_results(pilot_data)
        
        with tab5:
            self._show_lessons_learned(pilot_data)
    
    def _show_pilot_scope(self, pilot_data: Dict, action_plan: Dict):
        """Definição do escopo do piloto"""
        st.markdown("#### 🎯 Definição do Escopo do Piloto")
        
        if 'pilot_scope' not in pilot_data:
            pilot_data['pilot_scope'] = {}
        
        scope = pilot_data['pilot_scope']
        
        # Seleção de soluções para piloto
        st.markdown("##### 💡 Soluções para Piloto")
        
        available_actions = action_plan.get('action_items', [])
        selected_actions = st.multiselect(
            "Selecione ações para incluir no piloto:",
            [f"{item['title']} - {item.get('responsible', 'Sem responsável')}" for item in available_actions],
            default=scope.get('selected_actions', []),
            key=f"pilot_actions_{self.project_id}",
            help="Escolha as ações que serão testadas no piloto"
        )
        
        scope['selected_actions'] = selected_actions
        
        # Definição do escopo
        col1, col2 = st.columns(2)
        
        with col1:
            scope['area'] = st.text_input(
                "Área/Setor do Piloto:",
                value=scope.get('area', ''),
                key=f"pilot_area_{self.project_id}",
                placeholder="Ex: Linha de produção A, Setor de atendimento"
            )
            
            scope['population'] = st.text_input(
                "População Alvo:",
                value=scope.get('population', ''),
                key=f"pilot_population_{self.project_id}",
                placeholder="Ex: 50 funcionários, 100 clientes por dia"
            )
            
            scope['duration'] = st.number_input(
                "Duração do Piloto (dias):",
                min_value=1,
                max_value=180,
                value=scope.get('duration', 30),
                key=f"pilot_duration_{self.project_id}"
            )
        
        with col2:
            scope['start_date'] = st.date_input(
                "Data de Início:",
                value=datetime.fromisoformat(scope.get('start_date', datetime.now().date().isoformat())),
                key=f"pilot_start_{self.project_id}"
            ).isoformat()
            
            scope['success_criteria'] = st.text_area(
                "Critérios de Sucesso:",
                value=scope.get('success_criteria', ''),
                key=f"pilot_criteria_{self.project_id}",
                placeholder="Ex: Redução de 20% no tempo de processo, Aumento de 15% na satisfação",
                height=80
            )
        
        # Recursos necessários
        st.markdown("##### 👥 Recursos para o Piloto")
        
        scope['pilot_team'] = st.text_area(
            "Equipe do Piloto:",
            value=scope.get('pilot_team', ''),
            key=f"pilot_team_{self.project_id}",
            placeholder="Liste os membros da equipe e suas responsabilidades..."
        )
        
        scope['budget'] = st.number_input(
            "Orçamento do Piloto (R$):",
            min_value=0.0,
            value=scope.get('budget', 0.0),
            key=f"pilot_budget_{self.project_id}"
        )
        
        # Riscos específicos do piloto
        scope['pilot_risks'] = st.text_area(
            "Riscos Específicos do Piloto:",
            value=scope.get('pilot_risks', ''),
            key=f"pilot_risks_{self.project_id}",
            placeholder="Identifique riscos específicos da implementação piloto..."
        )
    
    def _show_pilot_plan(self, pilot_data: Dict):
        """Planejamento detalhado do piloto"""
        st.markdown("#### 📋 Plano Detalhado do Piloto")
        
        if 'pilot_plan' not in pilot_data:
            pilot_data['pilot_plan'] = {}
        
        plan = pilot_data['pilot_plan']
        
        # Fases do piloto
        st.markdown("##### 📅 Fases do Piloto")
        
        phases = [
            ("Preparação", "Preparação da equipe, recursos e ambiente"),
            ("Execução", "Implementação das soluções no ambiente piloto"),
            ("Monitoramento", "Coleta de dados e acompanhamento"),
            ("Avaliação", "Análise dos resultados e tomada de decisão")
        ]
        
        for i, (phase_name, phase_desc) in enumerate(phases):
            with st.expander(f"**Fase {i+1}: {phase_name}**"):
                phase_key = phase_name.lower()
                
                if phase_key not in plan:
                    plan[phase_key] = {}
                
                col1, col2 = st.columns(2)
                
                with col1:
                    plan[phase_key]['duration'] = st.number_input(
                        f"Duração da {phase_name} (dias):",
                        min_value=1,
                        max_value=60,
                        value=plan[phase_key].get('duration', 7),
                        key=f"phase_{phase_key}_duration_{self.project_id}"
                    )
                    
                    plan[phase_key]['responsible'] = st.text_input(
                        f"Responsável pela {phase_name}:",
                        value=plan[phase_key].get('responsible', ''),
                        key=f"phase_{phase_key}_responsible_{self.project_id}"
                    )
                
                with col2:
                    plan[phase_key]['activities'] = st.text_area(
                        f"Atividades da {phase_name}:",
                        value=plan[phase_key].get('activities', ''),
                        key=f"phase_{phase_key}_activities_{self.project_id}",
                        placeholder=f"Liste as atividades da fase de {phase_name.lower()}...",
                        height=80
                    )
                
                plan[phase_key]['deliverables'] = st.text_area(
                    f"Entregáveis da {phase_name}:",
                    value=plan[phase_key].get('deliverables', ''),
                    key=f"phase_{phase_key}_deliverables_{self.project_id}",
                    placeholder="Liste os entregáveis esperados..."
                )
        
        # Cronograma visual
        if all(plan.get(phase.lower(), {}).get('duration') for phase, _ in phases):
            st.markdown("##### 📊 Cronograma do Piloto")
            
            # Calcular datas
            scope = pilot_data.get('pilot_scope', {})
            start_date = datetime.fromisoformat(scope.get('start_date', datetime.now().date().isoformat()))
            
            timeline_data = []
            current_date = start_date
            
            for phase_name, _ in phases:
                phase_key = phase_name.lower()
                duration = plan[phase_key].get('duration', 7)
                end_date = current_date + timedelta(days=duration)
                
                timeline_data.append({
                    'Fase': phase_name,
                    'Início': current_date,
                    'Fim': end_date,
                    'Duração': duration,
                    'Responsável': plan[phase_key].get('responsible', 'Não atribuído')
                })
                
                current_date = end_date + timedelta(days=1)
            
            # Criar gráfico de Gantt
            fig = go.Figure()
            
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            
            for i, phase in enumerate(timeline_data):
                fig.add_trace(go.Bar(
                    y=[phase['Fase']],
                    x=[phase['Duração']],
                    base=[phase['Início']],
                    orientation='h',
                    name=phase['Fase'],
                    marker_color=colors[i % len(colors)],
                    text=f"{phase['Duração']} dias",
                    textposition='inside'
                ))
            
            fig.update_layout(
                title="Cronograma das Fases do Piloto",
                xaxis_title="Data",
                yaxis_title="Fases",
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Resumo do cronograma
            total_duration = sum(phase['Duração'] for phase in timeline_data)
            project_end = timeline_data[-1]['Fim']
            
            col_time1, col_time2, col_time3 = st.columns(3)
            
            with col_time1:
                st.metric("Duração Total", f"{total_duration} dias")
            
            with col_time2:
                st.metric("Data de Início", start_date.strftime('%d/%m/%Y'))
            
            with col_time3:
                st.metric("Data de Fim", project_end.strftime('%d/%m/%Y'))
    
    def _show_measurements(self, pilot_data: Dict):
        """Sistema de medições do piloto"""
        st.markdown("#### 📊 Sistema de Medições do Piloto")
        
        if 'measurements' not in pilot_data:
            pilot_data['measurements'] = []
        
        # Adicionar nova medição
        with st.expander("➕ Adicionar Medição"):
            col1, col2 = st.columns(2)
            
            with col1:
                metric_name = st.text_input(
                    "Nome da Métrica:",
                    key=f"metric_name_{self.project_id}",
                    placeholder="Ex: Tempo de ciclo, Taxa de defeitos"
                )
                
                metric_unit = st.text_input(
                    "Unidade:",
                    key=f"metric_unit_{self.project_id}",
                    placeholder="Ex: minutos, %, peças/hora"
                )
                
                metric_frequency = st.selectbox(
                    "Frequência de Coleta:",
                    ["Diária", "Semanal", "Por lote", "Contínua"],
                    key=f"metric_frequency_{self.project_id}"
                )
            
            with col2:
                metric_target = st.number_input(
                    "Meta:",
                    value=0.0,
                    key=f"metric_target_{self.project_id}"
                )
                
                metric_baseline = st.number_input(
                    "Baseline (valor atual):",
                    value=0.0,
                    key=f"metric_baseline_{self.project_id}"
                )
                
                metric_responsible = st.text_input(
                    "Responsável pela Coleta:",
                    key=f"metric_responsible_{self.project_id}"
                )
            
            metric_method = st.text_area(
                "Método de Coleta:",
                key=f"metric_method_{self.project_id}",
                placeholder="Como esta métrica será coletada?",
                height=60
            )
            
            if st.button("📊 Adicionar Métrica", key=f"add_metric_{self.project_id}"):
                if metric_name.strip():
                    pilot_data['measurements'].append({
                        'name': metric_name,
                        'unit': metric_unit,
                        'frequency': metric_frequency,
                        'target': metric_target,
                        'baseline': metric_baseline,
                        'responsible': metric_responsible,
                        'method': metric_method,
                        'data_points': [],
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Métrica '{metric_name}' adicionada!")
                    st.rerun()
        
        # Mostrar métricas existentes
        if pilot_data['measurements']:
            st.markdown("##### 📈 Métricas do Piloto")
            
            for i, metric in enumerate(pilot_data['measurements']):
                with st.expander(f"📊 **{metric['name']}** ({metric.get('unit', 'unidade')})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Baseline:** {metric.get('baseline', 0)} {metric.get('unit', '')}")
                        st.write(f"**Meta:** {metric.get('target', 0)} {metric.get('unit', '')}")
                        st.write(f"**Frequência:** {metric.get('frequency', 'N/A')}")
                        st.write(f"**Responsável:** {metric.get('responsible', 'Não atribuído')}")
                        
                        if metric.get('method'):
                            st.write(f"**Método:** {metric['method']}")
                    
                    with col2:
                        # Interface para adicionar dados
                        st.markdown("**Adicionar Medição:**")
                        
                        new_date = st.date_input(
                            "Data:",
                            key=f"metric_date_{i}_{self.project_id}"
                        )
                        
                        new_value = st.number_input(
                            "Valor:",
                            key=f"metric_value_{i}_{self.project_id}"
                        )
                        
                        if st.button("➕ Adicionar", key=f"add_data_point_{i}_{self.project_id}"):
                            pilot_data['measurements'][i]['data_points'].append({
                                'date': new_date.isoformat(),
                                'value': new_value,
                                'added_at': datetime.now().isoformat()
                            })
                            
                            st.success("✅ Medição adicionada!")
                            st.rerun()
                        
                        # Mostrar últimas medições
                        data_points = metric.get('data_points', [])
                        if data_points:
                            st.write("**Últimas medições:**")
                            for dp in data_points[-3:]:  # Últimas 3
                                st.write(f"• {dp['date']}: {dp['value']} {metric.get('unit', '')}")
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_metric_{i}_{self.project_id}"):
                            pilot_data['measurements'].pop(i)
                            st.rerun()
                        
                        # Estatísticas da métrica
                        data_points = metric.get('data_points', [])
                        if data_points:
                            values = [dp['value'] for dp in data_points]
                            current_avg = sum(values) / len(values)
                            
                            st.metric("Média Atual", f"{current_avg:.2f}")
                            
                            # Comparar com baseline e meta
                            baseline = metric.get('baseline', 0)
                            target = metric.get('target', 0)
                            
                            if baseline != 0:
                                improvement = ((current_avg - baseline) / baseline) * 100
                                if improvement > 0:
                                    st.success(f"📈 +{improvement:.1f}%")
                                else:
                                    st.error(f"📉 {improvement:.1f}%")
            
            # Gráfico consolidado das métricas
            if len(pilot_data['measurements']) > 0:
                st.markdown("##### 📊 Dashboard das Métricas")
                
                metrics_with_data = [m for m in pilot_data['measurements'] if m.get('data_points')]
                
                if metrics_with_data:
                    # Criar subplots
                    fig = make_subplots(
                        rows=min(2, len(metrics_with_data)),
                        cols=2 if len(metrics_with_data) > 1 else 1,
                        subplot_titles=[m['name'] for m in metrics_with_data[:4]]
                    )
                    
                    for i, metric in enumerate(metrics_with_data[:4]):
                        row = i // 2 + 1
                        col = i % 2 + 1
                        
                        data_points = metric['data_points']
                        dates = [dp['date'] for dp in data_points]
                        values = [dp['value'] for dp in data_points]
                        
                        fig.add_trace(
                            go.Scatter(
                                x=dates,
                                y=values,
                                mode='lines+markers',
                                name=metric['name'],
                                showlegend=False
                            ),
                            row=row, col=col
                        )
                        
                        # Adicionar linha de baseline
                        if metric.get('baseline'):
                            fig.add_hline(
                                y=metric['baseline'],
                                line_dash="dash",
                                line_color="red",
                                row=row, col=col
                            )
                        
                        # Adicionar linha de meta
                        if metric.get('target'):
                            fig.add_hline(
                                y=metric['target'],
                                line_dash="dash",
                                line_color="green",
                                row=row, col=col
                            )
                    
                    fig.update_layout(
                        title="Evolução das Métricas do Piloto",
                        height=400 * min(2, (len(metrics_with_data) + 1) // 2)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 Nenhuma métrica definida ainda. Adicione métricas para acompanhar o piloto.")
    
    def _show_results(self, pilot_data: Dict):
        """Análise dos resultados do piloto"""
        st.markdown("#### 📈 Resultados do Piloto")
        
        if 'results' not in pilot_data:
            pilot_data['results'] = {}
        
        results = pilot_data['results']
        
        # Resumo executivo
        st.markdown("##### 📋 Resumo Executivo")
        
        results['executive_summary'] = st.text_area(
            "Resumo Executivo dos Resultados:",
            value=results.get('executive_summary', ''),
            key=f"exec_summary_{self.project_id}",
            placeholder="Descreva os principais resultados e conclusões do piloto...",
            height=120
        )
        
        # Análise das métricas
        if pilot_data.get('measurements'):
            st.markdown("##### 📊 Análise das Métricas")
            
            metrics_summary = []
            
            for metric in pilot_data['measurements']:
                if metric.get('data_points'):
                    data_points = metric['data_points']
                    values = [dp['value'] for dp in data_points]
                    
                    current_avg = sum(values) / len(values)
                    baseline = metric.get('baseline', 0)
                    target = metric.get('target', 0)
                    
                    # Calcular melhoria
                    improvement = 0
                    improvement_pct = 0
                    
                    if baseline != 0:
                        improvement = current_avg - baseline
                        improvement_pct = (improvement / baseline) * 100
                    
                    # Verificar se atingiu meta
                    target_achieved = False
                    if target != 0:
                        if target > baseline:  # Meta de aumento
                            target_achieved = current_avg >= target
                        else:  # Meta de redução
                            target_achieved = current_avg <= target
                    
                    metrics_summary.append({
                        'Métrica': metric['name'],
                        'Baseline': f"{baseline} {metric.get('unit', '')}",
                        'Resultado': f"{current_avg:.2f} {metric.get('unit', '')}",
                        'Meta': f"{target} {metric.get('unit', '')}",
                        'Melhoria': f"{improvement_pct:+.1f}%",
                        'Meta Atingida': '✅' if target_achieved else '❌'
                    })
            
            if metrics_summary:
                summary_df = pd.DataFrame(metrics_summary)
                st.dataframe(summary_df, use_container_width=True)
                
                # Estatísticas gerais
                total_metrics = len(metrics_summary)
                targets_achieved = len([m for m in metrics_summary if m['Meta Atingida'] == '✅'])
                
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                
                with col_stats1:
                    st.metric("Métricas Avaliadas", total_metrics)
                
                with col_stats2:
                    st.metric("Metas Atingidas", f"{targets_achieved}/{total_metrics}")
                
                with col_stats3:
                    success_rate = (targets_achieved / total_metrics) * 100 if total_metrics > 0 else 0
                    st.metric("Taxa de Sucesso", f"{success_rate:.1f}%")
        
        # Avaliação qualitativa
        st.markdown("##### 🎯 Avaliação Qualitativa")
        
        col1, col2 = st.columns(2)
        
        with col1:
            results['positive_aspects'] = st.text_area(
                "Aspectos Positivos:",
                value=results.get('positive_aspects', ''),
                key=f"positive_aspects_{self.project_id}",
                placeholder="O que funcionou bem no piloto?",
                height=100
            )
            
            results['implementation_ease'] = st.selectbox(
                "Facilidade de Implementação:",
                ["Muito Difícil", "Difícil", "Moderada", "Fácil", "Muito Fácil"],
                index=2 if not results.get('implementation_ease') else 
                      ["Muito Difícil", "Difícil", "Moderada", "Fácil", "Muito Fácil"].index(results['implementation_ease']),
                key=f"implementation_ease_{self.project_id}"
            )
        
        with col2:
            results['challenges'] = st.text_area(
                "Desafios Encontrados:",
                value=results.get('challenges', ''),
                key=f"challenges_{self.project_id}",
                placeholder="Quais foram os principais desafios?",
                height=100
            )
            
            results['team_acceptance'] = st.selectbox(
                "Aceitação da Equipe:",
                ["Muito Baixa", "Baixa", "Moderada", "Alta", "Muito Alta"],
                index=2 if not results.get('team_acceptance') else 
                      ["Muito Baixa", "Baixa", "Moderada", "Alta", "Muito Alta"].index(results['team_acceptance']),
                key=f"team_acceptance_{self.project_id}"
            )
        
        # Decisão sobre continuidade
        st.markdown("##### ⚖️ Decisão sobre Continuidade")
        
        results['recommendation'] = st.selectbox(
            "Recomendação:",
            ["Implementar em larga escala", "Implementar com modificações", "Fazer novo piloto", "Não implementar"],
            index=0 if not results.get('recommendation') else 
                  ["Implementar em larga escala", "Implementar com modificações", "Fazer novo piloto", "Não implementar"].index(results['recommendation']),
            key=f"recommendation_{self.project_id}"
        )
        
        results['justification'] = st.text_area(
            "Justificativa da Recomendação:",
            value=results.get('justification', ''),
            key=f"justification_{self.project_id}",
            placeholder="Explique a razão da recomendação...",
            height=80
        )
        
        # Modificações necessárias (se aplicável)
        if results.get('recommendation') in ["Implementar com modificações", "Fazer novo piloto"]:
            results['modifications'] = st.text_area(
                "Modificações Necessárias:",
                value=results.get('modifications', ''),
                key=f"modifications_{self.project_id}",
                placeholder="Quais modificações são necessárias?",
                height=80
            )
    
    def _show_lessons_learned(self, pilot_data: Dict):
        """Lições aprendidas do piloto"""
        st.markdown("#### 🎓 Lições Aprendidas")
        
        if 'lessons_learned' not in pilot_data:
            pilot_data['lessons_learned'] = []
        
        # Adicionar nova lição
        with st.expander("➕ Adicionar Lição Aprendida"):
            col1, col2 = st.columns(2)
            
            with col1:
                lesson_category = st.selectbox(
                    "Categoria:",
                    ["Processo", "Pessoas", "Tecnologia", "Comunicação", "Planejamento", "Execução", "Medição"],
                    key=f"lesson_category_{self.project_id}"
                )
                
                lesson_type = st.selectbox(
                    "Tipo:",
                    ["O que funcionou bem", "O que não funcionou", "O que faria diferente", "Recomendação"],
                    key=f"lesson_type_{self.project_id}"
                )
            
            with col2:
                lesson_impact = st.selectbox(
                    "Impacto:",
                    ["Baixo", "Médio", "Alto"],
                    index=1,
                    key=f"lesson_impact_{self.project_id}"
                )
                
                lesson_author = st.text_input(
                    "Autor:",
                    key=f"lesson_author_{self.project_id}",
                    placeholder="Quem identificou esta lição?"
                )
            
            lesson_description = st.text_area(
                "Descrição da Lição:",
                key=f"lesson_description_{self.project_id}",
                placeholder="Descreva a lição aprendida em detalhes...",
                height=100
            )
            
            lesson_action = st.text_area(
                "Ação Recomendada:",
                key=f"lesson_action_{self.project_id}",
                placeholder="Que ação deve ser tomada baseada nesta lição?",
                height=60
            )
            
            if st.button("🎓 Adicionar Lição", key=f"add_lesson_{self.project_id}"):
                if lesson_description.strip():
                    pilot_data['lessons_learned'].append({
                        'category': lesson_category,
                        'type': lesson_type,
                        'impact': lesson_impact,
                        'author': lesson_author,
                        'description': lesson_description,
                        'action': lesson_action,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success("✅ Lição aprendida adicionada!")
                    st.rerun()
                else:
                    st.error("❌ Descrição é obrigatória")
        
        # Mostrar lições existentes
        if pilot_data['lessons_learned']:
            st.markdown("##### 📚 Biblioteca de Lições Aprendidas")
            
            # Filtros
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                category_filter = st.selectbox(
                    "Filtrar por Categoria:",
                    ["Todas"] + list(set([lesson['category'] for lesson in pilot_data['lessons_learned']])),
                    key=f"category_filter_{self.project_id}"
                )
            
            with col_f2:
                type_filter = st.selectbox(
                    "Filtrar por Tipo:",
                    ["Todos"] + list(set([lesson['type'] for lesson in pilot_data['lessons_learned']])),
                    key=f"type_filter_{self.project_id}"
                )
            
            with col_f3:
                impact_filter = st.selectbox(
                    "Filtrar por Impacto:",
                    ["Todos", "Alto", "Médio", "Baixo"],
                    key=f"impact_filter_{self.project_id}"
                )
            
            # Aplicar filtros
            filtered_lessons = pilot_data['lessons_learned']
            
            if category_filter != "Todas":
                filtered_lessons = [l for l in filtered_lessons if l['category'] == category_filter]
            
            if type_filter != "Todos":
                filtered_lessons = [l for l in filtered_lessons if l['type'] == type_filter]
            
            if impact_filter != "Todos":
                filtered_lessons = [l for l in filtered_lessons if l['impact'] == impact_filter]
            
            # Mostrar lições filtradas
            for i, lesson in enumerate(filtered_lessons):
                original_index = pilot_data['lessons_learned'].index(lesson)
                
                # Ícones por tipo
                type_icons = {
                    "O que funcionou bem": "✅",
                    "O que não funcionou": "❌",
                    "O que faria diferente": "🔄",
                    "Recomendação": "💡"
                }
                
                # Cores por impacto
                impact_colors = {
                    "Alto": "🔴",
                    "Médio": "🟡",
                    "Baixo": "🟢"
                }
                
                type_icon = type_icons.get(lesson['type'], "📝")
                impact_icon = impact_colors.get(lesson['impact'], "🟡")
                
                with st.expander(f"{type_icon} {impact_icon} **{lesson['category']}** - {lesson['type']}"):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**Descrição:** {lesson['description']}")
                        if lesson.get('action'):
                            st.write(f"**Ação Recomendada:** {lesson['action']}")
                    
                    with col2:
                        st.write(f"**Categoria:** {lesson['category']}")
                        st.write(f"**Impacto:** {lesson['impact']}")
                        if lesson.get('author'):
                            st.write(f"**Autor:** {lesson['author']}")
                        st.write(f"**Data:** {lesson['created_at'][:10]}")
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_lesson_{original_index}_{self.project_id}"):
                            pilot_data['lessons_learned'].pop(original_index)
                            st.rerun()
            
            # Estatísticas das lições
            if pilot_data['lessons_learned']:
                st.markdown("##### 📊 Estatísticas das Lições")
                
                # Distribuição por categoria
                category_count = {}
                for lesson in pilot_data['lessons_learned']:
                    cat = lesson['category']
                    category_count[cat] = category_count.get(cat, 0) + 1
                
                # Distribuição por tipo
                type_count = {}
                for lesson in pilot_data['lessons_learned']:
                    typ = lesson['type']
                    type_count[typ] = type_count.get(typ, 0) + 1
                
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    if len(category_count) > 1:
                        fig1 = px.pie(
                            values=list(category_count.values()),
                            names=list(category_count.keys()),
                            title="Lições por Categoria"
                        )
                        st.plotly_chart(fig1, use_container_width=True)
                
                with col_chart2:
                    if len(type_count) > 1:
                        fig2 = px.bar(
                            x=list(type_count.keys()),
                            y=list(type_count.values()),
                            title="Lições por Tipo"
                        )
                        fig2.update_xaxes(tickangle=45)
                        st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("🎓 Nenhuma lição aprendida registrada ainda. Documente os aprendizados do piloto.")
    
    def _show_action_buttons(self, pilot_data: Dict):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Piloto", key=f"save_{self.tool_name}_{self.project_id}"):
                success = self.manager.save_tool_data(self.tool_name, pilot_data, completed=False)
                if success:
                    st.success("💾 Piloto salvo!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("✅ Finalizar Piloto", key=f"complete_{self.tool_name}_{self.project_id}"):
                if self._validate_pilot(pilot_data):
                    success = self.manager.save_tool_data(self.tool_name, pilot_data, completed=True)
                    if success:
                        st.success("✅ Implementação piloto finalizada!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao finalizar")
                else:
                    st.error("❌ Complete os requisitos mínimos")
    
    def _validate_pilot(self, pilot_data: Dict) -> bool:
        """Valida se o piloto está completo"""
        # Verificar escopo definido
        scope = pilot_data.get('pilot_scope', {})
        if not scope.get('area') or not scope.get('success_criteria'):
            st.error("❌ Defina área e critérios de sucesso do piloto")
            return False
        
        # Verificar se há medições
        if not pilot_data.get('measurements'):
            st.error("❌ Adicione pelo menos uma métrica de acompanhamento")
            return False
        
        # Verificar se há resultados
        results = pilot_data.get('results', {})
        if not results.get('executive_summary') or not results.get('recommendation'):
            st.error("❌ Complete o resumo executivo e recomendação")
            return False
        
        return True


class FullScaleImplementationTool:
    """Ferramenta para Implementação em Larga Escala"""
    
    def __init__(self, manager: ImprovePhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "full_implementation"
    
    def show(self):
        """Interface principal da ferramenta"""
        st.markdown("## 🚀 Implementação em Larga Escala")
        st.markdown("Implemente as soluções validadas no piloto em toda a organização.")
        
        # Status da ferramenta
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ **Implementação em larga escala finalizada**")
        else:
            st.info("⏳ **Implementação em progresso**")
        
        # Verificar se piloto foi concluído
        pilot_data = self.manager.get_tool_data('pilot_implementation')
        if not pilot_data.get('results', {}).get('recommendation'):
            st.warning("⚠️ **Piloto não concluído**")
            st.info("💡 Complete a 'Implementação Piloto' primeiro")
            return
        
        # Verificar recomendação do piloto
        recommendation = pilot_data['results']['recommendation']
        if recommendation not in ["Implementar em larga escala", "Implementar com modificações"]:
            st.error(f"❌ **Recomendação do piloto:** {recommendation}")
            st.info("💡 A recomendação do piloto não suporta implementação em larga escala")
            return
        
        # Inicializar dados da sessão
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data if existing_data else {
                'rollout_plan': {},
                'training_plan': {},
                'communication_plan': {},
                'implementation_phases': [],
                'monitoring_system': {},
                'change_management': {}
            }
        
        implementation_data = st.session_state[session_key]
        
        # Mostrar recomendação do piloto
        self._show_pilot_recommendation(pilot_data)
        
        # Interface principal
        self._show_implementation_tabs(implementation_data, pilot_data)
        
        # Botões de ação
        self._show_action_buttons(implementation_data)
    
    def _show_pilot_recommendation(self, pilot_data: Dict):
        """Mostra recomendação do piloto"""
        st.markdown("### 🧪 Resultados do Piloto")
        
        results = pilot_data.get('results', {})
        recommendation = results.get('recommendation', 'N/A')
        
        col1, col2 = st.columns(2)
        
        with col1:
            if recommendation == "Implementar em larga escala":
                st.success(f"✅ **Recomendação:** {recommendation}")
            else:
                st.warning(f"⚠️ **Recomendação:** {recommendation}")
        
        with col2:
            # Métricas do piloto
            if pilot_data.get('measurements'):
                metrics_with_data = [m for m in pilot_data['measurements'] if m.get('data_points')]
                targets_achieved = 0
                
                for metric in metrics_with_data:
                    if metric.get('data_points'):
                        values = [dp['value'] for dp in metric['data_points']]
                        current_avg = sum(values) / len(values)
                        target = metric.get('target', 0)
                        baseline = metric.get('baseline', 0)
                        
                        if target != 0:
                            if target > baseline:
                                if current_avg >= target:
                                    targets_achieved += 1
                            else:
                                if current_avg <= target:
                                    targets_achieved += 1
                
                if metrics_with_data:
                    success_rate = (targets_achieved / len(metrics_with_data)) * 100
                    st.metric("Taxa de Sucesso do Piloto", f"{success_rate:.1f}%")
        
        # Justificativa
        if results.get('justification'):
            st.info(f"**Justificativa:** {results['justification']}")
        
        # Modificações necessárias
        if results.get('modifications'):
            st.warning(f"**Modificações Necessárias:** {results['modifications']}")
    
    def _show_implementation_tabs(self, implementation_data: Dict, pilot_data: Dict):
        """Mostra abas da implementação"""
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🗺️ Plano de Rollout",
            "🎓 Treinamento",
            "📢 Comunicação",
            "📊 Monitoramento",
            "🔄 Gestão da Mudança",
            "📈 Progresso"
        ])
        
        with tab1:
            self._show_rollout_plan(implementation_data, pilot_data)
        
        with tab2:
            self._show_training_plan(implementation_data)
        
        with tab3:
            self._show_communication_plan(implementation_data)
        
        with tab4:
            self._show_monitoring_system(implementation_data)
        
        with tab5:
            self._show_change_management(implementation_data)
        
        with tab6:
            self._show_progress_tracking(implementation_data)
    
    def _show_rollout_plan(self, implementation_data: Dict, pilot_data: Dict):
        """Plano de rollout"""
        st.markdown("#### 🗺️ Plano de Rollout")
        
        if 'rollout_plan' not in implementation_data:
            implementation_data['rollout_plan'] = {}
        
        rollout = implementation_data['rollout_plan']
        
        # Estratégia de rollout
        st.markdown("##### 📋 Estratégia de Rollout")
        
        col1, col2 = st.columns(2)
        
        with col1:
            rollout['strategy'] = st.selectbox(
                "Estratégia de Implementação:",
                ["Big Bang (Tudo de uma vez)", "Faseada por Área", "Faseada por Processo", "Piloto Expandido"],
                index=1 if not rollout.get('strategy') else 
                      ["Big Bang (Tudo de uma vez)", "Faseada por Área", "Faseada por Processo", "Piloto Expandido"].index(rollout['strategy']),
                key=f"rollout_strategy_{self.project_id}"
            )
            
            rollout['duration'] = st.number_input(
                "Duração Total (semanas):",
                min_value=1,
                max_value=104,
                value=rollout.get('duration', 12),
                key=f"rollout_duration_{self.project_id}"
            )
        
        with col2:
            rollout['priority_criteria'] = st.text_area(
                "Critérios de Priorização:",
                value=rollout.get('priority_criteria', ''),
                key=f"priority_criteria_{self.project_id}",
                placeholder="Como será definida a ordem de implementação?",
                height=80
            )
        
        # Definir fases de implementação
        st.markdown("##### 📅 Fases de Implementação")
        
        if 'implementation_phases' not in implementation_data:
            implementation_data['implementation_phases'] = []
        
        phases = implementation_data['implementation_phases']
        
        # Adicionar nova fase
        with st.expander("➕ Adicionar Fase"):
            col1, col2 = st.columns(2)
            
            with col1:
                phase_name = st.text_input(
                    "Nome da Fase:",
                    key=f"phase_name_{self.project_id}",
                    placeholder="Ex: Fase 1 - Produção, Fase 2 - Administrativo"
                )
                
                phase_areas = st.text_area(
                    "Áreas/Setores:",
                    key=f"phase_areas_{self.project_id}",
                    placeholder="Liste as áreas incluídas nesta fase...",
                    height=60
                )
                
                phase_duration = st.number_input(
                    "Duração (semanas):",
                    min_value=1,
                    max_value=52,
                    value=4,
                    key=f"phase_duration_{self.project_id}"
                )
            
            with col2:
                phase_start = st.date_input(
                    "Data de Início:",
                    key=f"phase_start_{self.project_id}"
                )
                
                phase_responsible = st.text_input(
                    "Responsável:",
                    key=f"phase_responsible_{self.project_id}",
                    placeholder="Nome do responsável pela fase"
                )
                
                phase_budget = st.number_input(
                    "Orçamento (R$):",
                    min_value=0.0,
                    key=f"phase_budget_{self.project_id}"
                )
            
            phase_description = st.text_area(
                "Descrição/Objetivos:",
                key=f"phase_description_{self.project_id}",
                placeholder="Descreva os objetivos e atividades desta fase...",
                height=80
            )
            
            if st.button("📅 Adicionar Fase", key=f"add_phase_{self.project_id}"):
                if phase_name.strip():
                    phases.append({
                        'name': phase_name,
                        'areas': phase_areas,
                        'duration': phase_duration,
                        'start_date': phase_start.isoformat(),
                        'end_date': (phase_start + timedelta(weeks=phase_duration)).isoformat(),
                        'responsible': phase_responsible,
                        'budget': phase_budget,
                        'description': phase_description,
                        'status': 'Planejada',
                        'progress': 0,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Fase '{phase_name}' adicionada!")
                    st.rerun()
                else:
                    st.error("❌ Nome da fase é obrigatório")
        
        # Mostrar fases existentes
        if phases:
            st.markdown("##### 📊 Fases Planejadas")
            
            total_budget = sum(phase.get('budget', 0) for phase in phases)
            total_duration = sum(phase.get('duration', 0) for phase in phases)
            
            col_summary1, col_summary2, col_summary3 = st.columns(3)
            
            with col_summary1:
                st.metric("Total de Fases", len(phases))
            
            with col_summary2:
                st.metric("Orçamento Total", f"R$ {total_budget:,.2f}")
            
            with col_summary3:
                st.metric("Duração Total", f"{total_duration} semanas")
            
            # Lista das fases
            for i, phase in enumerate(phases):
                with st.expander(f"**{phase['name']}** - {phase['status']} ({phase['duration']} semanas)"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Áreas:** {phase.get('areas', 'N/A')}")
                        st.write(f"**Descrição:** {phase.get('description', 'N/A')}")
                        st.write(f"**Responsável:** {phase.get('responsible', 'Não atribuído')}")
                    
                    with col2:
                        st.write(f"**Início:** {datetime.fromisoformat(phase['start_date']).strftime('%d/%m/%Y')}")
                        st.write(f"**Fim:** {datetime.fromisoformat(phase['end_date']).strftime('%d/%m/%Y')}")
                        st.write(f"**Orçamento:** R$ {phase.get('budget', 0):,.2f}")
                        
                        # Status e progresso
                        new_status = st.selectbox(
                            "Status:",
                            ["Planejada", "Em Execução", "Concluída", "Pausada"],
                            index=["Planejada", "Em Execução", "Concluída", "Pausada"].index(phase.get('status', 'Planejada')),
                            key=f"phase_status_{i}_{self.project_id}"
                        )
                        
                        phases[i]['status'] = new_status
                        
                        progress = st.slider(
                            "Progresso:",
                            0, 100, phase.get('progress', 0),
                            key=f"phase_progress_{i}_{self.project_id}",
                            format="%d%%"
                        )
                        
                        phases[i]['progress'] = progress
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_phase_{i}_{self.project_id}"):
                            phases.pop(i)
                            st.rerun()
            
            # Cronograma visual
            if len(phases) > 1:
                st.markdown("##### 📊 Cronograma das Fases")
                
                fig = go.Figure()
                
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
                
                for i, phase in enumerate(phases):
                    start_date = datetime.fromisoformat(phase['start_date'])
                    end_date = datetime.fromisoformat(phase['end_date'])
                    duration = (end_date - start_date).days
                    
                    fig.add_trace(go.Bar(
                        y=[phase['name']],
                        x=[duration],
                        base=[start_date],
                        orientation='h',
                        name=phase['name'],
                        marker_color=colors[i % len(colors)],
                        text=f"{phase['progress']}%",
                        textposition='inside'
                    ))
                
                fig.update_layout(
                    title="Cronograma das Fases de Implementação",
                    xaxis_title="Data",
                    yaxis_title="Fases",
                    height=max(300, len(phases) * 50),
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def _show_training_plan(self, implementation_data: Dict):
        """Plano de treinamento"""
        st.markdown("#### 🎓 Plano de Treinamento")
        
        if 'training_plan' not in implementation_data:
            implementation_data['training_plan'] = {}
        
        training = implementation_data['training_plan']
        
        # Estratégia de treinamento
        st.markdown("##### 📚 Estratégia de Treinamento")
        
        col1, col2 = st.columns(2)
        
        with col1:
            training['approach'] = st.selectbox(
                "Abordagem de Treinamento:",
                ["Cascata", "Train-the-Trainer", "Treinamento Direto", "E-learning", "Híbrido"],
                index=0 if not training.get('approach') else 
                      ["Cascata", "Train-the-Trainer", "Treinamento Direto", "E-learning", "Híbrido"].index(training['approach']),
                key=f"training_approach_{self.project_id}"
            )
            
            training['duration_per_person'] = st.number_input(
                "Duração por Pessoa (horas):",
                min_value=0.5,
                max_value=80.0,
                value=training.get('duration_per_person', 8.0),
                step=0.5,
                key=f"training_duration_{self.project_id}"
            )
        
        with col2:
            training['target_audience'] = st.text_area(
                "Público-Alvo:",
                value=training.get('target_audience', ''),
                key=f"training_audience_{self.project_id}",
                placeholder="Descreva quem será treinado...",
                height=80
            )
        
        # Módulos de treinamento
        st.markdown("##### 📖 Módulos de Treinamento")
        
        if 'modules' not in training:
            training['modules'] = []
        
        modules = training['modules']
        
        # Adicionar módulo
        with st.expander("➕ Adicionar Módulo"):
            col1, col2 = st.columns(2)
            
            with col1:
                module_name = st.text_input(
                    "Nome do Módulo:",
                    key=f"module_name_{self.project_id}",
                    placeholder="Ex: Introdução ao Novo Processo"
                )
                
                module_duration = st.number_input(
                    "Duração (horas):",
                    min_value=0.5,
                    max_value=16.0,
                    value=2.0,
                    step=0.5,
                    key=f"module_duration_{self.project_id}"
                )
                
                module_method = st.selectbox(
                    "Método:",
                    ["Presencial", "Online", "Hands-on", "Mentoring", "Job Rotation"],
                    key=f"module_method_{self.project_id}"
                )
            
            with col2:
                module_trainer = st.text_input(
                    "Instrutor:",
                    key=f"module_trainer_{self.project_id}",
                    placeholder="Nome do instrutor"
                )
                
                module_materials = st.text_area(
                    "Materiais Necessários:",
                    key=f"module_materials_{self.project_id}",
                    placeholder="Liste os materiais necessários...",
                    height=60
                )
            
            module_objectives = st.text_area(
                "Objetivos de Aprendizagem:",
                key=f"module_objectives_{self.project_id}",
                placeholder="O que os participantes devem aprender?",
                height=80
            )
            
            if st.button("📖 Adicionar Módulo", key=f"add_module_{self.project_id}"):
                if module_name.strip():
                    modules.append({
                        'name': module_name,
                        'duration': module_duration,
                        'method': module_method,
                        'trainer': module_trainer,
                        'materials': module_materials,
                        'objectives': module_objectives,
                        'status': 'Planejado',
                        'participants_trained': 0,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Módulo '{module_name}' adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Nome do módulo é obrigatório")
        
        # Mostrar módulos existentes
        if modules:
            st.markdown("##### 📊 Módulos Planejados")
            
            for i, module in enumerate(modules):
                with st.expander(f"📖 **{module['name']}** ({module['duration']}h - {module['method']})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Objetivos:** {module.get('objectives', 'N/A')}")
                        st.write(f"**Instrutor:** {module.get('trainer', 'Não definido')}")
                        if module.get('materials'):
                            st.write(f"**Materiais:** {module['materials']}")
                    
                    with col2:
                        new_status = st.selectbox(
                            "Status:",
                            ["Planejado", "Em Desenvolvimento", "Pronto", "Em Execução", "Concluído"],
                            index=["Planejado", "Em Desenvolvimento", "Pronto", "Em Execução", "Concluído"].index(module.get('status', 'Planejado')),
                            key=f"module_status_{i}_{self.project_id}"
                        )
                        
                        modules[i]['status'] = new_status
                        
                        participants = st.number_input(
                            "Participantes Treinados:",
                            min_value=0,
                            value=module.get('participants_trained', 0),
                            key=f"module_participants_{i}_{self.project_id}"
                        )
                        
                        modules[i]['participants_trained'] = participants
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_module_{i}_{self.project_id}"):
                            modules.pop(i)
                            st.rerun()
            
            # Estatísticas de treinamento
            total_duration = sum(module['duration'] for module in modules)
            total_participants = sum(module.get('participants_trained', 0) for module in modules)
            completed_modules = len([m for m in modules if m.get('status') == 'Concluído'])
            
            col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
            
            with col_stats1:
                st.metric("Total de Módulos", len(modules))
            
            with col_stats2:
                st.metric("Duração Total", f"{total_duration}h")
            
            with col_stats3:
                st.metric("Pessoas Treinadas", total_participants)
            
            with col_stats4:
                st.metric("Módulos Concluídos", completed_modules)
    
    def _show_communication_plan(self, implementation_data: Dict):
        """Plano de comunicação"""
        st.markdown("#### 📢 Plano de Comunicação")
        
        if 'communication_plan' not in implementation_data:
            implementation_data['communication_plan'] = {}
        
        comm = implementation_data['communication_plan']
        
        # Estratégia de comunicação
        st.markdown("##### 📣 Estratégia de Comunicação")
        
        comm['key_messages'] = st.text_area(
            "Mensagens-Chave:",
            value=comm.get('key_messages', ''),
            key=f"key_messages_{self.project_id}",
            placeholder="Quais são as principais mensagens a serem comunicadas?",
            height=100
        )
        
        # Stakeholders
        st.markdown("##### 👥 Mapa de Stakeholders")
        
        if 'stakeholders' not in comm:
            comm['stakeholders'] = []
        
        stakeholders = comm['stakeholders']
        
        # Adicionar stakeholder
        with st.expander("➕ Adicionar Stakeholder"):
            col1, col2 = st.columns(2)
            
            with col1:
                stakeholder_name = st.text_input(
                    "Nome/Grupo:",
                    key=f"stakeholder_name_{self.project_id}",
                    placeholder="Ex: Diretoria, Operadores, Clientes"
                )
                
                stakeholder_influence = st.selectbox(
                    "Influência:",
                    ["Baixa", "Média", "Alta"],
                    index=1,
                    key=f"stakeholder_influence_{self.project_id}"
                )
                
                stakeholder_interest = st.selectbox(
                    "Interesse:",
                    ["Baixo", "Médio", "Alto"],
                    index=1,
                    key=f"stakeholder_interest_{self.project_id}"
                )
            
            with col2:
                stakeholder_attitude = st.selectbox(
                    "Atitude:",
                    ["Resistente", "Neutro", "Favorável", "Defensor"],
                    index=1,
                    key=f"stakeholder_attitude_{self.project_id}"
                )
                
                stakeholder_channel = st.multiselect(
                    "Canais de Comunicação:",
                    ["E-mail", "Reunião", "Intranet", "Murais", "WhatsApp", "Apresentação", "Treinamento"],
                    key=f"stakeholder_channel_{self.project_id}"
                )
            
            stakeholder_message = st.text_area(
                "Mensagem Específica:",
                key=f"stakeholder_message_{self.project_id}",
                placeholder="Qual mensagem específica para este stakeholder?",
                height=60
            )
            
            if st.button("👥 Adicionar Stakeholder", key=f"add_stakeholder_{self.project_id}"):
                if stakeholder_name.strip():
                    stakeholders.append({
                        'name': stakeholder_name,
                        'influence': stakeholder_influence,
                        'interest': stakeholder_interest,
                        'attitude': stakeholder_attitude,
                        'channels': stakeholder_channel,
                        'message': stakeholder_message,
                        'last_contact': None,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Stakeholder '{stakeholder_name}' adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Nome do stakeholder é obrigatório")
        
        # Mostrar stakeholders
        if stakeholders:
            st.markdown("##### 📊 Matriz de Stakeholders")
            
            # Criar matriz de influência x interesse
            stakeholder_data = []
            
            for stakeholder in stakeholders:
                influence_map = {"Baixa": 1, "Média": 2, "Alta": 3}
                interest_map = {"Baixo": 1, "Médio": 2, "Alto": 3}
                
                stakeholder_data.append({
                    'Nome': stakeholder['name'],
                    'Influência': influence_map[stakeholder['influence']],
                    'Interesse': interest_map[stakeholder['interest']],
                    'Atitude': stakeholder['attitude'],
                    'Canais': ', '.join(stakeholder.get('channels', []))
                })
            
            if stakeholder_data:
                df = pd.DataFrame(stakeholder_data)
                
                fig = px.scatter(
                    df, x='Interesse', y='Influência', 
                    color='Atitude',
                    size=[1] * len(df),  # Tamanho uniforme
                    hover_name='Nome',
                    hover_data=['Canais'],
                    title="Matriz de Stakeholders (Influência x Interesse)"
                )
                
                fig.update_xaxes(range=[0.5, 3.5], tickvals=[1, 2, 3], ticktext=['Baixo', 'Médio', 'Alto'])
                fig.update_yaxes(range=[0.5, 3.5], tickvals=[1, 2, 3], ticktext=['Baixa', 'Média', 'Alta'])
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Lista detalhada
            for i, stakeholder in enumerate(stakeholders):
                with st.expander(f"👥 **{stakeholder['name']}** - {stakeholder['attitude']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Influência:** {stakeholder['influence']}")
                        st.write(f"**Interesse:** {stakeholder['interest']}")
                        st.write(f"**Atitude:** {stakeholder['attitude']}")
                        if stakeholder.get('message'):
                            st.write(f"**Mensagem:** {stakeholder['message']}")
                    
                    with col2:
                        if stakeholder.get('channels'):
                            st.write(f"**Canais:** {', '.join(stakeholder['channels'])}")
                        
                        # Registrar contato
                        if st.button("📞 Registrar Contato", key=f"contact_{i}_{self.project_id}"):
                            stakeholders[i]['last_contact'] = datetime.now().isoformat()
                            st.success("✅ Contato registrado!")
                            st.rerun()
                        
                        if stakeholder.get('last_contact'):
                            last_contact = datetime.fromisoformat(stakeholder['last_contact'])
                            st.write(f"**Último Contato:** {last_contact.strftime('%d/%m/%Y %H:%M')}")
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_stakeholder_{i}_{self.project_id}"):
                            stakeholders.pop(i)
                            st.rerun()
        
        # Cronograma de comunicação
        st.markdown("##### 📅 Cronograma de Comunicação")
        
        if 'communication_schedule' not in comm:
            comm['communication_schedule'] = []
        
        schedule = comm['communication_schedule']
        
        # Adicionar evento de comunicação
        with st.expander("➕ Adicionar Evento de Comunicação"):
            col1, col2 = st.columns(2)
            
            with col1:
                event_title = st.text_input(
                    "Título do Evento:",
                    key=f"event_title_{self.project_id}",
                    placeholder="Ex: Kick-off da Implementação"
                )
                
                event_date = st.date_input(
                    "Data:",
                    key=f"event_date_{self.project_id}"
                )
                
                event_audience = st.multiselect(
                    "Público:",
                    [s['name'] for s in stakeholders] if stakeholders else [],
                    key=f"event_audience_{self.project_id}"
                )
            
            with col2:
                event_channel = st.selectbox(
                    "Canal:",
                    ["Reunião", "E-mail", "Apresentação", "Intranet", "Mural", "WhatsApp", "Newsletter"],
                    key=f"event_channel_{self.project_id}"
                )
                
                event_responsible = st.text_input(
                    "Responsável:",
                    key=f"event_responsible_{self.project_id}"
                )
            
            event_content = st.text_area(
                "Conteúdo/Mensagem:",
                key=f"event_content_{self.project_id}",
                placeholder="Que informação será comunicada?",
                height=80
            )
            
            if st.button("📅 Adicionar Evento", key=f"add_event_{self.project_id}"):
                if event_title.strip():
                    schedule.append({
                        'title': event_title,
                        'date': event_date.isoformat(),
                        'audience': event_audience,
                        'channel': event_channel,
                        'responsible': event_responsible,
                        'content': event_content,
                        'status': 'Planejado',
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Evento '{event_title}' adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Título do evento é obrigatório")
        
        # Mostrar cronograma
        if schedule:
            st.markdown("##### 📊 Eventos de Comunicação")
            
            # Ordenar por data
            sorted_schedule = sorted(schedule, key=lambda x: x['date'])
            
            for i, event in enumerate(sorted_schedule):
                original_index = schedule.index(event)
                event_date = datetime.fromisoformat(event['date'])
                
                with st.expander(f"📅 **{event['title']}** - {event_date.strftime('%d/%m/%Y')} ({event['status']})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Canal:** {event['channel']}")
                        st.write(f"**Responsável:** {event.get('responsible', 'Não definido')}")
                        if event.get('audience'):
                            st.write(f"**Público:** {', '.join(event['audience'])}")
                        if event.get('content'):
                            st.write(f"**Conteúdo:** {event['content']}")
                    
                    with col2:
                        new_status = st.selectbox(
                            "Status:",
                            ["Planejado", "Em Preparação", "Executado", "Cancelado"],
                            index=["Planejado", "Em Preparação", "Executado", "Cancelado"].index(event.get('status', 'Planejado')),
                            key=f"event_status_{original_index}_{self.project_id}"
                        )
                        
                        schedule[original_index]['status'] = new_status
                        
                        # Verificar se está próximo
                        days_until = (event_date.date() - datetime.now().date()).days
                        
                        if days_until < 0:
                            st.error(f"⚠️ Atrasado ({abs(days_until)} dias)")
                        elif days_until == 0:
                            st.warning("🚨 Hoje")
                        elif days_until <= 7:
                            st.info(f"📅 Em {days_until} dias")
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_event_{original_index}_{self.project_id}"):
                            schedule.pop(original_index)
                            st.rerun()
    
    def _show_monitoring_system(self, implementation_data: Dict):
        """Sistema de monitoramento"""
        st.markdown("#### 📊 Sistema de Monitoramento")
        
        if 'monitoring_system' not in implementation_data:
            implementation_data['monitoring_system'] = {}
        
        monitoring = implementation_data['monitoring_system']
        
        # KPIs de implementação
        st.markdown("##### 📈 KPIs de Implementação")
        
        if 'kpis' not in monitoring:
            monitoring['kpis'] = []
        
        kpis = monitoring['kpis']
        
        # Adicionar KPI
        with st.expander("➕ Adicionar KPI"):
            col1, col2 = st.columns(2)
            
            with col1:
                kpi_name = st.text_input(
                    "Nome do KPI:",
                    key=f"kpi_name_{self.project_id}",
                    placeholder="Ex: % de Áreas Implementadas"
                )
                
                kpi_unit = st.text_input(
                    "Unidade:",
                    key=f"kpi_unit_{self.project_id}",
                    placeholder="Ex: %, unidades, dias"
                )
                
                kpi_target = st.number_input(
                    "Meta:",
                    key=f"kpi_target_{self.project_id}"
                )
            
            with col2:
                kpi_frequency = st.selectbox(
                    "Frequência de Medição:",
                    ["Diária", "Semanal", "Quinzenal", "Mensal"],
                    key=f"kpi_frequency_{self.project_id}"
                )
                
                kpi_responsible = st.text_input(
                    "Responsável:",
                    key=f"kpi_responsible_{self.project_id}"
                )
                
                kpi_threshold = st.number_input(
                    "Limite de Alerta:",
                    key=f"kpi_threshold_{self.project_id}",
                    help="Valor abaixo do qual será gerado alerta"
                )
            
            kpi_description = st.text_area(
                "Descrição/Fórmula:",
                key=f"kpi_description_{self.project_id}",
                placeholder="Como este KPI é calculado?",
                height=60
            )
            
            if st.button("📈 Adicionar KPI", key=f"add_kpi_{self.project_id}"):
                if kpi_name.strip():
                    kpis.append({
                        'name': kpi_name,
                        'unit': kpi_unit,
                        'target': kpi_target,
                        'frequency': kpi_frequency,
                        'responsible': kpi_responsible,
                        'threshold': kpi_threshold,
                        'description': kpi_description,
                        'measurements': [],
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ KPI '{kpi_name}' adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Nome do KPI é obrigatório")
        
        # Mostrar KPIs
        if kpis:
            st.markdown("##### 📊 Dashboard de KPIs")
            
            for i, kpi in enumerate(kpis):
                with st.expander(f"📈 **{kpi['name']}** (Meta: {kpi.get('target', 0)} {kpi.get('unit', '')})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Descrição:** {kpi.get('description', 'N/A')}")
                        st.write(f"**Frequência:** {kpi.get('frequency', 'N/A')}")
                        st.write(f"**Responsável:** {kpi.get('responsible', 'Não definido')}")
                        st.write(f"**Limite de Alerta:** {kpi.get('threshold', 0)} {kpi.get('unit', '')}")
                    
                    with col2:
                        # Adicionar medição
                        st.markdown("**Nova Medição:**")
                        
                        measurement_date = st.date_input(
                            "Data:",
                            key=f"measurement_date_{i}_{self.project_id}"
                        )
                        
                        measurement_value = st.number_input(
                            "Valor:",
                            key=f"measurement_value_{i}_{self.project_id}"
                        )
                        
                        if st.button("➕ Adicionar", key=f"add_measurement_{i}_{self.project_id}"):
                            kpis[i]['measurements'].append({
                                'date': measurement_date.isoformat(),
                                'value': measurement_value,
                                'added_at': datetime.now().isoformat()
                            })
                            
                            st.success("✅ Medição adicionada!")
                            st.rerun()
                        
                        # Mostrar últimas medições
                        measurements = kpi.get('measurements', [])
                        if measurements:
                            st.write("**Últimas medições:**")
                            for measurement in measurements[-3:]:
                                st.write(f"• {measurement['date']}: {measurement['value']} {kpi.get('unit', '')}")
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_kpi_{i}_{self.project_id}"):
                            kpis.pop(i)
                            st.rerun()
                        
                        # Status do KPI
                        measurements = kpi.get('measurements', [])
                        if measurements:
                            current_value = measurements[-1]['value']
                            target = kpi.get('target', 0)
                            threshold = kpi.get('threshold', 0)
                            
                            st.metric("Valor Atual", f"{current_value} {kpi.get('unit', '')}")
                            
                            # Status baseado no valor
                            if current_value >= target:
                                st.success("🎯 Meta atingida")
                            elif current_value <= threshold:
                                st.error("⚠️ Abaixo do limite")
                            else:
                                st.warning("📊 Em progresso")
            
            # Gráfico consolidado dos KPIs
            if len(kpis) > 0:
                kpis_with_data = [kpi for kpi in kpis if kpi.get('measurements')]
                
                if kpis_with_data:
                    st.markdown("##### 📊 Evolução dos KPIs")
                    
                    fig = make_subplots(
                        rows=min(2, len(kpis_with_data)),
                        cols=2 if len(kpis_with_data) > 1 else 1,
                        subplot_titles=[kpi['name'] for kpi in kpis_with_data[:4]]
                    )
                    
                    for i, kpi in enumerate(kpis_with_data[:4]):
                        row = i // 2 + 1
                        col = i % 2 + 1
                        
                        measurements = kpi['measurements']
                        dates = [m['date'] for m in measurements]
                        values = [m['value'] for m in measurements]
                        
                        fig.add_trace(
                            go.Scatter(
                                x=dates,
                                y=values,
                                mode='lines+markers',
                                name=kpi['name'],
                                showlegend=False
                            ),
                            row=row, col=col
                        )
                        
                        # Linha de meta
                        if kpi.get('target'):
                            fig.add_hline(
                                y=kpi['target'],
                                line_dash="dash",
                                line_color="green",
                                row=row, col=col
                            )
                        
                        # Linha de alerta
                        if kpi.get('threshold'):
                            fig.add_hline(
                                y=kpi['threshold'],
                                line_dash="dash",
                                line_color="red",
                                row=row, col=col
                            )
                    
                    fig.update_layout(
                        title="Dashboard de KPIs de Implementação",
                        height=400 * min(2, (len(kpis_with_data) + 1) // 2)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        # Sistema de alertas
        st.markdown("##### 🚨 Sistema de Alertas")
        
        monitoring['alert_rules'] = st.text_area(
            "Regras de Alerta:",
            value=monitoring.get('alert_rules', ''),
            key=f"alert_rules_{self.project_id}",
            placeholder="Defina quando e como os alertas devem ser disparados...",
            height=80
        )
        
        monitoring['escalation_process'] = st.text_area(
            "Processo de Escalação:",
            value=monitoring.get('escalation_process', ''),
            key=f"escalation_process_{self.project_id}",
            placeholder="Como os problemas devem ser escalados?",
            height=80
        )
    
    def _show_change_management(self, implementation_data: Dict):
        """Gestão da mudança"""
        st.markdown("#### 🔄 Gestão da Mudança")
        
        if 'change_management' not in implementation_data:
            implementation_data['change_management'] = {}
        
        change_mgmt = implementation_data['change_management']
        
        # Avaliação da prontidão para mudança
        st.markdown("##### 🎯 Avaliação da Prontidão para Mudança")
        
        col1, col2 = st.columns(2)
        
        with col1:
            change_mgmt['leadership_support'] = st.selectbox(
                "Apoio da Liderança:",
                ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"],
                index=2 if not change_mgmt.get('leadership_support') else 
                      ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"].index(change_mgmt['leadership_support']),
                key=f"leadership_support_{self.project_id}"
            )
            
            change_mgmt['employee_engagement'] = st.selectbox(
                "Engajamento dos Funcionários:",
                ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"],
                index=2 if not change_mgmt.get('employee_engagement') else 
                      ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"].index(change_mgmt['employee_engagement']),
                key=f"employee_engagement_{self.project_id}"
            )
            
            change_mgmt['resource_availability'] = st.selectbox(
                "Disponibilidade de Recursos:",
                ["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta"],
                index=2 if not change_mgmt.get('resource_availability') else 
                      ["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta"].index(change_mgmt['resource_availability']),
                key=f"resource_availability_{self.project_id}"
            )
        
        with col2:
            change_mgmt['change_capacity'] = st.selectbox(
                "Capacidade de Mudança:",
                ["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta"],
                index=2 if not change_mgmt.get('change_capacity') else 
                      ["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta"].index(change_mgmt['change_capacity']),
                key=f"change_capacity_{self.project_id}"
            )
            
            change_mgmt['communication_effectiveness'] = st.selectbox(
                "Eficácia da Comunicação:",
                ["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta"],
                index=2 if not change_mgmt.get('communication_effectiveness') else 
                      ["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta"].index(change_mgmt['communication_effectiveness']),
                key=f"communication_effectiveness_{self.project_id}"
            )
            
            change_mgmt['past_change_success'] = st.selectbox(
                "Sucesso em Mudanças Passadas:",
                ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"],
                index=2 if not change_mgmt.get('past_change_success') else 
                      ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"].index(change_mgmt['past_change_success']),
                key=f"past_change_success_{self.project_id}"
            )
        
        # Calcular score de prontidão
        readiness_factors = [
            change_mgmt.get('leadership_support', 'Médio'),
            change_mgmt.get('employee_engagement', 'Médio'),
            change_mgmt.get('resource_availability', 'Média'),
            change_mgmt.get('change_capacity', 'Média'),
            change_mgmt.get('communication_effectiveness', 'Média'),
            change_mgmt.get('past_change_success', 'Médio')
        ]
        
        score_map = {"Muito Baixo": 1, "Baixo": 2, "Médio": 3, "Alto": 4, "Muito Alto": 5,
                     "Muito Baixa": 1, "Baixa": 2, "Média": 3, "Alta": 4, "Muito Alta": 5}
        
        readiness_score = sum(score_map.get(factor, 3) for factor in readiness_factors) / len(readiness_factors)
        
        col_score1, col_score2 = st.columns(2)
        
        with col_score1:
            st.metric("Score de Prontidão", f"{readiness_score:.1f}/5")
        
        with col_score2:
            if readiness_score >= 4:
                st.success("🟢 Alta prontidão")
            elif readiness_score >= 3:
                st.warning("🟡 Prontidão moderada")
            else:
                st.error("🔴 Baixa prontidão")
        
        # Estratégias de gestão da mudança
        st.markdown("##### 🛠️ Estratégias de Gestão da Mudança")
        
        if 'strategies' not in change_mgmt:
            change_mgmt['strategies'] = []
        
        strategies = change_mgmt['strategies']
        
        # Adicionar estratégia
        with st.expander("➕ Adicionar Estratégia"):
            col1, col2 = st.columns(2)
            
            with col1:
                strategy_name = st.text_input(
                    "Nome da Estratégia:",
                    key=f"strategy_name_{self.project_id}",
                    placeholder="Ex: Programa de Embaixadores"
                )
                
                strategy_type = st.selectbox(
                    "Tipo:",
                    ["Comunicação", "Treinamento", "Incentivos", "Suporte", "Feedback", "Reconhecimento"],
                    key=f"strategy_type_{self.project_id}"
                )
                
                strategy_priority = st.selectbox(
                    "Prioridade:",
                    ["Baixa", "Média", "Alta"],
                    index=1,
                    key=f"strategy_priority_{self.project_id}"
                )
            
            with col2:
                strategy_target = st.text_input(
                    "Público-Alvo:",
                    key=f"strategy_target_{self.project_id}",
                    placeholder="A quem se destina esta estratégia?"
                )
                
                strategy_timeline = st.text_input(
                    "Prazo:",
                    key=f"strategy_timeline_{self.project_id}",
                    placeholder="Ex: 2 semanas, Durante toda implementação"
                )
                
                strategy_responsible = st.text_input(
                    "Responsável:",
                    key=f"strategy_responsible_{self.project_id}"
                )
            
            strategy_description = st.text_area(
                "Descrição:",
                key=f"strategy_description_{self.project_id}",
                placeholder="Descreva como esta estratégia será executada...",
                height=80
            )
            
            if st.button("🛠️ Adicionar Estratégia", key=f"add_strategy_{self.project_id}"):
                if strategy_name.strip():
                    strategies.append({
                        'name': strategy_name,
                        'type': strategy_type,
                        'priority': strategy_priority,
                        'target': strategy_target,
                        'timeline': strategy_timeline,
                        'responsible': strategy_responsible,
                        'description': strategy_description,
                        'status': 'Planejada',
                        'effectiveness': None,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Estratégia '{strategy_name}' adicionada!")
                    st.rerun()
                else:
                    st.error("❌ Nome da estratégia é obrigatório")
        
        # Mostrar estratégias
        if strategies:
            st.markdown("##### 📊 Estratégias Definidas")
            
            for i, strategy in enumerate(strategies):
                priority_icons = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}
                priority_icon = priority_icons.get(strategy['priority'], "🟡")
                
                with st.expander(f"{priority_icon} **{strategy['name']}** ({strategy['type']})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Descrição:** {strategy.get('description', 'N/A')}")
                        st.write(f"**Público-Alvo:** {strategy.get('target', 'N/A')}")
                        st.write(f"**Responsável:** {strategy.get('responsible', 'Não definido')}")
                        st.write(f"**Prazo:** {strategy.get('timeline', 'N/A')}")
                    
                    with col2:
                        new_status = st.selectbox(
                            "Status:",
                            ["Planejada", "Em Execução", "Executada", "Cancelada"],
                            index=["Planejada", "Em Execução", "Executada", "Cancelada"].index(strategy.get('status', 'Planejada')),
                            key=f"strategy_status_{i}_{self.project_id}"
                        )
                        
                        strategies[i]['status'] = new_status
                        
                        if new_status == "Executada":
                            effectiveness = st.selectbox(
                                "Eficácia:",
                                ["Baixa", "Média", "Alta"],
                                index=1 if not strategy.get('effectiveness') else 
                                      ["Baixa", "Média", "Alta"].index(strategy['effectiveness']),
                                key=f"strategy_effectiveness_{i}_{self.project_id}"
                            )
                            
                            strategies[i]['effectiveness'] = effectiveness
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_strategy_{i}_{self.project_id}"):
                            strategies.pop(i)
                            st.rerun()
        
        # Resistências identificadas
        st.markdown("##### ⚠️ Gestão de Resistências")
        
        if 'resistances' not in change_mgmt:
            change_mgmt['resistances'] = []
        
        resistances = change_mgmt['resistances']
        
        # Adicionar resistência
        with st.expander("➕ Identificar Resistência"):
            col1, col2 = st.columns(2)
            
            with col1:
                resistance_source = st.text_input(
                    "Fonte da Resistência:",
                    key=f"resistance_source_{self.project_id}",
                    placeholder="Quem ou que grupo está resistindo?"
                )
                
                resistance_type = st.selectbox(
                    "Tipo de Resistência:",
                    ["Falta de informação", "Medo de perder emprego", "Sobrecarga de trabalho", 
                     "Desconfiança", "Experiências passadas", "Falta de habilidades", "Cultura organizacional"],
                    key=f"resistance_type_{self.project_id}"
                )
                
                resistance_level = st.selectbox(
                    "Nível:",
                    ["Baixo", "Médio", "Alto"],
                    index=1,
                    key=f"resistance_level_{self.project_id}"
                )
            
            with col2:
                resistance_impact = st.selectbox(
                    "Impacto na Implementação:",
                    ["Baixo", "Médio", "Alto"],
                    index=1,
                    key=f"resistance_impact_{self.project_id}"
                )
                
                resistance_urgency = st.selectbox(
                    "Urgência de Ação:",
                    ["Baixa", "Média", "Alta"],
                    index=1,
                    key=f"resistance_urgency_{self.project_id}"
                )
            
            resistance_description = st.text_area(
                "Descrição da Resistência:",
                key=f"resistance_description_{self.project_id}",
                placeholder="Descreva a resistência observada...",
                height=60
            )
            
            resistance_action = st.text_area(
                "Ação Proposta:",
                key=f"resistance_action_{self.project_id}",
                placeholder="Como lidar com esta resistência?",
                height=60
            )
            
            if st.button("⚠️ Registrar Resistência", key=f"add_resistance_{self.project_id}"):
                if resistance_source.strip():
                    resistances.append({
                        'source': resistance_source,
                        'type': resistance_type,
                        'level': resistance_level,
                        'impact': resistance_impact,
                        'urgency': resistance_urgency,
                        'description': resistance_description,
                        'action': resistance_action,
                        'status': 'Identificada',
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Resistência de '{resistance_source}' registrada!")
                    st.rerun()
                else:
                    st.error("❌ Fonte da resistência é obrigatória")
        
        # Mostrar resistências
        if resistances:
            st.markdown("##### 📊 Resistências Identificadas")
            
            # Ordenar por urgência e impacto
            high_priority_resistances = [r for r in resistances if r.get('urgency') == 'Alta' or r.get('impact') == 'Alto']
            
            if high_priority_resistances:
                st.error(f"🚨 {len(high_priority_resistances)} resistência(s) de alta prioridade!")
            
            for i, resistance in enumerate(resistances):
                level_icons = {"Alto": "🔴", "Médio": "🟡", "Baixo": "🟢"}
                level_icon = level_icons.get(resistance['level'], "🟡")
                
                with st.expander(f"{level_icon} **{resistance['source']}** - {resistance['type']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Descrição:** {resistance.get('description', 'N/A')}")
                        st.write(f"**Nível:** {resistance['level']}")
                        st.write(f"**Impacto:** {resistance['impact']}")
                        st.write(f"**Urgência:** {resistance['urgency']}")
                    
                    with col2:
                        if resistance.get('action'):
                            st.write(f"**Ação Proposta:** {resistance['action']}")
                        
                        new_status = st.selectbox(
                            "Status:",
                            ["Identificada", "Em Tratamento", "Resolvida", "Monitorando"],
                            index=["Identificada", "Em Tratamento", "Resolvida", "Monitorando"].index(resistance.get('status', 'Identificada')),
                            key=f"resistance_status_{i}_{self.project_id}"
                        )
                        
                        resistances[i]['status'] = new_status
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_resistance_{i}_{self.project_id}"):
                            resistances.pop(i)
                            st.rerun()
    
    def _show_progress_tracking(self, implementation_data: Dict):
        """Acompanhamento do progresso"""
        st.markdown("#### 📈 Acompanhamento do Progresso")
        
        # Resumo geral
        st.markdown("##### 📊 Resumo Geral da Implementação")
        
        # Calcular estatísticas
        phases = implementation_data.get('implementation_phases', [])
        kpis = implementation_data.get('monitoring_system', {}).get('kpis', [])
        training_modules = implementation_data.get('training_plan', {}).get('modules', [])
        strategies = implementation_data.get('change_management', {}).get('strategies', [])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if phases:
                completed_phases = len([p for p in phases if p.get('status') == 'Concluída'])
                st.metric("Fases Concluídas", f"{completed_phases}/{len(phases)}")
            else:
                st.metric("Fases Concluídas", "0/0")
        
        with col2:
            if training_modules:
                completed_training = len([m for m in training_modules if m.get('status') == 'Concluído'])
                st.metric("Treinamentos", f"{completed_training}/{len(training_modules)}")
            else:
                st.metric("Treinamentos", "0/0")
        
        with col3:
            if strategies:
                executed_strategies = len([s for s in strategies if s.get('status') == 'Executada'])
                st.metric("Estratégias", f"{executed_strategies}/{len(strategies)}")
            else:
                st.metric("Estratégias", "0/0")
        
        with col4:
            if kpis:
                kpis_on_target = 0
                for kpi in kpis:
                    measurements = kpi.get('measurements', [])
                    if measurements:
                        current_value = measurements[-1]['value']
                        target = kpi.get('target', 0)
                        if current_value >= target:
                            kpis_on_target += 1
                
                st.metric("KPIs no Alvo", f"{kpis_on_target}/{len(kpis)}")
            else:
                st.metric("KPIs no Alvo", "0/0")
        
        # Progresso por área
        if phases:
            st.markdown("##### 📈 Progresso por Fase")
            
            phase_data = []
            for phase in phases:
                phase_data.append({
                    'Fase': phase['name'],
                    'Progresso': phase.get('progress', 0),
                    'Status': phase.get('status', 'Planejada'),
                    'Responsável': phase.get('responsible', 'N/A')
                })
            
            if phase_data:
                df = pd.DataFrame(phase_data)
                
                fig = px.bar(
                    df, x='Fase', y='Progresso',
                    color='Status',
                    title="Progresso das Fases de Implementação",
                    text='Progresso'
                )
                
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(yaxis_range=[0, 100])
                fig.update_xaxes(tickangle=45)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela detalhada
                st.dataframe(df, use_container_width=True)
        
        # Timeline de marcos
        st.markdown("##### 🎯 Timeline de Marcos")
        
        milestones = []
        
        # Marcos das fases
        for phase in phases:
            if phase.get('status') in ['Concluída', 'Em Execução']:
                milestones.append({
                    'date': phase.get('start_date', ''),
                    'milestone': f"Início: {phase['name']}",
                    'type': 'Fase',
                    'status': 'Concluído' if phase.get('progress', 0) > 0 else 'Planejado'
                })
                
                if phase.get('status') == 'Concluída':
                    milestones.append({
                        'date': phase.get('end_date', ''),
                        'milestone': f"Conclusão: {phase['name']}",
                        'type': 'Fase',
                        'status': 'Concluído'
                    })
        
        # Marcos de treinamento
        for module in training_modules:
            if module.get('status') == 'Concluído':
                milestones.append({
                    'date': module.get('created_at', '')[:10],
                    'milestone': f"Treinamento: {module['name']}",
                    'type': 'Treinamento',
                    'status': 'Concluído'
                })
        
        # Marcos de comunicação
        comm_events = implementation_data.get('communication_plan', {}).get('communication_schedule', [])
        for event in comm_events:
            if event.get('status') == 'Executado':
                milestones.append({
                    'date': event.get('date', ''),
                    'milestone': f"Comunicação: {event['title']}",
                    'type': 'Comunicação',
                    'status': 'Concluído'
                })
        
        if milestones:
            # Ordenar por data
            milestones = sorted(milestones, key=lambda x: x['date'])
            
            milestone_df = pd.DataFrame(milestones)
            milestone_df['date'] = pd.to_datetime(milestone_df['date'])
            
            fig = px.timeline(
                milestone_df, 
                x_start='date', 
                x_end='date',
                y='milestone',
                color='type',
                title="Timeline de Marcos da Implementação"
            )
            
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=max(400, len(milestones) * 30))
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Relatório de status
        st.markdown("##### 📋 Relatório de Status")
        
        col_report1, col_report2 = st.columns(2)
        
        with col_report1:
            st.markdown("**🟢 Sucessos:**")
            
            successes = []
            
            if phases:
                completed_phases = [p for p in phases if p.get('status') == 'Concluída']
                if completed_phases:
                    successes.append(f"✅ {len(completed_phases)} fase(s) concluída(s)")
            
            if training_modules:
                completed_training = [m for m in training_modules if m.get('status') == 'Concluído']
                if completed_training:
                    total_trained = sum(m.get('participants_trained', 0) for m in completed_training)
                    successes.append(f"✅ {total_trained} pessoas treinadas")
            
            if kpis:
                kpis_on_target = []
                for kpi in kpis:
                    measurements = kpi.get('measurements', [])
                    if measurements:
                        current_value = measurements[-1]['value']
                        target = kpi.get('target', 0)
                        if current_value >= target:
                            kpis_on_target.append(kpi)
                
                if kpis_on_target:
                    successes.append(f"✅ {len(kpis_on_target)} KPI(s) atingindo meta")
            
            if successes:
                for success in successes:
                    st.write(success)
            else:
                st.info("Nenhum sucesso registrado ainda")
        
        with col_report2:
            st.markdown("**🔴 Desafios/Riscos:**")
            
            challenges = []
            
            # Fases atrasadas
            if phases:
                delayed_phases = []
                for phase in phases:
                    end_date = datetime.fromisoformat(phase['end_date']).date()
                    if end_date < datetime.now().date() and phase.get('status') != 'Concluída':
                        delayed_phases.append(phase)
                
                if delayed_phases:
                    challenges.append(f"⚠️ {len(delayed_phases)} fase(s) atrasada(s)")
            
            # KPIs abaixo do alvo
            if kpis:
                kpis_below_target = []
                for kpi in kpis:
                    measurements = kpi.get('measurements', [])
                    if measurements:
                        current_value = measurements[-1]['value']
                        threshold = kpi.get('threshold', 0)
                        if current_value <= threshold:
                            kpis_below_target.append(kpi)
                
                if kpis_below_target:
                    challenges.append(f"🔴 {len(kpis_below_target)} KPI(s) abaixo do limite")
            
            # Resistências ativas
            resistances = implementation_data.get('change_management', {}).get('resistances', [])
            active_resistances = [r for r in resistances if r.get('status') not in ['Resolvida']]
            
            if active_resistances:
                high_impact = [r for r in active_resistances if r.get('impact') == 'Alto']
                if high_impact:
                    challenges.append(f"⚠️ {len(high_impact)} resistência(s) de alto impacto")
            
            if challenges:
                for challenge in challenges:
                    st.write(challenge)
            else:
                st.success("Nenhum desafio crítico identificado")
    
    def _show_action_buttons(self, implementation_data: Dict):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Implementação", key=f"save_{self.tool_name}_{self.project_id}"):
                success = self.manager.save_tool_data(self.tool_name, implementation_data, completed=False)
                if success:
                    st.success("💾 Implementação salva!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("✅ Finalizar Implementação", key=f"complete_{self.tool_name}_{self.project_id}"):
                if self._validate_implementation(implementation_data):
                    success = self.manager.save_tool_data(self.tool_name, implementation_data, completed=True)
                    if success:
                        st.success("✅ Implementação em larga escala finalizada!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao finalizar")
                else:
                    st.error("❌ Complete os requisitos mínimos")
    
    def _validate_implementation(self, implementation_data: Dict) -> bool:
        """Valida se a implementação está completa"""
        # Verificar se há fases definidas
        phases = implementation_data.get('implementation_phases', [])
        if not phases:
            st.error("❌ Defina pelo menos uma fase de implementação")
            return False
        
        # Verificar se há pelo menos uma fase concluída
        completed_phases = [p for p in phases if p.get('status') == 'Concluída']
        if not completed_phases:
            st.error("❌ Complete pelo menos uma fase de implementação")
            return False
        
        # Verificar se há KPIs de monitoramento
        kpis = implementation_data.get('monitoring_system', {}).get('kpis', [])
        if not kpis:
            st.error("❌ Defina pelo menos um KPI de monitoramento")
            return False
        
        return True


def show_improve_phase():
    """Interface principal da fase Improve"""
    st.title("🚀 Fase IMPROVE")
    st.markdown("Desenvolva, teste e implemente soluções para melhorar o processo.")
    
    # Verificar se há projeto selecionado
    if 'current_project' not in st.session_state or not st.session_state.current_project:
        st.warning("⚠️ Selecione um projeto primeiro")
        return
    
    project_data = st.session_state.current_project
    
    try:
        # Inicializar gerenciador da fase
        improve_manager = ImprovePhaseManager(project_data)
        
        # Menu de ferramentas
        st.markdown("## 🛠️ Ferramentas da Fase Improve")
        
        tools = [
            ("💡 Desenvolvimento de Soluções", "solution_development", SolutionDevelopmentTool),
            ("📋 Plano de Ação", "action_plan", ActionPlanTool),
            ("🧪 Implementação Piloto", "pilot_implementation", PilotImplementationTool),
            ("🚀 Implementação em Larga Escala", "full_implementation", FullScaleImplementationTool)
        ]
        
        # Mostrar status das ferramentas
        col1, col2, col3, col4 = st.columns(4)
        
        for i, (tool_name, tool_key, tool_class) in enumerate(tools):
            col = [col1, col2, col3, col4][i]
            with col:
                is_completed = improve_manager.is_tool_completed(tool_key)
                if is_completed:
                    st.success(f"✅ {tool_name.split(' ', 1)[1]}")
                else:
                    st.info(f"⏳ {tool_name.split(' ', 1)[1]}")
        
        # Seleção de ferramenta
        selected_tool = st.selectbox(
            "Selecione uma ferramenta:",
            tools,
            format_func=lambda x: x[0]
        )
        
        if selected_tool:
            tool_name, tool_key, tool_class = selected_tool
            
            st.divider()
            
            # Instanciar e mostrar ferramenta
            tool_instance = tool_class(improve_manager)
            tool_instance.show()
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar a fase Improve: {str(e)}")
        st.info("💡 Verifique se todos os módulos necessários estão instalados e se o ProjectManager está configurado corretamente")


# Esta linha deve estar no final do arquivo
if __name__ == "__main__":
    show_improve_phase()

