import streamlit as st
import sys
import os

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

st.title("🧪 Teste de Projetos")

# Simular usuário logado
if 'user_data' not in st.session_state:
    st.session_state.user_data = {
        'uid': 'test123',
        'name': 'cgscacau',
        'email': 'cgscacau@exemplo.com'
    }
    st.session_state.authentication_status = True

user_data = st.session_state.user_data
st.success(f"✅ Usuário simulado: {user_data['name']}")

# Testar imports
st.subheader("1. 📦 Testando Imports")

try:
    from src.utils.project_manager import ProjectManager
    st.success("✅ ProjectManager importado")
    pm = ProjectManager()
    st.success("✅ ProjectManager instanciado")
except Exception as e:
    st.error(f"❌ Erro no ProjectManager: {str(e)}")
    st.stop()

try:
    from config.firebase_config import get_firestore_client, test_firebase_connection
    st.success("✅ Firebase config importado")
except Exception as e:
    st.error(f"❌ Erro no Firebase config: {str(e)}")

# Testar conexão Firebase
st.subheader("2. 🔥 Testando Conexão Firebase")

if st.button("Testar Conexão"):
    try:
        success, message = test_firebase_connection()
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
    except Exception as e:
        st.error(f"❌ Erro no teste: {str(e)}")

# Testar Firestore diretamente
st.subheader("3. 🗄️ Testando Firestore")

if st.button("Testar Firestore Direto"):
    try:
        db = get_firestore_client()
        if db:
            st.success("✅ Cliente Firestore obtido")
            
            # Tentar listar coleções
            collections = list(db.collections())
            st.write(f"📁 Coleções encontradas: {len(collections)}")
            
            for col in collections:
                st.write(f"- {col.id}")
            
        else:
            st.error("❌ Cliente Firestore não obtido")
    except Exception as e:
        st.error(f"❌ Erro no Firestore: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

# Testar busca de projetos
st.subheader("4. 📊 Testando Busca de Projetos")

if st.button("Buscar Projetos"):
    try:
        projects = pm.get_user_projects(user_data['uid'])
        st.write(f"📊 Projetos encontrados: {len(projects)}")
        
        if projects:
            for i, project in enumerate(projects):
                st.write(f"**{i+1}.** {project.get('name', 'Sem nome')}")
                with st.expander(f"Detalhes do projeto {i+1}"):
                    st.json(project)
        else:
            st.warning("⚠️ Nenhum projeto encontrado")
            
            # Verificar se é problema de UID
            st.write(f"**UID usado na busca:** {user_data['uid']}")
            
    except Exception as e:
        st.error(f"❌ Erro ao buscar projetos: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

# Testar criação de projeto
st.subheader("5. ➕ Testando Criação de Projeto")

with st.form("test_project"):
    project_name = st.text_input("Nome do Projeto", value="Projeto Teste")
    project_desc = st.text_area("Descrição", value="Projeto de teste para verificar conexão")
    
    if st.form_submit_button("Criar Projeto Teste"):
        try:
            project_data = {
                'name': project_name,
                'description': project_desc,
                'expected_savings': 1000.0,
                'start_date': '2024-01-01',
                'target_end_date': '2024-06-01'
            }
            
            success, result = pm.create_project(user_data['uid'], project_data)
            
            if success:
                st.success(f"✅ Projeto criado! ID: {result}")
            else:
                st.error(f"❌ Erro ao criar: {result}")
                
        except Exception as e:
            st.error(f"❌ Erro na criação: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# Verificar dados do usuário real
st.subheader("6. 👤 Dados do Usuário Real")

if st.button("Usar Dados Reais"):
    # Tentar obter dados do usuário real do session_state principal
    try:
        from src.auth.firebase_auth import FirebaseAuth
        auth = FirebaseAuth()
        
        # Mostrar informações sobre o usuário atual
        if hasattr(st.session_state, 'user_data') and st.session_state.user_data:
            real_user = st.session_state.user_data
            st.json(real_user)
            
            # Buscar projetos com UID real
            if real_user.get('uid'):
                projects = pm.get_user_projects(real_user['uid'])
                st.write(f"📊 Projetos do usuário real: {len(projects)}")
                
                for project in projects:
                    st.write(f"- {project.get('name', 'Sem nome')}")
        else:
            st.warning("⚠️ Nenhum dado de usuário real encontrado")
            
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
