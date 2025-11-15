import streamlit as st
import time
from config.firebase_config import get_firebase_auth, initialize_firebase
from firebase_admin import auth
import re

class FirebaseAuth:
    def __init__(self):
        self.auth = get_firebase_auth()
        self.db = initialize_firebase()
        
    def validate_email(self, email):
        """Valida formato do email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        """Valida força da senha"""
        if len(password) < 8:
            return False, "Senha deve ter pelo menos 8 caracteres"
        if not re.search(r'[A-Z]', password):
            return False, "Senha deve conter pelo menos uma letra maiúscula"
        if not re.search(r'[a-z]', password):
            return False, "Senha deve conter pelo menos uma letra minúscula"
        if not re.search(r'\d', password):
            return False, "Senha deve conter pelo menos um número"
        return True, "Senha válida"
    
    def register_user(self, email, password, name, company=""):
        """Registra novo usuário"""
        try:
            # Validações
            if not self.validate_email(email):
                return False, "Email inválido"
            
            is_valid, message = self.validate_password(password)
            if not is_valid:
                return False, message
            
            # Criar usuário no Firebase Auth
            user = self.auth.create_user_with_email_and_password(email, password)
            
            # Enviar email de verificação
            self.auth.send_email_verification(user['idToken'])
            
            # Salvar dados adicionais no Firestore
            user_data = {
                'uid': user['localId'],
                'email': email,
                'name': name,
                'company': company,
                'created_at': time.time(),
                'email_verified': False,
                'projects': []
            }
            
            self.db.collection('users').document(user['localId']).set(user_data)
            
            return True, "Usuário registrado com sucesso! Verifique seu email."
            
        except Exception as e:
            error_message = str(e)
            if "EMAIL_EXISTS" in error_message:
                return False, "Este email já está cadastrado"
            elif "WEAK_PASSWORD" in error_message:
                return False, "Senha muito fraca"
            else:
                return False, f"Erro ao registrar usuário: {error_message}"
    
    def login_user(self, email, password):
        """Autentica usuário"""
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            
            # Verificar se email foi verificado
            account_info = self.auth.get_account_info(user['idToken'])
            if not account_info['users'][0]['emailVerified']:
                return False, "Por favor, verifique seu email antes de fazer login"
            
            # Buscar dados do usuário no Firestore
            user_doc = self.db.collection('users').document(user['localId']).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_data['idToken'] = user['idToken']
                user_data['refreshToken'] = user['refreshToken']
                return True, user_data
            else:
                return False, "Dados do usuário não encontrados"
                
        except Exception as e:
            error_message = str(e)
            if "INVALID_EMAIL" in error_message:
                return False, "Email inválido"
            elif "EMAIL_NOT_FOUND" in error_message:
                return False, "Email não cadastrado"
            elif "INVALID_PASSWORD" in error_message:
                return False, "Senha incorreta"
            else:
                return False, f"Erro ao fazer login: {error_message}"
    
    def reset_password(self, email):
        """Envia email para reset de senha"""
        try:
            self.auth.send_password_reset_email(email)
            return True, "Email de recuperação enviado com sucesso"
        except Exception as e:
            return False, f"Erro ao enviar email: {str(e)}"
    
    def logout_user(self):
        """Realiza logout do usuário"""
        for key in ['user_data', 'authentication_status', 'user_email']:
            if key in st.session_state:
                del st.session_state[key]
