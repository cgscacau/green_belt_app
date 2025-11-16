import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List
from src.utils.project_manager import ProjectManager

class DefineTools:
    def __init__(self, project_data: Dict):
        self.project = project_data
        self.project_manager = ProjectManager()
        self.project_id = project_data.get('id')
        self.define_data = project_data.get('define', {})
    
    def save_tool_data(self, tool_name: str, data: Dict, completed: bool = False):
        """Salva dados de uma ferramenta no Firebase"""
        try:
            # Preparar dados para atualização
            update_data = {
                f'define.{tool_name}.data': data,
                f'define.{tool_name}.completed': completed,
                f'define.{tool_name}.updated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Salvar no Firebase
            success = self.project_manager.update_project(self.project_id, update_data)
            
            if success:
                # Atualizar dados locais
                if 'define' not in self.project:
                    self.project['define'] = {}
                if tool_name not in self.project['define']:
                    self.project['define'][tool_name] = {}
                
                self.project['define'][tool_name]['data'] = data
                self.project['define'][tool_name]['completed'] = completed
                
                # Atualizar session_state
                st.session_state.current_project = self.project
                
                return True
            return False
            
        except Exception as e:
            st.error(f"Erro ao salvar dados: {str(e)}")
            return False
    
    def show_project_charter(self):
        """Ferramenta Project Charter"""
        st.markdown("## 📋 Project Charter")
        st.markdown("O Project Charter é o documento oficial que autoriza e define o projeto.")
        
        # Dados existentes
        charter_data = self.define_data.get('charter', {}).get('data', {})
        
        with st.form("charter_form"):
            st.markdown("### 📝 Informações do Charter")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Informações básicas
                st.markdown("#### 🎯 Definição do Projeto")
                
                problem_statement = st.text_area(
                    "Declaração do Problema *",
                    value=charter_data.get('problem_statement', ''),
                    placeholder="Descreva claramente o problema que será resolvido...",
                    height=100,
                    help="O que está errado? Qual é o problema específico?"
                )
                
                goal_statement = st.text_area(
                    "Declaração do Objetivo *",
                    value=charter_data.get('goal_statement', ''),
                    placeholder="O que queremos alcançar com este projeto...",
                    height=100,
                    help="Objetivo SMART do projeto"
                )
                
                scope_included = st.text_area(
                    "Escopo - O que está INCLUÍDO",
                    value=charter_data.get('scope_included', ''),
                    placeholder="Processos, áreas, produtos incluídos...",
                    height=80
                )
                
                scope_excluded = st.text_area(
                    "Escopo - O que está EXCLUÍDO",
                    value=charter_data.get('scope_excluded', ''),
                    placeholder="O que NÃO será abordado neste projeto...",
                    height=80
                )
            
            with col2:
                # Métricas e benefícios
                st.markdown("#### 📊 Métricas e Benefícios")
                
                primary_metric = st.text_input(
                    "Métrica Principal *",
                    value=charter_data.get('primary_metric', ''),
                    placeholder="Ex: Taxa de defeitos, Tempo de ciclo...",
                    help="Principal indicador que será melhorado"
                )
                
                baseline_value = st.text_input(
                    "Valor Atual (Baseline)",
                    value=charter_data.get('baseline_value', ''),
                    placeholder="Ex: 15%, 30 minutos, 50 defeitos/mês...",
                    help="Situação atual da métrica"
                )
                
                target_value = st.text_input(
                    "Meta (Target) *",
                    value=charter_data.get('target_value', ''),
                    placeholder="Ex: 5%, 20 minutos, 10 defeitos/mês...",
                    help="Onde queremos chegar"
                )
                
                financial_benefit = st.number_input(
                    "Benefício Financeiro Anual (R$)",
                    value=float(charter_data.get('financial_benefit', 0)),
                    min_value=0.0,
                    step=1000.0,
                    help="Impacto financeiro esperado por ano"
                )
                
                # Cronograma
                st.markdown("#### 📅 Cronograma")
                
                project_duration = st.selectbox(
                    "Duração Estimada",
                    options=["3 meses", "4 meses", "5 meses", "6 meses", "Outro"],
                    index=["3 meses", "4 meses", "5 meses", "6 meses", "Outro"].index(charter_data.get('project_duration', '4 meses'))
                )
                
                if project_duration == "Outro":
                    custom_duration = st.text_input(
                        "Especificar duração",
                        value=charter_data.get('custom_duration', ''),
                        placeholder="Ex: 8 semanas, 120 dias..."
                    )
                else:
                    custom_duration = ""
            
            # Seção de equipe
            st.markdown("### 👥 Equipe do Projeto")
            
            col3, col4 = st.columns(2)
            
            with col3:
                project_leader = st.text_input(
                    "Líder do Projeto (Green Belt) *",
                    value=charter_data.get('project_leader', ''),
                    placeholder="Nome do responsável pelo projeto"
                )
                
                sponsor = st.text_input(
                    "Sponsor/Champion *",
                    value=charter_data.get('sponsor', ''),
                    placeholder="Nome do patrocinador do projeto"
                )
            
            with col4:
                team_members = st.text_area(
                    "Membros da Equipe",
                    value=charter_data.get('team_members', ''),
                    placeholder="Liste os membros da equipe (um por linha)",
                    height=80
                )
                
                stakeholders = st.text_area(
                    "Principais Stakeholders",
                    value=charter_data.get('stakeholders', ''),
                    placeholder="Pessoas impactadas pelo projeto (um por linha)",
                    height=80
                )
            
            # Riscos e premissas
            st.markdown("### ⚠️ Riscos e Premissas")
            
            col5, col6 = st.columns(2)
            
            with col5:
                risks = st.text_area(
                    "Principais Riscos",
                    value=charter_data.get('risks', ''),
                    placeholder="Liste os principais riscos do projeto...",
                    height=100
                )
            
            with col6:
                assumptions = st.text_area(
                    "Premissas",
                    value=charter_data.get('assumptions', ''),
                    placeholder="O que estamos assumindo como verdade...",
                    height=100
                )
            
            # Botões do formulário
            st.divider()
            
            col7, col8, col9 = st.columns([2, 1, 1])
            
            with col8:
                save_draft = st.form_submit_button("💾 Salvar Rascunho", use_container_width=True)
            
            with col9:
                complete_charter = st.form_submit_button("✅ Finalizar Charter", use_container_width=True, type="primary")
            
            # Processar submissão
            if save_draft or complete_charter:
                # Validar campos obrigatórios apenas se estiver finalizando
                required_fields = [
                    (problem_statement, "Declaração do Problema"),
                    (goal_statement, "Declaração do Objetivo"),
                    (primary_metric, "Métrica Principal"),
                    (target_value, "Meta (Target)"),
                    (project_leader, "Líder do Projeto"),
                    (sponsor, "Sponsor/Champion")
                ]
                
                if complete_charter:
                    missing_fields = [field_name for field_value, field_name in required_fields if not field_value.strip()]
                    
                    if missing_fields:
                        st.error(f"❌ Campos obrigatórios não preenchidos: {', '.join(missing_fields)}")
                        return
                
                # Preparar dados para salvamento
                charter_data = {
                    'problem_statement': problem_statement,
                    'goal_statement': goal_statement,
                    'scope_included': scope_included,
                    'scope_excluded': scope_excluded,
                    'primary_metric': primary_metric,
                    'baseline_value': baseline_value,
                    'target_value': target_value,
                    'financial_benefit': financial_benefit,
                    'project_duration': project_duration,
                    'custom_duration': custom_duration,
                    'project_leader': project_leader,
                    'sponsor': sponsor,
                    'team_members': team_members,
                    'stakeholders': stakeholders,
                    'risks': risks,
                    'assumptions': assumptions
                }
                
                # Salvar dados
                success = self.save_tool_data('charter', charter_data, completed=complete_charter)
                
                if success:
                    if complete_charter:
                        st.success("✅ Charter finalizado e salvo com sucesso!")
                        st.balloons()
                    else:
                        st.success("💾 Rascunho salvo com sucesso!")
                    
                    # Rerun para atualizar a interface
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar Charter")
        
        # Mostrar resumo se charter estiver completo
        if self.define_data.get('charter', {}).get('completed', False):
            self.show_charter_summary()
    
    def show_charter_summary(self):
        """Exibe resumo do charter finalizado"""
        charter_data = self.define_data.get('charter', {}).get('data', {})
        
        st.markdown("### 📊 Resumo do Charter")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Métrica Principal", charter_data.get('primary_metric', 'N/A'))
        
        with col2:
            baseline = charter_data.get('baseline_value', 'N/A')
            target = charter_data.get('target_value', 'N/A')
            st.metric("Meta", f"{baseline} → {target}")
        
        with col3:
            benefit = charter_data.get('financial_benefit', 0)
            st.metric("Benefício Anual", f"R$ {benefit:,.2f}")
        
        # Botão para editar
        if st.button("✏️ Editar Charter", key="edit_charter"):
            # Reabrir para edição
            st.rerun()
    
    def show_stakeholder_mapping(self):
        """Ferramenta de Mapeamento de Stakeholders"""
        st.markdown("## 👥 Mapeamento de Stakeholders")
        st.markdown("Identifique e analise todas as pessoas impactadas pelo projeto.")
        
        # Dados existentes
        stakeholder_data = self.define_data.get('stakeholders', {}).get('data', [])
        
        # Interface para adicionar/editar stakeholders
        st.markdown("### ➕ Adicionar/Editar Stakeholder")
        
        with st.form("stakeholder_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                name = st.text_input("Nome *", placeholder="Nome do stakeholder")
                role = st.text_input("Cargo/Função", placeholder="Ex: Gerente de Produção")
                department = st.text_input("Departamento", placeholder="Ex: Operações")
            
            with col2:
                influence = st.selectbox(
                    "Nível de Influência *",
                    options=["Alto", "Médio", "Baixo"],
                    help="Capacidade de impactar o projeto"
                )
                
                interest = st.selectbox(
                    "Nível de Interesse *",
                    options=["Alto", "Médio", "Baixo"],
                    help="Interesse no resultado do projeto"
                )
                
                attitude = st.selectbox(
                    "Atitude *",
                    options=["Favorável", "Neutro", "Resistente"],
                    help="Posição em relação ao projeto"
                )
            
            with col3:
                impact = st.selectbox(
                    "Impacto do Projeto",
                    options=["Alto", "Médio", "Baixo"],
                    help="O quanto será impactado pelo projeto"
                )
                
                communication_preference = st.selectbox(
                    "Preferência de Comunicação",
                    options=["E-mail", "Reunião", "Relatório", "Dashboard", "Outro"]
                )
                
                notes = st.text_area(
                    "Observações",
                    placeholder="Informações adicionais sobre este stakeholder...",
                    height=60
                )
            
            # Botão para adicionar
            add_stakeholder = st.form_submit_button("➕ Adicionar Stakeholder", use_container_width=True)
            
            if add_stakeholder:
                if name and influence and interest and attitude:
                    new_stakeholder = {
                        'id': len(stakeholder_data) + 1,
                        'name': name,
                        'role': role,
                        'department': department,
                        'influence': influence,
                        'interest': interest,
                        'attitude': attitude,
                        'impact': impact,
                        'communication_preference': communication_preference,
                        'notes': notes,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    stakeholder_data.append(new_stakeholder)
                    
                    # Salvar dados
                    success = self.save_tool_data('stakeholders', stakeholder_data)
                    
                    if success:
                        st.success(f"✅ Stakeholder '{name}' adicionado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar stakeholder")
                else:
                    st.error("❌ Preencha os campos obrigatórios (Nome, Influência, Interesse, Atitude)")
        
        # Exibir lista de stakeholders
        if stakeholder_data:
            st.markdown("### 📋 Lista de Stakeholders")
            
            # Converter para DataFrame para melhor visualização
            df_stakeholders = pd.DataFrame(stakeholder_data)
            
            # Tabela interativa
            st.dataframe(
                df_stakeholders[['name', 'role', 'department', 'influence', 'interest', 'attitude']],
                use_container_width=True,
                column_config={
                    'name': 'Nome',
                    'role': 'Cargo',
                    'department': 'Departamento',
                    'influence': 'Influência',
                    'interest': 'Interesse',
                    'attitude': 'Atitude'
                }
            )
            
            # Matriz de Poder vs Interesse
            st.markdown("### 📊 Matriz Poder vs Interesse")
            
            # Preparar dados para o gráfico
            influence_map = {'Alto': 3, 'Médio': 2, 'Baixo': 1}
            interest_map = {'Alto': 3, 'Médio': 2, 'Baixo': 1}
            attitude_colors = {'Favorável': 'green', 'Neutro': 'orange', 'Resistente': 'red'}
            
            fig = go.Figure()
            
            for stakeholder in stakeholder_data:
                fig.add_trace(go.Scatter(
                    x=[interest_map[stakeholder['interest']]],
                    y=[influence_map[stakeholder['influence']]],
                    mode='markers+text',
                    text=[stakeholder['name']],
                    textposition="middle center",
                    marker=dict(
                        size=20,
                        color=attitude_colors[stakeholder['attitude']],
                        opacity=0.7
                    ),
                    name=stakeholder['attitude'],
                    showlegend=False
                ))
            
            fig.update_layout(
                title="Matriz Poder (Influência) vs Interesse",
                xaxis_title="Interesse",
                yaxis_title="Influência",
                xaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Baixo', 'Médio', 'Alto']),
                yaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Baixo', 'Médio', 'Alto']),
                height=500
            )
            
            # Adicionar quadrantes
            fig.add_shape(type="line", x0=2, y0=0, x1=2, y1=4, line=dict(color="gray", width=1, dash="dash"))
            fig.add_shape(type="line", x0=0, y0=2, x1=4, y1=2, line=dict(color="gray", width=1, dash="dash"))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Legenda da matriz
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("**🟢 Alto Poder, Alto Interesse**")
                st.caption("Gerenciar de perto")
            
            with col2:
                st.markdown("**🟡 Alto Poder, Baixo Interesse**")
                st.caption("Manter satisfeito")
            
            with col3:
                st.markdown("**🟠 Baixo Poder, Alto Interesse**")
                st.caption("Manter informado")
            
            with col4:
                st.markdown("**🔴 Baixo Poder, Baixo Interesse**")
                st.caption("Monitorar")
            
            # Opções de ação
            st.markdown("### ⚙️ Ações")
            
            col_action1, col_action2, col_action3 = st.columns(3)
            
            with col_action1:
                if st.button("📊 Exportar Lista", use_container_width=True):
                    csv = df_stakeholders.to_csv(index=False)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name=f"stakeholders_{self.project['name']}.csv",
                        mime="text/csv"
                    )
            
            with col_action2:
                if st.button("🗑️ Limpar Todos", use_container_width=True):
                    if st.session_state.get('confirm_clear_stakeholders'):
                        # Limpar dados
                        success = self.save_tool_data('stakeholders', [])
                        if success:
                            st.success("✅ Todos os stakeholders foram removidos")
                            st.rerun()
                        del st.session_state.confirm_clear_stakeholders
                    else:
                        st.session_state.confirm_clear_stakeholders = True
                        st.warning("⚠️ Clique novamente para confirmar")
            
            with col_action3:
                if st.button("✅ Finalizar Mapeamento", use_container_width=True, type="primary"):
                    # Marcar como completo
                    success = self.save_tool_data('stakeholders', stakeholder_data, completed=True)
                    if success:
                        st.success("✅ Mapeamento de Stakeholders finalizado!")
                        st.balloons()
                        st.rerun()
        
        else:
            st.info("👥 Nenhum stakeholder adicionado ainda. Use o formulário acima para começar.")
    
    def show_voice_of_customer(self):
        """Ferramenta Voice of Customer (VOC)"""
        st.markdown("## 🗣️ Voice of Customer (VOC)")
        st.markdown("Capture as necessidades, expectativas e requisitos dos clientes.")
        
        # Dados existentes
        voc_data = self.define_data.get('voc', {}).get('data', {})
        
        # Tabs para organizar VOC
        tab1, tab2, tab3 = st.tabs(["🎯 Definir Clientes", "📋 Coletar VOC", "📊 Análise VOC"])
        
        with tab1:
            st.markdown("### 🎯 Identificação dos Clientes")
            
            # Clientes identificados
            customers = voc_data.get('customers', [])
            
            with st.form("customer_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    customer_name = st.text_input("Nome do Cliente/Segmento *", placeholder="Ex: Operadores de máquina")
                    customer_type = st.selectbox("Tipo de Cliente", options=["Interno", "Externo", "Regulatório"])
                    customer_importance = st.selectbox("Importância", options=["Alta", "Média", "Baixa"])
                
                with col2:
                    customer_description = st.text_area(
                        "Descrição",
                        placeholder="Descreva este cliente/segmento...",
                        height=100
                    )
                
                if st.form_submit_button("➕ Adicionar Cliente"):
                    if customer_name:
                        new_customer = {
                            'id': len(customers) + 1,
                            'name': customer_name,
                            'type': customer_type,
                            'importance': customer_importance,
                            'description': customer_description,
                            'created_at': datetime.now().isoformat()
                        }
                        
                        customers.append(new_customer)
                        voc_data['customers'] = customers
                        
                        success = self.save_tool_data('voc', voc_data)
                        if success:
                            st.success(f"✅ Cliente '{customer_name}' adicionado!")
                            st.rerun()
            
            # Lista de clientes
            if customers:
                st.markdown("#### 📋 Clientes Identificados")
                for customer in customers:
                    with st.expander(f"{customer['name']} ({customer['type']})"):
                        st.write(f"**Importância:** {customer['importance']}")
                        st.write(f"**Descrição:** {customer['description']}")
        
        with tab2:
            st.markdown("### 📋 Coleta de Necessidades dos Clientes")
            
            if not voc_data.get('customers', []):
                st.warning("⚠️ Primeiro identifique os clientes na aba 'Definir Clientes'")
                return
            
            # Necessidades coletadas
            needs = voc_data.get('needs', [])
            
            with st.form("voc_needs_form"):
                # Seletor de cliente
                customer_options = [c['name'] for c in voc_data.get('customers', [])]
                selected_customer = st.selectbox("Cliente *", options=customer_options)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    need_statement = st.text_area(
                        "Necessidade/Requisito *",
                        placeholder="Ex: Reduzir tempo de setup da máquina...",
                        height=80
                    )
                    
                    collection_method = st.selectbox(
                        "Método de Coleta",
                        options=["Entrevista", "Survey", "Observação", "Focus Group", "Análise de Reclamações", "Outro"]
                    )
                
                with col2:
                    priority = st.selectbox("Prioridade *", options=["Alta", "Média", "Baixa"])
                    
                    current_satisfaction = st.slider(
                        "Satisfação Atual (1-10)",
                        min_value=1,
                        max_value=10,
                        value=5,
                        help="Como o cliente avalia a situação atual"
                    )
                    
                    notes = st.text_area(
                        "Observações",
                        placeholder="Contexto adicional, citações do cliente...",
                        height=60
                    )
                
                if st.form_submit_button("➕ Adicionar Necessidade"):
                    if selected_customer and need_statement:
                        new_need = {
                            'id': len(needs) + 1,
                            'customer': selected_customer,
                            'statement': need_statement,
                            'method': collection_method,
                            'priority': priority,
                            'satisfaction': current_satisfaction,
                            'notes': notes,
                            'created_at': datetime.now().isoformat()
                        }
                        
                        needs.append(new_need)
                        voc_data['needs'] = needs
                        
                        success = self.save_tool_data('voc', voc_data)
                        if success:
                            st.success("✅ Necessidade adicionada!")
                            st.rerun()
            
            # Lista de necessidades
            if needs:
                st.markdown("#### 📋 Necessidades Coletadas")
                
                df_needs = pd.DataFrame(needs)
                st.dataframe(
                    df_needs[['customer', 'statement', 'priority', 'satisfaction', 'method']],
                    use_container_width=True,
                    column_config={
                        'customer': 'Cliente',
                        'statement': 'Necessidade',
                        'priority': 'Prioridade',
                        'satisfaction': 'Satisfação Atual',
                        'method': 'Método'
                    }
                )
        
        with tab3:
            st.markdown("### 📊 Análise do VOC")
            
            needs = voc_data.get('needs', [])
            
            if not needs:
                st.info("📋 Colete algumas necessidades dos clientes primeiro")
                return
            
            # Análises gráficas
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribuição por prioridade
                priority_counts = {}
                for need in needs:
                    priority = need['priority']
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1
                
                fig_priority = px.pie(
                    values=list(priority_counts.values()),
                    names=list(priority_counts.keys()),
                    title="Distribuição por Prioridade",
                    color_discrete_map={'Alta': 'red', 'Média': 'orange', 'Baixa': 'green'}
                )
                st.plotly_chart(fig_priority, use_container_width=True)
            
            with col2:
                # Satisfação média por cliente
                customer_satisfaction = {}
                customer_counts = {}
                
                for need in needs:
                    customer = need['customer']
                    satisfaction = need['satisfaction']
                    
                    if customer not in customer_satisfaction:
                        customer_satisfaction[customer] = 0
                        customer_counts[customer] = 0
                    
                    customer_satisfaction[customer] += satisfaction
                    customer_counts[customer] += 1
                
                # Calcular médias
                avg_satisfaction = {
                    customer: customer_satisfaction[customer] / customer_counts[customer]
                    for customer in customer_satisfaction
                }
                
                fig_satisfaction = px.bar(
                    x=list(avg_satisfaction.keys()),
                    y=list(avg_satisfaction.values()),
                    title="Satisfação Média por Cliente",
                    labels={'x': 'Cliente', 'y': 'Satisfação Média'}
                )
                fig_satisfaction.update_layout(yaxis=dict(range=[0, 10]))
                st.plotly_chart(fig_satisfaction, use_container_width=True)
            
            # Priorização de necessidades
            st.markdown("#### 🎯 Necessidades Priorizadas")
            
            # Ordenar por prioridade e satisfação
            priority_order = {'Alta': 3, 'Média': 2, 'Baixa': 1}
            sorted_needs = sorted(needs, key=lambda x: (priority_order[x['priority']], -x['satisfaction']), reverse=True)
            
            for i, need in enumerate(sorted_needs[:5], 1):  # Top 5
                priority_color = {'Alta': '🔴', 'Média': '🟡', 'Baixa': '🟢'}
                st.markdown(f"**{i}. {priority_color[need['priority']]} {need['statement']}**")
                st.caption(f"Cliente: {need['customer']} | Satisfação atual: {need['satisfaction']}/10")
            
            # Finalizar VOC
            if st.button("✅ Finalizar VOC", type="primary", use_container_width=True):
                success = self.save_tool_data('voc', voc_data, completed=True)
                if success:
                    st.success("✅ Voice of Customer finalizado!")
                    st.balloons()
                    st.rerun()
    
    def show_sipoc_diagram(self):
        """Ferramenta SIPOC"""
        st.markdown("## 📊 Diagrama SIPOC")
        st.markdown("Suppliers - Inputs - Process - Outputs - Customers")
        
        # Dados existentes
        sipoc_data = self.define_data.get('sipoc', {}).get('data', {
            'suppliers': [],
            'inputs': [],
            'process_steps': [],
            'outputs': [],
            'customers': []
        })
        
        # Interface em tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏭 Suppliers", "📥 Inputs", "⚙️ Process", "📤 Outputs", "👥 Customers", "📊 Diagrama"])
        
        with tab1:
            st.markdown("### 🏭 Fornecedores (Suppliers)")
            st.caption("Quem fornece as entradas para o processo?")
            
            self._manage_sipoc_items('suppliers', sipoc_data, "Fornecedor", "Ex: Departamento de Compras")
        
        with tab2:
            st.markdown("### 📥 Entradas (Inputs)")
            st.caption("O que é necessário para executar o processo?")
            
            self._manage_sipoc_items('inputs', sipoc_data, "Entrada", "Ex: Matéria-prima, Informações")
        
        with tab3:
            st.markdown("### ⚙️ Processo (Process)")
            st.caption("Quais são os principais passos do processo?")
            
            self._manage_sipoc_process_steps(sipoc_data)
        
        with tab4:
            st.markdown("### 📤 Saídas (Outputs)")
            st.caption("O que o processo produz?")
            
            self._manage_sipoc_items('outputs', sipoc_data, "Saída", "Ex: Produto acabado, Relatório")
        
        with tab5:
            st.markdown("### 👥 Clientes (Customers)")
            st.caption("Quem recebe as saídas do processo?")
            
            self._manage_sipoc_items('customers', sipoc_data, "Cliente", "Ex: Cliente final, Próximo processo")
        
        with tab6:
            st.markdown("### 📊 Diagrama SIPOC Completo")
            
            self._show_sipoc_diagram(sipoc_data)
    
    def _manage_sipoc_items(self, category: str, sipoc_data: Dict, item_name: str, placeholder: str):
        """Gerencia itens do SIPOC (Suppliers, Inputs, Outputs, Customers)"""
        
        items = sipoc_data.get(category, [])
        
        with st.form(f"{category}_form"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                new_item = st.text_input(f"Novo {item_name} *", placeholder=placeholder)
            
            with col2:
                add_item = st.form_submit_button(f"➕ Adicionar", use_container_width=True)
            
            if add_item and new_item:
                items.append({
                    'id': len(items) + 1,
                    'name': new_item,
                    'created_at': datetime.now().isoformat()
                })
                
                sipoc_data[category] = items
                success = self.save_tool_data('sipoc', sipoc_data)
                
                if success:
                    st.success(f"✅ {item_name} adicionado!")
                    st.rerun()
        
        # Lista de itens
        if items:
            st.markdown(f"#### 📋 {item_name}s Cadastrados")
            
            for i, item in enumerate(items):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"**{i+1}.** {item['name']}")
                
                with col2:
                    if st.button("🗑️", key=f"delete_{category}_{i}", help=f"Remover {item_name.lower()}"):
                        items.pop(i)
                        sipoc_data[category] = items
                        success = self.save_tool_data('sipoc', sipoc_data)
                        if success:
                            st.rerun()
        else:
            st.info(f"📝 Nenhum {item_name.lower()} adicionado ainda")
    
    def _manage_sipoc_process_steps(self, sipoc_data: Dict):
        """Gerencia os passos do processo no SIPOC"""
        
        process_steps = sipoc_data.get('process_steps', [])
        
        with st.form("process_steps_form"):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                step_name = st.text_input("Nome do Passo *", placeholder="Ex: Receber material")
            
            with col2:
                step_description = st.text_input("Descrição", placeholder="Breve descrição do passo")
            
            with col3:
                add_step = st.form_submit_button("➕ Adicionar", use_container_width=True)
            
            if add_step and step_name:
                process_steps.append({
                    'id': len(process_steps) + 1,
                    'name': step_name,
                    'description': step_description,
                    'sequence': len(process_steps) + 1,
                    'created_at': datetime.now().isoformat()
                })
                
                sipoc_data['process_steps'] = process_steps
                success = self.save_tool_data('sipoc', sipoc_data)
                
                if success:
                    st.success("✅ Passo do processo adicionado!")
                    st.rerun()
        
        # Lista de passos
        if process_steps:
            st.markdown("#### ⚙️ Passos do Processo")
            
            for i, step in enumerate(process_steps):
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    st.markdown(f"**{i+1}.**")
                
                with col2:
                    st.markdown(f"**{step['name']}**")
                    if step.get('description'):
                        st.caption(step['description'])
                
                with col3:
                    if st.button("🗑️", key=f"delete_step_{i}", help="Remover passo"):
                        process_steps.pop(i)
                        # Reorganizar sequência
                        for j, remaining_step in enumerate(process_steps):
                            remaining_step['sequence'] = j + 1
                        
                        sipoc_data['process_steps'] = process_steps
                        success = self.save_tool_data('sipoc', sipoc_data)
                        if success:
                            st.rerun()
        else:
            st.info("⚙️ Nenhum passo do processo adicionado ainda")
    
    def _show_sipoc_diagram(self, sipoc_data: Dict):
        """Mostra o diagrama SIPOC visual"""
        
        # Verificar se há dados suficientes
        has_data = any([
            sipoc_data.get('suppliers', []),
            sipoc_data.get('inputs', []),
            sipoc_data.get('process_steps', []),
            sipoc_data.get('outputs', []),
            sipoc_data.get('customers', [])
        ])
        
        if not has_data:
            st.info("📊 Preencha as outras abas para visualizar o diagrama SIPOC")
            return
        
        # Criar visualização do SIPOC
        col1, col2, col3, col4, col5 = st.columns(5)
        
        columns = [
            (col1, "🏭 SUPPLIERS", sipoc_data.get('suppliers', []), '#FF6B6B'),
            (col2, "📥 INPUTS", sipoc_data.get('inputs', []), '#4ECDC4'),
            (col3, "⚙️ PROCESS", sipoc_data.get('process_steps', []), '#45B7D1'),
            (col4, "📤 OUTPUTS", sipoc_data.get('outputs', []), '#96CEB4'),
            (col5, "👥 CUSTOMERS", sipoc_data.get('customers', []), '#FFEAA7')
        ]
        
        for col, title, items, color in columns:
            with col:
                st.markdown(f"### {title}")
                
                if items:
                    for item in items:
                        if title == "⚙️ PROCESS":
                            st.markdown(f"""
                            <div style='background-color: {color}; padding: 8px; margin: 4px 0; border-radius: 5px; color: white; text-align: center;'>
                                <strong>{item.get('sequence', '')}. {item['name']}</strong>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style='background-color: {color}; padding: 8px; margin: 4px 0; border-radius: 5px; color: white; text-align: center;'>
                                {item['name']}
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown("*Vazio*")
        
        # Estatísticas do SIPOC
        st.markdown("### 📈 Estatísticas do SIPOC")
        
        col_stats1, col_stats2, col_stats3, col_stats4, col_stats5 = st.columns(5)
        
        with col_stats1:
            st.metric("Fornecedores", len(sipoc_data.get('suppliers', [])))
        
        with col_stats2:
            st.metric("Entradas", len(sipoc_data.get('inputs', [])))
        
        with col_stats3:
            st.metric("Passos do Processo", len(sipoc_data.get('process_steps', [])))
        
        with col_stats4:
            st.metric("Saídas", len(sipoc_data.get('outputs', [])))
        
        with col_stats5:
            st.metric("Clientes", len(sipoc_data.get('customers', [])))
        
        # Botão para finalizar SIPOC
        if st.button("✅ Finalizar SIPOC", type="primary", use_container_width=True):
            success = self.save_tool_data('sipoc', sipoc_data, completed=True)
            if success:
                st.success("✅ Diagrama SIPOC finalizado!")
                st.balloons()
                st.rerun()
    
    def show_project_timeline(self):
        """Ferramenta de Timeline do Projeto"""
        st.markdown("## 📅 Timeline do Projeto")
        st.markdown("Defina o cronograma detalhado das atividades do projeto.")
        
        # Dados existentes
        timeline_data = self.define_data.get('timeline', {}).get('data', {
            'milestones': [],
            'phases': []
        })
        
        # Tabs para timeline
        tab1, tab2, tab3 = st.tabs(["🎯 Marcos (Milestones)", "📋 Fases DMAIC", "📊 Cronograma Visual"])
        
        with tab1:
            st.markdown("### 🎯 Marcos do Projeto")
            
            milestones = timeline_data.get('milestones', [])
            
            with st.form("milestone_form"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    milestone_name = st.text_input("Nome do Marco *", placeholder="Ex: Charter Aprovado")
                    milestone_date = st.date_input("Data Prevista *", value=datetime.now().date())
                
                with col2:
                    milestone_type = st.selectbox(
                        "Tipo de Marco",
                        options=["Entregável", "Aprovação", "Revisão", "Evento", "Outro"]
                    )
                    responsible = st.text_input("Responsável", placeholder="Nome do responsável")
                
                with col3:
                    status = st.selectbox("Status", options=["Planejado", "Em andamento", "Concluído", "Atrasado"])
                    description = st.text_area("Descrição", placeholder="Descrição do marco...", height=60)
                
                if st.form_submit_button("➕ Adicionar Marco"):
                    if milestone_name and milestone_date:
                        new_milestone = {
                            'id': len(milestones) + 1,
                            'name': milestone_name,
                            'date': milestone_date.isoformat(),
                            'type': milestone_type,
                            'responsible': responsible,
                            'status': status,
                            'description': description,
                            'created_at': datetime.now().isoformat()
                        }
                        
                        milestones.append(new_milestone)
                        timeline_data['milestones'] = milestones
                        
                        success = self.save_tool_data('timeline', timeline_data)
                        if success:
                            st.success("✅ Marco adicionado!")
                            st.rerun()
            
            # Lista de marcos
            if milestones:
                st.markdown("#### 📋 Marcos Cadastrados")
                
                # Ordenar por data
                sorted_milestones = sorted(milestones, key=lambda x: x['date'])
                
                for milestone in sorted_milestones:
                    status_colors = {
                        'Planejado': '🔵',
                        'Em andamento': '🟡',
                        'Concluído': '🟢',
                        'Atrasado': '🔴'
                    }
                    
                    with st.expander(f"{status_colors[milestone['status']]} {milestone['name']} - {milestone['date']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Tipo:** {milestone['type']}")
                            st.write(f"**Status:** {milestone['status']}")
                        
                        with col2:
                            st.write(f"**Responsável:** {milestone['responsible']}")
                            st.write(f"**Data:** {milestone['date']}")
                        
                        if milestone['description']:
                            st.write(f"**Descrição:** {milestone['description']}")
        
        with tab2:
            st.markdown("### 📋 Cronograma das Fases DMAIC")
            
            phases = timeline_data.get('phases', [])
            
            # Se não existirem fases, criar template padrão
            if not phases:
                default_phases = [
                    {'name': 'Define', 'duration_weeks': 3, 'description': 'Definir problema e objetivos'},
                    {'name': 'Measure', 'duration_weeks': 4, 'description': 'Medir situação atual'},
                    {'name': 'Analyze', 'duration_weeks': 4, 'description': 'Analisar causas raiz'},
                    {'name': 'Improve', 'duration_weeks': 6, 'description': 'Implementar melhorias'},
                    {'name': 'Control', 'duration_weeks': 3, 'description': 'Controlar e sustentar'}
                ]
                
                st.info("📋 Criando cronograma padrão das fases DMAIC...")
                
                if st.button("🚀 Criar Cronograma Padrão", type="primary"):
                    timeline_data['phases'] = default_phases
                    success = self.save_tool_data('timeline', timeline_data)
                    if success:
                        st.success("✅ Cronograma padrão criado!")
                        st.rerun()
            
            else:
                st.markdown("#### ⏱️ Duração das Fases")
                
                # Permitir edição das durações
                with st.form("phases_duration_form"):
                    updated_phases = []
                    
                    for i, phase in enumerate(phases):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown(f"**{phase['name']}**")
                        
                        with col2:
                            duration = st.number_input(
                                f"Duração (semanas)",
                                min_value=1,
                                max_value=12,
                                value=phase.get('duration_weeks', 4),
                                key=f"duration_{i}"
                            )
                        
                        with col3:
                            description = st.text_input(
                                "Descrição",
                                value=phase.get('description', ''),
                                key=f"desc_{i}"
                            )
                        
                        updated_phases.append({
                            'name': phase['name'],
                            'duration_weeks': duration,
                            'description': description
                        })
                    
                    if st.form_submit_button("💾 Salvar Durações"):
                        timeline_data['phases'] = updated_phases
                        success = self.save_tool_data('timeline', timeline_data)
                        if success:
                            st.success("✅ Durações atualizadas!")
                            st.rerun()
                
                # Calcular datas das fases
                project_start = datetime.fromisoformat(self.project.get('start_date', datetime.now().isoformat()))
                
                st.markdown("#### 📅 Cronograma Calculado")
                
                current_date = project_start
                total_weeks = 0
                
                for phase in phases:
                    duration_weeks = phase.get('duration_weeks', 4)
                    end_date = current_date + timedelta(weeks=duration_weeks)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(f"**{phase['name']}**")
                    
                    with col2:
                        st.write(f"📅 {current_date.strftime('%d/%m/%Y')}")
                    
                    with col3:
                        st.write(f"📅 {end_date.strftime('%d/%m/%Y')}")
                    
                    with col4:
                        st.write(f"⏱️ {duration_weeks} semanas")
                    
                    current_date = end_date
                    total_weeks += duration_weeks
                
                st.info(f"📊 **Duração total do projeto:** {total_weeks} semanas ({total_weeks//4} meses)")
        
        with tab3:
            st.markdown("### 📊 Cronograma Visual")
            
            # Gráfico de Gantt simplificado
            phases = timeline_data.get('phases', [])
            milestones = timeline_data.get('milestones', [])
            
            if phases:
                # Preparar dados para o gráfico
                project_start = datetime.fromisoformat(self.project.get('start_date', datetime.now().isoformat()))
                
                gantt_data = []
                current_date = project_start
                
                for phase in phases:
                    duration_weeks = phase.get('duration_weeks', 4)
                    end_date = current_date + timedelta(weeks=duration_weeks)
                    
                    gantt_data.append({
                        'Task': phase['name'],
                        'Start': current_date,
                        'Finish': end_date,
                        'Resource': 'DMAIC'
                    })
                    
                    current_date = end_date
                
                # Criar DataFrame
                df_gantt = pd.DataFrame(gantt_data)
                
                # Gráfico de barras horizontais (Gantt simplificado)
                fig = px.timeline(
                    df_gantt,
                    x_start="Start",
                    x_end="Finish",
                    y="Task",
                    title="Cronograma das Fases DMAIC",
                    labels={"Task": "Fase"}
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Marcos no cronograma
                if milestones:
                    st.markdown("#### 🎯 Marcos no Cronograma")
                    
                    milestone_dates = []
                    milestone_names = []
                    
                    for milestone in milestones:
                        milestone_date = datetime.fromisoformat(milestone['date'])
                        milestone_dates.append(milestone_date)
                        milestone_names.append(milestone['name'])
                    
                    fig_milestones = go.Figure()
                    
                    fig_milestones.add_trace(go.Scatter(
                        x=milestone_dates,
                        y=[1] * len(milestone_dates),
                        mode='markers+text',
                        text=milestone_names,
                        textposition="top center",
                        marker=dict(size=15, color='red', symbol='diamond'),
                        name='Marcos'
                    ))
                    
                    fig_milestones.update_layout(
                        title="Marcos do Projeto",
                        xaxis_title="Data",
                        yaxis=dict(visible=False),
                        height=200
                    )
                    
                    st.plotly_chart(fig_milestones, use_container_width=True)
            
            else:
                st.info("📅 Configure as fases na aba 'Fases DMAIC' para visualizar o cronograma")
            
            # Finalizar Timeline
            if st.button("✅ Finalizar Timeline", type="primary", use_container_width=True):
                success = self.save_tool_data('timeline', timeline_data, completed=True)
                if success:
                    st.success("✅ Timeline do projeto finalizada!")
                    st.balloons()
                    st.rerun()

def show_define_tools(project_data: Dict):
    """Função principal para mostrar as ferramentas da fase Define"""
    
    if not project_data:
        st.error("❌ Projeto não encontrado")
        return
    
    # Inicializar classe de ferramentas
    tools = DefineTools(project_data)
    
    # Seletor de ferramenta
    st.markdown("### 🔧 Selecione a Ferramenta")
    
    tool_options = {
        "charter": "📋 Project Charter",
        "stakeholders": "👥 Stakeholder Mapping", 
        "voc": "🗣️ Voice of Customer",
        "sipoc": "📊 SIPOC Diagram",
        "timeline": "📅 Project Timeline"
    }
    
    # Verificar status das ferramentas
    define_data = project_data.get('define', {})
    
    cols = st.columns(len(tool_options))
    selected_tool = None
    
    for i, (tool_key, tool_name) in enumerate(tool_options.items()):
        with cols[i]:
            is_completed = define_data.get(tool_key, {}).get('completed', False)
            button_type = "primary" if is_completed else "secondary"
            status_icon = "✅" if is_completed else "⏳"
            
            if st.button(f"{status_icon} {tool_name}", key=f"tool_{tool_key}", use_container_width=True, type=button_type):
                selected_tool = tool_key
    
    # Mostrar ferramenta selecionada
    if selected_tool:
        st.divider()
        
        if selected_tool == "charter":
            tools.show_project_charter()
        elif selected_tool == "stakeholders":
            tools.show_stakeholder_mapping()
        elif selected_tool == "voc":
            tools.show_voice_of_customer()
        elif selected_tool == "sipoc":
            tools.show_sipoc_diagram()
        elif selected_tool == "timeline":
            tools.show_project_timeline()
    
    else:
        # Mostrar overview das ferramentas
        st.markdown("### 🎯 Ferramentas da Fase Define")
        
        st.markdown("""
        Selecione uma ferramenta acima para começar. As ferramentas marcadas com ✅ já foram concluídas.
        
        **Ordem recomendada:**
        1. 📋 **Project Charter** - Documente oficialmente o projeto
        2. 👥 **Stakeholder Mapping** - Identifique pessoas impactadas  
        3. 🗣️ **Voice of Customer** - Capture necessidades dos clientes
        4. 📊 **SIPOC Diagram** - Mapeie o processo atual
        5. 📅 **Project Timeline** - Defina cronograma detalhado
        """)
        
        # Progresso geral da fase Define
        total_tools = len(tool_options)
        completed_tools = sum(1 for tool_key in tool_options.keys() 
                            if define_data.get(tool_key, {}).get('completed', False))
        
        progress = (completed_tools / total_tools) * 100
        
        st.markdown("### 📊 Progresso da Fase Define")
        st.progress(progress / 100)
        st.caption(f"{completed_tools}/{total_tools} ferramentas concluídas ({progress:.1f}%)")
        
        if progress == 100:
            st.success("🎉 **Parabéns! Fase Define concluída com sucesso!**")
            st.info("✨ Você pode avançar para a fase **Measure** usando a navegação das fases.")
