"""
Aplicação principal do sistema Six Sigma Green Belt
Versão melhorada com inicialização robusta e gerenciamento de estado
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

# Configurar logging antes de qualquer import
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuração da página (deve ser a primeira chamada Streamlit)
st.set_page_config(
    page_title="Six Sigma Green Belt",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/seu-usuario/six-sigma-app',
        'Report a bug': 'https://github.com/seu-usuario/six-sigma-app/issues',
        'About': """
        # Six Sigma Green Belt System
        
        Sistema completo para gerenciamento de projetos Six Sigma seguindo a metodologia DMAIC.
        
        **Versão:** 2.0.0  
        **Desenvolvido com:** Streamlit & Firebase
        """
    }
)

# Adicionar diretórios ao path
def setup_python_path():
    """Configura o path do Python para imports"""
    try:
        current_dir = Path(__file__).parent
        src_dir = current_dir / "src"
        
        # Adicionar diretórios ao sys.path se não existirem
        paths_to_add = [str(current_dir), str(src_dir)]
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
        
        logger.info(f"Python path configurado: {paths_to_add}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao configurar Python path: {str(e)}")
        return False

# Configurar path
setup_python_path()

# Tentar importar módulos principais com fallback robusto
def import_core_modules():
    """Importa módulos principais com tratamento de erro"""
    modules = {}
    
    # Firebase Auth
    try:
        from src.auth.firebase_auth import FirebaseAuth
        modules['firebase_auth'] = FirebaseAuth
        logger.info("✅ Firebase Auth importado com sucesso")
    except ImportError as e:
        logger.error(f"❌ Erro ao importar Firebase Auth: {str(e)}")
        modules['firebase_auth'] = None
    
    # Navegação Principal
    try:
        from src.pages.main_navigation import show_main_navigation
        modules['main_navigation'] = show_main_navigation
        logger.info("✅ Navegação principal importada com sucesso")
    except ImportError as e:
        logger.error(f"❌ Erro ao importar navegação principal: {str(e)}")
        modules['main_navigation'] = None
    
    # Utilitários
    try:
        from src.utils.session_manager import SessionManager
        modules['session_manager'] = SessionManager
        logger.info("✅ Session Manager importado com sucesso")
    except ImportError as e:
        logger.warning(f"⚠️ Session Manager não disponível: {str(e)}")
        modules['session_manager'] = None
    
    try:
        from src.utils.offline_storage import get_offline_storage
        modules['offline_storage'] = get_offline_storage
        logger.info("✅ Offline Storage importado com sucesso")
    except ImportError as e:
        logger.warning(f"⚠️ Offline Storage não disponível: {str(e)}")
        modules['offline_storage'] = None
    
    # Configuração DMAIC
    try:
        from src.config.dmaic_config import DMAIC_PHASES_CONFIG
        modules['dmaic_config'] = DMAIC_PHASES_CONFIG
        logger.info("✅ Configuração DMAIC importada com sucesso")
    except ImportError as e:
        logger.warning(f"⚠️ Configuração DMAIC não disponível: {str(e)}")
        modules['dmaic_config'] = None
    
    return modules

# Importar módulos
CORE_MODULES = import_core_modules()

class AppState:
    """Gerenciador de estado da aplicação"""
    
    @staticmethod
    def initialize():
        """Inicializa estado da aplicação"""
        try:
            # Inicializar valores padrão se não existirem
            defaults = {
                'app_initialized': False,
                'authentication_status': False,
                'current_page': 'login',
                'app_version': '2.0.0',
                'initialization_time': datetime.utcnow().isoformat(),
                'debug_mode': False,
                'theme_config': {
                    'primary_color': '#1f77b4',
                    'background_color': '#ffffff',
                    'secondary_background_color': '#f0f2f6'
                }
            }
            
            for key, default_value in defaults.items():
                if key not in st.session_state:
                    st.session_state[key] = default_value
            
            # Usar SessionManager se disponível
            if CORE_MODULES.get('session_manager'):
                CORE_MODULES['session_manager'].initialize_session()
            
            # Marcar como inicializado
            st.session_state.app_initialized = True
            
            logger.info("✅ Estado da aplicação inicializado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização do estado: {str(e)}")
            return False
    
    @staticmethod
    def is_initialized() -> bool:
        """Verifica se a aplicação está inicializada"""
        return st.session_state.get('app_initialized', False)
    
    @staticmethod
    def get_debug_info() -> Dict[str, Any]:
        """Retorna informações de debug"""
        return {
            'app_initialized': AppState.is_initialized(),
            'session_keys_count': len(st.session_state),
            'authentication_status': st.session_state.get('authentication_status', False),
            'current_page': st.session_state.get('current_page', 'unknown'),
            'user_authenticated': st.session_state.get('user_data') is not None,
            'modules_loaded': {name: module is not None for name, module in CORE_MODULES.items()},
            'initialization_time': st.session_state.get('initialization_time'),
            'app_version': st.session_state.get('app_version')
        }

def show_loading_screen():
    """Exibe tela de carregamento"""
    st.markdown("""
    <div style='
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 60vh;
        text-align: center;
    '>
        <h1 style='color: #1f77b4; margin-bottom: 2rem;'>
            🎯 Six Sigma Green Belt
        </h1>
        <div style='
            width: 60px;
            height: 60px;
            border: 6px solid #f3f3f3;
            border-top: 6px solid #1f77b4;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 2rem;
        '></div>
        <p style='color: #666; font-size: 1.1em;'>
            Inicializando sistema...
        </p>
        <p style='color: #999; font-size: 0.9em;'>
            Carregando módulos e configurações
        </p>
    </div>
    
    <style>
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)

