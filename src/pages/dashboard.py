"""
Dashboard principal do sistema Six Sigma
Versão melhorada com cache, validação e componentes otimizados
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib

# Imports locais
from src.auth.firebase_auth import FirebaseAuth
from src.utils.navigation import NavigationManager
from src.utils.project_manager import ProjectManager

# Tentar importar novos utilitários (com fallback)
try:
    from src.utils.session_manager import SessionManager, FormManager
    from src.config.dmaic_config import DMAIC_PHASES_CONFIG, calculate_phase_completion_percentage
except ImportError:
    # Fallback para compatibilidade
    class SessionManager:
        @staticmethod
        def get_user_data():
            return st.session_state.get('user_data', {})
        
        @staticmethod
        def get_current_project():
            return st.session_state.get('current_project')
        
        @staticmethod
        def navigate_to_dmaic(project, phase='define'):
            st.session_state.current_project = project
            st.session_state.current_page = "dmaic"
            st.session_state.current_dmaic_phase = phase
            st.rerun()
        
        @staticmethod
        def navigate_to_page(page, clear_project=False):
            st.session_state.current_page = page
            if clear_project and 'current_project' in st.session_state:
                del st.session_state.current_project
            st.rerun()
        
        @staticmethod
        def generate_unique_key(base_key, suffix=None):
            timestamp = str(int(time.time() * 1000))[-6:]
            return f"{base_key}_{suffix}_{timestamp}" if suffix else f"{base_key}_{timestamp}"
        
        @staticmethod
        def get_cached_projects(user_uid):
            return st.session_state.get(f'cached_projects_{user_uid}')
        
        @staticmethod
        def set_cached_projects(user_uid, projects):
            st.session_state[f'cached_projects_{user_uid}'] = projects
        
        @staticmethod
        def invalidate_projects_cache(user_uid):
            cache_key = f'cached_projects_{user_uid}'
            if cache_key in st.session_state:
                del st.session_state[cache_key]
    
    class FormManager:
        @staticmethod
        def validate_and_store_project_form():
            return {
                'name': st.session_state.get('project_name_input', '').strip(),
                'description': st.session_state.get('project_description_input', '').strip(),
                'business_case': st.session_state.get('project_business_case_input', '').strip(),
                'problem_statement': st.session_state.get('project_problem_input', '').strip(),
                'success_criteria': st.session_state.get('project_success_input', '').strip(),
                'expected_savings': st.session_state.get('project_savings_input', 0.0),
                'start_date': st.session_state.get('project_start_date_input', datetime.now().date()).isoformat(),
                'target_end_date': st.session_state.get('project_end_date_input', datetime.now().date()).isoformat()
            }
    
    def calculate_phase_completion_percentage(phase_data, phase):
        if not isinstance(phase_data, dict):
            return 0.0
        tools_count = 5 if phase == 'define' else 4  # Fallback simples
        completed = sum(1 for tool_data in phase_data.values() 
                       if isinstance(tool_data, dict) and tool_data.get('completed', False))
        return (completed / tools_count) * 100 if tools_count > 0 else 0.0

# Cache para projetos
@st.cache_data(ttl=300, show_spinner=False)  # Cache por 5 minutos
def load_user_projects_cached(user_uid: str, force_refresh: bool = False) -> List[Dict]:
    """Carrega projetos do usuário com cache otimizado"""
    if not force_refresh:
        cached = SessionManager.get_cached_projects(user_uid)
        if cached is not None:
            return cached
    
    # Carregar do banco de dados
    project_manager = ProjectManager()
    projects = project_manager.get_user_projects(user_uid)
    
    # Armazenar no cache
    SessionManager.set_cached_projects(user_uid, projects)
    
    return projects

def show_dashboard():
    """Dashboard principal do sistema - Versão melhorada"""
    
    # Verificar autenticação
    if not st.session_state.get('authentication_status'):
        st.error("❌ Acesso negado. Faça login primeiro.")
        return
    
    # Obter dados do usuário
    user_data = SessionManager.get_user_data()
    if not user_data:
        st.error("❌ Dados do usuário não encontrados.")
        return
    
    # Inicializar componentes
    nav_manager = NavigationManager()
    project_manager = ProjectManager()
    
    # Renderizar header principal
    render_dashboard_header(user_data)
    
    # Carregar projetos com feedback visual
    with st.spinner("📊 Carregando projetos..."):
        try:
            force_refresh = st.session_state.get('force_refresh_projects', False)
            projects = load_user_projects_cached(user_data['uid'], force_refresh)
            
            # Resetar flag de refresh
            if force_refresh:
                st.session_state.force_refresh_projects = False
                
        except Exception as e:
            st.error(f"❌ Erro ao carregar projetos: {str(e)}")
            projects = []
    
    # Mostrar métricas principais
    render_dashboard_metrics(projects, project_manager)
    
    st.divider()
    
    # Conteúdo principal baseado na existência de projetos
    if not projects:
        render_welcome_section(project_manager, user_data)
    else:
        render_projects_overview(projects, project_manager, user_data)

def render_dashboard_header(user_data: Dict):
    """Renderiza o cabeçalho do dashboard"""
    col1, col2, col3 = st.columns([4, 1, 1])
    
    with col1:
        st.title(f"🏠 Dashboard - {user_data.get('name', 'Usuário')}")
        if user_data.get('company'):
            st.caption(f"📍 {user_data['company']}")
    
    with col2:
        refresh_key = SessionManager.generate_unique_key("refresh_dashboard")
        if st.button("🔄 Atualizar", use_container_width=True, key=refresh_key):
            # Forçar refresh dos projetos
            st.session_state.force_refresh_projects = True
            SessionManager.invalidate_projects_cache(user_data['uid'])
            st.rerun()
    
    with col3:
        logout_key = SessionManager.generate_unique_key("logout_dashboard")
        if st.button("🚪 Logout", use_container_width=True, key=logout_key):
            auth = FirebaseAuth()
            auth.logout_user()
            st.rerun()

def render_dashboard_metrics(projects: List[Dict], project_manager: ProjectManager):
    """Renderiza métricas principais com cálculos otimizados"""
    
    # Cálculos otimizados em uma única passagem
    metrics = {
        'total_projects': len(projects),
        'active_projects': 0,
        'completed_projects': 0,
        'paused_projects': 0,
        'total_savings': 0.0,
        'total_progress': 0.0
    }
    
    for project in projects:
        status = project.get('status', 'active')
        
        # Contar por status
        if status == 'active':
            metrics['active_projects'] += 1
        elif status == 'completed':
            metrics['completed_projects'] += 1
        elif status == 'paused':
            metrics['paused_projects'] += 1
        
        # Somar economias
        metrics['total_savings'] += project.get('expected_savings', 0)
        
        # Calcular progresso
        try:
            progress = calculate_project_progress_optimized(project)
            metrics['total_progress'] += progress
        except Exception:
            pass  # Ignorar erros de cálculo individual
    
    # Calcular progresso médio
    avg_progress = (metrics['total_progress'] / metrics['total_projects']) if metrics['total_projects'] > 0 else 0
    
    # Renderizar métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total de Projetos", 
            metrics['total_projects'],
            help="Número total de projetos criados"
        )
    
    with col2:
        delta_active = f"+{metrics['active_projects']}" if metrics['active_projects'] > 0 else None
        st.metric(
            "Projetos Ativos", 
            metrics['active_projects'],
            delta=delta_active,
            help="Projetos em andamento"
        )
    
    with col3:
        delta_completed = f"+{metrics['completed_projects']}" if metrics['completed_projects'] > 0 else None
        st.metric(
            "Projetos Concluídos", 
            metrics['completed_projects'],
            delta=delta_completed,
            help="Projetos finalizados"
        )
    
    with col4:
        st.metric(
            "Economia Esperada", 
            f"R$ {metrics['total_savings']:,.2f}",
            help="Soma da economia esperada de todos os projetos"
        )
    
    with col5:
        # Cor do delta baseada no progresso
        delta_color = "normal"
        if avg_progress >= 75:
            delta_color = "normal"
        elif avg_progress >= 50:
            delta_color = "normal"
        else:
            delta_color = "inverse"
        
        st.metric(
            "Progresso Médio", 
            f"{avg_progress:.1f}%",
            delta=f"{avg_progress:.0f}%",
            delta_color=delta_color,
            help="Progresso médio de todos os projetos"
        )

def calculate_project_progress_optimized(project: Dict) -> float:
    """Calcula progresso do projeto de forma otimizada"""
    try:
        phases = ['define', 'measure', 'analyze', 'improve', 'control']
        total_progress = 0.0
        
        for phase in phases:
            phase_data = project.get(phase, {})
            if isinstance(phase_data, dict):
                # Usar função otimizada se disponível
                try:
                    progress = calculate_phase_completion_percentage(phase_data, phase)
                except:
                    # Fallback para cálculo simples
                    tools_count = 5 if phase == 'define' else 4
                    completed = sum(1 for tool_data in phase_data.values() 
                                  if isinstance(tool_data, dict) and tool_data.get('completed', False))
                    progress = (completed / tools_count) * 100 if tools_count > 0 else 0
                
                total_progress += progress
        
        return total_progress / len(phases)
        
    except Exception:
        return 0.0

def render_welcome_section(project_manager: ProjectManager, user_data: Dict):
    """Seção de boas-vindas otimizada para novos usuários"""
    st.markdown("## 🚀 Bem-vindo ao Green Belt Six Sigma!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Comece sua jornada Six Sigma
        
        Este sistema foi desenvolvido para guiá-lo através da metodologia DMAIC 
        (Define, Measure, Analyze, Improve, Control) de forma estruturada e eficiente.
        
        **O que você pode fazer:**
        - ✅ Criar e gerenciar projetos Six Sigma
        - 📊 Realizar análises estatísticas avançadas
        - 📋 Gerar relatórios científicos profissionais
        - 🎯 Acompanhar o progresso através das fases DMAIC
        - 🔧 Utilizar ferramentas de qualidade integradas
        
        **Pronto para começar?** Use a seção "Criar Projeto" abaixo para começar!
        """)
    
    with col2:
        st.markdown("### 🎯 Próximos Passos")
        st.info("1. Role para baixo até 'Criar Projeto'")
        st.info("2. Preencha as informações básicas")
        st.info("3. Comece pela fase Define")
        
        st.markdown("### 📚 Recursos")
        
        # Botões com chaves únicas
        tutorial_key = SessionManager.generate_unique_key("tutorial_dmaic_welcome")
        if st.button("📖 Tutorial DMAIC", use_container_width=True, key=tutorial_key):
            SessionManager.navigate_to_page("help")
        
        help_key = SessionManager.generate_unique_key("help_center_welcome")
        if st.button("❓ Central de Ajuda", use_container_width=True, key=help_key):
            SessionManager.navigate_to_page("help")
    
    st.divider()
    render_create_project_section(project_manager, user_data, is_first_project=True)

