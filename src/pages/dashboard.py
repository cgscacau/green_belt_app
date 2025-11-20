import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime, timedelta
from src.auth.firebase_auth import FirebaseAuth
from src.utils.navigation import NavigationManager
from src.utils.project_manager import ProjectManager
from src.utils.formatters import format_currency, format_date_br, format_number_br

def show_dashboard():
    """Dashboard principal do sistema"""
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
            if 'cached_projects' in st.session_state:
                del st.session_state.cached_projects
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
        show_projects_overview(projects, project_manager, user_data)

def show_dashboard_metrics(projects):
    """Exibe métricas principais do dashboard"""
    total_projects = len(projects)
    active_projects = len([p for p in projects if p.get('status') == 'active'])
    completed_projects = len([p for p in projects if p.get('status') == 'completed'])
    total_savings = sum([p.get('expected_savings', 0) for p in projects])
    
    if projects:
        project_manager = ProjectManager()
        total_progress = 0
        for project in projects:
            total_progress += project_manager.calculate_project_progress(project)
        avg_progress = total_progress / len(projects)
    else:
        avg_progress = 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total de Projetos", total_projects, help="Número total de projetos criados")
    
    with col2:
        st.metric("Projetos Ativos", active_projects, help="Projetos em andamento")
    
    with col3:
        st.metric("Projetos Concluídos", completed_projects, help="Projetos finalizados")
    
    with col4:
        st.metric("Economia Esperada", format_currency(total_savings), help="Soma da economia esperada de todos os projetos")
    
    with col5:
        st.metric("Progresso Médio", f"{avg_progress:.1f}%", help="Progresso médio de todos os projetos")

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
        
        **Pronto para começar?** Use a seção "Criar Projeto" abaixo para começar!
        """)
    
    with col2:
        st.markdown("### 🎯 Próximos Passos")
        st.info("1. Role para baixo até 'Criar Projeto'")
        st.info("2. Preencha as informações básicas")
        st.info("3. Comece pela fase Define")
        
        st.markdown("### 📚 Recursos")
        if st.button("📖 Tutorial DMAIC", use_container_width=True, key="tutorial_dmaic_welcome"):
            st.session_state.current_page = "help"
            st.rerun()
        
        if st.button("❓ Central de Ajuda", use_container_width=True, key="help_center_welcome"):
            st.session_state.current_page = "help"
            st.rerun()
    
    st.divider()
    show_create_project_section(project_manager, user_data, is_first_project=True)

def show_projects_overview(projects, project_manager, user_data):
    """Visão geral dos projetos existentes"""
    st.markdown("## 📊 Seus Projetos Six Sigma")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Buscar projetos", placeholder="Digite o nome do projeto...", key="search_projects")
    
    with col2:
        status_filter = st.selectbox("📋 Status", options=["Todos", "Ativo", "Concluído", "Pausado"], index=0, key="status_filter")
    
    with col3:
        show_create = st.session_state.get('show_create_project', False)
        button_text = "❌ Fechar Criação" if show_create else "➕ Novo Projeto"
        button_type = "secondary" if show_create else "primary"
        
        if st.button(button_text, use_container_width=True, type=button_type, key="toggle_create_project"):
            st.session_state.show_create_project = not show_create
            st.rerun()
    
    filtered_projects = filter_projects(projects, search_term, status_filter)
    
    if filtered_projects:
        show_projects_grid(filtered_projects, project_manager)
        
        if len(filtered_projects) > 1:
            st.divider()
            show_projects_analytics(filtered_projects)
    else:
        st.info("Nenhum projeto encontrado com os filtros aplicados.")
    
    if st.session_state.get('show_create_project'):
        st.divider()
        show_create_project_section(project_manager, user_data, is_first_project=False)

def show_create_project_section(project_manager, user_data, is_first_project=False):
    """Seção para criação de projeto"""
    
    if is_first_project:
        st.markdown("## 🎯 Criar Seu Primeiro Projeto")
        st.markdown("Preencha as informações abaixo para começar sua jornada Six Sigma:")
    else:
        st.markdown("## ➕ Criar Novo Projeto")
    
    tab1, tab2, tab3 = st.tabs(["📋 Informações Básicas", "💼 Justificativa", "📅 Cronograma"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            project_name = st.text_input(
                "Nome do Projeto *",
                placeholder="Ex: Redução de Defeitos na Linha de Produção A",
                help="Nome claro e descritivo do projeto",
                key="project_name_input"
            )
        
        with col2:
            expected_savings = st.number_input(
                "Economia Esperada (R$)",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                help="Valor estimado de economia ou ganho financeiro",
                key="project_savings_input"
            )
        
        description = st.text_area(
            "Descrição do Projeto",
            placeholder="Descreva o problema atual, oportunidade de melhoria ou objetivo do projeto...",
            help="Descrição detalhada do que será trabalhado no projeto",
            height=120,
            key="project_description_input"
        )
    
    with tab2:
        business_case = st.text_area(
            "Justificativa do Negócio",
            placeholder="Por que este projeto é importante? Qual o impacto esperado no negócio? Quais são os benefícios?",
            help="Explique a importância estratégica e o impacto esperado",
            height=120,
            key="project_business_case_input"
        )
        
        col3, col4 = st.columns(2)
        
        with col3:
            problem_statement = st.text_area(
                "Declaração do Problema",
                placeholder="Qual é o problema específico que será resolvido?",
                height=80,
                key="project_problem_input"
            )
        
        with col4:
            success_criteria = st.text_area(
                "Critérios de Sucesso",
                placeholder="Como saberemos que o projeto foi bem-sucedido?",
                height=80,
                key="project_success_input"
            )
    
    with tab3:
        col5, col6 = st.columns(2)
        
        with col5:
            start_date = st.date_input(
                "Data de Início",
                value=datetime.now().date(),
                help="Quando o projeto deve começar",
                key="project_start_date_input"
            )
        
        with col6:
            target_end_date = st.date_input(
                "Data Alvo de Conclusão",
                value=(datetime.now() + timedelta(days=120)).date(),
                help="Meta para conclusão (recomendado: 3-4 meses)",
                key="project_end_date_input"
            )
        
        date_valid = target_end_date > start_date
        
        if not date_valid:
            st.error("❌ A data de conclusão deve ser posterior à data de início")
        else:
            duration = (target_end_date - start_date).days
            
            col7, col8, col9 = st.columns(3)
            
            with col7:
                st.metric("Duração Total", f"{duration} dias")
            
            with col8:
                weeks = duration // 7
                st.metric("Duração em Semanas", f"{weeks} semanas")
            
            with col9:
                months = round(duration / 30.44, 1)
                st.metric("Duração em Meses", f"{months} meses")
            
            if duration > 180:
                st.warning("⚠️ Projeto com duração longa (>6 meses). Considere dividir em fases menores.")
            elif duration < 30:
                st.warning("⚠️ Projeto com duração muito curta (<1 mês). Verifique se é adequado para Six Sigma.")
    
    if project_name:
        st.markdown("### 📊 Resumo do Projeto")
        
        summary_col1, summary_col2 = st.columns([2, 1])
        
        with summary_col1:
            st.markdown(f"""
            **Projeto:** {project_name}
            
            **Descrição:** {description[:100]}{'...' if len(description) > 100 else ''}
            
            **Economia Esperada:** {format_currency(expected_savings)}
            
            **Duração:** {duration if date_valid else 0} dias
            """)
        
        with summary_col2:
            if date_valid:
                st.metric("Status", "✅ Pronto para criar")
                st.metric("Fase Inicial", "🎯 Define")
                st.metric("Metodologia", "📋 DMAIC")
    
    st.divider()
    
    col_action1, col_action2, col_action3, col_action4 = st.columns([2, 1, 1, 2])
    
    with col_action2:
        create_button = st.button(
            "✅ Criar Projeto",
            use_container_width=True,
            type="primary",
            disabled=not project_name or not date_valid,
            key="create_project_button"
        )
    
    with col_action3:
        clear_button = st.button(
            "🔄 Limpar Tudo",
            use_container_width=True,
            key="clear_project_form"
        )
    
    if create_button and project_name and date_valid:
        create_project_handler(project_manager, user_data, {
            'name': project_name.strip(),
            'description': description.strip(),
            'business_case': business_case.strip(),
            'problem_statement': problem_statement.strip() if 'problem_statement' in locals() else '',
            'success_criteria': success_criteria.strip() if 'success_criteria' in locals() else '',
            'expected_savings': expected_savings,
            'start_date': start_date.isoformat(),
            'target_end_date': target_end_date.isoformat()
        })
    
    if clear_button:
        clear_project_form()

def create_project_handler(project_manager, user_data, project_data):
    """Manipula a criação do projeto e navegação"""
    
    with st.spinner("🔄 Criando projeto..."):
        success, result = project_manager.create_project(user_data['uid'], project_data)
    
    if success:
        st.success("🎉 Projeto criado com sucesso!")
        st.balloons()
        
        new_project = None
        try:
            new_project = project_manager.get_project(result)
            if new_project:
                st.info(f"✅ Projeto '{new_project.get('name')}' carregado e pronto para uso!")
            else:
                st.warning("⚠️ Projeto criado mas não foi possível carregá-lo automaticamente.")
        except Exception as e:
            st.warning(f"⚠️ Projeto criado mas erro ao carregar: {str(e)}")
        
        if new_project:
            st.session_state.newly_created_project = new_project
        
        st.markdown("### 🚀 O que fazer agora?")
        
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        
        with nav_col1:
            if st.button("🎯 Começar no DMAIC", use_container_width=True, type="primary", key="start_dmaic_new"):
                if new_project:
                    st.session_state.current_project = new_project
                elif 'newly_created_project' in st.session_state:
                    st.session_state.current_project = st.session_state.newly_created_project
                
                st.session_state.current_page = "dmaic"
                st.session_state.current_dmaic_phase = "define"
                st.session_state.show_create_project = False
                
                clear_project_form()
                
                st.success("🎯 Iniciando fase Define...")
                time.sleep(1)
                st.rerun()
        
        with nav_col2:
            if st.button("📊 Ver Dashboard", use_container_width=True, key="go_dashboard_new"):
                st.session_state.show_create_project = False
                clear_project_form()
                st.success("📊 Voltando ao Dashboard...")
                time.sleep(1)
                st.rerun()
        
        with nav_col3:
            if st.button("➕ Criar Outro", use_container_width=True, key="create_another_new"):
                clear_project_form()
                st.success("🔄 Formulário limpo para novo projeto!")
                st.rerun()
    
    else:
        st.error(f"❌ Erro ao criar projeto: {result}")
        
        with st.expander("🔍 Ver Detalhes do Erro"):
            if "Firebase" in str(result):
                st.error("🔥 **Problema de Conectividade Firebase**")
                st.markdown("- Verifique sua conexão com a internet")
                st.markdown("- Teste a configuração na página de configuração")
            elif "permission" in str(result).lower():
                st.error("🔒 **Problema de Permissão**")
                st.markdown("- Verifique as regras de segurança do Firestore")
                st.markdown("- Confirme se o usuário tem permissão de escrita")
            else:
                st.error(f"📋 **Erro Técnico:** {result}")

def clear_project_form():
    """Limpa todos os campos do formulário de projeto"""
    fields_to_clear = [
        'project_name_input', 'project_description_input', 'project_business_case_input',
        'project_savings_input', 'project_start_date_input', 'project_end_date_input',
        'project_problem_input', 'project_success_input'
    ]
    
    for field in fields_to_clear:
        if field in st.session_state:
            del st.session_state[field]

def filter_projects(projects, search_term, status_filter):
    """Filtra projetos baseado nos critérios"""
    filtered = projects
    
    if search_term:
        filtered = [
            p for p in filtered 
            if search_term.lower() in p.get('name', '').lower() or 
               search_term.lower() in p.get('description', '').lower()
        ]
    
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
    cols_per_row = 2
    
    for i in range(0, len(projects), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            if i + j < len(projects):
                project = projects[i + j]
                
                with col:
                    show_project_card(project, project_manager)

#######################################################################################################################################################################################
def show_project_card(project, project_manager):
    """Exibe um card individual do projeto - Versão com container leve"""
    project_id = project.get('id', 'unknown')
    
    try:
        progress = project_manager.calculate_project_progress(project)
    except:
        progress = 0
    
    status_info = {
        'active': {'icon': '🟢', 'text': 'Ativo', 'emoji': '🟢'},
        'completed': {'icon': '✅', 'text': 'Concluído', 'emoji': '✅'},
        'paused': {'icon': '⏸️', 'text': 'Pausado', 'emoji': '⏸️'}
    }
    
    status = project.get('status', 'active')
    status_data = status_info.get(status, status_info['active'])
    
    # Formatar data de criação
    created_date = format_date_br(project.get('created_at', '')) if project.get('created_at') else 'N/A'
    
    # Formatar economia esperada
    expected_savings = project.get('expected_savings', 0)
    savings_formatted = format_currency(expected_savings)
    
    # Container com borda simples
    with st.container(border=True):
        # Header
        col_h1, col_h2 = st.columns([4, 1])
        
        with col_h1:
            st.markdown(f"### {status_data['emoji']} {project.get('name', 'Sem nome')}")
        
        with col_h2:
            st.markdown(f"**{status_data['text']}**")
        
        # Descrição
        description = project.get('description', 'Sem descrição')
        st.caption(description[:120] + ('...' if len(description) > 120 else ''))
        
        st.markdown("")  # Espaçamento
        
        # Métricas
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.metric("💰 Economia", savings_formatted)
        
        with col_m2:
            st.metric("📅 Criado em", created_date)
        
        # Progresso
        st.markdown(f"**Progresso: {progress:.1f}%**")
        st.progress(progress / 100)
        
        st.markdown("")  # Espaçamento
        
        # Botões
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 DMAIC", key=f"dmaic_{project_id[:8]}", use_container_width=True, type="primary"):
                st.session_state.current_project = project
                st.session_state.current_page = "dmaic"
                st.session_state.current_dmaic_phase = "define"
                st.success(f"✅ Abrindo: {project.get('name')}")
                time.sleep(1)
                st.rerun()
        
        with col2:
            if st.button("📊 Selecionar", key=f"select_{project_id[:8]}", use_container_width=True):
                st.session_state.current_project = project
                st.success(f"📊 Selecionado: {project.get('name')}")
                time.sleep(1)
                st.rerun()
        
        with col3:
            confirm_key = f"confirm_delete_{project_id}"
            if st.session_state.get(confirm_key):
                if st.button("⚠️ Confirmar", key=f"confirm_{project_id[:8]}", use_container_width=True):
                    with st.spinner("Excluindo..."):
                        success = project_manager.delete_project(project_id)
                    if success:
                        st.success("✅ Excluído!")
                        if confirm_key in st.session_state:
                            del st.session_state[confirm_key]
                        if st.session_state.get('current_project', {}).get('id') == project_id:
                            del st.session_state.current_project
                        time.sleep(1)
                        st.rerun()
            else:
                if st.button("🗑️ Excluir", key=f"delete_{project_id[:8]}", use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.rerun()



#############################################################################################################################################################################################################

def show_projects_analytics(projects):
    """Exibe gráficos analíticos dos projetos"""
    st.markdown("### 📈 Análises dos Projetos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        status_counts = {}
        status_labels = {'active': 'Ativo', 'completed': 'Concluído', 'paused': 'Pausado'}
        
        for project in projects:
            status = project.get('status', 'active')
            label = status_labels.get(status, status)
            status_counts[label] = status_counts.get(label, 0) + 1
        
        if status_counts:
            fig_status = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title="Distribuição por Status",
                color_discrete_map={
                    'Ativo': '#28a745',
                    'Concluído': '#007bff',
                    'Pausado': '#ffc107'
                }
            )
            fig_status.update_layout(height=400)
            st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        project_names = [p.get('name', f"Projeto {i+1}")[:20] for i, p in enumerate(projects)]
        project_manager = ProjectManager()
        progress_values = [project_manager.calculate_project_progress(p) for p in projects]
        
        fig_progress = px.bar(
            x=progress_values,
            y=project_names,
            orientation='h',
            title="Progresso dos Projetos (%)",
            labels={'x': 'Progresso (%)', 'y': 'Projetos'},
            color=progress_values,
            color_continuous_scale='Viridis'
        )
        fig_progress.update_layout(height=400)
        st.plotly_chart(fig_progress, use_container_width=True)
    
    if len(projects) >= 3:
        st.markdown("### 📊 Estatísticas Adicionais")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            max_savings_project = max(projects, key=lambda x: x.get('expected_savings', 0))
            st.metric(
                "Maior Economia Esperada",
                format_currency(max_savings_project.get('expected_savings', 0)),
                delta=max_savings_project.get('name', 'N/A')[:20]
            )
        
        with col4:
            max_progress_project = max(projects, key=lambda x: project_manager.calculate_project_progress(x))
            max_progress = project_manager.calculate_project_progress(max_progress_project)
            st.metric(
                "Maior Progresso",
                f"{max_progress:.1f}%",
                delta=max_progress_project.get('name', 'N/A')[:20]
            )
        
        with col5:
            total_days = 0
            count = 0
            for project in projects:
                start_date = project.get('start_date')
                end_date = project.get('target_end_date')
                if start_date and end_date:
                    try:
                        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                        total_days += (end - start).days
                        count += 1
                    except:
                        pass
            
            avg_days = total_days // count if count > 0 else 0
            st.metric(
                "Duração Média",
                f"{avg_days} dias",
                delta=f"≈ {avg_days//30} meses" if avg_days > 0 else "N/A"
            )