def show_error_screen(error_message: str, details: Optional[str] = None):
    """Exibe tela de erro"""
    st.error("❌ **Erro na Aplicação**")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        ### 🚨 Problema Detectado
        
        {error_message}
        
        **O que você pode tentar:**
        1. Recarregar a página (F5)
        2. Limpar o cache do navegador
        3. Verificar sua conexão com a internet
        4. Contatar o suporte técnico
        """)
        
        if details:
            with st.expander("🔍 Detalhes Técnicos"):
                st.code(details)
    
    with col2:
        st.markdown("### 🔧 Ações Rápidas")
        
        if st.button("🔄 Recarregar Aplicação", type="primary", use_container_width=True):
            st.rerun()
        
        if st.button("🗑️ Limpar Cache", use_container_width=True):
            # Limpar cache do Streamlit
            st.cache_data.clear()
            st.cache_resource.clear()
            
            # Limpar session_state (mantendo apenas essenciais)
            keys_to_keep = {'app_version', 'theme_config'}
            keys_to_remove = [k for k in st.session_state.keys() if k not in keys_to_keep]
            
            for key in keys_to_remove:
                del st.session_state[key]
            
            st.success("✅ Cache limpo! Recarregando...")
            time.sleep(1)
            st.rerun()
        
        if st.button("📊 Info Debug", use_container_width=True):
            debug_info = AppState.get_debug_info()
            st.json(debug_info)

def show_login_screen():
    """Exibe tela de login"""
    try:
        # Verificar se Firebase Auth está disponível
        if not CORE_MODULES.get('firebase_auth'):
            st.error("❌ Sistema de autenticação não disponível")
            st.info("Verifique a configuração do Firebase")
            return
        
        # Criar instância do Firebase Auth
        auth = CORE_MODULES['firebase_auth']()
        
        # Interface de login
        st.markdown("""
        <div style='text-align: center; margin-bottom: 3rem;'>
            <h1 style='color: #1f77b4; font-size: 3em; margin-bottom: 0.5rem;'>
                🎯 Six Sigma Green Belt
            </h1>
            <p style='color: #666; font-size: 1.2em; margin-bottom: 2rem;'>
                Sistema de Gerenciamento de Projetos Six Sigma
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Container centralizado para login
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Abas para Login e Registro
            tab_login, tab_register = st.tabs(["🔑 Entrar", "👤 Registrar"])
            
            with tab_login:
                st.markdown("### Faça login em sua conta")
                
                with st.form("login_form"):
                    email = st.text_input(
                        "📧 Email",
                        placeholder="seu.email@exemplo.com",
                        help="Digite seu email cadastrado"
                    )
                    
                    password = st.text_input(
                        "🔒 Senha",
                        type="password",
                        placeholder="••••••••",
                        help="Digite sua senha"
                    )
                    
                    col_login1, col_login2 = st.columns(2)
                    
                    with col_login1:
                        login_button = st.form_submit_button(
                            "🚀 Entrar",
                            type="primary",
                            use_container_width=True
                        )
                    
                    with col_login2:
                        remember_me = st.checkbox("Lembrar de mim")
                
                # Processar login
                if login_button:
                    if email and password:
                        with st.spinner("🔐 Autenticando..."):
                            success, message = auth.login_user(email, password)
                        
                        if success:
                            st.success("✅ Login realizado com sucesso!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ Erro no login: {message}")
                    else:
                        st.warning("⚠️ Preencha todos os campos")
            
            with tab_register:
                st.markdown("### Criar nova conta")
                
                with st.form("register_form"):
                    reg_name = st.text_input(
                        "👤 Nome Completo",
                        placeholder="Seu Nome Completo",
                        help="Digite seu nome completo"
                    )
                    
                    reg_email = st.text_input(
                        "📧 Email",
                        placeholder="seu.email@exemplo.com",
                        help="Email será usado para login"
                    )
                    
                    reg_company = st.text_input(
                        "🏢 Empresa (Opcional)",
                        placeholder="Nome da sua empresa",
                        help="Empresa onde trabalha (opcional)"
                    )
                    
                    col_pass1, col_pass2 = st.columns(2)
                    
                    with col_pass1:
                        reg_password = st.text_input(
                            "🔒 Senha",
                            type="password",
                            placeholder="••••••••",
                            help="Mínimo 6 caracteres"
                        )
                    
                    with col_pass2:
                        reg_password_confirm = st.text_input(
                            "🔒 Confirmar Senha",
                            type="password",
                            placeholder="••••••••",
                            help="Digite a senha novamente"
                        )
                    
                    terms_accepted = st.checkbox(
                        "Aceito os termos de uso e política de privacidade",
                        help="Obrigatório para criar conta"
                    )
                    
                    register_button = st.form_submit_button(
                        "🎯 Criar Conta",
                        type="primary",
                        use_container_width=True
                    )
                
                # Processar registro
                if register_button:
                    # Validações
                    errors = []
                    
                    if not reg_name or len(reg_name.strip()) < 2:
                        errors.append("Nome deve ter pelo menos 2 caracteres")
                    
                    if not reg_email or "@" not in reg_email:
                        errors.append("Email inválido")
                    
                    if not reg_password or len(reg_password) < 6:
                        errors.append("Senha deve ter pelo menos 6 caracteres")
                    
                    if reg_password != reg_password_confirm:
                        errors.append("Senhas não coincidem")
                    
                    if not terms_accepted:
                        errors.append("Você deve aceitar os termos de uso")
                    
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        # Tentar registrar
                        user_data = {
                            'name': reg_name.strip(),
                            'email': reg_email.strip().lower(),
                            'company': reg_company.strip() if reg_company else None
                        }
                        
                        with st.spinner("👤 Criando conta..."):
                            success, message = auth.register_user(
                                reg_email.strip().lower(),
                                reg_password,
                                user_data
                            )
                        
                        if success:
                            st.success("✅ Conta criada com sucesso!")
                            st.info("🔑 Você pode fazer login agora")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Erro ao criar conta: {message}")
        
        # Rodapé informativo
        st.markdown("---")
        
        col_footer1, col_footer2, col_footer3 = st.columns(3)
        
        with col_footer1:
            st.markdown("""
            **🎯 Recursos do Sistema:**
            - Metodologia DMAIC completa
            - Ferramentas de análise estatística
            - Relatórios científicos
            """)
        
        with col_footer2:
            st.markdown("""
            **📊 Análises Disponíveis:**
            - Controle estatístico de processo
            - Análise de capacidade
            - Testes de hipóteses
            """)
        
        with col_footer3:
            st.markdown("""
            **🔧 Ferramentas Incluídas:**
            - Project Charter
            - Análise de causa raiz
            - Planos de controle
            """)
        
    except Exception as e:
        logger.error(f"Erro na tela de login: {str(e)}")
        show_error_screen(
            "Erro no sistema de autenticação",
            f"Detalhes: {str(e)}\n\n{traceback.format_exc()}"
        )

