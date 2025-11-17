"""
Sistema de armazenamento offline para dados do projeto
Versão melhorada com cache inteligente, validação e recuperação automática
"""

import streamlit as st
import json
import pickle
import hashlib
import time
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import os
import tempfile
from pathlib import Path

# Tentar importar utilitários melhorados
try:
    from src.utils.session_manager import SessionManager
    from src.config.dmaic_config import DMAIC_PHASES_CONFIG, DMACPhase
    HAS_NEW_UTILS = True
except ImportError:
    # Fallback para compatibilidade
    class SessionManager:
        @staticmethod
        def get_user_data():
            return st.session_state.get('user_data', {})
        
        @staticmethod
        def get_current_project():
            return st.session_state.get('current_project')
        
        @staticmethod
        def generate_unique_key(base_key, suffix=None):
            timestamp = str(int(time.time() * 1000))[-6:]
            return f"{base_key}_{suffix}_{timestamp}" if suffix else f"{base_key}_{timestamp}"
    
    HAS_NEW_UTILS = False

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageType(Enum):
    """Tipos de armazenamento disponíveis"""
    SESSION_STATE = "session_state"
    LOCAL_STORAGE = "local_storage"
    TEMPORARY_FILE = "temporary_file"
    BROWSER_CACHE = "browser_cache"

class DataType(Enum):
    """Tipos de dados armazenáveis"""
    PROJECT_DATA = "project_data"
    ANALYSIS_RESULTS = "analysis_results"
    UPLOADED_FILES = "uploaded_files"
    USER_PREFERENCES = "user_preferences"
    CACHE_DATA = "cache_data"
    FORM_DATA = "form_data"

@dataclass
class StorageItem:
    """Item de armazenamento com metadados"""
    key: str
    data: Any
    data_type: DataType
    storage_type: StorageType
    created_at: datetime
    expires_at: Optional[datetime] = None
    size_bytes: int = 0
    version: str = "1.0"
    checksum: str = ""

@dataclass
class StorageStats:
    """Estatísticas do sistema de armazenamento"""
    total_items: int = 0
    total_size_bytes: int = 0
    items_by_type: Dict[str, int] = None
    items_by_storage: Dict[str, int] = None
    expired_items: int = 0
    cache_hit_rate: float = 0.0
    operations_count: Dict[str, int] = None
    
    def __post_init__(self):
        if self.items_by_type is None:
            self.items_by_type = {}
        if self.items_by_storage is None:
            self.items_by_storage = {}
        if self.operations_count is None:
            self.operations_count = {'read': 0, 'write': 0, 'delete': 0}

