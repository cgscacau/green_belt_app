import streamlit as st
import sys
import os

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.pages.login import show_login_page
from src.pages.dashboard import show_dashboard
from src.pages.config_check import show_config_check
from config.firebase_config import check_firebase_config

def main():
    # Inicializar session state
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = False
    
    # Verificar configuração do Firebase
    config_status = check_firebase_config()
    config_ok = all(config_status.values())
    
    # Sidebar para navegação (apenas para debug)
    with st.sidebar:
        if st.button("🔧 Verificar Configuração"):
            st.session_state.show_config = True
        
        if not config_ok:
            st.error("⚠️ Configuração incompleta")
    
    # Mostrar página de configuração se solicitado ou se config estiver incompleta
    if st.session_state.get('show_config') or not config_ok:
        show_config_check()
        if st.button("🔙 Voltar ao Login"):
            st.session_state.show_config = False
            st.rerun()
        return
    
    # Verificar status de autenticação
    if st.session_state.authentication_status:
        show_dashboard()
    else:
        show_login_page()

if __name__ == "__main__":
    main()
