"""
🎮 CONTROL TOOLS - VERSÃO CORRIGIDA DEFINITIVA
✅ Chaves únicas em TODOS os widgets
✅ Medições visíveis e editáveis
✅ Exclusão funcional
✅ Sem erros de duplicação
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List
import warnings

warnings.filterwarnings('ignore')

try:
    from src.utils.project_manager import ProjectManager
except ImportError:
    try:
        from utils.project_manager import ProjectManager
    except ImportError:
        st.error("❌ Erro ao importar ProjectManager")
        st.stop()


class ControlPhaseManager:
    """Gerenciador da fase Control"""
    
    def __init__(self, project_data: Dict):
        self.project_data = project_data
        self.project_id = project_data.get('id')
        self.project_manager = ProjectManager()
    
    def save_tool_data(self, tool_name: str, data: Dict, completed: bool = False) -> bool:
        """Salva dados com limpeza de tipos"""
        try:
            cleaned_data = self._clean_numpy_types(data)
            
            update_data = {
                f'control.{tool_name}.data': cleaned_data,
                f'control.{tool_name}.completed': completed,
                f'control.{tool_name}.updated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            success = self.project_manager.update_project(self.project_id, update_data)
            
            if success and 'current_project' in st.session_state:
                if 'control' not in st.session_state.current_project:
                    st.session_state.current_project['control'] = {}
                
                st.session_state.current_project['control'][tool_name] = {
                    'data': cleaned_data,
                    'completed': completed,
                    'updated_at': datetime.now().isoformat()
                }
            
            return success
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar: {str(e)}")
            return False
    
    def _clean_numpy_types(self, obj):
        """Limpa tipos numpy"""
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
        """Verifica se ferramenta foi concluída"""
        control_data = self.project_data.get('control', {})
        tool_data = control_data.get(tool_name, {})
        return tool_data.get('completed', False) if isinstance(tool_data, dict) else False
    
    def get_tool_data(self, tool_name: str) -> Dict:
        """Recupera dados da ferramenta"""
        control_data = self.project_data.get('control', {})
        tool_data = control_data.get(tool_name, {})
        return tool_data.get('data', {}) if isinstance(tool_data, dict) else {}


class ControlPlanTool:
    """Ferramenta de Plano de Controle - CORRIGIDA"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "control_plan"
    
    def show(self):
        """Interface principal"""
        st.markdown("## 📊 Plano de Controle")
        
        # Status
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ Plano finalizado")
        else:
            st.info("⏳ Plano em desenvolvimento")
        
        # Inicializar dados
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data or {
                'control_points': [],
                'response_plans': []
            }
        
        control_data = st.session_state[session_key]
        
        # Tabs
        tab1, tab2 = st.tabs(["🎯 Pontos de Controle", "⚠️ Planos de Resposta"])
        
        with tab1:
            self._show_control_points(control_data)
        
        with tab2:
            self._show_response_plans(control_data)
        
        # Botões de ação
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar", key=f"save_{self.tool_name}", use_container_width=True):
                success = self.manager.save_tool_data(self.tool_name, control_data, completed=False)
                if success:
                    st.success("💾 Salvo!")
                    st.rerun()
        
        with col2:
            if st.button("✅ Finalizar", key=f"complete_{self.tool_name}", use_container_width=True, type="primary"):
                if control_data.get('control_points'):
                    success = self.manager.save_tool_data(self.tool_name, control_data, completed=True)
                    if success:
                        st.success("✅ Finalizado!")
                        st.balloons()
                        st.rerun()
                else:
                    st.error("❌ Adicione pelo menos um ponto de controle")
    
    def _show_control_points(self, control_data: Dict):
        """Gerenciar pontos de controle - CHAVES ÚNICAS"""
        st.markdown("### 🎯 Pontos de Controle")
        
        # Adicionar novo ponto
        with st.expander("➕ Adicionar Ponto"):
            # CHAVE ÚNICA: usar timestamp
            form_id = int(datetime.now().timestamp() * 1000)
            
            col1, col2 = st.columns(2)
            
            with col1:
                point_name = st.text_input(
                    "Nome *", 
                    key=f"pt_name_{form_id}",
                    placeholder="Ex: Taxa de defeitos"
                )
                metric_name = st.text_input(
                    "Métrica *", 
                    key=f"pt_metric_{form_id}",
                    placeholder="Ex: Defeitos por unidade"
                )
                unit = st.text_input(
                    "Unidade", 
                    key=f"pt_unit_{form_id}",
                    placeholder="Ex: ppm, %"
                )
            
            with col2:
                target = st.number_input(
                    "Meta *", 
                    key=f"pt_target_{form_id}",
                    step=0.01, 
                    format="%.2f"
                )
                lower_limit = st.number_input(
                    "Limite Inferior *", 
                    key=f"pt_lcl_{form_id}",
                    step=0.01, 
                    format="%.2f"
                )
                upper_limit = st.number_input(
                    "Limite Superior *", 
                    key=f"pt_ucl_{form_id}",
                    step=0.01, 
                    format="%.2f"
                )
            
            responsible = st.text_input(
                "Responsável *", 
                key=f"pt_resp_{form_id}"
            )
            
            if st.button("➕ Adicionar", key=f"add_pt_{form_id}"):
                if point_name and metric_name and responsible:
                    new_point = {
                        'id': f"point_{len(control_data['control_points'])}_{int(datetime.now().timestamp())}",
                        'name': point_name.strip(),
                        'metric': metric_name.strip(),
                        'unit': unit.strip(),
                        'target': float(target),
                        'lower_limit': float(lower_limit),
                        'upper_limit': float(upper_limit),
                        'responsible': responsible.strip(),
                        'status': 'Ativo',
                        'measurements': [],
                        'created_at': datetime.now().isoformat()
                    }
                    
                    control_data['control_points'].append(new_point)
                    st.success(f"✅ Ponto '{point_name}' adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios")
        
        # Exibir pontos existentes
        if control_data.get('control_points'):
            st.markdown("##### 📊 Pontos Definidos")
            
            for idx, point in enumerate(control_data['control_points']):
                point_id = point.get('id', f"point_{idx}")
                
                with st.expander(f"🎯 {point['name']} ({point.get('status', 'Ativo')})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Métrica:** {point['metric']} ({point.get('unit', '')})")
                        st.write(f"**Meta:** {point.get('target', 0)}")
                        st.write(f"**Limites:** [{point.get('lower_limit', 0)} - {point.get('upper_limit', 0)}]")
                        st.write(f"**Responsável:** {point.get('responsible', 'N/A')}")
                    
                    with col2:
                        # Adicionar medição - CHAVE ÚNICA
                        new_value = st.number_input(
                            "Nova medição:",
                            key=f"meas_val_{idx}_{point_id}",
                            step=0.01,
                            label_visibility="collapsed"
                        )
                        
                        if st.button("➕", key=f"add_meas_{idx}_{point_id}"):
                            if 'measurements' not in control_data['control_points'][idx]:
                                control_data['control_points'][idx]['measurements'] = []
                            
                            status = self._check_status(new_value, point)
                            
                            control_data['control_points'][idx]['measurements'].append({
                                'id': f"meas_{int(datetime.now().timestamp() * 1000)}",
                                'date': datetime.now().date().isoformat(),
                                'value': float(new_value),
                                'status': status,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            st.success("✅ Medição adicionada!")
                            st.rerun()
                        
                        # Botão de exclusão
                        if st.button("🗑️ Remover Ponto", key=f"del_pt_{idx}_{point_id}"):
                            control_data['control_points'].pop(idx)
                            st.success("✅ Ponto removido!")
                            st.rerun()
                    
                    # MOSTRAR MEDIÇÕES - CORRIGIDO
                    measurements = point.get('measurements', [])
                    if measurements:
                        st.markdown("---")
                        st.markdown("**📋 Medições Registradas:**")
                        
                        # Tabela de medições
                        for m_idx, meas in enumerate(measurements):
                            meas_id = meas.get('id', f"meas_{m_idx}")
                            meas_date = datetime.fromisoformat(meas['date']).strftime('%d/%m/%Y')
                            
                            col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns([2, 2, 1, 1, 1])
                            
                            with col_m1:
                                st.write(f"📅 {meas_date}")
                            
                            with col_m2:
                                st.write(f"**{meas['value']} {point.get('unit', '')}**")
                            
                            with col_m3:
                                status = meas.get('status', 'OK')
                                if status == 'OK':
                                    st.success("✅")
                                elif status == 'WARNING':
                                    st.warning("⚠️")
                                else:
                                    st.error("🚨")
                            
                            with col_m4:
                                # Editar - CHAVE ÚNICA
                                if st.button("✏️", key=f"edit_meas_{idx}_{m_idx}_{meas_id}"):
                                    st.session_state[f"editing_{idx}_{m_idx}"] = True
                                    st.rerun()
                            
                            with col_m5:
                                # Excluir - CHAVE ÚNICA
                                if st.button("🗑️", key=f"del_meas_{idx}_{m_idx}_{meas_id}"):
                                    control_data['control_points'][idx]['measurements'].pop(m_idx)
                                    st.success("✅ Medição removida!")
                                    st.rerun()
                            
                            # Modo edição
                            if st.session_state.get(f"editing_{idx}_{m_idx}", False):
                                with st.container():
                                    col_e1, col_e2, col_e3 = st.columns([2, 2, 1])
                                    
                                    with col_e1:
                                        new_date = st.date_input(
                                            "Data:",
                                            value=datetime.fromisoformat(meas['date']).date(),
                                            key=f"edit_date_{idx}_{m_idx}_{meas_id}"
                                        )
                                    
                                    with col_e2:
                                        new_val = st.number_input(
                                            "Valor:",
                                            value=float(meas['value']),
                                            key=f"edit_val_{idx}_{m_idx}_{meas_id}",
                                            step=0.01
                                        )
                                    
                                    with col_e3:
                                        if st.button("💾", key=f"save_edit_{idx}_{m_idx}_{meas_id}"):
                                            new_status = self._check_status(new_val, point)
                                            
                                            control_data['control_points'][idx]['measurements'][m_idx] = {
                                                'id': meas_id,
                                                'date': new_date.isoformat(),
                                                'value': float(new_val),
                                                'status': new_status,
                                                'timestamp': datetime.now().isoformat()
                                            }
                                            
                                            del st.session_state[f"editing_{idx}_{m_idx}"]
                                            st.success("✅ Atualizado!")
                                            st.rerun()
                        
                        # Gráfico
                        if len(measurements) >= 2:
                            self._plot_chart(point, measurements)
                    else:
                        st.info("📝 Nenhuma medição registrada")
        else:
            st.info("💡 Adicione o primeiro ponto de controle")
    
    def _check_status(self, value: float, point: Dict) -> str:
        """Verifica status da medição"""
        ucl = point.get('upper_limit', float('inf'))
        lcl = point.get('lower_limit', float('-inf'))
        target = point.get('target', 0)
        
        if value > ucl or value < lcl:
            return 'ALERT'
        elif target != 0 and abs(value - target) / abs(target) > 0.1:
            return 'WARNING'
        else:
            return 'OK'
    
    def _plot_chart(self, point: Dict, measurements: List[Dict]):
        """Plota gráfico de controle"""
        dates = [datetime.fromisoformat(m['date']) for m in measurements]
        values = [float(m['value']) for m in measurements]
        
        fig = go.Figure()
        
        colors = ['green' if m['status'] == 'OK' else 'orange' if m['status'] == 'WARNING' else 'red' 
                  for m in measurements]
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name='Medições',
            line=dict(color='blue', width=2),
            marker=dict(size=8, color=colors)
        ))
        
        fig.add_hline(y=point['target'], line_dash="solid", line_color="green", annotation_text="Meta")
        fig.add_hline(y=point['upper_limit'], line_dash="dash", line_color="red", annotation_text="LSC")
        fig.add_hline(y=point['lower_limit'], line_dash="dash", line_color="red", annotation_text="LIC")
        
        fig.update_layout(
            title=f"Gráfico de Controle - {point['name']}",
            xaxis_title="Data",
            yaxis_title=f"{point['metric']} ({point.get('unit', '')})",
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_response_plans(self, control_data: Dict):
        """Planos de resposta - CHAVES ÚNICAS"""
        st.markdown("### ⚠️ Planos de Resposta")
        
        # Adicionar plano
        with st.expander("➕ Adicionar Plano"):
            plan_id = int(datetime.now().timestamp() * 1000)
            
            trigger = st.selectbox(
                "Gatilho:",
                ["Fora dos limites", "Tendência negativa", "Meta não atingida", "Outro"],
                key=f"plan_trigger_{plan_id}"
            )
            
            severity = st.select_slider(
                "Severidade:",
                options=["Baixa", "Média", "Alta", "Crítica"],
                key=f"plan_severity_{plan_id}"
            )
            
            description = st.text_area(
                "Descrição:",
                key=f"plan_desc_{plan_id}",
                height=80
            )
            
            actions = st.text_area(
                "Ações:",
                key=f"plan_actions_{plan_id}",
                height=100
            )
            
            if st.button("⚠️ Adicionar", key=f"add_plan_{plan_id}"):
                if description and actions:
                    control_data['response_plans'].append({
                        'id': f"plan_{len(control_data['response_plans'])}_{plan_id}",
                        'trigger': trigger,
                        'severity': severity,
                        'description': description,
                        'actions': actions,
                        'created_at': datetime.now().isoformat()
                    })
                    st.success("✅ Plano adicionado!")
                    st.rerun()
        
        # Mostrar planos
        if control_data.get('response_plans'):
            for idx, plan in enumerate(control_data['response_plans']):
                plan_id = plan.get('id', f"plan_{idx}")
                
                severity_icons = {"Crítica": "🔴", "Alta": "🟠", "Média": "🟡", "Baixa": "🟢"}
                icon = severity_icons.get(plan['severity'], "⚪")
                
                with st.expander(f"{icon} {plan['trigger']} - {plan['severity']}"):
                    st.write(f"**Descrição:** {plan['description']}")
                    st.write(f"**Ações:** {plan['actions']}")
                    
                    if st.button("🗑️ Remover", key=f"del_plan_{idx}_{plan_id}"):
                        control_data['response_plans'].pop(idx)
                        st.success("✅ Plano removido!")
                        st.rerun()


class StandardDocumentationTool:
    """Documentação - CHAVES ÚNICAS"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "documentation"
    
    def show(self):
        """Interface principal"""
        st.markdown("## 📋 Documentação")
        
        is_completed = self.manager.is_tool_completed(self.tool_name)
        if is_completed:
            st.success("✅ Documentação completa")
        else:
            st.info("⏳ Em desenvolvimento")
        
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data or {
                'procedures': [],
                'work_instructions': [],
                'training_materials': []
            }
        
        doc_data = st.session_state[session_key]
        
        tab1, tab2, tab3 = st.tabs(["📄 POPs", "📝 Instruções", "🎓 Treinamento"])
        
        with tab1:
            self._show_pops(doc_data)
        
        with tab2:
            self._show_instructions(doc_data)
        
        with tab3:
            self._show_training(doc_data)
        
        # Botões
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar", key=f"save_{self.tool_name}", use_container_width=True):
                success = self.manager.save_tool_data(self.tool_name, doc_data, completed=False)
                if success:
                    st.success("💾 Salvo!")
                    st.rerun()
        
        with col2:
            if st.button("✅ Finalizar", key=f"complete_{self.tool_name}", use_container_width=True, type="primary"):
                if doc_data.get('procedures'):
                    success = self.manager.save_tool_data(self.tool_name, doc_data, completed=True)
                    if success:
                        st.success("✅ Finalizado!")
                        st.balloons()
                        st.rerun()
                else:
                    st.error("❌ Adicione pelo menos um POP")
    
    def _show_pops(self, doc_data: Dict):
        """POPs - CHAVES ÚNICAS"""
        st.markdown("### 📄 Procedimentos Operacionais Padrão")
        
        with st.expander("➕ Novo POP"):
            pop_id = int(datetime.now().timestamp() * 1000)
            
            title = st.text_input("Título *", key=f"pop_title_{pop_id}")
            code = st.text_input("Código", key=f"pop_code_{pop_id}", placeholder="POP-001")
            steps = st.text_area("Procedimento *", key=f"pop_steps_{pop_id}", height=150)
            
            if st.button("📄 Adicionar", key=f"add_pop_{pop_id}"):
                if title and steps:
                    doc_data['procedures'].append({
                        'id': f"pop_{len(doc_data['procedures'])}_{pop_id}",
                        'title': title,
                        'code': code,
                        'steps': steps,
                        'created_at': datetime.now().isoformat()
                    })
                    st.success("✅ POP adicionado!")
                    st.rerun()
        
        for idx, pop in enumerate(doc_data.get('procedures', [])):
            pop_id = pop.get('id', f"pop_{idx}")
            with st.expander(f"📄 {pop['title']}"):
                st.write(f"**Código:** {pop.get('code', 'N/A')}")
                st.text(pop['steps'])
                
                if st.button("🗑️ Remover", key=f"del_pop_{idx}_{pop_id}"):
                    doc_data['procedures'].pop(idx)
                    st.rerun()
    
    def _show_instructions(self, doc_data: Dict):
        """Instruções - CHAVES ÚNICAS"""
        st.markdown("### 📝 Instruções de Trabalho")
        
        with st.expander("➕ Nova Instrução"):
            wi_id = int(datetime.now().timestamp() * 1000)
            
            title = st.text_input("Título *", key=f"wi_title_{wi_id}")
            instructions = st.text_area("Instruções *", key=f"wi_inst_{wi_id}", height=150)
            
            if st.button("📝 Adicionar", key=f"add_wi_{wi_id}"):
                if title and instructions:
                    doc_data['work_instructions'].append({
                        'id': f"wi_{len(doc_data['work_instructions'])}_{wi_id}",
                        'title': title,
                        'instructions': instructions,
                        'created_at': datetime.now().isoformat()
                    })
                    st.success("✅ Instrução adicionada!")
                    st.rerun()
        
        for idx, wi in enumerate(doc_data.get('work_instructions', [])):
            wi_id = wi.get('id', f"wi_{idx}")
            with st.expander(f"📝 {wi['title']}"):
                st.text(wi['instructions'])
                
                if st.button("🗑️ Remover", key=f"del_wi_{idx}_{wi_id}"):
                    doc_data['work_instructions'].pop(idx)
                    st.rerun()
    
    def _show_training(self, doc_data: Dict):
        """Treinamento - CHAVES ÚNICAS CORRIGIDAS"""
        st.markdown("### 🎓 Material de Treinamento")
        
        with st.expander("➕ Novo Material"):
            # CORREÇÃO: Usar timestamp único
            tm_id = int(datetime.now().timestamp() * 1000)
            
            title = st.text_input("Título *", key=f"tm_title_{tm_id}_{self.project_id}")
            type_mat = st.selectbox(
                "Tipo", 
                ["Apresentação", "Vídeo", "Manual", "Quiz"],
                key=f"tm_type_{tm_id}_{self.project_id}"
            )
            description = st.text_area(
                "Descrição *", 
                key=f"tm_desc_{tm_id}_{self.project_id}",
                height=100
            )
            
            if st.button("🎓 Adicionar", key=f"add_tm_{tm_id}_{self.project_id}"):
                if title and description:
                    doc_data['training_materials'].append({
                        'id': f"tm_{len(doc_data['training_materials'])}_{tm_id}",
                        'title': title,
                        'type': type_mat,
                        'description': description,
                        'created_at': datetime.now().isoformat()
                    })
                    st.success("✅ Material adicionado!")
                    st.rerun()
        
        for idx, mat in enumerate(doc_data.get('training_materials', [])):
            mat_id = mat.get('id', f"tm_{idx}")
            with st.expander(f"🎓 {mat['title']} ({mat['type']})"):
                st.write(mat['description'])
                
                if st.button("🗑️ Remover", key=f"del_tm_{idx}_{mat_id}_{self.project_id}"):
                    doc_data['training_materials'].pop(idx)
                    st.rerun()


def show_control_phase():
    """Fase Control - VERSÃO CORRIGIDA"""
    st.title("🎮 Fase CONTROL")
    
    if 'current_project' not in st.session_state or not st.session_state.current_project:
        st.warning("⚠️ Selecione um projeto primeiro")
        return
    
    project_data = st.session_state.current_project
    control_manager = ControlPhaseManager(project_data)
    
    st.markdown("## 🛠️ Ferramentas")
    
    tools = [
        ("📊 Plano de Controle", "control_plan", ControlPlanTool),
        ("📋 Documentação", "documentation", StandardDocumentationTool)
    ]
    
    # Status
    cols = st.columns(len(tools))
    for idx, (name, key, tool_class) in enumerate(tools):
        with cols[idx]:
            is_completed = control_manager.is_tool_completed(key)
            if is_completed:
                st.success(f"✅ {name.split(' ', 1)[1]}")
            else:
                st.info(f"⏳ {name.split(' ', 1)[1]}")
    
    # Seletor
    selected = st.radio(
        "Selecione:",
        tools,
        format_func=lambda x: x[0],
        horizontal=False
    )
    
    if selected:
        st.markdown("---")
        tool_name, tool_key, tool_class = selected
        tool_instance = tool_class(control_manager)
        tool_instance.show()


if __name__ == "__main__":
    show_control_phase()
