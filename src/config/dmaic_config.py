"""
Configurações centralizadas para as fases DMAIC
Este arquivo define as ferramentas, ícones e configurações de cada fase
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List

class DMACPhase(Enum):
    """Enumeração das fases DMAIC"""
    DEFINE = "define"
    MEASURE = "measure"
    ANALYZE = "analyze"
    IMPROVE = "improve"
    CONTROL = "control"

@dataclass
class ToolConfig:
    """Configuração de uma ferramenta específica"""
    key: str
    name: str
    description: str
    icon: str
    enabled: bool = True
    required: bool = False

@dataclass
class PhaseConfig:
    """Configuração de uma fase DMAIC"""
    key: str
    name: str
    icon: str
    description: str
    color: str
    tools: List[ToolConfig]

# Configuração completa das fases DMAIC
DMAIC_PHASES_CONFIG = {
    DMACPhase.DEFINE: PhaseConfig(
        key="define",
        name="Define",
        icon="🎯",
        description="Definir problema, objetivos e escopo do projeto",
        color="#e3f2fd",
        tools=[
            ToolConfig(
                key="project_charter",
                name="Project Charter",
                description="Documento que define formalmente o projeto",
                icon="📋",
                required=True
            ),
            ToolConfig(
                key="stakeholder_analysis",
                name="Análise de Stakeholders",
                description="Identificação e análise das partes interessadas",
                icon="👥"
            ),
            ToolConfig(
                key="voice_of_customer",
                name="Voz do Cliente (VOC)",
                description="Captura dos requisitos e expectativas do cliente",
                icon="🗣️"
            ),
            ToolConfig(
                key="sipoc",
                name="Diagrama SIPOC",
                description="Visão de alto nível do processo (Suppliers, Inputs, Process, Outputs, Customers)",
                icon="🔄"
            ),
            ToolConfig(
                key="problem_statement",
                name="Declaração do Problema",
                description="Definição clara e específica do problema a ser resolvido",
                icon="❓"
            )
        ]
    ),
    
    DMACPhase.MEASURE: PhaseConfig(
        key="measure",
        name="Measure",
        icon="📏",
        description="Medir e coletar dados do estado atual do processo",
        color="#f3e5f5",
        tools=[
            ToolConfig(
                key="data_collection_plan",
                name="Plano de Coleta de Dados",
                description="Estratégia para coleta sistemática de dados",
                icon="📊",
                required=True
            ),
            ToolConfig(
                key="measurement_system",
                name="Sistema de Medição",
                description="Análise da confiabilidade do sistema de medição",
                icon="⚖️"
            ),
            ToolConfig(
                key="process_mapping",
                name="Mapeamento de Processo",
                description="Documentação detalhada do processo atual",
                icon="🗺️"
            ),
            ToolConfig(
                key="baseline_analysis",
                name="Análise da Linha Base",
                description="Estabelecimento da performance atual do processo",
                icon="📈"
            )
        ]
    ),
    
    DMACPhase.ANALYZE: PhaseConfig(
        key="analyze",
        name="Analyze",
        icon="🔍",
        description="Analisar dados e identificar causas raiz dos problemas",
        color="#fff3e0",
        tools=[
            ToolConfig(
                key="statistical_analysis",
                name="Análise Estatística",
                description="Análise estatística dos dados coletados",
                icon="📊",
                required=True
            ),
            ToolConfig(
                key="root_cause_analysis",
                name="Análise de Causa Raiz",
                description="Identificação das causas fundamentais dos problemas",
                icon="🌳",
                required=True
            ),
            ToolConfig(
                key="hypothesis_testing",
                name="Teste de Hipóteses",
                description="Validação estatística de hipóteses sobre o processo",
                icon="🧪"
            ),
            ToolConfig(
                key="process_analysis",
                name="Análise de Processo",
                description="Análise detalhada do desempenho do processo",
                icon="⚙️"
            )
        ]
    ),
    
    DMACPhase.IMPROVE: PhaseConfig(
        key="improve",
        name="Improve",
        icon="⚡",
        description="Desenvolver e implementar soluções para as causas raiz",
        color="#e8f5e8",
        tools=[
            ToolConfig(
                key="solution_development",
                name="Desenvolvimento de Soluções",
                description="Criação e avaliação de soluções potenciais",
                icon="💡",
                required=True
            ),
            ToolConfig(
                key="action_plan",
                name="Plano de Ação",
                description="Planejamento detalhado da implementação",
                icon="📋"
            ),
            ToolConfig(
                key="pilot_implementation",
                name="Implementação Piloto",
                description="Teste das soluções em escala reduzida",
                icon="🧪"
            ),
            ToolConfig(
                key="full_implementation",
                name="Implementação Completa",
                description="Implementação das soluções em escala total",
                icon="🚀"
            )
        ]
    ),
    
    DMACPhase.CONTROL: PhaseConfig(
        key="control",
        name="Control",
        icon="🎮",
        description="Controlar e sustentar as melhorias alcançadas",
        color="#fce4ec",
        tools=[
            ToolConfig(
                key="control_plan",
                name="Plano de Controle",
                description="Sistema para monitoramento contínuo do processo",
                icon="📋",
                required=True
            ),
            ToolConfig(
                key="monitoring_system",
                name="Sistema de Monitoramento",
                description="Ferramentas para acompanhamento da performance",
                icon="📈"
            ),
            ToolConfig(
                key="documentation",
                name="Documentação Padrão",
                description="Procedimentos e instruções padronizadas",
                icon="📚"
            ),
            ToolConfig(
                key="sustainability_plan",
                name="Plano de Sustentabilidade",
                description="Estratégias para manter as melhorias a longo prazo",
                icon="♻️"
            )
        ]
    )
}

def get_phase_config(phase: DMACPhase) -> PhaseConfig:
    """Retorna a configuração de uma fase específica"""
    return DMAIC_PHASES_CONFIG[phase]

def get_all_phases() -> List[PhaseConfig]:
    """Retorna todas as configurações de fases"""
    return list(DMAIC_PHASES_CONFIG.values())

def get_phase_tools(phase: DMACPhase) -> List[ToolConfig]:
    """Retorna as ferramentas de uma fase específica"""
    return DMAIC_PHASES_CONFIG[phase].tools

def get_tool_config(phase: DMACPhase, tool_key: str) -> ToolConfig:
    """Retorna a configuração de uma ferramenta específica"""
    tools = get_phase_tools(phase)
    for tool in tools:
        if tool.key == tool_key:
            return tool
    raise ValueError(f"Ferramenta '{tool_key}' não encontrada na fase '{phase.value}'")

def get_required_tools(phase: DMACPhase) -> List[ToolConfig]:
    """Retorna apenas as ferramentas obrigatórias de uma fase"""
    return [tool for tool in get_phase_tools(phase) if tool.required]

def calculate_phase_completion_percentage(phase_data: Dict, phase: DMACPhase) -> float:
    """Calcula a porcentagem de conclusão de uma fase"""
    if not isinstance(phase_data, dict):
        return 0.0
    
    tools = get_phase_tools(phase)
    if not tools:
        return 0.0
    
    completed_count = 0
    for tool in tools:
        tool_data = phase_data.get(tool.key, {})
        if isinstance(tool_data, dict) and tool_data.get('completed', False):
            completed_count += 1
    
    return (completed_count / len(tools)) * 100

def validate_phase_data(phase_data: Dict, phase: DMACPhase) -> Dict:
    """Valida os dados de uma fase e retorna informações de validação"""
    tools = get_phase_tools(phase)
    required_tools = get_required_tools(phase)
    
    validation_result = {
        'is_valid': True,
        'completion_percentage': calculate_phase_completion_percentage(phase_data, phase),
        'completed_tools': [],
        'missing_required_tools': [],
        'total_tools': len(tools),
        'required_tools_count': len(required_tools)
    }
    
    for tool in tools:
        tool_data = phase_data.get(tool.key, {})
        is_completed = isinstance(tool_data, dict) and tool_data.get('completed', False)
        
        if is_completed:
            validation_result['completed_tools'].append(tool.key)
        elif tool.required:
            validation_result['missing_required_tools'].append(tool.key)
    
    # Fase é válida se todas as ferramentas obrigatórias estão concluídas
    validation_result['is_valid'] = len(validation_result['missing_required_tools']) == 0
    
    return validation_result

# Exportar constantes para compatibilidade
DMAIC_PHASES = list(DMAIC_PHASES_CONFIG.keys())
PHASE_NAMES = {phase.value: config.name for phase, config in DMAIC_PHASES_CONFIG.items()}
PHASE_ICONS = {phase.value: config.icon for phase, config in DMAIC_PHASES_CONFIG.items()}
PHASE_COLORS = {phase.value: config.color for phase, config in DMAIC_PHASES_CONFIG.items()}
