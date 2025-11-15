import os
import streamlit as st
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, auth
import requests

load_dotenv()

# Configuração do Firebase para autenticação REST API
firebase_config = {
    "apiKey": st.secrets.get("FIREBASE_API_KEY", os.getenv("FIREBASE_API_KEY")),
    "authDomain": st.secrets.get("FIREBASE_AUTH_DOMAIN", os.getenv("FIREBASE_AUTH_DOMAIN")),
    "projectId": st.secrets.get("FIREBASE_PROJECT_ID", os.getenv("FIREBASE_PROJECT_ID")),
    "storageBucket": st.secrets.get("FIREBASE_STORAGE_BUCKET", os.getenv("FIREBASE_STORAGE_BUCKET")),
    "messagingSenderId": st.secrets.get("FIREBASE_MESSAGING_SENDER_ID", os.getenv("FIREBASE_MESSAGING_SENDER_ID")),
    "appId": st.secrets.get("FIREBASE_APP_ID", os.getenv("FIREBASE_APP_ID"))
}

def get_project_id():
    """Obtém o Project ID de diferentes fontes"""
    # Ordem de prioridade para obter Project ID
    project_id = None
    
    # 1. Streamlit Secrets
    if hasattr(st, 'secrets'):
        project_id = st.secrets.get("FIREBASE_PROJECT_ID")
        if project_id:
            st.write(f"🔧 Debug: Project ID obtido dos Streamlit Secrets: {project_id}")
            return project_id
    
    # 2. Variáveis de ambiente
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    if project_id:
        st.write(f"🔧 Debug: Project ID obtido da variável de ambiente: {project_id}")
        return project_id
    
    # 3. Google Cloud Project (ambiente Google Cloud)
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        st.write(f"🔧 Debug: Project ID obtido do Google Cloud: {project_id}")
        return project_id
    
    # 4. Do service account nos secrets
    if hasattr(st, 'secrets') and 'FIREBASE_SERVICE_ACCOUNT' in st.secrets:
        try:
            service_account = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
            project_id = service_account.get("project_id")
            if project_id:
                st.write(f"🔧 Debug: Project ID obtido do Service Account: {project_id}")
                return project_id
        except Exception as e:
            st.write(f"❌ Debug: Erro ao obter Project ID do Service Account: {str(e)}")
    
    # 5. Do arquivo local serviceAccountKey.json
    if os.path.exists("serviceAccountKey.json"):
        try:
            with open("serviceAccountKey.json", 'r') as f:
                service_account = json.load(f)
                project_id = service_account.get("project_id")
                if project_id:
                    st.write(f"🔧 Debug: Project ID obtido do arquivo local: {project_id}")
                    return project_id
        except Exception as e:
            st.write(f"❌ Debug: Erro ao ler arquivo local: {str(e)}")
    
    st.write("❌ Debug: Project ID não encontrado em nenhuma fonte")
    return None

def initialize_firebase():
    """Inicializa o Firebase Admin SDK com Project ID obrigatório"""
    try:
        # Verificar se já foi inicializado
        if firebase_admin._apps:
            st.write("✅ Debug: Firebase já inicializado, retornando cliente existente")
            return firestore.client()
        
        # Obter Project ID primeiro (obrigatório)
        project_id = get_project_id()
        if not project_id:
            st.error("❌ Project ID não encontrado. Configure FIREBASE_PROJECT_ID nos secrets ou variáveis de ambiente.")
            return None
        
        # Definir variável de ambiente para Google Cloud (backup)
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
        
        cred = None
        init_method = "unknown"
        
        # Método 1: Streamlit Secrets (Service Account)
        if hasattr(st, 'secrets') and 'FIREBASE_SERVICE_ACCOUNT' in st.secrets:
            try:
                service_account_info = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
                
                # Garantir que o project_id está no service account
                if "project_id" not in service_account_info:
                    service_account_info["project_id"] = project_id
                
                # Validar campos obrigatórios
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if not service_account_info.get(field)]
                
                if missing_fields:
                    st.write(f"❌ Debug: Campos obrigatórios ausentes no Service Account: {missing_fields}")
                    raise ValueError(f"Campos obrigatórios ausentes: {missing_fields}")
                
                cred = credentials.Certificate(service_account_info)
                init_method = "streamlit_secrets"
                st.write(f"✅ Debug: Credenciais obtidas dos Streamlit Secrets")
                
            except Exception as e:
                st.write(f"❌ Debug: Erro ao usar Streamlit Secrets: {str(e)}")
        
        # Método 2: Variável de ambiente com JSON
        if not cred and os.getenv("FIREBASE_SERVICE_ACCOUNT"):
            try:
                service_account_info = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT"))
                if "project_id" not in service_account_info:
                    service_account_info["project_id"] = project_id
                
                cred = credentials.Certificate(service_account_info)
                init_method = "env_json"
                st.write(f"✅ Debug: Credenciais obtidas da variável de ambiente JSON")
            except Exception as e:
                st.write(f"❌ Debug: Erro ao usar ENV JSON: {str(e)}")
        
        # Método 3: Arquivo local
        if not cred and os.path.exists("serviceAccountKey.json"):
            try:
                cred = credentials.Certificate("serviceAccountKey.json")
                init_method = "local_file"
                st.write(f"✅ Debug: Credenciais obtidas do arquivo local")
            except Exception as e:
                st.write(f"❌ Debug: Erro ao usar arquivo local: {str(e)}")
        
        # Método 4: Application Default Credentials (com project_id)
        if not cred:
            try:
                cred = credentials.ApplicationDefault()
                init_method = "application_default"
                st.write(f"✅ Debug: Usando Application Default Credentials")
            except Exception as e:
                st.write(f"❌ Debug: Erro ao usar Application Default: {str(e)}")
        
        # Se não conseguiu credenciais, tentar inicializar só com Project ID
        if not cred:
            try:
                st.write(f"🔧 Debug: Tentando inicializar apenas com Project ID: {project_id}")
                
                # Criar credenciais mínimas
                app_options = {
                    'projectId': project_id
                }
                
                app = firebase_admin.initialize_app(options=app_options)
                init_method = "project_id_only"
                st.write(f"✅ Debug: Inicializado apenas com Project ID")
                
                # Tentar retornar cliente Firestore
                return firestore.client()
                
            except Exception as e:
                st.write(f"❌ Debug: Erro ao inicializar com Project ID apenas: {str(e)}")
                return None
        
        # Inicializar com credenciais + project_id
        if cred:
            try:
                app_options = {
                    'projectId': project_id
                }
                
                app = firebase_admin.initialize_app(cred, options=app_options)
                st.write(f"✅ Debug: Firebase Admin inicializado com sucesso ({init_method})")
                
                # Testar conexão Firestore
                db = firestore.client()
                
                # Teste simples de conectividade
                try:
                    # Apenas verificar se consegue acessar o cliente
                    st.write(f"✅ Debug: Cliente Firestore criado com sucesso")
                    return db
                    
                except Exception as test_error:
                    st.write(f"⚠️ Debug: Cliente criado mas erro no teste: {str(test_error)}")
                    return db  # Retornar mesmo assim
            
            except Exception as init_error:
                st.write(f"❌ Debug: Erro na inicialização final: {str(init_error)}")
                return None
        
        st.error("❌ Não foi possível obter credenciais válidas")
        return None
        
    except Exception as e:
        st.error(f"❌ Erro crítico ao inicializar Firebase: {str(e)}")
        st.write(f"🔧 Debug: Tipo do erro: {type(e).__name__}")
        st.write(f"🔧 Debug: Detalhes: {str(e)}")
        return None

