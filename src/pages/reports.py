import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO
import json
from typing import Dict, List, Optional

from src.utils.project_manager import ProjectManager
from src.utils.formatters import format_currency, format_date_br, format_number_br

def show_reports_page():
    """Página de relatórios científicos completa"""
    
    st.title("📋 Relatórios Científicos Six Sigma")
    
    # Navegação no topo
    col1, col2, col3 = st.columns([1, 4, 1])
    
    with col1:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    with col2:
        st.markdown("### Gerador de Relatórios Científicos")
    
    with col3:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    st.divider()
    
    # Verificar se há projeto selecionado
    current_project = st.session_state.get('current_project')
    
    if not current_project:
        show_no_project_selected()
        return
    
    # Interface principal
    show_report_generator(current_project)


def show_no_project_selected():
    """Tela quando nenhum projeto está selecionado"""
    st.warning("⚠️ **Nenhum projeto selecionado**")
    
    st.markdown("""
    Para gerar relatórios, você precisa primeiro selecionar um projeto.
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📊 Ir para Projetos", use_container_width=True, type="primary"):
            st.session_state.current_page = 'projects'
            st.rerun()
    
    st.divider()
    
    # Preview de funcionalidades
    st.markdown("### 🎯 O Que Você Pode Gerar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 📄 Tipos de Relatório:
        - 📊 **Relatório Executivo** - Resumo para alta gerência
        - 📈 **Relatório Técnico Completo** - Análise detalhada
        - 📋 **Relatório por Fase DMAIC** - Específico de cada fase
        - 🎯 **Relatório de Resultados** - Ganhos e impactos
        - 📝 **Relatório Customizado** - Personalize seções
        """)
    
    with col2:
        st.markdown("""
        #### 🎨 Formatos Disponíveis:
        - 📄 **PDF Científico** - Formato acadêmico
        - 📊 **Apresentação** - Slides executivos
        - 🌐 **HTML Interativo** - Visualização web
        - 📈 **Dashboard** - Métricas em tempo real
        - 📋 **Markdown** - Documentação técnica
        """)


def show_report_generator(project: Dict):
    """Interface principal de geração de relatórios"""
    
    # Header do projeto
    st.success(f"✅ **Projeto Selecionado:** {project.get('name')}")
    
    # Calcular progresso
    project_manager = ProjectManager()
    progress = project_manager.calculate_project_progress(project)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Progresso Geral", f"{progress:.1f}%")
    
    with col2:
        status_map = {'active': 'Ativo', 'completed': 'Concluído', 'paused': 'Pausado'}
        status = status_map.get(project.get('status', 'active'), 'Ativo')
        st.metric("📋 Status", status)
    
    with col3:
        expected_savings = project.get('expected_savings', 0)
        st.metric("💰 Economia Esperada", format_currency(expected_savings))
    
    st.divider()
    
    # Abas de tipos de relatório
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Executivo", 
        "📈 Técnico Completo", 
        "📋 Por Fase DMAIC",
        "🎯 Resultados",
        "📝 Customizado"
    ])
    
    with tab1:
        generate_executive_report(project, project_manager)
    
    with tab2:
        generate_technical_report(project, project_manager)
    
    with tab3:
        generate_phase_report(project, project_manager)
    
    with tab4:
        generate_results_report(project, project_manager)
    
    with tab5:
        generate_custom_report(project, project_manager)


def generate_executive_report(project: Dict, project_manager: ProjectManager):
    """Gera relatório executivo resumido"""
    
    st.markdown("### 📊 Relatório Executivo")
    st.caption("Resumo gerencial para apresentação à alta direção")
    
    st.markdown("---")
    
    # Configurações
    col1, col2 = st.columns(2)
    
    with col1:
        include_charts = st.checkbox("📈 Incluir Gráficos", value=True, key="exec_charts")
        include_metrics = st.checkbox("📊 Incluir Métricas", value=True, key="exec_metrics")
    
    with col2:
        include_timeline = st.checkbox("📅 Incluir Cronograma", value=True, key="exec_timeline")
        include_roi = st.checkbox("💰 Incluir ROI", value=True, key="exec_roi")
    
    # Preview do relatório
    st.markdown("### 📄 Preview do Relatório")
    
    with st.expander("👁️ Ver Preview Completo", expanded=True):
        show_executive_preview(project, project_manager, {
            'charts': include_charts,
            'metrics': include_metrics,
            'timeline': include_timeline,
            'roi': include_roi
        })
    
    st.divider()
    
    # Opções de exportação
    st.markdown("### 💾 Exportar Relatório")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Gerar PDF", use_container_width=True, type="primary", key="exec_pdf"):
            with st.spinner("Gerando PDF..."):
                st.info("🚧 Funcionalidade de exportação PDF será implementada em breve")
                st.balloons()
    
    with col2:
        if st.button("📊 Gerar PowerPoint", use_container_width=True, key="exec_ppt"):
            with st.spinner("Gerando apresentação..."):
                st.info("🚧 Funcionalidade de exportação PowerPoint será implementada em breve")
    
    with col3:
        if st.button("📋 Copiar Markdown", use_container_width=True, key="exec_md"):
            markdown_content = generate_executive_markdown(project, project_manager)
            st.code(markdown_content, language="markdown")
            st.success("✅ Markdown gerado! Copie o conteúdo acima.")


