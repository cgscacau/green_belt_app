import os
import streamlit as st
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

load_dotenv()

# Configuração do Firebase para Pyrebase
firebase_config = {
    "apiKey": st.secrets.get("FIREBASE_API_KEY", os.getenv("FIREBASE_API_KEY")),
    "authDomain": st.secrets.get("FIREBASE_AUTH_DOMAIN", os.getenv("FIREBASE_AUTH_DOMAIN")),
    "databaseURL": st.secrets.get("FIREBASE_DATABASE_URL", os.getenv("FIREBASE_DATABASE_URL", "")),
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
            # Para Streamlit Cloud - usando secrets
            service_account_info = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
            cred = credentials.Certificate(service_account_info)
        
        elif os.getenv("FIREBASE_SERVICE_ACCOUNT"):
            # Para ambiente local - usando variável de ambiente com JSON
            service_account_info = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT"))
            cred = credentials.Certificate(service_account_info)
        
        elif os.path.exists("serviceAccountKey.json"):
            # Para desenvolvimento local - usando arquivo
            cred = credentials.Certificate("serviceAccountKey.json")
        
        else:
            # Configuração mínima para teste sem Admin SDK
            st.warning("⚠️ Firebase Admin SDK não configurado. Algumas funcionalidades podem estar limitadas.")
            return None
        
        # Inicializar Firebase Admin
        firebase_admin.initialize_app(cred)
        return firestore.client()
        
    except Exception as e:
        st.error(f"Erro ao inicializar Firebase: {str(e)}")
        return None

def get_firebase_auth():
    """Retorna instância do Firebase Auth via Pyrebase"""
    try:
        # Verificar se todas as configurações necessárias estão presentes
        required_keys = ["apiKey", "authDomain", "projectId"]
        missing_keys = [key for key in required_keys if not firebase_config.get(key)]
        
        if missing_keys:
            st.error(f"Configurações Firebase faltando: {', '.join(missing_keys)}")
            return None
        
        firebase = pyrebase.initialize_app(firebase_config)
        return firebase.auth()
        
    except Exception as e:
        st.error(f"Erro ao configurar Firebase Auth: {str(e)}")
        return None

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
