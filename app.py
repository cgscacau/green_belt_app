import streamlit as st
import sys
import os

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.pages.login import show_login_page
from src.pages.main_navigation import show_main_navigation
from src.pages.config_check import show_config_check
from config.firebase_config import check_firebase_config

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Green Belt Six Sigma",
        page_icon="🟢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS global
    st.markdown("""
    <style>
    .main-header {
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
    .phase-progress {
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Inicializar session state
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = False
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'
    
    # Verificar configuração do Firebase
    config_status = check_firebase_config()
    config_ok = all(config_status.values())
    
    # Sidebar para debug (apenas se não estiver logado)
    if not st.session_state.get('authentication_status'):
        with st.sidebar:
            if st.button("🔧 Verificar Configuração"):
                st.session_state.show_config = True
            
            if not config_ok:
                st.error("⚠️ Configuração incompleta")
    
    # Mostrar página de configuração se necessário
    if st.session_state.get('show_config') or not config_ok:
        show_config_check()
        if st.button("🔙 Voltar"):
            st.session_state.show_config = False
            st.rerun()
        return
    
    # Roteamento principal
    if st.session_state.authentication_status:
        # Usuário logado - mostrar navegação principal
        show_main_navigation()
    else:
        # Usuário não logado - mostrar página de login
        show_login_page()

if __name__ == "__main__":
    main()