def show_executive_preview(project: Dict, project_manager: ProjectManager, options: Dict):
    """Mostra preview do relatório executivo"""
    
    # Cabeçalho
    st.markdown(f"# 📊 Relatório Executivo: {project.get('name')}")
    st.caption(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
    
    st.markdown("---")
    
    # 1. Resumo Executivo
    st.markdown("## 1. Resumo Executivo")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        **Projeto:** {project.get('name')}
        
        **Objetivo:** {project.get('description', 'Não informado')}
        
        **Status:** {project.get('status', 'active').title()}
        
        **Progresso:** {project_manager.calculate_project_progress(project):.1f}%
        """)
    
    with col2:
        if options['metrics']:
            st.metric("💰 Economia Esperada", format_currency(project.get('expected_savings', 0)))
            
            start_date = project.get('start_date', '')
            if start_date:
                st.metric("📅 Início", format_date_br(start_date))
    
    # 2. Métricas Principais
    if options['metrics']:
        st.markdown("## 2. Métricas Principais")
        
        stats = project_manager.get_project_statistics(project)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Fases Completas", f"{stats['completed_phases']}/5")
        
        with col2:
            st.metric("🔧 Ferramentas Completas", f"{stats['completed_tools']}/{stats['total_tools']}")
        
        with col3:
            st.metric("📈 Progresso Geral", f"{project_manager.calculate_project_progress(project):.1f}%")
        
        with col4:
            if stats['has_uploaded_data']:
                st.metric("📊 Dados", "✅ Disponíveis")
            else:
                st.metric("📊 Dados", "⚠️ Pendente")
    
    # 3. Gráficos
    if options['charts']:
        st.markdown("## 3. Análise Visual")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de progresso por fase
            stats = project_manager.get_project_statistics(project)
            phase_names = ['Define', 'Measure', 'Analyze', 'Improve', 'Control']
            phase_progress = [stats['phase_progress'][p]['progress'] for p in ['define', 'measure', 'analyze', 'improve', 'control']]
            
            fig1 = go.Figure(data=[
                go.Bar(x=phase_names, y=phase_progress, marker_color='lightblue')
            ])
            fig1.update_layout(
                title="Progresso por Fase DMAIC",
                xaxis_title="Fase",
                yaxis_title="Progresso (%)",
                height=300
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Gráfico de ferramentas completadas
            completed = stats['completed_tools']
            pending = stats['total_tools'] - completed
            
            fig2 = go.Figure(data=[
                go.Pie(labels=['Completas', 'Pendentes'], values=[completed, pending],
                       marker_colors=['lightgreen', 'lightcoral'])
            ])
            fig2.update_layout(
                title="Status das Ferramentas",
                height=300
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    # 4. Cronograma
    if options['timeline']:
        st.markdown("## 4. Cronograma do Projeto")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            start_date = project.get('start_date', '')
            if start_date:
                st.markdown(f"**📅 Início:** {format_date_br(start_date)}")
            else:
                st.markdown("**📅 Início:** Não definido")
        
        with col2:
            target_date = project.get('target_end_date', '')
            if target_date:
                st.markdown(f"**🎯 Conclusão Prevista:** {format_date_br(target_date)}")
            else:
                st.markdown("**🎯 Conclusão Prevista:** Não definida")
        
        with col3:
            if start_date and target_date:
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
                    duration = (end - start).days
                    st.markdown(f"**⏱️ Duração:** {duration} dias")
                except:
                    st.markdown("**⏱️ Duração:** N/A")
    
    # 5. ROI
    if options['roi']:
        st.markdown("## 5. Retorno sobre Investimento (ROI)")
        
        expected_savings = project.get('expected_savings', 0)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            **Economia Esperada:** {format_currency(expected_savings)}
            
            *Nota: Os valores de investimento e ROI podem ser configurados nas ferramentas específicas do projeto.*
            """)
        
        with col2:
            if expected_savings > 0:
                st.success(f"💰 {format_currency(expected_savings)}")
            else:
                st.info("💰 A definir")
    
    # 6. Conclusões
    st.markdown("## 6. Conclusões e Próximos Passos")
    
    progress = project_manager.calculate_project_progress(project)
    
    if progress == 100:
        st.success("✅ **Projeto Concluído** - Todas as fases e ferramentas foram completadas.")
    elif progress >= 75:
        st.info("🎯 **Projeto em Fase Final** - Últimas etapas em andamento.")
    elif progress >= 50:
        st.warning("⚠️ **Projeto em Andamento** - Metade do caminho percorrido.")
    else:
        st.info("🚀 **Projeto Inicial** - Primeiras fases em desenvolvimento.")
    
    st.markdown("---")
    st.caption("Relatório gerado automaticamente pelo Sistema Green Belt Six Sigma")


