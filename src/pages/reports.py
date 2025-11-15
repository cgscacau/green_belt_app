import streamlit as st

def show_reports_page():
    """Página de relatórios"""
    
    st.title("📋 Relatórios Científicos")
    
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
    
    st.info("🚧 Gerador de relatórios científicos - será implementado nas próximas etapas")
    
    # Preview das funcionalidades
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📄 Tipos de Relatório:
        - 📊 Relatório Executivo
        - 📈 Relatório Técnico Completo
        - 📋 Relatório de Fase DMAIC
        - 🎯 Relatório de Resultados
        - 📝 Relatório Customizado
        """)
    
    with col2:
        st.markdown("""
        ### 🎨 Formatos Disponíveis:
        - 📄 PDF Científico
        - 🌐 HTML Interativo
        - 📊 PowerPoint Executivo
        - 📈 Dashboard Online
        - 📋 Word Editável
        """)
    
    # Exemplo de seleção
    st.markdown("### 🎯 Seleção de Projeto")
    
    current_project = st.session_state.get('current_project')
    if current_project:
        st.success(f"✅ Projeto selecionado: **{current_project.get('name')}**")
        
        if st.button("📊 Gerar Relatório de Exemplo", use_container_width=True, type="primary"):
            st.balloons()
            st.success("🎉 Relatório gerado com sucesso! (funcionalidade será implementada)")
    else:
        st.warning("⚠️ Selecione um projeto primeiro para gerar relatórios")
        
        if st.button("📊 Selecionar Projeto", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.rerun()
