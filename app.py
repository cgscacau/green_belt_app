"""
Aplicação Six Sigma - Versão Ultra Robusta
"""

import streamlit as st
import sys
import os
import logging
from pathlib import Path
import time

# Configurar página ANTES de qualquer outra coisa
st.set_page_config(
    page_title="Six Sigma Green Belt",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurar logging
logging.basicConfig(level=logging.ERROR)  # Só erros críticos
logger = logging.getLogger(__name__)

# Configurar path
def setup_path():
    current_dir = Path(__file__).parent
    src_dir = current_dir / "src"
    
    for path in [str(current_dir), str(src_dir)]:
        if path not in sys.path:
            sys.path.insert(0, path)

setup_path()

# CSS customizado para resolver problemas de tema
def inject_custom_css():
    st.markdown("""
    <style>
    /* Reset de cores para evitar erros de tema */
    .stApp {
        background-color: #ffffff;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Esconder avisos de tema */
    .stAlert[data-baseweb="notification"] {
        display: none;
    }
    
    /* Remover elementos que causam erro */
    iframe[src*="ethereum"] {
        display: none !important;
    }
    
    /* Estilo para login */
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Função de inicialização simples
def init_session():
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.authentication_status = False
        st.session_state.user_data = None
        st.session_state.current_page = 'login'

# Importação segura
def safe_import_auth():
    try:
        from src.auth.firebase_auth import FirebaseAuth
        return FirebaseAuth
    except ImportError:
        try:
            from auth.firebase_auth import FirebaseAuth
            return FirebaseAuth
        except ImportError:
            return None

def safe_import_dashboard():
    try:
        from src.pages.dashboard import show_dashboard
        return show_dashboard
    except ImportError:
        try:
            from pages.dashboard import show_dashboard
            return show_dashboard
        except ImportError:
            return None

# Login simples e funcional
def show_simple_login():
    inject_custom_css()
    
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    
    st.markdown("# 🎯 Six Sigma Green Belt")
    st.markdown("### Faça login para continuar")
    
    # Tentar importar auth
    FirebaseAuth = safe_import_auth()
    
    if not FirebaseAuth:
        st.error("❌ Sistema de autenticação não disponível")
        st.info("Verifique a configuração do Firebase")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    try:
        auth = FirebaseAuth()
        
        # Formulário de login
        with st.form("login_form"):
            email = st.text_input("📧 Email")
            password = st.text_input("🔒 Senha", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                login_btn = st.form_submit_button("🚀 Entrar", type="primary")
            with col2:
                clear_btn = st.form_submit_button("🔄 Limpar")
            
            if clear_btn:
                st.rerun()
            
            if login_btn and email and password:
                with st.spinner("Autenticando..."):
                    try:
                        success, message = auth.login_user(email, password)
                        
                        if success:
                            st.success("✅ Login realizado!")
                            time.sleep(1)  # Pausa menor
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
                        logger.error(f"Erro no login: {str(e)}")
        
        # Link para registro (simplificado)
        st.markdown("---")
        st.markdown("**Não tem conta?**")
        
        with st.expander("Criar conta"):
            with st.form("register_form"):
                reg_name = st.text_input("Nome Completo")
                reg_email = st.text_input("Email")
                reg_password = st.text_input("Senha", type="password")
                
                if st.form_submit_button("Criar Conta"):
                    if reg_name and reg_email and reg_password:
                        try:
                            user_data = {
                                'name': reg_name,
                                'email': reg_email
                            }
                            success, message = auth.register_user(reg_email, reg_password, user_data)
                            
                            if success:
                                st.success("✅ Conta criada! Faça login acima.")
                            else:
                                st.error(f"❌ {message}")
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
                    else:
                        st.warning("Preencha todos os campos")
    
    except Exception as e:
        st.error(f"❌ Erro na autenticação: {str(e)}")
        logger.error(f"Erro na tela de login: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Dashboard básico garantido
def show_basic_app():
    inject_custom_css()
    
    user_data = st.session_state.get('user_data', {})
    
    st.title(f"🏠 Dashboard - {user_data.get('name', 'Usuário')}")
    
    # Tentar carregar dashboard completo
    show_dashboard = safe_import_dashboard()
    
    if show_dashboard:
        try:
            show_dashboard()
            return
        except Exception as e:
            logger.error(f"Erro no dashboard: {str(e)}")
            st.warning("⚠️ Usando modo básico...")
    
    # Dashboard básico
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📊 **Sistema Ativo**\nModo básico funcionando")
    
    with col2:
        st.info("🎯 **Metodologia**\nDMAIC Six Sigma")
    
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.authentication_status = False
            st.session_state.user_data = None
            st.rerun()
    
    st.markdown("---")
    st.success("✅ Sistema funcionando corretamente!")
    
    # Informações do usuário na sidebar
    with st.sidebar:
        st.markdown("### 👤 Usuário")
        st.write(f"**Nome:** {user_data.get('name', 'N/A')}")
        st.write(f"**Email:** {user_data.get('email', 'N/A')}")
        
        st.markdown("---")
        if st.button("🔄 Recarregar Sistema"):
            st.rerun()

# Função principal ultra-simplificada
def main():
    try:
        init_session()
        
        # Verificar autenticação
        if st.session_state.get('authentication_status') and st.session_state.get('user_data'):
            show_basic_app()
        else:
            show_simple_login()
            
    except Exception as e:
        logger.critical(f"Erro crítico: {str(e)}")
        
        st.error("❌ **Erro Crítico**")
        st.markdown("Algo deu errado. Tente:")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Recarregar"):
                st.rerun()
        with col2:
            if st.button("🗑️ Reset"):
                st.session_state.clear()
                st.rerun()

if __name__ == "__main__":
    main()
