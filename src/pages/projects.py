import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import time

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
        # ✅ CORREÇÃO: Buscar projetos reais do Firebase
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
        active_projects = sum(1 for p in projects if p.get('status') == 'active')
        st.metric(
            "Total de Projetos", 
            total_projects,
            delta=f"{active_projects} ativos"
        )
    
    with col2:
        total_savings = sum(p.get('expected_savings', 0) for p in projects)
        st.metric(
            "Economia Total", 
            f"R$ {total_savings:,.2f}",
            delta="↗️ Acumulado"
        )
    
    with col3:
        # Calcular progresso real usando project_manager
        from src.utils.project_manager import ProjectManager
        project_manager = ProjectManager()
        
        progress_values = [project_manager.calculate_project_progress(p) for p in projects]
        avg_progress = np.mean(progress_values) if progress_values else 0
        
        st.metric(
            "Progresso Médio", 
            f"{avg_progress:.1f}%",
            delta=f"{len([p for p in progress_values if p >= 100])} concluídos"
        )
    
    with col4:
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
            ["Todos", "Ativo", "Concluído", "Pausado"]
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
        progress_filter,
        project_manager
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
            _render_projects_cards(filtered_projects, project_manager)
        else:
            _render_projects_table(filtered_projects, project_manager)
    
    # -------------------- ABA 2: GRÁFICOS --------------------
    with tab2:
        st.markdown("### 📊 Análise Gráfica")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_progress = _create_progress_chart(filtered_projects, project_manager)
            st.plotly_chart(fig_progress, use_container_width=True)
        
        with col2:
            fig_savings = _create_savings_chart(filtered_projects)
            st.plotly_chart(fig_savings, use_container_width=True)
        
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Performance")
            _render_performance_metrics(filtered_projects, project_manager)
        
        with col2:
            st.markdown("#### 💰 Análise Financeira")
            _render_financial_analysis(filtered_projects)


# ==================== FUNÇÕES AUXILIARES ====================

def _get_projects_from_firebase():
    """✅ CORREÇÃO: Busca projetos REAIS do Firebase"""
    from src.utils.project_manager import ProjectManager
    
    # Obter user_uid do session_state
    user_uid = st.session_state.get('user_data', {}).get('uid')
    
    if not user_uid:
        st.error("❌ Usuário não autenticado")
        return []
    
    # Buscar projetos do Firebase
    project_manager = ProjectManager()
    projects = project_manager.get_user_projects(user_uid)
    
    return projects


def _is_current_month(date_str):
    """Verifica se a data é do mês atual"""
    try:
        # Tentar formato ISO
        if 'T' in date_str or 'Z' in date_str:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            # Formato brasileiro
            date = datetime.strptime(date_str, '%d/%m/%Y')
        
        now = datetime.now()
        return date.month == now.month and date.year == now.year
    except:
        return False


def _apply_filters(projects, search_term, status_filter, progress_filter, project_manager):
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
        status_map = {
            "Ativo": "active",
            "Concluído": "completed",
            "Pausado": "paused"
        }
        filtered = [p for p in filtered if p.get('status') == status_map.get(status_filter, status_filter.lower())]
    
    # Filtro de progresso
    if progress_filter != "Todos":
        if progress_filter == "100%":
            filtered = [p for p in filtered if project_manager.calculate_project_progress(p) >= 100]
        else:
            min_p, max_p = map(int, progress_filter.replace('%', '').split('-'))
            filtered = [
                p for p in filtered 
                if min_p <= project_manager.calculate_project_progress(p) < max_p
            ]
    
    return filtered


