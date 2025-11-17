import streamlit as st
import sys
import os
import traceback
from typing import Optional

# Configurar path antes de qualquer import
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def safe_import():
    """Importa módulos com tratamento de erro"""
    try:
        from src.pages.login import show_login_page
        from src.pages.main_navigation import show_main_navigation
        from src.pages.config_check import show_config_check
        from config.firebase_config import check_firebase_config
        
        return {
            'show_login_page': show_login_page,
            'show_main_navigation': show_main_navigation,
            'show_config_check': show_config_check,
            'check_firebase_config': check_firebase_config
        }
    except ImportError as e:
        st.error(f"❌ Erro ao importar módulos: {str(e)}")
        st.error("Verifique se todos os arquivos estão no local correto:")
        st.code("""
        Estrutura esperada:
        /
        ├── app.py
        ├── config/
        │   └── firebase_config.py
        └── src/
            └── pages/
                ├── login.py
                ├── main_navigation.py
                └── config_check.py
        """)
        return None
    except Exception as e:
        st.error(f"❌ Erro inesperado na importação: {str(e)}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

def initialize_session_state():
    """Inicializa session state com valores padrão seguros"""
    default_states = {
        'authentication_status': False,
        'current_page': 'dashboard',
        'user_data': None,
        'current_project': None,
        'show_config': False,
        'app_initialized': True
    }
    
    for key, default_value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def cleanup_session_state():
    """Limpa estados problemáticos do session state"""
    try:
        # Lista de padrões de chaves para limpar
        cleanup_patterns = [
            'confirm_delete_',
            'temp_',
            'old_',
            'cache_'
        ]
        
        keys_to_remove = []
        
        # Encontrar chaves para remover
        for key in st.session_state.keys():
            try:
                # Verificar padrões problemáticos
                for pattern in cleanup_patterns:
                    if str(key).startswith(pattern):
                        keys_to_remove.append(key)
                        break
                
                # Verificar chaves muito antigas (mais de 100 caracteres podem ser problemáticas)
                if len(str(key)) > 100:
                    keys_to_remove.append(key)
                
                # Verificar valores None ou vazios em chaves críticas
                if key in ['user_data', 'current_project'] and st.session_state[key] is None:
                    continue  # Manter None para essas chaves críticas
                    
            except Exception as e:
                # Se houver erro ao verificar uma chave, marcar para remoção
                keys_to_remove.append(key)
        
        # Remover chaves problemáticas
        for key in keys_to_remove:
            try:
                del st.session_state[key]
            except KeyError:
                continue  # Chave já foi removida
                
    except Exception as e:
        # Se a limpeza falhar, não interromper a aplicação
        st.warning(f"⚠️ Aviso na limpeza do session state: {str(e)}")

def safe_get_session_state(key: str, default=None):
    """Obtém valor do session state com segurança"""
    try:
        return st.session_state.get(key, default)
    except KeyError:
        return default
    except Exception:
        return default

def safe_set_session_state(key: str, value):
    """Define valor no session state com segurança"""
    try:
        st.session_state[key] = value
        return True
    except Exception as e:
        st.warning(f"⚠️ Erro ao definir {key}: {str(e)}")
        return False

def check_app_health():
    """Verifica saúde da aplicação"""
    health_issues = []
    
    # Verificar se session state está funcionando
    try:
        test_key = f"health_check_{hash('test')}"
        st.session_state[test_key] = "ok"
        if st.session_state[test_key] != "ok":
            health_issues.append("Session state não está funcionando corretamente")
        del st.session_state[test_key]
    except Exception as e:
        health_issues.append(f"Erro no session state: {str(e)}")
    
    # Verificar imports
    modules = safe_import()
    if not modules:
        health_issues.append("Erro na importação de módulos")
    
    return health_issues

def show_error_page(error_message: str, error_details: Optional[str] = None):
    """Mostra página de erro amigável"""
    st.error("🚨 **Erro na Aplicação**")
    st.write(f"**Mensagem:** {error_message}")
    
    if error_details:
        with st.expander("📋 Detalhes do Erro"):
            st.code(error_details)
    
    st.write("---")
    st.write("**Possíveis soluções:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Recarregar App", key="reload_app"):
            # Limpar tudo e recarregar
            st.session_state.clear()
            st.rerun()
    
    with col2:
        if st.button("🧹 Limpar Cache", key="clear_cache"):
            cleanup_session_state()
            st.success("✅ Cache limpo!")
            st.rerun()
    
    with col3:
        if st.button("🔧 Verificar Config", key="check_config"):
            safe_set_session_state('show_config', True)
            st.rerun()

def main():
    """Função principal com tratamento robusto de erros"""
    try:
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
        .error-container {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 1rem;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Verificar saúde da aplicação
        health_issues = check_app_health()
        if health_issues:
            show_error_page(
                "Problemas detectados na inicialização",
                "\n".join(health_issues)
            )
            return
        
        # Limpar estados problemáticos
        cleanup_session_state()
        
        # Inicializar session state
        initialize_session_state()
        
        # Importar módulos
        modules = safe_import()
        if not modules:
            show_error_page("Erro na importação de módulos")
            return
        
        # Verificar configuração do Firebase
        try:
            config_status = modules['check_firebase_config']()
            config_ok = all(config_status.values()) if isinstance(config_status, dict) else False
        except Exception as e:
            st.warning(f"⚠️ Erro ao verificar configuração Firebase: {str(e)}")
            config_ok = False
        
        # Sidebar para debug/configuração
        with st.sidebar:
            if not safe_get_session_state('authentication_status', False):
                if st.button("🔧 Verificar Configuração", key="config_check_main"):
                    safe_set_session_state('show_config', True)
                    st.rerun()
                
                if not config_ok:
                    st.error("⚠️ Configuração incompleta")
                    st.info("Clique em 'Verificar Configuração' para mais detalhes")
            
            # Informações de debug (apenas em desenvolvimento)
            if st.checkbox("🔍 Debug Info", key="debug_info"):
                st.write("**Session State Keys:**")
                st.write(f"Total: {len(st.session_state.keys())}")
                
                if st.button("🧹 Limpar Debug", key="clear_debug"):
                    cleanup_session_state()
                    st.rerun()
        
        # Mostrar página de configuração se necessário
        if safe_get_session_state('show_config', False) or not config_ok:
            try:
                modules['show_config_check']()
                if st.button("🔙 Voltar", key="back_from_config"):
                    safe_set_session_state('show_config', False)
                    st.rerun()
            except Exception as e:
                show_error_page(
                    "Erro na página de configuração",
                    str(e)
                )
            return
        
        # Roteamento principal
        try:
            if safe_get_session_state('authentication_status', False):
                # Usuário logado - mostrar navegação principal
                modules['show_main_navigation']()
            else:
                # Usuário não logado - mostrar página de login
                modules['show_login_page']()
                
        except KeyError as e:
            show_error_page(
                f"Erro de chave não encontrada: {str(e)}",
                "Isso pode indicar um problema com o session state ou dados corrompidos."
            )
        except Exception as e:
            show_error_page(
                f"Erro na navegação: {str(e)}",
                traceback.format_exc()
            )
    
    except Exception as e:
        # Captura qualquer erro não tratado
        st.error("🚨 **Erro Crítico na Aplicação**")
        st.write(f"**Erro:** {str(e)}")
        
        with st.expander("📋 Detalhes Técnicos"):
            st.code(traceback.format_exc())
        
        if st.button("🔄 Reiniciar Aplicação", key="restart_app"):
            # Limpar completamente o session state
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