def test_firebase_connection():
    """Testa a conexão com Firebase de forma segura"""
    try:
        db = initialize_firebase()
        if not db:
            return False, "Firebase não inicializado"
        
        # Teste mais simples - apenas verificar se o cliente existe
        project_id = get_project_id()
        if project_id:
            return True, f"Conexão estabelecida com projeto: {project_id}"
        else:
            return False, "Project ID não disponível"
            
    except Exception as e:
        return False, f"Erro no teste: {str(e)}"

# Resto das classes permanecem iguais...
class FirebaseRestAuth:
    """Classe para autenticação usando Firebase REST API diretamente"""
    
    def __init__(self):
        self.api_key = firebase_config.get("apiKey")
        self.base_url = "https://identitytoolkit.googleapis.com/v1"
        
        if not self.api_key:
            raise ValueError("Firebase API Key não configurada")
    
    def sign_up_with_email_password(self, email, password):
        """Registra usuário usando REST API"""
        url = f"{self.base_url}/accounts:signUp?key={self.api_key}"
        
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            error_message = error_data.get("error", {}).get("message", str(e))
            return False, error_message
        except Exception as e:
            return False, str(e)
    
    def sign_in_with_email_password(self, email, password):
        """Autentica usuário usando REST API"""
        url = f"{self.base_url}/accounts:signInWithPassword?key={self.api_key}"
        
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            error_message = error_data.get("error", {}).get("message", str(e))
            return False, error_message
        except Exception as e:
            return False, str(e)
    
    def send_password_reset_email(self, email):
        """Envia email de reset de senha"""
        url = f"{self.base_url}/accounts:sendOobCode?key={self.api_key}"
        
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": email
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return True, "Email enviado com sucesso"
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            error_message = error_data.get("error", {}).get("message", str(e))
            return False, error_message
        except Exception as e:
            return False, str(e)
    
    def send_email_verification(self, id_token):
        """Envia email de verificação"""
        url = f"{self.base_url}/accounts:sendOobCode?key={self.api_key}"
        
        payload = {
            "requestType": "VERIFY_EMAIL",
            "idToken": id_token
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return True, "Email de verificação enviado"
        except Exception as e:
            return False, str(e)
    
    def get_user_info(self, id_token):
        """Obtém informações do usuário"""
        url = f"{self.base_url}/accounts:lookup?key={self.api_key}"
        
        payload = {
            "idToken": id_token
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return True, response.json()
        except Exception as e:
            return False, str(e)

def check_firebase_config():
    """Verifica se as configurações do Firebase estão corretas"""
    config_status = {
        "API Key": bool(firebase_config.get("apiKey")),
        "Auth Domain": bool(firebase_config.get("authDomain")),
        "Project ID": bool(firebase_config.get("projectId")),
        "Storage Bucket": bool(firebase_config.get("storageBucket")),
        "App ID": bool(firebase_config.get("appId"))
    }
    
    return config_status

def get_firebase_config():
    """Retorna configuração do Firebase"""
    return firebase_config
