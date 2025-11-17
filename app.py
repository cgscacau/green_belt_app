"""
Aplicação Six Sigma - Usando sua configuração Firebase que funciona
"""

import streamlit as st
import sys
import os
import logging
from pathlib import Path
import time

# Configurar página
st.set_page_config(
    page_title="Six Sigma Green Belt",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurar logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Configurar path
def setup_path():
    current_dir = Path(__file__).parent
    src_dir = current_dir / "src"
    
    for path in [str(current_dir), str(src_dir)]:
        if path not in sys.path:
            sys.path.insert(0, path)

setup_path()

# CSS básico
def inject_custom_css():
    st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
    }
    
    .stAlert[data-baseweb="notification"] {
        display: none;
    }
    
    iframe[src*="ethereum"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialização simples
def init_session():
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.authentication_status = False
        st.session_state.user_data = None

# Importações usando seu código
def get_firebase_auth():
    try:
        from src.auth.firebase_auth import FirebaseAuth
        return FirebaseAuth()
    except ImportError:
        try:
            from auth.firebase_auth import FirebaseAuth
            return FirebaseAuth()
        except ImportError:
            return None

def get_dashboard():
    try:
        from src.pages.dashboard import show_dashboard
        return show_dashboard
    except ImportError:
        try:
            from pages.dashboard import show_dashboard
            return show_dashboard
        except ImportError:
            return None

# Login simples que funcionava
def show_simple_login():
    inject_custom_css()
    
    st.markdown("# 🎯 Six Sigma Green Belt")
    st.markdown("### Sistema de Gerenciamento de Projetos Six Sigma")
    
    firebase_auth = get_firebase_auth()
    
    if not firebase_auth:
        st.error("❌ Sistema de autenticação não disponível")
        return
    
    # Formulário de login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "👤 Registro"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("📧 Email")
                password = st.text_input("🔒 Senha", type="password")
                
                login_btn = st.form_submit_button("🚀 Entrar", type="primary", use_container_width=True)
                
                if login_btn and email and password:
                    with st.spinner("Autenticando..."):
                        try:
                            # Usar SUA classe FirebaseAuth original
                            success, result = firebase_auth.login_user(email, password)
                            
                            if success:
                                # result contém os dados do usuário
                                st.session_state.authentication_status = True
                                st.session_state.user_data = result
                                
                                st.success("✅ Login realizado com sucesso!")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(result)
                                
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
        
        with tab2:
            with st.form("register_form"):
                reg_name = st.text_input("Nome Completo")
                reg_email = st.text_input("Email")
                reg_company = st.text_input("Empresa (opcional)")
                reg_password = st.text_input("Senha", type="password")
                
                reg_btn = st.form_submit_button("Criar Conta", type="primary", use_container_width=True)
                
                if reg_btn and reg_name and reg_email and reg_password:
                    with st.spinner("Criando conta..."):
                        try:
                            # Usar SUA classe FirebaseAuth original
                            success, message = firebase_auth.register_user(
                                reg_email, reg_password, reg_name, reg_company
                            )
                            
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                                
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")

# Aplicação principal simples
# Na função show_main_app(), substitua por:
def show_main_app():
    inject_custom_css()
    
    user_data = st.session_state.get('user_data', {})
    
    # Debug: mostrar informações na sidebar
    with st.sidebar:
        st.markdown("### 🔍 Debug Info")
        st.write(f"**Usuário:** {user_data.get('name', 'N/A')}")
        st.write(f"**Email:** {user_data.get('email', 'N/A')}")
        st.write(f"**UID:** {user_data.get('uid', 'N/A')[:8] if user_data.get('uid') else 'N/A'}...")
        
        # Verificar se consegue importar dashboard
        dashboard_func = get_dashboard()
        st.write(f"**Dashboard importado:** {'✅ Sim' if dashboard_func else '❌ Não'}")
        
        if st.button("🔄 Tentar Recarregar Dashboard"):
            st.rerun()
    
    # Tentar carregar dashboard completo
    dashboard_func = get_dashboard()
    
    if dashboard_func:
        try:
            st.info("🔄 Carregando dashboard completo...")
            dashboard_func()
            return
        except Exception as e:
            st.error(f"❌ Erro no dashboard completo: {str(e)}")
            
            # Mostrar detalhes do erro
            with st.expander("🔍 Detalhes do erro"):
                import traceback
                st.code(traceback.format_exc())
            
            st.warning("⚠️ Usando dashboard básico como fallback...")
    else:
        st.warning("⚠️ Dashboard completo não encontrado, usando básico...")
    
    # Dashboard básico como fallback
    show_basic_dashboard(user_data)

def show_basic_dashboard(user_data):
    """Dashboard básico funcional"""
    st.title(f"🏠 Dashboard Básico - {user_data.get('name', 'Usuário')}")
    
    if user_data.get('company'):
        st.caption(f"🏢 {user_data['company']}")
    
    st.warning("⚠️ **Modo Básico Ativo** - O dashboard completo não pôde ser carregado")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("✅ **Login OK**\nAutenticação funcionando")
    
    with col2:
        st.info("🎯 **Sistema**\nDMAIC Six Sigma")
    
    with col3:
        if st.button("🚪 Logout", type="secondary"):
            firebase_auth = get_firebase_auth()
            if firebase_auth:
                firebase_auth.logout_user()
            st.session_state.authentication_status = False
            st.session_state.user_data = None
            st.rerun()
    
    st.markdown("---")
    
    # Informações sobre o problema
    st.markdown("### 🔧 Diagnóstico")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **✅ Funcionando:**
        - Login com Firebase Auth
        - Dados do usuário carregados
        - Interface básica ativa
        """)
    
    with col2:
        st.markdown("""
        **⚠️ Problemas detectados:**
        - Dashboard completo não carrega
        - Firestore pode não estar conectado
        - Interface limitada
        """)
    
    # Botões de ação
    st.markdown("### 🚀 Ações")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Recarregar Sistema", type="primary"):
            st.rerun()
    
    with col2:
        if st.button("🗑️ Limpar Cache"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Cache limpo!")
            time.sleep(1)
            st.rerun()
    
    with col3:
        if st.button("📊 Forçar Dashboard"):
            # Tentar forçar carregamento do dashboard
            try:
                from src.pages.dashboard import show_dashboard
                show_dashboard()
            except Exception as e:
                st.error(f"Erro: {str(e)}")
