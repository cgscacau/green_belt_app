import streamlit as st
from typing import Dict, List
from datetime import datetime

# Importações das ferramentas das fases
try:
    from src.pages.improve_tools import show_improve_phase as show_improve_tools
except ImportError:
    try:
        from pages.improve_tools import show_improve_phase as show_improve_tools
    except ImportError:
        def show_improve_tools():
            st.error("❌ Módulo improve_tools não encontrado")
            st.info("Verifique se o arquivo improve_tools.py existe na pasta pages")

# ✅ ADICIONAR ESTE IMPORT
try:
    from src.pages.control_tools import show_control_phase as show_control_tools
except ImportError:
    try:
        from pages.control_tools import show_control_phase as show_control_tools
    except ImportError:
        def show_control_tools():
            st.error("❌ Módulo control_tools não encontrado")
            st.info("Verifique se o arquivo control_tools.py existe na pasta pages")


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
    
    # Definir configuração das fases com ferramentas corretas
    phases_config = {
        "define": {
            "name": "Define", 
            "icon": "🎯", 
            "description": "Definir problema, objetivos e escopo",
            "tools": ["charter", "stakeholders", "voc", "sipoc", "timeline"]
        },
        "measure": {
            "name": "Measure", 
            "icon": "📏", 
            "description": "Medir e coletar dados do estado atual",
            "tools": ["data_collection_plan", "file_upload", "baseline_data", "msa", "process_capability"]
        },
        "analyze": {
            "name": "Analyze", 
            "icon": "🔍", 
            "description": "Analisar dados e identificar causas raiz",
            "tools": ["statistical_analysis", "root_cause_analysis"]
        },

        "improve": {
            "name": "Improve", 
            "icon": "⚡", 
            "description": "Desenvolver e implementar soluções",
            "tools": ["solution_development", "action_plan", "pilot_implementation", "full_implementation"]
        },
        "control": {
            "name": "Control", 
            "icon": "🎮", 
            "description": "Controlar e sustentar melhorias",
            "tools": ["control_plan", "monitoring_system", "documentation", "sustainability_plan"]
        }
    }


        
    # Calcular progresso de cada fase
    phase_progress = {}
    for phase_key, phase_config in phases_config.items():
        phase_data = current_project.get(phase_key, {})
        
        if isinstance(phase_data, dict) and phase_data:
            # Contar ferramentas concluídas
            completed_tools = 0
            total_tools = len(phase_config["tools"])
            
            for tool_name in phase_config["tools"]:
                tool_data = phase_data.get(tool_name, {})
                if isinstance(tool_data, dict) and tool_data.get('completed', False):
                    completed_tools += 1
            
            # Calcular progresso
            progress = (completed_tools / total_tools * 100) if total_tools > 0 else 0
        else:
            progress = 0
        
        phase_progress[phase_key] = progress
    
    # Mostrar cards das fases
    cols = st.columns(5)
    
    for i, (phase_key, phase_config) in enumerate(phases_config.items()):
        with cols[i]:
            progress = phase_progress[phase_key]
            
            # Determinar cor baseada no progresso
            if progress == 100:
                color = "🟢"
                bg_color = "#e8f5e8"
            elif progress > 0:
                color = "🟡"
                bg_color = "#fff3cd"
            else:
                color = "🔴"
                bg_color = "#f8d7da"
            
            # Card da fase
            st.markdown(f"""
            <div style="
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 10px;
                text-align: center;
                margin: 5px;
                background-color: {bg_color};
            ">
                <h3>{phase_config['icon']} {phase_config['name']}</h3>
                <p style="font-size: 12px; margin: 5px 0;">{phase_config['description']}</p>
                <p style="font-size: 14px; font-weight: bold;">{color} {progress:.0f}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão para navegar para a fase
            if st.button(f"Ir para {phase_config['name']}", key=f"goto_{phase_key}", use_container_width=True):
                st.session_state['current_phase'] = phase_key
                st.rerun()
    
    # Mostrar progresso geral do projeto
    st.divider()
    
    overall_progress = sum(phase_progress.values()) / len(phases_config)
    
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
        show_improve_phase(project)
    elif phase == "control":
        show_control_phase(project)


def show_define_phase(project: Dict):
    """Mostrar fase Define"""
    try:
        from src.pages.define_tools import show_define_tools
    except ImportError:
        try:
            from pages.define_tools import show_define_tools
        except ImportError:
            def show_define_tools(project):
                st.error("❌ Módulo define_tools não encontrado")
    
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
    try:
        from src.pages.measure_tools import show_measure_tools
    except ImportError:
        try:
            from pages.measure_tools import show_measure_tools
        except ImportError:
            def show_measure_tools(project):
                st.error("❌ Módulo measure_tools não encontrado")
    
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
    try:
        from src.pages.analyze_tools import show_analyze_tools
    except ImportError:
        try:
            from pages.analyze_tools import show_analyze_tools
        except ImportError:
            def show_analyze_tools(project):
                st.error("❌ Módulo analyze_tools não encontrado")
    
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
        st.warning("⚠️ Recomendamos completar a fase **Analyze** antes de desenvolver soluções")
        st.info("💡 Você ainda pode usar as ferramentas, mas terá mais contexto após completar a análise")
    
    # Mostrar resumo dos insights da fase Analyze (se disponível)
    if analyze_completed:
        st.success("✅ **Fase Analyze concluída** - Insights disponíveis para desenvolvimento de soluções")
        
        # Mostrar causas raiz identificadas (se houver)
        rca_data = analyze_data.get('root_cause_analysis', {}).get('data', {})
        if rca_data.get('root_cause_final'):
            st.info(f"🎯 **Causa Raiz Principal:** {rca_data['root_cause_final']}")
    
    # Chamar as ferramentas da fase Improve
    try:
        show_improve_tools()
    except Exception as e:
        st.error(f"❌ Erro ao carregar ferramentas da fase Improve: {str(e)}")
        st.info("Verifique se o módulo improve_tools.py está configurado corretamente")


def show_control_phase(project: Dict):
    """Mostrar fase Control"""
    st.markdown("## 🎮 Control - Controlar")
    st.markdown("Implemente controles para sustentar as melhorias alcançadas.")
    
    # Verificar se a fase Improve foi concluída
    improve_data = project.get('improve', {})
    improve_completed = any(tool.get('completed', False) for tool in improve_data.values() if isinstance(tool, dict))
    
    if not improve_completed:
        st.warning("⚠️ Complete a fase **Improve** antes de estabelecer controles")
        st.info("💡 A fase Control foca em sustentar as melhorias implementadas")
        
        # Mostrar preview das ferramentas que estarão disponíveis
        st.markdown("### 🎯 Ferramentas que serão habilitadas após completar Improve:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("📊 **Plano de Controle** - Sistema de monitoramento contínuo")
            st.info("📈 **Gráficos de Controle** - SPC para monitoramento estatístico")
        
        with col2:
            st.info("📋 **Documentação Padrão** - Procedimentos padronizados")
            st.info("🔄 **Auditoria de Sustentabilidade** - Verificação contínua")
        
        return
    
    # Mostrar resumo das soluções implementadas
    st.success("✅ **Fase Improve concluída** - Controles disponíveis")
    
    # Mostrar soluções aprovadas (se houver)
    solution_data = improve_data.get('solution_development', {}).get('data', {})
    if solution_data.get('solutions'):
        approved_solutions = [sol for sol in solution_data['solutions'] if sol.get('status') == 'Aprovada']
        if approved_solutions:
            st.info(f"🎯 **{len(approved_solutions)} solução(ões) implementada(s)** - Requer monitoramento")
            
            with st.expander("Ver soluções implementadas"):
                for i, sol in enumerate(approved_solutions, 1):
                    st.write(f"**{i}.** {sol['name']} - R$ {sol.get('cost_estimate', 0):,.2f}")
    
    # Chamar as ferramentas da fase Control
    try:
        show_control_tools()
    except Exception as e:
        st.error(f"❌ Erro ao carregar ferramentas da fase Control: {str(e)}")
        st.info("Verifique se o módulo control_tools.py está configurado corretamente")
        
        # Mostrar stack trace para debug
        import traceback
        with st.expander("Ver detalhes do erro"):
            st.code(traceback.format_exc())

    # Placeholder para ferramentas futuras
    st.markdown("---")
    st.markdown("### 🔧 Ferramentas Disponíveis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Plano de Controle", disabled=True):
            st.info("Em desenvolvimento")
        
        if st.button("📈 Gráficos de Controle", disabled=True):
            st.info("Em desenvolvimento")
    
    with col2:
        if st.button("📋 Documentação Final", disabled=True):
            st.info("Em desenvolvimento")
        
        if st.button("📊 Dashboard de KPIs", disabled=True):
            st.info("Em desenvolvimento")


if __name__ == "__main__":
    show_dmaic_phase()
