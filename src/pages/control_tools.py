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
        
        solution_data = improve_data.get('solution_development', {}).get('data', {})
        if solution_data.get('solutions'):
            results['implemented_solutions'] = [
                sol for sol in solution_data['solutions'] 
                if sol.get('status') == 'Aprovada'
            ]
        
        pilot_data = improve_data.get('pilot_implementation', {}).get('data', {})
        if pilot_data.get('results'):
            results['pilot_results'] = pilot_data['results']
        
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
        
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ **Plano de controle finalizado**")
        else:
            st.info("⏳ **Plano em desenvolvimento**")
        
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
        
        self._show_improve_summary()
        self._show_control_tabs(control_data)
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
        """Gerenciamento de pontos de controle - VERSÃO ULTRA SIMPLIFICADA"""
        st.markdown("#### 🎯 Pontos de Controle")
        
        if 'control_points' not in control_data or control_data['control_points'] is None:
            control_data['control_points'] = []
        
        # Adicionar novo ponto
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
        
        if not control_data.get('control_points'):
            st.info("🎯 Nenhum ponto de controle definido.")
            return
        
        # Selecionar ponto
        point_names = [f"{i}. {p['name']}" for i, p in enumerate(control_data['control_points'])]
        
        selected_point_label = st.selectbox(
            "🎯 Selecione um Ponto de Controle:",
            point_names,
            key=f"select_point_{self.project_id}"
        )
        
        if not selected_point_label:
            return
        
        point_idx = int(selected_point_label.split('.')[0])
        point = control_data['control_points'][point_idx]
        
        # Informações do ponto
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
        
        # Abas
        tab1, tab2, tab3 = st.tabs(["➕ Adicionar Medição", "📊 Visualizar Gráfico", "📋 Gerenciar Medições"])
        
        # Tab 1: Adicionar
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
        
        # Tab 2: Gráfico
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
        
        # Tab 3: Gerenciar
        with tab3:
            measurements = point.get('measurements', [])
            
            if not measurements:
                st.info("📝 Nenhuma medição registrada.")
            else:
                st.markdown(f"#### 📋 {len(measurements)} Medição(ões) Registrada(s)")
                
                df_data = []
                for m_idx, m in enumerate(measurements):
                    status_icon = "✅" if m.get('status') == 'OK' else ("⚠️" if m.get('status') == 'WARNING' else "🚨")
                    df_data.append({
                        'ID': m_idx,
                        'Data': format_date_br(m['date']),
                        'Valor': f"{m['value']:.2f}",
                        'Status': f"{status_icon} {m.get('status', 'OK')}"
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.markdown("#### ✏️ Editar ou Excluir Medição")
                
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
        
        # Remover ponto completo
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
    
    def _check_control_status(self, value: float, point: Dict) -> str:
        """Verifica status de uma medição"""
        upper_limit = point.get('upper_limit', float('inf'))
        lower_limit = point.get('lower_limit', float('-inf'))
        target = point.get('target', 0)
        
        if lower_limit <= value <= upper_limit:
            if target != 0 and abs(value - target) / abs(target) <= 0.05:
                return 'OK'
            else:
                return 'WARNING'
        else:
            return 'ALERT'
    
    def _show_monitoring_schedule(self, control_data: Dict):
        """Cronograma de monitoramento"""
        st.markdown("#### 📅 Cronograma de Monitoramento")
        st.info("🚧 Funcionalidade de cronograma será implementada em breve")
    
    def _show_response_plans(self, control_data: Dict):
        """Planos de resposta"""
        st.markdown("#### ⚠️ Planos de Resposta")
        st.info("🚧 Funcionalidade de planos de resposta será implementada em breve")
    
    def _show_documentation(self, control_data: Dict):
        """Documentação"""
        st.markdown("#### 📋 Documentação do Plano")
        st.info("🚧 Funcionalidade de documentação será implementada em breve")
    
    def _show_action_buttons(self, control_data: Dict):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Plano", key=f"save_{self.tool_name}_{self.project_id}", use_container_width=True):
                success = self.manager.save_tool_data(self.tool_name, control_data, completed=False)
                if success:
                    st.success("💾 Plano salvo!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("✅ Finalizar Plano", key=f"complete_{self.tool_name}_{self.project_id}", use_container_width=True, type="primary"):
                if self._validate_control_plan(control_data):
                    success = self.manager.save_tool_data(self.tool_name, control_data, completed=True)
                    if success:
                        st.success("✅ Plano finalizado!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao finalizar")
                else:
                    st.error("❌ Complete os requisitos mínimos")
    
    def _validate_control_plan(self, control_data: Dict) -> bool:
        """Valida plano"""
        if not control_data.get('control_points'):
            st.error("❌ Defina pelo menos um ponto de controle")
            return False
        
        active_points = [p for p in control_data['control_points'] if p.get('status') == 'Ativo']
        if not active_points:
            st.error("❌ Pelo menos um ponto deve estar ativo")
            return False
        
        return True


def show_control_phase():
    """Interface principal da fase Control"""
    st.title("🎮 Fase CONTROL")
    st.markdown("Controle e sustente as melhorias implementadas no processo.")
    
    if 'current_project' not in st.session_state or not st.session_state.current_project:
        st.warning("⚠️ Selecione um projeto primeiro")
        return
    
    project_data = st.session_state.current_project
    
    improve_data = project_data.get('improve', {})
    improve_completed = any(tool.get('completed', False) for tool in improve_data.values() if isinstance(tool, dict))
    
    if not improve_completed:
        st.warning("⚠️ **A fase Improve deve ser concluída antes do Control**")
        st.info("💡 Complete pelo menos uma ferramenta da fase Improve para prosseguir")
        return
    
    control_manager = ControlPhaseManager(project_data)
    
    st.markdown("## 🛠️ Ferramentas da Fase Control")
    
    tools = [
        ("📊 Plano de Controle", "control_plan", ControlPlanTool),
    ]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        is_completed = control_manager.is_tool_completed("control_plan")
        if is_completed:
            st.success("✅ Plano de Controle")
        else:
            st.info("⏳ Plano de Controle")
    
    with col2:
        st.info("🚧 Monitoramento Estatístico")
    
    with col3:
        st.info("🚧 Documentação Padrão")
    
    with col4:
        st.info("🚧 Auditoria")
    
    selected_tool = st.selectbox(
        "Selecione uma ferramenta:",
        tools,
        format_func=lambda x: x[0]
    )
    
    if selected_tool:
        tool_name, tool_key, tool_class = selected_tool
        
        st.divider()
        
        tool_instance = tool_class(control_manager)
        tool_instance.show()


if __name__ == "__main__":
    show_control_phase()
