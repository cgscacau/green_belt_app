import streamlit as st
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
import hashlib
import time

class DMACPhase(Enum):
    DEFINE = "define"
    MEASURE = "measure"
    ANALYZE = "analyze"
    IMPROVE = "improve"
    CONTROL = "control"

@dataclass
class NavigationItem:
    key: str
    title: str
    icon: str
    description: str
    enabled: bool = True

class NavigationManager:
    def __init__(self):
        # Gerar timestamp único para evitar conflitos de chaves
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        
        self.dmaic_phases = {
            DMACPhase.DEFINE: NavigationItem(
                key="define",
                title="Define",
                icon="🎯",
                description="Definir o problema e objetivos do projeto"
            ),
            DMACPhase.MEASURE: NavigationItem(
                key="measure",
                title="Measure",
                icon="📏",
                description="Medir o desempenho atual do processo"
            ),
            DMACPhase.ANALYZE: NavigationItem(
                key="analyze",
                title="Analyze",
                icon="🔍",
                description="Analisar dados e identificar causas raiz"
            ),
            DMACPhase.IMPROVE: NavigationItem(
                key="improve",
                title="Improve",
                icon="⚡",
                description="Implementar soluções e melhorias"
            ),
            DMACPhase.CONTROL: NavigationItem(
                key="control",
                title="Control",
                icon="🎛️",
                description="Controlar e sustentar as melhorias"
            )
        }
        
        self.main_pages = {
            "dashboard": NavigationItem(
                key="dashboard",
                title="Dashboard",
                icon="🏠",
                description="Visão geral dos projetos"
            ),
            "projects": NavigationItem(
                key="projects",
                title="Projetos",
                icon="📊",
                description="Gerenciar projetos Six Sigma"
            ),
            "reports": NavigationItem(
                key="reports",
                title="Relatórios",
                icon="📋",
                description="Gerar relatórios científicos"
            ),
            "help": NavigationItem(
                key="help",
                title="Ajuda",
                icon="❓",
                description="Tutoriais e documentação"
            )
        }
    
    def _generate_unique_key(self, base_key: str) -> str:
        """Gera uma chave única para elementos Streamlit"""
        return f"{base_key}_{self.session_id}_{st.session_state.get('nav_counter', 0)}"
    
    def _increment_counter(self):
        """Incrementa contador para garantir chaves únicas"""
        if 'nav_counter' not in st.session_state:
            st.session_state.nav_counter = 0
        st.session_state.nav_counter += 1
    
    def render_top_navigation(self):
        """Renderiza navegação no topo da página"""
        current_page = st.session_state.get('current_page', 'dashboard')
        current_project = st.session_state.get('current_project')
        
        # Container para navegação
        with st.container():
            # Breadcrumb navigation
            breadcrumb_items = []
            breadcrumb_actions = []
            
            if current_page == 'dashboard':
                breadcrumb_items = ["🏠 Dashboard"]
                breadcrumb_actions = [None]
            elif current_page == 'projects':
                breadcrumb_items = ["🏠 Dashboard", "📊 Projetos"]
                breadcrumb_actions = ['dashboard', None]
            elif current_page == 'dmaic':
                if current_project:
                    phase = st.session_state.get('current_dmaic_phase', 'define').title()
                    phase_icon = self.dmaic_phases[DMACPhase(st.session_state.get('current_dmaic_phase', 'define'))].icon
                    breadcrumb_items = [
                        "🏠 Dashboard", 
                        "📊 Projetos", 
                        f"📋 {current_project.get('name', 'Projeto')[:20]}", 
                        f"{phase_icon} {phase}"
                    ]
                    breadcrumb_actions = ['dashboard', 'dashboard', 'dmaic_project', None]
                else:
                    breadcrumb_items = ["🏠 Dashboard", "📊 Projetos", "📋 DMAIC"]
                    breadcrumb_actions = ['dashboard', 'dashboard', None]
            elif current_page == 'reports':
                breadcrumb_items = ["🏠 Dashboard", "📋 Relatórios"]
                breadcrumb_actions = ['dashboard', None]
            elif current_page == 'help':
                breadcrumb_items = ["🏠 Dashboard", "❓ Ajuda"]
                breadcrumb_actions = ['dashboard', None]
            
            # Renderizar breadcrumb com links clicáveis
            if len(breadcrumb_items) > 1:
                # Usar texto simples para breadcrumb para evitar conflitos de chaves
                breadcrumb_text = " → ".join(breadcrumb_items)
                st.markdown(f"**Navegação:** {breadcrumb_text}")
                
                # Botões de navegação rápida
                if len(breadcrumb_items) > 1:
                    cols = st.columns(len(breadcrumb_items))
                    
                    for i, (item, action) in enumerate(zip(breadcrumb_items, breadcrumb_actions)):
                        if action and i < len(breadcrumb_items) - 1:  # Não mostrar botão para item atual
                            with cols[i]:
                                self._increment_counter()
                                if st.button(
                                    item, 
                                    key=self._generate_unique_key(f"breadcrumb_{i}_{action}"),
                                    use_container_width=True,
                                    help=f"Ir para {item}"
                                ):
                                    if action == 'dashboard':
                                        st.session_state.current_page = 'dashboard'
                                        if 'current_project' in st.session_state:
                                            del st.session_state.current_project
                                    elif action == 'dmaic_project':
                                        st.session_state.current_page = 'dmaic'
                                        st.session_state.current_dmaic_phase = 'define'
                                    st.rerun()
            
            st.divider()
    
    def render_sidebar_navigation(self, current_project: Optional[Dict] = None):
        """Renderiza navegação na sidebar"""
        with st.sidebar:
            # Informações do usuário
            user_data = st.session_state.get('user_data', {})
            st.markdown(f"### 👤 {user_data.get('name', 'Usuário')}")
            if user_data.get('company'):
                st.caption(f"🏢 {user_data.get('company')}")
            
            st.divider()
            
            # Navegação principal
            st.markdown("### 🧭 Navegação Principal")
            
            # Botões de navegação principal
            nav_buttons = [
                ("dashboard", "🏠 Dashboard", "Visão geral"),
                ("projects", "📊 Projetos", "Gerenciar projetos"),
                ("reports", "📋 Relatórios", "Gerar relatórios"),
                ("help", "❓ Ajuda", "Tutoriais e ajuda")
            ]
            
            current_page = st.session_state.get('current_page', 'dashboard')
            
            for page_key, button_text, help_text in nav_buttons:
                self._increment_counter()
                button_type = "primary" if current_page == page_key else "secondary"
                
                if st.button(
                    button_text, 
                    key=self._generate_unique_key(f"nav_main_{page_key}"),
                    use_container_width=True,
                    help=help_text,
                    type=button_type
                ):
                    st.session_state.current_page = page_key
                    # Limpar projeto atual se não for página DMAIC
                    if page_key != 'dmaic' and 'current_project' in st.session_state:
                        del st.session_state.current_project
                    st.rerun()
            
            st.divider()
            
            # Projeto atual
            if current_project:
                st.markdown("### 📋 Projeto Atual")
                project_name = current_project.get('name', 'Sem nome')
                st.info(f"**{project_name[:25]}{'...' if len(project_name) > 25 else ''}**")
                
                # Botão para fechar projeto
                self._increment_counter()
                if st.button(
                    "❌ Fechar Projeto", 
                    key=self._generate_unique_key("close_project"),
                    use_container_width=True
                ):
                    if 'current_project' in st.session_state:
                        del st.session_state.current_project
                    if 'current_dmaic_phase' in st.session_state:
                        del st.session_state.current_dmaic_phase
                    st.session_state.current_page = 'dashboard'
                    st.rerun()
                
                st.divider()
                
                # Navegação DMAIC
                st.markdown("### 📋 Fases DMAIC")
                
                progress_data = self.get_dmaic_phase_progress(current_project)
                current_dmaic_phase = st.session_state.get('current_dmaic_phase', 'define')
                
                for phase in DMACPhase:
                    phase_info = self.dmaic_phases[phase]
                    progress = progress_data.get(phase.value, 0)
                    
                    # Estilo do botão baseado no status
                    is_current = current_dmaic_phase == phase.value
                    button_type = "primary" if is_current else "secondary"
                    
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        self._increment_counter()
                        if st.button(
                            f"{phase_info.icon} {phase_info.title}",
                            key=self._generate_unique_key(f"nav_dmaic_{phase.value}"),
                            use_container_width=True,
                            help=phase_info.description,
                            type=button_type,
                            disabled=is_current
                        ):
                            st.session_state.current_dmaic_phase = phase.value
                            st.session_state.current_page = "dmaic"
                            st.rerun()
                    
                    with col2:
                        # Indicador de progresso
                        if progress == 100:
                            st.success("✅")
                        elif progress > 0:
                            st.warning(f"{progress:.0f}%")
                        else:
                            st.info("⏳")
                
                # Progresso geral do projeto
                overall_progress = sum(progress_data.values()) / len(progress_data)
                st.markdown("### 📈 Progresso Geral")
                st.progress(overall_progress / 100)
                st.caption(f"{overall_progress:.1f}% concluído")
            
            else:
                st.markdown("### 📋 Projeto")
                st.info("Nenhum projeto selecionado")
                self._increment_counter()
                if st.button(
                    "➕ Criar Projeto", 
                    key=self._generate_unique_key("create_project_sidebar"),
                    use_container_width=True
                ):
                    st.session_state.current_page = 'dashboard'
                    st.session_state.show_create_project = True
                    st.rerun()
            
            st.divider()
            
            # Botão de logout
            self._increment_counter()
            if st.button(
                "🚪 Logout", 
                key=self._generate_unique_key("logout_sidebar"),
                use_container_width=True, 
                type="secondary"
            ):
                from src.auth.firebase_auth import FirebaseAuth
                auth = FirebaseAuth()
                auth.logout_user()
                st.rerun()
    
    def get_dmaic_phase_progress(self, project_data: Dict) -> Dict[str, float]:
        """Calcula o progresso de cada fase DMAIC"""
        progress = {}
        
        for phase in DMACPhase:
            phase_data = project_data.get(phase.value, {})
            total_steps = self._get_phase_total_steps(phase)
            completed_steps = self._count_completed_steps(phase_data)
            progress[phase.value] = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        return progress
    
    def _get_phase_total_steps(self, phase: DMACPhase) -> int:
        """Retorna o número total de etapas por fase"""
        steps_count = {
            DMACPhase.DEFINE: 5,
            DMACPhase.MEASURE: 6,
            DMACPhase.ANALYZE: 7,
            DMACPhase.IMPROVE: 5,
            DMACPhase.CONTROL: 4
        }
        return steps_count.get(phase, 1)
    
    def _count_completed_steps(self, phase_data: Dict) -> int:
        """Conta etapas completadas em uma fase"""
        completed = 0
        for key, value in phase_data.items():
            if isinstance(value, dict) and value.get('completed', False):
                completed += 1
            elif isinstance(value, (str, list)) and value:
                completed += 1
        return completed
