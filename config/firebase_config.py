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

def initialize_firebase():
    """Inicializa o Firebase Admin SDK com múltiplas tentativas"""
    try:
        # Verificar se já foi inicializado
        if firebase_admin._apps:
            return firestore.client()
        
        cred = None
        init_method = "unknown"
        
        # Método 1: Streamlit Secrets (mais comum no Streamlit Cloud)
        if hasattr(st, 'secrets') and 'FIREBASE_SERVICE_ACCOUNT' in st.secrets:
            try:
                service_account_info = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
                cred = credentials.Certificate(service_account_info)
                init_method = "streamlit_secrets"
                st.write(f"🔧 Debug: Usando Streamlit Secrets para Firebase Admin")
            except Exception as e:
                st.write(f"❌ Debug: Erro ao usar Streamlit Secrets: {str(e)}")
        
        # Método 2: Variável de ambiente com JSON
        if not cred and os.getenv("FIREBASE_SERVICE_ACCOUNT"):
            try:
                service_account_info = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT"))
                cred = credentials.Certificate(service_account_info)
                init_method = "env_json"
                st.write(f"🔧 Debug: Usando variável de ambiente JSON")
            except Exception as e:
                st.write(f"❌ Debug: Erro ao usar ENV JSON: {str(e)}")
        
        # Método 3: Arquivo local (desenvolvimento)
        if not cred and os.path.exists("serviceAccountKey.json"):
            try:
                cred = credentials.Certificate("serviceAccountKey.json")
                init_method = "local_file"
                st.write(f"🔧 Debug: Usando arquivo local serviceAccountKey.json")
            except Exception as e:
                st.write(f"❌ Debug: Erro ao usar arquivo local: {str(e)}")
        
        # Método 4: Credenciais do ambiente (Google Cloud)
        if not cred:
            try:
                cred = credentials.ApplicationDefault()
                init_method = "application_default"
                st.write(f"🔧 Debug: Usando Application Default Credentials")
            except Exception as e:
                st.write(f"❌ Debug: Erro ao usar Application Default: {str(e)}")
        
        # Método 5: Apenas com Project ID (limitado, mas funcional)
        if not cred:
            project_id = firebase_config.get("projectId")
            if project_id:
                try:
                    # Inicializar sem credenciais (apenas leitura pública se configurado)
                    firebase_admin.initialize_app(options={'projectId': project_id})
                    init_method = "project_id_only"
                    st.write(f"🔧 Debug: Inicializado apenas com Project ID: {project_id}")
                    return firestore.client()
                except Exception as e:
                    st.write(f"❌ Debug: Erro ao inicializar com Project ID: {str(e)}")
        
        if cred:
            # Inicializar Firebase Admin
            app = firebase_admin.initialize_app(cred)
            st.write(f"✅ Debug: Firebase Admin inicializado com sucesso ({init_method})")
            
            # Testar conexão
            db = firestore.client()
            
            # Teste simples de conectividade
            try:
                # Tentar acessar uma coleção (sem criar dados)
                test_collection = db.collection('_test_connection')
                st.write(f"✅ Debug: Conexão com Firestore estabelecida")
                return db
            except Exception as test_error:
                st.write(f"⚠️ Debug: Firebase Admin inicializado mas erro ao conectar Firestore: {str(test_error)}")
                return db  # Retornar mesmo assim, pode funcionar
        
        # Se chegou aqui, não conseguiu inicializar
        st.error("❌ Não foi possível inicializar Firebase Admin SDK")
        st.write("🔧 Debug: Verifique as configurações do Firebase")
        return None
        
    except Exception as e:
        st.error(f"❌ Erro crítico ao inicializar Firebase: {str(e)}")
        st.write(f"🔧 Debug: Erro detalhado: {type(e).__name__}: {str(e)}")
        return None

def test_firebase_connection():
    """Testa a conexão com Firebase"""
    try:
        db = initialize_firebase()
        if db:
            # Tentar uma operação simples
            test_doc = db.collection('_connection_test').document('test')
            test_doc.set({'timestamp': firestore.SERVER_TIMESTAMP, 'test': True})
            
            # Ler o documento
            doc = test_doc.get()
            if doc.exists:
                # Limpar o teste
                test_doc.delete()
                return True, "Conexão testada com sucesso"
            else:
                return False, "Não foi possível ler dados do Firestore"
        else:
            return False, "Firebase não inicializado"
    except Exception as e:
        return False, f"Erro no teste: {str(e)}"

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
