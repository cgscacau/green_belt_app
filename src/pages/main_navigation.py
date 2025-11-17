"""
Sistema de navegação principal da aplicação
Versão melhorada com gerenciamento robusto de estado e UX otimizada
"""

import streamlit as st
from typing import Dict, Optional, Any
import time
import traceback

# Tentar importar utilitários melhorados
try:
    from src.utils.session_manager import SessionManager
    from src.config.dmaic_config import DMAIC_PHASES_CONFIG, DMACPhase, calculate_phase_completion_percentage
    HAS_NEW_UTILS = True
except ImportError:
    # Fallback para compatibilidade
    class SessionManager:
        @staticmethod
        def is_authenticated():
            return st.session_state.get('authentication_status', False)
        
        @staticmethod
        def get_user_data():
            return st.session_state.get('user_data', {})
        
        @staticmethod
        def get_current_project():
            return st.session_state.get('current_project')
        
        @staticmethod
        def get_current_phase():
            return st.session_state.get('current_phase', 'define')
        
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
        def logout():
            keys_to_clear = [
                'authentication_status', 'user_data', 'current_project', 
                'current_page', 'current_phase'
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    def calculate_phase_completion_percentage(phase_data, phase):
        if not isinstance(phase_data, dict):
            return 0.0
        tools_count = 5 if phase == 'define' else 4
        completed = sum(1 for tool_data in phase_data.values() 
                       if isinstance(tool_data, dict) and tool_data.get('completed', False))
        return (completed / tools_count) * 100 if tools_count > 0 else 0.0
    
    HAS_NEW_UTILS = False

# Importações das páginas com tratamento de erro robusto
def import_page_modules():
    """Importa módulos das páginas com fallback robusto"""
    modules = {}
    
    # Dashboard
    try:
        from src.pages.dashboard import show_dashboard
        modules['dashboard'] = show_dashboard
    except ImportError:
        try:
            from pages.dashboard import show_dashboard
            modules['dashboard'] = show_dashboard
        except ImportError:
            modules['dashboard'] = lambda: show_page_error('Dashboard', 'dashboard.py')
    
    # DMAIC Phases
    try:
        from src.pages.dmaic_phases import show_dmaic_phase
        modules['dmaic'] = show_dmaic_phase
    except ImportError:
        try:
            from pages.dmaic_phases import show_dmaic_phase
            modules['dmaic'] = show_dmaic_phase
        except ImportError:
            modules['dmaic'] = lambda: show_page_error('DMAIC', 'dmaic_phases.py')
    
    # Projects
    try:
        from src.pages.projects import show_projects_page
        modules['projects'] = show_projects_page
    except ImportError:
        try:
            from pages.projects import show_projects_page
            modules['projects'] = show_projects_page
        except ImportError:
            modules['projects'] = lambda: show_page_error('Projetos', 'projects.py')
    
    # Reports
    try:
        from src.pages.reports import show_reports_page
        modules['reports'] = show_reports_page
    except ImportError:
        try:
            from pages.reports import show_reports_page
            modules['reports'] = show_reports_page
        except ImportError:
            modules['reports'] = lambda: show_page_error('Relatórios', 'reports.py')
    
    # Help
    try:
        from src.pages.help import show_help_page
        modules['help'] = show_help_page
    except ImportError:
        try:
            from pages.help import show_help_page
            modules['help'] = show_help_page
        except ImportError:
            modules['help'] = lambda: show_page_error('Ajuda', 'help.py')
    
    return modules

# Cache dos módulos para evitar reimportações
@st.cache_resource
def get_page_modules():
    """Cache dos módulos das páginas"""
    return import_page_modules()

def show_main_navigation():
    """Controla a navegação principal da aplicação - Versão melhorada"""
    
    # Verificar autenticação
    if not SessionManager.is_authenticated():
        render_authentication_error()
        return False
    
    # Renderizar navegação no topo
    render_enhanced_top_navigation()
    
    # Obter página atual
    current_page = st.session_state.get('current_page', 'dashboard')
    
    # Validar página
    valid_pages = ['dashboard', 'projects', 'dmaic', 'reports', 'help']
    if current_page not in valid_pages:
        st.warning(f"⚠️ Página inválida: {current_page}. Redirecionando para Dashboard...")
        current_page = 'dashboard'
        st.session_state.current_page = 'dashboard'
        time.sleep(1)
        st.rerun()
    
    # Roteamento de páginas com tratamento de erro
    success = route_to_page(current_page)
    
    if success:
        # Renderizar navegação na sidebar
        render_enhanced_sidebar_navigation()
    
    return success

def render_authentication_error():
    """Renderiza erro de autenticação de forma amigável"""
    st.error("❌ **Acesso Negado**")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🔐 Você precisa estar logado para acessar esta área
        
        **Por que estou vendo isso?**
        - Sua sessão pode ter expirado
        - Você não fez login ainda
        - Houve um problema na autenticação
        
        **O que fazer:**
        1. Clique no botão "Ir para Login" ao lado
        2. Faça login com suas credenciais
        3. Você será redirecionado automaticamente
        """)
    
    with col2:
        st.markdown("### 🚀 Ação Rápida")
        
        login_key = SessionManager.generate_unique_key("go_to_login")
        if st.button("🔑 Ir para Login", key=login_key, use_container_width=True, type="primary"):
            # Limpar session state e redirecionar
            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        st.info("💡 **Dica:** Mantenha sua sessão ativa navegando regularmente")

def render_enhanced_top_navigation():
    """Renderiza navegação superior melhorada com breadcrumb funcional"""
    current_page = st.session_state.get('current_page', 'dashboard')
    current_project = SessionManager.get_current_project()
    
    # Container para breadcrumb
    with st.container():
        # Construir breadcrumb dinâmico
        breadcrumb_items = build_breadcrumb_items(current_page, current_project)
        
        if len(breadcrumb_items) > 1:
            st.markdown("**🧭 Navegação:**")
            
            # Renderizar breadcrumb como botões funcionais
            cols = st.columns(len(breadcrumb_items))
            
            for i, (col, item) in enumerate(zip(cols, breadcrumb_items)):
                with col:
                    render_breadcrumb_button(item, i)
        
        # Linha separadora
        st.markdown("---")

def build_breadcrumb_items(current_page: str, current_project: Optional[Dict]) -> list:
    """Constrói itens do breadcrumb baseado na página atual"""
    items = []
    
    # Sempre incluir Dashboard
    items.append({
        'label': '🏠 Dashboard',
        'action': 'go_dashboard',
        'is_current': current_page == 'dashboard'
    })
    
    if current_page == 'projects':
        items.append({
            'label': '📁 Projetos',
            'action': None,
            'is_current': True
        })
    
    elif current_page == 'dmaic':
        items.append({
            'label': '📁 Projetos',
            'action': 'go_projects',
            'is_current': False
        })
        
        if current_project:
            project_name = current_project.get('name', 'Projeto')
            truncated_name = project_name[:20] + "..." if len(project_name) > 20 else project_name
            
            items.append({
                'label': f"📊 {truncated_name}",
                'action': 'stay_dmaic',
                'is_current': False,
                'tooltip': project_name if len(project_name) > 20 else None
            })
            
            # Adicionar fase atual
            current_phase = SessionManager.get_current_phase()
            phase_names = {
                'define': '🎯 Define',
                'measure': '📊 Measure',
                'analyze': '🔍 Analyze',
                'improve': '⚡ Improve',
                'control': '🎮 Control'
            }
            
            phase_label = phase_names.get(current_phase, f"🔄 {current_phase.title()}")
            items.append({
                'label': phase_label,
                'action': None,
                'is_current': True
            })
        else:
            items.append({
                'label': '📋 DMAIC',
                'action': None,
                'is_current': True
            })
    
    elif current_page == 'reports':
        items.append({
            'label': '📋 Relatórios',
            'action': None,
            'is_current': True
        })
    
    elif current_page == 'help':
        items.append({
            'label': '❓ Ajuda',
            'action': None,
            'is_current': True
        })
    
    return items

def render_breadcrumb_button(item: Dict, index: int):
    """Renderiza botão individual do breadcrumb"""
    is_current = item.get('is_current', False)
    action = item.get('action')
    tooltip = item.get('tooltip')
    
    # Configuração do botão
    button_type = "secondary" if is_current else "primary"
    disabled = is_current or action is None
    
    # Chave única para o botão
    button_key = SessionManager.generate_unique_key(f"breadcrumb_{index}", action or "current")
    
    # Renderizar botão
    if st.button(
        item['label'],
        key=button_key,
        disabled=disabled,
        type=button_type,
        use_container_width=True,
        help=tooltip
    ):
        handle_breadcrumb_action(action)

def handle_breadcrumb_action(action: str):
    """Manipula ações dos botões do breadcrumb"""
    if action == 'go_dashboard':
        SessionManager.navigate_to_page('dashboard', clear_project=True)
    elif action == 'go_projects':
        SessionManager.navigate_to_page('projects', clear_project=True)
    elif action == 'stay_dmaic':
        # Manter na página DMAIC mas resetar para Define
        st.session_state.current_phase = 'define'
        st.rerun()

def route_to_page(page: str) -> bool:
    """Roteia para a página especificada com tratamento de erro"""
    try:
        page_modules = get_page_modules()
        
        if page in page_modules:
            # Executar página com tratamento de erro
            try:
                page_modules[page]()
                return True
            except Exception as e:
                render_page_execution_error(page, e)
                return False
        else:
            # Página não encontrada
            render_page_not_found_error(page)
            return False
            
    except Exception as e:
        st.error(f"❌ Erro crítico no roteamento: {str(e)}")
        
        with st.expander("🔍 Detalhes do erro"):
            st.code(traceback.format_exc())
        
        return False

def render_page_execution_error(page: str, error: Exception):
    """Renderiza erro de execução da página"""
    st.error(f"❌ **Erro ao carregar a página {page.title()}**")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        ### 🚨 Problema Detectado
        
        A página **{page.title()}** não pôde ser carregada devido a um erro interno.
        
        **Erro:** `{str(error)}`
        
        **Soluções possíveis:**
        1. Recarregue a página (F5)
        2. Volte ao Dashboard e tente novamente
        3. Verifique se todos os arquivos estão no local correto
        """)
    
    with col2:
        st.markdown("### 🔧 Ações Rápidas")
        
        dashboard_key = SessionManager.generate_unique_key("error_go_dashboard")
        if st.button("🏠 Ir para Dashboard", key=dashboard_key, use_container_width=True, type="primary"):
            SessionManager.navigate_to_page('dashboard', clear_project=True)
        
        reload_key = SessionManager.generate_unique_key("error_reload")
        if st.button("🔄 Tentar Novamente", key=reload_key, use_container_width=True):
            st.rerun()
    
    # Detalhes técnicos em expander
    with st.expander("🔍 Detalhes Técnicos"):
        st.code(f"Página: {page}")
        st.code(f"Erro: {str(error)}")
        st.code(traceback.format_exc())

