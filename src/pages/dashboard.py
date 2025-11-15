import streamlit as st
import time
from src.auth.firebase_auth import FirebaseAuth

def show_dashboard():
    if not st.session_state.get('authentication_status'):
        st.error("Acesso negado. Faça login primeiro.")
        return
    
    user_data = st.session_state.user_data
    
    # Header com informações do usuário
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title(f"🟢 Bem-vindo, {user_data['name']}!")
        if user_data.get('company'):
            st.caption(f"📍 {user_data['company']}")
    
    with col3:
        if st.button("🚪 Logout"):
            auth = FirebaseAuth()
            auth.logout_user()
            st.rerun()
    
    st.divider()
    
    # Métricas do usuário
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Projetos Ativos", len(user_data.get('projects', [])))
    
    with col2:
        st.metric("Projetos Concluídos", 0)  # Será implementado nas próximas etapas
    
    with col3:
        st.metric("Economia Gerada", "R$ 0")  # Será implementado nas próximas etapas
    
    with col4:
        st.metric("Tempo Médio", "0 dias")  # Será implementado nas próximas etapas
    
    st.divider()
    
    # Área principal - será expandida nas próximas etapas
    st.markdown("### 🚀 Seus Projetos Six Sigma")
    
    if not user_data.get('projects'):
        st.info("Você ainda não possui projetos. Clique no botão abaixo para criar seu primeiro projeto!")
        
        if st.button("➕ Criar Primeiro Projeto", use_container_width=True):
            st.session_state.show_create_project = True
            st.rerun()
    else:
        # Lista de projetos - será implementado nas próximas etapas
        st.write("Lista de projetos será implementada na próxima etapa")
    
    # Sidebar com navegação DMAIC - preview para próximas etapas
    with st.sidebar:
        st.markdown("### 📋 Metodologia DMAIC")
        
        phases = [
            ("🎯", "Define", "Definir o problema"),
            ("📏", "Measure", "Medir o processo atual"),
            ("🔍", "Analyze", "Analisar causas raiz"),
            ("⚡", "Improve", "Implementar melhorias"),
            ("🎛️", "Control", "Controlar o processo")
        ]
        
        for icon, phase, description in phases:
            with st.expander(f"{icon} {phase}"):
                st.caption(description)
                st.info("Disponível após criar um projeto")
