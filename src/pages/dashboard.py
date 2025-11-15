import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime, timedelta
from src.auth.firebase_auth import FirebaseAuth
from src.utils.navigation import NavigationManager
from src.utils.project_manager import ProjectManager

def show_dashboard():
    if not st.session_state.get('authentication_status'):
        st.error("Acesso negado. Faça login primeiro.")
        return
    
    user_data = st.session_state.user_data
    nav_manager = NavigationManager()
    project_manager = ProjectManager()
    
    # Header principal
    col1, col2, col3 = st.columns([4, 1, 1])
    
    with col1:
        st.title(f"🏠 Dashboard - {user_data['name']}")
        if user_data.get('company'):
            st.caption(f"📍 {user_data['company']}")
    
    with col2:
        if st.button("🔄 Atualizar", use_container_width=True, key="refresh_dashboard"):
            st.rerun()
    
    with col3:
        if st.button("🚪 Logout", use_container_width=True, key="logout_dashboard"):
            auth = FirebaseAuth()
            auth.logout_user()
            st.rerun()
    
    st.divider()
    
    # Carregar projetos do usuário
    with st.spinner("📊 Carregando projetos..."):
        projects = project_manager.get_user_projects(user_data['uid'])
    
    # Métricas principais
    show_dashboard_metrics(projects)
    
    st.divider()
    
    # Conteúdo principal baseado na existência de projetos
    if not projects:
        show_welcome_section(project_manager, user_data)
    else:
        show_projects_overview(projects, project_manager)
    
    # Modal para criar projeto (sempre verificar)
    if st.session_state.get('show_create_project'):
        show_create_project_modal(project_manager, user_data)

def show_dashboard_metrics(projects):
    """Exibe métricas principais do dashboard"""
    # Calcular métricas
    total_projects = len(projects)
    active_projects = len([p for p in projects if p.get('status') == 'active'])
    completed_projects = len([p for p in projects if p.get('status') == 'completed'])
    total_savings = sum([p.get('expected_savings', 0) for p in projects])
    
    # Média de progresso
    if projects:
        avg_progress = sum([p.get('overall_progress', 0) for p in projects]) / len(projects)
    else:
        avg_progress = 0
    
    # Layout das métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total de Projetos", 
            total_projects,
            help="Número total de projetos criados"
        )
    
    with col2:
        st.metric(
            "Projetos Ativos", 
            active_projects,
            help="Projetos em andamento"
        )
    
    with col3:
        st.metric(
            "Projetos Concluídos", 
            completed_projects,
            help="Projetos finalizados"
        )
    
    with col4:
        st.metric(
            "Economia Esperada", 
            f"R$ {total_savings:,.2f}",
            help="Soma da economia esperada de todos os projetos"
        )
    
    with col5:
        st.metric(
            "Progresso Médio", 
            f"{avg_progress:.1f}%",
            help="Progresso médio de todos os projetos"
        )

