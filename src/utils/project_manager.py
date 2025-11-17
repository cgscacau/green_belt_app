"""
Gerenciador de projetos Six Sigma
Versão melhorada com cache, validação e tratamento de erros robusto
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple, Any, Union
import time
import logging
from datetime import datetime, timedelta
import json
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum

# Tentar importar utilitários melhorados
try:
    from src.config.firebase_config import get_firestore_client
    from src.utils.session_manager import SessionManager
    from src.config.dmaic_config import (
        DMAIC_PHASES_CONFIG, DMACPhase, calculate_phase_completion_percentage,
        validate_phase_data
    )
    HAS_NEW_UTILS = True
except ImportError:
    # Fallback para compatibilidade
    try:
        from config.firebase_config import get_firestore_client
    except ImportError:
        def get_firestore_client():
            st.error("❌ Firebase não configurado")
            return None
    
    class SessionManager:
        @staticmethod
        def get_user_data():
            return st.session_state.get('user_data', {})
        
        @staticmethod
        def get_cached_projects(user_uid):
            return st.session_state.get(f'cached_projects_{user_uid}')
        
        @staticmethod
        def set_cached_projects(user_uid, projects):
            st.session_state[f'cached_projects_{user_uid}'] = projects
        
        @staticmethod
        def invalidate_projects_cache(user_uid):
            cache_key = f'cached_projects_{user_uid}'
            if cache_key in st.session_state:
                del st.session_state[cache_key]
    
    def calculate_phase_completion_percentage(phase_data, phase):
        if not isinstance(phase_data, dict):
            return 0.0
        tools_count = 5 if phase == 'define' else 4
        completed = sum(1 for tool_data in phase_data.values() 
                       if isinstance(tool_data, dict) and tool_data.get('completed', False))
        return (completed / tools_count) * 100 if tools_count > 0 else 0.0
    
    HAS_NEW_UTILS = False

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectStatus(Enum):
    """Status possíveis do projeto"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

@dataclass
class ProjectMetrics:
    """Métricas de um projeto"""
    total_phases: int = 5
    completed_phases: int = 0
    overall_progress: float = 0.0
    expected_savings: float = 0.0
    actual_savings: float = 0.0
    duration_days: int = 0
    tools_completed: int = 0
    tools_total: int = 21  # Total de ferramentas em todas as fases