def render_projects_overview(projects: List[Dict], project_manager: ProjectManager, user_data: Dict):
    """Visão geral dos projetos existentes - Versão otimizada"""
    st.markdown("## 📊 Seus Projetos Six Sigma")
    
    # Controles de filtro e pesquisa
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_key = SessionManager.generate_unique_key("search_projects")
        search_term = st.text_input(
            "🔍 Buscar projetos", 
            placeholder="Digite o nome do projeto...", 
            key=search_key
        )
    
    with col2:
        status_key = SessionManager.generate_unique_key("status_filter")
        status_filter = st.selectbox(
            "📋 Status", 
            options=["Todos", "Ativo", "Concluído", "Pausado"], 
            index=0, 
            key=status_key
        )
    
    with col3:
        show_create = st.session_state.get('show_create_project', False)
        button_text = "❌ Fechar Criação" if show_create else "➕ Novo Projeto"
        button_type = "secondary" if show_create else "primary"
        
        toggle_key = SessionManager.generate_unique_key("toggle_create_project")
        if st.button(button_text, use_container_width=True, type=button_type, key=toggle_key):
            st.session_state.show_create_project = not show_create
            st.rerun()
    
    # Filtrar projetos
    filtered_projects = filter_projects_optimized(projects, search_term, status_filter)
    
    if filtered_projects:
        # Mostrar projetos em grid
        render_projects_grid_optimized(filtered_projects, project_manager)
        
        # Analytics apenas se houver múltiplos projetos
        if len(filtered_projects) > 1:
            st.divider()
            render_projects_analytics_optimized(filtered_projects)
    else:
        st.info("🔍 Nenhum projeto encontrado com os filtros aplicados.")
        
        # Sugestões baseadas no filtro
        if search_term:
            st.markdown("**💡 Dicas:**")
            st.markdown("- Verifique a ortografia do termo de busca")
            st.markdown("- Tente termos mais genéricos")
        elif status_filter != "Todos":
            st.markdown(f"**💡 Dica:** Não há projetos com status '{status_filter}'. Tente 'Todos'.")
    
    # Seção de criação de projeto (se habilitada)
    if st.session_state.get('show_create_project'):
        st.divider()
        render_create_project_section(project_manager, user_data, is_first_project=False)

