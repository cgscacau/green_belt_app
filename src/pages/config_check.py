import streamlit as st
from config.firebase_config import check_firebase_config, initialize_firebase, test_firebase_connection

def show_config_check():
    """Página para verificar configurações do Firebase"""
    st.title("🔧 Verificação de Configuração Firebase")
    
    st.markdown("### Status das Configurações")
    
    config_status = check_firebase_config()
    
    all_configured = True
    for config_name, status in config_status.items():
        if status:
            st.success(f"✅ {config_name}: Configurado")
        else:
            st.error(f"❌ {config_name}: Não configurado")
            all_configured = False
    
    st.divider()
    
    # Teste de inicialização do Firebase
    st.markdown("### Teste de Inicialização do Firebase")
    
    if st.button("🧪 Testar Inicialização", use_container_width=True):
        with st.spinner("Testando inicialização..."):
            db = initialize_firebase()
            
            if db:
                st.success("✅ Firebase Admin SDK inicializado com sucesso!")
                
                # Teste de conexão
                st.markdown("### Teste de Conectividade")
                with st.spinner("Testando conectividade..."):
                    success, message = test_firebase_connection()
                    
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
            else:
                st.error("❌ Falha na inicialização do Firebase Admin SDK")
    
    st.divider()
    
    # Informações de debug
    st.markdown("### Informações de Debug")
    
    # Verificar secrets do Streamlit
    if hasattr(st, 'secrets'):
        st.info("🔐 Streamlit Secrets detectados")
        
        secrets_keys = []
        try:
            secrets_keys = list(st.secrets.keys()) if st.secrets else []
        except:
            secrets_keys = ["Erro ao acessar secrets"]
        
        st.write("**Chaves disponíveis:**", secrets_keys)
        
        # Verificar se service account está presente
        if 'FIREBASE_SERVICE_ACCOUNT' in secrets_keys:
            st.success("✅ FIREBASE_SERVICE_ACCOUNT encontrado nos secrets")
            
            # Verificar campos do service account
            try:
                sa = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                
                for field in required_fields:
                    if field in sa:
                        st.success(f"✅ {field}: Presente")
                    else:
                        st.error(f"❌ {field}: Ausente")
            except Exception as e:
                st.error(f"Erro ao verificar service account: {str(e)}")
        else:
            st.warning("⚠️ FIREBASE_SERVICE_ACCOUNT não encontrado nos secrets")
    else:
        st.warning("⚠️ Streamlit Secrets não detectados")
    
    st.divider()
    
    # Instruções de configuração
    st.markdown("### 📋 Instruções de Configuração")
    
    with st.expander("🔧 Configuração no Streamlit Cloud"):
        st.markdown("""
        **1. Acesse as configurações do seu app no Streamlit Cloud**
        
        **2. Vá em Settings → Secrets**
        
        **3. Adicione as configurações básicas:**
        ```toml
        FIREBASE_API_KEY = "AIzaSy..."
        FIREBASE_AUTH_DOMAIN = "seu-projeto.firebaseapp.com"
        FIREBASE_PROJECT_ID = "seu-projeto-id"
        FIREBASE_STORAGE_BUCKET = "seu-projeto.appspot.com"
        FIREBASE_MESSAGING_SENDER_ID = "123456789"
        FIREBASE_APP_ID = "1:123456789:web:abcdef"
        ```
        
        **4. Adicione o Service Account (OBRIGATÓRIO para Firestore):**
        ```toml
        [FIREBASE_SERVICE_ACCOUNT]
        type = "service_account"
        project_id = "seu-projeto-id"
        private_key_id = "abc123..."
        private_key = "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC..."
        client_email = "firebase-adminsdk-xxxxx@seu-projeto.iam.gserviceaccount.com"
        client_id = "123456789"
        auth_uri = "https://accounts.google.com/o/oauth2/auth"
        token_uri = "https://oauth2.googleapis.com/token"
        auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
        client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40seu-projeto.iam.gserviceaccount.com"
        ```
        
        **5. Como obter o Service Account:**
        - Vá para Firebase Console → Project Settings
        - Aba "Service accounts" 
        - Clique em "Generate new private key"
        - Baixe o arquivo JSON
        - Copie o conteúdo para os secrets do Streamlit
        """)
    
    with st.expander("🏠 Configuração Local"):
        st.markdown("""
        **1. Crie um arquivo `.env` na raiz do projeto:**
        ```env
        FIREBASE_API_KEY=AIzaSy...
        FIREBASE_AUTH_DOMAIN=seu-projeto.firebaseapp.com
        FIREBASE_PROJECT_ID=seu-projeto-id
        FIREBASE_STORAGE_BUCKET=seu-projeto.appspot.com
        FIREBASE_MESSAGING_SENDER_ID=123456789
        FIREBASE_APP_ID=1:123456789:web:abcdef
        ```
        
        **2. Baixe o arquivo serviceAccountKey.json:**
        - Firebase Console → Project Settings → Service accounts
        - Generate new private key
        - Salve como `serviceAccountKey.json` na raiz do projeto
        
        **3. Adicione ao .gitignore:**
        ```
        .env
        serviceAccountKey.json
        ```
        """)
    
    with st.expander("🔒 Regras de Segurança do Firestore"):
        st.markdown("""
        **Configure as regras no Firebase Console → Firestore → Rules:**
        
        ```javascript
        rules_version = '2';
        service cloud.firestore {
          match /databases/{database}/documents {
            // Permitir leitura/escrita para usuários autenticados
            match /{document=**} {
              allow read, write: if request.auth != null;
            }
            
            // Regras específicas para projetos
            match /projects/{projectId} {
              allow read, write: if request.auth != null 
                && request.auth.uid == resource.data.user_uid;
            }
            
            // Regras para usuários
            match /users/{userId} {
              allow read, write: if request.auth != null 
                && request.auth.uid == userId;
            }
          }
        }
        ```
        """)
    
    # Botão para voltar
    if st.button("🔙 Voltar ao App", use_container_width=True, type="primary"):
        st.session_state.show_config = False
        st.rerun()
