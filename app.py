"""
Aplicação principal do sistema Six Sigma Green Belt
Versão corrigida com transição de login robusta
"""

import streamlit as st
import sys
import os
import logging
import traceback
from pathlib import Path
from typing import Optional, Dict, Any
import time
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuração da página (deve ser a primeira chamada Streamlit)
st.set_page_config(
    page_title="Six Sigma Green Belt",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Six Sigma Green Belt System v2.0"
    }
)

# Configurar path do Python
def setup_python_path():
    """Configura o path do Python para imports"""
    try:
        current_dir = Path(__file__).parent
        src_dir = current_dir / "src"
        
        paths_to_add = [str(current_dir), str(src_dir)]
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
        
        return True
    except Exception as e:
        logger.error(f"Erro ao configurar Python path: {str(e)}")
        return False

setup_python_path()

# Função para importar módulos com fallback
def safe_import():
    """Importa módulos de forma segura"""
    modules = {}
    
    # Firebase Auth
    try:
        from src.auth.firebase_auth import FirebaseAuth
        modules['auth'] = FirebaseAuth
    except ImportError:
        try:
            from auth.firebase_auth import FirebaseAuth
            modules['auth'] = FirebaseAuth
        except ImportError:
            modules['auth'] = None
    
    # Dashboard
    try:
        from src.pages.dashboard import show_dashboard
        modules['dashboard'] = show_dashboard
    except ImportError:
        try:
            from pages.dashboard import show_dashboard
            modules['dashboard'] = show_dashboard
        except ImportError:
            modules['dashboard'] = None
    
    # Navegação principal
    try:
        from src.pages.main_navigation import show_main_navigation
        modules['navigation'] = show_main_navigation
    except ImportError:
        try:
            from pages.main_navigation import show_main_navigation
            modules['navigation'] = show_main_navigation
        except ImportError:
            modules['navigation'] = None
    
    return modules

# Importar módulos
MODULES = safe_import()

def initialize_session():
    """Inicializa session state com valores padrão"""
    defaults = {
        'authentication_status': False,
        'user_data': None,
        'current_page': 'dashboard',
        'app_initialized': True
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_login_page():
    """Página de login simplificada"""
    st.markdown("# 🎯 Six Sigma Green Belt")
    st.markdown("### Sistema de Gerenciamento de Projetos Six Sigma")
    
    # Verificar se Firebase Auth está disponível
    if not MODULES.get('auth'):
        st.error("❌ Sistema de autenticação não disponível")
        st.info("Verifique a configuração do Firebase")
        return
    
    # Criar instância do auth
    try:
        auth = MODULES['auth']()
    except Exception as e:
        st.error(f"❌ Erro ao inicializar autenticação: {str(e)}")
        return
    
    # Interface de login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "👤 Registro"])
        
        with tab1:
            st.markdown("#### Faça login em sua conta")
            
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("📧 Email", placeholder="seu.email@exemplo.com")
                password = st.text_input("🔒 Senha", type="password", placeholder="••••••••")
                
                submitted = st.form_submit_button("🚀 Entrar", type="primary", use_container_width=True)
                
                if submitted:
                    if email and password:
                        try:
                            with st.spinner("Autenticando..."):
                                success, message = auth.login_user(email, password)
                            
                            if success:
                                st.success("✅ Login realizado com sucesso!")
                                st.balloons()
                                
                                # ✅ CORREÇÃO: Aguardar um pouco antes de recarregar
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"❌ Erro no login: {message}")
                        except Exception as e:
                            st.error(f"❌ Erro inesperado: {str(e)}")
                            logger.error(f"Erro no login: {str(e)}")
                    else:
                        st.warning("⚠️ Preencha email e senha")
        
        with tab2:
            st.markdown("#### Criar nova conta")
            
            with st.form("register_form", clear_on_submit=False):
                reg_name = st.text_input("👤 Nome Completo")
                reg_email = st.text_input("📧 Email")
                reg_company = st.text_input("🏢 Empresa (opcional)")
                reg_password = st.text_input("🔒 Senha", type="password")
                reg_password_confirm = st.text_input("🔒 Confirmar Senha", type="password")
                
                reg_submitted = st.form_submit_button("🎯 Criar Conta", type="primary", use_container_width=True)
                
                if reg_submitted:
                    # Validações básicas
                    if not all([reg_name, reg_email, reg_password]):
                        st.error("❌ Preencha todos os campos obrigatórios")
                    elif reg_password != reg_password_confirm:
                        st.error("❌ Senhas não coincidem")
                    elif len(reg_password) < 6:
                        st.error("❌ Senha deve ter pelo menos 6 caracteres")
                    else:
                        try:
                            user_data = {
                                'name': reg_name.strip(),
                                'email': reg_email.strip().lower(),
                                'company': reg_company.strip() if reg_company else None
                            }
                            
                            with st.spinner("Criando conta..."):
                                success, message = auth.register_user(reg_email, reg_password, user_data)
                            
                            if success:
                                st.success("✅ Conta criada com sucesso!")
                                st.info("🔑 Você pode fazer login agora na aba 'Login'")
                            else:
                                st.error(f"❌ Erro ao criar conta: {message}")
                        except Exception as e:
                            st.error(f"❌ Erro inesperado: {str(e)}")
                            logger.error(f"Erro no registro: {str(e)}")

