import streamlit as st
import time
from config.firebase_config import get_firebase_auth, initialize_firebase, check_firebase_config
import re

class FirebaseAuth:
    def __init__(self):
        self.auth = get_firebase_auth()
        self.db = initialize_firebase()
        
        # Verificar se a configuração está correta
        if not self.auth:
            st.error("❌ Erro na configuração do Firebase. Verifique suas credenciais.")
            st.stop()
    
    def validate_email(self, email):
        """Valida formato do email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        """Valida força da senha"""
        if len(password) < 6:  # Firebase mínimo é 6
            return False, "Senha deve ter pelo menos 6 caracteres"
        if len(password) < 8:
            return False, "Recomendamos pelo menos 8 caracteres"
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
            
            if len(password) < 6:
                return False, "Senha deve ter pelo menos 6 caracteres"
            
            # Criar usuário no Firebase Auth
            user = self.auth.create_user_with_email_and_password(email, password)
            
            # Tentar enviar email de verificação
            try:
                self.auth.send_email_verification(user['idToken'])
                verification_sent = True
            except:
                verification_sent = False
            
            # Salvar dados adicionais no Firestore (se disponível)
            if self.db:
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
            
            message = "Usuário registrado com sucesso!"
            if verification_sent:
                message += " Verifique seu email."
            
            return True, message
            
        except Exception as e:
            error_message = str(e)
            if "EMAIL_EXISTS" in error_message:
                return False, "Este email já está cadastrado"
            elif "WEAK_PASSWORD" in error_message:
                return False, "Senha muito fraca"
            elif "INVALID_EMAIL" in error_message:
                return False, "Email inválido"
            else:
                return False, f"Erro ao registrar: {error_message}"
    
    def login_user(self, email, password):
        """Autentica usuário"""
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            
            # Buscar dados do usuário no Firestore (se disponível)
            user_data = {
                'uid': user['localId'],
                'email': email,
                'name': email.split('@')[0],  # Fallback se não houver Firestore
                'company': '',
                'idToken': user['idToken'],
                'refreshToken': user['refreshToken'],
                'projects': []
            }
            
            if self.db:
                user_doc = self.db.collection('users').document(user['localId']).get()
                if user_doc.exists:
                    firestore_data = user_doc.to_dict()
                    user_data.update(firestore_data)
                    user_data['idToken'] = user['idToken']
                    user_data['refreshToken'] = user['refreshToken']
            
            return True, user_data
                
        except Exception as e:
            error_message = str(e)
            if "INVALID_EMAIL" in error_message:
                return False, "Email inválido"
            elif "EMAIL_NOT_FOUND" in error_message:
                return False, "Email não cadastrado"
            elif "INVALID_PASSWORD" in error_message:
                return False, "Senha incorreta"
            elif "USER_DISABLED" in error_message:
                return False, "Usuário desabilitado"
            else:
                return False, f"Erro ao fazer login: {error_message}"
    
    def reset_password(self, email):
        """Envia email para reset de senha"""
        try:
            if not self.validate_email(email):
                return False, "Email inválido"
            
            self.auth.send_password_reset_email(email)
            return True, "Email de recuperação enviado com sucesso"
        except Exception as e:
            error_message = str(e)
            if "EMAIL_NOT_FOUND" in error_message:
                return False, "Email não encontrado"
            else:
                return False, f"Erro ao enviar email: {error_message}"
    
    def logout_user(self):
        """Realiza logout do usuário"""
        keys_to_remove = [
            'user_data', 
            'authentication_status', 
            'user_email',
            'show_create_project'
        ]
        
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
