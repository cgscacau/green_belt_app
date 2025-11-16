import streamlit as st
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config.firebase_config import initialize_firebase

class ProjectManager:
    def __init__(self):
        self.db = initialize_firebase()
        if not self.db:
            st.warning("⚠️ Firestore não inicializado. Algumas funcionalidades podem estar limitadas.")
    
    def create_project(self, user_uid: str, project_data: Dict) -> tuple[bool, str]:
        """Cria um novo projeto"""
        try:
            # Verificar se Firestore está disponível
            if not self.db:
                return False, "Banco de dados não disponível. Verifique a configuração do Firebase."
            
            # Validar dados obrigatórios
            if not project_data.get('name'):
                return False, "Nome do projeto é obrigatório"
            
            if not user_uid:
                return False, "Usuário não identificado"
            
            project_id = str(uuid.uuid4())
            
            # Estrutura padrão do projeto
            new_project = {
                'id': project_id,
                'user_uid': user_uid,
                'name': project_data['name'],
                'description': project_data.get('description', ''),
                'business_case': project_data.get('business_case', ''),
                'expected_savings': float(project_data.get('expected_savings', 0)),
                'start_date': project_data.get('start_date', datetime.now().isoformat()),
                'target_end_date': project_data.get('target_end_date', (datetime.now() + timedelta(days=120)).isoformat()),
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'current_phase': 'define',
                'overall_progress': 0,
                
                # Estrutura DMAIC
                'define': {
                    'charter': {'completed': False, 'data': {}},
                    'stakeholders': {'completed': False, 'data': []},
                    'voc': {'completed': False, 'data': {}},
                    'sipoc': {'completed': False, 'data': {}},
                    'timeline': {'completed': False, 'data': {}}
                },
                'measure': {
                    'data_collection_plan': {'completed': False, 'data': {}},
                    'baseline_data': {'completed': False, 'data': {}},
                    'msa': {'completed': False, 'data': {}},
                    'process_capability': {'completed': False, 'data': {}},
                    'ctq_metrics': {'completed': False, 'data': {}},
                    'uploaded_files': []
                },
                'analyze': {
                    'ishikawa': {'completed': False, 'data': {}},
                    'five_whys': {'completed': False, 'data': {}},
                    'pareto': {'completed': False, 'data': {}},
                    'hypothesis_tests': {'completed': False, 'data': {}},
                    'root_cause': {'completed': False, 'data': {}},
                    'statistical_analysis': {'completed': False, 'data': {}}
                },
                'improve': {
                    'solutions': {'completed': False, 'data': []},
                    'action_plan': {'completed': False, 'data': {}},
                    'pilot_results': {'completed': False, 'data': {}},
                    'implementation': {'completed': False, 'data': {}},
                    'validation': {'completed': False, 'data': {}}
                },
                'control': {
                    'control_plan': {'completed': False, 'data': {}},
                    'spc_charts': {'completed': False, 'data': {}},
                    'documentation': {'completed': False, 'data': {}},
                    'handover': {'completed': False, 'data': {}}
                }
            }
            

            
            # Salvar no Firestore
            self.db.collection('projects').document(project_id).set(new_project)
           
            
            # Atualizar lista de projetos do usuário
            try:
                user_ref = self.db.collection('users').document(user_uid)
                user_doc = user_ref.get()
                
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    projects = user_data.get('projects', [])
                    if project_id not in projects:  # Evitar duplicatas
                        projects.append(project_id)
                        user_ref.update({'projects': projects})
                        
                else:
                    # Criar documento do usuário se não existir
                    user_ref.set({
                        'projects': [project_id],
                        'updated_at': datetime.now().isoformat()
                    }, merge=True)
                    
                    
            except Exception as user_update_error:
                st.warning(f"⚠️ Projeto criado, mas erro ao atualizar usuário: {str(user_update_error)}")
            
            return True, project_id
            
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ Debug: Erro detalhado ao criar projeto: {error_msg}")
            
            # Análise específica de erros
            if "permission" in error_msg.lower():
                return False, "Erro de permissão no Firebase. Verifique as regras de segurança."
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                return False, "Erro de conexão. Verifique sua internet."
            elif "quota" in error_msg.lower():
                return False, "Quota do Firebase excedida. Tente novamente mais tarde."
            else:
                return False, f"Erro interno: {error_msg}"
    
    def get_user_projects(self, user_uid: str) -> List[Dict]:
        """Obtém todos os projetos do usuário"""
        try:
            if not self.db:
                st.warning("⚠️ Banco de dados não disponível")
                return []
            
            if not user_uid:
                st.warning("⚠️ ID do usuário não fornecido")
                return []
            
            projects = []
            

            
            projects_query = self.db.collection('projects').where('user_uid', '==', user_uid).stream()
            
            for doc in projects_query:
                project_data = doc.to_dict()
                if project_data:  # Verificar se dados existem
                    projects.append(project_data)
            
           
            
            # Ordenar por data de criação (mais recente primeiro)
            projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return projects
            
        except Exception as e:
            st.error(f"❌ Debug: Erro ao carregar projetos: {str(e)}")
            return []
    
    # Adicionar no arquivo src/utils/project_manager.py:
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Obtém um projeto específico"""
        try:
            if self.use_offline:
                return st.session_state.offline_projects.get(project_id)
            
            if not self.db or not project_id:
                return None
            
            doc = self.db.collection('projects').document(project_id).get()
            
            if doc.exists:
                project_data = doc.to_dict()
                
                return project_data
           
               
                return None
            
        except Exception as e:
            st.error(f"Erro ao carregar projeto: {str(e)}")
            return None

    
    def update_project(self, project_id: str, updates: Dict) -> bool:
        """Atualiza dados do projeto"""
        try:
            if not self.db or not project_id:
                return False
            
            updates['updated_at'] = datetime.now().isoformat()
            
            self.db.collection('projects').document(project_id).update(updates)
            return True
            
        except Exception as e:
            st.error(f"Erro ao atualizar projeto: {str(e)}")
            return False
    
    def delete_project(self, project_id: str, user_uid: str) -> bool:
        """Deleta um projeto"""
        try:
            if not self.db or not project_id:
                return False
            
            # Remover da coleção de projetos
            self.db.collection('projects').document(project_id).delete()
            
            # Remover da lista do usuário
            user_ref = self.db.collection('users').document(user_uid)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                projects = user_data.get('projects', [])
                if project_id in projects:
                    projects.remove(project_id)
                    user_ref.update({'projects': projects})
            
            return True
            
        except Exception as e:
            st.error(f"Erro ao deletar projeto: {str(e)}")
            return False
    
    def calculate_project_progress(self, project_data: Dict) -> float:
        """Calcula o progresso geral do projeto"""
        total_items = 0
        completed_items = 0
        
        phases = ['define', 'measure', 'analyze', 'improve', 'control']
        
        for phase in phases:
            phase_data = project_data.get(phase, {})
            for key, value in phase_data.items():
                if isinstance(value, dict) and 'completed' in value:
                    total_items += 1
                    if value['completed']:
                        completed_items += 1
        
        return (completed_items / total_items) * 100 if total_items > 0 else 0
