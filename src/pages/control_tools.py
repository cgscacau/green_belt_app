"""
Ferramentas da Fase Control do DMAIC
Implementação completa com 4 ferramentas funcionais
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import json

# Importar funções de formatação
from utils.formatters import (
    format_currency,
    format_date_br,
    format_date_input,
    parse_date_input,
    validate_currency_input
)


class ControlPhaseManager:
    """Gerenciador de dados da fase Control"""
    
    def __init__(self, firebase_manager):
        self.firebase = firebase_manager
        self.project_id = st.session_state.get('current_project_id')
    
    def get_control_data(self) -> Dict:
        """Obtém dados da fase Control"""
        if not self.project_id:
            return {}
        
        data = self.firebase.get_phase_data(self.project_id, 'control')
        if not data:
            return {
                'control_plan': {},
                'statistical_monitoring': {},
                'documentation': {},
                'audits': {}
            }
        return data
    
    def save_control_data(self, data: Dict) -> bool:
        """Salva dados da fase Control"""
        if not self.project_id:
            return False
        return self.firebase.save_phase_data(self.project_id, 'control', data)
    
    def get_control_points(self) -> Dict:
        """Obtém pontos de controle"""
        data = self.get_control_data()
        return data.get('control_plan', {}).get('control_points', {})
    
    def save_control_points(self, points: Dict) -> bool:
        """Salva pontos de controle"""
        data = self.get_control_data()
        if 'control_plan' not in data:
            data['control_plan'] = {}
        data['control_plan']['control_points'] = points
        return self.save_control_data(data)


class ControlPlanTool:
    """Ferramenta 1: Plano de Controle"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
    
    def show(self):
        """Exibe interface do Plano de Controle"""
        st.markdown("### 📊 Plano de Controle")
        st.markdown("Monitore os pontos críticos do processo para manter as melhorias alcançadas.")
        
        # Sistema de abas simplificado
        tab1, tab2, tab3 = st.tabs([
            "➕ Adicionar Ponto",
            "📊 Visualizar Pontos",
            "⚙️ Gerenciar Pontos"
        ])
        
        with tab1:
            self._add_control_point()
        
        with tab2:
            self._show_control_points()
        
        with tab3:
            self._manage_control_points()
    
    def _add_control_point(self):
        """Adiciona novo ponto de controle"""
        st.markdown("#### ➕ Adicionar Ponto de Controle")
        
        with st.form("add_control_point_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nome do Ponto de Controle*", placeholder="Ex: Temperatura do processo")
                metric = st.text_input("Métrica*", placeholder="Ex: Temperatura (°C)")
                target = st.number_input("Meta*", min_value=0.0, format="%.2f")
            
            with col2:
                usc = st.number_input("LSC (Limite Superior)*", min_value=0.0, format="%.2f")
                lic = st.number_input("LIC (Limite Inferior)*", min_value=0.0, format="%.2f")
                responsible = st.text_input("Responsável*", placeholder="Ex: João Silva")
            
            frequency = st.selectbox(
                "Frequência de Medição*",
                ["Horária", "Diária", "Semanal", "Quinzenal", "Mensal"]
            )
            
            measurement_method = st.text_area(
                "Método de Medição",
                placeholder="Descreva como a medição deve ser realizada..."
            )
            
            submitted = st.form_submit_button("➕ Adicionar Ponto", use_container_width=True)
            
            if submitted:
                if not all([name, metric, responsible]):
                    st.error("❌ Preencha todos os campos obrigatórios (*)!")
                    return
                
                points = self.manager.get_control_points()
                point_id = f"cp_{len(points) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                points[point_id] = {
                    'name': name,
                    'metric': metric,
                    'target': target,
                    'usc': usc,
                    'lic': lic,
                    'responsible': responsible,
                    'frequency': frequency,
                    'measurement_method': measurement_method,
                    'created_at': datetime.now().isoformat(),
                    'measurements': []
                }
                
                if self.manager.save_control_points(points):
                    st.success("✅ Ponto de controle adicionado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar ponto de controle!")
        
        # Seção para adicionar medições
        st.markdown("---")
        st.markdown("#### 📊 Adicionar Medições aos Pontos")
        
        points = self.manager.get_control_points()
        if not points:
            st.info("💡 Adicione um ponto de controle primeiro!")
            return
        
        point_options = {p['name']: pid for pid, p in points.items()}
        selected_point_name = st.selectbox("Selecione o Ponto", list(point_options.keys()))
        selected_point_id = point_options[selected_point_name]
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            # Data com formato brasileiro
            measurement_date = st.date_input(
                "Data da Medição",
                value=date.today(),
                format="DD/MM/YYYY"
            )
        with col2:
            measurement_value = st.number_input(
                "Valor Medido",
                format="%.2f",
                help="Use vírgula para decimais"
            )
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Adicionar Medição", use_container_width=True):
                if measurement_value is not None:
                    measurement = {
                        'date': measurement_date.isoformat(),
                        'value': measurement_value,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    points[selected_point_id]['measurements'].append(measurement)
                    
                    if self.manager.save_control_points(points):
                        st.success("✅ Medição adicionada com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar medição!")
    
    def _show_control_points(self):
        """Visualiza pontos de controle e gráficos"""
        st.markdown("#### 📊 Visualização dos Pontos de Controle")
        
        points = self.manager.get_control_points()
        if not points:
            st.info("💡 Nenhum ponto de controle cadastrado ainda.")
            return
        
        # Seletor de ponto
        point_options = {p['name']: pid for pid, p in points.items()}
        selected_point_name = st.selectbox(
            "Selecione um Ponto para Visualizar",
            list(point_options.keys()),
            key="view_point_selector"
        )
        selected_point_id = point_options[selected_point_name]
        point = points[selected_point_id]
        
        # Informações do ponto
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Métrica", point['metric'])
        with col2:
            st.metric("Meta", f"{point['target']:.2f}")
        with col3:
            st.metric("LSC", f"{point['usc']:.2f}")
        with col4:
            st.metric("LIC", f"{point['lic']:.2f}")
        
        st.markdown(f"**Responsável:** {point['responsible']}")
        st.markdown(f"**Frequência:** {point['frequency']}")
        
        # Tabela de medições
        measurements = point.get('measurements', [])
        if not measurements:
            st.info("💡 Nenhuma medição registrada ainda.")
            return
        
        st.markdown("#### 📋 Histórico de Medições")
        df_measurements = pd.DataFrame(measurements)
        df_measurements['date'] = pd.to_datetime(df_measurements['date']).dt.strftime('%d/%m/%Y')
        df_measurements['value'] = df_measurements['value'].apply(lambda x: f"{x:.2f}".replace('.', ','))
        
        st.dataframe(
            df_measurements[['date', 'value']].rename(columns={'date': 'Data', 'value': 'Valor'}),
            use_container_width=True,
            hide_index=True
        )
        
        # Gráfico de controle
        st.markdown("#### 📈 Gráfico de Controle")
        
        df_plot = pd.DataFrame(measurements)
        df_plot['date'] = pd.to_datetime(df_plot['date'])
        df_plot = df_plot.sort_values('date')
        
        fig = go.Figure()
        
        # Linha de medições
        fig.add_trace(go.Scatter(
            x=df_plot['date'],
            y=df_plot['value'],
            mode='lines+markers',
            name='Medições',
            line=dict(color='blue', width=2),
            marker=dict(size=8)
        ))
        
        # Linhas de controle
        fig.add_hline(y=point['target'], line_dash="dash", line_color="green", 
                      annotation_text="Meta", annotation_position="right")
        fig.add_hline(y=point['usc'], line_dash="dot", line_color="red",
                      annotation_text="LSC", annotation_position="right")
        fig.add_hline(y=point['lic'], line_dash="dot", line_color="red",
                      annotation_text="LIC", annotation_position="right")
        
        fig.update_layout(
            title=f"Gráfico de Controle - {point['name']}",
            xaxis_title="Data",
            yaxis_title=point['metric'],
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Análise rápida
        latest_value = df_plot['value'].iloc[-1]
        if latest_value > point['usc']:
            st.error(f"⚠️ Última medição ({latest_value:.2f}) está ACIMA do LSC!")
        elif latest_value < point['lic']:
            st.error(f"⚠️ Última medição ({latest_value:.2f}) está ABAIXO do LIC!")
        else:
            st.success(f"✅ Última medição ({latest_value:.2f}) está dentro dos limites de controle.")
    
    def _manage_control_points(self):
        """Gerencia pontos de controle (editar/excluir)"""
        st.markdown("#### ⚙️ Gerenciar Pontos de Controle")
        
        points = self.manager.get_control_points()
        if not points:
            st.info("💡 Nenhum ponto de controle cadastrado ainda.")
            return
        
        # Seletor de ponto
        point_options = {p['name']: pid for pid, p in points.items()}
        selected_point_name = st.selectbox(
            "Selecione um Ponto",
            list(point_options.keys()),
            key="manage_point_selector"
        )
        selected_point_id = point_options[selected_point_name]
        point = points[selected_point_id]
        
        # Editar medições
        st.markdown("##### ✏️ Editar Medições")
        measurements = point.get('measurements', [])
        
        if measurements:
            for idx, m in enumerate(measurements):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Data: {format_date_br(m['date'])}")
                with col2:
                    st.text(f"Valor: {m['value']:.2f}".replace('.', ','))
                with col3:
                    if st.button("✏️", key=f"edit_m_{idx}"):
                        st.session_state[f'editing_measurement_{idx}'] = True
                
                if st.session_state.get(f'editing_measurement_{idx}', False):
                    with st.form(f"edit_measurement_form_{idx}"):
                        new_date = st.date_input(
                            "Nova Data",
                            value=datetime.fromisoformat(m['date']).date(),
                            format="DD/MM/YYYY"
                        )
                        new_value = st.number_input("Novo Valor", value=m['value'], format="%.2f")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Salvar", use_container_width=True):
                                points[selected_point_id]['measurements'][idx] = {
                                    'date': new_date.isoformat(),
                                    'value': new_value,
                                    'timestamp': datetime.now().isoformat()
                                }
                                if self.manager.save_control_points(points):
                                    st.session_state[f'editing_measurement_{idx}'] = False
                                    st.success("✅ Medição atualizada!")
                                    st.rerun()
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state[f'editing_measurement_{idx}'] = False
                                st.rerun()
        else:
            st.info("💡 Nenhuma medição para editar.")
        
        # Excluir medições
        st.markdown("---")
        st.markdown("##### 🗑️ Excluir Medições")
        
        if measurements:
            for idx, m in enumerate(measurements):
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.text(f"{format_date_br(m['date'])} - Valor: {m['value']:.2f}".replace('.', ','))
                with col2:
                    if st.button(f"🗑️ Excluir", key=f"delete_m_{idx}"):
                        st.session_state[f'confirm_delete_{idx}'] = True
                with col3:
                    if st.session_state.get(f'confirm_delete_{idx}', False):
                        confirm_text = st.text_input(
                            "Digite EXCLUIR",
                            key=f"confirm_text_{idx}",
                            label_visibility="collapsed"
                        )
                        if st.button("✅ Confirmar", key=f"confirm_btn_{idx}"):
                            if confirm_text == "EXCLUIR":
                                points[selected_point_id]['measurements'].pop(idx)
                                if self.manager.save_control_points(points):
                                    st.session_state[f'confirm_delete_{idx}'] = False
                                    st.success("✅ Medição excluída!")
                                    st.rerun()
                            else:
                                st.error("❌ Texto incorreto!")
        else:
            st.info("💡 Nenhuma medição para excluir.")
        
        # Excluir ponto completo
        st.markdown("---")
        st.markdown("##### 🗑️ Excluir Ponto de Controle Completo")
        st.warning("⚠️ Esta ação excluirá o ponto e TODAS as suas medições!")
        
        if st.button("🗑️ Excluir Ponto Completo", key="delete_point_btn"):
            st.session_state['confirm_delete_point'] = True
        
        if st.session_state.get('confirm_delete_point', False):
            confirm_text = st.text_input("Digite EXCLUIR para confirmar", key="confirm_delete_point_text")
            if st.button("✅ Confirmar Exclusão do Ponto", key="confirm_delete_point_btn"):
                if confirm_text == "EXCLUIR":
                    del points[selected_point_id]
                    if self.manager.save_control_points(points):
                        st.session_state['confirm_delete_point'] = False
                        st.success("✅ Ponto de controle excluído!")
                        st.rerun()
                else:
                    st.error("❌ Texto incorreto!")


class StatisticalMonitoringTool:
    """Ferramenta 2: Monitoramento Estatístico (CEP)"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
    
    def show(self):
        """Exibe interface de Monitoramento Estatístico"""
        st.markdown("### 📈 Monitoramento Estatístico (CEP)")
        st.markdown("Análise estatística avançada dos pontos de controle.")
        
        tab1, tab2, tab3 = st.tabs([
            "📊 Análise de Capabilidade",
            "📉 Tendências e Padrões",
            "⚡ Alertas Automáticos"
        ])
        
        with tab1:
            self._show_capability_analysis()
        
        with tab2:
            self._show_trend_analysis()
        
        with tab3:
            self._show_automated_alerts()
    
    def _show_capability_analysis(self):
        """Análise de capabilidade do processo (Cp, Cpk)"""
        st.markdown("#### 📊 Análise de Capabilidade do Processo")
        
        points = self.manager.get_control_points()
        if not points:
            st.info("💡 Nenhum ponto de controle cadastrado ainda.")
            return
        
        # Seletor de ponto
        point_options = {p['name']: pid for pid, p in points.items()}
        selected_point_name = st.selectbox("Selecione um Ponto", list(point_options.keys()))
        selected_point_id = point_options[selected_point_name]
        point = points[selected_point_id]
        
        measurements = point.get('measurements', [])
        if len(measurements) < 30:
            st.warning(f"⚠️ Recomenda-se no mínimo 30 medições para análise confiável. Você tem: {len(measurements)}")
            if len(measurements) < 2:
                st.info("💡 Adicione mais medições para calcular a capabilidade.")
                return
        
        # Calcular estatísticas
        values = [m['value'] for m in measurements]
        mean = np.mean(values)
        std = np.std(values, ddof=1)
        
        usl = point['usc']  # Upper Specification Limit
        lsl = point['lic']  # Lower Specification Limit
        target = point['target']
        
        # Cp (Capabilidade do Processo)
        cp = (usl - lsl) / (6 * std) if std > 0 else 0
        
        # Cpk (Capabilidade do Processo considerando centralização)
        cpk_upper = (usl - mean) / (3 * std) if std > 0 else 0
        cpk_lower = (mean - lsl) / (3 * std) if std > 0 else 0
        cpk = min(cpk_upper, cpk_lower)
        
        # Exibir métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Média", f"{mean:.2f}".replace('.', ','))
        with col2:
            st.metric("Desvio Padrão", f"{std:.2f}".replace('.', ','))
        with col3:
            st.metric("Cp", f"{cp:.2f}".replace('.', ','))
        with col4:
            st.metric("Cpk", f"{cpk:.2f}".replace('.', ','))
        
        # Interpretação
        st.markdown("#### 🎯 Interpretação")
        
        if cpk >= 1.33:
            st.success("✅ **Processo Capaz**: Cpk ≥ 1.33 - Processo altamente capaz!")
        elif cpk >= 1.0:
            st.warning("⚠️ **Processo Marginalmente Capaz**: 1.0 ≤ Cpk < 1.33 - Melhorias recomendadas.")
        else:
            st.error("❌ **Processo Não Capaz**: Cpk < 1.0 - Ação imediata necessária!")
        
        # Gráfico de distribuição
        st.markdown("#### 📊 Distribuição dos Dados")
        
        fig = go.Figure()
        
        # Histograma
        fig.add_trace(go.Histogram(
            x=values,
            name='Frequência',
            nbinsx=20,
            marker_color='lightblue',
            opacity=0.7
        ))
        
        # Linhas de especificação
        fig.add_vline(x=lsl, line_dash="dash", line_color="red", annotation_text="LIC")
        fig.add_vline(x=usl, line_dash="dash", line_color="red", annotation_text="LSC")
        fig.add_vline(x=target, line_dash="solid", line_color="green", annotation_text="Meta")
        fig.add_vline(x=mean, line_dash="dot", line_color="blue", annotation_text="Média")
        
        fig.update_layout(
            title="Distribuição das Medições",
            xaxis_title=point['metric'],
            yaxis_title="Frequência",
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de probabilidade normal
        st.markdown("#### 📈 Gráfico de Probabilidade Normal")
        
        from scipy import stats
        theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(values)))
        sample_quantiles = np.sort(values)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=theoretical_quantiles,
            y=sample_quantiles,
            mode='markers',
            name='Dados',
            marker=dict(color='blue', size=6)
        ))
        
        # Linha de referência
        fig2.add_trace(go.Scatter(
            x=theoretical_quantiles,
            y=theoretical_quantiles * std + mean,
            mode='lines',
            name='Normal Teórica',
            line=dict(color='red', dash='dash')
        ))
        
        fig2.update_layout(
            title="Teste de Normalidade (Q-Q Plot)",
            xaxis_title="Quantis Teóricos",
            yaxis_title="Quantis da Amostra",
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    def _show_trend_analysis(self):
        """Análise de tendências e padrões"""
        st.markdown("#### 📉 Análise de Tendências e Padrões")
        
        points = self.manager.get_control_points()
        if not points:
            st.info("💡 Nenhum ponto de controle cadastrado ainda.")
            return
        
        # Seletor de ponto
        point_options = {p['name']: pid for pid, p in points.items()}
        selected_point_name = st.selectbox("Selecione um Ponto", list(point_options.keys()), key="trend_selector")
        selected_point_id = point_options[selected_point_name]
        point = points[selected_point_id]
        
        measurements = point.get('measurements', [])
        if len(measurements) < 7:
            st.warning("⚠️ São necessárias pelo menos 7 medições para análise de tendências confiável.")
            return
        
        # Preparar dados
        df = pd.DataFrame(measurements)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        values = df['value'].values
        mean = np.mean(values)
        std = np.std(values, ddof=1)
        
        # Detectar padrões
        patterns = []
        
        # Regra 1: Ponto fora dos limites de controle
        usl = point['usc']
        lsl = point['lic']
        if any(v > usl or v < lsl for v in values):
            patterns.append("🔴 **Regra 1 violada**: Pontos fora dos limites de controle")
        
        # Regra 2: 9 pontos consecutivos no mesmo lado da linha central
        if len(values) >= 9:
            for i in range(len(values) - 8):
                segment = values[i:i+9]
                if all(v > mean for v in segment) or all(v < mean for v in segment):
                    patterns.append(f"🟡 **Regra 2 violada**: 9 pontos consecutivos no mesmo lado (posição {i+1}-{i+9})")
                    break
        
        # Regra 3: 6 pontos consecutivos aumentando ou diminuindo
        if len(values) >= 6:
            for i in range(len(values) - 5):
                segment = values[i:i+6]
                diffs = np.diff(segment)
                if all(d > 0 for d in diffs):
                    patterns.append(f"🟠 **Regra 3 violada**: Tendência crescente de 6 pontos (posição {i+1}-{i+6})")
                    break
                elif all(d < 0 for d in diffs):
                    patterns.append(f"🟠 **Regra 3 violada**: Tendência decrescente de 6 pontos (posição {i+1}-{i+6})")
                    break
        
        # Regra 4: 14 pontos alternando para cima e para baixo
        if len(values) >= 14:
            diffs = np.diff(values)
            alternating = all(diffs[i] * diffs[i+1] < 0 for i in range(len(diffs)-1))
            if alternating:
                patterns.append("🟣 **Regra 4 violada**: 14 pontos alternando (oscilação sistemática)")
        
        # Exibir alertas
        if patterns:
            st.error("⚠️ **Padrões Não Aleatórios Detectados:**")
            for pattern in patterns:
                st.markdown(f"- {pattern}")
        else:
            st.success("✅ **Nenhum padrão não aleatório detectado** - Processo sob controle estatístico!")
        
        # Gráfico de tendência
        st.markdown("#### 📈 Gráfico de Tendência")
        
        fig = go.Figure()
        
        # Linha de dados
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['value'],
            mode='lines+markers',
            name='Medições',
            line=dict(color='blue', width=2),
            marker=dict(size=8)
        ))
        
        # Média móvel (últimos 7 pontos)
        if len(df) >= 7:
            df['moving_avg'] = df['value'].rolling(window=7, center=True).mean()
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['moving_avg'],
                mode='lines',
                name='Média Móvel (7 pontos)',
                line=dict(color='orange', width=2, dash='dash')
            ))
        
        # Linhas de controle
        fig.add_hline(y=mean, line_color="green", line_dash="dash", annotation_text="Média")
        fig.add_hline(y=usl, line_color="red", line_dash="dot", annotation_text="LSC")
        fig.add_hline(y=lsl, line_color="red", line_dash="dot", annotation_text="LIC")
        
        # Zonas de sigma
        fig.add_hrect(y0=mean-std, y1=mean+std, fillcolor="green", opacity=0.1, annotation_text="±1σ")
        fig.add_hrect(y0=mean-2*std, y1=mean+std-std, fillcolor="yellow", opacity=0.1)
        fig.add_hrect(y0=mean+std, y1=mean+2*std, fillcolor="yellow", opacity=0.1, annotation_text="±2σ")
        
        fig.update_layout(
            title=f"Análise de Tendência - {point['name']}",
            xaxis_title="Data",
            yaxis_title=point['metric'],
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas de tendência
        st.markdown("#### 📊 Estatísticas de Tendência")
        
        col1, col2, col3 = st.columns(3)
        
        # Calcular tendência linear
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        
        with col1:
            trend_direction = "⬆️ Crescente" if slope > 0 else "⬇️ Decrescente"
            st.metric("Direção da Tendência", trend_direction)
        
        with col2:
            st.metric("Inclinação", f"{slope:.4f}".replace('.', ','))
        
        with col3:
            # Calcular variação percentual
            if values[0] != 0:
                variation = ((values[-1] - values[0]) / abs(values[0])) * 100
                st.metric("Variação Total", f"{variation:+.1f}%".replace('.', ','))
    
    def _show_automated_alerts(self):
        """Sistema de alertas automáticos"""
        st.markdown("#### ⚡ Sistema de Alertas Automáticos")
        
        points = self.manager.get_control_points()
        if not points:
            st.info("💡 Nenhum ponto de controle cadastrado ainda.")
            return
        
        # Análise de todos os pontos
        st.markdown("##### 📊 Status de Todos os Pontos de Controle")
        
        alert_summary = {
            'critical': [],
            'warning': [],
            'ok': []
        }
        
        for pid, point in points.items():
            measurements = point.get('measurements', [])
            if not measurements:
                continue
            
            latest = measurements[-1]
            latest_value = latest['value']
            latest_date = format_date_br(latest['date'])
            
            status = {
                'name': point['name'],
                'value': latest_value,
                'date': latest_date,
                'metric': point['metric']
            }
            
            # Classificar por severidade
            if latest_value > point['usc'] or latest_value < point['lic']:
                status['alert'] = f"Fora dos limites ({latest_value:.2f})".replace('.', ',')
                alert_summary['critical'].append(status)
            elif latest_value > point['target'] * 1.05 or latest_value < point['target'] * 0.95:
                status['alert'] = f"Desviado da meta ({latest_value:.2f})".replace('.', ',')
                alert_summary['warning'].append(status)
            else:
                status['alert'] = f"Normal ({latest_value:.2f})".replace('.', ',')
                alert_summary['ok'].append(status)
        
        # Exibir alertas críticos
        if alert_summary['critical']:
            st.error(f"🔴 **{len(alert_summary['critical'])} Alerta(s) Crítico(s)**")
            for item in alert_summary['critical']:
                with st.expander(f"⚠️ {item['name']} - {item['alert']}"):
                    st.markdown(f"**Data:** {item['date']}")
                    st.markdown(f"**Métrica:** {item['metric']}")
                    st.markdown(f"**Valor:** {item['alert']}")
                    st.markdown("**Ação requerida:** Investigar imediatamente e tomar ação corretiva!")
        
        # Exibir avisos
        if alert_summary['warning']:
            st.warning(f"🟡 **{len(alert_summary['warning'])} Aviso(s)**")
            for item in alert_summary['warning']:
                with st.expander(f"⚡ {item['name']} - {item['alert']}"):
                    st.markdown(f"**Data:** {item['date']}")
                    st.markdown(f"**Métrica:** {item['metric']}")
                    st.markdown(f"**Valor:** {item['alert']}")
                    st.markdown("**Recomendação:** Monitorar próximas medições.")
        
        # Exibir status OK
        if alert_summary['ok']:
            st.success(f"✅ **{len(alert_summary['ok'])} Ponto(s) Sob Controle**")
            with st.expander("Ver detalhes"):
                for item in alert_summary['ok']:
                    st.markdown(f"- **{item['name']}**: {item['alert']} em {item['date']}")
        
        # Configurar notificações
        st.markdown("---")
        st.markdown("##### 🔔 Configurar Notificações")
        
        data = self.manager.get_control_data()
        notifications = data.get('notifications', {})
        
        with st.form("notification_settings"):
            st.markdown("Configure quando deseja receber alertas:")
            
            enable_email = st.checkbox(
                "Enviar alertas por e-mail",
                value=notifications.get('enable_email', False)
            )
            
            if enable_email:
                email = st.text_input(
                    "E-mail para notificações",
                    value=notifications.get('email', ''),
                    placeholder="seu.email@empresa.com"
                )
            
            enable_critical = st.checkbox(
                "Alertas para valores fora dos limites de controle",
                value=notifications.get('enable_critical', True)
            )
            
            enable_warning = st.checkbox(
                "Alertas para valores desviados da meta",
                value=notifications.get('enable_warning', False)
            )
            
            enable_trends = st.checkbox(
                "Alertas para tendências anormais detectadas",
                value=notifications.get('enable_trends', False)
            )
            
            submitted = st.form_submit_button("💾 Salvar Configurações")
            
            if submitted:
                notifications_config = {
                    'enable_email': enable_email,
                    'enable_critical': enable_critical,
                    'enable_warning': enable_warning,
                    'enable_trends': enable_trends
                }
                
                if enable_email:
                    notifications_config['email'] = email
                
                data['notifications'] = notifications_config
                if self.manager.save_control_data(data):
                    st.success("✅ Configurações de notificação salvas!")
                    st.rerun()


class StandardDocumentationTool:
    """Ferramenta 3: Documentação Padrão"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
    
    def show(self):
        """Exibe interface de Documentação Padrão"""
        st.markdown("### 📋 Documentação Padrão")
        st.markdown("Crie e gerencie SOPs, instruções de trabalho e registros padronizados.")
        
        tab1, tab2, tab3 = st.tabs([
            "📄 SOPs (Procedimentos)",
            "📝 Instruções de Trabalho",
            "📊 Registros e Formulários"
        ])
        
        with tab1:
            self._manage_sops()
        
        with tab2:
            self._manage_work_instructions()
        
        with tab3:
            self._manage_records()
    
    def _manage_sops(self):
        """Gerenciar Standard Operating Procedures"""
        st.markdown("#### 📄 Procedimentos Operacionais Padrão (SOPs)")
        
        data = self.manager.get_control_data()
        sops = data.get('documentation', {}).get('sops', {})
        
        # Adicionar novo SOP
        with st.expander("➕ Criar Novo SOP", expanded=not bool(sops)):
            with st.form("new_sop_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    sop_code = st.text_input("Código do SOP*", placeholder="Ex: SOP-001")
                    sop_title = st.text_input("Título*", placeholder="Ex: Procedimento de Calibração")
                    version = st.text_input("Versão", value="1.0")
                
                with col2:
                    department = st.text_input("Departamento", placeholder="Ex: Produção")
                    author = st.text_input("Autor*", placeholder="Ex: Maria Silva")
                    approval_date = st.date_input("Data de Aprovação", value=date.today(), format="DD/MM/YYYY")
                
                st.markdown("**Objetivo do SOP:**")
                objective = st.text_area("Objetivo", placeholder="Descreva o objetivo deste procedimento...")
                
                st.markdown("**Escopo:**")
                scope = st.text_area("Escopo", placeholder="Defina o escopo de aplicação...")
                
                st.markdown("**Procedimento (Passo a Passo):**")
                procedure = st.text_area(
                    "Procedimento",
                    placeholder="1. Primeiro passo\n2. Segundo passo\n3. Terceiro passo...",
                    height=200
                )
                
                st.markdown("**Responsabilidades:**")
                responsibilities = st.text_area("Responsabilidades", placeholder="Liste as responsabilidades...")
                
                st.markdown("**Referências:**")
                references = st.text_area("Referências", placeholder="Documentos relacionados, normas, etc.")
                
                submitted = st.form_submit_button("➕ Criar SOP", use_container_width=True)
                
                if submitted:
                    if not all([sop_code, sop_title, author]):
                        st.error("❌ Preencha todos os campos obrigatórios (*)!")
                    else:
                        sop_id = f"sop_{len(sops) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        
                        sops[sop_id] = {
                            'code': sop_code,
                            'title': sop_title,
                            'version': version,
                            'department': department,
                            'author': author,
                            'approval_date': approval_date.isoformat(),
                            'objective': objective,
                            'scope': scope,
                            'procedure': procedure,
                            'responsibilities': responsibilities,
                            'references': references,
                            'created_at': datetime.now().isoformat(),
                            'revisions': []
                        }
                        
                        if 'documentation' not in data:
                            data['documentation'] = {}
                        data['documentation']['sops'] = sops
                        
                        if self.manager.save_control_data(data):
                            st.success("✅ SOP criado com sucesso!")
                            st.rerun()
        
        # Listar SOPs existentes
        if sops:
            st.markdown("---")
            st.markdown("#### 📚 SOPs Cadastrados")
            
            for sop_id, sop in sops.items():
                with st.expander(f"📄 {sop['code']} - {sop['title']} (v{sop['version']})"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"**Autor:** {sop['author']}")
                    with col2:
                        st.markdown(f"**Departamento:** {sop.get('department', 'N/A')}")
                    with col3:
                        st.markdown(f"**Aprovado em:** {format_date_br(sop['approval_date'])}")
                    
                    st.markdown("**Objetivo:**")
                    st.info(sop['objective'])
                    
                    st.markdown("**Escopo:**")
                    st.info(sop['scope'])
                    
                    st.markdown("**Procedimento:**")
                    st.text_area("", value=sop['procedure'], height=200, disabled=True, key=f"proc_{sop_id}")
                    
                    if sop.get('responsibilities'):
                        st.markdown("**Responsabilidades:**")
                        st.info(sop['responsibilities'])
                    
                    if sop.get('references'):
                        st.markdown("**Referências:**")
                        st.info(sop['references'])
                    
                    # Histórico de revisões
                    revisions = sop.get('revisions', [])
                    if revisions:
                        st.markdown("**Histórico de Revisões:**")
                        df_rev = pd.DataFrame(revisions)
                        df_rev['date'] = pd.to_datetime(df_rev['date']).dt.strftime('%d/%m/%Y')
                        st.dataframe(df_rev[['version', 'date', 'changes']], hide_index=True)
                    
                    # Ações
                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.button("✏️ Revisar", key=f"edit_{sop_id}"):
                            st.info("💡 Funcionalidade de revisão em desenvolvimento")
                    with col_delete:
                        if st.button("🗑️ Excluir", key=f"del_{sop_id}"):
                            st.session_state[f'confirm_del_sop_{sop_id}'] = True
                    
                    if st.session_state.get(f'confirm_del_sop_{sop_id}', False):
                        st.warning("⚠️ Tem certeza que deseja excluir este SOP?")
                        confirm = st.text_input("Digite EXCLUIR para confirmar", key=f"confirm_sop_{sop_id}")
                        if st.button("Confirmar Exclusão", key=f"confirm_btn_sop_{sop_id}"):
                            if confirm == "EXCLUIR":
                                del sops[sop_id]
                                data['documentation']['sops'] = sops
                                if self.manager.save_control_data(data):
                                    st.success("✅ SOP excluído!")
                                    st.rerun()
        else:
            st.info("💡 Nenhum SOP cadastrado ainda. Crie o primeiro!")
    
    def _manage_work_instructions(self):
        """Gerenciar instruções de trabalho"""
        st.markdown("#### 📝 Instruções de Trabalho")
        
        data = self.manager.get_control_data()
        instructions = data.get('documentation', {}).get('work_instructions', {})
        
        # Adicionar nova instrução
        with st.expander("➕ Criar Nova Instrução de Trabalho", expanded=not bool(instructions)):
            with st.form("new_instruction_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    inst_code = st.text_input("Código*", placeholder="Ex: IT-001")
                    inst_title = st.text_input("Título*", placeholder="Ex: Setup da Máquina X")
                    process = st.text_input("Processo", placeholder="Ex: Extrusão")
                
                with col2:
                    equipment = st.text_input("Equipamento", placeholder="Ex: Extrusora #3")
                    author = st.text_input("Autor*")
                    revision_date = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
                
                st.markdown("**Passos da Instrução:**")
                steps = st.text_area(
                    "Passos",
                    placeholder="Passo 1: ...\nPasso 2: ...\nPasso 3: ...",
                    height=200
                )
                
                st.markdown("**Pontos Críticos de Qualidade:**")
                critical_points = st.text_area("Pontos Críticos", placeholder="Liste os pontos de atenção...")
                
                st.markdown("**Ferramentas/Materiais Necessários:**")
                tools = st.text_area("Ferramentas", placeholder="Liste as ferramentas necessárias...")
                
                submitted = st.form_submit_button("➕ Criar Instrução", use_container_width=True)
                
                if submitted:
                    if not all([inst_code, inst_title, author]):
                        st.error("❌ Preencha todos os campos obrigatórios (*)!")
                    else:
                        inst_id = f"inst_{len(instructions) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        
                        instructions[inst_id] = {
                            'code': inst_code,
                            'title': inst_title,
                            'process': process,
                            'equipment': equipment,
                            'author': author,
                            'revision_date': revision_date.isoformat(),
                            'steps': steps,
                            'critical_points': critical_points,
                            'tools': tools,
                            'created_at': datetime.now().isoformat()
                        }
                        
                        if 'documentation' not in data:
                            data['documentation'] = {}
                        data['documentation']['work_instructions'] = instructions
                        
                        if self.manager.save_control_data(data):
                            st.success("✅ Instrução de trabalho criada!")
                            st.rerun()
        
        # Listar instruções
        if instructions:
            st.markdown("---")
            st.markdown("#### 📚 Instruções Cadastradas")
            
            for inst_id, inst in instructions.items():
                with st.expander(f"📝 {inst['code']} - {inst['title']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Processo:** {inst.get('process', 'N/A')}")
                        st.markdown(f"**Equipamento:** {inst.get('equipment', 'N/A')}")
                    with col2:
                        st.markdown(f"**Autor:** {inst['author']}")
                        st.markdown(f"**Data:** {format_date_br(inst['revision_date'])}")
                    
                    st.markdown("**Passos:**")
                    st.text_area("", value=inst['steps'], height=150, disabled=True, key=f"steps_{inst_id}")
                    
                    if inst.get('critical_points'):
                        st.warning(f"⚠️ **Pontos Críticos:**\n\n{inst['critical_points']}")
                    
                    if inst.get('tools'):
                        st.info(f"🔧 **Ferramentas:**\n\n{inst['tools']}")
                    
                    if st.button("🗑️ Excluir", key=f"del_inst_{inst_id}"):
                        del instructions[inst_id]
                        data['documentation']['work_instructions'] = instructions
                        if self.manager.save_control_data(data):
                            st.success("✅ Instrução excluída!")
                            st.rerun()
        else:
            st.info("💡 Nenhuma instrução de trabalho cadastrada ainda.")
    
    def _manage_records(self):
        """Gerenciar registros e formulários"""
        st.markdown("#### 📊 Registros e Formulários Padrão")
        
        data = self.manager.get_control_data()
        records = data.get('documentation', {}).get('records', {})
        
        # Template de registros
        st.markdown("##### 📋 Templates Disponíveis")
        
        templates = {
            'checklist_diario': {
                'name': 'Checklist Diário de Produção',
                'fields': ['Data', 'Turno', 'Operador', 'Equipamento', 'Verificações', 'Observações']
            },
            'registro_calibracao': {
                'name': 'Registro de Calibração',
                'fields': ['Data', 'Instrumento', 'Padrão Utilizado', 'Resultado', 'Responsável']
            },
            'relatorio_nao_conformidade': {
                'name': 'Relatório de Não-Conformidade',
                'fields': ['Data', 'Descrição', 'Causa Raiz', 'Ação Corretiva', 'Responsável', 'Prazo']
            }
        }
        
        selected_template = st.selectbox(
            "Selecione um template",
            options=list(templates.keys()),
            format_func=lambda x: templates[x]['name']
        )
        
        template = templates[selected_template]
        
        with st.expander(f"📝 Preencher: {template['name']}", expanded=True):
            with st.form(f"record_{selected_template}"):
                record_data = {}
                
                for field in template['fields']:
                    if field == 'Data':
                        record_data[field] = st.date_input(field, value=date.today(), format="DD/MM/YYYY")
                    elif field in ['Observações', 'Descrição', 'Causa Raiz', 'Ação Corretiva']:
                        record_data[field] = st.text_area(field, height=100)
                    else:
                        record_data[field] = st.text_input(field)
                
                submitted = st.form_submit_button("💾 Salvar Registro", use_container_width=True)
                
                if submitted:
                    record_id = f"rec_{len(records) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    # Converter data para string
                    for key, value in record_data.items():
                        if isinstance(value, date):
                            record_data[key] = value.isoformat()
                    
                    records[record_id] = {
                        'template': selected_template,
                        'template_name': template['name'],
                        'data': record_data,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    if 'documentation' not in data:
                        data['documentation'] = {}
                    data['documentation']['records'] = records
                    
                    if self.manager.save_control_data(data):
                        st.success("✅ Registro salvo com sucesso!")
                        st.rerun()
        
        # Listar registros salvos
        if records:
            st.markdown("---")
            st.markdown("##### 📚 Registros Salvos")
            
            # Filtrar por template
            filter_template = st.selectbox(
                "Filtrar por tipo",
                options=['Todos'] + list(templates.keys()),
                format_func=lambda x: 'Todos os Tipos' if x == 'Todos' else templates[x]['name']
            )
            
            filtered_records = records if filter_template == 'Todos' else {
                k: v for k, v in records.items() if v['template'] == filter_template
            }
            
            for rec_id, record in filtered_records.items():
                with st.expander(f"📄 {record['template_name']} - {format_date_br(record['created_at'])}"):
                    for field, value in record['data'].items():
                        if isinstance(value, str) and len(value) > 50:
                            st.markdown(f"**{field}:**")
                            st.text_area("", value=value, height=100, disabled=True, key=f"field_{rec_id}_{field}")
                        else:
                            display_value = format_date_br(value) if field == 'Data' else value
                            st.markdown(f"**{field}:** {display_value}")
                    
                    if st.button("🗑️ Excluir", key=f"del_rec_{rec_id}"):
                        del records[rec_id]
                        data['documentation']['records'] = records
                        if self.manager.save_control_data(data):
                            st.success("✅ Registro excluído!")
                            st.rerun()
        else:
            st.info("💡 Nenhum registro salvo ainda.")


class SustainabilityAuditTool:
    """Ferramenta 4: Auditoria de Sustentabilidade"""
    
    def __init__(self, manager: ControlPhaseManager):
        self.manager = manager
    
    def show(self):
        """Exibe interface de Auditoria de Sustentabilidade"""
        st.markdown("### 🔄 Auditoria de Sustentabilidade")
        st.markdown("Garanta que as melhorias sejam mantidas ao longo do tempo.")
        
        tab1, tab2, tab3 = st.tabs([
            "📋 Checklist de Auditoria",
            "📊 Planos de Ação",
            "📈 Histórico de Auditorias"
        ])
        
        with tab1:
            self._audit_checklist()
        
        with tab2:
            self._action_plans()
        
        with tab3:
            self._audit_history()
    
    def _audit_checklist(self):
        """Checklist de auditoria"""
        st.markdown("#### 📋 Checklist de Auditoria de Sustentabilidade")
        
        data = self.manager.get_control_data()
        audits = data.get('audits', {})
        
        # Checklist padrão
        checklist_items = [
            {
                'category': 'Plano de Controle',
                'items': [
                    'Pontos de controle estão sendo monitorados conforme frequência definida',
                    'Responsáveis estão cumprindo suas atribuições',
                    'Limites de controle permanecem adequados',
                    'Medições estão dentro dos limites estabelecidos'
                ]
            },
            {
                'category': 'Documentação',
                'items': [
                    'SOPs estão atualizados e disponíveis',
                    'Instruções de trabalho são seguidas',
                    'Registros estão sendo preenchidos corretamente',
                    'Treinamentos estão em dia'
                ]
            },
            {
                'category': 'Processos',
                'items': [
                    'Processo permanece sob controle estatístico',
                    'Capabilidade do processo (Cpk) está adequada',
                    'Não há desvios significativos do padrão',
                    'Melhorias implementadas estão funcionando'
                ]
            },
            {
                'category': 'Equipe',
                'items': [
                    'Equipe está treinada nos novos procedimentos',
                    'Há engajamento da equipe com as melhorias',
                    'Sugestões de melhoria são coletadas',
                    'Comunicação sobre o plano de controle é clara'
                ]
            },
            {
                'category': 'Infraestrutura',
                'items': [
                    'Equipamentos estão calibrados e funcionando',
                    'Ferramentas necessárias estão disponíveis',
                    'Ambiente de trabalho está adequado',
                    'Recursos necessários estão alocados'
                ]
            }
        ]
        
        # Nova auditoria
        with st.expander("➕ Realizar Nova Auditoria", expanded=True):
            audit_date = st.date_input("Data da Auditoria", value=date.today(), format="DD/MM/YYYY")
            auditor = st.text_input("Auditor", placeholder="Nome do auditor")
            
            st.markdown("---")
            
            responses = {}
            total_items = 0
            compliant_items = 0
            
            for category_data in checklist_items:
                st.markdown(f"##### {category_data['category']}")
                
                for idx, item in enumerate(category_data['items']):
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"**{idx + 1}.** {item}")
                    
                    with col2:
                        key = f"{category_data['category']}_{idx}"
                        response = st.selectbox(
                            "Status",
                            options=['✅ Conforme', '⚠️ Parcial', '❌ Não Conforme', '➖ N/A'],
                            key=key,
                            label_visibility="collapsed"
                        )
                        responses[key] = {
                            'category': category_data['category'],
                            'item': item,
                            'response': response
                        }
                        
                        total_items += 1
                        if response == '✅ Conforme':
                            compliant_items += 1
                
                st.markdown("---")
            
            observations = st.text_area(
                "Observações Gerais",
                placeholder="Registre observações importantes, pontos de atenção, etc.",
                height=150
            )
            
            if st.button("💾 Salvar Auditoria", use_container_width=True):
                if not auditor:
                    st.error("❌ Preencha o nome do auditor!")
                else:
                    audit_id = f"audit_{len(audits) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    compliance_rate = (compliant_items / total_items * 100) if total_items > 0 else 0
                    
                    audits[audit_id] = {
                        'date': audit_date.isoformat(),
                        'auditor': auditor,
                        'responses': responses,
                        'observations': observations,
                        'compliance_rate': compliance_rate,
                        'total_items': total_items,
                        'compliant_items': compliant_items,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    data['audits'] = audits
                    
                    if self.manager.save_control_data(data):
                        st.success(f"✅ Auditoria salva! Taxa de conformidade: {compliance_rate:.1f}%")
                        st.rerun()
    
    def _action_plans(self):
        """Planos de ação para não-conformidades"""
        st.markdown("#### 📊 Planos de Ação Corretiva")
        
        data = self.manager.get_control_data()
        action_plans = data.get('action_plans', {})
        
        # Novo plano de ação
        with st.expander("➕ Criar Plano de Ação", expanded=not bool(action_plans)):
            with st.form("new_action_plan"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nc_description = st.text_area(
                        "Descrição da Não-Conformidade*",
                        placeholder="Descreva o problema identificado..."
                    )
                    root_cause = st.text_area(
                        "Causa Raiz*",
                        placeholder="Qual a causa raiz do problema?"
                    )
                
                with col2:
                    action = st.text_area(
                        "Ação Corretiva*",
                        placeholder="Que ação será tomada para corrigir?"
                    )
                    responsible = st.text_input("Responsável*", placeholder="Nome do responsável")
                
                col3, col4 = st.columns(2)
                with col3:
                    due_date = st.date_input("Prazo*", format="DD/MM/YYYY")
                with col4:
                    priority = st.selectbox("Prioridade", ["🔴 Alta", "🟡 Média", "🟢 Baixa"])
                
                submitted = st.form_submit_button("➕ Criar Plano", use_container_width=True)
                
                if submitted:
                    if not all([nc_description, root_cause, action, responsible]):
                        st.error("❌ Preencha todos os campos obrigatórios (*)!")
                    else:
                        plan_id = f"plan_{len(action_plans) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        
                        action_plans[plan_id] = {
                            'nc_description': nc_description,
                            'root_cause': root_cause,
                            'action': action,
                            'responsible': responsible,
                            'due_date': due_date.isoformat(),
                            'priority': priority,
                            'status': 'Aberto',
                            'created_at': datetime.now().isoformat(),
                            'updates': []
                        }
                        
                        data['action_plans'] = action_plans
                        
                        if self.manager.save_control_data(data):
                            st.success("✅ Plano de ação criado!")
                            st.rerun()
        
        # Listar planos de ação
        if action_plans:
            st.markdown("---")
            st.markdown("#### 📋 Planos de Ação Cadastrados")
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                filter_status = st.selectbox("Filtrar por Status", ["Todos", "Aberto", "Em Andamento", "Concluído"])
            with col2:
                filter_priority = st.selectbox("Filtrar por Prioridade", ["Todas", "🔴 Alta", "🟡 Média", "🟢 Baixa"])
            
            for plan_id, plan in action_plans.items():
                # Aplicar filtros
                if filter_status != "Todos" and plan['status'] != filter_status:
                    continue
                if filter_priority != "Todas" and plan['priority'] != filter_priority:
                    continue
                
                # Verificar se está atrasado
                due_date = datetime.fromisoformat(plan['due_date']).date()
                is_overdue = due_date < date.today() and plan['status'] != 'Concluído'
                
                status_icon = "✅" if plan['status'] == 'Concluído' else ("⏳" if is_overdue else "🔄")
                
                with st.expander(f"{status_icon} {plan['priority']} - {plan['nc_description'][:50]}..."):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Status:** {plan['status']}")
                        st.markdown(f"**Responsável:** {plan['responsible']}")
                    with col2:
                        st.markdown(f"**Prazo:** {format_date_br(plan['due_date'])}")
                        if is_overdue:
                            days_overdue = (date.today() - due_date).days
                            st.error(f"⚠️ Atrasado há {days_overdue} dia(s)!")
                    
                    st.markdown("**Não-Conformidade:**")
                    st.info(plan['nc_description'])
                    
                    st.markdown("**Causa Raiz:**")
                    st.warning(plan['root_cause'])
                    
                    st.markdown("**Ação Corretiva:**")
                    st.success(plan['action'])
                    
                    # Atualizações
                    updates = plan.get('updates', [])
                    if updates:
                        st.markdown("**Histórico de Atualizações:**")
                        for update in updates:
                            st.markdown(f"- {format_date_br(update['date'])}: {update['comment']}")
                    
                    # Adicionar atualização
                    st.markdown("---")
                    with st.form(f"update_{plan_id}"):
                        col_status, col_comment = st.columns([1, 2])
                        with col_status:
                            new_status = st.selectbox("Atualizar Status", ["Aberto", "Em Andamento", "Concluído"])
                        with col_comment:
                            update_comment = st.text_input("Comentário")
                        
                        if st.form_submit_button("💬 Adicionar Atualização"):
                            if update_comment:
                                plan['status'] = new_status
                                plan['updates'].append({
                                    'date': date.today().isoformat(),
                                    'status': new_status,
                                    'comment': update_comment
                                })
                                
                                if self.manager.save_control_data(data):
                                    st.success("✅ Atualização adicionada!")
                                    st.rerun()
                    
                    # Excluir plano
                    if st.button("🗑️ Excluir Plano", key=f"del_plan_{plan_id}"):
                        del action_plans[plan_id]
                        data['action_plans'] = action_plans
                        if self.manager.save_control_data(data):
                            st.success("✅ Plano excluído!")
                            st.rerun()
        else:
            st.info("💡 Nenhum plano de ação cadastrado ainda.")
    
    def _audit_history(self):
        """Histórico de auditorias"""
        st.markdown("#### 📈 Histórico de Auditorias")
        
        data = self.manager.get_control_data()
        audits = data.get('audits', {})
        
        if not audits:
            st.info("💡 Nenhuma auditoria realizada ainda.")
            return
        
        # Gráfico de evolução da conformidade
        audit_list = []
        for audit_id, audit in audits.items():
            audit_list.append({
                'date': datetime.fromisoformat(audit['date']),
                'compliance_rate': audit['compliance_rate'],
                'auditor': audit['auditor']
            })
        
        df_audits = pd.DataFrame(audit_list).sort_values('date')
        
        st.markdown("##### 📊 Evolução da Taxa de Conformidade")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_audits['date'],
            y=df_audits['compliance_rate'],
            mode='lines+markers',
            name='Taxa de Conformidade',
            line=dict(color='blue', width=3),
            marker=dict(size=10)
        ))
        
        fig.add_hline(y=100, line_dash="dash", line_color="green", annotation_text="100% Conforme")
        fig.add_hline(y=80, line_dash="dot", line_color="orange", annotation_text="Meta: 80%")
        
        fig.update_layout(
            xaxis_title="Data da Auditoria",
            yaxis_title="Taxa de Conformidade (%)",
            yaxis_range=[0, 105],
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Última Auditoria", f"{df_audits['compliance_rate'].iloc[-1]:.1f}%")
        with col2:
            st.metric("Média Geral", f"{df_audits['compliance_rate'].mean():.1f}%")
        with col3:
            st.metric("Total de Auditorias", len(audits))
        
        # Detalhes das auditorias
        st.markdown("---")
        st.markdown("##### 📋 Detalhes das Auditorias")
        
        for audit_id, audit in sorted(audits.items(), key=lambda x: x[1]['date'], reverse=True):
            with st.expander(f"📅 {format_date_br(audit['date'])} - {audit['auditor']} ({audit['compliance_rate']:.1f}% conforme)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Itens Conformes", f"{audit['compliant_items']}/{audit['total_items']}")
                with col2:
                    st.metric("Taxa de Conformidade", f"{audit['compliance_rate']:.1f}%")
                
                # Análise por categoria
                st.markdown("**Análise por Categoria:**")
                category_summary = {}
                for key, response in audit['responses'].items():
                    category = response['category']
                    if category not in category_summary:
                        category_summary[category] = {'total': 0, 'conforme': 0}
                    category_summary[category]['total'] += 1
                    if response['response'] == '✅ Conforme':
                        category_summary[category]['conforme'] += 1
                
                for category, counts in category_summary.items():
                    rate = (counts['conforme'] / counts['total'] * 100) if counts['total'] > 0 else 0
                    st.progress(rate / 100)
                    st.markdown(f"**{category}**: {counts['conforme']}/{counts['total']} ({rate:.0f}%)")
                
                # Não-conformidades
                non_compliant = [
                    r for r in audit['responses'].values()
                    if r['response'] in ['❌ Não Conforme', '⚠️ Parcial']
                ]
                
                if non_compliant:
                    st.markdown("**Não-Conformidades/Pontos de Atenção:**")
                    for nc in non_compliant:
                        st.markdown(f"- {nc['response']} {nc['item']}")
                
                # Observações
                if audit.get('observations'):
                    st.markdown("**Observações:**")
                    st.info(audit['observations'])


def show_control_phase():
    """Função principal da Fase Control"""
    st.title("🎯 Fase 5: Control (Controlar)")
    st.markdown("Mantenha as melhorias e garanta a sustentabilidade dos resultados.")
    
    # Verificar se há Firebase manager
    if 'firebase_manager' not in st.session_state:
        st.error("❌ Sistema não inicializado corretamente!")
        return
    
    # Criar manager
    manager = ControlPhaseManager(st.session_state.firebase_manager)
    
    # Menu de ferramentas
    tool_option = st.selectbox(
        "Selecione a Ferramenta",
        [
            "📊 Plano de Controle",
            "📈 Monitoramento Estatístico",
            "📋 Documentação Padrão",
            "🔄 Auditoria de Sustentabilidade"
        ]
    )
    
    st.markdown("---")
    
    # Exibir ferramenta selecionada
    if tool_option == "📊 Plano de Controle":
        tool = ControlPlanTool(manager)
        tool.show()
    
    elif tool_option == "📈 Monitoramento Estatístico":
        tool = StatisticalMonitoringTool(manager)
        tool.show()
    
    elif tool_option == "📋 Documentação Padrão":
        tool = StandardDocumentationTool(manager)
        tool.show()
    
    elif tool_option == "🔄 Auditoria de Sustentabilidade":
        tool = SustainabilityAuditTool(manager)
        tool.show()
