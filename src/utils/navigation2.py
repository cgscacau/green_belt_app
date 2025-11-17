"""
Gerenciador de navegação da aplicação
Versão melhorada com integração ao SessionManager e UX otimizada
"""

import streamlit as st
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import time
import logging

# Tentar importar utilitários melhorados
try:
    from src.utils.session_manager import SessionManager
    from src.config.dmaic_config import (
        DMAIC_PHASES_CONFIG, DMACPhase, get_phase_config, 
        calculate_phase_completion_percentage, validate_phase_data
    )
    HAS_NEW_UTILS = True
except ImportError:
    # Fallback para compatibilidade
    from enum import Enum
    
    class DMACPhase(Enum):
        DEFINE = "define"
        MEASURE = "measure"
        ANALYZE = "analyze"
        IMPROVE = "improve"
        CONTROL = "control"
    
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
    
    def calculate_phase_completion_percentage(phase_data, phase):
        if not isinstance(phase_data, dict):
            return 0.0
        tools_count = 5 if phase == 'define' else 4
        completed = sum(1 for tool_data in phase_data.values() 
                       if isinstance(tool_data, dict) and tool_data.get('completed', False))
        return (completed / tools_count) * 100 if tools_count > 0 else 0.0
    
    HAS_NEW_UTILS = False

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PageType(Enum):
    """Tipos de páginas da aplicação"""
    DASHBOARD = "dashboard"
    PROJECTS = "projects"
    DMAIC = "dmaic"
    REPORTS = "reports"
    HELP = "help"

@dataclass
class NavigationItem:
    """Item de navegação com configurações estendidas"""
    key: str
    title: str
    icon: str
    description: str
    enabled: bool = True
    requires_project: bool = False
    requires_auth: bool = True
    color: str = "#007bff"
    tooltip: Optional[str] = None

@dataclass
class BreadcrumbItem:
    """Item do breadcrumb"""
    label: str
    action: Optional[str] = None
    is_current: bool = False
    tooltip: Optional[str] = None
    icon: str = ""

