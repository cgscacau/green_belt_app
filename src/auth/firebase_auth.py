import streamlit as st
import time
import re
from config.firebase_config import FirebaseRestAuth, initialize_firebase, check_firebase_config

class FirebaseAuth:
    def __init__(self):
        try:
            self.auth = FirebaseRestAuth()
            self.db = initialize_firebase()
        except Exception as e:
            st.error(f"❌ Erro na configuração do Firebase: {str(e)}")
            st.info("Verifique se a API Key do Firebase está correta nas configurações.")
            st.stop()
    
    def validate_email(self, email):
        """Valida formato do email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        """Valida força da senha"""
        if len(password) < 6:
            return False, "Senha deve ter pelo menos 6 caracteres (mínimo do Firebase)"
        if len(password) < 8:
            return True, "Senha válida (recomendamos pelo menos 8 caracteres)"
        
        strength_checks = [
            (re.search(r'[A-Z]', password), "uma letra maiúscula"),
            (re.search(r'[a-z]', password), "uma letra minúscula"),
            (re.search(r'\d', password), "um número"),
            (re.search(r'[!@#$%^&*(),.?":{}|<>]', password), "um caractere especial")
        ]
        
        missing = [desc for check, desc in strength_checks if not check]
        
        if len(missing) > 2:
            return True, f"Senha válida (para maior segurança, adicione: {', '.join(missing[:2])})"
        
        return True, "Senha forte!"
    
    def register_user(self, email, password, name, company=""):
        """Registra novo usuário"""
        try:
            # Validações básicas
            if not self.validate_email(email):
                return False, "❌ Formato de email inválido"
            
            if len(password) < 6:
                return False, "❌ Senha deve ter pelo menos 6 caracteres"
            
            # Tentar registrar no Firebase Auth
            success, result = self.auth.sign_up_with_email_password(email, password)
            
            if not success:
                return self._handle_auth_error(result, "registro")
            
            # Extrair dados do usuário
            user_data = {
                'uid': result.get('localId'),
                'email': email,
                'name': name,
                'company': company,
                'created_at': time.time(),
                'email_verified': result.get('emailVerified', False),
                'projects': [],
                'idToken': result.get('idToken'),
                'refreshToken': result.get('refreshToken')
            }
            
            # Salvar no Firestore se disponível
            if self.db and user_data['uid']:
                try:
                    self.db.collection('users').document(user_data['uid']).set({
                        'uid': user_data['uid'],
                        'email': email,
                        'name': name,
                        'company': company,
                        'created_at': user_data['created_at'],
                        'email_verified': False,
                        'projects': []
                    })
                except Exception as e:
                    st.warning(f"Usuário criado, mas erro ao salvar dados: {str(e)}")
            
            # Tentar enviar email de verificação
            try:
                self.auth.send_email_verification(user_data['idToken'])
                message = "✅ Conta criada com sucesso! Email de verificação enviado."
            except:
                message = "✅ Conta criada com sucesso!"
            
            return True, message
            
        except Exception as e:
            return False, f"❌ Erro inesperado: {str(e)}"
    
    def login_user(self, email, password):
        """Autentica usuário"""
        try:
            # Validação básica
            if not email or not password:
                return False, "❌ Email e senha são obrigatórios"
            
            if not self.validate_email(email):
                return False, "❌ Formato de email inválido"
            
            # Tentar autenticar
            success, result = self.auth.sign_in_with_email_password(email, password)
            
            if not success:
                return self._handle_auth_error(result, "login")
            
            # Montar dados do usuário
            user_data = {
                'uid': result.get('localId'),
                'email': result.get('email', email),
                'name': email.split('@')[0],  # Fallback
                'company': '',
                'idToken': result.get('idToken'),
                'refreshToken': result.get('refreshToken'),
                'email_verified': result.get('emailVerified', False),
                'projects': []
            }
            
            # Buscar dados adicionais no Firestore
            if self.db and user_data['uid']:
                try:
                    user_doc = self.db.collection('users').document(user_data['uid']).get()
                    if user_doc.exists:
                        firestore_data = user_doc.to_dict()
                        user_data.update(firestore_data)
                        # Manter tokens atualizados
                        user_data['idToken'] = result.get('idToken')
                        user_data['refreshToken'] = result.get('refreshToken')
                except Exception as e:
                    st.warning(f"Erro ao carregar dados do usuário: {str(e)}")
            
            return True, user_data
                
        except Exception as e:
            return False, f"❌ Erro inesperado no login: {str(e)}"
    
    def reset_password(self, email):
        """Envia email para reset de senha"""
        try:
            if not self.validate_email(email):
                return False, "❌ Formato de email inválido"
            
            success, message = self.auth.send_password_reset_email(email)
            
            if success:
                return True, "✅ Email de recuperação enviado com sucesso!"
            else:
                return self._handle_auth_error(message, "reset de senha")
                
        except Exception as e:
            return False, f"❌ Erro ao enviar email: {str(e)}"
    
    def _handle_auth_error(self, error_message, operation):
        """Trata erros de autenticação de forma amigável"""
        error_map = {
            # Erros de registro
            "EMAIL_EXISTS": "Este email já está cadastrado. Tente fazer login.",
            "INVALID_EMAIL": "Formato de email inválido.",
            "WEAK_PASSWORD": "Senha muito fraca. Use pelo menos 6 caracteres.",
            "MISSING_PASSWORD": "Senha é obrigatória.",
            
            # Erros de login
            "INVALID_LOGIN_CREDENTIALS": "Email ou senha incorretos. Verifique suas credenciais.",
            "EMAIL_NOT_FOUND": "Email não encontrado. Verifique o email ou registre-se.",
            "INVALID_PASSWORD": "Senha incorreta.",
            "USER_DISABLED": "Esta conta foi desabilitada.",
            "TOO_MANY_ATTEMPTS_TRY_LATER": "Muitas tentativas. Tente novamente mais tarde.",
            
            # Erros de reset
            "EMAIL_NOT_FOUND": "Email não encontrado no sistema.",
            "MISSING_EMAIL": "Email é obrigatório para recuperação.",
        }
        
        # Procurar por mensagens conhecidas
        for error_key, friendly_message in error_map.items():
            if error_key in str(error_message).upper():
                return False, f"❌ {friendly_message}"
        
        # Mensagem genérica para erros não mapeados
        return False, f"❌ Erro no {operation}. Tente novamente ou entre em contato com o suporte."
    
    def logout_user(self):
        """Realiza logout do usuário"""
        keys_to_remove = [
            'user_data', 
            'authentication_status', 
            'user_email',
            'show_create_project',
            'current_project'
        ]
        
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    def check_connection(self):
        """Verifica se a conexão com Firebase está funcionando"""
        try:
            # Teste simples: tentar fazer uma requisição inválida para verificar conectividade
            self.auth.get_user_info("invalid_token")
            return True
        except:
            return False
