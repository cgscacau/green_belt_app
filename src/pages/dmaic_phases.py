import streamlit as st
import time
from datetime import datetime

def show_dmaic_phase():
    """Página das fases DMAIC - Versão Corrigida"""
    
    # Debug: Verificar se chegou aqui
    st.write("🔍 Debug: Função show_dmaic_phase() foi chamada")
    
    current_phase = st.session_state.get('current_dmaic_phase', 'define')
    current_project = st.session_state.get('current_project')
    
    st.write(f"🔍 Debug: Fase atual = {current_phase}")
    st.write(f"🔍 Debug: Projeto carregado = {bool(current_project)}")
    
    if not current_project:
        st.error("❌ Nenhum projeto selecionado!")
        st.write("🔍 Debug: Projeto não encontrado no session_state")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🏠 Voltar ao Dashboard", key="back_dashboard_error", use_container_width=True, type="primary"):
                st.session_state.current_page = 'dashboard'
                st.write("🔍 Debug: Navegando para dashboard...")
                st.rerun()
        
        with col2:
            if st.button("📊 Ver Projetos", key="view_projects_error", use_container_width=True):
                st.session_state.current_page = 'dashboard'
                st.write("🔍 Debug: Navegando para dashboard...")
                st.rerun()
        return
    
    # Se chegou aqui, temos um projeto
    st.write(f"🔍 Debug: Projeto encontrado: {current_project.get('name')}")
    
    # Header da fase
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
    
    # Informações do projeto
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
                key=f"quick_nav_{phase}_{int(time.time())}",
                use_container_width=True,
                type=button_type,
                disabled=is_current
            ):
                st.session_state.current_dmaic_phase = phase
                st.write(f"🔍 Debug: Mudando para fase {phase}")
                st.rerun()
    
    st.divider()
    
    # Conteúdo específico da fase atual
    show_phase_content(current_phase, current_project)

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
    """Conteúdo da fase Define"""
    
    st.markdown("### 🎯 Fase Define (Definir)")
    
    st.markdown("""
    **Objetivo:** Definir claramente o problema, objetivos e escopo do projeto.
    
    **Nesta fase você deve:**
    - ✅ Criar o Project Charter
    - ✅ Identificar stakeholders
    - ✅ Capturar Voice of Customer (VOC)
    - ✅ Desenvolver diagrama SIPOC
    - ✅ Definir timeline detalhado
    """)
    
    # Ferramentas da fase Define
    st.markdown("### 🔧 Ferramentas Disponíveis")
    
    tool_col1, tool_col2, tool_col3 = st.columns(3)
    
    with tool_col1:
        if st.button("📋 Project Charter", use_container_width=True, key="charter_tool"):
            st.session_state.current_tool = 'charter'
            st.info("🚧 Ferramenta Project Charter será implementada na próxima atualização")
    
    with tool_col2:
        if st.button("👥 Stakeholders", use_container_width=True, key="stakeholders_tool"):
            st.session_state.current_tool = 'stakeholders'
            st.info("🚧 Ferramenta Stakeholders será implementada na próxima atualização")
    
    with tool_col3:
        if st.button("🗣️ Voice of Customer", use_container_width=True, key="voc_tool"):
            st.session_state.current_tool = 'voc'
            st.info("🚧 Ferramenta VOC será implementada na próxima atualização")
    
    # Progresso da fase Define
    st.markdown("### 📊 Progresso da Fase Define")
    
    # Simular progresso baseado nos dados do projeto
    define_data = project.get('define', {})
    total_tools = 5  # Charter, Stakeholders, VOC, SIPOC, Timeline
    completed_tools = sum(1 for tool_data in define_data.values() if isinstance(tool_data, dict) and tool_data.get('completed', False))
    
    progress = (completed_tools / total_tools) * 100
    
    st.progress(progress / 100)
    st.caption(f"Progresso: {progress:.1f}% ({completed_tools}/{total_tools} ferramentas concluídas)")
    
    # Lista de ferramentas e status
    st.markdown("### ✅ Status das Ferramentas")
    
    tools_status = [
        ("📋 Project Charter", define_data.get('charter', {}).get('completed', False)),
        ("👥 Stakeholders", define_data.get('stakeholders', {}).get('completed', False)),
        ("🗣️ Voice of Customer", define_data.get('voc', {}).get('completed', False)),
        ("📊 SIPOC", define_data.get('sipoc', {}).get('completed', False)),
        ("📅 Timeline", define_data.get('timeline', {}).get('completed', False))
    ]
    
    for tool_name, completed in tools_status:
        status_icon = "✅" if completed else "⏳"
        status_text = "Concluído" if completed else "Pendente"
        st.markdown(f"{status_icon} **{tool_name}** - {status_text}")
    
    # Próximos passos
    if progress < 100:
        st.markdown("### 🚀 Próximos Passos")
        st.info("""
        **Para avançar na fase Define:**
        
        1. 📋 Complete o Project Charter com objetivos claros
        2. 👥 Identifique todos os stakeholders relevantes
        3. 🗣️ Capture a Voice of Customer (VOC)
        4. 📊 Desenvolva o diagrama SIPOC
        5. 📅 Defina o timeline detalhado do projeto
        
        **Tempo estimado:** 2-3 semanas
        """)
    else:
        st.success("🎉 Parabéns! Fase Define concluída!")
        st.info("Você pode avançar para a fase **Measure** usando os botões acima.")

def show_measure_phase(project):
    """Conteúdo da fase Measure"""
    st.markdown("### 📏 Fase Measure (Medir)")
    st.info("🚧 Conteúdo da fase Measure será implementado na próxima etapa")

def show_analyze_phase(project):
    """Conteúdo da fase Analyze"""
    st.markdown("### 🔍 Fase Analyze (Analisar)")
    st.info("🚧 Conteúdo da fase Analyze será implementado em etapas futuras")

def show_improve_phase(project):
    """Conteúdo da fase Improve"""
    st.markdown("### ⚡ Fase Improve (Melhorar)")
    st.info("🚧 Conteúdo da fase Improve será implementado em etapas futuras")

def show_control_phase(project):
    """Conteúdo da fase Control"""
    st.markdown("### 🎛️ Fase Control (Controlar)")
    st.info("🚧 Conteúdo da fase Control será implementado em etapas futuras")
