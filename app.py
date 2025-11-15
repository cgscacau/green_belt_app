import streamlit as st
import sys
import os

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.pages.login import show_login_page
from src.pages.dashboard import show_dashboard

def main():
    # Inicializar session state
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = False
    
    # Verificar status de autenticação
    if st.session_state.authentication_status:
        show_dashboard()
    else:
        show_login_page()

if __name__ == "__main__":
    main()
