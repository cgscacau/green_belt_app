"""
Aplicação Six Sigma - Corrigida para usar Firebase corretamente
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

# CSS customizado
def inject_custom_css():
    st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    .stAlert[data-baseweb="notification"] {
        display: none;
    }
    
    iframe[src*="ethereum"] {
        display: none !important;
    }
    
    .login-container {
        max-width: 450px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid #e9ecef;
    }
    
    .success-message {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #155724;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialização do session state
def init_session():
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.authentication_status = False
        st.session_state.user_data = None
        st.session_state.current_page = 'login'

# Importação da classe FirebaseAuth
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

# Importação do dashboard
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

# Login com dados do Firebase
def show_firebase_login():
    inject_custom_css()
    
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='color: #1f77b4; margin-bottom: 0.5rem;'>🎯 Six Sigma Green Belt</h1>
        <p style='color: #666; font-size: 1.1em;'>Sistema de Gerenciamento de Projetos Six Sigma</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Obter instância do Firebase Auth
    firebase_auth = get_firebase_auth()
    
    if not firebase_auth:
        st.error("❌ Sistema de autenticação não disponível")
        st.info("Verifique a configuração do Firebase")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Abas de Login e Registro
    tab_login, tab_register = st.tabs(["🔑 Entrar", "👤 Registrar"])
    
    with tab_login:
        st.markdown("### Acesse sua conta")
        
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "📧 Email",
                placeholder="seu.email@exemplo.com",
                help="Digite o email cadastrado"
            )
            
            password = st.text_input(
                "🔒 Senha",
                type="password",
                placeholder="••••••••",
                help="Digite sua senha"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                login_btn = st.form_submit_button("🚀 Entrar", type="primary", use_container_width=True)
            with col2:
                forgot_btn = st.form_submit_button("🔄 Esqueci a senha", use_container_width=True)
            
            # Processar login
            if login_btn and email and password:
                with st.spinner("🔐 Autenticando..."):
                    try:
                        # ✅ CORREÇÃO: Usar o método correto que retorna os dados do usuário
                        success, result = firebase_auth.login_user(email, password)
                        
                        if success:
                            # ✅ CORREÇÃO: result já contém os dados do usuário
                            user_data = result  # result é o dict com os dados do usuário
                            
                            # Armazenar no session state
                            st.session_state.authentication_status = True
                            st.session_state.user_data = user_data
                            
                            # Mostrar sucesso
                            st.markdown("""
                            <div class='success-message'>
                                <h4>✅ Login realizado com sucesso!</h4>
                                <p>Bem-vindo(a), <strong>{}</strong>!</p>
                                <p>Redirecionando para o sistema...</p>
                            </div>
                            """.format(user_data.get('name', user_data.get('email', 'Usuário'))), 
                            unsafe_allow_html=True)
                            
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            # result contém a mensagem de erro
                            st.error(result)
                            
                    except Exception as e:
                        st.error(f"❌ Erro inesperado: {str(e)}")
                        logger.error(f"Erro no login: {str(e)}")
            
            # Processar esqueci a senha
            elif forgot_btn and email:
                with st.spinner("📧 Enviando email..."):
                    try:
                        success, message = firebase_auth.reset_password(email)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
            elif forgot_btn and not email:
                st.warning("⚠️ Digite seu email para recuperar a senha")
    
    with tab_register:
        st.markdown("### Criar nova conta")
        
        with st.form("register_form", clear_on_submit=False):
            reg_name = st.text_input(
                "👤 Nome Completo",
                placeholder="Seu Nome Completo",
                help="Nome que aparecerá no sistema"
            )
            
            reg_email = st.text_input(
                "📧 Email",
                placeholder="seu.email@exemplo.com",
                help="Email será usado para login"
            )
            
            reg_company = st.text_input(
                "🏢 Empresa (Opcional)",
                placeholder="Nome da sua empresa",
                help="Empresa onde trabalha"
            )
            
            reg_password = st.text_input(
                "🔒 Senha",
                type="password",
                placeholder="••••••••",
                help="Mínimo 6 caracteres (Firebase)"
            )
            
            reg_password_confirm = st.text_input(
                "🔒 Confirmar Senha",
                type="password",
                placeholder="••••••••"
            )
            
            terms = st.checkbox("Aceito os termos de uso e política de privacidade")
            
            reg_btn = st.form_submit_button("🎯 Criar Conta", type="primary", use_container_width=True)
            
            if reg_btn:
                # Validações
                errors = []
                
                if not reg_name or len(reg_name.strip()) < 2:
                    errors.append("Nome deve ter pelo menos 2 caracteres")
                
                if not firebase_auth.validate_email(reg_email):
                    errors.append("Email inválido")
                
                if len(reg_password) < 6:
                    errors.append("Senha deve ter pelo menos 6 caracteres")
                
                if reg_password != reg_password_confirm:
                    errors.append("Senhas não coincidem")
                
                if not terms:
                    errors.append("Aceite os termos de uso")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    with st.spinner("👤 Criando conta..."):
                        try:
                            # ✅ CORREÇÃO: Usar parâmetros corretos
                            success, message = firebase_auth.register_user(
                                email=reg_email.strip().lower(),
                                password=reg_password,
                                name=reg_name.strip(),
                                company=reg_company.strip() if reg_company else ""
                            )
                            
                            if success:
                                st.success(message)
                                st.info("🔑 Agora você pode fazer login na aba 'Entrar'")
                            else:
                                st.error(message)
                                
                        except Exception as e:
                            st.error(f"❌ Erro inesperado: {str(e)}")
                            logger.error(f"Erro no registro: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Informações adicionais
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🎯 Recursos:**\n- Metodologia DMAIC\n- Análise estatística\n- Relatórios científicos")
    
    with col2:
        st.markdown("**📊 Ferramentas:**\n- Project Charter\n- Controle estatístico\n- Análise de capacidade")
    
    with col3:
        st.markdown("**🔧 Suporte:**\n- Tutoriais integrados\n- Templates prontos\n- Documentação completa")

# Aplicação principal
def show_main_application():
    inject_custom_css()
    
    user_data = st.session_state.get('user_data', {})
    
    # Verificar se user_data é válido
    if not user_data or not user_data.get('uid'):
        st.error("❌ Dados do usuário inválidos")
        
        if st.button("🚪 Voltar ao Login"):
            st.session_state.authentication_status = False
            st.session_state.user_data = None
            st.rerun()
        return
    
    # Tentar carregar dashboard completo
    dashboard_func = get_dashboard()
    
    if dashboard_func:
        try:
            dashboard_func()
            return
        except Exception as e:
            logger.error(f"Erro no dashboard: {str(e)}")
            st.warning("⚠️ Erro no dashboard completo, usando versão básica...")
    
    # Dashboard básico como fallback
    show_basic_dashboard(user_data)

def show_basic_dashboard(user_data):
    """Dashboard básico funcional"""
    # Header
    st.title(f"🏠 Dashboard - {user_data.get('name', 'Usuário')}")
    
    if user_data.get('company'):
        st.caption(f"🏢 {user_data['company']}")
    
    if user_data.get('email'):
        st.caption(f"📧 {user_data['email']}")
    
    st.markdown("---")
    
    # Informações do usuário
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info("✅ **Status**\nSistema ativo")
    
    with col2:
        st.info("🎯 **Metodologia**\nDMAIC Six Sigma")
    
    with col3:
        st.info("👤 **Usuário**\nAutenticado")
    
    with col4:
        if st.button("🚪 Logout", type="secondary"):
            firebase_auth = get_firebase_auth()
            if firebase_auth:
                firebase_auth.logout_user()
            st.session_state.authentication_status = False
            st.session_state.user_data = None
            st.rerun()
    
    st.markdown("---")
    
    # Conteúdo principal
    st.success("🎉 **Bem-vindo ao Six Sigma Green Belt!**")
    
    st.markdown("""
    ### 🚀 Sistema Funcionando Corretamente
    
    Você está logado com sucesso! O sistema está carregando em modo básico.
    
    **Próximos passos:**
    1. O sistema completo será carregado automaticamente
    2. Você terá acesso a todas as ferramentas DMAIC
    3. Poderá criar e gerenciar projetos Six Sigma
    
    **Recursos disponíveis:**
    - ✅ Autenticação Firebase funcionando
    - ✅ Dados do usuário carregados
    - ✅ Sistema de navegação ativo
    """)
    
    # Sidebar com informações do usuário
    with st.sidebar:
        st.markdown("### 👤 Perfil do Usuário")
        st.write(f"**Nome:** {user_data.get('name', 'N/A')}")
        st.write(f"**Email:** {user_data.get('email', 'N/A')}")
        
        if user_data.get('company'):
            st.write(f"**Empresa:** {user_data['company']}")
        
        st.write(f"**UID:** {user_data.get('uid', 'N/A')[:8]}...")
        
        if user_data.get('email_verified'):
            st.success("✅ Email verificado")
        else:
            st.warning("⚠️ Email não verificado")
        
        st.markdown("---")
        
        # Ações
        if st.button("🔄 Recarregar Sistema", use_container_width=True):
            st.rerun()
        
        if st.button("🗑️ Limpar Cache", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Cache limpo!")
            time.sleep(1)
            st.rerun()

# Função principal
def main():
    try:
        init_session()
        
        # ✅ CORREÇÃO: Verificação mais robusta
        is_authenticated = st.session_state.get('authentication_status', False)
        user_data = st.session_state.get('user_data')
        
        # Debug info (opcional)
        if st.sidebar.checkbox("🔍 Debug Info"):
            st.sidebar.json({
                'authenticated': is_authenticated,
                'user_data_exists': user_data is not None,
                'user_uid': user_data.get('uid') if user_data else None,
                'user_email': user_data.get('email') if user_data else None,
                'session_keys': len(st.session_state)
            })
        
        # Roteamento
        if is_authenticated and user_data and user_data.get('uid'):
            show_main_application()
        else:
            show_firebase_login()
            
    except Exception as e:
        logger.critical(f"Erro crítico: {str(e)}")
        
        st.error("❌ **Erro Crítico na Aplicação**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Recarregar", type="primary"):
                st.rerun()
        with col2:
            if st.button("🗑️ Reset Completo"):
                st.session_state.clear()
                st.rerun()
        
        with st.expander("🔍 Detalhes do erro"):
            st.code(f"Erro: {str(e)}")

if __name__ == "__main__":
    main()
