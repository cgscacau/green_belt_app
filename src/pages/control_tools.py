# control_tools_improved.py - VERSÃO COMPLETA E MELHORADA
# Todas as 4 ferramentas da fase Control implementadas com salvamento robusto

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import warnings

warnings.filterwarnings('ignore')

# Import do ProjectManager
try:
    from src.utils.project_manager import ProjectManager
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
            # Converter numpy types
            data = self._clean_numpy_types(data)
            
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
    
    def _clean_numpy_types(self, obj):
        """Remove tipos numpy para compatibilidade com Firebase"""
        if isinstance(obj, dict):
            return {k: self._clean_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_numpy_types(item) for item in obj]
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
        else:
            return obj
    
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
    """Ferramenta para Plano de Controle - VERSÃO MELHORADA"""
    
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
    
    def _show_control_points(self, control_data: Dict):
        """Gerenciamento de pontos de controle - VERSÃO MELHORADA"""
        st.markdown("#### 🎯 Pontos de Controle")
        
        # Adicionar novo ponto de controle
        with st.expander("➕ Adicionar Novo Ponto de Controle"):
            col1, col2 = st.columns(2)
            
            with col1:
                point_name = st.text_input(
                    "Nome do Ponto de Controle *",
                    key=f"new_point_name_{self.project_id}"
                )
                
                metric_name = st.text_input(
                    "Métrica/Variável *",
                    key=f"new_point_metric_{self.project_id}"
                )
                
                unit = st.text_input(
                    "Unidade de Medida",
                    key=f"new_point_unit_{self.project_id}"
                )
                
                frequency = st.selectbox(
                    "Frequência de Medição",
                    ["Diária", "Semanal", "Quinzenal", "Mensal"],
                    key=f"new_point_frequency_{self.project_id}"
                )
            
            with col2:
                target = st.number_input(
                    "Meta (Valor Alvo) *",
                    key=f"new_point_target_{self.project_id}",
                    step=0.01,
                    format="%.2f"
                )
                
                lower_limit = st.number_input(
                    "Limite Inferior de Controle (LSL) *",
                    key=f"new_point_lsl_{self.project_id}",
                    step=0.01,
                    format="%.2f"
                )
                
                upper_limit = st.number_input(
                    "Limite Superior de Controle (USL) *",
                    key=f"new_point_usl_{self.project_id}",
                    step=0.01,
                    format="%.2f"
                )
                
                responsible = st.text_input(
                    "Responsável *",
                    key=f"new_point_responsible_{self.project_id}"
                )
            
            description = st.text_area(
                "Descrição/Como Medir",
                key=f"new_point_description_{self.project_id}",
                placeholder="Descreva como este ponto de controle deve ser medido e monitorado..."
            )
            
            method = st.text_input(
                "Método de Medição",
                key=f"new_point_method_{self.project_id}",
                placeholder="Ex: Sistema ERP, Medição manual, Inspeção visual"
            )
            
            if st.button("➕ Adicionar Ponto de Controle", key=f"add_control_point_{self.project_id}"):
                if (point_name.strip() and metric_name.strip() and responsible.strip() and 
                    target is not None and lower_limit is not None and upper_limit is not None):
                    
                    control_data['control_points'].append({
                        'name': point_name.strip(),
                        'metric': metric_name.strip(),
                        'unit': unit,
                        'target': float(target),
                        'lower_limit': float(lower_limit),
                        'upper_limit': float(upper_limit),
                        'frequency': frequency,
                        'responsible': responsible.strip(),
                        'description': description,
                        'measurement_method': method,
                        'status': 'Ativo',
                        'measurements': [],
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Ponto de controle '{point_name}' adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios (marcados com *)")
        
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
                        
                        # Adicionar medição rápida - CHAVES ÚNICAS
                        unique_measure_key = f"new_meas_point{i}_{self.project_id}_{hash(point['name'])}"
                        
                        new_value = st.number_input(
                            "Nova medição:",
                            key=unique_measure_key,
                            step=0.01
                        )
                        
                        if st.button("➕ Adicionar", key=f"add_meas_btn_point{i}_{self.project_id}"):
                            if 'measurements' not in control_data['control_points'][i]:
                                control_data['control_points'][i]['measurements'] = []
                            
                            control_data['control_points'][i]['measurements'].append({
                                'date': datetime.now().date().isoformat(),
                                'value': float(new_value),
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
                    
                    # GERENCIAR MEDIÇÕES EXISTENTES - CHAVES ÚNICAS OTIMIZADAS
                    measurements = point.get('measurements', [])
                    if measurements:
                        st.markdown("---")
                        st.markdown("##### 📋 Medições Registradas")
                        
                        # Botão para atualizar
                        if st.button("🔄 Atualizar Medições", key=f"refresh_point_{i}_{self.project_id}"):
                            st.rerun()
                        
                        # Processar cada medição com ID único
                        for measure_idx, measurement in enumerate(measurements):
                            # ID único usando hash do ponto + índice + timestamp
                            measurement_id = hash(f"{point['name']}_{measure_idx}_{measurement.get('added_at')}")
                            unique_id = f"pt{i}_ms{measure_idx}_{self.project_id}_{measurement_id}"
                            
                            edit_key = f"edit_{unique_id}"
                            delete_key = f"del_{unique_id}"
                            
                            measurement_date_str = datetime.fromisoformat(measurement['date']).strftime('%d/%m/%Y')
                            
                            # Container para cada medição
                            with st.container():
                                is_editing = st.session_state.get(edit_key, False)
                                
                                if is_editing:
                                    # MODO EDIÇÃO
                                    st.markdown(f"**✏️ Editando medição de {measurement_date_str}:**")
                                    
                                    col_edit1, col_edit2, col_edit3 = st.columns([2, 2, 2])
                                    
                                    with col_edit1:
                                        edited_date = st.date_input(
                                            "Nova Data:",
                                            value=datetime.fromisoformat(measurement['date']).date(),
                                            key=f"ed_date_{unique_id}"
                                        )
                                    
                                    with col_edit2:
                                        edited_value = st.number_input(
                                            f"Novo Valor ({point.get('unit', '')}):",
                                            value=float(measurement['value']),
                                            key=f"ed_val_{unique_id}",
                                            step=0.01,
                                            format="%.2f"
                                        )
                                    
                                    with col_edit3:
                                        col_save, col_cancel = st.columns(2)
                                        
                                        with col_save:
                                            if st.button("💾", key=f"save_{unique_id}", help="Salvar"):
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
                                            if st.button("❌", key=f"cancel_{unique_id}", help="Cancelar"):
                                                if edit_key in st.session_state:
                                                    del st.session_state[edit_key]
                                                st.rerun()
                                
                                else:
                                    # MODO VISUALIZAÇÃO
                                    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
                                    
                                    with col1:
                                        st.write(f"📅 **{measurement_date_str}**")
                                    
                                    with col2:
                                        st.write(f"**{measurement['value']} {point.get('unit', '')}**")
                                    
                                    with col3:
                                        status = measurement.get('status', 'OK')
                                        if status == 'OK':
                                            st.success("✅")
                                        elif status == 'WARNING':
                                            st.warning("⚠️")
                                        else:
                                            st.error("🚨")
                                    
                                    with col4:
                                        if st.button("✏️", key=f"edit_btn_{unique_id}", help="Editar"):
                                            st.session_state[edit_key] = True
                                            st.rerun()
                                    
                                    with col5:
                                        # DELETE COM CONFIRMAÇÃO
                                        if st.button("🗑️", key=f"del_btn_{unique_id}", help="Excluir"):
                                            if st.session_state.get(delete_key, False):
                                                try:
                                                    # Remover diretamente
                                                    control_data['control_points'][i]['measurements'].pop(measure_idx)
                                                    
                                                    # Limpar estados relacionados
                                                    for key in list(st.session_state.keys()):
                                                        if unique_id in key:
                                                            del st.session_state[key]
                                                    
                                                    st.success(f"✅ Medição removida!")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"❌ Erro: {str(e)}")
                                            else:
                                                st.session_state[delete_key] = True
                                                st.warning("⚠️ Clique novamente para confirmar")
                                
                                # Separador
                                if measure_idx < len(measurements) - 1:
                                    st.divider()
                        
                        # Botão de limpeza de emergência
                        if st.button("🧹 Limpar Estados", key=f"emergency_clear_point_{i}_{self.project_id}"):
                            keys_to_remove = [k for k in st.session_state.keys() if f"pt{i}_" in k]
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
            if target != 0 and abs(value - target) / abs(target) <= 0.05:  # 5% da meta
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
                        num_events = 30
                    elif frequency == 'Semanal':
                        days_interval = 7
                        num_events = 12
                    elif frequency == 'Quinzenal':
                        days_interval = 14
                        num_events = 8
                    else:  # Mensal
                        days_interval = 30
                        num_events = 6
                    
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
            for i, event in enumerate(filtered_schedule[:20]):
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


# ==============================================
# NOVAS FERRAMENTAS DA FASE CONTROL
# ==============================================

class StatisticalProcessControlTool:
    """Ferramenta de Controle Estatístico de Processo (CEP)"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "statistical_monitoring"
    
    def show(self):
        st.markdown("## 📈 Controle Estatístico de Processo (CEP)")
        st.markdown("Monitore o processo usando gráficos de controle estatístico (Shewhart, CUSUM, EWMA).")
        
        # Status da ferramenta
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ **CEP configurado**")
        else:
            st.info("⏳ **CEP em configuração**")
        
        # Inicializar dados
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data if existing_data else {
                'control_charts': [],
                'rules_violations': []
            }
        
        cep_data = st.session_state[session_key]
        
        # Obter pontos de controle disponíveis
        control_plan_data = self.manager.get_tool_data('control_plan')
        control_points = control_plan_data.get('control_points', [])
        
        if not control_points:
            st.warning("⚠️ Defina pontos de controle primeiro no Plano de Controle")
            return
        
        # Seleção de ponto de controle para CEP
        st.markdown("### 📊 Configurar Gráfico de Controle")
        
        col1, col2 = st.columns(2)
        
        with col1:
            point_names = [p['name'] for p in control_points]
            selected_point_name = st.selectbox(
                "Ponto de Controle:",
                point_names,
                key=f"cep_point_{self.project_id}"
            )
            
            selected_point = next((p for p in control_points if p['name'] == selected_point_name), None)
        
        with col2:
            chart_type = st.selectbox(
                "Tipo de Gráfico:",
                ["X-barra e R", "Individuals (I-MR)", "P (Proporção)", "C (Contagem)", "CUSUM", "EWMA"],
                key=f"cep_chart_type_{self.project_id}"
            )
        
        if selected_point and selected_point.get('measurements'):
            measurements = selected_point['measurements']
            
            if len(measurements) < 5:
                st.warning("⚠️ Necessário pelo menos 5 medições para criar gráfico de controle")
                return
            
            # Extrair dados
            dates = [datetime.fromisoformat(m['date']) for m in measurements]
            values = [float(m['value']) for m in measurements]
            
            # Calcular limites de controle
            mean = np.mean(values)
            std = np.std(values)
            ucl = mean + 3 * std
            lcl = mean - 3 * std
            
            # Criar gráfico de controle
            fig = go.Figure()
            
            # Dados
            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='lines+markers',
                name='Medições',
                line=dict(color='blue'),
                marker=dict(size=8)
            ))
            
            # Linha central
            fig.add_hline(y=mean, line_dash="solid", line_color="green", 
                         annotation_text="Média", annotation_position="right")
            
            # Limites de controle
            fig.add_hline(y=ucl, line_dash="dash", line_color="red", 
                         annotation_text="LSC", annotation_position="right")
            fig.add_hline(y=lcl, line_dash="dash", line_color="red", 
                         annotation_text="LIC", annotation_position="right")
            
            # Limites de especificação (se existirem)
            if selected_point.get('upper_limit'):
                fig.add_hline(y=selected_point['upper_limit'], line_dash="dot", line_color="orange", 
                             annotation_text="USL", annotation_position="right")
            
            if selected_point.get('lower_limit'):
                fig.add_hline(y=selected_point['lower_limit'], line_dash="dot", line_color="orange", 
                             annotation_text="LSL", annotation_position="right")
            
            fig.update_layout(
                title=f"Gráfico de Controle - {selected_point_name} ({chart_type})",
                xaxis_title="Data",
                yaxis_title=f"{selected_point['metric']} ({selected_point.get('unit', '')})",
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Análise de regras de controle
            st.markdown("### 🔍 Análise de Regras de Controle")
            
            violations = self._check_control_rules(values, mean, std, ucl, lcl)
            
            if violations:
                st.warning(f"⚠️ **{len(violations)} violação(ões) detectada(s):**")
                for violation in violations:
                    st.write(f"• {violation}")
                
                cep_data['rules_violations'] = violations
            else:
                st.success("✅ Nenhuma violação das regras de controle detectada")
            
            # Estatísticas do processo
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Média", f"{mean:.2f}")
            
            with col2:
                st.metric("Desvio Padrão", f"{std:.2f}")
            
            with col3:
                st.metric("LSC", f"{ucl:.2f}")
            
            with col4:
                st.metric("LIC", f"{lcl:.2f}")
            
            # Salvar configuração do gráfico
            if st.button("💾 Salvar Configuração CEP", key=f"save_cep_{self.project_id}"):
                chart_config = {
                    'point_name': selected_point_name,
                    'chart_type': chart_type,
                    'mean': float(mean),
                    'std': float(std),
                    'ucl': float(ucl),
                    'lcl': float(lcl),
                    'created_at': datetime.now().isoformat()
                }
                
                cep_data['control_charts'].append(chart_config)
                
                success = self.manager.save_tool_data(self.tool_name, cep_data, completed=True)
                if success:
                    st.success("✅ Configuração CEP salva!")
                    st.rerun()
        else:
            st.info("📝 Adicione medições ao ponto de controle para criar o gráfico CEP")
    
    def _check_control_rules(self, values: List[float], mean: float, std: float, ucl: float, lcl: float) -> List[str]:
        """Verifica regras de controle (Western Electric Rules)"""
        violations = []
        n = len(values)
        
        # Regra 1: Ponto fora dos limites de controle
        for i, val in enumerate(values):
            if val > ucl or val < lcl:
                violations.append(f"Regra 1: Ponto {i+1} fora dos limites de controle")
        
        # Regra 2: 2 de 3 pontos consecutivos além de 2σ
        sigma_2_upper = mean + 2 * std
        sigma_2_lower = mean - 2 * std
        
        for i in range(n - 2):
            points_beyond = sum(1 for j in range(i, i + 3) 
                               if values[j] > sigma_2_upper or values[j] < sigma_2_lower)
            if points_beyond >= 2:
                violations.append(f"Regra 2: Pontos {i+1}-{i+3} têm 2/3 além de 2σ")
        
        # Regra 3: 4 de 5 pontos consecutivos além de 1σ
        sigma_1_upper = mean + std
        sigma_1_lower = mean - std
        
        for i in range(n - 4):
            points_beyond = sum(1 for j in range(i, i + 5) 
                               if values[j] > sigma_1_upper or values[j] < sigma_1_lower)
            if points_beyond >= 4:
                violations.append(f"Regra 3: Pontos {i+1}-{i+5} têm 4/5 além de 1σ")
        
        # Regra 4: 8 pontos consecutivos de um lado da média
        for i in range(n - 7):
            if all(v > mean for v in values[i:i+8]) or all(v < mean for v in values[i:i+8]):
                violations.append(f"Regra 4: 8 pontos consecutivos de um lado da média (pontos {i+1}-{i+8})")
        
        return violations


class StandardDocumentationTool:
    """Ferramenta de Documentação de Procedimentos Padrão"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "standard_documentation"
    
    def show(self):
        st.markdown("## 📋 Procedimentos Operacionais Padrão (POP)")
        st.markdown("Documente os procedimentos padronizados para manter as melhorias implementadas.")
        
        # Status
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ **Documentação finalizada**")
        else:
            st.info("⏳ **Documentação em desenvolvimento**")
        
        # Inicializar dados
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data if existing_data else {
                'procedures': [],
                'work_instructions': [],
                'training_materials': []
            }
        
        doc_data = st.session_state[session_key]
        
        # Tabs para diferentes tipos de documentação
        tab1, tab2, tab3 = st.tabs([
            "📄 POPs",
            "📝 Instruções de Trabalho",
            "🎓 Material de Treinamento"
        ])
        
        with tab1:
            self._show_procedures(doc_data)
        
        with tab2:
            self._show_work_instructions(doc_data)
        
        with tab3:
            self._show_training_materials(doc_data)
        
        # Botões de ação
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Documentação", key=f"save_doc_{self.project_id}"):
                success = self.manager.save_tool_data(self.tool_name, doc_data, completed=False)
                if success:
                    st.success("💾 Documentação salva!")
        
        with col2:
            if st.button("✅ Finalizar Documentação", key=f"complete_doc_{self.project_id}"):
                if doc_data.get('procedures'):
                    success = self.manager.save_tool_data(self.tool_name, doc_data, completed=True)
                    if success:
                        st.success("✅ Documentação finalizada!")
                        st.balloons()
                        st.rerun()
                else:
                    st.error("❌ Adicione pelo menos um POP")
    
    def _show_procedures(self, doc_data: Dict):
        """Gerenciar POPs"""
        st.markdown("### 📄 Procedimentos Operacionais Padrão")
        
        # Adicionar novo POP
        with st.expander("➕ Adicionar Novo POP"):
            pop_title = st.text_input(
                "Título do POP *",
                key=f"pop_title_{self.project_id}"
            )
            
            pop_code = st.text_input(
                "Código do Documento",
                key=f"pop_code_{self.project_id}",
                placeholder="Ex: POP-001"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                pop_version = st.text_input(
                    "Versão",
                    value="1.0",
                    key=f"pop_version_{self.project_id}"
                )
            
            with col2:
                pop_author = st.text_input(
                    "Autor",
                    key=f"pop_author_{self.project_id}"
                )
            
            pop_objective = st.text_area(
                "Objetivo",
                key=f"pop_objective_{self.project_id}",
                placeholder="Objetivo deste procedimento...",
                height=80
            )
            
            pop_scope = st.text_area(
                "Escopo",
                key=f"pop_scope_{self.project_id}",
                placeholder="Onde este procedimento se aplica...",
                height=80
            )
            
            pop_steps = st.text_area(
                "Passos do Procedimento *",
                key=f"pop_steps_{self.project_id}",
                placeholder="1. Passo 1\n2. Passo 2\n3. Passo 3...",
                height=150
            )
            
            pop_references = st.text_area(
                "Referências/Documentos Relacionados",
                key=f"pop_references_{self.project_id}",
                height=60
            )
            
            if st.button("📄 Adicionar POP", key=f"add_pop_{self.project_id}"):
                if pop_title.strip() and pop_steps.strip():
                    doc_data['procedures'].append({
                        'title': pop_title,
                        'code': pop_code,
                        'version': pop_version,
                        'author': pop_author,
                        'objective': pop_objective,
                        'scope': pop_scope,
                        'steps': pop_steps,
                        'references': pop_references,
                        'status': 'Ativo',
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ POP '{pop_title}' adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Título e passos são obrigatórios")
        
        # Mostrar POPs existentes
        if doc_data.get('procedures'):
            st.markdown("#### 📋 POPs Criados")
            
            for i, pop in enumerate(doc_data['procedures']):
                with st.expander(f"📄 **{pop['title']}** - Versão {pop['version']}"):
                    st.write(f"**Código:** {pop.get('code', 'N/A')}")
                    st.write(f"**Autor:** {pop.get('author', 'N/A')}")
                    st.write(f"**Status:** {pop.get('status', 'Ativo')}")
                    
                    st.markdown("**Objetivo:**")
                    st.write(pop.get('objective', 'N/A'))
                    
                    st.markdown("**Escopo:**")
                    st.write(pop.get('scope', 'N/A'))
                    
                    st.markdown("**Procedimento:**")
                    st.text(pop.get('steps', ''))
                    
                    if pop.get('references'):
                        st.markdown("**Referências:**")
                        st.write(pop['references'])
                    
                    if st.button("🗑️ Remover", key=f"remove_pop_{i}_{self.project_id}"):
                        doc_data['procedures'].pop(i)
                        st.rerun()
        else:
            st.info("📄 Nenhum POP criado ainda")
    
    def _show_work_instructions(self, doc_data: Dict):
        """Instruções de trabalho detalhadas"""
        st.markdown("### 📝 Instruções de Trabalho")
        
        # Similar ao POP, mas mais simples
        with st.expander("➕ Adicionar Instrução de Trabalho"):
            wi_title = st.text_input(
                "Título da Instrução *",
                key=f"wi_title_{self.project_id}"
            )
            
            wi_task = st.text_input(
                "Tarefa/Atividade",
                key=f"wi_task_{self.project_id}"
            )
            
            wi_instructions = st.text_area(
                "Instruções Detalhadas *",
                key=f"wi_instructions_{self.project_id}",
                placeholder="Descreva passo a passo como executar a tarefa...",
                height=150
            )
            
            wi_safety = st.text_area(
                "Precauções de Segurança",
                key=f"wi_safety_{self.project_id}",
                placeholder="EPIs necessários, cuidados especiais...",
                height=80
            )
            
            if st.button("📝 Adicionar Instrução", key=f"add_wi_{self.project_id}"):
                if wi_title.strip() and wi_instructions.strip():
                    doc_data['work_instructions'].append({
                        'title': wi_title,
                        'task': wi_task,
                        'instructions': wi_instructions,
                        'safety': wi_safety,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Instrução '{wi_title}' adicionada!")
                    st.rerun()
                else:
                    st.error("❌ Título e instruções são obrigatórios")
        
        # Mostrar instruções
        if doc_data.get('work_instructions'):
            st.markdown("#### 📋 Instruções Criadas")
            
            for i, wi in enumerate(doc_data['work_instructions']):
                with st.expander(f"📝 **{wi['title']}**"):
                    if wi.get('task'):
                        st.write(f"**Tarefa:** {wi['task']}")
                    
                    st.markdown("**Instruções:**")
                    st.text(wi['instructions'])
                    
                    if wi.get('safety'):
                        st.markdown("**⚠️ Segurança:**")
                        st.write(wi['safety'])
                    
                    if st.button("🗑️ Remover", key=f"remove_wi_{i}_{self.project_id}"):
                        doc_data['work_instructions'].pop(i)
                        st.rerun()
        else:
            st.info("📝 Nenhuma instrução criada ainda")
    
    def _show_training_materials(self, doc_data: Dict):
        """Material de treinamento"""
        st.markdown("### 🎓 Material de Treinamento")
        
        with st.expander("➕ Adicionar Material de Treinamento"):
            tm_title = st.text_input(
                "Título do Material *",
                key=f"tm_title_{self.project_id}"
            )
            
            tm_type = st.selectbox(
                "Tipo de Material",
                ["Apresentação", "Vídeo", "Manual", "Quiz", "Checklist", "Outro"],
                key=f"tm_type_{self.project_id}"
            )
            
            tm_description = st.text_area(
                "Descrição/Conteúdo *",
                key=f"tm_description_{self.project_id}",
                height=120
            )
            
            tm_duration = st.number_input(
                "Duração Estimada (minutos)",
                min_value=5,
                max_value=480,
                value=30,
                key=f"tm_duration_{self.project_id}"
            )
            
            if st.button("🎓 Adicionar Material", key=f"add_tm_{self.project_id}"):
                if tm_title.strip() and tm_description.strip():
                    doc_data['training_materials'].append({
                        'title': tm_title,
                        'type': tm_type,
                        'description': tm_description,
                        'duration': tm_duration,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Material '{tm_title}' adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Título e descrição são obrigatórios")
        
        if doc_data.get('training_materials'):
            st.markdown("#### 📋 Materiais Criados")
            
            for i, tm in enumerate(doc_data['training_materials']):
                with st.expander(f"🎓 **{tm['title']}** ({tm['type']})"):
                    st.write(f"**Tipo:** {tm['type']}")
                    st.write(f"**Duração:** {tm['duration']} minutos")
                    
                    st.markdown("**Descrição:**")
                    st.write(tm['description'])
                    
                    if st.button("🗑️ Remover", key=f"remove_tm_{i}_{self.project_id}"):
                        doc_data['training_materials'].pop(i)
                        st.rerun()
        else:
            st.info("🎓 Nenhum material criado ainda")


class SustainabilityAuditTool:
    """Ferramenta de Auditoria de Sustentabilidade"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "sustainability_audit"
    
    def show(self):
        st.markdown("## 🔄 Auditoria de Sustentabilidade")
        st.markdown("Realize auditorias periódicas para garantir a sustentação das melhorias ao longo do tempo.")
        
        # Status
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ **Sistema de auditoria configurado**")
        else:
            st.info("⏳ **Sistema em configuração**")
        
        # Inicializar dados
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data if existing_data else {
                'audit_schedule': [],
                'audits_completed': [],
                'findings': []
            }
        
        audit_data = st.session_state[session_key]
        
        # Tabs para diferentes aspectos da auditoria
        tab1, tab2, tab3 = st.tabs([
            "📅 Cronograma de Auditorias",
            "📋 Realizar Auditoria",
            "📊 Resultados e Tendências"
        ])
        
        with tab1:
            self._show_audit_schedule(audit_data)
        
        with tab2:
            self._show_conduct_audit(audit_data)
        
        with tab3:
            self._show_audit_results(audit_data)
        
        # Botões de ação
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Configuração", key=f"save_audit_{self.project_id}"):
                success = self.manager.save_tool_data(self.tool_name, audit_data, completed=False)
                if success:
                    st.success("💾 Configuração salva!")
        
        with col2:
            if st.button("✅ Finalizar Configuração", key=f"complete_audit_{self.project_id}"):
                if audit_data.get('audit_schedule'):
                    success = self.manager.save_tool_data(self.tool_name, audit_data, completed=True)
                    if success:
                        st.success("✅ Sistema de auditoria configurado!")
                        st.balloons()
                        st.rerun()
                else:
                    st.error("❌ Configure o cronograma de auditorias")
    
    def _show_audit_schedule(self, audit_data: Dict):
        """Cronograma de auditorias"""
        st.markdown("### 📅 Cronograma de Auditorias")
        
        # Configurar frequência de auditorias
        col1, col2 = st.columns(2)
        
        with col1:
            audit_frequency = st.selectbox(
                "Frequência de Auditorias:",
                ["Mensal", "Trimestral", "Semestral", "Anual"],
                key=f"audit_frequency_{self.project_id}"
            )
        
        with col2:
            auditor = st.text_input(
                "Auditor Responsável:",
                key=f"auditor_{self.project_id}"
            )
        
        if st.button("📅 Gerar Cronograma", key=f"gen_audit_schedule_{self.project_id}"):
            # Gerar próximas auditorias baseado na frequência
            start_date = datetime.now().date()
            
            if audit_frequency == "Mensal":
                intervals = [30 * i for i in range(1, 13)]
            elif audit_frequency == "Trimestral":
                intervals = [90 * i for i in range(1, 5)]
            elif audit_frequency == "Semestral":
                intervals = [180 * i for i in range(1, 3)]
            else:  # Anual
                intervals = [365]
            
            schedule = []
            for interval in intervals:
                audit_date = start_date + timedelta(days=interval)
                schedule.append({
                    'date': audit_date.isoformat(),
                    'auditor': auditor,
                    'status': 'Agendada',
                    'created_at': datetime.now().isoformat()
                })
            
            audit_data['audit_schedule'] = schedule
            st.success(f"✅ Cronograma gerado com {len(schedule)} auditorias!")
            st.rerun()
        
        # Mostrar cronograma
        if audit_data.get('audit_schedule'):
            st.markdown("#### 📋 Auditorias Agendadas")
            
            for i, audit in enumerate(audit_data['audit_schedule']):
                audit_date = datetime.fromisoformat(audit['date'])
                status_icon = "🟢" if audit['status'] == 'Concluída' else "🟡"
                
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"{status_icon} **{audit_date.strftime('%d/%m/%Y')}**")
                
                with col2:
                    st.write(f"Auditor: {audit.get('auditor', 'N/A')}")
                
                with col3:
                    st.write(f"Status: {audit['status']}")
        else:
            st.info("📅 Nenhuma auditoria agendada")
    
    def _show_conduct_audit(self, audit_data: Dict):
        """Realizar auditoria"""
        st.markdown("### 📋 Realizar Auditoria")
        
        # Checklist de auditoria
        st.markdown("#### ✅ Checklist de Verificação")
        
        audit_date = st.date_input(
            "Data da Auditoria:",
            value=datetime.now().date(),
            key=f"current_audit_date_{self.project_id}"
        )
        
        auditor_name = st.text_input(
            "Nome do Auditor:",
            key=f"current_auditor_{self.project_id}"
        )
        
        # Categorias de verificação
        st.markdown("**Pontos de Verificação:**")
        
        checks = {}
        
        check_categories = [
            ("Documentação", [
                "POPs estão atualizados e disponíveis",
                "Registros de controle estão sendo mantidos",
                "Treinamentos foram realizados"
            ]),
            ("Processo", [
                "Processo está sendo seguido conforme definido",
                "Medições estão sendo feitas na frequência correta",
                "Limites de controle estão sendo respeitados"
            ]),
            ("Resultados", [
                "Metas estão sendo atingidas",
                "Melhorias estão sendo sustentadas",
                "Não houve regressão do processo"
            ]),
            ("Pessoas", [
                "Equipe está treinada e capacitada",
                "Responsabilidades estão claras",
                "Engajamento da equipe é adequado"
            ])
        ]
        
        for category, items in check_categories:
            st.markdown(f"**{category}:**")
            
            for item in items:
                check_key = f"{category}_{item}"
                checks[check_key] = st.checkbox(
                    item,
                    key=f"check_{hash(check_key)}_{self.project_id}"
                )
        
        # Observações e achados
        findings = st.text_area(
            "Achados e Observações:",
            key=f"audit_findings_{self.project_id}",
            placeholder="Descreva não-conformidades, oportunidades de melhoria, observações...",
            height=150
        )
        
        # Ações corretivas
        corrective_actions = st.text_area(
            "Ações Corretivas Recomendadas:",
            key=f"corrective_actions_{self.project_id}",
            placeholder="Liste as ações necessárias para corrigir não-conformidades...",
            height=100
        )
        
        # Conclusão da auditoria
        audit_conclusion = st.selectbox(
            "Conclusão:",
            ["Conforme", "Conforme com observações", "Não conforme"],
            key=f"audit_conclusion_{self.project_id}"
        )
        
        if st.button("📝 Registrar Auditoria", key=f"register_audit_{self.project_id}"):
            # Calcular score
            total_checks = len(checks)
            passed_checks = sum(1 for v in checks.values() if v)
            score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
            
            audit_record = {
                'date': audit_date.isoformat(),
                'auditor': auditor_name,
                'checks': checks,
                'score': float(score),
                'findings': findings,
                'corrective_actions': corrective_actions,
                'conclusion': audit_conclusion,
                'created_at': datetime.now().isoformat()
            }
            
            audit_data['audits_completed'].append(audit_record)
            
            # Atualizar cronograma
            for scheduled in audit_data.get('audit_schedule', []):
                if scheduled['date'] == audit_date.isoformat():
                    scheduled['status'] = 'Concluída'
            
            st.success(f"✅ Auditoria registrada! Score: {score:.1f}%")
            st.rerun()
    
    def _show_audit_results(self, audit_data: Dict):
        """Resultados e tendências"""
        st.markdown("### 📊 Resultados e Tendências")
        
        audits = audit_data.get('audits_completed', [])
        
        if not audits:
            st.info("📊 Nenhuma auditoria realizada ainda")
            return
        
        # Gráfico de tendência de scores
        dates = [datetime.fromisoformat(a['date']) for a in audits]
        scores = [a['score'] for a in audits]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=scores,
            mode='lines+markers',
            name='Score da Auditoria',
            line=dict(color='blue', width=3),
            marker=dict(size=10)
        ))
        
        # Linha de referência 80%
        fig.add_hline(y=80, line_dash="dash", line_color="green", 
                     annotation_text="Meta: 80%", annotation_position="right")
        
        fig.update_layout(
            title="Tendência dos Scores de Auditoria",
            xaxis_title="Data",
            yaxis_title="Score (%)",
            yaxis_range=[0, 100],
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Auditorias Realizadas", len(audits))
        
        with col2:
            avg_score = np.mean(scores)
            st.metric("Score Médio", f"{avg_score:.1f}%")
        
        with col3:
            last_score = scores[-1]
            st.metric("Última Auditoria", f"{last_score:.1f}%")
        
        with col4:
            conformes = sum(1 for a in audits if a.get('conclusion') == 'Conforme')
            st.metric("Conformes", f"{conformes}/{len(audits)}")
        
        # Detalhes das auditorias
        st.markdown("#### 📋 Histórico de Auditorias")
        
        for i, audit in enumerate(reversed(audits)):
            audit_date = datetime.fromisoformat(audit['date'])
            
            conclusion_colors = {
                'Conforme': '🟢',
                'Conforme com observações': '🟡',
                'Não conforme': '🔴'
            }
            
            color_icon = conclusion_colors.get(audit['conclusion'], '⚪')
            
            with st.expander(f"{color_icon} **{audit_date.strftime('%d/%m/%Y')}** - Score: {audit['score']:.1f}%"):
                st.write(f"**Auditor:** {audit.get('auditor', 'N/A')}")
                st.write(f"**Conclusão:** {audit['conclusion']}")
                
                if audit.get('findings'):
                    st.markdown("**Achados:**")
                    st.write(audit['findings'])
                
                if audit.get('corrective_actions'):
                    st.markdown("**Ações Corretivas:**")
                    st.write(audit['corrective_actions'])


# ==============================================
# FUNÇÃO PRINCIPAL DA FASE CONTROL
# ==============================================

def show_control_phase():
    """Interface principal da fase Control - VERSÃO COMPLETA"""
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
        ("📈 Controle Estatístico (CEP)", "statistical_monitoring", StatisticalProcessControlTool),
        ("📋 Documentação Padrão (POP)", "standard_documentation", StandardDocumentationTool),
        ("🔄 Auditoria de Sustentabilidade", "sustainability_audit", SustainabilityAuditTool)
    ]
    
    # Mostrar status das ferramentas
    col1, col2, col3, col4 = st.columns(4)
    
    for i, (tool_name, tool_key, tool_class) in enumerate(tools):
        col = [col1, col2, col3, col4][i]
        with col:
            is_completed = control_manager.is_tool_completed(tool_key)
            if is_completed:
                st.success(f"✅ {tool_name.split(' ', 1)[1]}")
            else:
                st.info(f"⏳ {tool_name.split(' ', 1)[1]}")
    
    # Seleção de ferramenta
    selected_tool = st.selectbox(
        "Selecione uma ferramenta:",
        tools,
        format_func=lambda x: x[0]
    )
    
    if selected_tool:
        tool_name, tool_key, tool_class = selected_tool
        
        st.divider()
        
        # Instanciar e mostrar ferramenta
        tool_instance = tool_class(control_manager)
        tool_instance.show()


if __name__ == "__main__":
    show_control_phase()
