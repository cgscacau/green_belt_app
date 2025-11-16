import streamlit as st
import time
from datetime import datetime
from src.pages.define_tools import show_define_tools


def show_dmaic_phase():
    """Página das fases DMAIC - Com navegação corrigida"""
    
    current_phase = st.session_state.get('current_dmaic_phase', 'define')
    current_project = st.session_state.get('current_project')
    
    if not current_project:
        st.error("❌ Nenhum projeto selecionado!")
        
        # Botões de retorno funcionais
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🏠 Voltar ao Dashboard", key="back_dashboard_no_project", use_container_width=True, type="primary"):
                st.session_state.current_page = 'dashboard'
                # Limpar dados de projeto se necessário
                if 'current_project' in st.session_state:
                    del st.session_state.current_project
                if 'current_dmaic_phase' in st.session_state:
                    del st.session_state.current_dmaic_phase
                st.rerun()
        
        with col2:
            if st.button("📊 Ver Projetos", key="view_projects_no_project", use_container_width=True):
                st.session_state.current_page = 'dashboard'
                st.rerun()
        return
    
    # Header da fase com botões de navegação
    col_header1, col_header2, col_header3 = st.columns([3, 1, 1])
    
    with col_header1:
        phase_icons = {
            'define': '🎯',
            'measure': '📏', 
            'analyze': '🔍',
            'improve': '⚡',
            'control': '🎛️'
        }
        
        phase_names = {
            'define': 'Define - Definir',
            'measure': 'Measure - Medir',
            'analyze': 'Analyze - Analisar', 
            'improve': 'Improve - Melhorar',
            'control': 'Control - Controlar'
        }
        
        icon = phase_icons.get(current_phase, '📋')
        name = phase_names.get(current_phase, current_phase.title())
        
        st.title(f"{icon} {name}")
        st.caption(f"Projeto: **{current_project.get('name', 'Sem nome')}**")
    
    with col_header2:
        if st.button("📊 Dashboard", key="return_dashboard", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.success("📊 Voltando ao Dashboard...")
            time.sleep(1)
            st.rerun()
    
    with col_header3:
        if st.button("❌ Fechar Projeto", key="close_project", use_container_width=True):
            # Limpar projeto atual
            if 'current_project' in st.session_state:
                del st.session_state.current_project
            if 'current_dmaic_phase' in st.session_state:
                del st.session_state.current_dmaic_phase
            st.session_state.current_page = 'dashboard'
            st.success("❌ Projeto fechado!")
            time.sleep(1)
            st.rerun()
    
    # Informações do projeto
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Economia Esperada", f"R$ {current_project.get('expected_savings', 0):,.2f}")
    
    with col2:
        created_date = current_project.get('created_at', '')[:10] if current_project.get('created_at') else 'N/A'
        st.metric("Criado em", created_date)
    
    with col3:
        st.metric("Status", current_project.get('status', 'active').title())
    
    st.divider()
    
    # Navegação entre fases
    st.markdown("### 🔄 Navegação entre Fases DMAIC")
    
    phase_buttons = st.columns(5)
    phases = ['define', 'measure', 'analyze', 'improve', 'control']
    
    for i, phase in enumerate(phases):
        with phase_buttons[i]:
            is_current = phase == current_phase
            button_type = "primary" if is_current else "secondary"
            
            if st.button(
                f"{phase_icons[phase]} {phase.title()}", 
                key=f"nav_phase_{phase}",
                use_container_width=True,
                type=button_type,
                disabled=is_current
            ):
                st.session_state.current_dmaic_phase = phase
                st.success(f"Mudando para fase {phase.title()}...")
                time.sleep(1)
                st.rerun()
    
    st.divider()
    
    # Conteúdo específico da fase atual
    show_phase_content(current_phase, current_project)
    
    # Botões de navegação no final da página
    st.divider()
    st.markdown("### 🧭 Navegação")
    
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
    
    with nav_col1:
        if st.button("🏠 Dashboard", key="bottom_dashboard", use_container_width=True, type="secondary"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    with nav_col2:
        if st.button("📋 Relatórios", key="bottom_reports", use_container_width=True, type="secondary"):
            st.session_state.current_page = 'reports'
            st.rerun()
    
    with nav_col3:
        if st.button("❓ Ajuda", key="bottom_help", use_container_width=True, type="secondary"):
            st.session_state.current_page = 'help'
            st.rerun()
    
    with nav_col4:
        if st.button("🔄 Atualizar", key="bottom_refresh", use_container_width=True, type="secondary"):
            st.rerun()

def show_phase_content(phase, project):
    """Mostra conteúdo específico de cada fase"""
    
    if phase == 'define':
        show_define_phase(project)
    elif phase == 'measure':
        show_measure_phase(project)
    elif phase == 'analyze':
        show_analyze_phase(project)
    elif phase == 'improve':
        show_improve_phase(project)
    elif phase == 'control':
        show_control_phase(project)
    else:
        st.error(f"Fase '{phase}' não reconhecida")

def show_define_phase(project):
    """Conteúdo da fase Define com ferramentas funcionais"""
    show_define_tools(project)
    
    st.markdown("### 🎯 Fase Define (Definir)")
    
    # Tabs para organizar o conteúdo
    tab1, tab2, tab3 = st.tabs(["📋 Visão Geral", "🔧 Ferramentas", "📊 Progresso"])
    
    with tab1:
        st.markdown("""
        **Objetivo:** Definir claramente o problema, objetivos e escopo do projeto.
        
        **Principais Atividades:**
        - ✅ Criar o Project Charter
        - ✅ Identificar e mapear stakeholders
        - ✅ Capturar Voice of Customer (VOC)
        - ✅ Desenvolver diagrama SIPOC
        - ✅ Definir timeline detalhado do projeto
        
        **Entregáveis:**
        - Project Charter aprovado
        - Mapa de stakeholders
        - Requisitos do cliente documentados
        - Processo mapeado (SIPOC)
        - Cronograma do projeto
        """)
        
        # Informações do projeto atual
        st.markdown("#### 📝 Informações do Projeto")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.markdown(f"""
            **Nome:** {project.get('name', 'N/A')}
            
            **Descrição:** {project.get('description', 'N/A')}
            
            **Economia Esperada:** R$ {project.get('expected_savings', 0):,.2f}
            """)
        
        with info_col2:
            st.markdown(f"""
            **Status:** {project.get('status', 'active').title()}
            
            **Data de Início:** {project.get('start_date', 'N/A')[:10] if project.get('start_date') else 'N/A'}
            
            **Data Alvo:** {project.get('target_end_date', 'N/A')[:10] if project.get('target_end_date') else 'N/A'}
            """)
    
    with tab2:
        st.markdown("### 🔧 Ferramentas da Fase Define")
        
        # Grid de ferramentas
        tool_col1, tool_col2, tool_col3 = st.columns(3)
        
        with tool_col1:
            st.markdown("#### 📋 Project Charter")
            st.markdown("Documento que define oficialmente o projeto")
            if st.button("🚀 Abrir Charter", key="open_charter", use_container_width=True, type="primary"):
                st.info("🚧 Ferramenta Project Charter será implementada na próxima atualização")
        
        with tool_col2:
            st.markdown("#### 👥 Stakeholders")
            st.markdown("Identificar pessoas impactadas pelo projeto")
            if st.button("👥 Mapear Stakeholders", key="open_stakeholders", use_container_width=True, type="primary"):
                st.info("🚧 Ferramenta Stakeholders será implementada na próxima atualização")
        
        with tool_col3:
            st.markdown("#### 🗣️ Voice of Customer")
            st.markdown("Capturar necessidades e expectativas")
            if st.button("🗣️ Capturar VOC", key="open_voc", use_container_width=True, type="primary"):
                st.info("🚧 Ferramenta VOC será implementada na próxima atualização")
        
        # Segunda linha de ferramentas
        tool_col4, tool_col5, tool_col6 = st.columns(3)
        
        with tool_col4:
            st.markdown("#### 📊 SIPOC")
            st.markdown("Mapeamento do processo atual")
            if st.button("📊 Criar SIPOC", key="open_sipoc", use_container_width=True, type="primary"):
                st.info("🚧 Ferramenta SIPOC será implementada na próxima atualização")
        
        with tool_col5:
            st.markdown("#### 📅 Timeline")
            st.markdown("Cronograma detalhado do projeto")
            if st.button("📅 Definir Timeline", key="open_timeline", use_container_width=True, type="primary"):
                st.info("🚧 Ferramenta Timeline será implementada na próxima atualização")
        
        with tool_col6:
            st.markdown("#### 📈 Métricas")
            st.markdown("Definir indicadores de sucesso")
            if st.button("📈 Definir Métricas", key="open_metrics", use_container_width=True, type="primary"):
                st.info("🚧 Ferramenta Métricas será implementada na próxima atualização")
    
    with tab3:
        st.markdown("### 📊 Progresso da Fase Define")
        
        # Calcular progresso baseado nos dados do projeto
        define_data = project.get('define', {})
        total_tools = 6  # Charter, Stakeholders, VOC, SIPOC, Timeline, Metrics
        completed_tools = sum(1 for tool_data in define_data.values() if isinstance(tool_data, dict) and tool_data.get('completed', False))
        
        progress = (completed_tools / total_tools) * 100
        
        # Mostrar progresso
        st.metric("Progresso Geral da Fase", f"{progress:.1f}%", f"{completed_tools}/{total_tools} ferramentas")
        st.progress(progress / 100)
        
        # Lista detalhada de status
        st.markdown("#### ✅ Status Detalhado das Ferramentas")
        
        tools_status = [
            ("📋 Project Charter", define_data.get('charter', {}).get('completed', False)),
            ("👥 Stakeholders", define_data.get('stakeholders', {}).get('completed', False)),
            ("🗣️ Voice of Customer", define_data.get('voc', {}).get('completed', False)),
            ("📊 SIPOC", define_data.get('sipoc', {}).get('completed', False)),
            ("📅 Timeline", define_data.get('timeline', {}).get('completed', False)),
            ("📈 Métricas", define_data.get('metrics', {}).get('completed', False))
        ]
        
        for tool_name, completed in tools_status:
            status_icon = "✅" if completed else "⏳"
            status_text = "Concluído" if completed else "Pendente"
            status_color = "green" if completed else "orange"
            
            col_status1, col_status2 = st.columns([3, 1])
            with col_status1:
                st.markdown(f"{status_icon} **{tool_name}**")
            with col_status2:
                st.markdown(f":{status_color}[{status_text}]")
        
        # Próximos passos
        if progress < 100:
            st.markdown("#### 🚀 Próximos Passos Recomendados")
            
            next_steps = []
            if not define_data.get('charter', {}).get('completed', False):
                next_steps.append("📋 Complete o Project Charter")
            if not define_data.get('stakeholders', {}).get('completed', False):
                next_steps.append("👥 Identifique os stakeholders")
            if not define_data.get('voc', {}).get('completed', False):
                next_steps.append("🗣️ Capture a Voice of Customer")
            
            for step in next_steps[:3]:  # Mostrar apenas os 3 primeiros
                st.info(f"• {step}")
            
            st.markdown("**Tempo estimado para conclusão:** 2-3 semanas")
        else:
            st.success("🎉 **Parabéns! Fase Define concluída com sucesso!**")
            st.info("✨ Você pode avançar para a fase **Measure** usando a navegação acima.")
            
            if st.button("➡️ Avançar para Measure", key="advance_measure", type="primary"):
                st.session_state.current_dmaic_phase = "measure"
                st.success("Avançando para fase Measure...")
                time.sleep(1)
                st.rerun()

def show_measure_phase(project):
    """Conteúdo da fase Measure com ferramentas funcionais"""
    from src.pages.measure_tools import show_measure_tools
    show_measure_tools(project)
    
    st.markdown("### 📏 Fase Measure (Medir)")
    
    st.info("""
    🚧 **Fase Measure em Desenvolvimento**
    
    Esta fase incluirá:
    - 📊 Plano de coleta de dados
    - 📈 Upload e análise de arquivos
    - 📋 Análise de sistema de medição (MSA)
    - 🎯 Estudos de capacidade do processo
    - 📐 Definição de métricas CTQ
    """)
    
    if st.button("⬅️ Voltar para Define", key="back_to_define", type="secondary"):
        st.session_state.current_dmaic_phase = "define"
        st.rerun()

def show_analyze_phase(project):
    """Mostrar fase Analyze"""
    from src.pages.analyze_tools import show_analyze_tools
    
    st.markdown("## 🔍 Analyze - Analisar")
    st.markdown("Identifique as causas raiz dos problemas através de análise estatística e ferramentas de qualidade.")
    
    # Verificar se a fase Measure foi concluída
    measure_data = project.get('measure', {})
    measure_completed = any(tool.get('completed', False) for tool in measure_data.values() if isinstance(tool, dict))
    
    if not measure_completed:
        st.warning("⚠️ Recomendamos completar pelo menos uma ferramenta da fase **Measure** antes de prosseguir")
    
    # Ferramentas da fase Analyze
    show_analyze_tools(project)

def show_phase_content(phase: str, project: Dict):
    """Mostrar conteúdo específico da fase"""
    
    if phase == "define":
        show_define_phase(project)
    elif phase == "measure":
        show_measure_phase(project)
    elif phase == "analyze":
        show_analyze_phase(project)  # Adicionar esta linha
    elif phase == "improve":
        st.info("🚧 Fase Improve em desenvolvimento")
    elif phase == "control":
        st.info("🚧 Fase Control em desenvolvimento")



def show_improve_phase(project):
    """Conteúdo da fase Improve"""
    st.markdown("### ⚡ Fase Improve (Melhorar)")
    st.info("🚧 Fase Improve será implementada em etapas futuras")

def show_control_phase(project):
    """Conteúdo da fase Control"""
    st.markdown("### 🎛️ Fase Control (Controlar)")
    st.info("🚧 Fase Control será implementada em etapas futuras")