def _render_projects_cards(projects, project_manager):
    """✅ CORRIGIDO: Renderiza projetos em formato de cards com BOTÕES FUNCIONAIS"""
    
    for i in range(0, len(projects), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(projects):
                project = projects[i + j]
                project_id = project.get('id', 'unknown')
                
                with col:
                    with st.container(border=True):
                        # Status com cor
                        status = project.get('status', 'active')
                        status_map = {
                            'active': ('🟢', 'Ativo'),
                            'completed': ('🔵', 'Concluído'),
                            'paused': ('🟡', 'Pausado')
                        }
                        status_emoji, status_text = status_map.get(status, ('⚪', 'Desconhecido'))
                        
                        st.markdown(f"### {status_emoji} {project.get('name', 'Sem nome')}")
                        st.caption(project.get('description', 'Sem descrição'))
                        
                        st.markdown("")  # Espaçamento
                        
                        # Métricas
                        col1, col2 = st.columns(2)
                        with col1:
                            savings = project.get('expected_savings', 0)
                            st.metric("💰 Economia", f"R$ {savings:,.2f}")
                        
                        with col2:
                            created = project.get('created_at', '')
                            if created:
                                try:
                                    date_obj = datetime.fromisoformat(created.replace('Z', '+00:00'))
                                    date_str = date_obj.strftime('%d/%m/%Y')
                                except:
                                    date_str = 'N/A'
                            else:
                                date_str = 'N/A'
                            st.metric("📅 Criado em", date_str)
                        
                        # Progresso
                        progress = project_manager.calculate_project_progress(project)
                        st.markdown(f"**Progresso: {progress:.1f}%**")
                        st.progress(progress / 100)
                        
                        st.markdown("")  # Espaçamento
                        
                        # Progresso por fase DMAIC
                        st.caption("**Fases DMAIC:**")
                        phase_cols = st.columns(5)
                        
                        phases = {
                            'D': ('define', project.get('define', {})),
                            'M': ('measure', project.get('measure', {})),
                            'A': ('analyze', project.get('analyze', {})),
                            'I': ('improve', project.get('improve', {})),
                            'C': ('control', project.get('control', {}))
                        }
                        
                        for idx, (short_name, (phase_key, phase_data)) in enumerate(phases.items()):
                            if isinstance(phase_data, dict):
                                completed = sum(1 for tool in phase_data.values() 
                                              if isinstance(tool, dict) and tool.get('completed', False))
                                total = len([t for t in phase_data.values() 
                                           if isinstance(t, dict) and 'completed' in t])
                                
                                phase_progress = (completed / total * 100) if total > 0 else 0
                                emoji = "✅" if phase_progress == 100 else "⏳"
                                
                                phase_cols[idx].caption(f"{emoji} {short_name}: {phase_progress:.0f}%")
                        
                        st.markdown("")  # Espaçamento
                        
                        # ✅ CORREÇÃO: Botões com session_state CORRETO
                        btn_cols = st.columns(3)
                        
                        with btn_cols[0]:
                            # Botão ABRIR
                            if st.button("📂 Abrir", key=f"open_{project_id}", use_container_width=True, type="primary"):
                                # ✅ CRÍTICO: Salvar projeto COMPLETO, não apenas ID
                                st.session_state['current_project'] = project
                                st.session_state['current_page'] = 'dmaic'
                                st.session_state['current_phase'] = 'define'
                                
                                st.success(f"✅ Abrindo: {project.get('name')}")
                                time.sleep(0.3)
                                st.rerun()
                        
                        with btn_cols[1]:
                            # Botão EDITAR
                            if st.button("✏️ Editar", key=f"edit_{project_id}", use_container_width=True):
                                st.session_state['editing_project_id'] = project_id
                                st.session_state['editing_project'] = project
                                st.info(f"📝 Edição: {project.get('name')}")
                                st.rerun()
                        
                        with btn_cols[2]:
                            # Botão EXCLUIR com confirmação
                            confirm_key = f"confirm_delete_{project_id}"
                            
                            if st.session_state.get(confirm_key, False):
                                if st.button("⚠️ Confirmar", key=f"confirm_{project_id}", use_container_width=True):
                                    with st.spinner("🗑️ Excluindo..."):
                                        success = project_manager.delete_project(project_id, project['user_uid'])
                                    
                                    if success:
                                        st.success("✅ Excluído!")
                                        if confirm_key in st.session_state:
                                            del st.session_state[confirm_key]
                                        if st.session_state.get('current_project', {}).get('id') == project_id:
                                            del st.session_state['current_project']
                                        time.sleep(1)
                                        st.rerun()
                            else:
                                if st.button("🗑️ Excluir", key=f"delete_{project_id}", use_container_width=True):
                                    st.session_state[confirm_key] = True
                                    st.warning(f"⚠️ Confirme: {project.get('name')}")
                                    st.rerun()


def _render_projects_table(projects, project_manager):
    """Renderiza projetos em formato de tabela"""
    
    table_data = []
    for p in projects:
        progress = project_manager.calculate_project_progress(p)
        
        status_map = {
            'active': 'Ativo',
            'completed': 'Concluído',
            'paused': 'Pausado'
        }
        
        table_data.append({
            'Nome': p.get('name', ''),
            'Status': status_map.get(p.get('status', 'active'), 'Ativo'),
            'Progresso (%)': f"{progress:.1f}",
            'Economia (R$)': f"{p.get('expected_savings', 0):,.2f}",
            'Criado em': p.get('created_at', '')[:10] if p.get('created_at') else 'N/A'
        })
    
    df = pd.DataFrame(table_data)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Nome': st.column_config.TextColumn('Nome do Projeto', width='large'),
            'Status': st.column_config.TextColumn('Status', width='small'),
            'Progresso (%)': st.column_config.NumberColumn('Progresso', width='small'),
            'Economia (R$)': st.column_config.TextColumn('Economia', width='medium')
        }
    )


