import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

def show_projects_page():
    """Página de gerenciamento completo de projetos Six Sigma"""
    
    st.title("📊 Gerenciamento de Projetos Six Sigma")
    
    # ==================== HEADER COM NAVEGAÇÃO ====================
    col1, col2, col3 = st.columns([1, 4, 1])
    
    with col1:
        if st.button("⬅️ Voltar", use_container_width=True, key="btn_voltar_projects"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    with col2:
        st.markdown("### Gerenciamento Avançado de Projetos")
    
    with col3:
        if st.button("🏠 Dashboard", use_container_width=True, key="btn_home_projects"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    st.divider()
    
    # ==================== BUSCAR PROJETOS DO FIREBASE ====================
    try:
        # SUBSTITUA ESTA LINHA pela sua função real de buscar projetos
        projects = _get_projects_from_firebase()
        
        if not projects:
            st.warning("📭 Nenhum projeto encontrado. Crie seu primeiro projeto!")
            if st.button("➕ Criar Novo Projeto"):
                st.session_state.current_page = 'dashboard'
                st.rerun()
            return
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar projetos: {str(e)}")
        return
    
    # ==================== ESTATÍSTICAS GERAIS ====================
    st.markdown("## 📈 Visão Geral")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_projects = len(projects)
        active_projects = sum(1 for p in projects if p.get('status') == 'Ativo')
        st.metric(
            "Total de Projetos", 
            total_projects,
            delta=f"{active_projects} ativos"
        )
    
    with col2:
        total_savings = sum(p.get('savings', 0) for p in projects)
        st.metric(
            "Economia Total", 
            f"R$ {total_savings:,.2f}",
            delta="↗️ Acumulado"
        )
    
    with col3:
        avg_progress = np.mean([p.get('progress', 0) for p in projects])
        st.metric(
            "Progresso Médio", 
            f"{avg_progress:.1f}%",
            delta=f"{len([p for p in projects if p.get('progress', 0) >= 100])} concluídos"
        )
    
    with col4:
        # Calcular tempo médio (exemplo - ajuste conforme sua estrutura)
        st.metric(
            "Projetos Este Mês", 
            len([p for p in projects if _is_current_month(p.get('created_at', ''))]),
            delta="↗️ Novos"
        )
    
    st.divider()
    
    # ==================== FILTROS E BUSCA ====================
    st.markdown("## 🔍 Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔎 Buscar projeto", placeholder="Nome ou descrição...")
    
    with col2:
        status_filter = st.selectbox(
            "📊 Status",
            ["Todos", "Ativo", "Concluído", "Pausado", "Cancelado"]
        )
    
    with col3:
        progress_filter = st.selectbox(
            "📈 Progresso",
            ["Todos", "0-25%", "25-50%", "50-75%", "75-100%", "100%"]
        )
    
    # Aplicar filtros
    filtered_projects = _apply_filters(
        projects, 
        search_term, 
        status_filter, 
        progress_filter
    )
    
    st.markdown(f"**{len(filtered_projects)}** projeto(s) encontrado(s)")
    
    st.divider()
    
    # ==================== ABAS DE VISUALIZAÇÃO ====================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Lista de Projetos", 
        "📊 Gráficos", 
        "🔄 Comparação",
        "📈 Análise Detalhada"
    ])
    
    # -------------------- ABA 1: LISTA DE PROJETOS --------------------
    with tab1:
        st.markdown("### 📋 Todos os Projetos")
        
        # Opção de visualização
        view_mode = st.radio(
            "Modo de visualização:",
            ["Cards", "Tabela"],
            horizontal=True,
            key="view_mode_projects"
        )
        
        if view_mode == "Cards":
            _render_projects_cards(filtered_projects)
        else:
            _render_projects_table(filtered_projects)
    
    # -------------------- ABA 2: GRÁFICOS --------------------
    with tab2:
        st.markdown("### 📊 Análise Gráfica")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de progresso por projeto
            fig_progress = _create_progress_chart(filtered_projects)
            st.plotly_chart(fig_progress, use_container_width=True)
        
        with col2:
            # Gráfico de economia por projeto
            fig_savings = _create_savings_chart(filtered_projects)
            st.plotly_chart(fig_savings, use_container_width=True)
        
        # Gráfico de distribuição por fase DMAIC
        st.markdown("#### 📊 Distribuição por Fase DMAIC")
        fig_phases = _create_phases_distribution(filtered_projects)
        st.plotly_chart(fig_phases, use_container_width=True)
    
    # -------------------- ABA 3: COMPARAÇÃO --------------------
    with tab3:
        st.markdown("### 🔄 Comparação Entre Projetos")
        
        if len(filtered_projects) < 2:
            st.info("Selecione pelo menos 2 projetos para comparar")
        else:
            selected_projects = st.multiselect(
                "Selecione projetos para comparar:",
                options=[p['name'] for p in filtered_projects],
                default=[p['name'] for p in filtered_projects[:2]]
            )
            
            if selected_projects:
                comparison_data = [p for p in filtered_projects if p['name'] in selected_projects]
                _render_comparison(comparison_data)
    
    # -------------------- ABA 4: ANÁLISE DETALHADA --------------------
    with tab4:
        st.markdown("### 📈 Análise Detalhada")
        
        # Estatísticas avançadas
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Performance")
            _render_performance_metrics(filtered_projects)
        
        with col2:
            st.markdown("#### 💰 Análise Financeira")
            _render_financial_analysis(filtered_projects)