def filter_projects_optimized(projects: List[Dict], search_term: str, status_filter: str) -> List[Dict]:
    """Filtragem otimizada de projetos"""
    if not projects:
        return []
    
    filtered = projects
    
    # Filtro de busca
    if search_term and search_term.strip():
        search_lower = search_term.lower().strip()
        filtered = [
            p for p in filtered 
            if (search_lower in p.get('name', '').lower() or 
                search_lower in p.get('description', '').lower())
        ]
    
    # Filtro de status
    if status_filter != "Todos":
        status_map = {
            "Ativo": "active",
            "Concluído": "completed",
            "Pausado": "paused"
        }
        target_status = status_map.get(status_filter)
        if target_status:
            filtered = [p for p in filtered if p.get('status') == target_status]
    
    return filtered

def render_projects_grid_optimized(projects: List[Dict], project_manager: ProjectManager):
    """Grid de projetos otimizado"""
    cols_per_row = 2
    
    for i in range(0, len(projects), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            if i + j < len(projects):
                project = projects[i + j]
                
                with col:
                    render_project_card_optimized(project, project_manager)

def render_project_card_optimized(project: Dict, project_manager: ProjectManager):
    """Card de projeto otimizado com melhor UX"""
    project_id = project.get('id', 'unknown')
    project_name = project.get('name', 'Sem nome')
    
    # Calcular progresso uma única vez
    try:
        progress = calculate_project_progress_optimized(project)
    except Exception:
        progress = 0
    
    # Configurações de status
    status_config = {
        'active': {'icon': '🟢', 'color': '#28a745', 'text': 'Ativo'},
        'completed': {'icon': '✅', 'color': '#007bff', 'text': 'Concluído'},
        'paused': {'icon': '⏸️', 'color': '#ffc107', 'text': 'Pausado'}
    }
    
    status = project.get('status', 'active')
    status_data = status_config.get(status, status_config['active'])
    
    # Dados do projeto
    created_date = project.get('created_at', '')[:10] if project.get('created_at') else 'N/A'
    expected_savings = project.get('expected_savings', 0)
    description = project.get('description', 'Sem descrição')
    
    # Renderizar card
    with st.container():
        # Card HTML otimizado
        st.markdown(f"""
        <div style='
            border: 1px solid #e1e5e9; 
            border-radius: 12px; 
            padding: 1.5rem; 
            margin: 1rem 0; 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s ease-in-out;
        '>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                <h4 style='margin: 0; color: #2c3e50; font-size: 1.1em;'>{status_data['icon']} {project_name[:30]}{'...' if len(project_name) > 30 else ''}</h4>
                <span style='
                    background-color: {status_data['color']}; 
                    color: white; 
                    padding: 0.25rem 0.5rem; 
                    border-radius: 12px; 
                    font-size: 0.8em; 
                    font-weight: bold;
                '>{status_data['text']}</span>
            </div>
            
            <p style='color: #6c757d; font-size: 0.9em; margin-bottom: 1rem; line-height: 1.4;'>
                {description[:120]}{'...' if len(description) > 120 else ''}
            </p>
            
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;'>
                <div>
                    <small style='color: #28a745; font-weight: bold;'>💰 Economia Esperada</small><br>
                    <strong style='color: #2c3e50;'>R$ {expected_savings:,.2f}</strong>
                </div>
                <div>
                    <small style='color: #007bff; font-weight: bold;'>📅 Criado em</small><br>
                    <strong style='color: #2c3e50;'>{created_date}</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Progresso com cores dinâmicas
        st.markdown(f"**Progresso: {progress:.1f}%**")
        
        # Cor da barra baseada no progresso
        if progress >= 80:
            progress_color = "#28a745"  # Verde
        elif progress >= 50:
            progress_color = "#ffc107"  # Amarelo
        elif progress > 0:
            progress_color = "#17a2b8"  # Azul
        else:
            progress_color = "#dc3545"  # Vermelho
        
        # Barra de progresso personalizada
        st.markdown(f"""
        <div style='
            width: 100%; 
            background-color: #e9ecef; 
            border-radius: 10px; 
            height: 10px; 
            margin-bottom: 1rem;
        '>
            <div style='
                width: {progress}%; 
                background-color: {progress_color}; 
                height: 10px; 
                border-radius: 10px; 
                transition: width 0.3s ease-in-out;
            '></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dmaic_key = SessionManager.generate_unique_key("dmaic", project_id[:8])
            if st.button("🎯 Abrir DMAIC", key=dmaic_key, use_container_width=True, type="primary"):
                SessionManager.navigate_to_dmaic(project, 'define')
                st.success(f"✅ Abrindo projeto: {project_name}")
                time.sleep(0.5)
        
        with col2:
            select_key = SessionManager.generate_unique_key("select", project_id[:8])
            if st.button("📊 Selecionar", key=select_key, use_container_width=True):
                st.session_state.current_project = project
                st.success(f"📊 Projeto selecionado: {project_name}")
                time.sleep(0.5)
        
        with col3:
            # Sistema de confirmação para exclusão
            confirm_key = f"confirm_delete_{project_id}"
            if st.session_state.get(confirm_key):
                delete_confirm_key = SessionManager.generate_unique_key("confirm_delete", project_id[:8])
                if st.button("⚠️ Confirmar", key=delete_confirm_key, use_container_width=True, type="primary"):
                    with st.spinner("Excluindo projeto..."):
                        success = project_manager.delete_project(project_id, project['user_uid'])
                    
                    if success:
                        st.success("✅ Projeto excluído com sucesso!")
                        # Limpar confirmação e cache
                        if confirm_key in st.session_state:
                            del st.session_state[confirm_key]
                        if st.session_state.get('current_project', {}).get('id') == project_id:
                            del st.session_state.current_project
                        
                        # Invalidar cache
                        user_data = SessionManager.get_user_data()
                        SessionManager.invalidate_projects_cache(user_data['uid'])
                        
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Erro ao excluir projeto")
            else:
                delete_key = SessionManager.generate_unique_key("delete", project_id[:8])
                if st.button("🗑️ Excluir", key=delete_key, use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.warning("⚠️ Clique em 'Confirmar' para excluir permanentemente")
                    st.rerun()

def render_projects_analytics_optimized(projects: List[Dict]):
    """Analytics otimizados dos projetos"""
    st.markdown("### 📈 Análises dos Projetos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de status otimizado
        status_counts = {'Ativo': 0, 'Concluído': 0, 'Pausado': 0}
        status_map = {'active': 'Ativo', 'completed': 'Concluído', 'paused': 'Pausado'}
        
        for project in projects:
            status = project.get('status', 'active')
            label = status_map.get(status, 'Ativo')
            status_counts[label] += 1
        
        # Filtrar apenas status com valores > 0
        filtered_status = {k: v for k, v in status_counts.items() if v > 0}
        
        if filtered_status:
            fig_status = px.pie(
                values=list(filtered_status.values()),
                names=list(filtered_status.keys()),
                title="Distribuição por Status",
                color_discrete_map={
                    'Ativo': '#28a745',
                    'Concluído': '#007bff',
                    'Pausado': '#ffc107'
                }
            )
            fig_status.update_layout(height=400, showlegend=True)
            fig_status.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        # Gráfico de progresso otimizado
        project_data = []
        for i, project in enumerate(projects):
            name = project.get('name', f"Projeto {i+1}")
            # Truncar nomes muito longos
            display_name = name[:20] + "..." if len(name) > 20 else name
            progress = calculate_project_progress_optimized(project)
            
            project_data.append({
                'name': display_name,
                'progress': progress,
                'full_name': name  # Para tooltip
            })
        
        # Ordenar por progresso para melhor visualização
        project_data.sort(key=lambda x: x['progress'], reverse=True)
        
        if project_data:
            fig_progress = px.bar(
                x=[p['progress'] for p in project_data],
                y=[p['name'] for p in project_data],
                orientation='h',
                title="Progresso dos Projetos (%)",
                labels={'x': 'Progresso (%)', 'y': 'Projetos'},
                color=[p['progress'] for p in project_data],
                color_continuous_scale='RdYlGn',
                range_color=[0, 100]
            )
            
            # Customizar layout
            fig_progress.update_layout(
                height=400,
                coloraxis_colorbar=dict(title="Progresso %"),
                xaxis=dict(range=[0, 100])
            )
            
            # Adicionar hover personalizado
            fig_progress.update_traces(
                hovertemplate='<b>%{customdata}</b><br>Progresso: %{x:.1f}%<extra></extra>',
                customdata=[p['full_name'] for p in project_data]
            )
            
            st.plotly_chart(fig_progress, use_container_width=True)
    
    # Estatísticas adicionais para 3+ projetos
    if len(projects) >= 3:
        render_additional_statistics(projects)

def render_additional_statistics(projects: List[Dict]):
    """Estatísticas adicionais otimizadas"""
    st.markdown("### 📊 Estatísticas Adicionais")
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        # Projeto com maior economia
        max_savings_project = max(projects, key=lambda x: x.get('expected_savings', 0))
        max_savings = max_savings_project.get('expected_savings', 0)
        max_savings_name = max_savings_project.get('name', 'N/A')[:20]
        
        st.metric(
            "Maior Economia Esperada",
            f"R$ {max_savings:,.2f}",
            delta=max_savings_name,
            help=f"Projeto: {max_savings_project.get('name', 'N/A')}"
        )
    
    with col4:
        # Projeto com maior progresso
        max_progress_project = max(projects, key=lambda x: calculate_project_progress_optimized(x))
        max_progress = calculate_project_progress_optimized(max_progress_project)
        max_progress_name = max_progress_project.get('name', 'N/A')[:20]
        
        st.metric(
            "Maior Progresso",
            f"{max_progress:.1f}%",
            delta=max_progress_name,
            help=f"Projeto: {max_progress_project.get('name', 'N/A')}"
        )
    
    with col5:
        # Duração média dos projetos
        total_days = 0
        count = 0
        
        for project in projects:
            start_date = project.get('start_date')
            end_date = project.get('target_end_date')
            
            if start_date and end_date:
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    total_days += (end - start).days
                    count += 1
                except Exception:
                    pass  # Ignorar datas inválidas
        
        if count > 0:
            avg_days = total_days // count
            avg_months = avg_days // 30
            delta_text = f"≈ {avg_months} meses" if avg_months > 0 else "< 1 mês"
        else:
            avg_days = 0
            delta_text = "N/A"
        
        st.metric(
            "Duração Média",
            f"{avg_days} dias",
            delta=delta_text,
            help="Duração média baseada nas datas de início e fim"
        )

def render_create_project_section(project_manager: ProjectManager, user_data: Dict, is_first_project: bool = False):
    """Seção de criação de projeto otimizada"""
    
    # Header diferenciado
    if is_first_project:
        st.markdown("## 🎯 Criar Seu Primeiro Projeto")
        st.markdown("Preencha as informações abaixo para começar sua jornada Six Sigma:")
    else:
        st.markdown("## ➕ Criar Novo Projeto")
    
    # Formulário em abas para melhor organização
    tab1, tab2, tab3 = st.tabs(["📋 Informações Básicas", "💼 Justificativa", "📅 Cronograma"])
    
    # Variáveis para validação
    validation_errors = []
    validation_warnings = []
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            project_name = st.text_input(
                "Nome do Projeto *",
                placeholder="Ex: Redução de Defeitos na Linha de Produção A",
                help="Nome claro e descritivo do projeto",
                key="project_name_input"
            )
            
            # Validação em tempo real do nome
            if project_name:
                if len(project_name.strip()) < 5:
                    validation_errors.append("Nome deve ter pelo menos 5 caracteres")
                elif len(project_name) > 100:
                    validation_warnings.append("Nome muito longo (>100 caracteres)")
        
        with col2:
            expected_savings = st.number_input(
                "Economia Esperada (R$)",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                help="Valor estimado de economia ou ganho financeiro",
                key="project_savings_input",
                format="%.2f"
            )
            
            # Validação da economia
            if expected_savings <= 0:
                validation_warnings.append("Considere definir uma economia esperada para justificar o projeto")
        
        description = st.text_area(
            "Descrição do Projeto",
            placeholder="Descreva o problema atual, oportunidade de melhoria ou objetivo do projeto...",
            help="Descrição detalhada do que será trabalhado no projeto",
            height=120,
            key="project_description_input"
        )
    
    with tab2:
        business_case = st.text_area(
            "Justificativa do Negócio",
            placeholder="Por que este projeto é importante? Qual o impacto esperado no negócio? Quais são os benefícios?",
            help="Explique a importância estratégica e o impacto esperado",
            height=120,
            key="project_business_case_input"
        )
        
        col3, col4 = st.columns(2)
        
        with col3:
            problem_statement = st.text_area(
                "Declaração do Problema",
                placeholder="Qual é o problema específico que será resolvido?",
                height=80,
                key="project_problem_input"
            )
        
        with col4:
            success_criteria = st.text_area(
                "Critérios de Sucesso",
                placeholder="Como saberemos que o projeto foi bem-sucedido?",
                height=80,
                key="project_success_input"
            )
    
    with tab3:
        col5, col6 = st.columns(2)
        
        with col5:
            start_date = st.date_input(
                "Data de Início",
                value=datetime.now().date(),
                help="Quando o projeto deve começar",
                key="project_start_date_input"
            )
        
        with col6:
            target_end_date = st.date_input(
                "Data Alvo de Conclusão",
                value=(datetime.now() + timedelta(days=120)).date(),
                help="Meta para conclusão (recomendado: 3-4 meses)",
                key="project_end_date_input"
            )
        
        # Validação de datas
        date_valid = target_end_date > start_date
        
        if not date_valid:
            validation_errors.append("A data de conclusão deve ser posterior à data de início")
        else:
            duration = (target_end_date - start_date).days
            
            # Métricas de duração
            col7, col8, col9 = st.columns(3)
            
            with col7:
                st.metric("Duração Total", f"{duration} dias")
            
            with col8:
                weeks = duration // 7
                st.metric("Duração em Semanas", f"{weeks} semanas")
            
            with col9:
                months = round(duration / 30.44, 1)
                st.metric("Duração em Meses", f"{months} meses")
            
            # Validações de duração
            if duration > 180:
                validation_warnings.append("Projeto com duração longa (>6 meses). Considere dividir em fases menores.")
            elif duration < 30:
                validation_warnings.append("Projeto com duração muito curta (<1 mês). Verifique se é adequado para Six Sigma.")
    
    # Mostrar erros e avisos de validação
    if validation_errors:
        for error in validation_errors:
            st.error(f"❌ {error}")
    
    if validation_warnings:
        for warning in validation_warnings:
            st.warning(f"⚠️ {warning}")
    
    # Resumo do projeto (se nome preenchido)
    if project_name and project_name.strip():
        render_project_summary(project_name, description, expected_savings, duration if date_valid else 0)
    
    st.divider()
    
    # Botões de ação
    col_action1, col_action2, col_action3, col_action4 = st.columns([2, 1, 1, 2])
    
    with col_action2:
        create_key = SessionManager.generate_unique_key("create_project_button")
        can_create = (project_name and project_name.strip() and 
                     date_valid and len(validation_errors) == 0)
        
        create_button = st.button(
            "✅ Criar Projeto",
            use_container_width=True,
            type="primary",
            disabled=not can_create,
            key=create_key
        )
    
    with col_action3:
        clear_key = SessionManager.generate_unique_key("clear_project_form")
        clear_button = st.button(
            "🔄 Limpar Tudo",
            use_container_width=True,
            key=clear_key
        )
    
    # Processar ações
    if create_button and can_create:
        project_data = FormManager.validate_and_store_project_form()
        handle_project_creation_optimized(project_manager, user_data, project_data)
    
    if clear_button:
        clear_project_form_optimized()

def render_project_summary(name: str, description: str, savings: float, duration: int):
    """Renderiza resumo do projeto"""
    st.markdown("### 📊 Resumo do Projeto")
    
    summary_col1, summary_col2 = st.columns([2, 1])
    
    with summary_col1:
        st.markdown(f"""
        **Projeto:** {name}
        
        **Descrição:** {description[:100]}{'...' if len(description) > 100 else ''}
        
        **Economia Esperada:** R$ {savings:,.2f}
        
        **Duração:** {duration} dias
        """)
    
    with summary_col2:
        if duration > 0:
            st.metric("Status", "✅ Pronto para criar")
            st.metric("Fase Inicial", "🎯 Define")
            st.metric("Metodologia", "📋 DMAIC")

def handle_project_creation_optimized(project_manager: ProjectManager, user_data: Dict, project_data: Dict):
    """Manipula criação de projeto com feedback otimizado"""
    
    # Feedback visual durante criação
    progress_placeholder = st.empty()
    
    with progress_placeholder:
        with st.spinner("🔄 Criando projeto..."):
            success, result = project_manager.create_project(user_data['uid'], project_data)
    
    progress_placeholder.empty()
    
    if success:
        # Feedback de sucesso
        st.success("🎉 Projeto criado com sucesso!")
        st.balloons()
        
        # Invalidar cache
        SessionManager.invalidate_projects_cache(user_data['uid'])
        
        # Tentar carregar projeto criado
        new_project = None
        try:
            new_project = project_manager.get_project(result)
            if new_project:
                st.info(f"✅ Projeto '{new_project.get('name')}' carregado e pronto para uso!")
                st.session_state.newly_created_project = new_project
            else:
                st.warning("⚠️ Projeto criado mas não foi possível carregá-lo automaticamente.")
        except Exception as e:
            st.warning(f"⚠️ Projeto criado mas erro ao carregar: {str(e)}")
        
        # Opções de navegação
        render_post_creation_options(new_project)
        
    else:
        # Tratamento de erro melhorado
        st.error(f"❌ Erro ao criar projeto: {result}")
        render_error_details(result)

def render_post_creation_options(new_project: Optional[Dict]):
    """Opções após criação bem-sucedida do projeto"""
    st.markdown("### 🚀 O que fazer agora?")
    
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    
    with nav_col1:
        start_key = SessionManager.generate_unique_key("start_dmaic_new")
        if st.button("🎯 Começar no DMAIC", use_container_width=True, type="primary", key=start_key):
            if new_project:
                SessionManager.navigate_to_dmaic(new_project, 'define')
            elif 'newly_created_project' in st.session_state:
                SessionManager.navigate_to_dmaic(st.session_state.newly_created_project, 'define')
            else:
                st.error("Projeto não encontrado")
    
    with nav_col2:
        dashboard_key = SessionManager.generate_unique_key("go_dashboard_new")
        if st.button("📊 Ver Dashboard", use_container_width=True, key=dashboard_key):
            st.session_state.show_create_project = False
            clear_project_form_optimized()
            st.success("📊 Voltando ao Dashboard...")
            time.sleep(0.5)
            st.rerun()
    
    with nav_col3:
        another_key = SessionManager.generate_unique_key("create_another_new")
        if st.button("➕ Criar Outro", use_container_width=True, key=another_key):
            clear_project_form_optimized()
            st.success("🔄 Formulário limpo para novo projeto!")
            st.rerun()

def render_error_details(error_message: str):
    """Renderiza detalhes do erro de forma útil"""
    with st.expander("🔍 Ver Detalhes do Erro"):
        if "Firebase" in str(error_message):
            st.error("🔥 **Problema de Conectividade Firebase**")
            st.markdown("- Verifique sua conexão com a internet")
            st.markdown("- Teste a configuração na página de configuração")
        elif "permission" in str(error_message).lower():
            st.error("🔒 **Problema de Permissão**")
            st.markdown("- Verifique as regras de segurança do Firestore")
            st.markdown("- Confirme se o usuário tem permissão de escrita")
        else:
            st.error(f"📋 **Erro Técnico:** {error_message}")

def clear_project_form_optimized():
    """Limpa formulário de projeto de forma otimizada"""
    form_fields = [
        'project_name_input', 'project_description_input', 'project_business_case_input',
        'project_savings_input', 'project_start_date_input', 'project_end_date_input',
        'project_problem_input', 'project_success_input'
    ]
    
    for field in form_fields:
        if field in st.session_state:
            del st.session_state[field]

# Função principal para compatibilidade
def main():
    """Função principal para teste standalone"""
    show_dashboard()

if __name__ == "__main__":
    main()
