import streamlit as st
from src.auth.firebase_auth import FirebaseAuth

def show_login_page():
    st.set_page_config(
        page_title="Green Belt Six Sigma - Login",
        page_icon="🟢",
        layout="centered"
    )
    
    # CSS customizado
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .login-form {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='main-header'>🟢 Green Belt Six Sigma</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #666;'>Sistema de Gestão de Projetos DMAIC</h3>", unsafe_allow_html=True)
    
    auth = FirebaseAuth()
    
    # Tabs para Login e Registro
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Registrar"])
    
    with tab1:
        with st.form("login_form"):
            st.markdown("### Acesse sua conta")
            email = st.text_input("📧 Email", placeholder="seu@email.com")
            password = st.text_input("🔒 Senha", type="password", placeholder="Sua senha")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                login_button = st.form_submit_button("Entrar", use_container_width=True)
            with col2:
                forgot_password = st.form_submit_button("Esqueci a senha", use_container_width=True)
            
            if login_button:
                if email and password:
                    with st.spinner("Autenticando..."):
                        success, result = auth.login_user(email, password)
                    
                    if success:
                        st.session_state.user_data = result
                        st.session_state.authentication_status = True
                        st.session_state.user_email = email
                        st.success("Login realizado com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(result)
                else:
                    st.warning("Por favor, preencha todos os campos")
            
            if forgot_password:
                if email:
                    success, message = auth.reset_password(email)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.warning("Digite seu email para recuperar a senha")
    
    with tab2:
        with st.form("register_form"):
            st.markdown("### Criar nova conta")
            reg_name = st.text_input("👤 Nome completo", placeholder="Seu nome completo")
            reg_email = st.text_input("📧 Email", placeholder="seu@email.com", key="reg_email")
            reg_company = st.text_input("🏢 Empresa (opcional)", placeholder="Nome da empresa")
            reg_password = st.text_input("🔒 Senha", type="password", placeholder="Mínimo 8 caracteres", key="reg_password")
            reg_confirm_password = st.text_input("🔒 Confirmar senha", type="password", placeholder="Confirme sua senha")
            
            # Indicador de força da senha
            if reg_password:
                is_valid, message = auth.validate_password(reg_password)
                if is_valid:
                    st.success("✅ Senha forte")
                else:
                    st.warning(f"⚠️ {message}")
            
            terms_accepted = st.checkbox("Aceito os termos de uso e política de privacidade")
            
            register_button = st.form_submit_button("Criar conta", use_container_width=True)
            
            if register_button:
                if all([reg_name, reg_email, reg_password, reg_confirm_password]):
                    if reg_password != reg_confirm_password:
                        st.error("As senhas não coincidem")
                    elif not terms_accepted:
                        st.error("Você deve aceitar os termos de uso")
                    else:
                        with st.spinner("Criando conta..."):
                            success, message = auth.register_user(
                                reg_email, reg_password, reg_name, reg_company
                            )
                        
                        if success:
                            st.success(message)
                            st.info("Após verificar seu email, você poderá fazer login")
                        else:
                            st.error(message)
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios")
