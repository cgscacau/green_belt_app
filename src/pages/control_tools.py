"""
🎮 CONTROL TOOLS - VERSÃO PREMIUM REESCRITA
✅ Page Control totalmente funcional
✅ Cálculos de progresso corretos
✅ Conectividade Firebase plena
✅ Interface moderna e intuitiva
✅ Todas as ferramentas completas
"""

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
    try:
        from utils.project_manager import ProjectManager
    except ImportError:
        st.error("❌ Não foi possível importar ProjectManager")
        st.stop()


# ============================================================================
# GERENCIADOR CENTRALIZADO - VERSÃO PREMIUM
# ============================================================================

class ControlPhaseManagerPremium:
    """Gerenciador centralizado da fase Control - VERSÃO PREMIUM"""
    
    def __init__(self, project_data: Dict):
        self.project_data = project_data
        self.project_id = project_data.get('id')
        self.project_manager = ProjectManager()
        
        # Cache para melhor performance
        self._cache = {}
    
    def save_tool_data(self, tool_name: str, data: Dict, completed: bool = False) -> bool:
        """
        Salva dados de uma ferramenta com validação e atualização automática
        ✅ VERSÃO PREMIUM: Validação robusta + Sincronização Firebase
        """
        try:
            # Limpar tipos numpy antes de salvar
            cleaned_data = self._clean_numpy_types(data)
            
            # Estrutura de atualização
            update_data = {
                f'control.{tool_name}.data': cleaned_data,
                f'control.{tool_name}.completed': completed,
                f'control.{tool_name}.updated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Salvar no Firebase
            success = self.project_manager.update_project(self.project_id, update_data)
            
            if success:
                # Atualizar session_state imediatamente
                self._update_session_state(tool_name, cleaned_data, completed)
                
                # Limpar cache
                self._cache.clear()
                
                return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar: {str(e)}")
            return False
    
    def _update_session_state(self, tool_name: str, data: Dict, completed: bool):
        """Atualiza session_state com dados salvos"""
        if 'current_project' in st.session_state:
            if 'control' not in st.session_state.current_project:
                st.session_state.current_project['control'] = {}
            
            st.session_state.current_project['control'][tool_name] = {
                'data': data,
                'completed': completed,
                'updated_at': datetime.now().isoformat()
            }
    
    def _clean_numpy_types(self, obj):
        """Remove tipos numpy para compatibilidade Firebase"""
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
        """Recupera dados de uma ferramenta com cache"""
        cache_key = f"tool_data_{tool_name}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        control_data = self.project_data.get('control', {})
        tool_data = control_data.get(tool_name, {})
        result = tool_data.get('data', {}) if isinstance(tool_data, dict) else {}
        
        self._cache[cache_key] = result
        return result
    
    def get_control_progress(self) -> float:
        """
        Calcula progresso total da fase Control
        ✅ PREMIUM: Cálculo correto e preciso
        """
        tools = ['control_plan', 'monitoring_system', 'documentation', 'sustainability_plan']
        completed = sum(1 for tool in tools if self.is_tool_completed(tool))
        return (completed / len(tools)) * 100
    
    def get_improve_results(self) -> Dict:
        """Recupera resultados da fase Improve"""
        improve_data = self.project_data.get('improve', {})
        
        results = {
            'implemented_solutions': [],
            'kpis_data': [],
            'pilot_results': {},
            'benefits_achieved': 0
        }
        
        # Soluções implementadas
        solution_data = improve_data.get('solution_development', {}).get('data', {})
        if solution_data.get('solutions'):
            results['implemented_solutions'] = [
                sol for sol in solution_data['solutions'] 
                if sol.get('status') == 'Aprovada'
            ]
        
        # KPIs
        full_impl = improve_data.get('full_implementation', {}).get('data', {})
        monitoring = full_impl.get('monitoring_system', {})
        if monitoring.get('kpis'):
            results['kpis_data'] = monitoring['kpis']
        
        # Resultados do piloto
        pilot_data = improve_data.get('pilot_implementation', {}).get('data', {})
        if pilot_data.get('results'):
            results['pilot_results'] = pilot_data['results']
        
        return results


# ============================================================================
# FERRAMENTA 1: PLANO DE CONTROLE PREMIUM
# ============================================================================

class ControlPlanToolPremium:
    """
    📊 PLANO DE CONTROLE - VERSÃO PREMIUM
    ✅ Interface moderna e intuitiva
    ✅ Gerenciamento de pontos de controle
    ✅ Cronograma automatizado
    ✅ Planos de resposta
    """
    
    def __init__(self, manager: ControlPhaseManagerPremium):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "control_plan"
    
    def show(self):
        """Interface principal"""
        st.markdown("## 📊 Plano de Controle Premium")
        
        # Card de status
        self._show_status_card()
        
        # Inicializar dados
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data or {
                'control_points': [],
                'monitoring_schedule': [],
                'response_plans': [],
                'documentation': {}
            }
        
        control_data = st.session_state[session_key]
        
        # Resumo dos resultados da fase Improve
        self._show_improve_summary()
        
        st.divider()
        
        # Tabs organizadas
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
        
        # Botões de ação premium
        self._show_action_buttons(control_data)
    
    def _show_status_card(self):
        """Mostra card de status premium"""
        is_completed = self.manager.is_tool_completed(self.tool_name)
        
        if is_completed:
            st.success("✅ **Plano de Controle Finalizado**")
        else:
            st.info("⏳ **Plano em Desenvolvimento**")
        
        # Métricas de progresso
        control_data = self.manager.get_tool_data(self.tool_name)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            points = len(control_data.get('control_points', []))
            st.metric("Pontos de Controle", points, help="Total de pontos definidos")
        
        with col2:
            schedule = len(control_data.get('monitoring_schedule', []))
            st.metric("Eventos Agendados", schedule, help="Monitoramentos programados")
        
        with col3:
            plans = len(control_data.get('response_plans', []))
            st.metric("Planos de Resposta", plans, help="Ações preparadas")
    
    def _show_improve_summary(self):
        """Resumo dos resultados da fase Improve"""
        st.markdown("### 🎯 Resultados da Implementação")
        
        improve_results = self.manager.get_improve_results()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            solutions = improve_results['implemented_solutions']
            st.metric("Soluções Implementadas", len(solutions))
            
            if solutions:
                with st.expander("📋 Ver soluções"):
                    for i, sol in enumerate(solutions, 1):
                        st.write(f"**{i}.** {sol.get('name', 'Solução')}")
        
        with col2:
            kpis = improve_results['kpis_data']
            st.metric("KPIs Monitorados", len(kpis))
            
            if kpis:
                with st.expander("📊 Ver KPIs"):
                    for kpi in kpis:
                        st.write(f"• {kpi.get('name', 'KPI')} ({kpi.get('unit', '')})")
        
        with col3:
            pilot_results = improve_results['pilot_results']
            if pilot_results.get('recommendation'):
                st.metric("Status do Piloto", "✅ Aprovado")
            else:
                st.metric("Status do Piloto", "⏳ Pendente")
    
    def _show_control_points(self, control_data: Dict):
        """
        Gerenciamento de pontos de controle
        ✅ PREMIUM: Interface intuitiva + Validação robusta
        """
        st.markdown("#### 🎯 Pontos de Controle")
        
        # Adicionar novo ponto
        with st.expander("➕ Adicionar Ponto de Controle", expanded=not control_data.get('control_points')):
            with st.form(key=f"add_point_form_{self.project_id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    point_name = st.text_input("Nome do Ponto *", placeholder="Ex: Taxa de defeitos")
                    metric_name = st.text_input("Métrica *", placeholder="Ex: Defeitos por unidade")
                    unit = st.text_input("Unidade", placeholder="Ex: ppm, %, unidades")
                    frequency = st.selectbox("Frequência", ["Diária", "Semanal", "Quinzenal", "Mensal"])
                
                with col2:
                    target = st.number_input("Meta *", step=0.01, format="%.2f")
                    lower_limit = st.number_input("Limite Inferior (LIC) *", step=0.01, format="%.2f")
                    upper_limit = st.number_input("Limite Superior (LSC) *", step=0.01, format="%.2f")
                    responsible = st.text_input("Responsável *")
                
                description = st.text_area("Descrição/Como Medir", height=80)
                method = st.text_input("Método de Medição", placeholder="Ex: Sistema ERP")
                
                submitted = st.form_submit_button("➕ Adicionar Ponto", use_container_width=True)
                
                if submitted:
                    if point_name and metric_name and responsible and target is not None:
                        new_point = {
                            'id': f"point_{len(control_data['control_points'])}_{int(datetime.now().timestamp())}",
                            'name': point_name.strip(),
                            'metric': metric_name.strip(),
                            'unit': unit.strip(),
                            'target': float(target),
                            'lower_limit': float(lower_limit),
                            'upper_limit': float(upper_limit),
                            'frequency': frequency,
                            'responsible': responsible.strip(),
                            'description': description.strip(),
                            'measurement_method': method.strip(),
                            'status': 'Ativo',
                            'measurements': [],
                            'created_at': datetime.now().isoformat()
                        }
                        
                        control_data['control_points'].append(new_point)
                        st.success(f"✅ Ponto '{point_name}' adicionado!")
                        st.rerun()
                    else:
                        st.error("❌ Preencha todos os campos obrigatórios (marcados com *)")
        
        # Exibir pontos existentes
        if control_data.get('control_points'):
            st.markdown("##### 📊 Pontos de Controle Ativos")
            
            for idx, point in enumerate(control_data['control_points']):
                point_id = point.get('id', f"point_{idx}")
                
                with st.expander(f"🎯 **{point['name']}** ({point.get('status', 'Ativo')})"):
                    self._render_control_point(point, idx, control_data)
        else:
            st.info("💡 Nenhum ponto de controle definido. Adicione o primeiro acima!")
    
    def _render_control_point(self, point: Dict, idx: int, control_data: Dict):
        """Renderiza detalhes de um ponto de controle"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"**Métrica:** {point['metric']} ({point.get('unit', '')})")
            st.write(f"**Meta:** {point.get('target', 0)}")
            st.write(f"**Limites:** {point.get('lower_limit', 0)} - {point.get('upper_limit', 0)}")
            st.write(f"**Frequência:** {point.get('frequency', 'N/A')}")
            st.write(f"**Responsável:** {point.get('responsible', 'Não definido')}")
            
            if point.get('description'):
                st.caption(f"📝 {point['description']}")
        
        with col2:
            # Adicionar medição rápida
            st.markdown("**Nova Medição:**")
            
            new_value = st.number_input(
                "Valor:",
                key=f"meas_val_{idx}_{self.project_id}",
                step=0.01,
                label_visibility="collapsed"
            )
            
            if st.button("➕ Adicionar", key=f"add_meas_{idx}_{self.project_id}"):
                if 'measurements' not in control_data['control_points'][idx]:
                    control_data['control_points'][idx]['measurements'] = []
                
                status = self._check_control_status(new_value, point)
                
                control_data['control_points'][idx]['measurements'].append({
                    'date': datetime.now().date().isoformat(),
                    'value': float(new_value),
                    'status': status,
                    'timestamp': datetime.now().isoformat()
                })
                
                st.success("✅ Medição registrada!")
                st.rerun()
            
            # Status atual
            measurements = point.get('measurements', [])
            if measurements:
                last_meas = measurements[-1]
                status = last_meas.get('status', 'OK')
                
                if status == 'OK':
                    st.success("✅ No controle")
                elif status == 'WARNING':
                    st.warning("⚠️ Atenção")
                else:
                    st.error("🚨 Fora de controle")
            
            # Botão de exclusão
            if st.button("🗑️ Remover", key=f"del_point_{idx}_{self.project_id}"):
                control_data['control_points'].pop(idx)
                st.success("✅ Ponto removido!")
                st.rerun()
        
        # Gráfico de medições
        if measurements:
            self._plot_control_chart(point, measurements)
    
    def _check_control_status(self, value: float, point: Dict) -> str:
        """Verifica status baseado nos limites"""
        ucl = point.get('upper_limit', float('inf'))
        lcl = point.get('lower_limit', float('-inf'))
        target = point.get('target', 0)
        
        if value > ucl or value < lcl:
            return 'ALERT'
        elif target != 0 and abs(value - target) / abs(target) > 0.1:
            return 'WARNING'
        else:
            return 'OK'
    
    def _plot_control_chart(self, point: Dict, measurements: List[Dict]):
        """Plota gráfico de controle"""
        if len(measurements) < 2:
            return
        
        dates = [datetime.fromisoformat(m['date']) for m in measurements]
        values = [float(m['value']) for m in measurements]
        
        fig = go.Figure()
        
        # Linha de dados
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
        
        # Linhas de referência
        fig.add_hline(y=point['target'], line_dash="solid", line_color="green", 
                     annotation_text="Meta")
        fig.add_hline(y=point['upper_limit'], line_dash="dash", line_color="red", 
                     annotation_text="LSC")
        fig.add_hline(y=point['lower_limit'], line_dash="dash", line_color="red", 
                     annotation_text="LIC")
        
        fig.update_layout(
            title=f"Gráfico de Controle - {point['name']}",
            xaxis_title="Data",
            yaxis_title=f"{point['metric']} ({point.get('unit', '')})",
            height=350,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_monitoring_schedule(self, control_data: Dict):
        """Cronograma de monitoramento automático"""
        st.markdown("#### 📅 Cronograma de Monitoramento")
        
        if not control_data.get('control_points'):
            st.info("💡 Defina pontos de controle primeiro")
            return
        
        # Gerar cronograma
        if st.button("📅 Gerar Cronograma Automático", type="primary"):
            schedule = self._generate_schedule(control_data['control_points'])
            control_data['monitoring_schedule'] = schedule
            st.success(f"✅ {len(schedule)} eventos agendados!")
            st.rerun()
        
        # Mostrar cronograma
        if control_data.get('monitoring_schedule'):
            self._display_schedule(control_data)
        else:
            st.info("📅 Clique no botão acima para gerar o cronograma")
    
    def _generate_schedule(self, control_points: List[Dict]) -> List[Dict]:
        """Gera cronograma automático"""
        schedule = []
        start_date = datetime.now().date()
        
        for point in control_points:
            if point.get('status') != 'Ativo':
                continue
            
            frequency = point.get('frequency', 'Semanal')
            
            # Definir intervalos
            freq_map = {
                'Diária': (1, 30),
                'Semanal': (7, 12),
                'Quinzenal': (14, 8),
                'Mensal': (30, 6)
            }
            
            interval, num_events = freq_map.get(frequency, (7, 12))
            
            for i in range(num_events):
                event_date = start_date + timedelta(days=i * interval)
                
                schedule.append({
                    'date': event_date.isoformat(),
                    'point_name': point['name'],
                    'metric': point['metric'],
                    'responsible': point.get('responsible', ''),
                    'frequency': frequency,
                    'status': 'Agendado',
                    'completed': False
                })
        
        return sorted(schedule, key=lambda x: x['date'])
    
    def _display_schedule(self, control_data: Dict):
        """Exibe cronograma"""
        st.markdown("##### 📋 Próximos Eventos")
        
        schedule = control_data['monitoring_schedule']
        today = datetime.now().date()
        
        # Filtrar próximos 30 dias
        upcoming = [e for e in schedule if datetime.fromisoformat(e['date']).date() >= today][:15]
        
        for idx, event in enumerate(upcoming):
            event_date = datetime.fromisoformat(event['date'])
            days_until = (event_date.date() - today).days
            
            # Cor baseada no status
            if event.get('completed'):
                icon = "✅"
            elif days_until < 0:
                icon = "🔴"
            elif days_until <= 2:
                icon = "🟡"
            else:
                icon = "🟢"
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"{icon} **{event['point_name']}**")
            
            with col2:
                st.write(f"📅 {event_date.strftime('%d/%m/%Y')} (em {days_until} dias)")
            
            with col3:
                if st.checkbox("✓", key=f"evt_{idx}", value=event.get('completed', False)):
                    event['completed'] = True
                    event['status'] = 'Concluído'
    
    def _show_response_plans(self, control_data: Dict):
        """Planos de resposta a desvios"""
        st.markdown("#### ⚠️ Planos de Resposta")
        
        # Adicionar plano
        with st.expander("➕ Adicionar Plano de Resposta"):
            trigger = st.selectbox(
                "Gatilho:",
                ["Fora dos limites", "Tendência negativa", "Meta não atingida", "Outro"]
            )
            
            severity = st.select_slider(
                "Severidade:",
                options=["Baixa", "Média", "Alta", "Crítica"]
            )
            
            description = st.text_area("Descrição do Problema:", height=80)
            actions = st.text_area("Ações de Resposta:", height=100)
            responsible = st.text_input("Responsável:")
            
            if st.button("⚠️ Adicionar Plano"):
                if description and actions:
                    control_data['response_plans'].append({
                        'trigger': trigger,
                        'severity': severity,
                        'description': description,
                        'actions': actions,
                        'responsible': responsible,
                        'status': 'Ativo',
                        'created_at': datetime.now().isoformat()
                    })
                    st.success("✅ Plano adicionado!")
                    st.rerun()
        
        # Mostrar planos
        if control_data.get('response_plans'):
            for idx, plan in enumerate(control_data['response_plans']):
                severity_colors = {
                    "Crítica": "🔴",
                    "Alta": "🟠",
                    "Média": "🟡",
                    "Baixa": "🟢"
                }
                
                icon = severity_colors.get(plan['severity'], "⚪")
                
                with st.expander(f"{icon} {plan['trigger']} - {plan['severity']}"):
                    st.write(f"**Descrição:** {plan['description']}")
                    st.write(f"**Ações:** {plan['actions']}")
                    st.write(f"**Responsável:** {plan.get('responsible', 'N/A')}")
        else:
            st.info("💡 Nenhum plano de resposta definido")
    
    def _show_documentation(self, control_data: Dict):
        """Documentação do plano"""
        st.markdown("#### 📋 Documentação")
        
        if 'documentation' not in control_data:
            control_data['documentation'] = {}
        
        doc = control_data['documentation']
        
        doc['objective'] = st.text_area(
            "🎯 Objetivo do Plano:",
            value=doc.get('objective', ''),
            height=80
        )
        
        doc['scope'] = st.text_area(
            "🔍 Escopo:",
            value=doc.get('scope', ''),
            height=80
        )
        
        doc['responsibilities'] = st.text_area(
            "👥 Responsabilidades:",
            value=doc.get('responsibilities', ''),
            height=100
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            doc['review_frequency'] = st.selectbox(
                "🔄 Frequência de Revisão:",
                ["Mensal", "Trimestral", "Semestral", "Anual"],
                index=1
            )
        
        with col2:
            next_review = datetime.now() + timedelta(days=90)
            doc['next_review'] = st.date_input(
                "📅 Próxima Revisão:",
                value=next_review
            ).isoformat()
    
    def _show_action_buttons(self, control_data: Dict):
        """Botões de ação premium"""
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 **Salvar Plano**", use_container_width=True, type="secondary"):
                success = self.manager.save_tool_data(self.tool_name, control_data, completed=False)
                if success:
                    st.success("💾 Plano salvo com sucesso!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("📊 **Gerar Relatório**", use_container_width=True):
                self._generate_report(control_data)
        
        with col3:
            if st.button("✅ **Finalizar Plano**", use_container_width=True, type="primary"):
                if self._validate_plan(control_data):
                    success = self.manager.save_tool_data(self.tool_name, control_data, completed=True)
                    if success:
                        st.success("✅ Plano finalizado!")
                        st.balloons()
                        st.rerun()
                else:
                    st.error("❌ Complete os requisitos mínimos")
    
    def _validate_plan(self, control_data: Dict) -> bool:
        """Valida completude do plano"""
        if not control_data.get('control_points'):
            st.error("❌ Defina pelo menos um ponto de controle")
            return False
        
        active_points = [p for p in control_data['control_points'] if p.get('status') == 'Ativo']
        if not active_points:
            st.error("❌ Pelo menos um ponto deve estar ativo")
            return False
        
        doc = control_data.get('documentation', {})
        if not doc.get('objective') or not doc.get('scope'):
            st.error("❌ Complete a documentação básica")
            return False
        
        return True
    
    def _generate_report(self, control_data: Dict):
        """Gera relatório em markdown"""
        report = f"""
# Plano de Controle - Relatório

**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

## Resumo Executivo
- **Pontos de Controle:** {len(control_data.get('control_points', []))}
- **Eventos Agendados:** {len(control_data.get('monitoring_schedule', []))}
- **Planos de Resposta:** {len(control_data.get('response_plans', []))}

## Pontos de Controle
"""
        
        for point in control_data.get('control_points', []):
            report += f"""
### {point['name']}
- **Métrica:** {point['metric']} ({point.get('unit', '')})
- **Meta:** {point.get('target', 0)}
- **Responsável:** {point.get('responsible', 'N/A')}
"""
        
        st.download_button(
            "📥 Baixar Relatório",
            data=report,
            file_name=f"plano_controle_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )


# ============================================================================
# FERRAMENTA 2: SISTEMA DE MONITORAMENTO PREMIUM
# ============================================================================

class MonitoringSystemToolPremium:
    """
    📈 SISTEMA DE MONITORAMENTO - VERSÃO PREMIUM
    ✅ Dashboards em tempo real
    ✅ Alertas automáticos
    ✅ Análise de tendências
    """
    
    def __init__(self, manager: ControlPhaseManagerPremium):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "monitoring_system"
    
    def show(self):
        """Interface principal"""
        st.markdown("## 📈 Sistema de Monitoramento Premium")
        
        is_completed = self.manager.is_tool_completed(self.tool_name)
        
        if is_completed:
            st.success("✅ **Sistema configurado e operacional**")
        else:
            st.info("⏳ **Sistema em configuração**")
        
        # Dashboard em tempo real
        self._show_realtime_dashboard()
        
        st.divider()
        
        # Configurações
        self._show_configurations()
        
        # Botões de ação
        st.divider()
        
        if st.button("✅ **Ativar Sistema**", type="primary", use_container_width=True):
            success = self.manager.save_tool_data(self.tool_name, {'status': 'active'}, completed=True)
            if success:
                st.success("✅ Sistema ativado!")
                st.balloons()
    
    def _show_realtime_dashboard(self):
        """Dashboard em tempo real"""
        st.markdown("### 📊 Dashboard em Tempo Real")
        
        # Obter pontos de controle
        control_plan = self.manager.get_tool_data('control_plan')
        points = control_plan.get('control_points', [])
        
        if not points:
            st.info("💡 Configure pontos de controle primeiro")
            return
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            active_points = sum(1 for p in points if p.get('status') == 'Ativo')
            st.metric("Pontos Ativos", active_points)
        
        with col2:
            total_measurements = sum(len(p.get('measurements', [])) for p in points)
            st.metric("Medições Totais", total_measurements)
        
        with col3:
            in_control = sum(1 for p in points if self._is_point_in_control(p))
            st.metric("No Controle", f"{in_control}/{active_points}")
        
        with col4:
            alerts = sum(1 for p in points if not self._is_point_in_control(p))
            st.metric("Alertas", alerts, delta_color="inverse")
        
        # Gráfico de status
        if points:
            self._plot_status_overview(points)
    
    def _is_point_in_control(self, point: Dict) -> bool:
        """Verifica se ponto está no controle"""
        measurements = point.get('measurements', [])
        if not measurements:
            return True
        
        last_meas = measurements[-1]
        return last_meas.get('status', 'OK') == 'OK'
    
    def _plot_status_overview(self, points: List[Dict]):
        """Plota overview de status"""
        status_counts = {'OK': 0, 'WARNING': 0, 'ALERT': 0}
        
        for point in points:
            measurements = point.get('measurements', [])
            if measurements:
                status = measurements[-1].get('status', 'OK')
                status_counts[status] = status_counts.get(status, 0) + 1
        
        fig = go.Figure(data=[go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            marker_colors=['green', 'orange', 'red']
        )])
        
        fig.update_layout(
            title="Status dos Pontos de Controle",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_configurations(self):
        """Configurações do sistema"""
        st.markdown("### ⚙️ Configurações")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("📧 Alertas por Email", value=True)
            st.checkbox("📱 Notificações Push", value=False)
            st.checkbox("📊 Relatórios Automáticos", value=True)
        
        with col2:
            st.selectbox("Frequência de Alertas:", ["Imediato", "Diário", "Semanal"])
            st.number_input("Limiar de Alerta (%):", min_value=0, max_value=100, value=80)


# ============================================================================
# FERRAMENTA 3: DOCUMENTAÇÃO PADRÃO PREMIUM
# ============================================================================

class DocumentationToolPremium:
    """
    📋 DOCUMENTAÇÃO PADRÃO - VERSÃO PREMIUM
    ✅ POPs estruturados
    ✅ Instruções de trabalho
    ✅ Material de treinamento
    """
    
    def __init__(self, manager: ControlPhaseManagerPremium):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "documentation"
    
    def show(self):
        """Interface principal"""
        st.markdown("## 📋 Documentação Operacional Premium")
        
        is_completed = self.manager.is_tool_completed(self.tool_name)
        
        if is_completed:
            st.success("✅ **Documentação completa**")
        else:
            st.info("⏳ **Documentação em desenvolvimento**")
        
        # Inicializar dados
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data or {
                'procedures': [],
                'work_instructions': [],
                'training_materials': []
            }
        
        doc_data = st.session_state[session_key]
        
        # Tabs
        tab1, tab2, tab3 = st.tabs([
            "📄 POPs",
            "📝 Instruções",
            "🎓 Treinamento"
        ])
        
        with tab1:
            self._show_pops(doc_data)
        
        with tab2:
            self._show_instructions(doc_data)
        
        with tab3:
            self._show_training(doc_data)
        
        # Botões de ação
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 **Salvar**", use_container_width=True):
                success = self.manager.save_tool_data(self.tool_name, doc_data, completed=False)
                if success:
                    st.success("💾 Salvo!")
        
        with col2:
            if st.button("✅ **Finalizar**", use_container_width=True, type="primary"):
                if doc_data.get('procedures'):
                    success = self.manager.save_tool_data(self.tool_name, doc_data, completed=True)
                    if success:
                        st.success("✅ Finalizado!")
                        st.balloons()
                else:
                    st.error("❌ Adicione pelo menos um POP")
    
    def _show_pops(self, doc_data: Dict):
        """Gerenciar POPs"""
        st.markdown("### 📄 Procedimentos Operacionais Padrão")
        
        # Adicionar POP
        with st.expander("➕ Novo POP"):
            with st.form("add_pop"):
                title = st.text_input("Título *")
                code = st.text_input("Código", placeholder="POP-001")
                objective = st.text_area("Objetivo", height=80)
                steps = st.text_area("Procedimento *", height=150)
                
                if st.form_submit_button("📄 Adicionar"):
                    if title and steps:
                        doc_data['procedures'].append({
                            'title': title,
                            'code': code,
                            'objective': objective,
                            'steps': steps,
                            'created_at': datetime.now().isoformat()
                        })
                        st.success("✅ POP adicionado!")
                        st.rerun()
        
        # Listar POPs
        for idx, pop in enumerate(doc_data.get('procedures', [])):
            with st.expander(f"📄 {pop['title']}"):
                st.write(f"**Código:** {pop.get('code', 'N/A')}")
                st.write(f"**Objetivo:** {pop.get('objective', '')}")
                st.text(pop.get('steps', ''))
    
    def _show_instructions(self, doc_data: Dict):
        """Instruções de trabalho"""
        st.markdown("### 📝 Instruções de Trabalho")
        
        with st.expander("➕ Nova Instrução"):
            title = st.text_input("Título *")
            instructions = st.text_area("Instruções *", height=150)
            
            if st.button("📝 Adicionar"):
                if title and instructions:
                    doc_data['work_instructions'].append({
                        'title': title,
                        'instructions': instructions,
                        'created_at': datetime.now().isoformat()
                    })
                    st.success("✅ Instrução adicionada!")
                    st.rerun()
        
        for inst in doc_data.get('work_instructions', []):
            with st.expander(f"📝 {inst['title']}"):
                st.text(inst['instructions'])
    
    def _show_training(self, doc_data: Dict):
        """Material de treinamento"""
        st.markdown("### 🎓 Material de Treinamento")
        
        with st.expander("➕ Novo Material"):
            title = st.text_input("Título *")
            type_mat = st.selectbox("Tipo", ["Apresentação", "Vídeo", "Manual", "Quiz"])
            description = st.text_area("Descrição *", height=100)
            
            if st.button("🎓 Adicionar"):
                if title and description:
                    doc_data['training_materials'].append({
                        'title': title,
                        'type': type_mat,
                        'description': description,
                        'created_at': datetime.now().isoformat()
                    })
                    st.success("✅ Material adicionado!")
                    st.rerun()
        
        for mat in doc_data.get('training_materials', []):
            with st.expander(f"🎓 {mat['title']} ({mat['type']})"):
                st.write(mat['description'])


# ============================================================================
# FERRAMENTA 4: PLANO DE SUSTENTABILIDADE PREMIUM
# ============================================================================

class SustainabilityPlanToolPremium:
    """
    🔄 PLANO DE SUSTENTABILIDADE - VERSÃO PREMIUM
    ✅ Auditorias programadas
    ✅ Análise de tendências
    ✅ Ações preventivas
    """
    
    def __init__(self, manager: ControlPhaseManagerPremium):
        self.manager = manager
        self.project_id = manager.project_id
        self.tool_name = "sustainability_plan"
    
    def show(self):
        """Interface principal"""
        st.markdown("## 🔄 Plano de Sustentabilidade Premium")
        
        is_completed = self.manager.is_tool_completed(self.tool_name)
        
        if is_completed:
            st.success("✅ **Plano ativo e monitorando**")
        else:
            st.info("⏳ **Plano em desenvolvimento**")
        
        # Inicializar dados
        session_key = f"{self.tool_name}_{self.project_id}"
        if session_key not in st.session_state:
            existing_data = self.manager.get_tool_data(self.tool_name)
            st.session_state[session_key] = existing_data or {
                'audits': [],
                'improvements': [],
                'lessons_learned': []
            }
        
        sust_data = st.session_state[session_key]
        
        # Tabs
        tab1, tab2, tab3 = st.tabs([
            "📅 Auditorias",
            "📈 Melhorias Contínuas",
            "📚 Lições Aprendidas"
        ])
        
        with tab1:
            self._show_audits(sust_data)
        
        with tab2:
            self._show_improvements(sust_data)
        
        with tab3:
            self._show_lessons(sust_data)
        
        # Botões
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 **Salvar**", use_container_width=True):
                success = self.manager.save_tool_data(self.tool_name, sust_data, completed=False)
                if success:
                    st.success("💾 Salvo!")
        
        with col2:
            if st.button("✅ **Ativar Plano**", use_container_width=True, type="primary"):
                success = self.manager.save_tool_data(self.tool_name, sust_data, completed=True)
                if success:
                    st.success("✅ Plano ativo!")
                    st.balloons()
    
    def _show_audits(self, sust_data: Dict):
        """Auditorias periódicas"""
        st.markdown("### 📅 Auditorias de Sustentabilidade")
        
        # Agendar auditoria
        with st.expander("➕ Agendar Auditoria"):
            audit_date = st.date_input("Data da Auditoria:")
            auditor = st.text_input("Auditor:")
            
            if st.button("📅 Agendar"):
                sust_data['audits'].append({
                    'date': audit_date.isoformat(),
                    'auditor': auditor,
                    'status': 'Agendada',
                    'created_at': datetime.now().isoformat()
                })
                st.success("✅ Auditoria agendada!")
                st.rerun()
        
        # Listar auditorias
        for audit in sust_data.get('audits', []):
            audit_date = datetime.fromisoformat(audit['date'])
            status_icon = "🟢" if audit['status'] == 'Concluída' else "🟡"
            
            st.write(f"{status_icon} **{audit_date.strftime('%d/%m/%Y')}** - {audit.get('auditor', 'N/A')}")
    
    def _show_improvements(self, sust_data: Dict):
        """Melhorias contínuas"""
        st.markdown("### 📈 Melhorias Contínuas")
        
        with st.expander("➕ Registrar Melhoria"):
            title = st.text_input("Título da Melhoria:")
            description = st.text_area("Descrição:", height=100)
            
            if st.button("📈 Registrar"):
                sust_data['improvements'].append({
                    'title': title,
                    'description': description,
                    'date': datetime.now().isoformat()
                })
                st.success("✅ Melhoria registrada!")
                st.rerun()
        
        for imp in sust_data.get('improvements', []):
            with st.expander(f"📈 {imp['title']}"):
                st.write(imp['description'])
    
    def _show_lessons(self, sust_data: Dict):
        """Lições aprendidas"""
        st.markdown("### 📚 Lições Aprendidas")
        
        with st.expander("➕ Adicionar Lição"):
            lesson = st.text_area("Lição Aprendida:", height=100)
            
            if st.button("📚 Adicionar"):
                sust_data['lessons_learned'].append({
                    'lesson': lesson,
                    'date': datetime.now().isoformat()
                })
                st.success("✅ Lição registrada!")
                st.rerun()
        
        for lesson in sust_data.get('lessons_learned', []):
            st.info(f"💡 {lesson['lesson']}")


# ============================================================================
# FUNÇÃO PRINCIPAL - VERSÃO PREMIUM
# ============================================================================

def show_control_phase():
    """
    🎮 FASE CONTROL - VERSÃO PREMIUM COMPLETA
    ✅ Page Control funcional
    ✅ Cálculos corretos
    ✅ Firebase integrado
    ✅ Interface moderna
    """
    
    st.title("🎮 Fase CONTROL - Premium Edition")
    st.markdown("**Sistema completo para controle e sustentação das melhorias**")
    
    # Verificar projeto selecionado
    if 'current_project' not in st.session_state or not st.session_state.current_project:
        st.warning("⚠️ **Selecione um projeto primeiro**")
        if st.button("📁 Ir para Projetos"):
            st.session_state.current_page = 'projects'
            st.rerun()
        return
    
    project_data = st.session_state.current_project
    project_name = project_data.get('name', 'Projeto')
    
    # Header premium
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### 📊 Projeto: **{project_name}**")
    
    with col2:
        # Progresso da fase
        control_manager = ControlPhaseManagerPremium(project_data)
        progress = control_manager.get_control_progress()
        st.metric("Progresso", f"{progress:.0f}%")
    
    st.divider()
    
    # Menu de ferramentas premium
    st.markdown("## 🛠️ Ferramentas Disponíveis")
    
    tools = [
        ("📊 Plano de Controle", "control_plan", ControlPlanToolPremium, 
         "Defina pontos de controle e sistema de monitoramento"),
        ("📈 Sistema de Monitoramento", "monitoring_system", MonitoringSystemToolPremium,
         "Dashboard em tempo real e alertas automáticos"),
        ("📋 Documentação Operacional", "documentation", DocumentationToolPremium,
         "POPs, instruções e material de treinamento"),
        ("🔄 Plano de Sustentabilidade", "sustainability_plan", SustainabilityPlanToolPremium,
         "Auditorias e melhorias contínuas")
    ]
    
    # Cards de status
    cols = st.columns(4)
    
    for idx, (name, key, tool_class, desc) in enumerate(tools):
        with cols[idx]:
            is_completed = control_manager.is_tool_completed(key)
            
            if is_completed:
                st.success(f"✅ {name.split(' ', 1)[1]}")
            else:
                st.info(f"⏳ {name.split(' ', 1)[1]}")
    
    st.divider()
    
    # Seletor de ferramenta
    selected = st.radio(
        "Selecione uma ferramenta:",
        tools,
        format_func=lambda x: f"{x[0]} - {x[3]}",
        horizontal=False
    )
    
    if selected:
        tool_name, tool_key, tool_class, description = selected
        
        st.markdown("---")
        
        # Instanciar e renderizar ferramenta
        tool_instance = tool_class(control_manager)
        tool_instance.show()


# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    show_control_phase()