class NavigationManager:
    """Gerenciador centralizado de navegação - Versão melhorada"""
    
    def __init__(self):
        """Inicializa o gerenciador de navegação"""
        # Gerar ID único da sessão para evitar conflitos
        self.session_id = self._generate_session_id()
        
        # Contador para chaves únicas
        self.key_counter = 0
        
        # Configuração das páginas principais
        self.main_pages = self._initialize_main_pages()
        
        # Configuração das fases DMAIC
        self.dmaic_phases = self._initialize_dmaic_phases()
        
        logger.info(f"NavigationManager inicializado com session_id: {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """Gera ID único da sessão"""
        timestamp = str(time.time())
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def _initialize_main_pages(self) -> Dict[str, NavigationItem]:
        """Inicializa configuração das páginas principais"""
        return {
            PageType.DASHBOARD.value: NavigationItem(
                key="dashboard",
                title="Dashboard",
                icon="🏠",
                description="Visão geral dos projetos e métricas",
                color="#28a745",
                tooltip="Página inicial com resumo de todos os projetos"
            ),
            PageType.PROJECTS.value: NavigationItem(
                key="projects",
                title="Projetos",
                icon="📊",
                description="Gerenciar projetos Six Sigma",
                color="#007bff",
                tooltip="Criar, editar e gerenciar projetos"
            ),
            PageType.DMAIC.value: NavigationItem(
                key="dmaic",
                title="DMAIC",
                icon="🎯",
                description="Executar metodologia DMAIC",
                requires_project=True,
                color="#dc3545",
                tooltip="Trabalhar nas fases do projeto selecionado"
            ),
            PageType.REPORTS.value: NavigationItem(
                key="reports",
                title="Relatórios",
                icon="📋",
                description="Gerar relatórios científicos",
                color="#ffc107",
                tooltip="Criar relatórios detalhados dos projetos"
            ),
            PageType.HELP.value: NavigationItem(
                key="help",
                title="Ajuda",
                icon="❓",
                description="Tutoriais e documentação",
                color="#6f42c1",
                tooltip="Guias, tutoriais e documentação"
            )
        }
    
    def _initialize_dmaic_phases(self) -> Dict[DMACPhase, NavigationItem]:
        """Inicializa configuração das fases DMAIC"""
        if HAS_NEW_UTILS:
            # Usar configuração centralizada
            phases = {}
            for phase_enum in DMACPhase:
                config = get_phase_config(phase_enum)
                phases[phase_enum] = NavigationItem(
                    key=config.key,
                    title=config.name,
                    icon=config.icon,
                    description=config.description,
                    requires_project=True,
                    color=config.color,
                    tooltip=f"Fase {config.name}: {config.description}"
                )
            return phases
        else:
            # Fallback para configuração manual
            return {
                DMACPhase.DEFINE: NavigationItem(
                    key="define",
                    title="Define",
                    icon="🎯",
                    description="Definir o problema e objetivos do projeto",
                    requires_project=True,
                    color="#e3f2fd",
                    tooltip="Primeira fase: definir problema, objetivos e escopo"
                ),
                DMACPhase.MEASURE: NavigationItem(
                    key="measure",
                    title="Measure",
                    icon="📏",
                    description="Medir o desempenho atual do processo",
                    requires_project=True,
                    color="#f3e5f5",
                    tooltip="Segunda fase: medir e coletar dados"
                ),
                DMACPhase.ANALYZE: NavigationItem(
                    key="analyze",
                    title="Analyze",
                    icon="🔍",
                    description="Analisar dados e identificar causas raiz",
                    requires_project=True,
                    color="#fff3e0",
                    tooltip="Terceira fase: analisar dados e encontrar causas"
                ),
                DMACPhase.IMPROVE: NavigationItem(
                    key="improve",
                    title="Improve",
                    icon="⚡",
                    description="Implementar soluções e melhorias",
                    requires_project=True,
                    color="#e8f5e8",
                    tooltip="Quarta fase: desenvolver e implementar soluções"
                ),
                DMACPhase.CONTROL: NavigationItem(
                    key="control",
                    title="Control",
                    icon="🎮",
                    description="Controlar e sustentar as melhorias",
                    requires_project=True,
                    color="#fce4ec",
                    tooltip="Quinta fase: controlar e sustentar melhorias"
                )
            }
    
    def generate_unique_key(self, base_key: str, suffix: Optional[str] = None) -> str:
        """Gera chave única para componentes Streamlit"""
        self.key_counter += 1
        timestamp = str(int(time.time() * 1000))[-4:]  # Últimos 4 dígitos
        
        if suffix:
            return f"{base_key}_{suffix}_{self.session_id}_{self.key_counter}_{timestamp}"
        else:
            return f"{base_key}_{self.session_id}_{self.key_counter}_{timestamp}"
    
    def can_access_page(self, page_key: str) -> Tuple[bool, Optional[str]]:
        """Verifica se o usuário pode acessar uma página"""
        if page_key not in self.main_pages:
            return False, f"Página '{page_key}' não existe"
        
        page_config = self.main_pages[page_key]
        
        # Verificar autenticação
        if page_config.requires_auth and not SessionManager.is_authenticated():
            return False, "Usuário não autenticado"
        
        # Verificar se requer projeto
        if page_config.requires_project and not SessionManager.get_current_project():
            return False, "Página requer projeto selecionado"
        
        # Verificar se está habilitada
        if not page_config.enabled:
            return False, "Página temporariamente indisponível"
        
        return True, None
    
    def render_top_navigation(self):
        """Renderiza navegação no topo da página - Versão melhorada"""
        try:
            current_page = st.session_state.get('current_page', 'dashboard')
            current_project = SessionManager.get_current_project()
            
            # Construir breadcrumb
            breadcrumb_items = self._build_breadcrumb(current_page, current_project)
            
            if len(breadcrumb_items) > 1:
                self._render_breadcrumb(breadcrumb_items)
            
            # Renderizar barra de status (opcional)
            self._render_status_bar()
            
        except Exception as e:
            logger.error(f"Erro ao renderizar navegação superior: {str(e)}")
            st.error("❌ Erro na navegação superior")
    
    def _build_breadcrumb(self, current_page: str, current_project: Optional[Dict]) -> List[BreadcrumbItem]:
        """Constrói lista de itens do breadcrumb"""
        items = []
        
        # Sempre incluir Dashboard
        items.append(BreadcrumbItem(
            label="🏠 Dashboard",
            action="go_dashboard",
            is_current=(current_page == 'dashboard'),
            tooltip="Voltar ao dashboard principal"
        ))
        
        # Adicionar itens baseados na página atual
        if current_page == 'projects':
            items.append(BreadcrumbItem(
                label="📊 Projetos",
                is_current=True,
                tooltip="Página de gerenciamento de projetos"
            ))
        
        elif current_page == 'dmaic':
            # Adicionar Projetos
            items.append(BreadcrumbItem(
                label="📊 Projetos",
                action="go_projects",
                tooltip="Voltar à lista de projetos"
            ))
            
            # Adicionar projeto atual
            if current_project:
                project_name = current_project.get('name', 'Projeto')
                truncated_name = self._truncate_text(project_name, 20)
                
                items.append(BreadcrumbItem(
                    label=f"📋 {truncated_name}",
                    action="stay_project",
                    tooltip=project_name if len(project_name) > 20 else None
                ))
                
                # Adicionar fase atual
                current_phase = SessionManager.get_current_phase()
                phase_info = self.dmaic_phases.get(DMACPhase(current_phase))
                
                if phase_info:
                    items.append(BreadcrumbItem(
                        label=f"{phase_info.icon} {phase_info.title}",
                        is_current=True,
                        tooltip=phase_info.description
                    ))
            else:
                items.append(BreadcrumbItem(
                    label="📋 DMAIC",
                    is_current=True,
                    tooltip="Metodologia DMAIC"
                ))
        
        elif current_page == 'reports':
            items.append(BreadcrumbItem(
                label="📋 Relatórios",
                is_current=True,
                tooltip="Geração de relatórios"
            ))
        
        elif current_page == 'help':
            items.append(BreadcrumbItem(
                label="❓ Ajuda",
                is_current=True,
                tooltip="Centro de ajuda e documentação"
            ))
        
        return items
    
    def _render_breadcrumb(self, items: List[BreadcrumbItem]):
        """Renderiza breadcrumb como botões funcionais"""
        st.markdown("**🧭 Navegação:**")
        
        # Criar colunas baseado no número de itens
        cols = st.columns(len(items))
        
        for i, (col, item) in enumerate(zip(cols, items)):
            with col:
                self._render_breadcrumb_button(item, i)
        
        st.markdown("---")
    
    def _render_breadcrumb_button(self, item: BreadcrumbItem, index: int):
        """Renderiza botão individual do breadcrumb"""
        # Configurar botão
        button_type = "secondary" if item.is_current else "primary"
        disabled = item.is_current or item.action is None
        
        # Gerar chave única
        button_key = self.generate_unique_key(f"breadcrumb_{index}", item.action or "current")
        
        # Renderizar botão
        if st.button(
            item.label,
            key=button_key,
            disabled=disabled,
            type=button_type,
            use_container_width=True,
            help=item.tooltip
        ):
            self._handle_breadcrumb_action(item.action)
    
    def _handle_breadcrumb_action(self, action: str):
        """Manipula ações dos botões do breadcrumb"""
        try:
            if action == 'go_dashboard':
                SessionManager.navigate_to_page('dashboard', clear_project=True)
            elif action == 'go_projects':
                SessionManager.navigate_to_page('projects', clear_project=True)
            elif action == 'stay_project':
                # Manter projeto mas resetar para Define
                st.session_state.current_phase = 'define'
                st.session_state.current_dmaic_phase = 'define'
                st.rerun()
            else:
                logger.warning(f"Ação de breadcrumb desconhecida: {action}")
        
        except Exception as e:
            logger.error(f"Erro ao executar ação do breadcrumb '{action}': {str(e)}")
            st.error(f"❌ Erro na navegação: {str(e)}")
    
    def _render_status_bar(self):
        """Renderiza barra de status opcional"""
        if st.checkbox("ℹ️ Mostrar Status", key=self.generate_unique_key("show_status")):
            current_project = SessionManager.get_current_project()
            user_data = SessionManager.get_user_data()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                auth_status = "✅ Logado" if SessionManager.is_authenticated() else "❌ Deslogado"
                st.caption(f"**Status:** {auth_status}")
            
            with col2:
                user_name = user_data.get('name', 'N/A') if user_data else 'N/A'
                st.caption(f"**Usuário:** {user_name}")
            
            with col3:
                project_name = current_project.get('name', 'Nenhum') if current_project else 'Nenhum'
                project_display = self._truncate_text(project_name, 15)
                st.caption(f"**Projeto:** {project_display}")
            
            with col4:
                current_phase = SessionManager.get_current_phase()
                st.caption(f"**Fase:** {current_phase.title()}")
            
            st.markdown("---")
    
    def render_sidebar_navigation(self, current_project: Optional[Dict] = None):
        """Renderiza navegação na sidebar - Versão melhorada"""
        with st.sidebar:
            try:
                # Header do usuário
                self._render_user_section()
                
                st.divider()
                
                # Navegação principal
                self._render_main_navigation_section()
                
                st.divider()
                
                # Seção do projeto atual
                self._render_project_section(current_project)
                
                st.divider()
                
                # Seção de utilitários
                self._render_utilities_section()
                
                st.divider()
                
                # Logout
                self._render_logout_section()
                
            except Exception as e:
                logger.error(f"Erro ao renderizar sidebar: {str(e)}")
                st.error("❌ Erro na navegação lateral")
    
    def _render_user_section(self):
        """Renderiza seção do usuário na sidebar"""
        user_data = SessionManager.get_user_data()
        
        if user_data:
            name = user_data.get('name', 'Usuário')
            email = user_data.get('email', '')
            company = user_data.get('company', '')
            
            st.markdown(f"### 👤 {name}")
            
            if email:
                st.caption(f"📧 {email}")
            
            if company:
                st.caption(f"🏢 {company}")
        else:
            st.warning("⚠️ Dados do usuário não encontrados")
    
    def _render_main_navigation_section(self):
        """Renderiza seção de navegação principal"""
        st.markdown("### 🧭 Navegação Principal")
        
        current_page = st.session_state.get('current_page', 'dashboard')
        
        # Renderizar botões das páginas principais
        for page_key, page_config in self.main_pages.items():
            self._render_navigation_button(page_config, current_page)
    
    def _render_navigation_button(self, page_config: NavigationItem, current_page: str):
        """Renderiza botão de navegação individual"""
        # Verificar se pode acessar a página
        can_access, error_msg = self.can_access_page(page_config.key)
        
        # Configurar botão
        is_current = current_page == page_config.key
        button_type = "primary" if is_current else "secondary"
        disabled = not can_access or is_current
        
        # Tooltip personalizado
        tooltip = page_config.tooltip
        if not can_access and error_msg:
            tooltip = f"❌ {error_msg}"
        elif is_current:
            tooltip = f"📍 Página atual: {page_config.description}"
        
        # Gerar chave única
        button_key = self.generate_unique_key("nav_main", page_config.key)
        
        # Renderizar botão
        if st.button(
            f"{page_config.icon} {page_config.title}",
            key=button_key,
            use_container_width=True,
            help=tooltip,
            type=button_type,
            disabled=disabled
        ):
            # Navegar para a página
            clear_project = not page_config.requires_project
            SessionManager.navigate_to_page(page_config.key, clear_project=clear_project)
    
    def _render_project_section(self, current_project: Optional[Dict]):
        """Renderiza seção do projeto atual"""
        st.markdown("### 📊 Projeto Atual")
        
        if current_project:
            self._render_current_project_info(current_project)
            self._render_dmaic_navigation(current_project)
        else:
            self._render_no_project_info()
    
    def _render_current_project_info(self, project: Dict):
        """Renderiza informações do projeto atual"""
        project_name = project.get('name', 'Projeto sem nome')
        display_name = self._truncate_text(project_name, 25)
        
        st.info(f"**{display_name}**")
        
        # Informações em colunas
        col1, col2 = st.columns(2)
        
        with col1:
            savings = project.get('expected_savings', 0)
            st.caption(f"💰 R$ {savings:,.0f}")
        
        with col2:
            created_date = project.get('created_at', '')[:10] if project.get('created_at') else 'N/A'
            st.caption(f"📅 {created_date}")
        
        # Status do projeto
        status = project.get('status', 'active')
        status_config = {
            'active': {'icon': '🟢', 'text': 'Ativo'},
            'completed': {'icon': '✅', 'text': 'Concluído'},
            'paused': {'icon': '⏸️', 'text': 'Pausado'}
        }
        
        status_info = status_config.get(status, status_config['active'])
        st.caption(f"**Status:** {status_info['icon']} {status_info['text']}")
        
        # Botão para fechar projeto
        close_key = self.generate_unique_key("close_project")
        if st.button(
            "❌ Fechar Projeto",
            key=close_key,
            use_container_width=True,
            help="Voltar ao dashboard sem projeto selecionado"
        ):
            SessionManager.navigate_to_page('dashboard', clear_project=True)
    
    def _render_dmaic_navigation(self, project: Dict):
        """Renderiza navegação das fases DMAIC"""
        st.markdown("### 📋 Fases DMAIC")
        
        # Calcular progresso das fases
        phases_progress = self.get_dmaic_phase_progress(project)
        current_phase = SessionManager.get_current_phase()
        
        # Renderizar cada fase
        for phase_enum, phase_config in self.dmaic_phases.items():
            self._render_dmaic_phase_button(
                phase_enum, phase_config, phases_progress, current_phase
            )
        
        # Progresso geral
        self._render_overall_progress(phases_progress)
    
    def _render_dmaic_phase_button(
        self, 
        phase_enum: DMACPhase, 
        phase_config: NavigationItem, 
        phases_progress: Dict[str, float], 
        current_phase: str
    ):
        """Renderiza botão individual da fase DMAIC"""
        phase_key = phase_enum.value
        progress = phases_progress.get(phase_key, 0.0)
        is_current = current_phase == phase_key
        
        # Layout em colunas
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Botão da fase
            button_key = self.generate_unique_key("nav_dmaic", phase_key)
            button_type = "primary" if is_current else "secondary"
            
            if st.button(
                f"{phase_config.icon} {phase_config.title}",
                key=button_key,
                use_container_width=True,
                help=phase_config.tooltip,
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
            self._render_progress_indicator(progress)
    
    def _render_progress_indicator(self, progress: float):
        """Renderiza indicador de progresso"""
        if progress == 100:
            st.success("✅")
        elif progress >= 75:
            st.info("🔷")
        elif progress >= 50:
            st.warning("🔶")
        elif progress >= 25:
            st.warning("🔸")
        elif progress > 0:
            st.info("🔹")
        else:
            st.error("⏳")
    
    def _render_overall_progress(self, phases_progress: Dict[str, float]):
        """Renderiza progresso geral do projeto"""
        if phases_progress:
            overall_progress = sum(phases_progress.values()) / len(phases_progress)
            
            st.markdown("### 📈 Progresso Geral")
            st.progress(overall_progress / 100)
            st.caption(f"{overall_progress:.1f}% concluído")
            
            # Estatísticas rápidas
            completed_phases = sum(1 for p in phases_progress.values() if p == 100)
            in_progress_phases = sum(1 for p in phases_progress.values() if 0 < p < 100)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Completas", f"{completed_phases}/5")
            with col2:
                st.metric("Em Progresso", in_progress_phases)
    
    def _render_no_project_info(self):
        """Renderiza informações quando não há projeto selecionado"""
        st.info("Nenhum projeto selecionado")
        
        st.markdown("""
        **Para trabalhar com DMAIC:**
        1. Vá ao Dashboard
        2. Selecione um projeto existente
        3. Ou crie um novo projeto
        
        **Páginas disponíveis:**
        - 🏠 Dashboard
        - 📊 Projetos
        - 📋 Relatórios
        - ❓ Ajuda
        """)
    
    def _render_utilities_section(self):
        """Renderiza seção de utilitários"""
        if st.checkbox("🔧 Utilitários", key=self.generate_unique_key("show_utilities")):
            
            # Limpar cache
            if st.button("🗑️ Limpar Cache", key=self.generate_unique_key("clear_cache")):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.success("✅ Cache limpo!")
                time.sleep(1)
                st.rerun()
            
            # Informações de debug
            if st.button("🔍 Debug Info", key=self.generate_unique_key("debug_info")):
                debug_info = {
                    'Session ID': self.session_id,
                    'Key Counter': self.key_counter,
                    'Current Page': st.session_state.get('current_page', 'N/A'),
                    'Session Keys': len(st.session_state),
                    'Authenticated': SessionManager.is_authenticated()
                }
                
                st.json(debug_info)
    
    def _render_logout_section(self):
        """Renderiza seção de logout"""
        logout_key = self.generate_unique_key("logout_sidebar")
        
        if st.button(
            "🚪 Logout",
            key=logout_key,
            use_container_width=True,
            type="secondary"
        ):
            # Sistema de confirmação
            if not hasattr(st.session_state, 'confirm_logout'):
                st.session_state.confirm_logout = True
                st.warning("⚠️ Clique novamente para confirmar logout")
                st.rerun()
            else:
                # Executar logout
                try:
                    SessionManager.logout()
                except Exception as e:
                    logger.error(f"Erro no logout: {str(e)}")
                    st.error("❌ Erro no logout")
    
    def get_dmaic_phase_progress(self, project_data: Dict) -> Dict[str, float]:
        """Calcula o progresso de cada fase DMAIC - Versão otimizada"""
        progress = {}
        
        try:
            if HAS_NEW_UTILS:
                # Usar configuração centralizada
                for phase_enum in DMACPhase:
                    phase_key = phase_enum.value
                    phase_data = project_data.get(phase_key, {})
                    progress[phase_key] = calculate_phase_completion_percentage(phase_data, phase_enum)
            else:
                # Fallback para cálculo manual
                for phase_enum in DMACPhase:
                    phase_key = phase_enum.value
                    phase_data = project_data.get(phase_key, {})
                    progress[phase_key] = calculate_phase_completion_percentage(phase_data, phase_key)
        
        except Exception as e:
            logger.error(f"Erro ao calcular progresso das fases: {str(e)}")
            # Retornar progresso zerado em caso de erro
            progress = {phase.value: 0.0 for phase in DMACPhase}
        
        return progress
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Trunca texto se exceder o comprimento máximo"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def get_navigation_state(self) -> Dict[str, Any]:
        """Retorna estado atual da navegação para debug"""
        current_project = SessionManager.get_current_project()
        
        return {
            'session_id': self.session_id,
            'key_counter': self.key_counter,
            'current_page': st.session_state.get('current_page'),
            'current_project_id': current_project.get('id') if current_project else None,
            'current_phase': SessionManager.get_current_phase(),
            'authenticated': SessionManager.is_authenticated(),
            'session_keys_count': len(st.session_state)
        }

# Instância global para facilitar uso
navigation_manager = NavigationManager()

# Funções de conveniência para compatibilidade
def render_top_navigation():
    """Função de conveniência para navegação superior"""
    navigation_manager.render_top_navigation()

def render_sidebar_navigation(current_project: Optional[Dict] = None):
    """Função de conveniência para navegação lateral"""
    navigation_manager.render_sidebar_navigation(current_project)

def generate_unique_key(base_key: str, suffix: Optional[str] = None) -> str:
    """Função de conveniência para gerar chaves únicas"""
    return navigation_manager.generate_unique_key(base_key, suffix)

# Função principal para compatibilidade
def main():
    """Função principal para teste standalone"""
    st.title("🧭 Navigation Manager Test")
    
    # Simular dados para teste
    if 'test_project' not in st.session_state:
        st.session_state.test_project = {
            'id': 'test123',
            'name': 'Projeto de Teste',
            'created_at': '2024-01-01',
            'expected_savings': 50000,
            'status': 'active'
        }
    
    # Renderizar navegação
    render_top_navigation()
    render_sidebar_navigation(st.session_state.test_project)
    
    # Mostrar estado
    st.json(navigation_manager.get_navigation_state())

if __name__ == "__main__":
    main()