@dataclass
class ProjectValidation:
    """Resultado da validação de um projeto"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

class ProjectManager:
    """Gerenciador de projetos Six Sigma - Versão melhorada"""
    
    def __init__(self):
        """Inicializa o gerenciador de projetos"""
        self.db = get_firestore_client()
        self.collection_name = "projects"
        self.cache_ttl = 300  # 5 minutos
        
        # Estatísticas da sessão
        self.session_stats = {
            'projects_loaded': 0,
            'projects_created': 0,
            'projects_updated': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        logger.info("ProjectManager inicializado")
    
    def create_project(self, user_uid: str, project_data: Dict) -> Tuple[bool, Union[str, Dict]]:
        """
        Cria um novo projeto com validação completa
        
        Args:
            user_uid: ID do usuário
            project_data: Dados do projeto
            
        Returns:
            Tuple[bool, Union[str, Dict]]: (sucesso, id_projeto_ou_erro)
        """
        try:
            # Validar dados de entrada
            validation = self._validate_project_data(project_data)
            if not validation.is_valid:
                error_msg = f"Dados inválidos: {'; '.join(validation.errors)}"
                logger.error(f"Falha na validação do projeto: {error_msg}")
                return False, error_msg
            
            # Preparar dados do projeto
            prepared_data = self._prepare_project_data(user_uid, project_data)
            
            # Verificar conexão com Firebase
            if not self.db:
                return False, "Erro de conexão com o banco de dados"
            
            # Criar documento no Firestore
            doc_ref = self.db.collection(self.collection_name).document()
            prepared_data['id'] = doc_ref.id
            
            # Salvar no banco
            doc_ref.set(prepared_data)
            
            # Invalidar cache do usuário
            SessionManager.invalidate_projects_cache(user_uid)
            
            # Atualizar estatísticas
            self.session_stats['projects_created'] += 1
            
            logger.info(f"Projeto criado com sucesso: {doc_ref.id}")
            return True, doc_ref.id
            
        except Exception as e:
            error_msg = f"Erro ao criar projeto: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_user_projects(self, user_uid: str, force_refresh: bool = False) -> List[Dict]:
        """Obtém projetos do usuário"""
        try:
            # Verificar cache primeiro
            if not force_refresh:
                cached_projects = SessionManager.get_cached_projects(user_uid)
                if cached_projects is not None:
                    return cached_projects
            
            if not self.db:
                st.error("❌ Banco de dados não disponível")
                return []
            
            # Query no Firestore - IMPORTANTE: verificar se a coleção existe
            projects_ref = self.db.collection(self.collection_name)  # "projects"
            
            # Fazer query com o UID do usuário
            query = projects_ref.where("user_uid", "==", user_uid).order_by("created_at", direction="DESCENDING")
            
            # Executar query
            docs = query.get()
            projects = []
            
            for doc in docs:
                project_data = doc.to_dict()
                project_data['id'] = doc.id
                projects.append(project_data)
            
            # Armazenar no cache
            SessionManager.set_cached_projects(user_uid, projects)
            
            return projects
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar projetos: {str(e)}")
            return []

    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """
        Obtém um projeto específico por ID
        
        Args:
            project_id: ID do projeto
            
        Returns:
            Optional[Dict]: Dados do projeto ou None
        """
        try:
            if not self.db:
                return None
            
            doc_ref = self.db.collection(self.collection_name).document(project_id)
            doc = doc_ref.get()
            
            if doc.exists:
                project_data = doc.to_dict()
                project_data['id'] = doc.id
                
                # Enriquecer dados
                enriched_project = self._enrich_project_data(project_data)
                
                logger.info(f"Projeto {project_id} carregado com sucesso")
                return enriched_project
            else:
                logger.warning(f"Projeto {project_id} não encontrado")
                return None
                
        except Exception as e:
            error_msg = f"Erro ao carregar projeto {project_id}: {str(e)}"
            logger.error(error_msg)
            return None
    
    def update_project(self, project_id: str, user_uid: str, updates: Dict) -> bool:
        """
        Atualiza um projeto existente
        
        Args:
            project_id: ID do projeto
            user_uid: ID do usuário (para validação)
            updates: Dados a serem atualizados
            
        Returns:
            bool: Sucesso da operação
        """
        try:
            if not self.db:
                return False
            
            # Validar propriedade do projeto
            project = self.get_project(project_id)
            if not project or project.get('user_uid') != user_uid:
                logger.error(f"Usuário {user_uid} não autorizado a atualizar projeto {project_id}")
                return False
            
            # Preparar updates
            prepared_updates = self._prepare_project_updates(updates)
            prepared_updates['updated_at'] = datetime.utcnow().isoformat()
            
            # Atualizar no banco
            doc_ref = self.db.collection(self.collection_name).document(project_id)
            doc_ref.update(prepared_updates)
            
            # Invalidar cache
            SessionManager.invalidate_projects_cache(user_uid)
            
            # Atualizar estatísticas
            self.session_stats['projects_updated'] += 1
            
            logger.info(f"Projeto {project_id} atualizado com sucesso")
            return True
            
        except Exception as e:
            error_msg = f"Erro ao atualizar projeto {project_id}: {str(e)}"
            logger.error(error_msg)
            return False
    
    def delete_project(self, project_id: str, user_uid: str) -> bool:
        """
        Exclui um projeto
        
        Args:
            project_id: ID do projeto
            user_uid: ID do usuário (para validação)
            
        Returns:
            bool: Sucesso da operação
        """
        try:
            if not self.db:
                return False
            
            # Validar propriedade do projeto
            project = self.get_project(project_id)
            if not project or project.get('user_uid') != user_uid:
                logger.error(f"Usuário {user_uid} não autorizado a excluir projeto {project_id}")
                return False
            
            # Excluir do banco
            doc_ref = self.db.collection(self.collection_name).document(project_id)
            doc_ref.delete()
            
            # Invalidar cache
            SessionManager.invalidate_projects_cache(user_uid)
            
            logger.info(f"Projeto {project_id} excluído com sucesso")
            return True
            
        except Exception as e:
            error_msg = f"Erro ao excluir projeto {project_id}: {str(e)}"
            logger.error(error_msg)
            return False
    
    def calculate_project_progress(self, project: Dict) -> float:
        """
        Calcula progresso geral do projeto de forma otimizada
        
        Args:
            project: Dados do projeto
            
        Returns:
            float: Progresso em porcentagem (0-100)
        """
        try:
            if HAS_NEW_UTILS:
                # Usar configuração centralizada
                total_progress = 0.0
                phases_count = 0
                
                for phase_enum in DMACPhase:
                    phase_key = phase_enum.value
                    phase_data = project.get(phase_key, {})
                    
                    if isinstance(phase_data, dict):
                        phase_progress = calculate_phase_completion_percentage(phase_data, phase_enum)
                        total_progress += phase_progress
                        phases_count += 1
                
                return total_progress / phases_count if phases_count > 0 else 0.0
            else:
                # Fallback para cálculo manual
                phases = ['define', 'measure', 'analyze', 'improve', 'control']
                total_progress = 0.0
                
                for phase in phases:
                    phase_data = project.get(phase, {})
                    if isinstance(phase_data, dict):
                        phase_progress = calculate_phase_completion_percentage(phase_data, phase)
                        total_progress += phase_progress
                
                return total_progress / len(phases)
                
        except Exception as e:
            logger.error(f"Erro ao calcular progresso do projeto: {str(e)}")
            return 0.0
    
    def get_project_metrics(self, project: Dict) -> ProjectMetrics:
        """
        Calcula métricas detalhadas do projeto
        
        Args:
            project: Dados do projeto
            
        Returns:
            ProjectMetrics: Métricas calculadas
        """
        try:
            metrics = ProjectMetrics()
            
            # Progresso geral
            metrics.overall_progress = self.calculate_project_progress(project)
            
            # Economia esperada
            metrics.expected_savings = project.get('expected_savings', 0.0)
            metrics.actual_savings = project.get('actual_savings', 0.0)
            
            # Duração
            start_date = project.get('start_date')
            end_date = project.get('target_end_date')
            
            if start_date and end_date:
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    metrics.duration_days = (end - start).days
                except Exception:
                    pass
            
            # Fases e ferramentas
            completed_phases = 0
            tools_completed = 0
            
            phases = ['define', 'measure', 'analyze', 'improve', 'control']
            for phase in phases:
                phase_data = project.get(phase, {})
                if isinstance(phase_data, dict):
                    # Contar ferramentas concluídas na fase
                    phase_tools_completed = sum(
                        1 for tool_data in phase_data.values()
                        if isinstance(tool_data, dict) and tool_data.get('completed', False)
                    )
                    tools_completed += phase_tools_completed
                    
                    # Verificar se fase está completa
                    if HAS_NEW_UTILS:
                        try:
                            phase_enum = DMACPhase(phase)
                            phase_progress = calculate_phase_completion_percentage(phase_data, phase_enum)
                        except:
                            phase_progress = calculate_phase_completion_percentage(phase_data, phase)
                    else:
                        phase_progress = calculate_phase_completion_percentage(phase_data, phase)
                    
                    if phase_progress == 100:
                        completed_phases += 1
            
            metrics.completed_phases = completed_phases
            metrics.tools_completed = tools_completed
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas do projeto: {str(e)}")
            return ProjectMetrics()
    
    def validate_project(self, project: Dict) -> ProjectValidation:
        """
        Valida um projeto completo
        
        Args:
            project: Dados do projeto
            
        Returns:
            ProjectValidation: Resultado da validação
        """
        validation = ProjectValidation(is_valid=True, errors=[], warnings=[], suggestions=[])
        
        try:
            # Validações básicas
            if not project.get('name', '').strip():
                validation.errors.append("Nome do projeto é obrigatório")
            
            if not project.get('user_uid', '').strip():
                validation.errors.append("Usuário do projeto é obrigatório")
            
            # Validações de negócio
            expected_savings = project.get('expected_savings', 0)
            if expected_savings <= 0:
                validation.warnings.append("Considere definir uma economia esperada")
            
            # Validações de datas
            start_date = project.get('start_date')
            end_date = project.get('target_end_date')
            
            if start_date and end_date:
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    
                    if end <= start:
                        validation.errors.append("Data de término deve ser posterior à data de início")
                    else:
                        duration = (end - start).days
                        if duration > 365:
                            validation.warnings.append("Projeto muito longo (>1 ano)")
                        elif duration < 30:
                            validation.warnings.append("Projeto muito curto (<1 mês)")
                except Exception:
                    validation.errors.append("Formato de data inválido")
            
            # Validações das fases DMAIC
            phases_validation = self._validate_dmaic_phases(project)
            validation.warnings.extend(phases_validation.get('warnings', []))
            validation.suggestions.extend(phases_validation.get('suggestions', []))
            
            # Determinar se é válido
            validation.is_valid = len(validation.errors) == 0
            
        except Exception as e:
            validation.errors.append(f"Erro na validação: {str(e)}")
            validation.is_valid = False
        
        return validation
    
    def get_user_project_statistics(self, user_uid: str) -> Dict[str, Any]:
        """
        Obtém estatísticas dos projetos do usuário
        
        Args:
            user_uid: ID do usuário
            
        Returns:
            Dict: Estatísticas calculadas
        """
        try:
            projects = self.get_user_projects(user_uid)
            
            if not projects:
                return {
                    'total_projects': 0,
                    'active_projects': 0,
                    'completed_projects': 0,
                    'total_expected_savings': 0.0,
                    'average_progress': 0.0,
                    'projects_by_status': {},
                    'average_duration_days': 0
                }
            
            # Calcular estatísticas
            stats = {
                'total_projects': len(projects),
                'active_projects': 0,
                'completed_projects': 0,
                'paused_projects': 0,
                'total_expected_savings': 0.0,
                'total_actual_savings': 0.0,
                'average_progress': 0.0,
                'projects_by_status': {},
                'average_duration_days': 0,
                'total_tools_completed': 0,
                'phases_distribution': {phase: 0 for phase in ['define', 'measure', 'analyze', 'improve', 'control']}
            }
            
            total_progress = 0.0
            total_duration = 0
            duration_count = 0
            
            for project in projects:
                # Status
                status = project.get('status', 'active')
                if status == 'active':
                    stats['active_projects'] += 1
                elif status == 'completed':
                    stats['completed_projects'] += 1
                elif status == 'paused':
                    stats['paused_projects'] += 1
                
                stats['projects_by_status'][status] = stats['projects_by_status'].get(status, 0) + 1
                
                # Economia
                stats['total_expected_savings'] += project.get('expected_savings', 0)
                stats['total_actual_savings'] += project.get('actual_savings', 0)
                
                # Progresso
                project_progress = self.calculate_project_progress(project)
                total_progress += project_progress
                
                # Duração
                start_date = project.get('start_date')
                end_date = project.get('target_end_date')
                
                if start_date and end_date:
                    try:
                        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                        duration = (end - start).days
                        total_duration += duration
                        duration_count += 1
                    except Exception:
                        pass
                
                # Métricas do projeto
                metrics = self.get_project_metrics(project)
                stats['total_tools_completed'] += metrics.tools_completed
                
                # Distribuição por fases (projeto com maior progresso em cada fase)
                for phase in stats['phases_distribution']:
                    phase_data = project.get(phase, {})
                    if isinstance(phase_data, dict) and phase_data:
                        stats['phases_distribution'][phase] += 1
            
            # Calcular médias
            stats['average_progress'] = total_progress / len(projects)
            stats['average_duration_days'] = total_duration / duration_count if duration_count > 0 else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas do usuário: {str(e)}")
            return {}
    
    def export_project_data(self, project_id: str, format_type: str = 'json') -> Optional[str]:
        """
        Exporta dados do projeto
        
        Args:
            project_id: ID do projeto
            format_type: Formato de exportação ('json', 'csv')
            
        Returns:
            Optional[str]: Dados exportados ou None
        """
        try:
            project = self.get_project(project_id)
            if not project:
                return None
            
            if format_type.lower() == 'json':
                return json.dumps(project, indent=2, ensure_ascii=False, default=str)
            elif format_type.lower() == 'csv':
                # Implementar exportação CSV se necessário
                return self._export_project_to_csv(project)
            else:
                logger.error(f"Formato de exportação não suportado: {format_type}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao exportar projeto {project_id}: {str(e)}")
            return None
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da sessão atual
        
        Returns:
            Dict: Estatísticas da sessão
        """
        return {
            **self.session_stats,
            'cache_hit_rate': (
                self.session_stats['cache_hits'] / 
                (self.session_stats['cache_hits'] + self.session_stats['cache_misses'])
                if (self.session_stats['cache_hits'] + self.session_stats['cache_misses']) > 0 
                else 0
            ),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # Métodos privados
    
    def _validate_project_data(self, project_data: Dict) -> ProjectValidation:
        """Valida dados de entrada do projeto"""
        validation = ProjectValidation(is_valid=True, errors=[], warnings=[], suggestions=[])
        
        # Validações obrigatórias
        required_fields = ['name']
        for field in required_fields:
            if not project_data.get(field, '').strip():
                validation.errors.append(f"Campo '{field}' é obrigatório")
        
        # Validações de formato
        name = project_data.get('name', '')
        if name and len(name) < 3:
            validation.errors.append("Nome deve ter pelo menos 3 caracteres")
        elif name and len(name) > 100:
            validation.warnings.append("Nome muito longo (>100 caracteres)")
        
        # Validações de negócio
        expected_savings = project_data.get('expected_savings', 0)
        if expected_savings < 0:
            validation.errors.append("Economia esperada não pode ser negativa")
        elif expected_savings == 0:
            validation.suggestions.append("Considere definir uma economia esperada")
        
        validation.is_valid = len(validation.errors) == 0
        return validation
    
    def _prepare_project_data(self, user_uid: str, project_data: Dict) -> Dict:
        """Prepara dados do projeto para salvamento"""
        current_time = datetime.utcnow().isoformat()
        
        prepared_data = {
            'user_uid': user_uid,
            'name': project_data.get('name', '').strip(),
            'description': project_data.get('description', '').strip(),
            'business_case': project_data.get('business_case', '').strip(),
            'problem_statement': project_data.get('problem_statement', '').strip(),
            'success_criteria': project_data.get('success_criteria', '').strip(),
            'expected_savings': float(project_data.get('expected_savings', 0)),
            'actual_savings': 0.0,
            'start_date': project_data.get('start_date', current_time),
            'target_end_date': project_data.get('target_end_date'),
            'status': ProjectStatus.ACTIVE.value,
            'created_at': current_time,
            'updated_at': current_time,
            'version': '1.0',
            # Inicializar estrutura das fases DMAIC
            'define': {},
            'measure': {},
            'analyze': {},
            'improve': {},
            'control': {}
        }
        
        return prepared_data
    
    def _prepare_project_updates(self, updates: Dict) -> Dict:
        """Prepara dados para atualização"""
        # Filtrar campos permitidos para atualização
        allowed_fields = [
            'name', 'description', 'business_case', 'problem_statement',
            'success_criteria', 'expected_savings', 'actual_savings',
            'target_end_date', 'status', 'define', 'measure', 'analyze',
            'improve', 'control'
        ]
        
        prepared_updates = {}
        for field in allowed_fields:
            if field in updates:
                prepared_updates[field] = updates[field]
        
        return prepared_updates
    
    def _enrich_project_data(self, project: Dict) -> Dict:
        """Enriquece dados do projeto com métricas calculadas"""
        try:
            # Calcular progresso
            project['calculated_progress'] = self.calculate_project_progress(project)
            
            # Adicionar métricas
            metrics = self.get_project_metrics(project)
            project['metrics'] = asdict(metrics)
            
            # Adicionar informações de validação
            validation = self.validate_project(project)
            project['validation'] = {
                'is_valid': validation.is_valid,
                'has_warnings': len(validation.warnings) > 0,
                'warnings_count': len(validation.warnings),
                'suggestions_count': len(validation.suggestions)
            }
            
            return project
            
        except Exception as e:
            logger.error(f"Erro ao enriquecer dados do projeto: {str(e)}")
            return project
    
    def _validate_dmaic_phases(self, project: Dict) -> Dict:
        """Valida fases DMAIC do projeto"""
        warnings = []
        suggestions = []
        
        phases = ['define', 'measure', 'analyze', 'improve', 'control']
        
        for i, phase in enumerate(phases):
            phase_data = project.get(phase, {})
            
            if not isinstance(phase_data, dict):
                continue
            
            # Verificar se fase anterior tem pelo menos algum progresso
            if i > 0:
                previous_phase = phases[i-1]
                previous_data = project.get(previous_phase, {})
                
                if isinstance(previous_data, dict):
                    previous_completed = any(
                        isinstance(tool_data, dict) and tool_data.get('completed', False)
                        for tool_data in previous_data.values()
                    )
                    
                    current_completed = any(
                        isinstance(tool_data, dict) and tool_data.get('completed', False)
                        for tool_data in phase_data.values()
                    )
                    
                    if current_completed and not previous_completed:
                        warnings.append(
                            f"Fase {phase.title()} iniciada sem completar {previous_phase.title()}"
                        )
            
            # Sugestões baseadas no progresso
            if isinstance(phase_data, dict) and phase_data:
                completed_tools = sum(
                    1 for tool_data in phase_data.values()
                    if isinstance(tool_data, dict) and tool_data.get('completed', False)
                )
                
                if completed_tools == 0:
                    suggestions.append(f"Considere iniciar a fase {phase.title()}")
        
        return {'warnings': warnings, 'suggestions': suggestions}
    
    def _export_project_to_csv(self, project: Dict) -> str:
        """Exporta projeto para formato CSV"""
        # Implementação básica - pode ser expandida
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Campo', 'Valor'])
        
        # Dados básicos
        basic_fields = ['name', 'description', 'status', 'expected_savings', 'created_at']
        for field in basic_fields:
            writer.writerow([field, project.get(field, '')])
        
        # Progresso
        writer.writerow(['calculated_progress', project.get('calculated_progress', 0)])
        
        return output.getvalue()

# Cache da instância para evitar recriações
@st.cache_resource
def get_project_manager() -> ProjectManager:
    """Retorna instância cached do ProjectManager"""
    return ProjectManager()

# Função de conveniência
def create_project_manager() -> ProjectManager:
    """Cria nova instância do ProjectManager"""
    return ProjectManager()

# Função principal para compatibilidade
def main():
    """Função principal para teste standalone"""
    st.title("🔧 Project Manager Test")
    
    # Criar instância
    pm = get_project_manager()
    
    # Mostrar estatísticas da sessão
    st.json(pm.get_session_statistics())
    
    # Teste básico (se autenticado)
    user_data = SessionManager.get_user_data()
    if user_data and user_data.get('uid'):
        projects = pm.get_user_projects(user_data['uid'])
        st.write(f"Projetos encontrados: {len(projects)}")
        
        if projects:
            stats = pm.get_user_project_statistics(user_data['uid'])
            st.json(stats)

if __name__ == "__main__":
    main()