class OfflineStorage:
    """Sistema de armazenamento offline melhorado"""
    
    def __init__(self, max_size_mb: int = 50, default_ttl_minutes: int = 60):
        """
        Inicializa o sistema de armazenamento
        
        Args:
            max_size_mb: Tamanho máximo em MB
            default_ttl_minutes: TTL padrão em minutos
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        
        # Prefixos para diferentes tipos de dados
        self.prefixes = {
            DataType.PROJECT_DATA: "project_",
            DataType.ANALYSIS_RESULTS: "analysis_",
            DataType.UPLOADED_FILES: "upload_",
            DataType.USER_PREFERENCES: "pref_",
            DataType.CACHE_DATA: "cache_",
            DataType.FORM_DATA: "form_"
        }
        
        # Estatísticas
        self.stats = StorageStats()
        self._operations = {'read': 0, 'write': 0, 'delete': 0, 'hit': 0, 'miss': 0}
        
        # Inicialização
        self._initialize_storage()
        
        logger.info(f"OfflineStorage inicializado - Max: {max_size_mb}MB, TTL: {default_ttl_minutes}min")
    
    def _initialize_storage(self):
        """Inicializa o sistema de armazenamento"""
        try:
            # Limpar itens expirados na inicialização
            self._cleanup_expired_items()
            
            # Calcular estatísticas iniciais
            self._update_statistics()
            
        except Exception as e:
            logger.error(f"Erro na inicialização do storage: {str(e)}")
    
    def store_data(
        self, 
        key: str, 
        data: Any, 
        data_type: DataType = DataType.CACHE_DATA,
        storage_type: StorageType = StorageType.SESSION_STATE,
        ttl_minutes: Optional[int] = None,
        compress: bool = True
    ) -> bool:
        """
        Armazena dados com configurações avançadas
        
        Args:
            key: Chave única para os dados
            data: Dados a serem armazenados
            data_type: Tipo dos dados
            storage_type: Tipo de armazenamento
            ttl_minutes: TTL em minutos (None = usar padrão)
            compress: Se deve comprimir os dados
            
        Returns:
            bool: Sucesso da operação
        """
        try:
            # Validar entrada
            if not key or data is None:
                logger.warning("Chave ou dados inválidos para armazenamento")
                return False
            
            # Preparar chave com prefixo
            full_key = self._build_key(key, data_type)
            
            # Serializar dados
            serialized_data = self._serialize_data(data, compress)
            if serialized_data is None:
                return False
            
            # Calcular TTL
            ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self.default_ttl
            expires_at = datetime.utcnow() + ttl
            
            # Criar item de armazenamento
            storage_item = StorageItem(
                key=full_key,
                data=serialized_data,
                data_type=data_type,
                storage_type=storage_type,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                size_bytes=len(str(serialized_data)),
                checksum=self._calculate_checksum(serialized_data)
            )
            
            # Verificar limite de tamanho
            if not self._check_size_limit(storage_item.size_bytes):
                logger.warning(f"Limite de tamanho excedido para item {full_key}")
                return False
            
            # Armazenar baseado no tipo
            success = self._store_by_type(storage_item, storage_type)
            
            if success:
                self._operations['write'] += 1
                logger.debug(f"Dados armazenados: {full_key} ({storage_item.size_bytes} bytes)")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao armazenar dados '{key}': {str(e)}")
            return False
    
    def retrieve_data(
        self, 
        key: str, 
        data_type: DataType = DataType.CACHE_DATA,
        storage_type: StorageType = StorageType.SESSION_STATE,
        decompress: bool = True
    ) -> Optional[Any]:
        """
        Recupera dados armazenados
        
        Args:
            key: Chave dos dados
            data_type: Tipo dos dados
            storage_type: Tipo de armazenamento
            decompress: Se deve descomprimir os dados
            
        Returns:
            Optional[Any]: Dados recuperados ou None
        """
        try:
            # Preparar chave
            full_key = self._build_key(key, data_type)
            
            # Recuperar baseado no tipo
            storage_item = self._retrieve_by_type(full_key, storage_type)
            
            if storage_item is None:
                self._operations['miss'] += 1
                return None
            
            # Verificar expiração
            if self._is_expired(storage_item):
                logger.debug(f"Item expirado removido: {full_key}")
                self.delete_data(key, data_type, storage_type)
                self._operations['miss'] += 1
                return None
            
            # Deserializar dados
            data = self._deserialize_data(storage_item.data, decompress)
            
            if data is not None:
                self._operations['read'] += 1
                self._operations['hit'] += 1
                logger.debug(f"Dados recuperados: {full_key}")
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao recuperar dados '{key}': {str(e)}")
            self._operations['miss'] += 1
            return None
    
    def delete_data(
        self, 
        key: str, 
        data_type: DataType = DataType.CACHE_DATA,
        storage_type: StorageType = StorageType.SESSION_STATE
    ) -> bool:
        """
        Remove dados armazenados
        
        Args:
            key: Chave dos dados
            data_type: Tipo dos dados
            storage_type: Tipo de armazenamento
            
        Returns:
            bool: Sucesso da operação
        """
        try:
            full_key = self._build_key(key, data_type)
            success = self._delete_by_type(full_key, storage_type)
            
            if success:
                self._operations['delete'] += 1
                logger.debug(f"Dados removidos: {full_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao remover dados '{key}': {str(e)}")
            return False
    
    def exists(
        self, 
        key: str, 
        data_type: DataType = DataType.CACHE_DATA,
        storage_type: StorageType = StorageType.SESSION_STATE
    ) -> bool:
        """
        Verifica se dados existem
        
        Args:
            key: Chave dos dados
            data_type: Tipo dos dados
            storage_type: Tipo de armazenamento
            
        Returns:
            bool: Se os dados existem
        """
        try:
            full_key = self._build_key(key, data_type)
            return self._exists_by_type(full_key, storage_type)
        except Exception as e:
            logger.error(f"Erro ao verificar existência de '{key}': {str(e)}")
            return False
    
    def list_keys(
        self, 
        data_type: Optional[DataType] = None,
        storage_type: Optional[StorageType] = None,
        include_expired: bool = False
    ) -> List[str]:
        """
        Lista chaves armazenadas
        
        Args:
            data_type: Filtrar por tipo de dados
            storage_type: Filtrar por tipo de armazenamento
            include_expired: Incluir itens expirados
            
        Returns:
            List[str]: Lista de chaves
        """
        try:
            all_keys = []
            
            # Listar chaves do session_state
            if storage_type is None or storage_type == StorageType.SESSION_STATE:
                session_keys = self._list_session_keys(data_type, include_expired)
                all_keys.extend(session_keys)
            
            # Remover prefixos das chaves
            clean_keys = []
            for key in all_keys:
                if data_type:
                    prefix = self.prefixes.get(data_type, "")
                    if key.startswith(prefix):
                        clean_keys.append(key[len(prefix):])
                else:
                    # Remover qualquer prefixo conhecido
                    clean_key = key
                    for prefix in self.prefixes.values():
                        if key.startswith(prefix):
                            clean_key = key[len(prefix):]
                            break
                    clean_keys.append(clean_key)
            
            return clean_keys
            
        except Exception as e:
            logger.error(f"Erro ao listar chaves: {str(e)}")
            return []
    
    def clear_storage(
        self, 
        data_type: Optional[DataType] = None,
        storage_type: Optional[StorageType] = None,
        confirm: bool = False
    ) -> int:
        """
        Limpa armazenamento
        
        Args:
            data_type: Limpar apenas tipo específico
            storage_type: Limpar apenas armazenamento específico
            confirm: Confirmação de segurança
            
        Returns:
            int: Número de itens removidos
        """
        if not confirm:
            logger.warning("Limpeza de storage requer confirmação")
            return 0
        
        try:
            removed_count = 0
            
            # Obter chaves para remover
            keys_to_remove = self.list_keys(data_type, storage_type, include_expired=True)
            
            # Remover cada chave
            for key in keys_to_remove:
                if self.delete_data(key, data_type or DataType.CACHE_DATA, storage_type or StorageType.SESSION_STATE):
                    removed_count += 1
            
            logger.info(f"Storage limpo: {removed_count} itens removidos")
            return removed_count
            
        except Exception as e:
            logger.error(f"Erro ao limpar storage: {str(e)}")
            return 0
    
    def cleanup_expired(self) -> int:
        """
        Remove itens expirados
        
        Returns:
            int: Número de itens removidos
        """
        return self._cleanup_expired_items()
    
    def get_statistics(self) -> StorageStats:
        """
        Obtém estatísticas do armazenamento
        
        Returns:
            StorageStats: Estatísticas atualizadas
        """
        self._update_statistics()
        return self.stats
    
    def optimize_storage(self) -> Dict[str, int]:
        """
        Otimiza o armazenamento
        
        Returns:
            Dict[str, int]: Resultado da otimização
        """
        try:
            results = {
                'expired_removed': 0,
                'duplicates_removed': 0,
                'size_reduced_bytes': 0
            }
            
            # Remover expirados
            results['expired_removed'] = self._cleanup_expired_items()
            
            # Remover duplicatas (baseado em checksum)
            results['duplicates_removed'] = self._remove_duplicates()
            
            # Compactar dados grandes
            results['size_reduced_bytes'] = self._compress_large_items()
            
            logger.info(f"Storage otimizado: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Erro na otimização do storage: {str(e)}")
            return {}
    
    def export_data(self, format_type: str = 'json') -> Optional[str]:
        """
        Exporta todos os dados
        
        Args:
            format_type: Formato de exportação
            
        Returns:
            Optional[str]: Dados exportados
        """
        try:
            export_data = {}
            
            # Coletar todos os dados
            for data_type in DataType:
                keys = self.list_keys(data_type)
                type_data = {}
                
                for key in keys:
                    data = self.retrieve_data(key, data_type)
                    if data is not None:
                        type_data[key] = data
                
                if type_data:
                    export_data[data_type.value] = type_data
            
            # Adicionar metadados
            export_data['_metadata'] = {
                'exported_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'statistics': asdict(self.get_statistics())
            }
            
            # Serializar baseado no formato
            if format_type.lower() == 'json':
                return json.dumps(export_data, indent=2, default=str, ensure_ascii=False)
            else:
                logger.error(f"Formato de exportação não suportado: {format_type}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {str(e)}")
            return None
    
    def import_data(self, data_str: str, format_type: str = 'json', overwrite: bool = False) -> bool:
        """
        Importa dados
        
        Args:
            data_str: String com dados
            format_type: Formato dos dados
            overwrite: Se deve sobrescrever dados existentes
            
        Returns:
            bool: Sucesso da operação
        """
        try:
            # Deserializar dados
            if format_type.lower() == 'json':
                import_data = json.loads(data_str)
            else:
                logger.error(f"Formato de importação não suportado: {format_type}")
                return False
            
            # Validar estrutura
            if '_metadata' not in import_data:
                logger.warning("Dados de importação sem metadados")
            
            imported_count = 0
            
            # Importar cada tipo de dados
            for type_name, type_data in import_data.items():
                if type_name.startswith('_'):
                    continue  # Pular metadados
                
                try:
                    data_type = DataType(type_name)
                except ValueError:
                    logger.warning(f"Tipo de dados desconhecido ignorado: {type_name}")
                    continue
                
                # Importar itens do tipo
                for key, data in type_data.items():
                    if not overwrite and self.exists(key, data_type):
                        continue  # Pular se já existe e não deve sobrescrever
                    
                    if self.store_data(key, data, data_type):
                        imported_count += 1
            
            logger.info(f"Dados importados: {imported_count} itens")
            return imported_count > 0
            
        except Exception as e:
            logger.error(f"Erro ao importar dados: {str(e)}")
            return False
    
    # Métodos privados
    
    def _build_key(self, key: str, data_type: DataType) -> str:
        """Constrói chave completa com prefixo"""
        prefix = self.prefixes.get(data_type, "")
        return f"{prefix}{key}"
    
    def _serialize_data(self, data: Any, compress: bool = True) -> Optional[str]:
        """Serializa dados para armazenamento"""
        try:
            if compress and isinstance(data, (dict, list)):
                # Usar JSON compacto para estruturas
                return json.dumps(data, separators=(',', ':'), default=str, ensure_ascii=False)
            else:
                # Usar JSON normal
                return json.dumps(data, default=str, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro na serialização: {str(e)}")
            return None
    
    def _deserialize_data(self, data_str: str, decompress: bool = True) -> Optional[Any]:
        """Deserializa dados do armazenamento"""
        try:
            return json.loads(data_str)
        except Exception as e:
            logger.error(f"Erro na deserialização: {str(e)}")
            return None
    
    def _calculate_checksum(self, data: Any) -> str:
        """Calcula checksum dos dados"""
        try:
            data_str = str(data)
            return hashlib.md5(data_str.encode()).hexdigest()[:8]
        except Exception:
            return ""
    
    def _check_size_limit(self, item_size: int) -> bool:
        """Verifica limite de tamanho"""
        current_size = self._calculate_total_size()
        return (current_size + item_size) <= self.max_size_bytes
    
    def _calculate_total_size(self) -> int:
        """Calcula tamanho total usado"""
        total_size = 0
        
        # Calcular tamanho do session_state
        for key, value in st.session_state.items():
            if any(key.startswith(prefix) for prefix in self.prefixes.values()):
                total_size += len(str(value))
        
        return total_size
    
    def _store_by_type(self, storage_item: StorageItem, storage_type: StorageType) -> bool:
        """Armazena item baseado no tipo de armazenamento"""
        try:
            if storage_type == StorageType.SESSION_STATE:
                # Armazenar no session_state com metadados
                st.session_state[storage_item.key] = {
                    'data': storage_item.data,
                    'created_at': storage_item.created_at.isoformat(),
                    'expires_at': storage_item.expires_at.isoformat() if storage_item.expires_at else None,
                    'checksum': storage_item.checksum,
                    'version': storage_item.version
                }
                return True
            else:
                logger.warning(f"Tipo de armazenamento não implementado: {storage_type}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao armazenar por tipo {storage_type}: {str(e)}")
            return False
    
    def _retrieve_by_type(self, key: str, storage_type: StorageType) -> Optional[StorageItem]:
        """Recupera item baseado no tipo de armazenamento"""
        try:
            if storage_type == StorageType.SESSION_STATE:
                if key not in st.session_state:
                    return None
                
                stored_data = st.session_state[key]
                
                # Verificar se é formato novo (com metadados)
                if isinstance(stored_data, dict) and 'data' in stored_data:
                    return StorageItem(
                        key=key,
                        data=stored_data['data'],
                        data_type=DataType.CACHE_DATA,  # Será determinado pelo contexto
                        storage_type=storage_type,
                        created_at=datetime.fromisoformat(stored_data['created_at']),
                        expires_at=datetime.fromisoformat(stored_data['expires_at']) if stored_data.get('expires_at') else None,
                        checksum=stored_data.get('checksum', ''),
                        version=stored_data.get('version', '1.0')
                    )
                else:
                    # Formato legado - dados diretos
                    return StorageItem(
                        key=key,
                        data=stored_data,
                        data_type=DataType.CACHE_DATA,
                        storage_type=storage_type,
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + self.default_ttl
                    )
            else:
                logger.warning(f"Tipo de armazenamento não implementado: {storage_type}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao recuperar por tipo {storage_type}: {str(e)}")
            return None
    
    def _delete_by_type(self, key: str, storage_type: StorageType) -> bool:
        """Remove item baseado no tipo de armazenamento"""
        try:
            if storage_type == StorageType.SESSION_STATE:
                if key in st.session_state:
                    del st.session_state[key]
                    return True
                return False
            else:
                logger.warning(f"Tipo de armazenamento não implementado: {storage_type}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao remover por tipo {storage_type}: {str(e)}")
            return False
    
    def _exists_by_type(self, key: str, storage_type: StorageType) -> bool:
        """Verifica existência baseado no tipo de armazenamento"""
        try:
            if storage_type == StorageType.SESSION_STATE:
                return key in st.session_state
            else:
                return False
        except Exception:
            return False
    
    def _list_session_keys(self, data_type: Optional[DataType], include_expired: bool) -> List[str]:
        """Lista chaves do session_state"""
        keys = []
        
        for key in st.session_state.keys():
            # Filtrar por tipo se especificado
            if data_type:
                prefix = self.prefixes.get(data_type, "")
                if not key.startswith(prefix):
                    continue
            else:
                # Verificar se é uma chave de storage
                if not any(key.startswith(prefix) for prefix in self.prefixes.values()):
                    continue
            
            # Verificar expiração se não incluir expirados
            if not include_expired:
                storage_item = self._retrieve_by_type(key, StorageType.SESSION_STATE)
                if storage_item and self._is_expired(storage_item):
                    continue
            
            keys.append(key)
        
        return keys
    
    def _is_expired(self, storage_item: StorageItem) -> bool:
        """Verifica se item está expirado"""
        if not storage_item.expires_at:
            return False
        return datetime.utcnow() > storage_item.expires_at
    
    def _cleanup_expired_items(self) -> int:
        """Remove itens expirados"""
        removed_count = 0
        
        try:
            # Listar todas as chaves
            all_keys = []
            for key in st.session_state.keys():
                if any(key.startswith(prefix) for prefix in self.prefixes.values()):
                    all_keys.append(key)
            
            # Verificar cada chave
            for key in all_keys:
                storage_item = self._retrieve_by_type(key, StorageType.SESSION_STATE)
                if storage_item and self._is_expired(storage_item):
                    if self._delete_by_type(key, StorageType.SESSION_STATE):
                        removed_count += 1
            
            if removed_count > 0:
                logger.info(f"Itens expirados removidos: {removed_count}")
            
        except Exception as e:
            logger.error(f"Erro na limpeza de itens expirados: {str(e)}")
        
        return removed_count
    
    def _remove_duplicates(self) -> int:
        """Remove itens duplicados baseado em checksum"""
        removed_count = 0
        checksums_seen = set()
        
        try:
            all_keys = []
            for key in st.session_state.keys():
                if any(key.startswith(prefix) for prefix in self.prefixes.values()):
                    all_keys.append(key)
            
            for key in all_keys:
                storage_item = self._retrieve_by_type(key, StorageType.SESSION_STATE)
                if storage_item and storage_item.checksum:
                    if storage_item.checksum in checksums_seen:
                        if self._delete_by_type(key, StorageType.SESSION_STATE):
                            removed_count += 1
                    else:
                        checksums_seen.add(storage_item.checksum)
            
            if removed_count > 0:
                logger.info(f"Duplicatas removidas: {removed_count}")
                
        except Exception as e:
            logger.error(f"Erro na remoção de duplicatas: {str(e)}")
        
        return removed_count
    
    def _compress_large_items(self) -> int:
        """Comprime itens grandes"""
        # Placeholder para implementação futura
        return 0
    
    def _update_statistics(self):
        """Atualiza estatísticas do armazenamento"""
        try:
            # Resetar estatísticas
            self.stats = StorageStats()
            
            # Contar itens por tipo e armazenamento
            for key in st.session_state.keys():
                if any(key.startswith(prefix) for prefix in self.prefixes.values()):
                    self.stats.total_items += 1
                    
                    # Calcular tamanho
                    item_size = len(str(st.session_state[key]))
                    self.stats.total_size_bytes += item_size
                    
                    # Identificar tipo
                    data_type = None
                    for dt, prefix in self.prefixes.items():
                        if key.startswith(prefix):
                            data_type = dt.value
                            break
                    
                    if data_type:
                        self.stats.items_by_type[data_type] = self.stats.items_by_type.get(data_type, 0) + 1
                    
                    # Tipo de armazenamento (sempre session_state por enquanto)
                    storage_type = StorageType.SESSION_STATE.value
                    self.stats.items_by_storage[storage_type] = self.stats.items_by_storage.get(storage_type, 0) + 1
                    
                    # Verificar expiração
                    storage_item = self._retrieve_by_type(key, StorageType.SESSION_STATE)
                    if storage_item and self._is_expired(storage_item):
                        self.stats.expired_items += 1
            
            # Calcular taxa de acerto do cache
            total_reads = self._operations['hit'] + self._operations['miss']
            if total_reads > 0:
                self.stats.cache_hit_rate = self._operations['hit'] / total_reads
            
            # Operações
            self.stats.operations_count = self._operations.copy()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas: {str(e)}")

# Instância global para facilitar uso
@st.cache_resource
def get_offline_storage() -> OfflineStorage:
    """Retorna instância cached do OfflineStorage"""
    return OfflineStorage()

# Funções de conveniência para compatibilidade
def store_project_data(project_id: str, data: Dict, ttl_minutes: int = 60) -> bool:
    """Armazena dados de projeto"""
    storage = get_offline_storage()
    return storage.store_data(
        key=project_id,
        data=data,
        data_type=DataType.PROJECT_DATA,
        ttl_minutes=ttl_minutes
    )

def retrieve_project_data(project_id: str) -> Optional[Dict]:
    """Recupera dados de projeto"""
    storage = get_offline_storage()
    return storage.retrieve_data(
        key=project_id,
        data_type=DataType.PROJECT_DATA
    )

def store_analysis_results(analysis_id: str, results: Dict, ttl_minutes: int = 120) -> bool:
    """Armazena resultados de análise"""
    storage = get_offline_storage()
    return storage.store_data(
        key=analysis_id,
        data=results,
        data_type=DataType.ANALYSIS_RESULTS,
        ttl_minutes=ttl_minutes
    )

def retrieve_analysis_results(analysis_id: str) -> Optional[Dict]:
    """Recupera resultados de análise"""
    storage = get_offline_storage()
    return storage.retrieve_data(
        key=analysis_id,
        data_type=DataType.ANALYSIS_RESULTS
    )

def store_uploaded_file_data(file_id: str, data: Any, ttl_minutes: int = 180) -> bool:
    """Armazena dados de arquivo enviado"""
    storage = get_offline_storage()
    return storage.store_data(
        key=file_id,
        data=data,
        data_type=DataType.UPLOADED_FILES,
        ttl_minutes=ttl_minutes
    )

def retrieve_uploaded_file_data(file_id: str) -> Optional[Any]:
    """Recupera dados de arquivo enviado"""
    storage = get_offline_storage()
    return storage.retrieve_data(
        key=file_id,
        data_type=DataType.UPLOADED_FILES
    )

# Função principal para compatibilidade
def main():
    """Função principal para teste standalone"""
    st.title("💾 Offline Storage Test")
    
    # Criar instância
    storage = get_offline_storage()
    
    # Interface de teste
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Armazenar Dados")
        
        test_key = st.text_input("Chave", value="test_key")
        test_data = st.text_area("Dados (JSON)", value='{"test": "value"}')
        data_type = st.selectbox("Tipo", options=[dt.value for dt in DataType])
        ttl = st.number_input("TTL (minutos)", value=60, min_value=1)
        
        if st.button("Armazenar"):
            try:
                data_obj = json.loads(test_data)
                success = storage.store_data(
                    key=test_key,
                    data=data_obj,
                    data_type=DataType(data_type),
                    ttl_minutes=ttl
                )
                if success:
                    st.success("✅ Dados armazenados!")
                else:
                    st.error("❌ Erro ao armazenar")
            except json.JSONDecodeError:
                st.error("❌ JSON inválido")
    
    with col2:
        st.subheader("Recuperar Dados")
        
        retrieve_key = st.text_input("Chave para recuperar", value="test_key")
        retrieve_type = st.selectbox("Tipo para recuperar", options=[dt.value for dt in DataType])
        
        if st.button("Recuperar"):
            data = storage.retrieve_data(
                key=retrieve_key,
                data_type=DataType(retrieve_type)
            )
            if data is not None:
                st.success("✅ Dados encontrados!")
                st.json(data)
            else:
                st.warning("⚠️ Dados não encontrados")
    
    # Estatísticas
    st.divider()
    st.subheader("📊 Estatísticas")
    
    stats = storage.get_statistics()
    
    col3, col4, col5, col6 = st.columns(4)
    with col3:
        st.metric("Total de Itens", stats.total_items)
    with col4:
        st.metric("Tamanho Total", f"{stats.total_size_bytes / 1024:.1f} KB")
    with col5:
        st.metric("Taxa de Acerto", f"{stats.cache_hit_rate:.1%}")
    with col6:
        st.metric("Itens Expirados", stats.expired_items)
    
    # Operações
    if st.button("🧹 Limpar Expirados"):
        removed = storage.cleanup_expired()
        st.success(f"✅ {removed} itens expirados removidos")
    
    if st.button("⚡ Otimizar Storage"):
        results = storage.optimize_storage()
        st.json(results)
    
    # Listar chaves
    st.subheader("🔑 Chaves Armazenadas")
    keys = storage.list_keys()
    if keys:
        st.write(keys)
    else:
        st.info("Nenhuma chave encontrada")

if __name__ == "__main__":
    main()
