import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date
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

# Import das funções de formatação
try:
    from src.utils.formatters import (
        format_currency,
        format_date_br,
        format_number_br,
        parse_currency_input,
        validate_currency_input,
        format_date_input,
        parse_date_input
    )
except ImportError:
    st.error("❌ Não foi possível importar funções de formatação")
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

####################################################################################################################################################################################################
    
def _show_control_points(self, control_data: Dict):
    """Gerenciamento de pontos de controle - VERSÃO ULTRA SIMPLIFICADA"""
    st.markdown("#### 🎯 Pontos de Controle")
    
    # Inicializar lista se não existir
    if 'control_points' not in control_data or control_data['control_points'] is None:
        control_data['control_points'] = []
    
    # ========== ADICIONAR NOVO PONTO DE CONTROLE ==========
    with st.expander("➕ Adicionar Ponto de Controle"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_point_name = st.text_input("Nome *", key=f"new_point_name_{self.project_id}")
            new_metric = st.text_input("Métrica *", key=f"new_metric_{self.project_id}")
            new_unit = st.text_input("Unidade", key=f"new_unit_{self.project_id}")
            new_target = st.number_input("Meta", key=f"new_target_{self.project_id}", step=0.01)
        
        with col2:
            new_lower = st.number_input("Limite Inferior", key=f"new_lower_{self.project_id}", step=0.01)
            new_upper = st.number_input("Limite Superior", key=f"new_upper_{self.project_id}", step=0.01)
            new_frequency = st.selectbox("Frequência", ["Diária", "Semanal", "Quinzenal", "Mensal"], key=f"new_freq_{self.project_id}")
            new_responsible = st.text_input("Responsável", key=f"new_resp_{self.project_id}")
        
        if st.button("➕ Adicionar Ponto", key=f"add_point_{self.project_id}"):
            if new_point_name.strip() and new_metric.strip():
                control_data['control_points'].append({
                    'name': new_point_name.strip(),
                    'metric': new_metric.strip(),
                    'unit': new_unit.strip(),
                    'target': new_target,
                    'lower_limit': new_lower,
                    'upper_limit': new_upper,
                    'frequency': new_frequency,
                    'responsible': new_responsible.strip(),
                    'status': 'Ativo',
                    'measurements': [],
                    'created_at': datetime.now().isoformat()
                })
                self.manager.save_tool_data(self.tool_name, control_data, completed=False)
                st.success("✅ Ponto adicionado!")
                st.rerun()
    
    # ========== MOSTRAR PONTOS EXISTENTES ==========
    if not control_data.get('control_points'):
        st.info("🎯 Nenhum ponto de controle definido.")
        return
    
    # Selecionar ponto para trabalhar
    point_names = [f"{i}. {p['name']}" for i, p in enumerate(control_data['control_points'])]
    
    selected_point_label = st.selectbox(
        "🎯 Selecione um Ponto de Controle:",
        point_names,
        key=f"select_point_{self.project_id}"
    )
    
    if not selected_point_label:
        return
    
    # Extrair índice
    point_idx = int(selected_point_label.split('.')[0])
    point = control_data['control_points'][point_idx]
    
    # ========== EXIBIR INFORMAÇÕES DO PONTO ==========
    st.markdown(f"### 📊 {point['name']}")
    
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.metric("Métrica", f"{point['metric']} ({point.get('unit', '')})")
        st.metric("Meta", point.get('target', 0))
    
    with col_info2:
        st.metric("Limite Inferior", point.get('lower_limit', 0))
        st.metric("Limite Superior", point.get('upper_limit', 0))
    
    with col_info3:
        st.metric("Frequência", point.get('frequency', 'N/A'))
        st.metric("Responsável", point.get('responsible', 'N/A'))
    
    st.divider()
    
    # ========== ABAS: ADICIONAR / VISUALIZAR / GERENCIAR ==========
    tab1, tab2, tab3 = st.tabs(["➕ Adicionar Medição", "📊 Visualizar Gráfico", "📋 Gerenciar Medições"])
    
    # ========== TAB 1: ADICIONAR MEDIÇÃO ==========
    with tab1:
        st.markdown("#### ➕ Nova Medição")
        
        col_add1, col_add2, col_add3 = st.columns([2, 2, 1])
        
        with col_add1:
            add_date_input = st.text_input(
                "📅 Data:",
                value=format_date_input(datetime.now().date()),
                key=f"add_date_{point_idx}",
                placeholder="DD/MM/AAAA"
            )
        
        with col_add2:
            add_value = st.number_input(
                f"Valor ({point.get('unit', '')}):",
                key=f"add_value_{point_idx}",
                step=0.01,
                value=0.0
            )
        
        with col_add3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Adicionar", key=f"btn_add_{point_idx}", use_container_width=True):
                add_date, is_valid, error = parse_date_input(add_date_input)
                
                if not is_valid:
                    st.error(f"❌ {error}")
                else:
                    if 'measurements' not in control_data['control_points'][point_idx]:
                        control_data['control_points'][point_idx]['measurements'] = []
                    
                    status = self._check_control_status(add_value, point)
                    
                    control_data['control_points'][point_idx]['measurements'].append({
                        'date': add_date.isoformat(),
                        'value': float(add_value),
                        'status': status,
                        'added_at': datetime.now().isoformat()
                    })
                    
                    self.manager.save_tool_data(self.tool_name, control_data, completed=False)
                    st.success(f"✅ Medição adicionada: {format_date_br(add_date.isoformat())} - {add_value}")
                    st.rerun()
    
    # ========== TAB 2: VISUALIZAR GRÁFICO ==========
    with tab2:
        measurements = point.get('measurements', [])
        
        if not measurements or len(measurements) < 2:
            st.info("📊 Adicione pelo menos 2 medições para visualizar o gráfico.")
        else:
            st.markdown("#### 📈 Gráfico de Controle")
            
            dates = [datetime.fromisoformat(m['date']) for m in measurements]
            values = [m['value'] for m in measurements]
            
            target = point.get('target', 0)
            upper = point.get('upper_limit', 0)
            lower = point.get('lower_limit', 0)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(x=dates, y=values, mode='lines+markers', name='Valores', line=dict(color='blue', width=2)))
            fig.add_trace(go.Scatter(x=[dates[0], dates[-1]], y=[target, target], mode='lines', name='Meta', line=dict(color='green', dash='dash')))
            fig.add_trace(go.Scatter(x=[dates[0], dates[-1]], y=[upper, upper], mode='lines', name='LSC', line=dict(color='red', dash='dot')))
            fig.add_trace(go.Scatter(x=[dates[0], dates[-1]], y=[lower, lower], mode='lines', name='LIC', line=dict(color='red', dash='dot')))
            
            fig.update_layout(title=f"{point['name']}", xaxis_title="Data", yaxis_title=f"{point['metric']} ({point.get('unit', '')})", height=400)
            
            st.plotly_chart(fig, use_container_width=True)
            
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("Média", f"{np.mean(values):.2f}")
            col_s2.metric("Desvio", f"{np.std(values):.2f}")
            col_s3.metric("Mínimo", f"{np.min(values):.2f}")
            col_s4.metric("Máximo", f"{np.max(values):.2f}")
    
    # ========== TAB 3: GERENCIAR MEDIÇÕES ==========
    with tab3:
        measurements = point.get('measurements', [])
        
        if not measurements:
            st.info("📝 Nenhuma medição registrada.")
        else:
            st.markdown(f"#### 📋 {len(measurements)} Medição(ões) Registrada(s)")
            
            # Criar DataFrame para visualização
            df_data = []
            for m_idx, m in enumerate(measurements):
                status_icon = "✅" if m.get('status') == 'OK' else ("⚠️" if m.get('status') == 'WARNING' else "🚨")
                df_data.append({
                    'ID': m_idx,
                    'Data': format_date_br(m['date']),
                    'Valor': f"{m['value']:.2f}",
                    'Status': f"{status_icon} {m.get('status', 'OK')}"
                })
            
            # Mostrar tabela
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("#### ✏️ Editar ou Excluir Medição")
            
            # Selecionar medição
            measure_idx = st.number_input(
                "ID da Medição:",
                min_value=0,
                max_value=len(measurements) - 1,
                value=0,
                step=1,
                key=f"measure_idx_{point_idx}"
            )
            
            if 0 <= measure_idx < len(measurements):
                selected_m = measurements[measure_idx]
                
                st.info(f"📍 Selecionada: {format_date_br(selected_m['date'])} - {selected_m['value']} {point.get('unit', '')}")
                
                # MODO: Editar ou Excluir
                action = st.radio(
                    "Ação:",
                    ["✏️ Editar", "🗑️ Excluir"],
                    key=f"action_{point_idx}_{measure_idx}",
                    horizontal=True
                )
                
                if action == "✏️ Editar":
                    col_e1, col_e2 = st.columns(2)
                    
                    with col_e1:
                        edit_date_input = st.text_input(
                            "Nova Data:",
                            value=format_date_input(datetime.fromisoformat(selected_m['date']).date()),
                            key=f"edit_date_{point_idx}_{measure_idx}"
                        )
                    
                    with col_e2:
                        edit_value = st.number_input(
                            "Novo Valor:",
                            value=float(selected_m['value']),
                            key=f"edit_value_{point_idx}_{measure_idx}",
                            step=0.01
                        )
                    
                    if st.button("💾 Salvar Alterações", key=f"save_{point_idx}_{measure_idx}"):
                        edit_date, is_valid, error = parse_date_input(edit_date_input)
                        
                        if not is_valid:
                            st.error(f"❌ {error}")
                        else:
                            new_status = self._check_control_status(edit_value, point)
                            
                            control_data['control_points'][point_idx]['measurements'][measure_idx] = {
                                'date': edit_date.isoformat(),
                                'value': float(edit_value),
                                'status': new_status,
                                'added_at': selected_m.get('added_at', datetime.now().isoformat()),
                                'updated_at': datetime.now().isoformat()
                            }
                            
                            self.manager.save_tool_data(self.tool_name, control_data, completed=False)
                            st.success("✅ Atualizado!")
                            st.rerun()
                
                else:  # Excluir
                    st.warning(f"⚠️ **ATENÇÃO:** Você vai EXCLUIR a medição:")
                    st.error(f"📅 {format_date_br(selected_m['date'])} - 📊 {selected_m['value']} {point.get('unit', '')}")
                    
                    confirm_text = st.text_input(
                        "Digite 'EXCLUIR' para confirmar:",
                        key=f"confirm_{point_idx}_{measure_idx}"
                    )
                    
                    if st.button("🗑️ EXCLUIR PERMANENTEMENTE", key=f"delete_{point_idx}_{measure_idx}", type="primary"):
                        if confirm_text.strip().upper() == "EXCLUIR":
                            control_data['control_points'][point_idx]['measurements'].pop(measure_idx)
                            self.manager.save_tool_data(self.tool_name, control_data, completed=False)
                            st.success("✅ Excluído!")
                            st.rerun()
                        else:
                            st.error("❌ Digite 'EXCLUIR' para confirmar")
    
    # ========== REMOVER PONTO DE CONTROLE ==========
    st.divider()
    with st.expander("🗑️ Remover Ponto de Controle Completo"):
        st.warning(f"⚠️ Isso vai excluir o ponto '{point['name']}' e TODAS as suas medições!")
        
        confirm_point = st.text_input("Digite 'EXCLUIR TUDO' para confirmar:", key=f"confirm_point_{point_idx}")
        
        if st.button("🗑️ EXCLUIR PONTO COMPLETO", key=f"delete_point_{point_idx}", type="primary"):
            if confirm_point.strip().upper() == "EXCLUIR TUDO":
                control_data['control_points'].pop(point_idx)
                self.manager.save_tool_data(self.tool_name, control_data, completed=False)
                st.success("✅ Ponto excluído!")
                st.rerun()
            else:
                st.error("❌ Digite 'EXCLUIR TUDO' para confirmar")
        
