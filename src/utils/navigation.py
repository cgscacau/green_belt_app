import streamlit as st
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional

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
            DMACPhase.DEFINE: 5,    # Charter, Stakeholders, VOC, SIPOC, Timeline
            DMACPhase.MEASURE: 6,   # Plano coleta, Dados, MSA, Baseline, Capability, CTQ
            DMACPhase.ANALYZE: 7,   # Ishikawa, 5 Porquês, Pareto, Hipóteses, Testes, Root Cause, Priorização
            DMACPhase.IMPROVE: 5,   # Soluções, Plano Ação, Piloto, Implementação, Validação
            DMACPhase.CONTROL: 4    # Controles, SPC, Documentação, Handover
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
    
    def render_sidebar_navigation(self, current_project: Optional[Dict] = None):
        """Renderiza navegação na sidebar"""
        with st.sidebar:
            st.markdown("### 🧭 Navegação")
            
            # Navegação principal
            selected_page = st.selectbox(
                "Página Principal",
                options=list(self.main_pages.keys()),
                format_func=lambda x: f"{self.main_pages[x].icon} {self.main_pages[x].title}",
                index=0 if not st.session_state.get('current_page') else list(self.main_pages.keys()).index(st.session_state.get('current_page', 'dashboard'))
            )
            
            st.session_state.current_page = selected_page
            
            # Navegação DMAIC (apenas se projeto selecionado)
            if current_project:
                st.markdown("### 📋 Fases DMAIC")
                
                progress_data = self.get_dmaic_phase_progress(current_project)
                
                for phase in DMACPhase:
                    phase_info = self.dmaic_phases[phase]
                    progress = progress_data.get(phase.value, 0)
                    
                    # Botão da fase com progresso
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if st.button(
                            f"{phase_info.icon} {phase_info.title}",
                            key=f"nav_{phase.value}",
                            use_container_width=True,
                            help=phase_info.description
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
                st.info("Selecione um projeto para acessar as fases DMAIC")
