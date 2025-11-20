import streamlit as st
from typing import Dict
from src.pages.dashboard import show_dashboard
from src.pages.dmaic_phases import show_dmaic_phase
from src.pages.projects import show_projects_page
from src.pages.reports import show_reports_page
from src.pages.help import show_help_page

def show_main_navigation():
    """Controla a navegação principal da aplicação"""
    
    if not st.session_state.get('authentication_status'):
        st.error("❌ Usuário não autenticado")
        return False
    
    # Renderizar navegação no topo (breadcrumb)
    render_top_navigation()
    
    # Obter página atual
    current_page = st.session_state.get('current_page', 'dashboard')
    
    # Roteamento de páginas
    if current_page == 'dashboard':
        show_dashboard()
    elif current_page == 'projects':
        show_projects_page()
    elif current_page == 'dmaic':
        show_dmaic_phase()
    elif current_page == 'reports':
        show_reports_page()
    elif current_page == 'help':
        show_help_page()
    else:
        # Página padrão
        st.session_state.current_page = 'dashboard'
        show_dashboard()
    
    # Renderizar navegação na sidebar (sempre visível)
    current_project = st.session_state.get('current_project')
    render_sidebar_navigation(current_project)
    
    return True

def render_top_navigation():
    """Renderiza a navegação superior (breadcrumb)"""
    current_page = st.session_state.get('current_page', 'dashboard')
    current_project = st.session_state.get('current_project')
    
    # Construir breadcrumb
    breadcrumb_items = []
    
    # Sempre incluir Dashboard
    breadcrumb_items.append("🏠 Dashboard")
    
    if current_page == 'projects':
        breadcrumb_items.append("📁 Projetos")
    elif current_page == 'dmaic' and current_project:
        breadcrumb_items.append("📁 Projetos")
        breadcrumb_items.append(f"📊 {current_project.get('name', 'Projeto')}")
        
        # Adicionar fase atual se disponível
        current_phase = st.session_state.get('current_phase', 'define')
        phase_names = {
            'define': '🎯 Define',
            'measure': '📊 Measure', 
            'analyze': '🔍 Analyze',
            'improve': '⚡ Improve',
            'control': '✅ Control'
        }
        breadcrumb_items.append(phase_names.get(current_phase, current_phase))
    elif current_page == 'reports':
        breadcrumb_items.append("📋 Relatórios")
    elif current_page == 'help':
        breadcrumb_items.append("❓ Ajuda")
    
    # Renderizar breadcrumb com botões funcionais
    st.markdown("**Navegação:**")
    
    cols = st.columns(len(breadcrumb_items))
    
    for i, (col, item) in enumerate(zip(cols, breadcrumb_items)):
        with col:
            # Tornar os botões funcionais
            if i == 0:  # Dashboard
                if st.button(item, key=f"nav_dashboard_{i}", use_container_width=True):
                    st.session_state.current_page = 'dashboard'
                    if 'current_project' in st.session_state:
                        del st.session_state.current_project
                    st.rerun()
            elif "Projetos" in item:
                if st.button(item, key=f"nav_projects_{i}", use_container_width=True):
                    st.session_state.current_page = 'projects'
                    if 'current_project' in st.session_state:
                        del st.session_state.current_project
                    st.rerun()
            elif "Relatórios" in item:
                if st.button(item, key=f"nav_reports_{i}", use_container_width=True):
                    st.session_state.current_page = 'reports'
                    st.rerun()
            else:
                # Outros itens (apenas visual)
                st.button(item, key=f"nav_item_{i}", disabled=True, use_container_width=True)