# ==================== FUNÇÕES AUXILIARES ====================

def _get_projects_from_firebase():
    """
    SUBSTITUA esta função pela sua lógica real de buscar projetos do Firebase
    """
    # Exemplo de estrutura - AJUSTE conforme seu Firebase
    
    # Se você já tem uma função, use ela:
    # from firebase_config import get_all_projects
    # return get_all_projects()
    
    # Dados de exemplo (REMOVA quando integrar com Firebase real)
    return [
        {
            'id': '1',
            'name': 'Redução de Falhas nas Perfuratrizes',
            'description': 'Projeto para reduzir falhas operacionais',
            'status': 'Ativo',
            'created_at': '16/11/2025',
            'savings': 180000.00,
            'progress': 62.9,
            'phases': {
                'define': 100,
                'measure': 100,
                'analyze': 75,
                'improve': 25,
                'control': 0
            }
        },
        {
            'id': '2',
            'name': 'Otimização de Processos Logísticos',
            'description': 'Melhorar eficiência da cadeia logística',
            'status': 'Ativo',
            'created_at': '01/11/2025',
            'savings': 95000.00,
            'progress': 45.0,
            'phases': {
                'define': 100,
                'measure': 80,
                'analyze': 40,
                'improve': 0,
                'control': 0
            }
        }
    ]


def _is_current_month(date_str):
    """Verifica se a data é do mês atual"""
    try:
        date = datetime.strptime(date_str, '%d/%m/%Y')
        now = datetime.now()
        return date.month == now.month and date.year == now.year
    except:
        return False


def _apply_filters(projects, search_term, status_filter, progress_filter):
    """Aplica filtros aos projetos"""
    filtered = projects
    
    # Filtro de busca
    if search_term:
        filtered = [
            p for p in filtered 
            if search_term.lower() in p.get('name', '').lower() 
            or search_term.lower() in p.get('description', '').lower()
        ]
    
    # Filtro de status
    if status_filter != "Todos":
        filtered = [p for p in filtered if p.get('status') == status_filter]
    
    # Filtro de progresso
    if progress_filter != "Todos":
        if progress_filter == "100%":
            filtered = [p for p in filtered if p.get('progress', 0) == 100]
        else:
            min_p, max_p = map(int, progress_filter.replace('%', '').split('-'))
            filtered = [
                p for p in filtered 
                if min_p <= p.get('progress', 0) < max_p
            ]
    
    return filtered


