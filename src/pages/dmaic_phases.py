import streamlit as st
from typing import Dict, List
from datetime import datetime

def show_dmaic_phase():
    """Mostrar navegação entre fases DMAIC"""
    
    if 'current_project' not in st.session_state or not st.session_state.current_project:
        st.error("❌ Nenhum projeto selecionado")
        st.info("💡 Vá para a página de Projetos e selecione um projeto")
        return
    
    current_project = st.session_state.current_project
    project_name = current_project.get('name', 'Projeto')
    
    # Header da fase atual
    st.markdown(f"# 🎯 Projeto: {project_name}")
    
    # Navegação entre fases DMAIC
    st.markdown("## 🧭 Navegação entre Fases DMAIC")
    
    # Definir as fases
    phases = {
        "define": {"name": "Define", "icon": "🎯", "description": "Definir problema, objetivos e escopo"},
        "measure": {"name": "Measure", "icon": "📏", "description": "Medir e coletar dados do estado atual"},
        "analyze": {"name": "Analyze", "icon": "🔍", "description": "Analisar dados e identificar causas raiz"},
        "improve": {"name": "Improve", "icon": "⚡", "description": "Desenvolver e implementar soluções"},
        "control": {"name": "Control", "icon": "🎮", "description": "Controlar e sustentar melhorias"}
    }
    
    # Verificar progresso de cada fase
    phase_progress = {}
    for phase_key in phases.keys():
        phase_data = current_project.get(phase_key, {})
        if isinstance(phase_data, dict):
            completed_tools = sum(1 for tool_data in phase_data.values() 
                                if isinstance(tool_data, dict) and tool_data.get('completed', False))
            total_tools = len(phase_data) if phase_data else 5  # Assumir 5 ferramentas por fase
            progress = (completed_tools / total_tools * 100) if total_tools > 0 else 0
        else:
            progress = 0
        
        phase_progress[phase_key] = progress
    
    # Mostrar cards das fases
    cols = st.columns(5)
    
    for i, (phase_key, phase_info) in enumerate(phases.items()):
        with cols[i]:
            progress = phase_progress[phase_key]
            
            # Determinar cor baseada no progresso
            if progress == 100:
                color = "🟢"
            elif progress > 0:
                color = "🟡"
            else:
                color = "🔴"
            
            # Card da fase
            st.markdown(f"""
            <div style="
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 10px;
                text-align: center;
                margin: 5px;
                background-color: {'#e8f5e8' if progress == 100 else '#fff3cd' if progress > 0 else '#f8d7da'};
            ">
                <h3>{phase_info['icon']} {phase_info['name']}</h3>
                <p style="font-size: 12px; margin: 5px 0;">{phase_info['description']}</p>
                <p style="font-size: 14px; font-weight: bold;">{color} {progress:.0f}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão para navegar para a fase
            if st.button(f"Ir para {phase_info['name']}", key=f"goto_{phase_key}", use_container_width=True):
                st.session_state['current_phase'] = phase_key
                st.rerun()
    
    # Mostrar progresso geral do projeto
    st.divider()
    
    overall_progress = sum(phase_progress.values()) / len(phases)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.progress(overall_progress / 100)
        st.caption(f"Progresso Geral do Projeto: {overall_progress:.1f}%")
    
    with col2:
        if overall_progress == 100:
            st.success("🎉 Completo!")
        else:
            st.info(f"⏳ {overall_progress:.0f}%")
    
    # Determinar fase atual
    if 'current_phase' not in st.session_state:
        # Determinar fase automaticamente baseada no progresso
        for phase_key, progress in phase_progress.items():
            if progress < 100:
                st.session_state['current_phase'] = phase_key
                break
        else:
            st.session_state['current_phase'] = 'define'  # Default
    
    current_phase = st.session_state.get('current_phase', 'define')
    
    # Mostrar conteúdo da fase atual
    st.divider()
    show_phase_content(current_phase, current_project)


def show_phase_content(phase: str, project: Dict):
    """Mostrar conteúdo específico da fase"""
    
    if phase == "define":
        show_define_phase(project)
    elif phase == "measure":
        show_measure_phase(project)
    elif phase == "analyze":
        show_analyze_phase(project)
    elif phase == "improve":
        st.info("🚧 Fase Improve em desenvolvimento")
    elif phase == "control":
        st.info("🚧 Fase Control em desenvolvimento")


def show_define_phase(project: Dict):
    """Mostrar fase Define"""
    from src.pages.define_tools import show_define_tools
    
    st.markdown("## 🎯 Define - Definir")
    st.markdown("Defina claramente o problema, objetivos, escopo e equipe do projeto.")
    
    # Informações do projeto
    col1, col2, col3 = st.columns(3)
    
    with col1:
        expected_benefit = project.get('expected_benefit', 0)
        st.metric("Benefício Esperado", f"R$ {expected_benefit:,.2f}")
    
    with col2:
        created_at = project.get('created_at', '')
        if created_at:
            try:
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                st.metric("Criado em", date_obj.strftime('%d/%m/%Y'))
            except:
                st.metric("Criado em", "N/A")
        else:
            st.metric("Criado em", "N/A")
    
    with col3:
        status = project.get('status', 'Active')
        st.metric("Status", status)
    
    # Ferramentas da fase Define
    show_define_tools(project)


def show_measure_phase(project: Dict):
    """Mostrar fase Measure"""
    from src.pages.measure_tools import show_measure_tools
    
    st.markdown("## 📏 Measure - Medir")
    st.markdown("Meça o desempenho atual do processo e colete dados para análise.")
    
    # Verificar se a fase Define foi iniciada
    define_data = project.get('define', {})
    define_started = any(tool.get('completed', False) for tool in define_data.values() if isinstance(tool, dict))
    
    if not define_started:
        st.warning("⚠️ Recomendamos completar pelo menos o **Project Charter** na fase Define antes de prosseguir")
    
    # Ferramentas da fase Measure
    show_measure_tools(project)


def show_analyze_phase(project: Dict):
    """Mostrar fase Analyze"""
    from src.pages.analyze_tools import show_analyze_tools
    
    st.markdown("## 🔍 Analyze - Analisar")
    st.markdown("Identifique as causas raiz dos problemas através de análise estatística e ferramentas de qualidade.")
    
    # Verificar se a fase Measure foi concluída
    measure_data = project.get('measure', {})
    measure_completed = any(tool.get('completed', False) for tool in measure_data.values() if isinstance(tool, dict))
    
    if not measure_completed:
        st.warning("⚠️ Recomendamos completar pelo menos uma ferramenta da fase **Measure** antes de prosseguir")
    
    # Mostrar resumo dos dados disponíveis
    if f'uploaded_data_{project.get("id")}' in st.session_state:
        df = st.session_state[f'uploaded_data_{project.get("id")}']
        
        st.info(f"📊 **Dados Disponíveis:** {df.shape[0]} linhas, {df.shape[1]} colunas")
        
        numeric_cols = len(df.select_dtypes(include=['number']).columns)
        if numeric_cols > 0:
            st.success(f"✅ {numeric_cols} variáveis numéricas disponíveis para análise")
        else:
            st.warning("⚠️ Nenhuma variável numérica detectada - verifique o upload de dados")
    else:
        st.warning("⚠️ Nenhum dado carregado - faça upload na fase Measure")
    
    # Ferramentas da fase Analyze
    show_analyze_tools(project)


def show_improve_phase(project: Dict):
    """Mostrar fase Improve"""
    st.markdown("## ⚡ Improve - Melhorar")
    st.markdown("Desenvolva e implemente soluções para as causas raiz identificadas.")
    
    # Verificar se a fase Analyze foi concluída
    analyze_data = project.get('analyze', {})
    analyze_completed = any(tool.get('completed', False) for tool in analyze_data.values() if isinstance(tool, dict))
    
    if not analyze_completed:
        st.warning("⚠️ Complete a fase **Analyze** antes de desenvolver soluções")
    
    st.info("🚧 **Fase Improve em desenvolvimento**")
    
    st.markdown("""
    ### 🔧 Ferramentas que serão incluídas:
    
    - **💡 Geração de Soluções**: Brainstorming, SCAMPER, Design Thinking
    - **📊 Matriz de Priorização**: Esforço vs Impacto, Critérios múltiplos
    - **🧪 Teste Piloto**: Planejamento e execução de pilotos
    - **📈 Análise Custo-Benefício**: ROI das soluções propostas
    - **📋 Plano de Implementação**: Cronograma, responsáveis, recursos
    """)


def show_control_phase(project: Dict):
    """Mostrar fase Control"""
    st.markdown("## 🎮 Control - Controlar")
    st.markdown("Implemente controles para sustentar as melhorias alcançadas.")
    
    # Verificar se a fase Improve foi concluída
    improve_data = project.get('improve', {})
    improve_completed = any(tool.get('completed', False) for tool in improve_data.values() if isinstance(tool, dict))
    
    if not improve_completed:
        st.warning("⚠️ Complete a fase **Improve** antes de estabelecer controles")
    
    st.info("🚧 **Fase Control em desenvolvimento**")
    
    st.markdown("""
    ### 🎯 Ferramentas que serão incluídas:
    
    - **📊 Plano de Controle**: Sistema de monitoramento contínuo
    - **📈 Gráficos de Controle**: SPC para monitoramento estatístico
    - **📋 Procedimentos Padrão**: Documentação dos novos processos
    - **🎓 Plano de Treinamento**: Capacitação da equipe
    - **📊 Dashboard de KPIs**: Monitoramento visual dos resultados
    - **📝 Documentação Final**: Lições aprendidas e handover
    """)
