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
    """Inicializa o Firebase Admin SDK"""
    try:
        # Verificar se já foi inicializado
        if firebase_admin._apps:
            return firestore.client()
        
        # Tentar obter credenciais do Streamlit Secrets primeiro
        if hasattr(st, 'secrets') and 'FIREBASE_SERVICE_ACCOUNT' in st.secrets:
            service_account_info = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
            cred = credentials.Certificate(service_account_info)
        
        elif os.getenv("FIREBASE_SERVICE_ACCOUNT"):
            service_account_info = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT"))
            cred = credentials.Certificate(service_account_info)
        
        elif os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
        
        else:
            return None
        
        # Inicializar Firebase Admin
        firebase_admin.initialize_app(cred)
        return firestore.client()
        
    except Exception as e:
        st.error(f"Erro ao inicializar Firebase Admin: {str(e)}")
        return None

def get_firebase_config():
    """Retorna configuração do Firebase"""
    return firebase_config

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