def _render_projects_cards(projects):
    """Renderiza projetos em formato de cards"""
    
    for i in range(0, len(projects), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(projects):
                project = projects[i + j]
                
                with col:
                    with st.container():
                        # Status com cor
                        status = project.get('status', 'Ativo')
                        status_color = {
                            'Ativo': '🟢',
                            'Concluído': '🔵',
                            'Pausado': '🟡',
                            'Cancelado': '🔴'
                        }.get(status, '⚪')
                        
                        st.markdown(f"### {status_color} {project['name']}")
                        st.caption(project.get('description', 'Sem descrição'))
                        
                        # Métricas
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("💰 Economia", f"R$ {project.get('savings', 0):,.2f}")
                        with col2:
                            st.metric("📅 Criado em", project.get('created_at', 'N/A'))
                        
                        # Progresso
                        progress = project.get('progress', 0)
                        st.markdown(f"**Progresso: {progress:.1f}%**")
                        st.progress(progress / 100)
                        
                        # Progresso por fase
                        phases = project.get('phases', {})
                        if phases:
                            st.caption("**Fases DMAIC:**")
                            phase_cols = st.columns(5)
                            phase_names = ['D', 'M', 'A', 'I', 'C']
                            phase_keys = ['define', 'measure', 'analyze', 'improve', 'control']
                            
                            for idx, (name, key) in enumerate(zip(phase_names, phase_keys)):
                                phase_progress = phases.get(key, 0)
                                emoji = "✅" if phase_progress == 100 else "⏳"
                                phase_cols[idx].caption(f"{emoji} {name}: {phase_progress}%")
                        
                        # Botões de ação
                        btn_cols = st.columns(3)
                        with btn_cols[0]:
                            if st.button("📂 Abrir", key=f"open_{project['id']}", use_container_width=True):
                                st.session_state.selected_project = project['id']
                                st.session_state.current_page = 'dmaic'
                                st.rerun()
                        
                        with btn_cols[1]:
                            if st.button("✏️ Editar", key=f"edit_{project['id']}", use_container_width=True):
                                st.session_state.editing_project = project['id']
                                st.rerun()
                        
                        with btn_cols[2]:
                            if st.button("🗑️ Excluir", key=f"delete_{project['id']}", use_container_width=True):
                                st.session_state.deleting_project = project['id']
                                st.rerun()
                        
                        st.divider()


def _render_projects_table(projects):
    """Renderiza projetos em formato de tabela"""
    
    # Preparar dados para DataFrame
    table_data = []
    for p in projects:
        table_data.append({
            'Nome': p.get('name', ''),
            'Status': p.get('status', ''),
            'Progresso (%)': f"{p.get('progress', 0):.1f}",
            'Economia (R$)': f"{p.get('savings', 0):,.2f}",
            'Criado em': p.get('created_at', ''),
            'ID': p.get('id', '')
        })
    
    df = pd.DataFrame(table_data)
    
    # Exibir tabela interativa
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Nome': st.column_config.TextColumn('Nome do Projeto', width='large'),
            'Status': st.column_config.TextColumn('Status', width='small'),
            'Progresso (%)': st.column_config.NumberColumn('Progresso', width='small'),
            'Economia (R$)': st.column_config.TextColumn('Economia', width='medium'),
            'Criado em': st.column_config.DateColumn('Data de Criação', width='small')
        }
    )


def _create_progress_chart(projects):
    """Cria gráfico de progresso por projeto"""
    df = pd.DataFrame([
        {'Projeto': p['name'], 'Progresso': p.get('progress', 0)}
        for p in projects
    ])
    
    fig = px.bar(
        df,
        x='Projeto',
        y='Progresso',
        title='Progresso por Projeto',
        color='Progresso',
        color_continuous_scale='RdYlGn',
        range_color=[0, 100]
    )
    
    fig.update_layout(
        yaxis_title='Progresso (%)',
        yaxis_range=[0, 100]
    )
    
    return fig


def _create_savings_chart(projects):
    """Cria gráfico de economia por projeto"""
    df = pd.DataFrame([
        {'Projeto': p['name'], 'Economia': p.get('savings', 0)}
        for p in projects
    ])
    
    fig = px.bar(
        df,
        x='Projeto',
        y='Economia',
        title='Economia por Projeto',
        color='Economia',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        yaxis_title='Economia (R$)'
    )
    
    return fig


