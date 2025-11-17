import streamlit as st
import time
import uuid
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from config.firebase_config import initialize_firebase

class ProjectManager:
    def __init__(self):
        self.db = initialize_firebase()
        if not self.db:
            st.warning("⚠️ Firestore não inicializado. Algumas funcionalidades podem estar limitadas.")
        
        # Obter UID do usuário atual
        self.user_uid = self._get_current_user_uid()
    
    def _get_current_user_uid(self) -> Optional[str]:
        """Obtém UID do usuário atual"""
        if 'user_data' in st.session_state:
            return st.session_state.user_data.get('uid')
        return None
    
    def _ensure_user_authenticated(self) -> bool:
        """Verifica se usuário está autenticado"""
        if not self.user_uid:
            st.error("❌ Usuário não autenticado")
            return False
        
        if not self.db:
            st.error("❌ Conexão com Firebase não disponível")
            return False
        
        return True
    
    def _convert_numpy_types(self, obj):
        """Converte tipos numpy para tipos nativos Python compatíveis com Firestore"""
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif pd.isna(obj):
            return None
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        else:
            return obj
    
    def _prepare_dataframe_for_firestore(self, df: pd.DataFrame) -> Dict:
        """Prepara DataFrame para salvar no Firestore convertendo tipos problemáticos"""
        try:
            # Criar uma cópia do DataFrame
            df_clean = df.copy()
            
            # Converter tipos numpy para tipos nativos Python
            for col in df_clean.columns:
                if df_clean[col].dtype == 'object':
                    # Para colunas de objeto, converter valores individuais
                    df_clean[col] = df_clean[col].apply(lambda x: self._convert_numpy_types(x))
                elif pd.api.types.is_integer_dtype(df_clean[col]):
                    # Converter inteiros numpy para int nativo
                    df_clean[col] = df_clean[col].astype('Int64')  # Nullable integer
                elif pd.api.types.is_float_dtype(df_clean[col]):
                    # Converter floats numpy para float nativo
                    df_clean[col] = df_clean[col].astype('float64')
                elif pd.api.types.is_bool_dtype(df_clean[col]):
                    # Converter boolean numpy para bool nativo
                    df_clean[col] = df_clean[col].astype('boolean')  # Nullable boolean
            
            # Substituir NaN por None (compatível com Firestore)
            df_clean = df_clean.where(pd.notnull(df_clean), None)
            
            # Converter para JSON usando orient='records'
            records = df_clean.to_dict('records')
            
            # Aplicar conversão adicional nos records
            clean_records = []
            for record in records:
                clean_record = self._convert_numpy_types(record)
                clean_records.append(clean_record)
            
            return {
                'records': clean_records,
                'columns': list(df.columns),
                'index': df.index.tolist()
            }
            
        except Exception as e:
            st.error(f"Erro ao preparar DataFrame: {str(e)}")
            raise e
    
    def _restore_dataframe_from_firestore(self, data: Dict) -> pd.DataFrame:
        """Restaura DataFrame a partir dos dados salvos no Firestore"""
        try:
            if 'records' in data:
                # Novo formato
                df = pd.DataFrame(data['records'])
                if 'columns' in data:
                    # Garantir ordem das colunas
                    df = df.reindex(columns=data['columns'])
                return df
            else:
                # Formato antigo (JSON string)
                return pd.read_json(data, orient='records')
                
        except Exception as e:
            st.error(f"Erro ao restaurar DataFrame: {str(e)}")
            return pd.DataFrame()
    
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
            
            # Converter valores numéricos para tipos nativos
            expected_savings = project_data.get('expected_savings', 0)
            if isinstance(expected_savings, (np.number, np.integer, np.floating)):
                expected_savings = float(expected_savings)
            
            # Estrutura padrão do projeto
            new_project = {
                'id': project_id,
                'user_uid': user_uid,
                'name': str(project_data['name']),
                'description': str(project_data.get('description', '')),
                'business_case': str(project_data.get('business_case', '')),
                'expected_savings': expected_savings,
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
                    'file_upload': {'completed': False, 'data': {}},
                    'uploaded_files': []
                },
                'analyze': {
                    'statistical_analysis': {'completed': False, 'data': {}},
                    'root_cause_analysis': {'completed': False, 'data': {}},
                    'hypothesis_testing': {'completed': False, 'data': {}},
                    'process_analysis': {'completed': False, 'data': {}},
                    'ishikawa': {'completed': False, 'data': {}},
                    'five_whys': {'completed': False, 'data': {}},
                    'pareto': {'completed': False, 'data': {}},
                    'hypothesis_tests': {'completed': False, 'data': {}},
                    'root_cause': {'completed': False, 'data': {}}
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
            
            # Converter toda a estrutura para tipos compatíveis com Firestore
            new_project = self._convert_numpy_types(new_project)
            
            # Salvar no Firestore
            self.db.collection('projects').document(project_id).set(new_project)
            
            # Atualizar lista de projetos do usuário
            try:
                user_ref = self.db.collection('users').document(user_uid)
                user_doc = user_ref.get()
                
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    projects = user_data.get('projects', [])
                    if project_id not in projects:
                        projects.append(project_id)
                        user_ref.update({'projects': projects})
                else:
                    user_ref.set({
                        'projects': [project_id],
                        'updated_at': datetime.now().isoformat()
                    }, merge=True)
                    
            except Exception as user_update_error:
                st.warning(f"⚠️ Projeto criado, mas erro ao atualizar usuário: {str(user_update_error)}")
            
            # Atualizar session state
            new_project['id'] = project_id
            st.session_state.current_project = new_project
            
            return True, project_id
            
        except Exception as e:
            error_msg = str(e)
            
            # Análise específica de erros
            if "permission" in error_msg.lower():
                return False, "Erro de permissão no Firebase. Verifique as regras de segurança."
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                return False, "Erro de conexão. Verifique sua internet."
            elif "quota" in error_msg.lower():
                return False, "Quota do Firebase excedida. Tente novamente mais tarde."
            elif "convert" in error_msg.lower() and "firestore" in error_msg.lower():
                return False, "Erro de conversão de dados. Verifique os tipos de dados fornecidos."
            else:
                return False, f"Erro interno: {error_msg}"
    
    def get_user_projects(self, user_uid: str) -> List[Dict]:
        """Obtém todos os projetos do usuário"""
        try:
            if not self.db:
                return []
            
            if not user_uid:
                return []
            
            projects = []
            projects_query = self.db.collection('projects').where('user_uid', '==', user_uid).stream()
            
            for doc in projects_query:
                project_data = doc.to_dict()
                if project_data:
                    projects.append(project_data)
            
            # Ordenar por data de criação (mais recente primeiro)
            projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return projects
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar projetos: {str(e)}")
            return []
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Obtém um projeto específico com sincronização completa"""
        try:
            if not self.db or not project_id:
                return None
            
            doc = self.db.collection('projects').document(project_id).get()
            
            if not doc.exists:
                st.error("❌ Projeto não encontrado")
                return None
            
            project_data = doc.to_dict()
            project_data['id'] = doc.id
            
            # Verificar se pertence ao usuário atual
            if self.user_uid and project_data.get('user_uid') != self.user_uid:
                st.error("❌ Acesso negado ao projeto")
                return None
            
            # Atualizar session state para garantir sincronização
            st.session_state.current_project = project_data
            
            # Sincronizar dados de upload se existirem
            self._sync_uploaded_data(project_id, project_data)
            
            return project_data
            
        except Exception as e:
            st.error(f"Erro ao carregar projeto: {str(e)}")
            return None
    
    def update_project(self, project_id: str, updates: Dict) -> bool:
        """Atualiza dados do projeto com sincronização melhorada"""
        try:
            if not self.db or not project_id:
                return False
            
            # Converter tipos numpy antes de salvar
            updates = self._convert_numpy_types(updates)
            
            # Adicionar timestamp de atualização
            updates['updated_at'] = datetime.now().isoformat()
            
            # Atualizar no Firestore
            self.db.collection('projects').document(project_id).update(updates)
            
            # Atualizar session state se for o projeto atual
            if ('current_project' in st.session_state and 
                st.session_state.current_project.get('id') == project_id):
                
                # Fazer merge das atualizações
                current_project = st.session_state.current_project.copy()
                
                # Merge recursivo para estruturas aninhadas
                def deep_merge(dict1, dict2):
                    for key, value in dict2.items():
                        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                            deep_merge(dict1[key], value)
                        else:
                            dict1[key] = value
                
                deep_merge(current_project, updates)
                st.session_state.current_project = current_project
            
            return True
            
        except Exception as e:
            st.error(f"Erro ao atualizar projeto: {str(e)}")
            return False
    
    def delete_project(self, project_id: str, user_uid: str) -> bool:
        """Deleta um projeto"""
        try:
            if not self.db or not project_id:
                return False
            
            # Verificar se pertence ao usuário
            project = self.get_project(project_id)
            if not project:
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
            
            # Limpar session state se for o projeto atual
            if ('current_project' in st.session_state and 
                st.session_state.current_project.get('id') == project_id):
                del st.session_state.current_project
                
                # Limpar dados relacionados ao projeto
                keys_to_remove = [k for k in st.session_state.keys() if project_id in str(k)]
                for key in keys_to_remove:
                    del st.session_state[key]
            
            return True
            
        except Exception as e:
            st.error(f"Erro ao deletar projeto: {str(e)}")
            return False
    
    def save_uploaded_data(self, project_id: str, dataframe: pd.DataFrame, filename: str, 
                          additional_info: Dict = None) -> bool:
        """Salva dados de upload no projeto com tratamento robusto de tipos"""
        if not self._ensure_user_authenticated():
            return False
        
        try:
            # Preparar DataFrame para Firestore
            df_data = self._prepare_dataframe_for_firestore(dataframe)
            
            # Preparar informações sobre o dataset com conversão de tipos
            dataset_info = {
                'filename': str(filename),
                'columns': [str(col) for col in dataframe.columns],
                'shape': [int(dataframe.shape[0]), int(dataframe.shape[1])],
                'dtypes': {str(col): str(dtype) for col, dtype in dataframe.dtypes.items()},
                'uploaded_at': datetime.now().isoformat(),
                'data_summary': {
                    'total_rows': int(len(dataframe)),
                    'total_columns': int(len(dataframe.columns)),
                    'numeric_columns': int(len(dataframe.select_dtypes(include=['number']).columns)),
                    'categorical_columns': int(len(dataframe.select_dtypes(include=['object']).columns)),
                    'missing_values': int(dataframe.isnull().sum().sum()),
                    'memory_usage': int(dataframe.memory_usage(deep=True).sum())
                }
            }
            
            # Adicionar informações extras se fornecidas
            if additional_info:
                additional_info = self._convert_numpy_types(additional_info)
                dataset_info.update(additional_info)
            
            # Verificar tamanho dos dados
            data_json = json.dumps(df_data)
            data_size = len(data_json.encode('utf-8'))
            
            # Preparar dados para salvar
            if data_size > 800000:  # 800KB como limite de segurança
                st.warning("⚠️ Dataset muito grande. Salvando apenas metadados.")
                upload_data = {
                    'dataframe_data': None,
                    'dataset_info': dataset_info,
                    'size_warning': f"Dataset muito grande ({data_size / 1024:.1f}KB). Dados mantidos apenas em memória."
                }
            else:
                upload_data = {
                    'dataframe_data': df_data,
                    'dataset_info': dataset_info
                }
            
            # Converter todos os dados para tipos compatíveis
            upload_data = self._convert_numpy_types(upload_data)
            
            # Atualizar no Firestore
            update_data = {
                'measure.file_upload.data': upload_data,
                'measure.file_upload.completed': True,
                'measure.file_upload.updated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            success = self.update_project(project_id, update_data)
            
            if success:
                # Salvar no session state também
                st.session_state[f'uploaded_data_{project_id}'] = dataframe
                st.session_state[f'upload_info_{project_id}'] = dataset_info
                st.success("✅ Dados salvos com sucesso!")
            
            return success
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar dados de upload: {str(e)}")
            return False
    
    def get_uploaded_data(self, project_id: str) -> Optional[pd.DataFrame]:
        """Recupera dados de upload com fallback para Firebase"""
        # Primeiro tentar session state
        session_key = f'uploaded_data_{project_id}'
        if session_key in st.session_state:
            return st.session_state[session_key]
        
        # Se não estiver no session state, tentar carregar do Firebase
        project = self.get_project(project_id)
        if project:
            measure_data = project.get('measure', {})
            file_upload_data = measure_data.get('file_upload', {}).get('data', {})
            
            if file_upload_data.get('dataframe_data'):
                try:
                    df = self._restore_dataframe_from_firestore(file_upload_data['dataframe_data'])
                    # Salvar no session state para próximas consultas
                    st.session_state[session_key] = df
                    
                    # Salvar info também
                    if file_upload_data.get('dataset_info'):
                        st.session_state[f'upload_info_{project_id}'] = file_upload_data['dataset_info']
                    
                    return df
                except Exception as e:
                    st.error(f"❌ Erro ao carregar dados do Firebase: {str(e)}")
            elif file_upload_data.get('size_warning'):
                st.warning(file_upload_data['size_warning'])
        
        return None
    
    def get_upload_info(self, project_id: str) -> Optional[Dict]:
        """Recupera informações sobre o upload"""
        # Tentar session state primeiro
        info_key = f'upload_info_{project_id}'
        if info_key in st.session_state:
            return st.session_state[info_key]
        
        # Tentar Firebase
        project = self.get_project(project_id)
        if project:
            measure_data = project.get('measure', {})
            file_upload_data = measure_data.get('file_upload', {}).get('data', {})
            dataset_info = file_upload_data.get('dataset_info')
            
            if dataset_info:
                st.session_state[info_key] = dataset_info
                return dataset_info
        
        return None
    
    def _sync_uploaded_data(self, project_id: str, project_data: Dict):
        """Sincroniza dados de upload salvos no projeto"""
        try:
            # Verificar se há dados de upload salvos no projeto
            measure_data = project_data.get('measure', {})
            
            # Sincronizar file_upload
            file_upload_data = measure_data.get('file_upload', {}).get('data', {})
            if file_upload_data.get('dataframe_data'):
                try:
                    df = self._restore_dataframe_from_firestore(file_upload_data['dataframe_data'])
                    st.session_state[f'uploaded_data_{project_id}'] = df
                    
                    # Sincronizar informações do dataset
                    if file_upload_data.get('dataset_info'):
                        st.session_state[f'upload_info_{project_id}'] = file_upload_data['dataset_info']
                
                except Exception as e:
                    st.warning(f"⚠️ Erro ao sincronizar dados de upload: {str(e)}")
            
            # Sincronizar baseline_data
            baseline_data = measure_data.get('baseline_data', {}).get('data', {})
            if baseline_data.get('baseline_metrics'):
                st.session_state[f'baseline_data_{project_id}'] = baseline_data
            
            # Sincronizar dados de outras ferramentas
            for phase in ['define', 'measure', 'analyze', 'improve', 'control']:
                phase_data = project_data.get(phase, {})
                for tool_name, tool_data in phase_data.items():
                    if isinstance(tool_data, dict) and tool_data.get('data'):
                        session_key = f"{tool_name}_{project_id}"
                        st.session_state[session_key] = tool_data['data']
        
        except Exception as e:
            st.warning(f"⚠️ Erro na sincronização de dados: {str(e)}")
    
    def ensure_project_sync(self, project_id: str) -> bool:
        """Força sincronização completa do projeto"""
        try:
            project = self.get_project(project_id)
            if project:
                st.session_state.current_project = project
                self._sync_uploaded_data(project_id, project)
                return True
            return False
        except Exception as e:
            st.error(f"❌ Erro na sincronização: {str(e)}")
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
    
    def get_project_statistics(self, project_data: Dict) -> Dict:
        """Obtém estatísticas detalhadas do projeto"""
        stats = {
            'total_phases': 5,
            'completed_phases': 0,
            'total_tools': 0,
            'completed_tools': 0,
            'phase_progress': {},
            'has_uploaded_data': False,
            'data_info': None
        }
        
        phases = ['define', 'measure', 'analyze', 'improve', 'control']
        
        for phase in phases:
            phase_data = project_data.get(phase, {})
            phase_total = 0
            phase_completed = 0
            
            for key, value in phase_data.items():
                if isinstance(value, dict) and 'completed' in value:
                    phase_total += 1
                    stats['total_tools'] += 1
                    
                    if value['completed']:
                        phase_completed += 1
                        stats['completed_tools'] += 1
            
            phase_progress = (phase_completed / phase_total * 100) if phase_total > 0 else 0
            stats['phase_progress'][phase] = {
                'completed': phase_completed,
                'total': phase_total,
                'progress': phase_progress
            }
            
            if phase_progress == 100:
                stats['completed_phases'] += 1
        
        # Verificar dados carregados
        project_id = project_data.get('id')
        if project_id:
            upload_info = self.get_upload_info(project_id)
            if upload_info:
                stats['has_uploaded_data'] = True
                stats['data_info'] = upload_info
        
        return stats


# Classe auxiliar para gerenciamento de sincronização
class DataSyncManager:
    """Gerenciador de sincronização de dados entre fases"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.project_manager = ProjectManager()
    
    def ensure_data_available(self, show_warnings: bool = True) -> bool:
        """Garante que os dados estejam disponíveis"""
        # Verificar se há dados no session state
        if f'uploaded_data_{self.project_id}' in st.session_state:
            return True
        
        # Tentar carregar do Firebase
        df = self.project_manager.get_uploaded_data(self.project_id)
        if df is not None:
            if show_warnings:
                st.success("✅ Dados sincronizados com sucesso!")
            return True
        
        # Dados não encontrados
        if show_warnings:
            self._show_no_data_warning()
        return False
    
    def get_project_data(self, force_refresh: bool = False) -> Optional[Dict]:
        """Obtém dados do projeto com opção de forçar atualização"""
        if force_refresh or 'current_project' not in st.session_state:
            return self.project_manager.get_project(self.project_id)
        
        return st.session_state.get('current_project')
    
    def get_uploaded_dataframe(self) -> Optional[pd.DataFrame]:
        """Obtém DataFrame com dados carregados"""
        return self.project_manager.get_uploaded_data(self.project_id)
    
    def _show_no_data_warning(self):
        """Mostra aviso quando dados não estão disponíveis"""
        st.warning("⚠️ **Dados não encontrados**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Ir para Measure", key=f"goto_measure_{self.project_id}"):
                st.session_state['navigate_to'] = 'measure'
                st.rerun()
        
        with col2:
            if st.button("🔄 Sincronizar Dados", key=f"sync_data_{self.project_id}"):
                with st.spinner("Sincronizando..."):
                    success = self.project_manager.ensure_project_sync(self.project_id)
                    if success:
                        st.success("✅ Dados sincronizados!")
                        st.rerun()
                    else:
                        st.error("❌ Erro na sincronização")
        
        with col3:
            if st.button("🏠 Voltar ao Projeto", key=f"back_project_{self.project_id}"):
                if 'navigate_to' in st.session_state:
                    del st.session_state['navigate_to']
                st.rerun()
        
        st.info("💡 **Dica:** Certifique-se de que você fez upload dos dados na fase **Measure** → **Upload de Dados**")
    
    def show_data_status(self):
        """Mostra status dos dados do projeto"""
        with st.expander("📊 Status dos Dados do Projeto"):
            project_data = self.get_project_data()
            
            if not project_data:
                st.error("❌ Projeto não carregado")
                return
            
            # Status do upload
            file_upload_completed = project_data.get('measure', {}).get('file_upload', {}).get('completed', False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if file_upload_completed:
                    st.success("✅ Dados carregados")
                    
                    # Informações sobre os dados
                    upload_info = self.project_manager.get_upload_info(self.project_id)
                    if upload_info:
                        st.write(f"**Arquivo:** {upload_info.get('filename', 'N/A')}")
                        shape = upload_info.get('shape', [0, 0])
                        st.write(f"**Dimensões:** {shape[0]} linhas × {shape[1]} colunas")
                        st.write(f"**Upload:** {upload_info.get('uploaded_at', 'N/A')[:10]}")
                else:
                    st.error("❌ Dados não carregados")
            
            with col2:
                # Status do session state
                session_key = f'uploaded_data_{self.project_id}'
                if session_key in st.session_state:
                    df = st.session_state[session_key]
                    st.success(f"✅ Dados em memória: {len(df)} × {len(df.columns)}")
                else:
                    st.warning("⚠️ Dados não estão em memória")
            
            # Botões de ação
            col3, col4 = st.columns(2)
            
            with col3:
                if st.button("🔄 Recarregar Dados", key=f"reload_data_{self.project_id}"):
                    self.project_manager.ensure_project_sync(self.project_id)
                    st.rerun()
            
            with col4:
                if st.button("🧹 Limpar Cache", key=f"clear_cache_{self.project_id}"):
                    keys_to_remove = [k for k in st.session_state.keys() if self.project_id in str(k)]
                    for key in keys_to_remove:
                        if key != 'current_project':  # Manter projeto atual
                            del st.session_state[key]
                    st.info("Cache limpo!")