def render_sidebar_navigation(current_project=None):
    """Renderiza a navegação na sidebar"""
    with st.sidebar:
        # Usuário atual
        user_data = st.session_state.get('user_data', {})
        if user_data:
            st.markdown(f"👤 **{user_data.get('email', 'Usuário')}**")
        
        st.divider()
        
        # Navegação Principal
        st.markdown("### 🧭 Navegação Principal")
        
        # Dashboard
        if st.button("🏠 Dashboard", key="sidebar_dashboard", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            if 'current_project' in st.session_state:
                del st.session_state.current_project
            if 'current_phase' in st.session_state:
                del st.session_state.current_phase
            st.rerun()
        
        # Projetos
        if st.button("📁 Projetos", key="sidebar_projects", use_container_width=True):
            st.session_state.current_page = 'projects'
            if 'current_project' in st.session_state:
                del st.session_state.current_project
            if 'current_phase' in st.session_state:
                del st.session_state.current_phase
            st.rerun()
        
        # Relatórios
        if st.button("📋 Relatórios", key="sidebar_reports", use_container_width=True):
            st.session_state.current_page = 'reports'
            st.rerun()
        
        # Ajuda
        if st.button("❓ Ajuda", key="sidebar_help", use_container_width=True):
            st.session_state.current_page = 'help'
            st.rerun()
        
        st.divider()
        
        # Projeto Atual (se houver)
        if current_project:
            st.markdown("### 📊 Projeto Atual")
            
            project_name = current_project.get('name', 'Projeto sem nome')
            st.info(f"**{project_name}**")
            
            # Informações do projeto
            if current_project.get('expected_savings'):
                st.write(f"💰 R$ {current_project['expected_savings']:,.2f}")
            
            if current_project.get('start_date'):
                st.write(f"📅 {current_project['start_date'][:10]}")
            
            # Botão para fechar projeto
            if st.button("❌ Fechar Projeto", key="close_project", use_container_width=True):
                if 'current_project' in st.session_state:
                    del st.session_state.current_project
                if 'current_phase' in st.session_state:
                    del st.session_state.current_phase
                st.session_state.current_page = 'projects'
                st.rerun()
            
            st.divider()
            
            # Fases DMAIC com progresso dinâmico
            st.markdown("### 🔄 Fases DMAIC")
            
            current_phase = st.session_state.get('current_phase', 'define')
            
            # Calcular progresso real de cada fase
            phases_progress = _calculate_phases_progress(current_project)
            
            phases = [
                ('define', '🎯', 'Define', phases_progress.get('define', 0)),
                ('measure', '📊', 'Measure', phases_progress.get('measure', 0)),
                ('analyze', '🔍', 'Analyze', phases_progress.get('analyze', 0)),
                ('improve', '⚡', 'Improve', phases_progress.get('improve', 0)),
                ('control', '✅', 'Control', phases_progress.get('control', 0))
            ]
            
            for phase_key, icon, phase_name, progress in phases:
                # Estilo baseado na fase atual
                button_type = "primary" if phase_key == current_phase else "secondary"
                
                # Botão da fase
                if st.button(
                    f"{icon} {phase_name}",
                    key=f"phase_{phase_key}",
                    use_container_width=True,
                    type=button_type
                ):
                    st.session_state.current_phase = phase_key
                    st.session_state.current_page = 'dmaic'
                    st.rerun()
                
                # Barra de progresso com cores dinâmicas
                progress_value = progress / 100
                st.progress(progress_value)
                
                # Caption com cor baseada no progresso
                if progress == 100:
                    st.success(f"✅ {progress:.0f}%")
                elif progress >= 50:
                    st.warning(f"⚠️ {progress:.0f}%")
                elif progress > 0:
                    st.info(f"🔄 {progress:.0f}%")
                else:
                    st.caption(f"⏳ {progress:.0f}%")
        
        st.divider()
        
        # Logout
        if st.button("🚪 Logout", key="logout_button", use_container_width=True, type="secondary"):
            # Limpar session state
            keys_to_clear = [
                'authentication_status', 'user_data', 'current_project', 
                'current_page', 'current_phase'
            ]
            
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.rerun()


def _calculate_phases_progress(project_data: Dict) -> Dict:
    """
    ✅ CORREÇÃO: Calcula progresso real de cada fase baseado nas ferramentas concluídas
    Conta apenas as ferramentas que REALMENTE EXISTEM
    """
    progress = {}
    
    try:
        # Definir explicitamente quais ferramentas existem em cada fase
        phase_tools = {
            'define': ['charter', 'stakeholders', 'voc', 'sipoc', 'timeline'],
            'measure': ['data_collection_plan', 'file_upload', 'process_capability', 'msa', 'baseline_data'],
            'analyze': ['statistical_analysis', 'root_cause_analysis'],  # ← CORRIGIDO: apenas 2 ferramentas
            'improve': ['solution_development', 'action_plan', 'pilot_implementation', 'full_implementation'],
            'control': ['control_plan', 'documentation']  # ← CORRIGIDO: apenas 2 ferramentas
        }
        
        for phase, tools in phase_tools.items():
            phase_data = project_data.get(phase, {})
            completed = 0
            
            for tool in tools:
                tool_data = phase_data.get(tool, {})
                if isinstance(tool_data, dict) and tool_data.get('completed', False):
                    completed += 1
            
            progress[phase] = (completed / len(tools)) * 100 if tools else 0
        
    except Exception as e:
        # Em caso de erro, retornar valores padrão
        st.error(f"Erro no cálculo de progresso: {str(e)}")
        progress = {
            'define': 0,
            'measure': 0,
            'analyze': 0,
            'improve': 0,
            'control': 0
        }
    
    return progress
