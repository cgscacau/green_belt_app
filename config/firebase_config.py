import os
import streamlit as st
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

load_dotenv()

# Configuração do Firebase
firebase_config = {
    "apiKey": st.secrets.get("FIREBASE_API_KEY", os.getenv("FIREBASE_API_KEY")),
    "authDomain": st.secrets.get("FIREBASE_AUTH_DOMAIN", os.getenv("FIREBASE_AUTH_DOMAIN")),
    "databaseURL": st.secrets.get("FIREBASE_DATABASE_URL", os.getenv("FIREBASE_DATABASE_URL")),
    "projectId": st.secrets.get("FIREBASE_PROJECT_ID", os.getenv("FIREBASE_PROJECT_ID")),
    "storageBucket": st.secrets.get("FIREBASE_STORAGE_BUCKET", os.getenv("FIREBASE_STORAGE_BUCKET")),
    "messagingSenderId": st.secrets.get("FIREBASE_MESSAGING_SENDER_ID", os.getenv("FIREBASE_MESSAGING_SENDER_ID")),
    "appId": st.secrets.get("FIREBASE_APP_ID", os.getenv("FIREBASE_APP_ID"))
}

def initialize_firebase():
    """Inicializa o Firebase Admin SDK"""
    if not firebase_admin._apps:
        # Para produção, use service account key
        if st.secrets.get("FIREBASE_SERVICE_ACCOUNT_KEY"):
            cred = credentials.Certificate(st.secrets["FIREBASE_SERVICE_ACCOUNT_KEY"])
        else:
            # Para desenvolvimento local
            cred = credentials.Certificate("path/to/serviceAccountKey.json")
        
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

def get_firebase_auth():
    """Retorna instância do Firebase Auth via Pyrebase"""
    firebase = pyrebase.initialize_app(firebase_config)
    return firebase.auth()