#########################################################################################################################################################################################################################
    
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
        
        # Inicializar lista se não existir
        if 'monitoring_schedule' not in control_data or control_data['monitoring_schedule'] is None:
            control_data['monitoring_schedule'] = []
        
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
                # Data com formato brasileiro
                current_filter_date = datetime.now().date()
                
                date_filter_input = st.text_input(
                    "📅 Filtrar por data:",
                    value=format_date_input(current_filter_date),
                    key=f"date_filter_input_{self.project_id}",
                    placeholder="DD/MM/AAAA",
                    help="Digite a data no formato brasileiro"
                )
                
                date_filter, is_valid_filter, error_filter = parse_date_input(date_filter_input)
                if not is_valid_filter and date_filter_input:
                    st.error(error_filter)
                if date_filter is None:
                    date_filter = current_filter_date  # Fallback
            
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
                
                with st.expander(f"{color} **{event['point_name']}** - {format_date_br(event['date'])}"):
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
        
        # Inicializar lista se não existir
        if 'response_plans' not in control_data or control_data['response_plans'] is None:
            control_data['response_plans'] = []
        
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
            # Data de próxima revisão com formato brasileiro
            current_next_review = doc.get('next_review', (datetime.now() + timedelta(days=90)).date().isoformat())
            if isinstance(current_next_review, str):
                try:
                    current_next_review = datetime.fromisoformat(current_next_review).date()
                except:
                    current_next_review = (datetime.now() + timedelta(days=90)).date()
            
            next_review_input = st.text_input(
                "📅 Próxima Revisão:",
                value=format_date_input(current_next_review),
                key=f"doc_next_review_input_{self.project_id}",
                placeholder="DD/MM/AAAA",
                help="Digite a data da próxima revisão"
            )
            
            next_review_date, is_valid_review, error_review = parse_date_input(next_review_input)
            if not is_valid_review and next_review_input:
                st.error(error_review)
            if next_review_date is None:
                next_review_date = current_next_review
            
            doc['next_review'] = next_review_date.isoformat()
        
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
                # Data da revisão com formato brasileiro
                revision_date_input = st.text_input(
                    "📅 Data da Revisão:",
                    value=format_date_input(datetime.now().date()),
                    key=f"revision_date_input_{self.project_id}",
                    placeholder="DD/MM/AAAA",
                    help="Data desta revisão"
                )
                
                revision_date, is_valid_rev_date, error_rev_date = parse_date_input(revision_date_input)
                if not is_valid_rev_date and revision_date_input:
                    st.error(error_rev_date)
                if revision_date is None:
                    revision_date = datetime.now().date()
            
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
                        'date': revision_date.isoformat() if isinstance(revision_date, (datetime, date)) else revision_date,
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
                with st.expander(f"📖 Versão {revision['version']} - {format_date_br(revision['date'])}"):
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
            if st.button("💾 Salvar Plano", key=f"save_{self.tool_name}_{self.project_id}", use_container_width=True):
                success = self.manager.save_tool_data(self.tool_name, control_data, completed=False)
                if success:
                    st.success("💾 Plano de controle salvo!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("📋 Gerar Relatório", key=f"report_{self.tool_name}_{self.project_id}", use_container_width=True):
                self._generate_control_report(control_data)
        
        with col3:
            if st.button("✅ Finalizar Plano", key=f"complete_{self.tool_name}_{self.project_id}", use_container_width=True, type="primary"):
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


class StatisticalMonitoringTool:
    """Ferramenta para Monitoramento Estatístico"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "statistical_monitoring"
    
    def show(self):
        """Interface principal da ferramenta"""
        st.markdown("## 📈 Monitoramento Estatístico")
        st.markdown("Utilize gráficos de controle e análises estatísticas para monitorar a estabilidade do processo.")
        
        # Status da ferramenta
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ **Monitoramento estatístico finalizado**")
        else:
            st.info("⏳ **Monitoramento em desenvolvimento**")
        
        # Inicializar dados da sessão
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data if existing_data else {
                'control_charts': [],
                'capability_analysis': {},
                'trend_analysis': {}
            }
        
        monitoring_data = st.session_state[session_key]
        
        # Verificar se há dados do plano de controle
        control_plan_data = self.manager.get_tool_data('control_plan')
        
        if not control_plan_data.get('control_points'):
            st.warning("⚠️ **Configure o Plano de Controle primeiro**")
            st.info("💡 O monitoramento estatístico precisa de pontos de controle com medições")
            return
        
        # Interface principal
        self._show_monitoring_tabs(monitoring_data, control_plan_data)
        
        # Botões de ação
        self._show_action_buttons(monitoring_data)
    
    def _show_monitoring_tabs(self, monitoring_data: Dict, control_plan_data: Dict):
        """Mostra abas do monitoramento estatístico"""
        tab1, tab2, tab3 = st.tabs([
            "📊 Gráficos de Controle",
            "📈 Análise de Capacidade",
            "🔍 Análise de Tendências"
        ])
        
        with tab1:
            self._show_control_charts(monitoring_data, control_plan_data)
        
        with tab2:
            self._show_capability_analysis(monitoring_data, control_plan_data)
        
        with tab3:
            self._show_trend_analysis(monitoring_data, control_plan_data)
    
    def _show_control_charts(self, monitoring_data: Dict, control_plan_data: Dict):
        """Gráficos de controle"""
        st.markdown("#### 📊 Gráficos de Controle")
        
        control_points = control_plan_data.get('control_points', [])
        
        # Selecionar ponto de controle
        points_with_measurements = [p for p in control_points if p.get('measurements')]
        
        if not points_with_measurements:
            st.info("📊 Adicione medições aos pontos de controle para visualizar gráficos")
            return
        
        selected_point_name = st.selectbox(
            "Selecione o Ponto de Controle:",
            [p['name'] for p in points_with_measurements],
            key=f"select_chart_point_{self.project_id}"
        )
        
        if selected_point_name:
            # Encontrar ponto selecionado
            selected_point = next(p for p in points_with_measurements if p['name'] == selected_point_name)
            measurements = selected_point.get('measurements', [])
            
            if len(measurements) < 3:
                st.warning("⚠️ Pelo menos 3 medições são necessárias para gráficos de controle")
                return
            
            # Preparar dados
            dates = [datetime.fromisoformat(m['date']) for m in measurements]
            values = [m['value'] for m in measurements]
            
            target = selected_point.get('target', 0)
            upper_limit = selected_point.get('upper_limit', 0)
            lower_limit = selected_point.get('lower_limit', 0)
            
            # Criar gráfico de controle
            fig = go.Figure()
            
            # Linha dos valores
            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='lines+markers',
                name='Valores Medidos',
                line=dict(color='blue', width=2),
                marker=dict(size=8)
            ))
            
            # Linha da meta
            fig.add_trace(go.Scatter(
                x=[dates[0], dates[-1]],
                y=[target, target],
                mode='lines',
                name='Meta',
                line=dict(color='green', width=2, dash='dash')
            ))
            
            # Limite superior
            fig.add_trace(go.Scatter(
                x=[dates[0], dates[-1]],
                y=[upper_limit, upper_limit],
                mode='lines',
                name='Limite Superior',
                line=dict(color='red', width=2, dash='dot')
            ))
            
            # Limite inferior
            fig.add_trace(go.Scatter(
                x=[dates[0], dates[-1]],
                y=[lower_limit, lower_limit],
                mode='lines',
                name='Limite Inferior',
                line=dict(color='red', width=2, dash='dot')
            ))
            
            # Marcar pontos fora de controle
            out_of_control = []
            out_of_control_dates = []
            
            for i, value in enumerate(values):
                if value > upper_limit or value < lower_limit:
                    out_of_control.append(value)
                    out_of_control_dates.append(dates[i])
            
            if out_of_control:
                fig.add_trace(go.Scatter(
                    x=out_of_control_dates,
                    y=out_of_control,
                    mode='markers',
                    name='Fora de Controle',
                    marker=dict(color='red', size=12, symbol='x')
                ))
            
            fig.update_layout(
                title=f"Gráfico de Controle - {selected_point['name']}",
                xaxis_title="Data",
                yaxis_title=f"{selected_point['metric']} ({selected_point.get('unit', '')})",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Média", f"{np.mean(values):.2f}")
            
            with col2:
                st.metric("Desvio Padrão", f"{np.std(values):.2f}")
            
            with col3:
                st.metric("Mínimo", f"{np.min(values):.2f}")
            
            with col4:
                st.metric("Máximo", f"{np.max(values):.2f}")
            
            # Análise de estabilidade
            st.markdown("##### 📊 Análise de Estabilidade")
            
            pct_in_control = ((len(values) - len(out_of_control)) / len(values)) * 100
            
            if pct_in_control >= 95:
                st.success(f"✅ **Processo estável:** {pct_in_control:.1f}% das medições dentro dos limites")
            elif pct_in_control >= 80:
                st.warning(f"⚠️ **Atenção:** {pct_in_control:.1f}% das medições dentro dos limites")
            else:
                st.error(f"🚨 **Processo instável:** {pct_in_control:.1f}% das medições dentro dos limites")
    
    def _show_capability_analysis(self, monitoring_data: Dict, control_plan_data: Dict):
        """Análise de capacidade do processo"""
        st.markdown("#### 📈 Análise de Capacidade")
        
        control_points = control_plan_data.get('control_points', [])
        points_with_measurements = [p for p in control_points if p.get('measurements') and len(p['measurements']) >= 20]
        
        if not points_with_measurements:
            st.info("📈 Pelo menos 20 medições são necessárias para análise de capacidade")
            return
        
        selected_point_name = st.selectbox(
            "Selecione o Ponto de Controle:",
            [p['name'] for p in points_with_measurements],
            key=f"select_capability_point_{self.project_id}"
        )
        
        if selected_point_name:
            selected_point = next(p for p in points_with_measurements if p['name'] == selected_point_name)
            measurements = selected_point.get('measurements', [])
            values = [m['value'] for m in measurements]
            
            target = selected_point.get('target', 0)
            upper_spec = selected_point.get('upper_limit', 0)
            lower_spec = selected_point.get('lower_limit', 0)
            
            # Calcular índices de capacidade
            mean = np.mean(values)
            std = np.std(values, ddof=1)  # Desvio padrão amostral
            
            # Cp - Capacidade potencial
            cp = (upper_spec - lower_spec) / (6 * std) if std > 0 else 0
            
            # Cpk - Capacidade real
            cpk_upper = (upper_spec - mean) / (3 * std) if std > 0 else 0
            cpk_lower = (mean - lower_spec) / (3 * std) if std > 0 else 0
            cpk = min(cpk_upper, cpk_lower)
            
            # Pp - Performance potencial
            pp = (upper_spec - lower_spec) / (6 * std) if std > 0 else 0
            
            # Ppk - Performance real
            ppk_upper = (upper_spec - mean) / (3 * std) if std > 0 else 0
            ppk_lower = (mean - lower_spec) / (3 * std) if std > 0 else 0
            ppk = min(ppk_upper, ppk_lower)
            
            # Mostrar índices
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Cp", f"{cp:.2f}")
                if cp >= 1.33:
                    st.success("✅ Excelente")
                elif cp >= 1.0:
                    st.warning("⚠️ Aceitável")
                else:
                    st.error("🚨 Inadequado")
            
            with col2:
                st.metric("Cpk", f"{cpk:.2f}")
                if cpk >= 1.33:
                    st.success("✅ Excelente")
                elif cpk >= 1.0:
                    st.warning("⚠️ Aceitável")
                else:
                    st.error("🚨 Inadequado")
            
            with col3:
                st.metric("Pp", f"{pp:.2f}")
            
            with col4:
                st.metric("Ppk", f"{ppk:.2f}")
            
            # Histograma com limites
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=values,
                name='Distribuição',
                nbinsx=20,
                marker_color='lightblue'
            ))
            
            # Adicionar linhas verticais
            fig.add_vline(x=lower_spec, line_dash="dash", line_color="red", annotation_text="LSL")
            fig.add_vline(x=upper_spec, line_dash="dash", line_color="red", annotation_text="USL")
            fig.add_vline(x=target, line_dash="solid", line_color="green", annotation_text="Target")
            fig.add_vline(x=mean, line_dash="dot", line_color="blue", annotation_text="Média")
            
            fig.update_layout(
                title=f"Distribuição - {selected_point['name']}",
                xaxis_title=f"{selected_point['metric']} ({selected_point.get('unit', '')})",
                yaxis_title="Frequência",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Interpretação
            st.markdown("##### 📊 Interpretação")
            
            st.markdown("""
            **Índices de Capacidade:**
            - **Cp/Pp ≥ 1.33**: Processo capaz (excelente)
            - **Cp/Pp ≥ 1.00**: Processo minimamente capaz
            - **Cp/Pp < 1.00**: Processo incapaz
            
            **Cpk/Ppk considera o centramento do processo:**
            - Se Cpk < Cp: Processo descentrado
            - Se Cpk ≈ Cp: Processo centrado
            """)
    
    def _show_trend_analysis(self, monitoring_data: Dict, control_plan_data: Dict):
        """Análise de tendências"""
        st.markdown("#### 🔍 Análise de Tendências")
        
        control_points = control_plan_data.get('control_points', [])
        points_with_measurements = [p for p in control_points if p.get('measurements') and len(p['measurements']) >= 5]
        
        if not points_with_measurements:
            st.info("🔍 Pelo menos 5 medições são necessárias para análise de tendências")
            return
        
        selected_point_name = st.selectbox(
            "Selecione o Ponto de Controle:",
            [p['name'] for p in points_with_measurements],
            key=f"select_trend_point_{self.project_id}"
        )
        
        if selected_point_name:
            selected_point = next(p for p in points_with_measurements if p['name'] == selected_point_name)
            measurements = selected_point.get('measurements', [])
            
            dates = [datetime.fromisoformat(m['date']) for m in measurements]
            values = [m['value'] for m in measurements]
            
            # Criar série temporal numérica para regressão
            x_numeric = np.arange(len(values))
            
            # Calcular linha de tendência
            z = np.polyfit(x_numeric, values, 1)
            p = np.poly1d(z)
            trend_line = p(x_numeric)
            
            # Criar gráfico
            fig = go.Figure()
            
            # Valores reais
            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='lines+markers',
                name='Valores',
                line=dict(color='blue', width=2),
                marker=dict(size=8)
            ))
            
            # Linha de tendência
            fig.add_trace(go.Scatter(
                x=dates,
                y=trend_line,
                mode='lines',
                name='Tendência',
                line=dict(color='red', width=2, dash='dash')
            ))
            
            fig.update_layout(
                title=f"Análise de Tendência - {selected_point['name']}",
                xaxis_title="Data",
                yaxis_title=f"{selected_point['metric']} ({selected_point.get('unit', '')})",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Análise da tendência
            slope = z[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Inclinação da Tendência", f"{slope:.4f}")
                
                if abs(slope) < 0.01:
                    st.success("✅ Processo estável (sem tendência significativa)")
                elif slope > 0:
                    st.warning("⚠️ Tendência crescente")
                else:
                    st.warning("⚠️ Tendência decrescente")
            
            with col2:
                # Variação total
                variation = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                st.metric("Variação Total", f"{variation:.2f}%")
    
    def _show_action_buttons(self, monitoring_data: Dict):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Análises", key=f"save_{self.tool_name}_{self.project_id}", use_container_width=True):
                success = self.manager.save_tool_data(self.tool_name, monitoring_data, completed=False)
                if success:
                    st.success("💾 Análises salvas!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("✅ Finalizar Monitoramento", key=f"complete_{self.tool_name}_{self.project_id}", use_container_width=True, type="primary"):
                success = self.manager.save_tool_data(self.tool_name, monitoring_data, completed=True)
                if success:
                    st.success("✅ Monitoramento estatístico finalizado!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Erro ao finalizar")


class StandardDocumentationTool:
    """Ferramenta para Documentação Padrão"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "standard_documentation"
    
    def show(self):
        """Interface principal da ferramenta"""
        st.markdown("## 📋 Documentação Padrão")
        st.markdown("Crie e mantenha a documentação padrão do processo melhorado.")
        
        # Status da ferramenta
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ **Documentação padrão finalizada**")
        else:
            st.info("⏳ **Documentação em desenvolvimento**")
        
        # Inicializar dados da sessão
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data if existing_data else {
                'procedures': [],
                'work_instructions': [],
                'forms': [],
                'training_materials': []
            }
        
        doc_data = st.session_state[session_key]
        
        # Interface principal
        self._show_documentation_tabs(doc_data)
        
        # Botões de ação
        self._show_action_buttons(doc_data)
    
    def _show_documentation_tabs(self, doc_data: Dict):
        """Mostra abas da documentação"""
        tab1, tab2, tab3, tab4 = st.tabs([
            "📄 Procedimentos",
            "📝 Instruções de Trabalho",
            "📋 Formulários",
            "🎓 Material de Treinamento"
        ])
        
        with tab1:
            self._show_procedures(doc_data)
        
        with tab2:
            self._show_work_instructions(doc_data)
        
        with tab3:
            self._show_forms(doc_data)
        
        with tab4:
            self._show_training_materials(doc_data)
    
    def _show_procedures(self, doc_data: Dict):
        """Gerenciamento de procedimentos"""
        st.markdown("#### 📄 Procedimentos Operacionais Padrão (POP)")
        
        # Inicializar lista se não existir
        if 'procedures' not in doc_data or doc_data['procedures'] is None:
            doc_data['procedures'] = []
        
        # Adicionar procedimento
        with st.expander("➕ Adicionar Procedimento"):
            proc_title = st.text_input(
                "Título do Procedimento *",
                key=f"proc_title_{self.project_id}",
                placeholder="Ex: POP-001 - Controle de Qualidade"
            )
            
            proc_version = st.text_input(
                "Versão *",
                key=f"proc_version_{self.project_id}",
                placeholder="Ex: 1.0"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                proc_author = st.text_input(
                    "Autor:",
                    key=f"proc_author_{self.project_id}"
                )
                
                proc_approver = st.text_input(
                    "Aprovador:",
                    key=f"proc_approver_{self.project_id}"
                )
            
            with col2:
                # Data de criação
                proc_date_input = st.text_input(
                    "📅 Data de Criação:",
                    value=format_date_input(datetime.now().date()),
                    key=f"proc_date_input_{self.project_id}",
                    placeholder="DD/MM/AAAA"
                )
                
                proc_date, is_valid_proc, error_proc = parse_date_input(proc_date_input)
                if not is_valid_proc and proc_date_input:
                    st.error(error_proc)
                if proc_date is None:
                    proc_date = datetime.now().date()
                
                # Data de revisão
                proc_review_input = st.text_input(
                    "📅 Próxima Revisão:",
                    value=format_date_input((datetime.now() + timedelta(days=365)).date()),
                    key=f"proc_review_input_{self.project_id}",
                    placeholder="DD/MM/AAAA"
                )
                
                proc_review_date, is_valid_review, error_review = parse_date_input(proc_review_input)
                if not is_valid_review and proc_review_input:
                    st.error(error_review)
                if proc_review_date is None:
                    proc_review_date = (datetime.now() + timedelta(days=365)).date()
            
            proc_objective = st.text_area(
                "Objetivo:",
                key=f"proc_objective_{self.project_id}",
                placeholder="Descreva o objetivo deste procedimento...",
                height=80
            )
            
            proc_scope = st.text_area(
                "Escopo:",
                key=f"proc_scope_{self.project_id}",
                placeholder="Defina o escopo de aplicação...",
                height=80
            )
            
            proc_content = st.text_area(
                "Conteúdo do Procedimento:",
                key=f"proc_content_{self.project_id}",
                placeholder="Descreva o procedimento em detalhes...",
                height=200
            )
            
            if st.button("📄 Adicionar Procedimento", key=f"add_procedure_{self.project_id}"):
                if proc_title.strip() and proc_version.strip() and proc_content.strip():
                    doc_data['procedures'].append({
                        'title': proc_title,
                        'version': proc_version,
                        'author': proc_author,
                        'approver': proc_approver,
                        'date': proc_date.isoformat(),
                        'review_date': proc_review_date.isoformat(),
                        'objective': proc_objective,
                        'scope': proc_scope,
                        'content': proc_content,
                        'status': 'Ativo',
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success("✅ Procedimento adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Título, versão e conteúdo são obrigatórios")
        
        # Mostrar procedimentos existentes
        if doc_data.get('procedures'):
            st.markdown("##### 📚 Procedimentos Cadastrados")
            
            for i, proc in enumerate(doc_data['procedures']):
                with st.expander(f"📄 **{proc['title']}** v{proc['version']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Autor:** {proc.get('author', 'N/A')}")
                        st.write(f"**Aprovador:** {proc.get('approver', 'N/A')}")
                        st.write(f"**Data:** {format_date_br(proc['date'])}")
                        st.write(f"**Próxima Revisão:** {format_date_br(proc['review_date'])}")
                        
                        st.markdown("**Objetivo:**")
                        st.write(proc.get('objective', 'N/A'))
                        
                        st.markdown("**Escopo:**")
                        st.write(proc.get('scope', 'N/A'))
                        
                        st.markdown("**Conteúdo:**")
                        st.write(proc['content'])
                    
                    with col2:
                        new_status = st.selectbox(
                            "Status:",
                            ["Ativo", "Obsoleto", "Em Revisão"],
                            index=["Ativo", "Obsoleto", "Em Revisão"].index(proc.get('status', 'Ativo')),
                            key=f"proc_status_{i}_{self.project_id}"
                        )
                        
                        doc_data['procedures'][i]['status'] = new_status
                        
                        if st.button("🗑️", key=f"remove_proc_{i}_{self.project_id}"):
                            doc_data['procedures'].pop(i)
                            st.rerun()
        else:
            st.info("📄 Nenhum procedimento cadastrado ainda.")
    
    def _show_work_instructions(self, doc_data: Dict):
        """Gerenciamento de instruções de trabalho"""
        st.markdown("#### 📝 Instruções de Trabalho")
        
        # Inicializar lista se não existir
        if 'work_instructions' not in doc_data or doc_data['work_instructions'] is None:
            doc_data['work_instructions'] = []
        
        # Adicionar instrução
        with st.expander("➕ Adicionar Instrução de Trabalho"):
            inst_title = st.text_input(
                "Título *",
                key=f"inst_title_{self.project_id}",
                placeholder="Ex: IT-001 - Operação de Equipamento X"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                inst_process = st.text_input(
                    "Processo Relacionado:",
                    key=f"inst_process_{self.project_id}"
                )
                
                inst_responsible = st.text_input(
                    "Responsável:",
                    key=f"inst_responsible_{self.project_id}"
                )
            
            with col2:
                inst_frequency = st.selectbox(
                    "Frequência:",
                    ["Contínua", "Diária", "Semanal", "Mensal", "Conforme Necessário"],
                    key=f"inst_frequency_{self.project_id}"
                )
                
                inst_difficulty = st.selectbox(
                    "Nível de Dificuldade:",
                    ["Básico", "Intermediário", "Avançado"],
                    key=f"inst_difficulty_{self.project_id}"
                )
            
            inst_steps = st.text_area(
                "Passos da Instrução:",
                key=f"inst_steps_{self.project_id}",
                placeholder="1. Primeiro passo\n2. Segundo passo\n3. Terceiro passo...",
                height=150
            )
            
            inst_safety = st.text_area(
                "Precauções de Segurança:",
                key=f"inst_safety_{self.project_id}",
                placeholder="Liste as precauções de segurança...",
                height=80
            )
            
            if st.button("📝 Adicionar Instrução", key=f"add_instruction_{self.project_id}"):
                if inst_title.strip() and inst_steps.strip():
                    doc_data['work_instructions'].append({
                        'title': inst_title,
                        'process': inst_process,
                        'responsible': inst_responsible,
                        'frequency': inst_frequency,
                        'difficulty': inst_difficulty,
                        'steps': inst_steps,
                        'safety': inst_safety,
                        'status': 'Ativo',
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success("✅ Instrução adicionada!")
                    st.rerun()
                else:
                    st.error("❌ Título e passos são obrigatórios")
        
        # Mostrar instruções existentes
        if doc_data.get('work_instructions'):
            st.markdown("##### 📚 Instruções Cadastradas")
            
            for i, inst in enumerate(doc_data['work_instructions']):
                with st.expander(f"📝 **{inst['title']}** - {inst['difficulty']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Processo:** {inst.get('process', 'N/A')}")
                        st.write(f"**Responsável:** {inst.get('responsible', 'N/A')}")
                        st.write(f"**Frequência:** {inst['frequency']}")
                        
                        st.markdown("**Passos:**")
                        st.write(inst['steps'])
                        
                        if inst.get('safety'):
                            st.markdown("**⚠️ Precauções de Segurança:**")
                            st.warning(inst['safety'])
                    
                    with col2:
                        new_status = st.selectbox(
                            "Status:",
                            ["Ativo", "Obsoleto", "Em Revisão"],
                            index=["Ativo", "Obsoleto", "Em Revisão"].index(inst.get('status', 'Ativo')),
                            key=f"inst_status_{i}_{self.project_id}"
                        )
                        
                        doc_data['work_instructions'][i]['status'] = new_status
                        
                        if st.button("🗑️", key=f"remove_inst_{i}_{self.project_id}"):
                            doc_data['work_instructions'].pop(i)
                            st.rerun()
        else:
            st.info("📝 Nenhuma instrução cadastrada ainda.")
    
    def _show_forms(self, doc_data: Dict):
        """Gerenciamento de formulários"""
        st.markdown("#### 📋 Formulários e Checklists")
        
        # Inicializar lista se não existir
        if 'forms' not in doc_data or doc_data['forms'] is None:
            doc_data['forms'] = []
        
        # Adicionar formulário
        with st.expander("➕ Adicionar Formulário"):
            form_title = st.text_input(
                "Título *",
                key=f"form_title_{self.project_id}",
                placeholder="Ex: Checklist de Inspeção de Qualidade"
            )
            
            form_type = st.selectbox(
                "Tipo:",
                ["Checklist", "Registro", "Relatório", "Formulário de Auditoria", "Outro"],
                key=f"form_type_{self.project_id}"
            )
            
            form_purpose = st.text_area(
                "Propósito:",
                key=f"form_purpose_{self.project_id}",
                placeholder="Descreva o propósito deste formulário...",
                height=80
            )
            
            form_fields = st.text_area(
                "Campos do Formulário:",
                key=f"form_fields_{self.project_id}",
                placeholder="Liste os campos:\n- Campo 1\n- Campo 2\n- Campo 3...",
                height=120
            )
            
            if st.button("📋 Adicionar Formulário", key=f"add_form_{self.project_id}"):
                if form_title.strip() and form_fields.strip():
                    doc_data['forms'].append({
                        'title': form_title,
                        'type': form_type,
                        'purpose': form_purpose,
                        'fields': form_fields,
                        'status': 'Ativo',
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success("✅ Formulário adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Título e campos são obrigatórios")
        
        # Mostrar formulários existentes
        if doc_data.get('forms'):
            st.markdown("##### 📚 Formulários Cadastrados")
            
            for i, form in enumerate(doc_data['forms']):
                with st.expander(f"📋 **{form['title']}** - {form['type']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown("**Propósito:**")
                        st.write(form.get('purpose', 'N/A'))
                        
                        st.markdown("**Campos:**")
                        st.write(form['fields'])
                    
                    with col2:
                        new_status = st.selectbox(
                            "Status:",
                            ["Ativo", "Obsoleto", "Em Revisão"],
                            index=["Ativo", "Obsoleto", "Em Revisão"].index(form.get('status', 'Ativo')),
                            key=f"form_status_{i}_{self.project_id}"
                        )
                        
                        doc_data['forms'][i]['status'] = new_status
                        
                        if st.button("🗑️", key=f"remove_form_{i}_{self.project_id}"):
                            doc_data['forms'].pop(i)
                            st.rerun()
        else:
            st.info("📋 Nenhum formulário cadastrado ainda.")
    
    def _show_training_materials(self, doc_data: Dict):
        """Gerenciamento de material de treinamento"""
        st.markdown("#### 🎓 Material de Treinamento")
        
        # Inicializar lista se não existir
        if 'training_materials' not in doc_data or doc_data['training_materials'] is None:
            doc_data['training_materials'] = []
        
        # Adicionar material
        with st.expander("➕ Adicionar Material de Treinamento"):
            train_title = st.text_input(
                "Título *",
                key=f"train_title_{self.project_id}",
                placeholder="Ex: Treinamento de Operação do Novo Processo"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                train_target = st.text_input(
                    "Público-Alvo:",
                    key=f"train_target_{self.project_id}",
                    placeholder="Ex: Operadores de linha"
                )
                
                train_duration = st.text_input(
                    "Duração:",
                    key=f"train_duration_{self.project_id}",
                    placeholder="Ex: 2 horas"
                )
            
            with col2:
                train_method = st.selectbox(
                    "Método:",
                    ["Presencial", "Online", "Híbrido", "On-the-job"],
                    key=f"train_method_{self.project_id}"
                )
                
                train_level = st.selectbox(
                    "Nível:",
                    ["Básico", "Intermediário", "Avançado"],
                    key=f"train_level_{self.project_id}"
                )
            
            train_objectives = st.text_area(
                "Objetivos de Aprendizado:",
                key=f"train_objectives_{self.project_id}",
                placeholder="Liste os objetivos do treinamento...",
                height=80
            )
            
            train_content = st.text_area(
                "Conteúdo do Treinamento:",
                key=f"train_content_{self.project_id}",
                placeholder="Descreva o conteúdo que será abordado...",
                height=120
            )
            
            if st.button("🎓 Adicionar Material", key=f"add_training_{self.project_id}"):
                if train_title.strip() and train_content.strip():
                    doc_data['training_materials'].append({
                        'title': train_title,
                        'target': train_target,
                        'duration': train_duration,
                        'method': train_method,
                        'level': train_level,
                        'objectives': train_objectives,
                        'content': train_content,
                        'status': 'Ativo',
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success("✅ Material adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Título e conteúdo são obrigatórios")
        
        # Mostrar materiais existentes
        if doc_data.get('training_materials'):
            st.markdown("##### 📚 Materiais Cadastrados")
            
            for i, train in enumerate(doc_data['training_materials']):
                with st.expander(f"🎓 **{train['title']}** - {train['level']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Público-Alvo:** {train.get('target', 'N/A')}")
                        st.write(f"**Duração:** {train.get('duration', 'N/A')}")
                        st.write(f"**Método:** {train['method']}")
                        
                        st.markdown("**Objetivos:**")
                        st.write(train.get('objectives', 'N/A'))
                        
                        st.markdown("**Conteúdo:**")
                        st.write(train['content'])
                    
                    with col2:
                        new_status = st.selectbox(
                            "Status:",
                            ["Ativo", "Obsoleto", "Em Revisão"],
                            index=["Ativo", "Obsoleto", "Em Revisão"].index(train.get('status', 'Ativo')),
                            key=f"train_status_{i}_{self.project_id}"
                        )
                        
                        doc_data['training_materials'][i]['status'] = new_status
                        
                        if st.button("🗑️", key=f"remove_train_{i}_{self.project_id}"):
                            doc_data['training_materials'].pop(i)
                            st.rerun()
        else:
            st.info("🎓 Nenhum material cadastrado ainda.")
    
    def _show_action_buttons(self, doc_data: Dict):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Documentação", key=f"save_{self.tool_name}_{self.project_id}", use_container_width=True):
                success = self.manager.save_tool_data(self.tool_name, doc_data, completed=False)
                if success:
                    st.success("💾 Documentação salva!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("✅ Finalizar Documentação", key=f"complete_{self.tool_name}_{self.project_id}", use_container_width=True, type="primary"):
                if self._validate_documentation(doc_data):
                    success = self.manager.save_tool_data(self.tool_name, doc_data, completed=True)
                    if success:
                        st.success("✅ Documentação padrão finalizada!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao finalizar")
                else:
                    st.error("❌ Complete os requisitos mínimos")
    
    def _validate_documentation(self, doc_data: Dict) -> bool:
        """Valida se a documentação está completa"""
        # Verificar se há pelo menos um item em cada categoria
        if not doc_data.get('procedures'):
            st.error("❌ Adicione pelo menos um procedimento")
            return False
        
        if not doc_data.get('work_instructions'):
            st.error("❌ Adicione pelo menos uma instrução de trabalho")
            return False
        
        return True


class SustainabilityAuditTool:
    """Ferramenta para Auditoria de Sustentabilidade"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "sustainability_audit"
    
    def show(self):
        """Interface principal da ferramenta"""
        st.markdown("## 🔄 Auditoria de Sustentabilidade")
        st.markdown("Avalie a sustentabilidade das melhorias e planeje auditorias periódicas.")
        
        # Status da ferramenta
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ **Auditoria de sustentabilidade finalizada**")
        else:
            st.info("⏳ **Auditoria em desenvolvimento**")
        
        # Inicializar dados da sessão
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data if existing_data else {
                'audit_plan': {},
                'audit_checklist': [],
                'audit_findings': [],
                'corrective_actions': []
            }
        
        audit_data = st.session_state[session_key]
        
        # Interface principal
        self._show_audit_tabs(audit_data)
        
        # Botões de ação
        self._show_action_buttons(audit_data)
    
    def _show_audit_tabs(self, audit_data: Dict):
        """Mostra abas da auditoria"""
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Plano de Auditoria",
            "✅ Checklist",
            "🔍 Achados",
            "⚡ Ações Corretivas"
        ])
        
        with tab1:
            self._show_audit_plan(audit_data)
        
        with tab2:
            self._show_audit_checklist(audit_data)
        
        with tab3:
            self._show_audit_findings(audit_data)
        
        with tab4:
            self._show_corrective_actions(audit_data)
    
    def _show_audit_plan(self, audit_data: Dict):
        """Plano de auditoria"""
        st.markdown("#### 📋 Plano de Auditoria")
        
        if 'audit_plan' not in audit_data or audit_data['audit_plan'] is None:
            audit_data['audit_plan'] = {}
        
        plan = audit_data['audit_plan']
        
        # Configurações da auditoria
        col1, col2 = st.columns(2)
        
        with col1:
            plan['frequency'] = st.selectbox(
                "Frequência das Auditorias:",
                ["Mensal", "Trimestral", "Semestral", "Anual"],
                index=1 if not plan.get('frequency') else 
                      ["Mensal", "Trimestral", "Semestral", "Anual"].index(plan['frequency']),
                key=f"audit_frequency_{self.project_id}"
            )
            
            plan['lead_auditor'] = st.text_input(
                "Auditor Líder:",
                value=plan.get('lead_auditor', ''),
                key=f"lead_auditor_{self.project_id}"
            )
            
            plan['audit_team'] = st.text_area(
                "Equipe de Auditoria:",
                value=plan.get('audit_team', ''),
                key=f"audit_team_{self.project_id}",
                placeholder="Liste os membros da equipe...",
                height=80
            )
        
        with col2:
            # Próxima auditoria
            next_audit_default = (datetime.now() + timedelta(days=90)).date()
            current_next_audit = plan.get('next_audit_date', next_audit_default.isoformat())
            
            if isinstance(current_next_audit, str):
                try:
                    current_next_audit = datetime.fromisoformat(current_next_audit).date()
                except:
                    current_next_audit = next_audit_default
            
            next_audit_input = st.text_input(
                "📅 Próxima Auditoria:",
                value=format_date_input(current_next_audit),
                key=f"next_audit_input_{self.project_id}",
                placeholder="DD/MM/AAAA"
            )
            
            next_audit_date, is_valid_next, error_next = parse_date_input(next_audit_input)
            if not is_valid_next and next_audit_input:
                st.error(error_next)
            if next_audit_date is None:
                next_audit_date = current_next_audit
            
            plan['next_audit_date'] = next_audit_date.isoformat()
            
            plan['scope'] = st.text_area(
                "Escopo da Auditoria:",
                value=plan.get('scope', ''),
                key=f"audit_scope_{self.project_id}",
                placeholder="Defina o escopo...",
                height=80
            )
        
        plan['objectives'] = st.text_area(
            "Objetivos da Auditoria:",
            value=plan.get('objectives', ''),
            key=f"audit_objectives_{self.project_id}",
            placeholder="Liste os objetivos das auditorias...",
            height=100
        )
        
        plan['criteria'] = st.text_area(
            "Critérios de Auditoria:",
            value=plan.get('criteria', ''),
            key=f"audit_criteria_{self.project_id}",
            placeholder="Defina os critérios de avaliação...",
            height=100
        )
    
    def _show_audit_checklist(self, audit_data: Dict):
        """Checklist de auditoria"""
        st.markdown("#### ✅ Checklist de Auditoria")
        
        # Inicializar lista se não existir
        if 'audit_checklist' not in audit_data or audit_data['audit_checklist'] is None:
            audit_data['audit_checklist'] = []
        
        # Adicionar item de checklist
        with st.expander("➕ Adicionar Item de Verificação"):
            check_category = st.selectbox(
                "Categoria:",
                ["Controle de Processo", "Documentação", "Treinamento", "Equipamentos", "Conformidade", "Outro"],
                key=f"check_category_{self.project_id}"
            )
            
            check_item = st.text_input(
                "Item de Verificação *",
                key=f"check_item_{self.project_id}",
                placeholder="Ex: Plano de controle está sendo seguido?"
            )
            
            check_criteria = st.text_area(
                "Critério de Aceitação:",
                key=f"check_criteria_{self.project_id}",
                placeholder="Descreva o critério...",
                height=80
            )
            
            check_method = st.text_input(
                "Método de Verificação:",
                key=f"check_method_{self.project_id}",
                placeholder="Ex: Revisão de registros, Observação"
            )
            
            if st.button("✅ Adicionar Item", key=f"add_check_{self.project_id}"):
                if check_item.strip():
                    audit_data['audit_checklist'].append({
                        'category': check_category,
                        'item': check_item,
                        'criteria': check_criteria,
                        'method': check_method,
                        'status': 'Pendente',
                        'result': '',
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success("✅ Item adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Item de verificação é obrigatório")
        
        # Mostrar checklist
        if audit_data.get('audit_checklist'):
            st.markdown("##### 📋 Itens de Verificação")
            
            # Agrupar por categoria
            categories = {}
            for item in audit_data['audit_checklist']:
                cat = item['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
            
            for category, items in categories.items():
                with st.expander(f"**{category}** ({len(items)} itens)"):
                    for i, item in enumerate(items):
                        original_idx = audit_data['audit_checklist'].index(item)
                        
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write(f"**{item['item']}**")
                            st.caption(f"Critério: {item.get('criteria', 'N/A')}")
                            st.caption(f"Método: {item.get('method', 'N/A')}")
                        
                        with col2:
                            new_status = st.selectbox(
                                "Status:",
                                ["Pendente", "Conforme", "Não Conforme", "N/A"],
                                index=["Pendente", "Conforme", "Não Conforme", "N/A"].index(item.get('status', 'Pendente')),
                                key=f"check_status_{original_idx}_{self.project_id}"
                            )
                            
                            audit_data['audit_checklist'][original_idx]['status'] = new_status
                            
                            result = st.text_area(
                                "Observações:",
                                value=item.get('result', ''),
                                key=f"check_result_{original_idx}_{self.project_id}",
                                height=60
                            )
                            
                            audit_data['audit_checklist'][original_idx]['result'] = result
                        
                        with col3:
                            if st.button("🗑️", key=f"remove_check_{original_idx}_{self.project_id}"):
                                audit_data['audit_checklist'].pop(original_idx)
                                st.rerun()
                        
                        st.divider()
            
            # Estatísticas
            total = len(audit_data['audit_checklist'])
            conforme = len([i for i in audit_data['audit_checklist'] if i.get('status') == 'Conforme'])
            nao_conforme = len([i for i in audit_data['audit_checklist'] if i.get('status') == 'Não Conforme'])
            
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            
            with col_stats1:
                st.metric("Total de Itens", total)
            
            with col_stats2:
                st.metric("Conformes", f"{conforme}/{total}")
            
            with col_stats3:
                st.metric("Não Conformes", nao_conforme)
        else:
            st.info("✅ Nenhum item de checklist definido ainda.")
    
    def _show_audit_findings(self, audit_data: Dict):
        """Achados de auditoria"""
        st.markdown("#### 🔍 Achados de Auditoria")
        
        # Inicializar lista se não existir
        if 'audit_findings' not in audit_data or audit_data['audit_findings'] is None:
            audit_data['audit_findings'] = []
        
        # Adicionar achado
        with st.expander("➕ Adicionar Achado"):
            finding_type = st.selectbox(
                "Tipo:",
                ["Não Conformidade Maior", "Não Conformidade Menor", "Observação", "Oportunidade de Melhoria"],
                key=f"finding_type_{self.project_id}"
            )
            
            # Data do achado
            finding_date_input = st.text_input(
                "📅 Data do Achado:",
                value=format_date_input(datetime.now().date()),
                key=f"finding_date_input_{self.project_id}",
                placeholder="DD/MM/AAAA"
            )
            
            finding_date, is_valid_finding, error_finding = parse_date_input(finding_date_input)
            if not is_valid_finding and finding_date_input:
                st.error(error_finding)
            if finding_date is None:
                finding_date = datetime.now().date()
            
            finding_area = st.text_input(
                "Área/Processo:",
                key=f"finding_area_{self.project_id}"
            )
            
            finding_description = st.text_area(
                "Descrição do Achado *",
                key=f"finding_description_{self.project_id}",
                placeholder="Descreva o achado em detalhes...",
                height=100
            )
            
            finding_evidence = st.text_area(
                "Evidências:",
                key=f"finding_evidence_{self.project_id}",
                placeholder="Liste as evidências encontradas...",
                height=80
            )
            
            if st.button("🔍 Adicionar Achado", key=f"add_finding_{self.project_id}"):
                if finding_description.strip():
                    audit_data['audit_findings'].append({
                        'type': finding_type,
                        'date': finding_date.isoformat(),
                        'area': finding_area,
                        'description': finding_description,
                        'evidence': finding_evidence,
                        'status': 'Aberto',
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success("✅ Achado adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Descrição do achado é obrigatória")
        
        # Mostrar achados
        if audit_data.get('audit_findings'):
            st.markdown("##### 📋 Achados Registrados")
            
            for i, finding in enumerate(audit_data['audit_findings']):
                # Ícone baseado no tipo
                type_icons = {
                    "Não Conformidade Maior": "🔴",
                    "Não Conformidade Menor": "🟡",
                    "Observação": "🔵",
                    "Oportunidade de Melhoria": "🟢"
                }
                icon = type_icons.get(finding['type'], "🔵")
                
                with st.expander(f"{icon} **{finding['type']}** - {format_date_br(finding['date'])}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Área:** {finding.get('area', 'N/A')}")
                        
                        st.markdown("**Descrição:**")
                        st.write(finding['description'])
                        
                        st.markdown("**Evidências:**")
                        st.write(finding.get('evidence', 'N/A'))
                    
                    with col2:
                        new_status = st.selectbox(
                            "Status:",
                            ["Aberto", "Em Análise", "Resolvido", "Fechado"],
                            index=["Aberto", "Em Análise", "Resolvido", "Fechado"].index(finding.get('status', 'Aberto')),
                            key=f"finding_status_{i}_{self.project_id}"
                        )
                        
                        audit_data['audit_findings'][i]['status'] = new_status
                        
                        if st.button("🗑️", key=f"remove_finding_{i}_{self.project_id}"):
                            audit_data['audit_findings'].pop(i)
                            st.rerun()
            
            # Estatísticas
            total_findings = len(audit_data['audit_findings'])
            open_findings = len([f for f in audit_data['audit_findings'] if f.get('status') in ['Aberto', 'Em Análise']])
            
            col_find1, col_find2 = st.columns(2)
            
            with col_find1:
                st.metric("Total de Achados", total_findings)
            
            with col_find2:
                st.metric("Achados Abertos", open_findings)
        else:
            st.info("🔍 Nenhum achado registrado ainda.")
    
    def _show_corrective_actions(self, audit_data: Dict):
        """Ações corretivas"""
        st.markdown("#### ⚡ Ações Corretivas")
        
        # Inicializar lista se não existir
        if 'corrective_actions' not in audit_data or audit_data['corrective_actions'] is None:
            audit_data['corrective_actions'] = []
        
        # Adicionar ação corretiva
        with st.expander("➕ Adicionar Ação Corretiva"):
            action_finding = st.selectbox(
                "Achado Relacionado:",
                ["N/A"] + [f"{f['type']} - {f.get('area', 'N/A')}" for f in audit_data.get('audit_findings', [])],
                key=f"action_finding_{self.project_id}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                action_description = st.text_area(
                    "Descrição da Ação *",
                    key=f"action_description_{self.project_id}",
                    placeholder="Descreva a ação corretiva...",
                    height=80
                )
                
                action_responsible = st.text_input(
                    "Responsável:",
                    key=f"action_responsible_{self.project_id}"
                )
            
            with col2:
                # Data prevista
                action_due_input = st.text_input(
                    "📅 Prazo:",
                    value=format_date_input((datetime.now() + timedelta(days=30)).date()),
                    key=f"action_due_input_{self.project_id}",
                    placeholder="DD/MM/AAAA"
                )
                
                action_due_date, is_valid_due, error_due = parse_date_input(action_due_input)
                if not is_valid_due and action_due_input:
                    st.error(error_due)
                if action_due_date is None:
                    action_due_date = (datetime.now() + timedelta(days=30)).date()
                
                action_priority = st.selectbox(
                    "Prioridade:",
                    ["Alta", "Média", "Baixa"],
                    key=f"action_priority_{self.project_id}"
                )
            
            if st.button("⚡ Adicionar Ação", key=f"add_action_{self.project_id}"):
                if action_description.strip():
                    audit_data['corrective_actions'].append({
                        'finding': action_finding,
                        'description': action_description,
                        'responsible': action_responsible,
                        'due_date': action_due_date.isoformat(),
                        'priority': action_priority,
                        'status': 'Planejada',
                        'created_at': datetime.now().isoformat()
                    })
                    
                    st.success("✅ Ação corretiva adicionada!")
                    st.rerun()
                else:
                    st.error("❌ Descrição da ação é obrigatória")
        
        # Mostrar ações
        if audit_data.get('corrective_actions'):
            st.markdown("##### 📋 Ações Corretivas Planejadas")
            
            for i, action in enumerate(audit_data['corrective_actions']):
                # Ícone baseado na prioridade
                priority_icons = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}
                icon = priority_icons.get(action['priority'], "🟡")
                
                # Verificar se está atrasada
                due_date = datetime.fromisoformat(action['due_date']).date()
                is_overdue = due_date < datetime.now().date() and action.get('status') != 'Concluída'
                
                with st.expander(f"{icon} **{action['description'][:50]}...** - {format_date_br(action['due_date'])} {'🚨 ATRASADA' if is_overdue else ''}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Achado:** {action.get('finding', 'N/A')}")
                        st.write(f"**Responsável:** {action.get('responsible', 'Não definido')}")
                        
                        st.markdown("**Descrição:**")
                        st.write(action['description'])
                        
                        # Campo de progresso
                        progress = st.text_area(
                            "Progresso/Observações:",
                            value=action.get('progress', ''),
                            key=f"action_progress_{i}_{self.project_id}",
                            height=60
                        )
                        
                        audit_data['corrective_actions'][i]['progress'] = progress
                    
                    with col2:
                        new_status = st.selectbox(
                            "Status:",
                            ["Planejada", "Em Execução", "Concluída", "Cancelada"],
                            index=["Planejada", "Em Execução", "Concluída", "Cancelada"].index(action.get('status', 'Planejada')),
                            key=f"action_status_{i}_{self.project_id}"
                        )
                        
                        audit_data['corrective_actions'][i]['status'] = new_status
                        
                        if st.button("🗑️", key=f"remove_action_{i}_{self.project_id}"):
                            audit_data['corrective_actions'].pop(i)
                            st.rerun()
            
            # Estatísticas
            total_actions = len(audit_data['corrective_actions'])
            completed_actions = len([a for a in audit_data['corrective_actions'] if a.get('status') == 'Concluída'])
            overdue_actions = len([a for a in audit_data['corrective_actions'] 
                                 if datetime.fromisoformat(a['due_date']).date() < datetime.now().date() 
                                 and a.get('status') != 'Concluída'])
            
            col_act1, col_act2, col_act3 = st.columns(3)
            
            with col_act1:
                st.metric("Total de Ações", total_actions)
            
            with col_act2:
                st.metric("Concluídas", f"{completed_actions}/{total_actions}")
            
            with col_act3:
                st.metric("Atrasadas", overdue_actions)
        else:
            st.info("⚡ Nenhuma ação corretiva definida ainda.")
    
    def _show_action_buttons(self, audit_data: Dict):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Auditoria", key=f"save_{self.tool_name}_{self.project_id}", use_container_width=True):
                success = self.manager.save_tool_data(self.tool_name, audit_data, completed=False)
                if success:
                    st.success("💾 Auditoria salva!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("✅ Finalizar Auditoria", key=f"complete_{self.tool_name}_{self.project_id}", use_container_width=True, type="primary"):
                if self._validate_audit(audit_data):
                    success = self.manager.save_tool_data(self.tool_name, audit_data, completed=True)
                    if success:
                        st.success("✅ Auditoria de sustentabilidade finalizada!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao finalizar")
                else:
                    st.error("❌ Complete os requisitos mínimos")
    
    def _validate_audit(self, audit_data: Dict) -> bool:
        """Valida se a auditoria está completa"""
        # Verificar plano
        plan = audit_data.get('audit_plan', {})
        if not plan.get('objectives') or not plan.get('scope'):
            st.error("❌ Complete o plano de auditoria (objetivos e escopo)")
            return False
        
        # Verificar checklist
        if not audit_data.get('audit_checklist'):
            st.error("❌ Adicione itens ao checklist de auditoria")
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
        ("📈 Monitoramento Estatístico", "statistical_monitoring", StatisticalMonitoringTool),
        ("📋 Documentação Padrão", "standard_documentation", StandardDocumentationTool),
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