def _create_progress_chart(projects, project_manager):
    """Cria gráfico de progresso por projeto"""
    df = pd.DataFrame([
        {
            'Projeto': p['name'][:20],
            'Progresso': project_manager.calculate_project_progress(p)
        }
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
        {'Projeto': p['name'][:20], 'Economia': p.get('expected_savings', 0)}
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
    
    fig.update_layout(yaxis_title='Economia (R$)')
    
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
        for phase_name, phase_key in [
            ('Define', 'define'),
            ('Measure', 'measure'),
            ('Analyze', 'analyze'),
            ('Improve', 'improve'),
            ('Control', 'control')
        ]:
            phase_data = p.get(phase_key, {})
            if isinstance(phase_data, dict):
                completed = sum(1 for tool in phase_data.values() 
                              if isinstance(tool, dict) and tool.get('completed', False))
                total = len([t for t in phase_data.values() 
                           if isinstance(t, dict) and 'completed' in t])
                progress = (completed / total * 100) if total > 0 else 0
            else:
                progress = 0
            
            phases_data[phase_name].append(progress)
    
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
    """Renderiza comparação entre projetos"""
    from src.utils.project_manager import ProjectManager
    project_manager = ProjectManager()
    
    comparison_data = []
    for p in projects:
        stats = project_manager.get_project_statistics(p)
        
        comparison_data.append({
            'Projeto': p['name'],
            'Status': p.get('status', 'active'),
            'Progresso': f"{project_manager.calculate_project_progress(p):.1f}%",
            'Economia': f"R$ {p.get('expected_savings', 0):,.2f}",
            'Define': f"{stats['phase_progress'].get('define', {}).get('progress', 0):.0f}%",
            'Measure': f"{stats['phase_progress'].get('measure', {}).get('progress', 0):.0f}%",
            'Analyze': f"{stats['phase_progress'].get('analyze', {}).get('progress', 0):.0f}%",
            'Improve': f"{stats['phase_progress'].get('improve', {}).get('progress', 0):.0f}%",
            'Control': f"{stats['phase_progress'].get('control', {}).get('progress', 0):.0f}%"
        })
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Gráfico de radar
    st.markdown("#### 📊 Comparação Visual (Fases DMAIC)")
    
    fig = go.Figure()
    categories = ['Define', 'Measure', 'Analyze', 'Improve', 'Control']
    
    for p in projects:
        stats = project_manager.get_project_statistics(p)
        values = [
            stats['phase_progress'].get('define', {}).get('progress', 0),
            stats['phase_progress'].get('measure', {}).get('progress', 0),
            stats['phase_progress'].get('analyze', {}).get('progress', 0),
            stats['phase_progress'].get('improve', {}).get('progress', 0),
            stats['phase_progress'].get('control', {}).get('progress', 0)
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=p['name'][:20]
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_performance_metrics(projects, project_manager):
    """Renderiza métricas de performance"""
    
    total = len(projects)
    active = len([p for p in projects if p.get('status') == 'active'])
    
    progress_values = [project_manager.calculate_project_progress(p) for p in projects]
    completed = len([p for p in progress_values if p >= 100])
    
    st.metric("Taxa de Conclusão", f"{(completed/total*100) if total > 0 else 0:.1f}%")
    st.metric("Projetos Ativos", active)
    st.metric("Projetos Concluídos", completed)


def _render_financial_analysis(projects):
    """Renderiza análise financeira"""
    
    total_savings = sum(p.get('expected_savings', 0) for p in projects)
    avg_savings = np.mean([p.get('expected_savings', 0) for p in projects]) if projects else 0
    max_savings = max([p.get('expected_savings', 0) for p in projects]) if projects else 0
    
    st.metric("Economia Total", f"R$ {total_savings:,.2f}")
    st.metric("Economia Média", f"R$ {avg_savings:,.2f}")
    st.metric("Maior Economia", f"R$ {max_savings:,.2f}")