def show_main_app():
    """Aplicação principal"""
    try:
        # ✅ CORREÇÃO: Verificar se user_data existe e é válido
        user_data = st.session_state.get('user_data')
        if not user_data:
            st.error("❌ Dados do usuário não encontrados")
            
            # Botão para fazer logout e voltar ao login
            if st.button("🚪 Voltar ao Login"):
                st.session_state.authentication_status = False
                st.session_state.user_data = None
                st.rerun()
            return
        
        # ✅ CORREÇÃO: Tentar usar navegação principal primeiro
        if MODULES.get('navigation'):
            try:
                MODULES['navigation']()
                return
            except Exception as e:
                logger.error(f"Erro na navegação principal: {str(e)}")
                st.warning("⚠️ Problema na navegação principal, usando dashboard básico...")
        
        # ✅ CORREÇÃO: Fallback para dashboard se navegação falhar
        if MODULES.get('dashboard'):
            try:
                MODULES['dashboard']()
                return
            except Exception as e:
                logger.error(f"Erro no dashboard: {str(e)}")
                st.error("❌ Erro ao carregar dashboard")
        
        # ✅ CORREÇÃO: Dashboard básico como último recurso
        show_basic_dashboard(user_data)
        
    except Exception as e:
        logger.error(f"Erro na aplicação principal: {str(e)}")
        st.error("❌ Erro na aplicação principal")
        
        # Mostrar detalhes do erro e opções de recuperação
        with st.expander("🔍 Detalhes do erro"):
            st.code(f"Erro: {str(e)}\n\n{traceback.format_exc()}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Tentar Novamente"):
                st.rerun()
        with col2:
            if st.button("🚪 Fazer Logout"):
                st.session_state.authentication_status = False
                st.session_state.user_data = None
                st.rerun()

def show_basic_dashboard(user_data):
    """Dashboard básico como fallback"""
    st.title(f"🏠 Dashboard - {user_data.get('name', 'Usuário')}")
    
    if user_data.get('company'):
        st.caption(f"🏢 {user_data['company']}")
    
    st.markdown("---")
    
    # Informações básicas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📊 **Sistema Carregado**\nModo básico ativo")
    
    with col2:
        st.info("🎯 **Metodologia**\nDMAIC Six Sigma")
    
    with col3:
        st.info("👤 **Usuário**\nAutenticado com sucesso")
    
    st.markdown("---")
    
    # Mensagem informativa
    st.warning("⚠️ **Modo Básico Ativo**")
    st.markdown("""
    O sistema está funcionando em modo básico. Isso pode acontecer se:
    - Alguns módulos não foram carregados corretamente
    - Há problemas de conectividade
    - É a primeira execução do sistema
    
    **O que você pode fazer:**
    1. Recarregar a página (F5)
    2. Verificar sua conexão com a internet
    3. Aguardar alguns instantes e tentar novamente
    """)
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Recarregar Sistema", type="primary"):
            st.rerun()
    
    with col2:
        if st.button("🗑️ Limpar Cache"):
            # Limpar cache do Streamlit
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Cache limpo!")
            time.sleep(1)
            st.rerun()
    
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.authentication_status = False
            st.session_state.user_data = None
            st.rerun()
    
    # Sidebar com informações
    with st.sidebar:
        st.markdown("### 👤 Informações do Usuário")
        st.write(f"**Nome:** {user_data.get('name', 'N/A')}")
        st.write(f"**Email:** {user_data.get('email', 'N/A')}")
        if user_data.get('company'):
            st.write(f"**Empresa:** {user_data['company']}")
        
        st.markdown("---")
        st.markdown("### 🔧 Sistema")
        st.write("**Status:** Modo Básico")
        st.write("**Versão:** 2.0.0")
        
        # Debug info
        if st.checkbox("🔍 Debug Info"):
            st.json({
                'authentication_status': st.session_state.get('authentication_status'),
                'user_data_present': user_data is not None,
                'modules_loaded': {k: v is not None for k, v in MODULES.items()},
                'session_keys': len(st.session_state)
            })

def main():
    """Função principal"""
    try:
        # ✅ CORREÇÃO: Inicializar session state
        initialize_session()
        
        # ✅ CORREÇÃO: Verificar autenticação de forma mais robusta
        is_authenticated = st.session_state.get('authentication_status', False)
        user_data = st.session_state.get('user_data')
        
        # Se não está autenticado OU não tem dados do usuário, mostrar login
        if not is_authenticated or not user_data:
            show_login_page()
        else:
            # Está autenticado e tem dados do usuário
            show_main_app()
        
    except Exception as e:
        logger.critical(f"Erro crítico na aplicação: {str(e)}")
        
        # Tela de erro crítico
        st.error("❌ **Erro Crítico na Aplicação**")
        st.markdown("Ocorreu um erro inesperado. Tente as opções abaixo:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Recarregar Aplicação", type="primary"):
                st.rerun()
        
        with col2:
            if st.button("🗑️ Resetar Sistema"):
                st.session_state.clear()
                st.rerun()
        
        # Mostrar detalhes do erro
        with st.expander("🔍 Detalhes técnicos"):
            st.code(f"Erro: {str(e)}\n\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