def render_page_not_found_error(page: str):
    """Renderiza erro de página não encontrada"""
    st.error(f"❌ **Página '{page}' não encontrada**")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        ### 📄 Página Indisponível
        
        A página **{page}** não foi encontrada ou não está disponível.
        
        **Páginas disponíveis:**
        - 🏠 Dashboard
        - 📁 Projetos  
        - 📋 DMAIC (requer projeto selecionado)
        - 📊 Relatórios
        - ❓ Ajuda
        """)
    
    with col2:
        st.markdown("### 🧭 Navegação")
        
        dashboard_key = SessionManager.generate_unique_key("notfound_dashboard")
        if st.button("🏠 Ir para Dashboard", key=dashboard_key, use_container_width=True, type="primary"):
            SessionManager.navigate_to_page('dashboard', clear_project=True)
        
        projects_key = SessionManager.generate_unique_key("notfound_projects")
        if st.button("📁 Ver Projetos", key=projects_key, use_container_width=True):
            SessionManager.navigate_to_page('projects')

def show_page_error(page_name: str, filename: str):
    """Mostra erro quando módulo da página não pode ser importado"""
    st.error(f"❌ **Módulo {page_name} não encontrado**")
    
    st.markdown(f"""
    ### 🚨 Problema de Configuração
    
    O arquivo **{filename}** não foi encontrado ou não pode ser importado.
    
    **Verifique:**
    - Se o arquivo existe na pasta `src/pages/` ou `pages/`
    - Se não há erros de sintaxe no arquivo
    - Se todas as dependências estão instaladas
    
    **Localização esperada:**
    - `src/pages/{filename}`
    - `pages/{filename}`
    """)
    
    dashboard_key = SessionManager.generate_unique_key(f"error_{filename}_dashboard")
    if st.button("🏠 Voltar ao Dashboard", key=dashboard_key, type="primary"):
        SessionManager.navigate_to_page('dashboard', clear_project=True)

def render_enhanced_sidebar_navigation():
    """Renderiza navegação na sidebar melhorada"""
    with st.sidebar:
        # Header do usuário
        render_user_header()
        
        st.divider()
        
        # Debug info (opcional)
        render_debug_section()
        
        # Navegação principal
        render_main_navigation_buttons()
        
        st.divider()
        
        # Projeto atual
        render_current_project_section()
        
        st.divider()
        
        # Logout
        render_logout_section()

def render_user_header():
    """Renderiza header do usuário na sidebar"""
    user_data = SessionManager.get_user_data()
    
    if user_data:
        st.markdown(f"### 👤 {user_data.get('name', 'Usuário')}")
        st.caption(f"📧 {user_data.get('email', 'email@exemplo.com')}")
        
        if user_data.get('company'):
            st.caption(f"🏢 {user_data['company']}")
    else:
        st.warning("⚠️ Dados do usuário não encontrados")

def render_debug_section():
    """Renderiza seção de debug (opcional)"""
    debug_key = SessionManager.generate_unique_key("debug_nav")
    if st.checkbox("🔍 Debug Info", key=debug_key):
        current_project = SessionManager.get_current_project()
        
        debug_info = {
            'Página atual': st.session_state.get('current_page', 'N/A'),
            'Projeto': current_project.get('name') if current_project else 'Nenhum',
            'Fase': SessionManager.get_current_phase(),
            'Autenticado': SessionManager.is_authenticated(),
            'Session keys': len(st.session_state)
        }
        
        for key, value in debug_info.items():
            st.caption(f"**{key}:** {value}")

def render_main_navigation_buttons():
    """Renderiza botões de navegação principal"""
    st.markdown("### 🧭 Navegação Principal")
    
    current_page = st.session_state.get('current_page', 'dashboard')
    
    # Configuração dos botões
    nav_buttons = [
        {
            'key': 'dashboard',
            'label': '🏠 Dashboard',
            'help': 'Visão geral dos projetos'
        },
        {
            'key': 'projects',
            'label': '📁 Projetos',
            'help': 'Gerenciar projetos Six Sigma'
        },
        {
            'key': 'reports',
            'label': '📋 Relatórios',
            'help': 'Gerar relatórios científicos'
        },
        {
            'key': 'help',
            'label': '❓ Ajuda',
            'help': 'Tutoriais e documentação'
        }
    ]
    
    # Renderizar botões
    for button_config in nav_buttons:
        button_key = SessionManager.generate_unique_key("nav_main", button_config['key'])
        button_type = "primary" if current_page == button_config['key'] else "secondary"
        
        if st.button(
            button_config['label'],
            key=button_key,
            use_container_width=True,
            help=button_config['help'],
            type=button_type
        ):
            # Navegar para a página
            clear_project = button_config['key'] not in ['dmaic']
            SessionManager.navigate_to_page(button_config['key'], clear_project=clear_project)

def render_current_project_section():
    """Renderiza seção do projeto atual"""
    current_project = SessionManager.get_current_project()
    
    st.markdown("### 📊 Projeto Atual")
    
    if current_project:
        render_project_info(current_project)
        render_dmaic_phases_navigation(current_project)
    else:
        render_no_project_info()

def render_project_info(project: Dict):
    """Renderiza informações do projeto atual"""
    project_name = project.get('name', 'Projeto sem nome')
    
    # Nome truncado para sidebar
    display_name = project_name[:25] + "..." if len(project_name) > 25 else project_name
    
    st.info(f"**{display_name}**")
    
    # Informações básicas
    col1, col2 = st.columns(2)
    
    with col1:
        expected_savings = project.get('expected_savings', 0)
        st.caption(f"💰 R$ {expected_savings:,.0f}")
    
    with col2:
        created_date = project.get('created_at', '')[:10] if project.get('created_at') else 'N/A'
        st.caption(f"📅 {created_date}")
    
    # Botão para fechar projeto
    close_key = SessionManager.generate_unique_key("close_project_sidebar")
    if st.button(
        "❌ Fechar Projeto",
        key=close_key,
        use_container_width=True,
        help="Voltar ao dashboard sem projeto selecionado"
    ):
        SessionManager.navigate_to_page('dashboard', clear_project=True)

def render_dmaic_phases_navigation(project: Dict):
    """Renderiza navegação das fases DMAIC na sidebar"""
    st.markdown("### 📋 Fases DMAIC")
    
    # Calcular progresso das fases
    phases_progress = calculate_phases_progress_optimized(project)
    current_phase = SessionManager.get_current_phase()
    
    # Configuração das fases
    phases = [
        {'key': 'define', 'name': 'Define', 'icon': '🎯'},
        {'key': 'measure', 'name': 'Measure', 'icon': '📊'},
        {'key': 'analyze', 'name': 'Analyze', 'icon': '🔍'},
        {'key': 'improve', 'name': 'Improve', 'icon': '⚡'},
        {'key': 'control', 'name': 'Control', 'icon': '🎮'}
    ]
    
    # Renderizar fases
    for phase in phases:
        render_phase_navigation_item(phase, phases_progress, current_phase)
    
    # Progresso geral
    render_overall_progress_sidebar(phases_progress)

def calculate_phases_progress_optimized(project: Dict) -> Dict[str, float]:
    """Calcula progresso das fases de forma otimizada"""
    progress = {}
    
    try:
        if HAS_NEW_UTILS:
            # Usar configuração centralizada
            for phase_enum in DMACPhase:
                phase_key = phase_enum.value
                phase_data = project.get(phase_key, {})
                progress[phase_key] = calculate_phase_completion_percentage(phase_data, phase_enum)
        else:
            # Fallback para cálculo manual
            phases = ['define', 'measure', 'analyze', 'improve', 'control']
            for phase in phases:
                phase_data = project.get(phase, {})
                progress[phase] = calculate_phase_completion_percentage(phase_data, phase)
    
    except Exception as e:
        # Em caso de erro, retornar valores padrão
        phases = ['define', 'measure', 'analyze', 'improve', 'control']
        progress = {phase: 0.0 for phase in phases}
    
    return progress

def render_phase_navigation_item(phase: Dict, phases_progress: Dict, current_phase: str):
    """Renderiza item individual da navegação de fases"""
    phase_key = phase['key']
    progress = phases_progress.get(phase_key, 0.0)
    is_current = current_phase == phase_key
    
    # Layout em colunas
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Botão da fase
        button_key = SessionManager.generate_unique_key("nav_dmaic", phase_key)
        button_type = "primary" if is_current else "secondary"
        
        if st.button(
            f"{phase['icon']} {phase['name']}",
            key=button_key,
            use_container_width=True,
            help=f"Ir para fase {phase['name']}",
            type=button_type,
            disabled=is_current
        ):
            # Navegar para a fase
            st.session_state.current_phase = phase_key
            st.session_state.current_dmaic_phase = phase_key  # Compatibilidade
            st.session_state.current_page = "dmaic"
            st.rerun()
    
    with col2:
        # Indicador de progresso
        if progress == 100:
            st.success("✅")
        elif progress >= 50:
            st.warning(f"{progress:.0f}%")
        elif progress > 0:
            st.info(f"{progress:.0f}%")
        else:
            st.error("⏳")

def render_overall_progress_sidebar(phases_progress: Dict):
    """Renderiza progresso geral na sidebar"""
    if phases_progress:
        overall_progress = sum(phases_progress.values()) / len(phases_progress)
        
        st.markdown("### 📈 Progresso Geral")
        st.progress(overall_progress / 100)
        st.caption(f"{overall_progress:.1f}% concluído")
        
        # Status baseado no progresso
        if overall_progress == 100:
            st.success("🎉 Projeto Completo!")
        elif overall_progress >= 75:
            st.info("🚀 Quase lá!")
        elif overall_progress >= 50:
            st.warning("⚡ Meio caminho!")
        elif overall_progress >= 25:
            st.info("🌱 Progredindo...")
        else:
            st.info("🏁 Começando...")

def render_no_project_info():
    """Renderiza informações quando não há projeto selecionado"""
    st.info("Nenhum projeto selecionado")
    
    st.markdown("""
    **Para criar um projeto:**
    1. Vá ao Dashboard
    2. Clique em "➕ Novo Projeto"
    3. Preencha as informações
    
    **Para selecionar um projeto:**
    1. Vá para Projetos
    2. Clique em "📊 Selecionar"
    """)

def render_logout_section():
    """Renderiza seção de logout"""
    logout_key = SessionManager.generate_unique_key("logout_sidebar")
    if st.button(
        "🚪 Logout",
        key=logout_key,
        use_container_width=True,
        type="secondary"
    ):
        # Confirmar logout
        if 'confirm_logout' not in st.session_state:
            st.session_state.confirm_logout = True
            st.warning("⚠️ Confirme o logout clicando novamente")
            st.rerun()
        else:
            # Fazer logout
            SessionManager.logout()

# Função principal para compatibilidade
def main():
    """Função principal para teste standalone"""
    show_main_navigation()

if __name__ == "__main__":
    main()
