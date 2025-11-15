import streamlit as st
from config.firebase_config import check_firebase_config

def show_config_check():
    """Página para verificar configurações do Firebase"""
    st.title("🔧 Verificação de Configuração")
    
    st.markdown("### Status das Configurações Firebase")
    
    config_status = check_firebase_config()
    
    for config_name, status in config_status.items():
        if status:
            st.success(f"✅ {config_name}: Configurado")
        else:
            st.error(f"❌ {config_name}: Não configurado")
    
    st.markdown("### Variáveis de Ambiente Detectadas")
    
    # Verificar secrets do Streamlit
    if hasattr(st, 'secrets'):
        st.info("🔐 Streamlit Secrets detectados")
        secrets_keys = list(st.secrets.keys()) if st.secrets else []
        for key in secrets_keys:
            if key.startswith('FIREBASE'):
                st.success(f"✅ {key}")
    else:
        st.warning("⚠️ Streamlit Secrets não detectados")
    
    st.markdown("### Instruções de Configuração")
    
    with st.expander("📋 Como configurar no Streamlit Cloud"):
        st.markdown("""
        1. Acesse seu app no Streamlit Cloud
        2. Clique em "Settings" → "Secrets"
        3. Adicione as seguintes variáveis:
        
        ```toml
        FIREBASE_API_KEY = "sua_api_key"
        FIREBASE_AUTH_DOMAIN = "seu_projeto.firebaseapp.com"
        FIREBASE_PROJECT_ID = "seu_projeto_id"
        FIREBASE_STORAGE_BUCKET = "seu_projeto.appspot.com"
        FIREBASE_MESSAGING_SENDER_ID = "123456789"
        FIREBASE_APP_ID = "1:123456789:web:abcdef"
        
        [FIREBASE_SERVICE_ACCOUNT]
        type = "service_account"
        project_id = "seu_projeto_id"
        private_key_id = "key_id"
        private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
        client_email = "firebase-adminsdk-xxxxx@seu_projeto.iam.gserviceaccount.com"
        client_id = "123456789"
        auth_uri = "https://accounts.google.com/o/oauth2/auth"
        token_uri = "https://oauth2.googleapis.com/token"
        auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
        client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40seu_projeto.iam.gserviceaccount.com"
        ```
        """)
    
    with st.expander("🏠 Como configurar localmente"):
        st.markdown("""
        1. Crie um arquivo `.env` na raiz do projeto
        2. Adicione as variáveis:
        
        ```env
        FIREBASE_API_KEY=sua_api_key
        FIREBASE_AUTH_DOMAIN=seu_projeto.firebaseapp.com
        FIREBASE_PROJECT_ID=seu_projeto_id
        FIREBASE_STORAGE_BUCKET=seu_projeto.appspot.com
        FIREBASE_MESSAGING_SENDER_ID=123456789
        FIREBASE_APP_ID=1:123456789:web:abcdef
        ```
        
        3. Baixe o arquivo `serviceAccountKey.json` do Firebase Console
        4. Coloque na raiz do projeto
        """)