def generate_technical_report(project: Dict, project_manager: ProjectManager):
    """Gera relatório técnico completo"""
    
    st.markdown("### 📈 Relatório Técnico Completo")
    st.caption("Documentação detalhada com todas as análises e dados")
    
    st.info("🚧 **Em Desenvolvimento**")
    
    st.markdown("""
    O relatório técnico completo incluirá:
    
    #### 📋 Seções:
    1. **Introdução** - Contexto e objetivos
    2. **Metodologia DMAIC** - Descrição detalhada de cada fase
    3. **Define** - Charter, stakeholders, VOC, SIPOC
    4. **Measure** - Plano de coleta, dados baseline, MSA, capacidade
    5. **Analyze** - Análises estatísticas, causas raiz
    6. **Improve** - Soluções, plano de ação, resultados piloto
    7. **Control** - Plano de controle, documentação
    8. **Resultados** - Ganhos financeiros, melhorias de processo
    9. **Conclusões** - Lições aprendidas, recomendações
    10. **Anexos** - Dados brutos, gráficos adicionais
    
    #### 📊 Inclui:
    - Todos os gráficos estatísticos
    - Tabelas de dados completas
    - Análises detalhadas
    - Referências bibliográficas
    - Formato científico (ABNT/APA)
    """)
    
    if st.button("📄 Gerar Relatório Técnico", use_container_width=True, type="primary"):
        st.balloons()
        st.success("🎉 Funcionalidade será implementada em breve!")


def generate_phase_report(project: Dict, project_manager: ProjectManager):
    """Gera relatório específico de uma fase DMAIC"""
    
    st.markdown("### 📋 Relatório por Fase DMAIC")
    st.caption("Relatório focado em uma fase específica do projeto")
    
    # Seleção da fase
    phase_options = {
        'define': '🎯 Define - Definição do Projeto',
        'measure': '📊 Measure - Medição e Coleta',
        'analyze': '📈 Analyze - Análise Estatística',
        'improve': '🔧 Improve - Melhorias',
        'control': '✅ Control - Controle'
    }
    
    selected_phase = st.selectbox(
        "Selecione a Fase",
        options=list(phase_options.keys()),
        format_func=lambda x: phase_options[x],
        key="phase_report_select"
    )
    
    st.divider()
    
    # Obter dados da fase
    phase_data = project.get(selected_phase, {})
    stats = project_manager.get_project_statistics(project)
    phase_stats = stats['phase_progress'].get(selected_phase, {})
    
    # Header da fase
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Progresso da Fase", f"{phase_stats.get('progress', 0):.1f}%")
    
    with col2:
        completed = phase_stats.get('completed', 0)
        total = phase_stats.get('total', 0)
        st.metric("🔧 Ferramentas", f"{completed}/{total}")
    
    with col3:
        if phase_stats.get('progress', 0) == 100:
            st.metric("✅ Status", "Completa")
        else:
            st.metric("⏳ Status", "Em Andamento")
    
    st.divider()
    
    # Preview do relatório da fase
    with st.expander("👁️ Ver Preview do Relatório", expanded=True):
        show_phase_preview(project, selected_phase, phase_data, phase_stats)
    
    st.divider()
    
    # Exportação
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Gerar PDF da Fase", use_container_width=True, type="primary"):
            st.info("🚧 Exportação PDF será implementada em breve")
    
    with col2:
        if st.button("📋 Copiar Markdown", use_container_width=True):
            st.code(f"# Relatório da Fase {phase_options[selected_phase]}\n\n...", language="markdown")
            st.success("✅ Markdown gerado!")


