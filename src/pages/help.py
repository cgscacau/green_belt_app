import streamlit as st

def show_help_page():
    """Página de ajuda e tutoriais"""
    
    st.title("❓ Central de Ajuda")
    
    # Navegação no topo
    col1, col2, col3 = st.columns([1, 4, 1])
    
    with col1:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    with col2:
        st.markdown("### Tutoriais e Documentação DMAIC")
    
    with col3:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    st.divider()
    
    # Tabs de ajuda
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Tutoriais", "🔧 Como Usar", "📊 Ferramentas", "❓ FAQ"])
    
    with tab1:
        st.markdown("## 📚 Tutoriais DMAIC")
        
        tutorials = [
            ("🎯 Introdução ao Six Sigma", "Conceitos básicos e metodologia DMAIC"),
            ("📋 Como criar um projeto", "Passo a passo para iniciar seu projeto"),
            ("📊 Análise estatística", "Ferramentas estatísticas essenciais"),
            ("📈 Interpretação de resultados", "Como analisar e apresentar dados"),
            ("📋 Geração de relatórios", "Criando relatórios científicos profissionais")
        ]
        
        for title, description in tutorials:
            with st.expander(title):
                st.info(f"🚧 {description} - Tutorial será implementado nas próximas etapas")
    
    with tab2:
        st.markdown("## 🔧 Como Usar o Sistema")
        
        st.markdown("""
        ### 🚀 Primeiros Passos
        
        1. **Criar Projeto**: Clique em "➕ Novo Projeto" no dashboard
        2. **Definir Objetivos**: Preencha o charter na fase Define
        3. **Coletar Dados**: Upload de arquivos na fase Measure
        4. **Analisar**: Use as ferramentas estatísticas na fase Analyze
        5. **Implementar**: Crie planos de ação na fase Improve
        6. **Controlar**: Configure monitoramento na fase Control
        
        ### 🧭 Navegação
        
        - Use o **breadcrumb** no topo para navegar entre páginas
        - A **sidebar** mostra navegação principal e fases DMAIC
        - O **dashboard** é sua página inicial com visão geral
        
        ### 💡 Dicas
        
        - Salve seu trabalho frequentemente
        - Complete uma fase antes de avançar
        - Use os tooltips para orientação
        - Consulte os tutoriais quando necessário
        """)
    
    with tab3:
        st.markdown("## 📊 Ferramentas Disponíveis")
        
        tools_by_phase = {
            "🎯 Define": [
                "Project Charter",
                "Stakeholder Map", 
                "Voice of Customer (VOC)",
                "SIPOC Diagram",
                "Timeline do Projeto"
            ],
            "📏 Measure": [
                "Plano de Coleta de Dados",
                "Upload de Arquivos (Excel, CSV, PDF, TXT)",
                "Análise de Sistema de Medição (MSA)",
                "Estudos de Capacidade",
                "Métricas CTQ"
            ],
            "🔍 Analyze": [
                "Diagrama de Ishikawa",
                "5 Porquês",
                "Análise de Pareto",
                "Testes de Hipóteses",
                "Análises Estatísticas Avançadas"
            ],
            "⚡ Improve": [
                "Brainstorming de Soluções",
                "Matriz de Priorização",
                "Plano de Ação",
                "Análise de Risco",
                "Validação de Melhorias"
            ],
            "🎛️ Control": [
                "Cartas de Controle",
                "Plano de Controle",
                "Documentação de Processos",
                "Sistema de Monitoramento"
            ]
        }
        
        for phase, tools in tools_by_phase.items():
            with st.expander(phase):
                for tool in tools:
                    st.markdown(f"- ✅ {tool}")
    
    with tab4:
        st.markdown("## ❓ Perguntas Frequentes")
        
        faqs = [
            ("Como criar meu primeiro projeto?", "Clique em '➕ Novo Projeto' no dashboard e preencha as informações básicas."),
            ("Posso fazer upload de quais tipos de arquivo?", "O sistema aceita Excel (.xlsx, .xls), CSV, PDF e TXT."),
            ("Como navegar entre as fases DMAIC?", "Use a sidebar à esquerda ou os botões de navegação rápida em cada fase."),
            ("Os dados ficam salvos automaticamente?", "Sim, todas as alterações são salvas automaticamente no Firebase."),
            ("Posso trabalhar em múltiplos projetos?", "Sim, você pode criar e gerenciar quantos projetos precisar."),
            ("Como gerar relatórios?", "Acesse a página 'Relatórios' e selecione o projeto desejado."),
            ("Há limite de usuários por conta?", "Cada conta é individual. Para uso corporativo, entre em contato."),
            ("Como recuperar minha senha?", "Use a opção 'Esqueci a senha' na tela de login."),
        ]
        
        for question, answer in faqs:
            with st.expander(question):
                st.markdown(answer)
    
    # Suporte
    st.divider()
    st.markdown("### 🆘 Precisa de Mais Ajuda?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Contato", use_container_width=True):
            st.info("Email: suporte@greenbelt.com")
    
    with col2:
        if st.button("💬 Chat", use_container_width=True):
            st.info("Chat online em breve!")
    
    with col3:
        if st.button("📖 Documentação", use_container_width=True):
            st.info("Documentação completa em desenvolvimento")
