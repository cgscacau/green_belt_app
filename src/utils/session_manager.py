"""
Gerenciador centralizado de sessão do Streamlit
Centraliza todas as operações de session_state para consistência
"""

import streamlit as st
import time
from typing import Dict, List, Optional, Any
from enum import Enum
import hashlib

class PageType(Enum):
    """Tipos de páginas da aplicação"""
    DASHBOARD = "dashboard"
    PROJECTS = "projects"
    DMAIC = "dmaic"
    REPORTS = "reports"
    HELP = "help"

class SessionManager:
    """Gerenciador centralizado do session_state"""
    
    # Chaves padrão do session_state
    KEYS = {
        'AUTH_STATUS': 'authentication_status',
        'USER_DATA': 'user_data',
        'CURRENT_PAGE': 'current_page',
        'CURRENT_PROJECT': 'current_project',
        'CURRENT_PHASE': 'current_phase',
        'CURRENT_DMAIC_PHASE': 'current_dmaic_phase',
        'NEWLY_CREATED_PROJECT': 'newly_created_project',
        'SHOW_CREATE_PROJECT': 'show_create_project',
        'NAV_COUNTER': 'nav_counter',
        'CACHED_PROJECTS': 'cached_projects',
        'PROJECTS_CACHE_TIME': 'projects_cache_time'
    }
    
    @staticmethod
    def initialize_session():
        """Inicializa valores padrão do session_state se não existirem"""
        defaults = {
            SessionManager.KEYS['AUTH_STATUS']: False,
            SessionManager.KEYS['CURRENT_PAGE']: PageType.DASHBOARD.value,
            SessionManager.KEYS['NAV_COUNTER']: 0,
            SessionManager.KEYS['SHOW_CREATE_PROJECT']: False
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @staticmethod
    def is_authenticated() -> bool:
        """Verifica se o usuário está autenticado"""
        return st.session_state.get(SessionManager.KEYS['AUTH_STATUS'], False)
    
    @staticmethod
    def get_user_data() -> Dict:
        """Retorna dados do usuário autenticado"""
        return st.session_state.get(SessionManager.KEYS['USER_DATA'], {})
    
    @staticmethod
    def set_user_data(user_data: Dict):
        """Define dados do usuário"""
        st.session_state[SessionManager.KEYS['USER_DATA']] = user_data
        st.session_state[SessionManager.KEYS['AUTH_STATUS']] = True
    
    @staticmethod
    def get_current_page() -> str:
        """Retorna a página atual"""
        return st.session_state.get(SessionManager.KEYS['CURRENT_PAGE'], PageType.DASHBOARD.value)
    
    @staticmethod
    def set_current_page(page: str):
        """Define a página atual"""
        if page in [p.value for p in PageType]:
            st.session_state[SessionManager.KEYS['CURRENT_PAGE']] = page
        else:
            raise ValueError(f"Página inválida: {page}")
    
    @staticmethod
    def get_current_project() -> Optional[Dict]:
        """Retorna o projeto atual"""
        return st.session_state.get(SessionManager.KEYS['CURRENT_PROJECT'])
    
    @staticmethod
    def set_current_project(project: Dict):
        """Define o projeto atual"""
        st.session_state[SessionManager.KEYS['CURRENT_PROJECT']] = project
        # Limpar fase atual quando trocar de projeto
        if SessionManager.KEYS['CURRENT_PHASE'] in st.session_state:
            del st.session_state[SessionManager.KEYS['CURRENT_PHASE']]
        if SessionManager.KEYS['CURRENT_DMAIC_PHASE'] in st.session_state:
            del st.session_state[SessionManager.KEYS['CURRENT_DMAIC_PHASE']]
    
    @staticmethod
    def get_current_phase() -> str:
        """Retorna a fase atual (suporta ambas as chaves por compatibilidade)"""
        # Priorizar current_phase, fallback para current_dmaic_phase
        return (st.session_state.get(SessionManager.KEYS['CURRENT_PHASE']) or 
                st.session_state.get(SessionManager.KEYS['CURRENT_DMAIC_PHASE'], 'define'))
    
    @staticmethod
    def set_current_phase(phase: str):
        """Define a fase atual (sincroniza ambas as chaves)"""
        valid_phases = ['define', 'measure', 'analyze', 'improve', 'control']
        if phase not in valid_phases:
            raise ValueError(f"Fase inválida: {phase}. Deve ser uma de: {valid_phases}")
        
        # Sincronizar ambas as chaves para compatibilidade
        st.session_state[SessionManager.KEYS['CURRENT_PHASE']] = phase
        st.session_state[SessionManager.KEYS['CURRENT_DMAIC_PHASE']] = phase
    
    @staticmethod
    def clear_project_context():
        """Limpa todo o contexto relacionado a projeto"""
        keys_to_clear = [
            SessionManager.KEYS['CURRENT_PROJECT'],
            SessionManager.KEYS['CURRENT_PHASE'],
            SessionManager.KEYS['CURRENT_DMAIC_PHASE'],
            SessionManager.KEYS['NEWLY_CREATED_PROJECT'],
            SessionManager.KEYS['SHOW_CREATE_PROJECT']
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def clear_form_data():
        """Limpa dados de formulários"""
        form_keys = [
            'project_name_input', 'project_description_input', 
            'project_business_case_input', 'project_savings_input',
            'project_start_date_input', 'project_end_date_input',
            'project_problem_input', 'project_success_input'
        ]
        
        for key in form_keys:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def navigate_to_page(page: str, clear_project: bool = False, clear_forms: bool = False):
        """Navegação centralizada entre páginas"""
        SessionManager.set_current_page(page)
        
        if clear_project:
            SessionManager.clear_project_context()
        
        if clear_forms:
            SessionManager.clear_form_data()
        
        st.rerun()
    
    @staticmethod
    def navigate_to_dmaic(project: Dict, phase: str = 'define'):
        """Navegação específica para DMAIC"""
        SessionManager.set_current_project(project)
        SessionManager.set_current_phase(phase)
        SessionManager.set_current_page(PageType.DMAIC.value)
        st.rerun()
    
    @staticmethod
    def logout():
        """Faz logout completo do usuário"""
        # Chaves críticas que devem ser preservadas durante logout
        preserve_keys = {'theme', 'sidebar_state'}
        
        # Salvar chaves a serem preservadas
        preserved_data = {}
        for key in preserve_keys:
            if key in st.session_state:
                preserved_data[key] = st.session_state[key]
        
        # Limpar tudo
        st.session_state.clear()
        
        # Restaurar chaves preservadas
        for key, value in preserved_data.items():
            st.session_state[key] = value
        
        # Reinicializar valores padrão
        SessionManager.initialize_session()
        
        st.rerun()
    
    @staticmethod
    def generate_unique_key(base_key: str, suffix: str = None) -> str:
        """Gera chave única para componentes Streamlit"""
        counter = st.session_state.get(SessionManager.KEYS['NAV_COUNTER'], 0)
        timestamp = str(int(time.time() * 1000))[-6:]  # Últimos 6 dígitos do timestamp
        
        if suffix:
            unique_key = f"{base_key}_{suffix}_{counter}_{timestamp}"
        else:
            unique_key = f"{base_key}_{counter}_{timestamp}"
        
        # Incrementar contador
        st.session_state[SessionManager.KEYS['NAV_COUNTER']] = counter + 1
        
        return unique_key
    
    @staticmethod
    def get_cached_projects(user_uid: str) -> Optional[List[Dict]]:
        """Retorna projetos do cache se ainda válidos"""
        cache_key = f"cached_projects_{user_uid}"
        cache_time_key = f"projects_cache_time_{user_uid}"
        
        if cache_key not in st.session_state or cache_time_key not in st.session_state:
            return None
        
        # Verificar se cache ainda é válido (5 minutos)
        cache_time = st.session_state[cache_time_key]
        if time.time() - cache_time > 300:  # 5 minutos
            # Cache expirado, limpar
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            if cache_time_key in st.session_state:
                del st.session_state[cache_time_key]
            return None
        
        return st.session_state[cache_key]
    
    @staticmethod
    def set_cached_projects(user_uid: str, projects: List[Dict]):
        """Armazena projetos no cache"""
        cache_key = f"cached_projects_{user_uid}"
        cache_time_key = f"projects_cache_time_{user_uid}"
        
        st.session_state[cache_key] = projects
        st.session_state[cache_time_key] = time.time()
    
    @staticmethod
    def invalidate_projects_cache(user_uid: str):
        """Invalida cache de projetos do usuário"""
        cache_key = f"cached_projects_{user_uid}"
        cache_time_key = f"projects_cache_time_{user_uid}"
        
        if cache_key in st.session_state:
            del st.session_state[cache_key]
        if cache_time_key in st.session_state:
            del st.session_state[cache_time_key]
    
    @staticmethod
    def get_project_data_hash(project: Dict) -> str:
        """Gera hash dos dados do projeto para cache"""
        project_str = str(sorted(project.items()))
        return hashlib.md5(project_str.encode()).hexdigest()[:8]
    
    @staticmethod
    def debug_session_info() -> Dict:
        """Retorna informações de debug do session_state"""
        current_project = SessionManager.get_current_project()
        
        return {
            'authenticated': SessionManager.is_authenticated(),
            'current_page': SessionManager.get_current_page(),
            'current_project_name': current_project.get('name') if current_project else None,
            'current_project_id': current_project.get('id') if current_project else None,
            'current_phase': SessionManager.get_current_phase(),
            'user_email': SessionManager.get_user_data().get('email'),
            'session_keys_count': len(st.session_state),
            'nav_counter': st.session_state.get(SessionManager.KEYS['NAV_COUNTER'], 0)
        }
    
    @staticmethod
    def clean_expired_cache():
        """Limpa caches expirados do session_state"""
        current_time = time.time()
        keys_to_remove = []
        
        for key in st.session_state.keys():
            # Procurar por chaves de cache de tempo
            if key.endswith('_cache_time'):
                cache_time = st.session_state[key]
                if current_time - cache_time > 300:  # 5 minutos
                    # Marcar para remoção
                    keys_to_remove.append(key)
                    # Também remover o cache correspondente
                    cache_key = key.replace('_cache_time', '')
                    if cache_key in st.session_state:
                        keys_to_remove.append(cache_key)
        
        # Remover chaves expiradas
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        
        return len(keys_to_remove)

class FormManager:
    """Gerenciador específico para formulários"""
    
    @staticmethod
    def get_form_data(form_name: str) -> Dict:
        """Retorna dados de um formulário específico"""
        form_key = f"form_data_{form_name}"
        return st.session_state.get(form_key, {})
    
    @staticmethod
    def set_form_data(form_name: str, data: Dict):
        """Armazena dados de um formulário"""
        form_key = f"form_data_{form_name}"
        st.session_state[form_key] = data
    
    @staticmethod
    def clear_form_data(form_name: str):
        """Limpa dados de um formulário específico"""
        form_key = f"form_data_{form_name}"
        if form_key in st.session_state:
            del st.session_state[form_key]
    
    @staticmethod
    def validate_and_store_project_form() -> Dict:
        """Valida e armazena dados do formulário de projeto"""
        form_data = {
            'name': st.session_state.get('project_name_input', '').strip(),
            'description': st.session_state.get('project_description_input', '').strip(),
            'business_case': st.session_state.get('project_business_case_input', '').strip(),
            'problem_statement': st.session_state.get('project_problem_input', '').strip(),
            'success_criteria': st.session_state.get('project_success_input', '').strip(),
            'expected_savings': st.session_state.get('project_savings_input', 0.0),
            'start_date': st.session_state.get('project_start_date_input'),
            'target_end_date': st.session_state.get('project_end_date_input')
        }
        
        # Converter datas para string se necessário
        if form_data['start_date']:
            form_data['start_date'] = form_data['start_date'].isoformat()
        if form_data['target_end_date']:
            form_data['target_end_date'] = form_data['target_end_date'].isoformat()
        
        FormManager.set_form_data('project_creation', form_data)
        return form_data

# Instância global para facilitar uso
session_manager = SessionManager()
form_manager = FormManager()
