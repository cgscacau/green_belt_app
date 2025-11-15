import streamlit as st
import time

def show_dmaic_phase():
    """Página das fases DMAIC"""
    
    current_phase = st.session_state.get('current_dmaic_phase', 'define')
    current_project = st.session_state.get('current_project')
    
    # Gerar timestamp único para chaves
    timestamp = int(time.time() * 1000) % 10000
    
    if not current_project:
        st.error("❌ Nenhum projeto selecionado!")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🏠 Voltar ao Dashboard", key=f"back_dashboard_{timestamp}", use_container_width=True, type="primary"):
                st.session_state.current_page = 'dashboard'
                st.rerun()
        
        with col2:
            if st.button("📊 Ver Projetos", key=f"view_projects_{timestamp}", use_container_width=True):
                st.session_state.current_page = 'dashboard'
                st.rerun()
        return
    
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
    
    st.divider()
    
    # Navegação entre fases
    st.markdown("### 🔄 Navegação Rápida entre Fases")
    
    phase_buttons = st.columns(5)
    phases = ['define', 'measure', 'analyze', 'improve', 'control']
    
    for i, phase in enumerate(phases):
        with phase_buttons[i]:
            is_current = phase == current_phase
            button_type = "primary" if is_current else "secondary"
            
            if st.button(
                f"{phase_icons[phase]} {phase.title()}", 
                key=f"quick_nav_{phase}_{timestamp}",
                use_container_width=True,
                type=button_type,
                disabled=is_current
            ):
                st.session_state.current_dmaic_phase = phase
                st.rerun()
    
    st.divider()
    
    # Conteúdo da fase atual
    st.info(f"🚧 Fase {current_phase.upper()} - será implementada nas próximas etapas")
    
    # Descrições das fases
    phase_descriptions = {
        'define': """
        ### 🎯 Fase Define (Definir)
        
        **Objetivo:** Definir claramente o problema, objetivos e escopo do projeto.
        
        **Ferramentas principais:**
        - Project Charter
        - Mapeamento de Stakeholders  
        - Voice of Customer (VOC)
        - Diagrama SIPOC
        - Timeline do projeto
        
        **Entregáveis:**
        - Charter do projeto aprovado
        - Definição clara do problema
        - Objetivos SMART definidos
        - Equipe do projeto formada
        """,
        
        'measure': """
        ### 📏 Fase Measure (Medir)
        
        **Objetivo:** Medir o desempenho atual do processo e estabelecer baseline.
        
        **Ferramentas principais:**
        - Plano de coleta de dados
        - Análise de sistemas de medição (MSA)
        - Estudos de capacidade
        - Métricas CTQ (Critical to Quality)
        
        **Entregáveis:**
        - Baseline do processo atual
        - Dados coletados e validados
        - Capacidade do processo medida
        - Sistema de medição validado
        """,
        
        'analyze': """
        ### 🔍 Fase Analyze (Analisar)
        
        **Objetivo:** Analisar dados para identificar causas raiz dos problemas.
        
        **Ferramentas principais:**
        - Diagrama de Ishikawa
        - 5 Porquês
        - Análise de Pareto
        - Testes de hipóteses
        - Análises estatísticas
        
        **Entregáveis:**
        - Causas raiz identificadas
        - Hipóteses testadas estatisticamente
        - Oportunidades de melhoria priorizadas
        """,
        
        'improve': """
        ### ⚡ Fase Improve (Melhorar)
        
        **Objetivo:** Desenvolver e implementar soluções para as causas raiz.
        
        **Ferramentas principais:**
        - Brainstorming de soluções
        - Matriz de priorização
        - Plano de ação
        - Testes piloto
        - Análise de risco
        
        **Entregáveis:**
        - Soluções implementadas
        - Resultados do piloto validados
        - Plano de implementação completo
        """,
        
        'control': """
        ### 🎛️ Fase Control (Controlar)
        
        **Objetivo:** Controlar e sustentar as melhorias implementadas.
        
        **Ferramentas principais:**
        - Cartas de controle
        - Plano de controle
        - Procedimentos padronizados
        - Sistema de monitoramento
        
        **Entregáveis:**
        - Sistema de controle implementado
        - Documentação atualizada
        - Processo transferido para operação
        - Benefícios sustentados
        """
    }
    
    # Mostrar descrição da fase atual
    if current_phase in phase_descriptions:
        st.markdown(phase_descriptions[current_phase])
    
    # Progresso da fase
    st.markdown("### 📊 Progresso desta Fase")
    
    # Simular progresso (será implementado com dados reais)
    import random
    random.seed(hash(current_project.get('id', '')) + hash(current_phase))  # Progresso consistente
    progress = random.randint(0, 100)
    st.progress(progress / 100)
    st.caption(f"Progresso: {progress}% concluído")
    
    # Próximos passos
    with st.expander("🚀 Próximos Passos"):
        st.markdown(f"""
        **Para a fase {current_phase.upper()}:**
        
        1. ✅ Completar ferramentas obrigatórias
        2. 📊 Revisar análises realizadas  
        3. 📋 Documentar resultados
        4. ✔️ Validar com stakeholders
        5. ➡️ Avançar para próxima fase
        
        **Tempo estimado:** 2-4 semanas
        """)
