import streamlit as st

def show_projects_page():
    """Página de gerenciamento detalhado de projetos"""
    
    st.title("📊 Gerenciamento de Projetos")
    
    # Botão de retorno no topo
    col1, col2, col3 = st.columns([1, 4, 1])
    
    with col1:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    with col2:
        st.markdown("### Gerenciamento Avançado de Projetos")
    
    with col3:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    st.divider()
    
    # Conteúdo da página
    st.info("🚧 Página de gerenciamento detalhado de projetos - será implementada na próxima etapa")
    
    st.markdown("""
    ### Funcionalidades Planejadas:
    - 📊 Visualização avançada de projetos
    - 📈 Gráficos de performance
    - 🔄 Comparação entre projetos
    - 📋 Relatórios de status
    - ⚙️ Configurações avançadas
    """)
    
    # Exemplo de conteúdo futuro
    with st.expander("🔮 Preview das Funcionalidades"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Projetos Ativos", "3", "↗️ +1")
            st.metric("Economia Total", "R$ 125.000", "↗️ +15%")
        
        with col2:
            st.metric("Tempo Médio", "85 dias", "↘️ -10 dias")
            st.metric("Taxa de Sucesso", "87%", "↗️ +5%")
