import streamlit as st
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class OfflineProjectManager:
    """Gerenciador de projetos offline usando session_state"""
    
    def __init__(self):
        if 'offline_projects' not in st.session_state:
            st.session_state.offline_projects = {}
        
        if 'offline_users' not in st.session_state:
            st.session_state.offline_users = {}
    
    def create_project(self, user_uid: str, project_data: Dict) -> tuple[bool, str]:
        """Cria projeto offline"""
        try:
            project_id = str(uuid.uuid4())
            
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
                'offline_mode': True,
                
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
            
            # Salvar projeto
            st.session_state.offline_projects[project_id] = new_project
            
            # Atualizar lista de projetos do usuário
            if user_uid not in st.session_state.offline_users:
                st.session_state.offline_users[user_uid] = {'projects': []}
            
            if project_id not in st.session_state.offline_users[user_uid]['projects']:
                st.session_state.offline_users[user_uid]['projects'].append(project_id)
            
            return True, project_id
            
        except Exception as e:
            return False, f"Erro offline: {str(e)}"
    
    def get_user_projects(self, user_uid: str) -> List[Dict]:
        """Obtém projetos do usuário offline"""
        try:
            user_data = st.session_state.offline_users.get(user_uid, {})
            project_ids = user_data.get('projects', [])
            
            projects = []
            for project_id in project_ids:
                if project_id in st.session_state.offline_projects:
                    projects.append(st.session_state.offline_projects[project_id])
            
            # Ordenar por data de criação
            projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return projects
            
        except Exception as e:
            st.error(f"Erro ao carregar projetos offline: {str(e)}")
            return []
    
    def calculate_project_progress(self, project_data: Dict) -> float:
        """Calcula progresso offline"""
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