def show_main_application():
    """Exibe aplicação principal"""
    try:
        # Verificar se navegação principal está disponível
        if not CORE_MODULES.get('main_navigation'):
            st.error("❌ Sistema de navegação não disponível")
            st.info("Verifique os módulos da aplicação")
            return
        
        # Executar navegação principal
        navigation_function = CORE_MODULES['main_navigation']
        success = navigation_function()
        
        if not success:
            st.warning("⚠️ Problema na navegação principal")
            
            # Opções de recuperação
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Tentar Novamente", type="primary"):
                    st.rerun()
            
            with col2:
                if st.button("🚪 Fazer Logout"):
                    # Limpar autenticação
                    for key in ['authentication_status', 'user_data', 'current_project']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
        
    except Exception as e:
        logger.error(f"Erro na aplicação principal: {str(e)}")
        show_error_screen(
            "Erro na aplicação principal",
            f"Detalhes: {str(e)}\n\n{traceback.format_exc()}"
        )

def show_debug_panel():
    """Painel de debug (apenas em modo debug)"""
    if not st.session_state.get('debug_mode', False):
        return
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔍 Debug Panel")
        
        if st.button("📊 Show Debug Info"):
            debug_info = AppState.get_debug_info()
            st.json(debug_info)
        
        if st.button("🗑️ Clear All Cache"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Cache cleared!")
        
        if st.button("🔄 Restart App"):
            st.session_state.clear()
            st.rerun()
        
        # Toggle debug mode
        if st.button("🐛 Disable Debug"):
            st.session_state.debug_mode = False
            st.rerun()

def main():
    """Função principal da aplicação"""
    try:
        # Mostrar tela de carregamento inicial
        if not AppState.is_initialized():
            show_loading_screen()
            
            # Simular tempo de carregamento
            time.sleep(1)
            
            # Inicializar aplicação
            if not AppState.initialize():
                show_error_screen("Falha na inicialização da aplicação")
                return
            
            # Recarregar após inicialização
            st.rerun()
        
        # Debug panel (se habilitado)
        show_debug_panel()
        
        # Verificar status de autenticação
        is_authenticated = st.session_state.get('authentication_status', False)
        
        if not is_authenticated:
            # Mostrar tela de login
            show_login_screen()
        else:
            # Mostrar aplicação principal
            show_main_application()
        
        # Rodapé da aplicação
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.caption(f"Six Sigma Green Belt v{st.session_state.get('app_version', '2.0.0')}")
        
        with col2:
            if st.button("🐛 Debug Mode") and not st.session_state.get('debug_mode'):
                st.session_state.debug_mode = True
                st.rerun()
        
        with col3:
            current_time = datetime.now().strftime("%H:%M:%S")
            st.caption(f"⏰ {current_time}")
        
    except Exception as e:
        # Capturar qualquer erro não tratado
        logger.critical(f"Erro crítico na aplicação: {str(e)}")
        show_error_screen(
            "Erro crítico na aplicação",
            f"Erro: {str(e)}\n\nStack trace:\n{traceback.format_exc()}"
        )

# Executar aplicação
if __name__ == "__main__":
    try:
        logger.info("🚀 Iniciando Six Sigma Green Belt Application")
        main()
    except Exception as e:
        logger.critical(f"Falha crítica na inicialização: {str(e)}")
        st.error("❌ **Falha Crítica na Aplicação**")
        st.code(f"Erro: {str(e)}\n\n{traceback.format_exc()}")
