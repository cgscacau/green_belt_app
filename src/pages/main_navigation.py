import streamlit as st
from src.pages.dashboard import show_dashboard
from src.pages.projects import show_projects_page
from src.pages.dmaic_phases import show_dmaic_phase
from src.pages.reports import show_reports_page
from src.pages.help import show_help_page
from src.utils.navigation import NavigationManager

def show_main_navigation():
    """Controla a navegação principal da aplicação"""
    
    # Verificar autenticação
    if not st.session_state.get('authentication_status'):
        return False
    
    # Inicializar gerenciador de navegação
    nav_manager = NavigationManager()
    
    # Renderizar navegação no topo (breadcrumb)
    nav_manager.render_top_navigation()
    
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
    nav_manager.render_sidebar_navigation(current_project)
    
    return True
