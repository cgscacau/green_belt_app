"""
Navegação e controle das fases DMAIC
Versão melhorada com configuração centralizada e melhor UX
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time

# Tentar importar configurações centralizadas
try:
    from src.config.dmaic_config import (
        DMAIC_PHASES_CONFIG, DMACPhase, get_phase_config, 
        calculate_phase_completion_percentage, validate_phase_data
    )
    from src.utils.session_manager import SessionManager
    HAS_NEW_CONFIG = True
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
        def get_current_project():
            return st.session_state.get('current_project')
        
        @staticmethod
        def get_current_phase():
            return st.session_state.get('current_phase', 'define')
        
        @staticmethod
        def set_current_phase(phase):
            st.session_state['current_phase'] = phase
        
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
    
    HAS_NEW_CONFIG = False

# Importações das ferramentas das fases com fallback robusto
def import_phase_tools():
    """Importa ferramentas das fases com tratamento de erro robusto"""
    tools = {}
    
    # Define tools
    try:
        from src.pages.define_tools import show_define_tools
        tools['define'] = show_define_tools
    except ImportError:
        try:
            from pages.define_tools import show_define_tools
            tools['define'] = show_define_tools
        except ImportError:
            tools['define'] = lambda project: show_phase_placeholder('define')
    
    # Measure tools
    try:
        from src.pages.measure_tools import show_measure_tools
        tools['measure'] = show_measure_tools
    except ImportError:
        try:
            from pages.measure_tools import show_measure_tools
            tools['measure'] = show_measure_tools
        except ImportError:
            tools['measure'] = lambda project: show_phase_placeholder('measure')
    
    # Analyze tools
    try:
        from src.pages.analyze_tools import show_analyze_tools
        tools['analyze'] = show_analyze_tools
    except ImportError:
        try:
            from pages.analyze_tools import show_analyze_tools
            tools['analyze'] = show_analyze_tools
        except ImportError:
            tools['analyze'] = lambda project: show_phase_placeholder('analyze')
    
    # Improve tools
    try:
        from src.pages.improve_tools import show_improve_phase as show_improve_tools
        tools['improve'] = lambda: show_improve_tools()
    except ImportError:
        try:
            from pages.improve_tools import show_improve_phase as show_improve_tools
            tools['improve'] = lambda: show_improve_tools()
        except ImportError:
            tools['improve'] = lambda: show_phase_placeholder('improve')
    
    # Control tools
    try:
        from src.pages.control_tools import show_control_phase as show_control_tools
        tools['control'] = lambda: show_control_tools()
    except ImportError:
        try:
            from pages.control_tools import show_control_phase as show_control_tools
            tools['control'] = lambda: show_control_tools()
        except ImportError:
            tools['control'] = lambda: show_phase_placeholder('control')
    
    return tools

# Cache das ferramentas para evitar reimportações
@st.cache_resource
def get_phase_tools():
    """Cache das ferramentas das fases"""
    return import_phase_tools()

def show_dmaic_phase():
    """Navegação principal entre fases DMAIC - Versão melhorada"""
    
    # Verificar projeto selecionado
    current_project = SessionManager.get_current_project()
    
    if not current_project:
        render_no_project_selected()
        return
    
    # Renderizar header do projeto
    render_project_header(current_project)
    
    # Renderizar navegação entre fases
    render_dmaic_navigation(current_project)
    
    # Determinar e mostrar fase atual
    current_phase = SessionManager.get_current_phase()
    render_current_phase_content(current_phase, current_project)

def render_no_project_selected():
    """Renderiza tela quando nenhum projeto está selecionado"""
    st.error("❌ Nenhum projeto selecionado")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("💡 Para usar o DMAIC, você precisa selecionar um projeto primeiro.")
        
        st.markdown("""
        ### Como selecionar um projeto:
        1. Vá para a página **Dashboard** ou **Projetos**
        2. Encontre o projeto desejado
        3. Clique em **"📊 Selecionar"** ou **"🎯 Abrir DMAIC"**
        """)
    
    with col2:
        # Botão para ir aos projetos
        projects_key = SessionManager.generate_unique_key("go_to_projects")
        if st.button("📁 Ir para Projetos", key=projects_key, use_container_width=True, type="primary"):
            SessionManager.navigate_to_page("projects")
        
        # Botão para dashboard
        dashboard_key = SessionManager.generate_unique_key("go_to_dashboard")
        if st.button("🏠 Ir para Dashboard", key=dashboard_key, use_container_width=True):
            SessionManager.navigate_to_page("dashboard")

def render_project_header(project: Dict):
    """Renderiza header do projeto atual"""
    project_name = project.get('name', 'Projeto')
    project_id = project.get('id', 'unknown')
    
    # Header principal
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title(f"🎯 {project_name}")
        
        # Informações adicionais do projeto
        created_date = project.get('created_at', '')[:10] if project.get('created_at') else 'N/A'
        expected_savings = project.get('expected_savings', 0)
        
        st.caption(f"📅 Criado em: {created_date} | 💰 Economia esperada: R$ {expected_savings:,.2f}")
    
    with col2:
        # Status do projeto
        status = project.get('status', 'active')
        status_config = {
            'active': {'icon': '🟢', 'text': 'Ativo', 'color': 'success'},
            'completed': {'icon': '✅', 'text': 'Concluído', 'color': 'info'},
            'paused': {'icon': '⏸️', 'text': 'Pausado', 'color': 'warning'}
        }
        
        status_info = status_config.get(status, status_config['active'])
        
        if status_info['color'] == 'success':
            st.success(f"{status_info['icon']} {status_info['text']}")
        elif status_info['color'] == 'info':
            st.info(f"{status_info['icon']} {status_info['text']}")
        else:
            st.warning(f"{status_info['icon']} {status_info['text']}")
    
    with col3:
        # Botão para fechar projeto
        close_key = SessionManager.generate_unique_key("close_project_dmaic")
        if st.button("❌ Fechar Projeto", key=close_key, use_container_width=True):
            SessionManager.navigate_to_page("dashboard", clear_project=True)

def render_dmaic_navigation(project: Dict):
    """Renderiza navegação entre fases DMAIC melhorada"""
    st.markdown("## 🧭 Navegação entre Fases DMAIC")
    
    # Configuração das fases
    if HAS_NEW_CONFIG:
        phases_info = []
        for phase_enum in DMACPhase:
            config = get_phase_config(phase_enum)
            phases_info.append({
                'key': config.key,
                'name': config.name,
                'icon': config.icon,
                'description': config.description,
                'color': config.color
            })
    else:
        # Fallback para configuração manual
        phases_info = [
            {
                'key': 'define',
                'name': 'Define',
                'icon': '🎯',
                'description': 'Definir problema, objetivos e escopo',
                'color': '#e3f2fd'
            },
            {
                'key': 'measure',
                'name': 'Measure',
                'icon': '📏',
                'description': 'Medir e coletar dados do estado atual',
                'color': '#f3e5f5'
            },
            {
                'key': 'analyze',
                'name': 'Analyze',
                'icon': '🔍',
                'description': 'Analisar dados e identificar causas raiz',
                'color': '#fff3e0'
            },
            {
                'key': 'improve',
                'name': 'Improve',
                'icon': '⚡',
                'description': 'Desenvolver e implementar soluções',
                'color': '#e8f5e8'
            },
            {
                'key': 'control',
                'name': 'Control',
                'icon': '🎮',
                'description': 'Controlar e sustentar melhorias',
                'color': '#fce4ec'
            }
        ]
    
    # Calcular progresso de cada fase
    phase_progress = calculate_all_phases_progress(project, phases_info)
    
    # Renderizar cards das fases
    cols = st.columns(5)
    current_phase = SessionManager.get_current_phase()
    
    for i, (col, phase_info) in enumerate(zip(cols, phases_info)):
        with col:
            render_phase_card(phase_info, phase_progress, current_phase, project)
    
    # Progresso geral do projeto
    render_overall_progress(phase_progress)

def calculate_all_phases_progress(project: Dict, phases_info: List[Dict]) -> Dict[str, float]:
    """Calcula progresso de todas as fases"""
    progress = {}
    
    for phase_info in phases_info:
        phase_key = phase_info['key']
        phase_data = project.get(phase_key, {})
        
        try:
            if HAS_NEW_CONFIG:
                # Usar função da configuração centralizada
                phase_enum = DMACPhase(phase_key)
                progress[phase_key] = calculate_phase_completion_percentage(phase_data, phase_enum)
            else:
                # Fallback para cálculo manual
                progress[phase_key] = calculate_phase_completion_percentage(phase_data, phase_key)
        except Exception as e:
            st.error(f"Erro ao calcular progresso da fase {phase_key}: {str(e)}")
            progress[phase_key] = 0.0
    
    return progress

def render_phase_card(phase_info: Dict, phase_progress: Dict, current_phase: str, project: Dict):
    """Renderiza card individual da fase"""
    phase_key = phase_info['key']
    progress = phase_progress.get(phase_key, 0.0)
    is_current = current_phase == phase_key
    
    # Determinar cor baseada no progresso e se é fase atual
    if is_current:
        border_color = "#007bff"
        bg_color = "#e7f3ff"
    elif progress == 100:
        border_color = "#28a745"
        bg_color = "#e8f5e8"
    elif progress > 0:
        border_color = "#ffc107"
        bg_color = "#fff3cd"
    else:
        border_color = "#dc3545"
        bg_color = "#f8d7da"
    
    # Card HTML customizado
    st.markdown(f"""
    <div style="
        border: 3px solid {border_color};
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        margin: 10px 0;
        background: linear-gradient(135deg, {bg_color} 0%, {phase_info.get('color', '#ffffff')} 100%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease-in-out;
        cursor: pointer;
    " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
        <h3 style="margin: 10px 0; color: #2c3e50;">
            {phase_info['icon']} {phase_info['name']}
        </h3>
        <p style="font-size: 12px; margin: 8px 0; color: #6c757d; line-height: 1.3;">
            {phase_info['description']}
        </p>
        <div style="margin: 10px 0;">
            <strong style="font-size: 16px; color: {'#007bff' if is_current else '#2c3e50'};">
                {get_progress_icon(progress)} {progress:.0f}%
            </strong>
        </div>
        {'<div style="background: #007bff; color: white; padding: 4px 8px; border-radius: 10px; font-size: 10px; margin-top: 8px;">ATUAL</div>' if is_current else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # Botão para navegar para a fase
    button_key = SessionManager.generate_unique_key("goto_phase", phase_key)
    button_text = f"{'🔄 Continuar' if is_current else '➡️ Ir para'} {phase_info['name']}"
    button_type = "primary" if is_current else "secondary"
    
    if st.button(button_text, key=button_key, use_container_width=True, type=button_type):
        SessionManager.set_current_phase(phase_key)
        st.success(f"✅ Navegando para fase {phase_info['name']}")
        time.sleep(0.5)
        st.rerun()

def get_progress_icon(progress: float) -> str:
    """Retorna ícone baseado no progresso"""
    if progress == 100:
        return "🟢"
    elif progress >= 75:
        return "🟡"
    elif progress >= 25:
        return "🟠"
    elif progress > 0:
        return "🔴"
    else:
        return "⚪"

def render_overall_progress(phase_progress: Dict):
    """Renderiza progresso geral do projeto"""
    st.divider()
    
    if phase_progress:
        overall_progress = sum(phase_progress.values()) / len(phase_progress)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("### 📈 Progresso Geral do Projeto")
            
            # Barra de progresso customizada
            st.markdown(f"""
            <div style='
                width: 100%; 
                background-color: #e9ecef; 
                border-radius: 20px; 
                height: 30px; 
                position: relative;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
            '>
                <div style='
                    width: {overall_progress}%; 
                    background: linear-gradient(90deg, #28a745 0%, #20c997 50%, #17a2b8 100%); 
                    height: 30px; 
                    border-radius: 20px; 
                    transition: width 0.5s ease-in-out;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                '>{overall_progress:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
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
        
        with col3:
            # Estatísticas rápidas
            completed_phases = sum(1 for p in phase_progress.values() if p == 100)
            in_progress_phases = sum(1 for p in phase_progress.values() if 0 < p < 100)
            
            st.metric("Fases Completas", f"{completed_phases}/5")
            st.metric("Em Progresso", in_progress_phases)

def render_current_phase_content(phase: str, project: Dict):
    """Renderiza conteúdo da fase atual"""
    st.divider()
    
    # Header da fase atual
    phase_info = get_phase_info(phase)
    
    st.markdown(f"""
    <div style='
        background: linear-gradient(135deg, {phase_info['color']} 0%, #ffffff 100%);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #007bff;
        margin: 20px 0;
    '>
        <h2 style='margin: 0; color: #2c3e50;'>
            {phase_info['icon']} {phase_info['name']} - {phase_info['description']}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar informações da fase
    render_phase_info(phase, project)
    
    # Carregar e mostrar ferramentas da fase
    try:
        phase_tools = get_phase_tools()
        
        if phase in phase_tools:
            if phase == 'improve':
                # Improve tools tem interface diferente
                phase_tools[phase]()
            elif phase == 'control':
                # Control tools tem interface diferente
                phase_tools[phase]()
            else:
                # Define, Measure, Analyze recebem projeto
                phase_tools[phase](project)
        else:
            show_phase_placeholder(phase)
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar ferramentas da fase {phase}: {str(e)}")
        show_phase_placeholder(phase)
        
        # Debug info em expander
        with st.expander("🔍 Informações de Debug"):
            st.code(f"Erro: {str(e)}")
            st.code(f"Fase: {phase}")
            st.code(f"Projeto ID: {project.get('id', 'N/A')}")

def get_phase_info(phase: str) -> Dict:
    """Retorna informações da fase"""
    phase_info_map = {
        'define': {
            'name': 'Define',
            'icon': '🎯',
            'description': 'Definir problema, objetivos e escopo',
            'color': '#e3f2fd'
        },
        'measure': {
            'name': 'Measure',
            'icon': '📏',
            'description': 'Medir e coletar dados do estado atual',
            'color': '#f3e5f5'
        },
        'analyze': {
            'name': 'Analyze',
            'icon': '🔍',
            'description': 'Analisar dados e identificar causas raiz',
            'color': '#fff3e0'
        },
        'improve': {
            'name': 'Improve',
            'icon': '⚡',
            'description': 'Desenvolver e implementar soluções',
            'color': '#e8f5e8'
        },
        'control': {
            'name': 'Control',
            'icon': '🎮',
            'description': 'Controlar e sustentar melhorias',
            'color': '#fce4ec'
        }
    }
    
    return phase_info_map.get(phase, phase_info_map['define'])

def render_phase_info(phase: str, project: Dict):
    """Renderiza informações específicas da fase"""
    phase_data = project.get(phase, {})
    
    # Informações gerais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Progresso da fase atual
        try:
            if HAS_NEW_CONFIG:
                phase_enum = DMACPhase(phase)
                progress = calculate_phase_completion_percentage(phase_data, phase_enum)
            else:
                progress = calculate_phase_completion_percentage(phase_data, phase)
            
            st.metric("Progresso da Fase", f"{progress:.1f}%")
        except Exception:
            st.metric("Progresso da Fase", "Erro")
    
    with col2:
        # Ferramentas concluídas
        completed_tools = 0
        if isinstance(phase_data, dict):
            for tool_data in phase_data.values():
                if isinstance(tool_data, dict) and tool_data.get('completed', False):
                    completed_tools += 1
        
        total_tools = get_phase_tools_count(phase)
        st.metric("Ferramentas", f"{completed_tools}/{total_tools}")
    
    with col3:
        # Status da fase
        if progress == 100:
            st.success("✅ Fase Completa")
        elif progress > 0:
            st.info("🔄 Em Progresso")
        else:
            st.warning("⏳ Não Iniciada")
    
    # Verificações de pré-requisitos
    render_phase_prerequisites(phase, project)

def get_phase_tools_count(phase: str) -> int:
    """Retorna número de ferramentas da fase"""
    tools_count = {
        'define': 5,
        'measure': 4,
        'analyze': 4,
        'improve': 4,
        'control': 4
    }
    return tools_count.get(phase, 4)

def render_phase_prerequisites(phase: str, project: Dict):
    """Renderiza verificações de pré-requisitos da fase"""
    
    if phase == 'measure':
        # Verificar se Define foi iniciada
        define_data = project.get('define', {})
        define_started = any(
            isinstance(tool_data, dict) and tool_data.get('completed', False)
            for tool_data in define_data.values()
        )
        
        if not define_started:
            st.warning("⚠️ **Recomendação:** Complete pelo menos o **Project Charter** na fase Define antes de prosseguir para Measure")
    
    elif phase == 'analyze':
        # Verificar se Measure foi concluída
        measure_data = project.get('measure', {})
        measure_completed = any(
            isinstance(tool_data, dict) and tool_data.get('completed', False)
            for tool_data in measure_data.values()
        )
        
        if not measure_completed:
            st.warning("⚠️ **Recomendação:** Complete pelo menos uma ferramenta da fase **Measure** antes de prosseguir para Analyze")
        
        # Verificar dados disponíveis
        project_id = project.get('id')
        if project_id and f'uploaded_data_{project_id}' in st.session_state:
            df = st.session_state[f'uploaded_data_{project_id}']
            numeric_cols = len(df.select_dtypes(include=['number']).columns)
            
            st.info(f"📊 **Dados Disponíveis:** {df.shape[0]} linhas, {df.shape[1]} colunas")
            
            if numeric_cols > 0:
                st.success(f"✅ {numeric_cols} variáveis numéricas disponíveis para análise")
            else:
                st.warning("⚠️ Nenhuma variável numérica detectada - verifique o upload de dados")
        else:
            st.warning("⚠️ Nenhum dado carregado - faça upload na fase Measure")
    
    elif phase == 'improve':
        # Verificar se Analyze foi concluída
        analyze_data = project.get('analyze', {})
        analyze_completed = any(
            isinstance(tool_data, dict) and tool_data.get('completed', False)
            for tool_data in analyze_data.values()
        )
        
        if not analyze_completed:
            st.warning("⚠️ **Recomendação:** Complete a fase **Analyze** antes de desenvolver soluções")
            st.info("💡 Você ainda pode usar as ferramentas, mas terá mais contexto após completar a análise")
        else:
            st.success("✅ **Fase Analyze concluída** - Insights disponíveis para desenvolvimento de soluções")
            
            # Mostrar causas raiz identificadas
            rca_data = analyze_data.get('root_cause_analysis', {}).get('data', {})
            if rca_data.get('root_cause_final'):
                st.info(f"🎯 **Causa Raiz Principal:** {rca_data['root_cause_final']}")
    
    elif phase == 'control':
        # Verificar se Improve foi concluída
        improve_data = project.get('improve', {})
        improve_completed = any(
            isinstance(tool_data, dict) and tool_data.get('completed', False)
            for tool_data in improve_data.values()
        )
        
        if not improve_completed:
            st.warning("⚠️ **Recomendação:** Complete a fase **Improve** antes de estabelecer controles")
            st.info("💡 A fase Control foca em sustentar as melhorias implementadas")
            
            # Preview das ferramentas
            st.markdown("### 🎯 Ferramentas que serão habilitadas após completar Improve:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("📊 **Plano de Controle** - Sistema de monitoramento contínuo")
                st.info("📈 **Gráficos de Controle** - SPC para monitoramento estatístico")
            
            with col2:
                st.info("📋 **Documentação Padrão** - Procedimentos padronizados")
                st.info("🔄 **Auditoria de Sustentabilidade** - Verificação contínua")
        else:
            st.success("✅ **Fase Improve concluída** - Controles disponíveis")
            
            # Mostrar soluções implementadas
            solution_data = improve_data.get('solution_development', {}).get('data', {})
            if solution_data.get('solutions'):
                approved_solutions = [
                    sol for sol in solution_data['solutions'] 
                    if sol.get('status') == 'Aprovada'
                ]
                
                if approved_solutions:
                    st.info(f"🎯 **{len(approved_solutions)} solução(ões) implementada(s)** - Requer monitoramento")
                    
                    with st.expander("Ver soluções implementadas"):
                        for i, sol in enumerate(approved_solutions, 1):
                            cost = sol.get('cost_estimate', 0)
                            st.write(f"**{i}.** {sol['name']} - R$ {cost:,.2f}")

def show_phase_placeholder(phase_name: str):
    """Placeholder para fases não implementadas ou com erro"""
    st.info(f"🚧 **Ferramentas da fase {phase_name.title()} em desenvolvimento**")
    
    st.markdown(f"### 🎯 O que estará disponível na fase {phase_name.title()}:")
    
    # Ferramentas previstas por fase
    tools_preview = {
        'define': [
            "📋 Project Charter - Documento formal do projeto",
            "👥 Análise de Stakeholders - Mapeamento das partes interessadas",
            "🗣️ Voz do Cliente (VOC) - Requisitos do cliente",
            "🔄 Diagrama SIPOC - Visão do processo",
            "❓ Declaração do Problema - Definição clara do problema"
        ],
        'measure': [
            "📊 Plano de Coleta de Dados - Estratégia de medição",
            "⚖️ Sistema de Medição - Análise de confiabilidade",
            "🗺️ Mapeamento de Processo - Documentação detalhada",
            "📈 Análise da Linha Base - Performance atual"
        ],
        'analyze': [
            "📊 Análise Estatística - Análise dos dados",
            "🌳 Análise de Causa Raiz - Identificação de causas",
            "🧪 Teste de Hipóteses - Validação estatística",
            "⚙️ Análise de Processo - Performance detalhada"
        ],
        'improve': [
            "💡 Desenvolvimento de Soluções - Criação de soluções",
            "📋 Plano de Ação - Planejamento da implementação",
            "🧪 Implementação Piloto - Teste em escala reduzida",
            "🚀 Implementação Completa - Escala total"
        ],
        'control': [
            "📋 Plano de Controle - Monitoramento contínuo",
            "📈 Sistema de Monitoramento - Acompanhamento",
            "📚 Documentação Padrão - Procedimentos",
            "♻️ Plano de Sustentabilidade - Manutenção das melhorias"
        ]
    }
    
    tools = tools_preview.get(phase_name, [])
    
    for tool in tools:
        st.markdown(f"- {tool}")
    
    st.markdown("---")
    st.info("💡 **Dica:** As ferramentas serão habilitadas automaticamente conforme o desenvolvimento do sistema.")

# Função principal para compatibilidade
def main():
    """Função principal para teste standalone"""
    show_dmaic_phase()

if __name__ == "__main__":
    main()
