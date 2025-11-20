#Control_tools.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import warnings

# Suprimir warnings
warnings.filterwarnings('ignore')

# Import do ProjectManager com tratamento de erro
try:
    from src.utils.project_manager import ProjectManager
except ImportError:
    try:
        from src.core.project_manager import ProjectManager
    except ImportError:
        st.error("❌ Não foi possível importar ProjectManager")
        st.stop()


class ControlPhaseManager:
    """Gerenciador centralizado da fase Control"""
    
    def __init__(self, project_data: Dict):
        self.project_data = project_data
        self.project_id = project_data.get('id')
        self.project_manager = ProjectManager()
    
    def save_tool_data(self, tool_name: str, data: Dict, completed: bool = False) -> bool:
        """Salva dados de uma ferramenta com atualização de estado"""
        try:
            update_data = {
                f'control.{tool_name}.data': data,
                f'control.{tool_name}.completed': completed,
                f'control.{tool_name}.updated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            success = self.project_manager.update_project(self.project_id, update_data)
            
            if success and 'current_project' in st.session_state:
                # Atualizar session_state imediatamente
                if 'control' not in st.session_state.current_project:
                    st.session_state.current_project['control'] = {}
                if tool_name not in st.session_state.current_project['control']:
                    st.session_state.current_project['control'][tool_name] = {}
                
                st.session_state.current_project['control'][tool_name] = {
                    'data': data,
                    'completed': completed,
                    'updated_at': datetime.now().isoformat()
                }
            
            return success
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar dados: {str(e)}")
            return False
    
    def is_tool_completed(self, tool_name: str) -> bool:
        """Verifica se uma ferramenta foi concluída"""
        control_data = self.project_data.get('control', {})
        tool_data = control_data.get(tool_name, {})
        return tool_data.get('completed', False) if isinstance(tool_data, dict) else False
    
    def get_tool_data(self, tool_name: str) -> Dict:
        """Recupera dados de uma ferramenta"""
        control_data = self.project_data.get('control', {})
        tool_data = control_data.get(tool_name, {})
        return tool_data.get('data', {}) if isinstance(tool_data, dict) else {}
    
    def get_improve_results(self) -> Dict:
        """Recupera resultados da fase Improve para usar no Control"""
        improve_data = self.project_data.get('improve', {})
        results = {
            'implemented_solutions': [],
            'kpis_data': [],
            'pilot_results': {}
        }
        
        # Soluções implementadas
        solution_data = improve_data.get('solution_development', {}).get('data', {})
        if solution_data.get('solutions'):
            results['implemented_solutions'] = [
                sol for sol in solution_data['solutions'] 
                if sol.get('status') == 'Aprovada'
            ]
        
        # Resultados do piloto
        pilot_data = improve_data.get('pilot_implementation', {}).get('data', {})
        if pilot_data.get('results'):
            results['pilot_results'] = pilot_data['results']
        
        # KPIs da implementação
        full_impl_data = improve_data.get('full_implementation', {}).get('data', {})
        monitoring_data = full_impl_data.get('monitoring_system', {})
        if monitoring_data.get('kpis'):
            results['kpis_data'] = monitoring_data['kpis']
        
        return results


class ControlPlanTool:
    """Ferramenta para Plano de Controle"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "control_plan"
    
    def show(self):
        """Interface principal da ferramenta"""
        st.markdown("## 📊 Plano de Controle")
        st.markdown("Desenvolva um sistema abrangente para monitorar e controlar as melhorias implementadas.")
        
        # Status da ferramenta
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ **Plano de controle finalizado**")
        else:
            st.info("⏳ **Plano em desenvolvimento**")
        
        # Inicializar dados da sessão
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data if existing_data else {
                'control_points': [],
                'monitoring_schedule': [],
                'response_plans': [],
                'documentation': {}
            }
        
        control_data = st.session_state[session_key]
        
        # Mostrar resultados da fase Improve
        self._show_improve_summary()
        
        # Interface principal
        self._show_control_tabs(control_data)
        
        # Botões de ação
        self._show_action_buttons(control_data)
    
    def _show_improve_summary(self):
        """Mostra resumo dos resultados da fase Improve"""
        st.markdown("### 🎯 Resultados da Implementação")
        
        improve_results = self.manager.get_improve_results()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            solutions = improve_results['implemented_solutions']
            st.metric("Soluções Implementadas", len(solutions))
            
            if solutions:
                with st.expander("Ver soluções"):
                    for i, sol in enumerate(solutions, 1):
                        st.write(f"**{i}.** {sol['name']}")
        
        with col2:
            kpis = improve_results['kpis_data']
            st.metric("KPIs Monitorados", len(kpis))
            
            if kpis:
                with st.expander("Ver KPIs"):
                    for kpi in kpis:
                        st.write(f"• {kpi['name']} ({kpi.get('unit', '')})")
        
        with col3:
            pilot_results = improve_results['pilot_results']
            if pilot_results.get('recommendation'):
                st.metric("Status do Piloto", "✅ Aprovado")
                st.caption(pilot_results['recommendation'])
            else:
                st.metric("Status do Piloto", "⏳ Pendente")
    
    def _show_control_tabs(self, control_data: Dict):
        """Mostra abas do plano de controle"""
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 Pontos de Controle",
            "📅 Cronograma",
            "⚠️ Planos de Resposta",
            "📋 Documentação"
        ])
        
        with tab1:
            self._show_control_points(control_data)
        
        with tab2:
            self._show_monitoring_schedule(control_data)
        
        with tab3:
            self._show_response_plans(control_data)
        
        with tab4:
            self._show_documentation(control_data)
    ######################################################################################################################################################    
    def _show_control_points(self, control_data: Dict):
        """Gerenciamento de pontos de controle"""
        st.markdown("#### 🎯 Pontos de Controle")
        
        # [... código anterior permanece igual até "Mostrar pontos existentes" ...]
        
        # Mostrar pontos existentes
        if control_data.get('control_points'):
            st.markdown("##### 📊 Pontos de Controle Definidos")
            
            for i, point in enumerate(control_data['control_points']):
                with st.expander(f"🎯 **{point['name']}** - {point['status']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Métrica:** {point['metric']} ({point.get('unit', '')})")
                        st.write(f"**Meta:** {point.get('target', 0)}")
                        st.write(f"**Limites:** {point.get('lower_limit', 0)} - {point.get('upper_limit', 0)}")
                        st.write(f"**Descrição:** {point.get('description', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Frequência:** {point.get('frequency', 'N/A')}")
                        st.write(f"**Responsável:** {point.get('responsible', 'Não definido')}")
                        if point.get('measurement_method'):
                            st.write(f"**Método:** {point['measurement_method']}")
                        
                        # Adicionar medição rápida
                        new_value = st.number_input(
                            "Nova medição:",
                            key=f"new_measurement_{i}_{self.project_id}",
                            step=0.01
                        )
                        
                        if st.button("➕ Adicionar", key=f"add_measurement_{i}_{self.project_id}"):
                            if 'measurements' not in control_data['control_points'][i]:
                                control_data['control_points'][i]['measurements'] = []
                            
                            control_data['control_points'][i]['measurements'].append({
                                'date': datetime.now().date().isoformat(),
                                'value': new_value,
                                'status': self._check_control_status(new_value, point),
                                'added_at': datetime.now().isoformat()
                            })
                            
                            st.success("✅ Medição adicionada!")
                            st.rerun()
                    
                    with col3:
                        new_status = st.selectbox(
                            "Status:",
                            ["Ativo", "Inativo", "Suspenso"],
                            index=["Ativo", "Inativo", "Suspenso"].index(point.get('status', 'Ativo')),
                            key=f"point_status_{i}_{self.project_id}"
                        )
                        
                        control_data['control_points'][i]['status'] = new_status
                        
                        if st.button("🗑️ Remover Ponto", key=f"remove_point_{i}_{self.project_id}"):
                            confirm_key = f"confirm_delete_point_{i}_{self.project_id}"
                            
                            if st.session_state.get(confirm_key, False):
                                control_data['control_points'].pop(i)
                                if confirm_key in st.session_state:
                                    del st.session_state[confirm_key]
                                st.success("✅ Ponto removido!")
                                st.rerun()
                            else:
                                st.session_state[confirm_key] = True
                                st.warning("⚠️ Clique novamente para confirmar")
                        
                        # Status atual baseado nas medições
                        measurements = point.get('measurements', [])
                        if measurements:
                            last_measurement = measurements[-1]
                            status = last_measurement.get('status', 'OK')
                            
                            if status == 'OK':
                                st.success("✅ No controle")
                            elif status == 'WARNING':
                                st.warning("⚠️ Atenção")
                            else:
                                st.error("🚨 Fora de controle")
                    
                    # ✅ NOVA SEÇÃO: GERENCIAR MEDIÇÕES EXISTENTES
                    measurements = point.get('measurements', [])
                    if measurements:
                        st.markdown("---")
                        st.markdown("##### 📋 Medições Registradas")
                        
                        # Botão para atualizar
                        if st.button("🔄 Atualizar Medições", key=f"refresh_point_{i}_{self.project_id}"):
                            st.rerun()
                        
                        # Processar cada medição
                        for measure_idx in range(len(measurements)):
                            # Verificar se o índice ainda existe
                            if measure_idx >= len(control_data['control_points'][i]['measurements']):
                                continue
                                
                            measurement = control_data['control_points'][i]['measurements'][measure_idx]
                            
                            # Chave única para esta medição
                            unique_id = f"point{i}_measure{measure_idx}_{len(measurements)}_{self.project_id}"
                            edit_key = f"editing_{unique_id}"
                            delete_confirm_key = f"delete_confirm_{unique_id}"
                            
                            measurement_date_str = datetime.fromisoformat(measurement['date']).strftime('%d/%m/%Y')
                            
                            # Container para cada medição
                            with st.container():
                                # Verificar se está em modo de edição
                                is_editing = st.session_state.get(edit_key, False)
                                
                                if is_editing:
                                    # ✅ MODO EDIÇÃO
                                    st.markdown(f"**✏️ Editando medição de {measurement_date_str}:**")
                                    
                                    col_edit1, col_edit2, col_edit3 = st.columns([2, 2, 2])
                                    
                                    with col_edit1:
                                        edited_date = st.date_input(
                                            "Nova Data:",
                                            value=datetime.fromisoformat(measurement['date']).date(),
                                            key=f"edit_point_date_{unique_id}"
                                        )
                                    
                                    with col_edit2:
                                        edited_value = st.number_input(
                                            f"Novo Valor ({point.get('unit', '')}):",
                                            value=float(measurement['value']),
                                            key=f"edit_point_value_{unique_id}",
                                            step=0.01,
                                            format="%.2f"
                                        )
                                    
                                    with col_edit3:
                                        col_save, col_cancel = st.columns(2)
                                        
                                        with col_save:
                                            if st.button("💾", key=f"save_point_{unique_id}", help="Salvar"):
                                                # Verificar se índice ainda é válido
                                                if measure_idx < len(control_data['control_points'][i]['measurements']):
                                                    # Recalcular status com novo valor
                                                    new_status = self._check_control_status(edited_value, point)
                                                    
                                                    control_data['control_points'][i]['measurements'][measure_idx] = {
                                                        'date': edited_date.isoformat(),
                                                        'value': float(edited_value),
                                                        'status': new_status,
                                                        'added_at': measurement.get('added_at', datetime.now().isoformat()),
                                                        'updated_at': datetime.now().isoformat()
                                                    }
                                                    
                                                    # Limpar estado de edição
                                                    if edit_key in st.session_state:
                                                        del st.session_state[edit_key]
                                                    
                                                    st.success("✅ Medição atualizada!")
                                                    st.rerun()
                                        
                                        with col_cancel:
                                            if st.button("❌", key=f"cancel_point_{unique_id}", help="Cancelar"):
                                                if edit_key in st.session_state:
                                                    del st.session_state[edit_key]
                                                st.rerun()
                                
                                else:
                                    # ✅ MODO VISUALIZAÇÃO
                                    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
                                    
                                    with col1:
                                        st.write(f"📅 **{measurement_date_str}**")
                                    
                                    with col2:
                                        st.write(f"**{measurement['value']} {point.get('unit', '')}**")
                                    
                                    with col3:
                                        # Status da medição
                                        status = measurement.get('status', 'OK')
                                        if status == 'OK':
                                            st.success("✅")
                                        elif status == 'WARNING':
                                            st.warning("⚠️")
                                        else:
                                            st.error("🚨")
                                    
                                    with col4:
                                        if st.button("✏️", key=f"edit_point_{unique_id}", help="Editar"):
                                            st.session_state[edit_key] = True
                                            st.rerun()
                                    
                                    with col5:
                                        # ✅ DELETE PARA MEDIÇÕES DO PONTO DE CONTROLE
                                        if st.button("🗑️", key=f"delete_point_{unique_id}", help="Excluir medição"):
                                            if st.session_state.get(delete_confirm_key, False):
                                                try:
                                                    # Verificar se ainda existe
                                                    if measure_idx < len(control_data['control_points'][i]['measurements']):
                                                        # Remover diretamente pelo índice
                                                        control_data['control_points'][i]['measurements'].pop(measure_idx)
                                                        
                                                        # Limpar estados relacionados
                                                        keys_to_remove = []
                                                        for key in st.session_state.keys():
                                                            if (f"point{i}_measure" in key or 
                                                                f"delete_confirm_point{i}" in key or
                                                                f"editing_point{i}" in key):
                                                                keys_to_remove.append(key)
                                                        
                                                        for key in keys_to_remove:
                                                            try:
                                                                del st.session_state[key]
                                                            except:
                                                                pass
                                                        
                                                        st.success(f"✅ Medição de {measurement_date_str} removida!")
                                                        st.rerun()
                                                    else:
                                                        st.error("❌ Medição não encontrada")
                                                except Exception as e:
                                                    st.error(f"❌ Erro ao remover: {str(e)}")
                                            else:
                                                # Primeira vez - pedir confirmação
                                                st.session_state[delete_confirm_key] = True
                                                st.warning("⚠️ Clique novamente para confirmar exclusão")
                                
                                # Separador
                                if measure_idx < len(measurements) - 1:
                                    st.divider()
                        
                        # ✅ BOTÃO DE LIMPEZA DE EMERGÊNCIA
                        if st.button("🧹 Limpar Estados", key=f"emergency_clear_point_{i}_{self.project_id}"):
                            keys_to_remove = []
                            for key in st.session_state.keys():
                                if f"point{i}_" in key:
                                    keys_to_remove.append(key)
                            
                            for key in keys_to_remove:
                                try:
                                    del st.session_state[key]
                                except:
                                    pass
                            
                            st.success("🧹 Estados limpos!")
                            st.rerun()
                    
                    else:
                        st.info("📝 Nenhuma medição registrada ainda.")
        else:
            st.info("🎯 Nenhum ponto de controle definido ainda.")

    
    def _check_control_status(self, value: float, point: Dict) -> str:
        """Verifica status de uma medição baseada nos limites"""
        upper_limit = point.get('upper_limit', float('inf'))
        lower_limit = point.get('lower_limit', float('-inf'))
        target = point.get('target', 0)
        
        if lower_limit <= value <= upper_limit:
            # Dentro dos limites, mas verificar proximidade da meta
            if abs(value - target) / target <= 0.05:  # 5% da meta
                return 'OK'
            else:
                return 'WARNING'
        else:
            return 'ALERT'
    
    def _show_monitoring_schedule(self, control_data: Dict):
        """Cronograma de monitoramento"""
        st.markdown("#### 📅 Cronograma de Monitoramento")
        
        if not control_data.get('control_points'):
            st.info("💡 Defina pontos de controle primeiro")
            return
        
        # Gerar cronograma automático
        if st.button("📅 Gerar Cronograma Automático", key=f"auto_schedule_{self.project_id}"):
            schedule = []
            start_date = datetime.now().date()
            
            for point in control_data['control_points']:
                if point.get('status') == 'Ativo':
                    frequency = point.get('frequency', 'Semanal')
                    
                    # Calcular próximas datas baseadas na frequência
                    if frequency == 'Diária':
                        days_interval = 1
                        num_events = 30  # 30 dias
                    elif frequency == 'Semanal':
                        days_interval = 7
                        num_events = 12  # 12 semanas
                    elif frequency == 'Quinzenal':
                        days_interval = 14
                        num_events = 8   # 16 semanas
                    else:  # Mensal
                        days_interval = 30
                        num_events = 6   # 6 meses
                    
                    for j in range(num_events):
                        event_date = start_date + timedelta(days=j * days_interval)
                        
                        schedule.append({
                            'date': event_date.isoformat(),
                            'point_name': point['name'],
                            'metric': point['metric'],
                            'responsible': point.get('responsible', ''),
                            'frequency': frequency,
                            'status': 'Agendado',
                            'completed': False
                        })
            
            control_data['monitoring_schedule'] = sorted(schedule, key=lambda x: x['date'])
            st.success(f"✅ Cronograma gerado com {len(schedule)} eventos!")
            st.rerun()
        
        # Mostrar cronograma
        if control_data.get('monitoring_schedule'):
            st.markdown("##### 📊 Eventos de Monitoramento")
            
            # Filtros
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                date_filter = st.date_input(
                    "Filtrar por data:",
                    key=f"date_filter_{self.project_id}",
                    value=datetime.now().date()
                )
            
            with col_f2:
                status_filter = st.selectbox(
                    "Status:",
                    ["Todos", "Agendado", "Concluído", "Atrasado"],
                    key=f"status_filter_schedule_{self.project_id}"
                )
            
            # Aplicar filtros
            schedule = control_data['monitoring_schedule']
            filtered_schedule = []
            
            for event in schedule:
                event_date = datetime.fromisoformat(event['date']).date()
                
                # Filtro de data (mostrar eventos próximos)
                if abs((event_date - date_filter).days) <= 7:
                    
                    # Atualizar status baseado na data
                    if event_date < datetime.now().date() and not event.get('completed', False):
                        event['status'] = 'Atrasado'
                    
                    # Filtro de status
                    if status_filter == "Todos" or event.get('status') == status_filter:
                        filtered_schedule.append(event)
            
            # Mostrar eventos
            for i, event in enumerate(filtered_schedule[:20]):  # Limitar a 20 eventos
                original_index = schedule.index(event)
                event_date = datetime.fromisoformat(event['date'])
                
                # Determinar cor baseada no status
                if event.get('status') == 'Concluído':
                    color = "🟢"
                elif event.get('status') == 'Atrasado':
                    color = "🔴"
                else:
                    color = "🟡"
                
                with st.expander(f"{color} **{event['point_name']}** - {event_date.strftime('%d/%m/%Y')}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Métrica:** {event['metric']}")
                        st.write(f"**Responsável:** {event.get('responsible', 'Não definido')}")
                        st.write(f"**Frequência:** {event['frequency']}")
                    
                    with col2:
                        # Marcar como concluído
                        completed = st.checkbox(
                            "Concluído",
                            value=event.get('completed', False),
                            key=f"completed_{original_index}_{self.project_id}"
                        )
                        
                        if completed != event.get('completed', False):
                            control_data['monitoring_schedule'][original_index]['completed'] = completed
                            control_data['monitoring_schedule'][original_index]['status'] = 'Concluído' if completed else 'Agendado'
                        
                        # Observações
                        notes = st.text_area(
                            "Observações:",
                            value=event.get('notes', ''),
                            key=f"notes_{original_index}_{self.project_id}",
                            height=60
                        )
                        
                        control_data['monitoring_schedule'][original_index]['notes'] = notes
                    
                    with col3:
                        if st.button("🗑️", key=f"remove_event_{original_index}_{self.project_id}"):
                            control_data['monitoring_schedule'].pop(original_index)
                            st.rerun()
            
            # Estatísticas do cronograma
            total_events = len(schedule)
            completed_events = len([e for e in schedule if e.get('completed', False)])
            overdue_events = len([e for e in schedule if e.get('status') == 'Atrasado'])
            
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            
            with col_stats1:
                st.metric("Total de Eventos", total_events)
            
            with col_stats2:
                st.metric("Concluídos", f"{completed_events}/{total_events}")
            
            with col_stats3:
                st.metric("Atrasados", overdue_events)
        else:
            st.info("📅 Nenhum cronograma definido ainda.")
    
    def _show_response_plans(self, control_data: Dict):
        """Planos de resposta"""
        st.markdown("#### ⚠️ Planos de Resposta")
        
        # Adicionar plano de resposta
        with st.expander("➕ Adicionar Plano de Resposta"):
            col1, col2 = st.columns(2)
            
            with col1:
                response_trigger = st.selectbox(
                    "Gatilho:",
                    ["Fora dos limites de controle", "Tendência negativa", "Meta não atingida", "Falha no processo", "Outro"],
                    key=f"response_trigger_{self.project_id}"
                )
                
                response_severity = st.selectbox(
                    "Severidade:",
                    ["Baixa", "Média", "Alta", "Crítica"],
                    key=f"response_severity_{self.project_id}"
                )
                
                response_responsible = st.text_input(
                    "Responsável:",
                    key=f"response_responsible_{self.project_id}"
                )
            
            with col2:
                response_timeframe = st.selectbox(
                    "Prazo de Resposta:",
                    ["Imediato (< 1 hora)", "Rápido (< 4 horas)", "Normal (< 24 horas)", "Programado (< 1 semana)"],
                    key=f"response_timeframe_{self.project_id}"
                )
                
                response_escalation = st.text_input(
                    "Escalação:",
                    key=f"response_escalation_{self.project_id}",
                    placeholder="Para quem escalar se necessário"
                )
            
            response_description = st.text_area(
                "Descrição do Problema:",
                key=f"response_description_{self.project_id}",
                placeholder="Que tipo de problema este plano aborda?",
                height=80
            )
            
            response_actions = st.text_area(
                "Ações de Resposta:",
                key=f"response_actions_{self.project_id}",
                placeholder="Que ações devem ser tomadas quando este problema ocorrer?",
                height=100
            )
            
            if st.button("⚠️ Adicionar Plano", key=f"add_response_{self.project_id}"):
                if response_description.strip() and response_actions.strip():
                    control_data['response_plans'].append({
                        'trigger': response_trigger,
                        'severity': response_severity,
                        'description': response_description,
                        'actions': response_actions,
                        'responsible': response_responsible,
                        'timeframe': response_timeframe,
                        'escalation': response_escalation,
                        'status': 'Ativo',
                        'usage_count': 0,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success("✅ Plano de resposta adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Descrição e ações são obrigatórias")
        
        # Mostrar planos existentes
        if control_data.get('response_plans'):
            st.markdown("##### 📋 Planos de Resposta Definidos")
            
            for i, plan in enumerate(control_data['response_plans']):
                severity_colors = {"Crítica": "🔴", "Alta": "🟠", "Média": "🟡", "Baixa": "🟢"}
                severity_icon = severity_colors.get(plan['severity'], "🟡")
                
                with st.expander(f"{severity_icon} **{plan['trigger']}** - {plan['severity']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Descrição:** {plan['description']}")
                        st.write(f"**Ações:** {plan['actions']}")
                        st.write(f"**Responsável:** {plan.get('responsible', 'Não definido')}")
                    
                    with col2:
                        st.write(f"**Prazo:** {plan['timeframe']}")
                        if plan.get('escalation'):
                            st.write(f"**Escalação:** {plan['escalation']}")
                        st.write(f"**Usado:** {plan.get('usage_count', 0)} vez(es)")
                        
                        # Registrar uso do plano
                        if st.button("📝 Registrar Uso", key=f"use_plan_{i}_{self.project_id}"):
                            control_data['response_plans'][i]['usage_count'] = plan.get('usage_count', 0) + 1
                            control_data['response_plans'][i]['last_used'] = datetime.now().isoformat()
                            st.success("✅ Uso registrado!")
                            st.rerun()
                    
                    with col3:
                        new_status = st.selectbox(
                            "Status:",
                            ["Ativo", "Inativo", "Revisão"],
                            index=["Ativo", "Inativo", "Revisão"].index(plan.get('status', 'Ativo')),
                            key=f"plan_status_{i}_{self.project_id}"
                        )
                        
                        control_data['response_plans'][i]['status'] = new_status
                        
                        if st.button("🗑️", key=f"remove_plan_{i}_{self.project_id}"):
                            control_data['response_plans'].pop(i)
                            st.rerun()
        else:
            st.info("⚠️ Nenhum plano de resposta definido ainda.")
    
    def _show_documentation(self, control_data: Dict):
        """Documentação do plano de controle"""
        st.markdown("#### 📋 Documentação do Plano de Controle")
        
        if 'documentation' not in control_data:
            control_data['documentation'] = {}
        
        doc = control_data['documentation']
        
        # Seções da documentação
        st.markdown("##### 📖 Seções do Documento")
        
        # Objetivo do controle
        doc['objective'] = st.text_area(
            "🎯 Objetivo do Plano de Controle:",
            value=doc.get('objective', ''),
            key=f"doc_objective_{self.project_id}",
            placeholder="Descreva o objetivo geral do plano de controle...",
            height=80
        )
        
        # Escopo
        doc['scope'] = st.text_area(
            "🔍 Escopo:",
            value=doc.get('scope', ''),
            key=f"doc_scope_{self.project_id}",
            placeholder="Defina o que está incluído e excluído do controle...",
            height=80
        )
        
        # Responsabilidades
        doc['responsibilities'] = st.text_area(
            "👥 Responsabilidades:",
            value=doc.get('responsibilities', ''),
            key=f"doc_responsibilities_{self.project_id}",
            placeholder="Defina quem é responsável por cada aspecto do controle...",
            height=100
        )
        
        # Procedimentos
        doc['procedures'] = st.text_area(
            "📋 Procedimentos:",
            value=doc.get('procedures', ''),
            key=f"doc_procedures_{self.project_id}",
            placeholder="Descreva os procedimentos detalhados de controle...",
            height=120
        )
        
        # Revisão e atualização
        col1, col2 = st.columns(2)
        
        with col1:
            doc['review_frequency'] = st.selectbox(
                "🔄 Frequência de Revisão:",
                ["Mensal", "Trimestral", "Semestral", "Anual"],
                index=1 if not doc.get('review_frequency') else 
                      ["Mensal", "Trimestral", "Semestral", "Anual"].index(doc['review_frequency']),
                key=f"doc_review_freq_{self.project_id}"
            )
        
        with col2:
            doc['next_review'] = st.date_input(
                "📅 Próxima Revisão:",
                value=datetime.fromisoformat(doc.get('next_review', (datetime.now() + timedelta(days=90)).date().isoformat())),
                key=f"doc_next_review_{self.project_id}"
            ).isoformat()
        
        # Histórico de revisões
        st.markdown("##### 📚 Histórico de Revisões")
        
        if 'revision_history' not in doc:
            doc['revision_history'] = []
        
        # Adicionar revisão
        with st.expander("➕ Adicionar Revisão"):
            col1, col2 = st.columns(2)
            
            with col1:
                revision_version = st.text_input(
                    "Versão:",
                    key=f"revision_version_{self.project_id}",
                    placeholder="Ex: 1.0, 1.1, 2.0"
                )
                
                revision_author = st.text_input(
                    "Autor:",
                    key=f"revision_author_{self.project_id}"
                )
            
            with col2:
                revision_date = st.date_input(
                    "Data:",
                    key=f"revision_date_{self.project_id}"
                )
            
            revision_changes = st.text_area(
                "Alterações:",
                key=f"revision_changes_{self.project_id}",
                placeholder="Descreva as alterações feitas nesta revisão...",
                height=80
            )
            
            if st.button("📚 Adicionar Revisão", key=f"add_revision_{self.project_id}"):
                if revision_version.strip() and revision_changes.strip():
                    doc['revision_history'].append({
                        'version': revision_version,
                        'date': revision_date.isoformat(),
                        'author': revision_author,
                        'changes': revision_changes,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Revisão {revision_version} adicionada!")
                    st.rerun()
                else:
                    st.error("❌ Versão e alterações são obrigatórias")
        
        # Mostrar histórico
        if doc.get('revision_history'):
            for i, revision in enumerate(doc['revision_history']):
                with st.expander(f"📖 Versão {revision['version']} - {revision['date']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Autor:** {revision.get('author', 'N/A')}")
                        st.write(f"**Alterações:** {revision['changes']}")
                    
                    with col2:
                        if st.button("🗑️", key=f"remove_revision_{i}_{self.project_id}"):
                            doc['revision_history'].pop(i)
                            st.rerun()
    
    def _show_action_buttons(self, control_data: Dict):
        """Botões de ação"""
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Salvar Plano", key=f"save_{self.tool_name}_{self.project_id}"):
                success = self.manager.save_tool_data(self.tool_name, control_data, completed=False)
                if success:
                    st.success("💾 Plano de controle salvo!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("📋 Gerar Relatório", key=f"report_{self.tool_name}_{self.project_id}"):
                self._generate_control_report(control_data)
        
        with col3:
            if st.button("✅ Finalizar Plano", key=f"complete_{self.tool_name}_{self.project_id}"):
                if self._validate_control_plan(control_data):
                    success = self.manager.save_tool_data(self.tool_name, control_data, completed=True)
                    if success:
                        st.success("✅ Plano de controle finalizado!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao finalizar")
                else:
                    st.error("❌ Complete os requisitos mínimos")
    
    def _generate_control_report(self, control_data: Dict):
        """Gera relatório do plano de controle"""
        st.markdown("### 📋 Relatório do Plano de Controle")
        
        # Resumo executivo
        points = control_data.get('control_points', [])
        schedule = control_data.get('monitoring_schedule', [])
        plans = control_data.get('response_plans', [])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Pontos de Controle", len(points))
        
        with col2:
            st.metric("Eventos Agendados", len(schedule))
        
        with col3:
            st.metric("Planos de Resposta", len(plans))
        
        # Detalhes do relatório
        report_content = f"""
        # Plano de Controle - Relatório
        
        **Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
        
        ## Resumo Executivo
        - **Pontos de Controle Definidos:** {len(points)}
        - **Eventos de Monitoramento:** {len(schedule)}
        - **Planos de Resposta:** {len(plans)}
        
        ## Pontos de Controle
        """
        
        for point in points:
            report_content += f"""
        ### {point['name']}
        - **Métrica:** {point['metric']} ({point.get('unit', '')})
        - **Meta:** {point.get('target', 0)}
        - **Limites:** {point.get('lower_limit', 0)} - {point.get('upper_limit', 0)}
        - **Responsável:** {point.get('responsible', 'Não definido')}
        - **Frequência:** {point.get('frequency', 'N/A')}
        """
        
        st.download_button(
            "📥 Baixar Relatório",
            data=report_content,
            file_name=f"plano_controle_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )
    
    def _validate_control_plan(self, control_data: Dict) -> bool:
        """Valida se o plano de controle está completo"""
        # Verificar pontos de controle
        if not control_data.get('control_points'):
            st.error("❌ Defina pelo menos um ponto de controle")
            return False
        
        # Verificar se há pontos ativos
        active_points = [p for p in control_data['control_points'] if p.get('status') == 'Ativo']
        if not active_points:
            st.error("❌ Pelo menos um ponto de controle deve estar ativo")
            return False
        
        # Verificar se há responsáveis definidos
        points_without_responsible = [p for p in active_points if not p.get('responsible', '').strip()]
        if points_without_responsible:
            st.error(f"❌ {len(points_without_responsible)} ponto(s) sem responsável")
            return False
        
        # Verificar documentação básica
        doc = control_data.get('documentation', {})
        if not doc.get('objective') or not doc.get('scope'):
            st.error("❌ Complete a documentação básica (objetivo e escopo)")
            return False
        
        return True


def show_control_phase():
    """Interface principal da fase Control"""
    st.title("🎮 Fase CONTROL")
    st.markdown("Controle e sustente as melhorias implementadas no processo.")
    
    # Verificar se há projeto selecionado
    if 'current_project' not in st.session_state or not st.session_state.current_project:
        st.warning("⚠️ Selecione um projeto primeiro")
        return
    
    project_data = st.session_state.current_project
    
    # Verificar se a fase Improve foi concluída
    improve_data = project_data.get('improve', {})
    improve_completed = any(tool.get('completed', False) for tool in improve_data.values() if isinstance(tool, dict))
    
    if not improve_completed:
        st.warning("⚠️ **A fase Improve deve ser concluída antes do Control**")
        st.info("💡 Complete pelo menos uma ferramenta da fase Improve para prosseguir")
        return
    
    # Inicializar gerenciador da fase
    control_manager = ControlPhaseManager(project_data)
    
    # Menu de ferramentas
    st.markdown("## 🛠️ Ferramentas da Fase Control")
    
    tools = [
        ("📊 Plano de Controle", "control_plan", ControlPlanTool),
        ("📈 Monitoramento Estatístico", "statistical_monitoring", None),  # Futuro
        ("📋 Documentação Padrão", "standard_documentation", None),        # Futuro
        ("🔄 Auditoria de Sustentabilidade", "sustainability_audit", None) # Futuro
    ]
    
    # Mostrar status das ferramentas
    col1, col2, col3, col4 = st.columns(4)
    
    for i, (tool_name, tool_key, tool_class) in enumerate(tools):
        col = [col1, col2, col3, col4][i]
        with col:
            if tool_class:
                is_completed = control_manager.is_tool_completed(tool_key)
                if is_completed:
                    st.success(f"✅ {tool_name.split(' ', 1)[1]}")
                else:
                    st.info(f"⏳ {tool_name.split(' ', 1)[1]}")
            else:
                st.info(f"🚧 {tool_name.split(' ', 1)[1]}")
    
    # Seleção de ferramenta
    available_tools = [t for t in tools if t[2] is not None]
    
    if available_tools:
        selected_tool = st.selectbox(
            "Selecione uma ferramenta:",
            available_tools,
            format_func=lambda x: x[0]
        )
        
        if selected_tool:
            tool_name, tool_key, tool_class = selected_tool
            
            st.divider()
            
            # Instanciar e mostrar ferramenta
            tool_instance = tool_class(control_manager)
            tool_instance.show()
    else:
        st.info("🚧 Ferramentas da fase Control em desenvolvimento")


if __name__ == "__main__":
    show_control_phase()