def _create_phases_distribution(projects):
    """Cria gráfico de distribuição por fase DMAIC"""
    
    phases_data = {
        'Define': [],
        'Measure': [],
        'Analyze': [],
        'Improve': [],
        'Control': []
    }
    
    for p in projects:
        phases = p.get('phases', {})
        phases_data['Define'].append(phases.get('define', 0))
        phases_data['Measure'].append(phases.get('measure', 0))
        phases_data['Analyze'].append(phases.get('analyze', 0))
        phases_data['Improve'].append(phases.get('improve', 0))
        phases_data['Control'].append(phases.get('control', 0))
    
    # Calcular médias
    avg_phases = {k: np.mean(v) if v else 0 for k, v in phases_data.items()}
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(avg_phases.keys()),
            y=list(avg_phases.values()),
            marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        )
    ])
    
    fig.update_layout(
        title='Progresso Médio por Fase DMAIC',
        yaxis_title='Progresso Médio (%)',
        yaxis_range=[0, 100]
    )
    
    return fig


def _render_comparison(projects):
    """Renderiza comparação entre projetos selecionados"""
    
    # Tabela comparativa
    comparison_data = []
    for p in projects:
        comparison_data.append({
            'Projeto': p['name'],
            'Status': p.get('status', ''),
            'Progresso': f"{p.get('progress', 0):.1f}%",
            'Economia': f"R$ {p.get('savings', 0):,.2f}",
            'Define': f"{p.get('phases', {}).get('define', 0)}%",
            'Measure': f"{p.get('phases', {}).get('measure', 0)}%",
            'Analyze': f"{p.get('phases', {}).get('analyze', 0)}%",
            'Improve': f"{p.get('phases', {}).get('improve', 0)}%",
            'Control': f"{p.get('phases', {}).get('control', 0)}%"
        })
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Gráfico de radar comparativo
    st.markdown("#### 📊 Comparação Visual (Fases DMAIC)")
    
    fig = go.Figure()
    
    categories = ['Define', 'Measure', 'Analyze', 'Improve', 'Control']
    
    for p in projects:
        phases = p.get('phases', {})
        values = [
            phases.get('define', 0),
            phases.get('measure', 0),
            phases.get('analyze', 0),
            phases.get('improve', 0),
            phases.get('control', 0)
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=p['name']
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_performance_metrics(projects):
    """Renderiza métricas de performance"""
    
    total = len(projects)
    active = len([p for p in projects if p.get('status') == 'Ativo'])
    completed = len([p for p in projects if p.get('progress', 0) == 100])
    
    st.metric("Taxa de Conclusão", f"{(completed/total*100) if total > 0 else 0:.1f}%")
    st.metric("Projetos Ativos", active)
    st.metric("Projetos Concluídos", completed)
    
    # Progresso médio por fase
    st.markdown("**Progresso Médio por Fase:**")
    for phase in ['define', 'measure', 'analyze', 'improve', 'control']:
        avg = np.mean([p.get('phases', {}).get(phase, 0) for p in projects])
        st.progress(avg / 100, text=f"{phase.capitalize()}: {avg:.1f}%")


def _render_financial_analysis(projects):
    """Renderiza análise financeira"""
    
    total_savings = sum(p.get('savings', 0) for p in projects)
    avg_savings = np.mean([p.get('savings', 0) for p in projects]) if projects else 0
    max_savings = max([p.get('savings', 0) for p in projects]) if projects else 0
    
    st.metric("Economia Total", f"R$ {total_savings:,.2f}")
    st.metric("Economia Média", f"R$ {avg_savings:,.2f}")
    st.metric("Maior Economia", f"R$ {max_savings:,.2f}")
    
    # ROI projetado (exemplo - ajuste conforme sua lógica)
    roi = (total_savings / len(projects)) if projects else 0
    st.metric("ROI Médio por Projeto", f"R$ {roi:,.2f}")