def show_welcome_section(project_manager, user_data):
    """Seção de boas-vindas para novos usuários"""
    st.markdown("## 🚀 Bem-vindo ao Green Belt Six Sigma!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Comece sua jornada Six Sigma
        
        Este sistema foi desenvolvido para guiá-lo através da metodologia DMAIC 
        (Define, Measure, Analyze, Improve, Control) de forma estruturada e eficiente.
        
        **O que você pode fazer:**
        - ✅ Criar e gerenciar projetos Six Sigma
        - 📊 Realizar análises estatísticas avançadas
        - 📋 Gerar relatórios científicos profissionais
        - 🎯 Acompanhar o progresso através das fases DMAIC
        - 🔧 Utilizar ferramentas de qualidade integradas
        
        **Pronto para começar?** Clique no botão ao lado para criar seu primeiro projeto!
        """)
    
    with col2:
        st.markdown("### 🎯 Criar Primeiro Projeto")
        
        if st.button("➕ Novo Projeto", use_container_width=True, type="primary", key="create_first_project"):
            st.session_state.show_create_project = True
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("### 📚 Recursos")
        if st.button("📖 Tutorial DMAIC", use_container_width=True, key="tutorial_dmaic"):
            st.session_state.current_page = "help"
            st.rerun()
        
        if st.button("❓ Central de Ajuda", use_container_width=True, key="help_center"):
            st.session_state.current_page = "help"
            st.rerun()

def show_projects_overview(projects, project_manager):
    """Visão geral dos projetos existentes"""
    st.markdown("## 📊 Seus Projetos Six Sigma")
    
    # Filtros e controles
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Buscar projetos", placeholder="Digite o nome do projeto...", key="search_projects")
    
    with col2:
        status_filter = st.selectbox(
            "📋 Status",
            options=["Todos", "Ativo", "Concluído", "Pausado"],
            index=0,
            key="status_filter"
        )
    
    with col3:
        if st.button("➕ Novo Projeto", use_container_width=True, type="primary", key="create_new_project"):
            st.session_state.show_create_project = True
            st.rerun()
    
    # Filtrar projetos
    filtered_projects = filter_projects(projects, search_term, status_filter)
    
    # Exibir projetos
    if filtered_projects:
        show_projects_grid(filtered_projects, project_manager)
        
        # Gráficos de análise
        if len(filtered_projects) > 1:
            show_projects_analytics(filtered_projects)
    else:
        st.info("Nenhum projeto encontrado com os filtros aplicados.")

def filter_projects(projects, search_term, status_filter):
    """Filtra projetos baseado nos critérios"""
    filtered = projects
    
    # Filtro por termo de busca
    if search_term:
        filtered = [
            p for p in filtered 
            if search_term.lower() in p.get('name', '').lower() or 
               search_term.lower() in p.get('description', '').lower()
        ]
    
    # Filtro por status
    if status_filter != "Todos":
        status_map = {
            "Ativo": "active",
            "Concluído": "completed",
            "Pausado": "paused"
        }
        filtered = [p for p in filtered if p.get('status') == status_map[status_filter]]
    
    return filtered

def show_projects_grid(projects, project_manager):
    """Exibe projetos em formato de grid"""
    # Organizar projetos em colunas
    cols_per_row = 2
    
    for i in range(0, len(projects), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            if i + j < len(projects):
                project = projects[i + j]
                
                with col:
                    show_project_card(project, project_manager)

def show_project_card(project, project_manager):
    """Exibe um card individual do projeto"""
    # Gerar ID único para este card
    card_id = f"{project['id']}_{int(time.time() * 1000) % 10000}"
    
    # Calcular progresso
    progress = project_manager.calculate_project_progress(project)
    
    # Status styling
    status_colors = {
        'active': '🟢',
        'completed': '✅',
        'paused': '⏸️'
    }
    
    status_icon = status_colors.get(project.get('status', 'active'), '🟢')
    
    with st.container():
        st.markdown(f"""
        <div style='border: 1px solid #ddd; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; background-color: #f9f9f9;'>
            <h4>{status_icon} {project.get('name', 'Sem nome')}</h4>
            <p style='color: #666; font-size: 0.9em;'>{project.get('description', 'Sem descrição')[:100]}...</p>
            <div style='margin: 0.5rem 0;'>
                <small>💰 Economia esperada: R$ {project.get('expected_savings', 0):,.2f}</small><br>
                <small>📅 Criado: {project.get('created_at', '')[:10]}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Barra de progresso
        st.progress(progress / 100)
        st.caption(f"Progresso: {progress:.1f}%")
        
        # Botões de ação com chaves únicas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📂 Abrir", key=f"open_{card_id}", use_container_width=True):
                st.session_state.current_project = project
                st.session_state.current_page = "dmaic"
                st.session_state.current_dmaic_phase = project.get('current_phase', 'define')
                st.rerun()
        
        with col2:
            if st.button("✏️ Editar", key=f"edit_{card_id}", use_container_width=True):
                st.session_state.edit_project = project
                st.rerun()
        
        with col3:
            # Verificar se já foi clicado para confirmar
            confirm_key = f"confirm_delete_{project['id']}"
            if st.session_state.get(confirm_key):
                if st.button("⚠️ Confirmar", key=f"confirm_delete_{card_id}", use_container_width=True, type="primary"):
                    success = project_manager.delete_project(project['id'], project['user_uid'])
                    if success:
                        st.success("Projeto excluído!")
                        # Limpar estado de confirmação
                        if confirm_key in st.session_state:
                            del st.session_state[confirm_key]
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro ao excluir projeto")
            else:
                if st.button("🗑️ Excluir", key=f"delete_{card_id}", use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.rerun()

def show_projects_analytics(projects):
    """Exibe gráficos analíticos dos projetos"""
    st.markdown("### 📈 Análises dos Projetos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de status dos projetos
        status_counts = {}
        for project in projects:
            status = project.get('status', 'active')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            fig_status = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title="Distribuição por Status"
            )
            st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        # Gráfico de progresso dos projetos
        project_names = [p.get('name', f"Projeto {i+1}")[:20] for i, p in enumerate(projects)]
        progress_values = [p.get('overall_progress', 0) for p in projects]
        
        fig_progress = px.bar(
            x=progress_values,
            y=project_names,
            orientation='h',
            title="Progresso dos Projetos (%)",
            labels={'x': 'Progresso (%)', 'y': 'Projetos'}
        )
        fig_progress.update_layout(height=400)
        st.plotly_chart(fig_progress, use_container_width=True)

@st.dialog("➕ Criar Novo Projeto")
def show_create_project_modal(project_manager, user_data):
    """Modal para criação de novo projeto usando st.dialog"""
    
    st.markdown("### Informações do Projeto")
    
    with st.form("create_project_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            project_name = st.text_input(
                "🎯 Nome do Projeto *",
                placeholder="Ex: Redução de Defeitos na Linha 1",
                help="Nome claro e descritivo do projeto",
                key="new_project_name"
            )
            
            description = st.text_area(
                "📝 Descrição",
                placeholder="Descreva brevemente o problema ou oportunidade...",
                help="Descrição detalhada do projeto",
                key="new_project_description"
            )
        
        with col2:
            business_case = st.text_area(
                "💼 Caso de Negócio",
                placeholder="Justificativa do projeto, impacto no negócio...",
                help="Por que este projeto é importante?",
                key="new_project_business_case"
            )
            
            expected_savings = st.number_input(
                "💰 Economia Esperada (R$)",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                help="Valor estimado de economia ou ganho",
                key="new_project_savings"
            )
        
        col3, col4 = st.columns(2)
        
        with col3:
            start_date = st.date_input(
                "📅 Data de Início",
                value=datetime.now().date(),
                help="Data prevista para início do projeto",
                key="new_project_start_date"
            )
        
        with col4:
            target_end_date = st.date_input(
                "🎯 Data Alvo de Conclusão",
                value=(datetime.now() + timedelta(days=120)).date(),
                help="Data prevista para conclusão (padrão: 120 dias)",
                key="new_project_end_date"
            )
        
        # Validação de datas
        if target_end_date <= start_date:
            st.error("❌ A data de conclusão deve ser posterior à data de início")
        
        # Botões do formulário
        col5, col6 = st.columns([1, 1])
        
        with col5:
            submit_button = st.form_submit_button(
                "✅ Criar Projeto", 
                use_container_width=True, 
                type="primary",
                disabled=not project_name or target_end_date <= start_date
            )
        
        with col6:
            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                st.session_state.show_create_project = False
                st.rerun()
        
        if submit_button:
            if project_name and target_end_date > start_date:
                # Mostrar spinner durante criação
                with st.spinner("🔄 Criando projeto..."):
                    project_data = {
                        'name': project_name,
                        'description': description,
                        'business_case': business_case,
                        'expected_savings': expected_savings,
                        'start_date': start_date.isoformat(),
                        'target_end_date': target_end_date.isoformat()
                    }
                    
                    success, result = project_manager.create_project(user_data['uid'], project_data)
                
                if success:
                    st.success("✅ Projeto criado com sucesso!")
                    st.balloons()
                    
                    # Aguardar um momento e fechar modal
                    time.sleep(2)
                    st.session_state.show_create_project = False
                    
                    # Limpar campos do formulário
                    for key in ['new_project_name', 'new_project_description', 'new_project_business_case', 
                               'new_project_savings', 'new_project_start_date', 'new_project_end_date']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.rerun()
                else:
                    st.error(f"❌ Erro ao criar projeto: {result}")
                    
                    # Debug: mostrar detalhes do erro se disponível
                    if "Firebase" in str(result):
                        st.error("🔥 Erro de conexão com Firebase. Verifique sua conexão com a internet.")
                    elif "permission" in str(result).lower():
                        st.error("🔒 Erro de permissão. Verifique suas credenciais.")
                    else:
                        st.error(f"📋 Detalhes: {result}")
            else:
                if not project_name:
                    st.error("❌ Nome do projeto é obrigatório")
                if target_end_date <= start_date:
                    st.error("❌ Data de conclusão deve ser posterior à data de início")