def show_phase_preview(project: Dict, phase: str, phase_data: Dict, phase_stats: Dict):
    """Mostra preview do relatório de fase"""
    
    phase_names = {
        'define': '🎯 Define - Definição do Projeto',
        'measure': '📊 Measure - Medição e Coleta de Dados',
        'analyze': '📈 Analyze - Análise Estatística',
        'improve': '🔧 Improve - Implementação de Melhorias',
        'control': '✅ Control - Controle e Sustentação'
    }
    
    st.markdown(f"# {phase_names[phase]}")
    st.caption(f"Projeto: {project.get('name')}")
    st.caption(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
    
    st.markdown("---")
    
    # Status da fase
    st.markdown("## Status da Fase")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Progresso:** {phase_stats.get('progress', 0):.1f}%")
        st.markdown(f"**Ferramentas Completadas:** {phase_stats.get('completed', 0)}/{phase_stats.get('total', 0)}")
    
    with col2:
        if phase_stats.get('progress', 0) == 100:
            st.success("✅ Fase Concluída")
        elif phase_stats.get('progress', 0) > 0:
            st.warning("⏳ Fase em Andamento")
        else:
            st.info("📋 Fase Não Iniciada")
    
    # Ferramentas da fase
    st.markdown("## Ferramentas Utilizadas")
    
    for tool_name, tool_data in phase_data.items():
        if isinstance(tool_data, dict):
            is_completed = tool_data.get('completed', False)
            status_icon = "✅" if is_completed else "⏳"
            
            with st.expander(f"{status_icon} {tool_name.replace('_', ' ').title()}"):
                if is_completed:
                    st.success("Ferramenta concluída")
                    
                    # Mostrar dados se existirem
                    data = tool_data.get('data', {})
                    if data:
                        st.json(data)
                else:
                    st.info("Ferramenta pendente")
    
    st.markdown("---")
    st.caption("Relatório gerado pelo Sistema Green Belt Six Sigma")


def generate_results_report(project: Dict, project_manager: ProjectManager):
    """Gera relatório de resultados e impactos"""
    
    st.markdown("### 🎯 Relatório de Resultados")
    st.caption("Ganhos financeiros, melhorias de processo e impactos")
    
    st.info("🚧 **Em Desenvolvimento**")
    
    st.markdown("""
    O relatório de resultados incluirá:
    
    #### 💰 Resultados Financeiros:
    - Economia real vs. esperada
    - ROI do projeto
    - Payback period
    - Custos evitados
    
    #### 📊 Melhorias de Processo:
    - Redução de defeitos
    - Melhoria de capacidade (Cp, Cpk)
    - Redução de variação (Sigma level)
    - Redução de lead time
    
    #### 🎯 Impactos:
    - Satisfação do cliente
    - Impacto operacional
    - Ganhos de qualidade
    - Benefícios intangíveis
    
    #### 📈 Gráficos:
    - Antes vs. Depois
    - Tendências ao longo do tempo
    - Pareto de ganhos
    - Comparativos
    """)


def generate_custom_report(project: Dict, project_manager: ProjectManager):
    """Gera relatório customizado"""
    
    st.markdown("### 📝 Relatório Customizado")
    st.caption("Personalize as seções e conteúdo do seu relatório")
    
    st.markdown("#### Selecione as Seções:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_summary = st.checkbox("📋 Resumo Executivo", value=True, key="custom_summary")
        include_define = st.checkbox("🎯 Fase Define", value=True, key="custom_define")
        include_measure = st.checkbox("📊 Fase Measure", value=True, key="custom_measure")
        include_analyze = st.checkbox("📈 Fase Analyze", value=True, key="custom_analyze")
        include_improve = st.checkbox("🔧 Fase Improve", value=True, key="custom_improve")
    
    with col2:
        include_control = st.checkbox("✅ Fase Control", value=True, key="custom_control")
        include_results = st.checkbox("🎯 Resultados", value=True, key="custom_results")
        include_charts = st.checkbox("📊 Gráficos", value=True, key="custom_charts")
        include_data = st.checkbox("📋 Dados Brutos", value=False, key="custom_data")
        include_appendix = st.checkbox("📎 Anexos", value=False, key="custom_appendix")
    
    st.divider()
    
    st.markdown("#### Configurações Adicionais:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_format = st.selectbox(
            "Formato de Saída",
            ["PDF", "PowerPoint", "HTML", "Markdown", "Word"],
            key="custom_format"
        )
        
        language = st.selectbox(
            "Idioma",
            ["Português (BR)", "English", "Español"],
            key="custom_language"
        )
    
    with col2:
        style = st.selectbox(
            "Estilo",
            ["Científico", "Executivo", "Técnico", "Simples"],
            key="custom_style"
        )
        
        color_scheme = st.selectbox(
            "Esquema de Cores",
            ["Azul (Padrão)", "Verde", "Vermelho", "Cinza", "Colorido"],
            key="custom_colors"
        )
    
    st.divider()
    
    # Resumo da seleção
    selected_sections = []
    if include_summary: selected_sections.append("Resumo Executivo")
    if include_define: selected_sections.append("Define")
    if include_measure: selected_sections.append("Measure")
    if include_analyze: selected_sections.append("Analyze")
    if include_improve: selected_sections.append("Improve")
    if include_control: selected_sections.append("Control")
    if include_results: selected_sections.append("Resultados")
    if include_charts: selected_sections.append("Gráficos")
    if include_data: selected_sections.append("Dados Brutos")
    if include_appendix: selected_sections.append("Anexos")
    
    st.info(f"📋 Seções selecionadas: {len(selected_sections)}")
    
    if st.button("📄 Gerar Relatório Customizado", use_container_width=True, type="primary"):
        with st.spinner("Gerando relatório..."):
            st.success("🎉 Relatório customizado será implementado em breve!")
            st.balloons()


def generate_executive_markdown(project: Dict, project_manager: ProjectManager) -> str:
    """Gera conteúdo markdown do relatório executivo"""
    
    progress = project_manager.calculate_project_progress(project)
    stats = project_manager.get_project_statistics(project)
    
    markdown = f"""# 📊 Relatório Executivo: {project.get('name')}

**Gerado em:** {datetime.now().strftime('%d/%m/%Y às %H:%M')}

---

## 1. Resumo Executivo

**Projeto:** {project.get('name')}

**Objetivo:** {project.get('description', 'Não informado')}

**Status:** {project.get('status', 'active').title()}

**Progresso:** {progress:.1f}%

**Economia Esperada:** R$ {project.get('expected_savings', 0):,.2f}

---

## 2. Métricas Principais

- **Fases Completas:** {stats['completed_phases']}/5
- **Ferramentas Completas:** {stats['completed_tools']}/{stats['total_tools']}
- **Progresso Geral:** {progress:.1f}%
- **Dados:** {"✅ Disponíveis" if stats['has_uploaded_data'] else "⚠️ Pendente"}

---

## 3. Status por Fase DMAIC

"""
    
    for phase in ['define', 'measure', 'analyze', 'improve', 'control']:
        phase_info = stats['phase_progress'][phase]
        phase_name = phase.title()
        phase_progress = phase_info['progress']
        status = "✅" if phase_progress == 100 else "⏳"
        
        markdown += f"- **{status} {phase_name}:** {phase_progress:.1f}% ({phase_info['completed']}/{phase_info['total']} ferramentas)\n"
    
    markdown += """
---

## 4. Conclusões

"""
    
    if progress == 100:
        markdown += "✅ **Projeto Concluído** - Todas as fases e ferramentas foram completadas.\n"
    elif progress >= 75:
        markdown += "🎯 **Projeto em Fase Final** - Últimas etapas em andamento.\n"
    elif progress >= 50:
        markdown += "⚠️ **Projeto em Andamento** - Metade do caminho percorrido.\n"
    else:
        markdown += "🚀 **Projeto Inicial** - Primeiras fases em desenvolvimento.\n"
    
    markdown += """
---

*Relatório gerado automaticamente pelo Sistema Green Belt Six Sigma*
"""
    
    return markdown
