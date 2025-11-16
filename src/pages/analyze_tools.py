import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from src.utils.project_manager import ProjectManager
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def show_statistical_analysis(project_data: Dict):
    """Análise Estatística dos Dados"""
    
    project_id = project_data.get('id')
    
    st.markdown("## 📊 Análise Estatística")
    st.markdown("Realize análises estatísticas para identificar padrões e tendências nos dados.")
    
    # Verificar se há dados carregados
    if f'uploaded_data_{project_id}' not in st.session_state:
        st.warning("⚠️ Primeiro faça upload dos dados na fase Measure")
        if st.button("🔄 Ir para Upload de Dados"):
            st.session_state['navigate_to'] = 'measure'
            st.rerun()
        return
    
    df = st.session_state[f'uploaded_data_{project_id}']
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_columns:
        st.error("❌ Nenhuma coluna numérica encontrada")
        return
    
    # Status
    is_completed = project_data.get('analyze', {}).get('statistical_analysis', {}).get('completed', False)
    if is_completed:
        st.success("✅ Análise estatística finalizada")
    else:
        st.info("⏳ Análise em desenvolvimento")
    
    # Tabs para diferentes análises
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Tendências", "🔗 Correlações", "📊 Distribuições", "🧪 Testes"])
    
    with tab1:
        st.markdown("### 📈 Análise de Tendências")
        
        # Seleção de variável
        trend_var = st.selectbox("Selecione a variável:", numeric_columns, key=f"trend_var_{project_id}")
        
        # Análise temporal
        if trend_var:
            data_series = df[trend_var].dropna()
            
            if len(data_series) > 0:
                # Gráfico de linha temporal
                fig = px.line(x=range(len(data_series)), y=data_series, 
                             title=f"Tendência Temporal - {trend_var}")
                fig.update_xaxes(title="Observação")
                fig.update_yaxes(title=trend_var)
                
                # Adicionar linha de tendência
                z = np.polyfit(range(len(data_series)), data_series, 1)
                p = np.poly1d(z)
                fig.add_scatter(x=list(range(len(data_series))), y=p(range(len(data_series))), 
                               mode='lines', name='Tendência', line=dict(dash='dash'))
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Estatísticas de tendência
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    slope = z[0]
                    st.metric("Inclinação", f"{slope:.4f}")
                
                with col2:
                    # Teste de Mann-Kendall para tendência
                    try:
                        from scipy.stats import kendalltau
                        tau, p_value = kendalltau(range(len(data_series)), data_series)
                        st.metric("Kendall Tau", f"{tau:.4f}")
                    except:
                        st.metric("Kendall Tau", "N/A")
                
                with col3:
                    # Variabilidade
                    cv = (data_series.std() / data_series.mean()) * 100 if data_series.mean() != 0 else 0
                    st.metric("Coef. Variação", f"{cv:.2f}%")
    
    with tab2:
        st.markdown("### 🔗 Análise de Correlações")
        
        if len(numeric_columns) >= 2:
            # Matriz de correlação
            corr_matrix = df[numeric_columns].corr()
            
            # Heatmap
            fig = px.imshow(corr_matrix, 
                           text_auto=True, 
                           aspect="auto",
                           title="Matriz de Correlação",
                           color_continuous_scale='RdBu_r',
                           zmin=-1, zmax=1)
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Correlações mais fortes
            st.markdown("#### 🔍 Correlações Mais Significativas")
            
            # Encontrar correlações > 0.5 ou < -0.5
            strong_correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.5:
                        strong_correlations.append({
                            'Variável 1': corr_matrix.columns[i],
                            'Variável 2': corr_matrix.columns[j],
                            'Correlação': corr_value,
                            'Força': 'Forte' if abs(corr_value) > 0.7 else 'Moderada'
                        })
            
            if strong_correlations:
                df_corr = pd.DataFrame(strong_correlations)
                df_corr = df_corr.sort_values('Correlação', key=abs, ascending=False)
                st.dataframe(df_corr, use_container_width=True)
            else:
                st.info("📊 Nenhuma correlação forte encontrada (|r| > 0.5)")
            
            # Scatter plot para correlações específicas
            st.markdown("#### 📊 Análise Detalhada de Correlação")
            col1, col2 = st.columns(2)
            
            with col1:
                x_var = st.selectbox("Variável X:", numeric_columns, key=f"corr_x_{project_id}")
            with col2:
                y_options = [col for col in numeric_columns if col != x_var]
                if y_options:
                    y_var = st.selectbox("Variável Y:", y_options, key=f"corr_y_{project_id}")
                    
                    # Scatter plot com linha de tendência
                    fig = px.scatter(df, x=x_var, y=y_var, trendline="ols",
                                   title=f"Correlação: {x_var} vs {y_var}")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Estatísticas da correlação
                    corr_coef = df[x_var].corr(df[y_var])
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Correlação", f"{corr_coef:.4f}")
                    with col_b:
                        st.metric("R²", f"{corr_coef**2:.4f}")
                    with col_c:
                        # Interpretação
                        if abs(corr_coef) > 0.7:
                            st.success("🔗 Forte")
                        elif abs(corr_coef) > 0.3:
                            st.warning("🔗 Moderada")
                        else:
                            st.info("🔗 Fraca")
        else:
            st.warning("⚠️ Necessário pelo menos 2 variáveis numéricas")
    
    with tab3:
        st.markdown("### 📊 Análise de Distribuições")
        
        # Seleção de variável
        dist_var = st.selectbox("Selecione a variável:", numeric_columns, key=f"dist_var_{project_id}")
        
        if dist_var:
            data_col = df[dist_var].dropna()
            
            if len(data_col) > 0:
                # Layout com gráficos
                col1, col2 = st.columns(2)
                
                with col1:
                    # Histograma
                    fig_hist = px.histogram(x=data_col, nbins=30, title=f"Histograma - {dist_var}")
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with col2:
                    # Q-Q Plot para normalidade
                    try:
                        from scipy.stats import probplot
                        fig_qq = go.Figure()
                        
                        # Calcular Q-Q plot
                        (osm, osr), (slope, intercept, r) = probplot(data_col, dist="norm", plot=None)
                        
                        fig_qq.add_scatter(x=osm, y=osr, mode='markers', name='Dados')
                        fig_qq.add_scatter(x=osm, y=slope * osm + intercept, 
                                         mode='lines', name='Linha Teórica')
                        fig_qq.update_layout(title=f"Q-Q Plot - {dist_var}", 
                                           xaxis_title="Quantis Teóricos",
                                           yaxis_title="Quantis da Amostra")
                        st.plotly_chart(fig_qq, use_container_width=True)
                    except:
                        # Box plot alternativo
                        fig_box = px.box(y=data_col, title=f"Box Plot - {dist_var}")
                        st.plotly_chart(fig_box, use_container_width=True)
                
                # Testes de normalidade
                st.markdown("#### 🧪 Testes de Normalidade")
                
                col_a, col_b, col_c = st.columns(3)
                
                try:
                    # Shapiro-Wilk (para n < 5000)
                    if len(data_col) < 5000:
                        shapiro_stat, shapiro_p = stats.shapiro(data_col)
                        with col_a:
                            st.metric("Shapiro-Wilk", f"p = {shapiro_p:.4f}")
                            if shapiro_p > 0.05:
                                st.success("✅ Normal")
                            else:
                                st.error("❌ Não Normal")
                    
                    # Kolmogorov-Smirnov
                    ks_stat, ks_p = stats.kstest(data_col, 'norm', args=(data_col.mean(), data_col.std()))
                    with col_b:
                        st.metric("Kolmogorov-Smirnov", f"p = {ks_p:.4f}")
                        if ks_p > 0.05:
                            st.success("✅ Normal")
                        else:
                            st.error("❌ Não Normal")
                    
                    # Anderson-Darling
                    try:
                        ad_stat, ad_crit, ad_sig = stats.anderson(data_col, dist='norm')
                        with col_c:
                            # Usar nível de 5%
                            critical_5 = ad_crit[2]  # 5% level
                            st.metric("Anderson-Darling", f"stat = {ad_stat:.4f}")
                            if ad_stat < critical_5:
                                st.success("✅ Normal")
                            else:
                                st.error("❌ Não Normal")
                    except:
                        with col_c:
                            st.info("N/A")
                
                except Exception as e:
                    st.warning(f"⚠️ Erro nos testes: {str(e)}")
                
                # Estatísticas descritivas
                st.markdown("#### 📋 Estatísticas Descritivas")
                
                stats_data = {
                    'Estatística': ['Média', 'Mediana', 'Desvio Padrão', 'Assimetria', 'Curtose', 'Mínimo', 'Máximo'],
                    'Valor': [
                        f"{data_col.mean():.4f}",
                        f"{data_col.median():.4f}",
                        f"{data_col.std():.4f}",
                        f"{stats.skew(data_col):.4f}",
                        f"{stats.kurtosis(data_col):.4f}",
                        f"{data_col.min():.4f}",
                        f"{data_col.max():.4f}"
                    ]
                }
                
                st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
    
    with tab4:
        st.markdown("### 🧪 Testes Estatísticos")
        
        # Tipo de teste
        test_type = st.selectbox(
            "Selecione o tipo de teste:",
            ["Teste t (1 amostra)", "Teste t (2 amostras)", "ANOVA", "Teste de Proporções"],
            key=f"test_type_{project_id}"
        )
        
        if test_type == "Teste t (1 amostra)":
            st.markdown("#### 📊 Teste t para Uma Amostra")
            
            col1, col2 = st.columns(2)
            with col1:
                test_var = st.selectbox("Variável:", numeric_columns, key=f"ttest_var_{project_id}")
            with col2:
                mu0 = st.number_input("Valor de referência (μ₀):", value=0.0, key=f"mu0_{project_id}")
            
            if st.button("🧪 Executar Teste t", key=f"run_ttest_{project_id}"):
                data_test = df[test_var].dropna()
                
                if len(data_test) > 0:
                    t_stat, p_value = stats.ttest_1samp(data_test, mu0)
                    
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.metric("Estatística t", f"{t_stat:.4f}")
                    
                    with col_b:
                        st.metric("p-valor", f"{p_value:.4f}")
                    
                    with col_c:
                        if p_value < 0.05:
                            st.error("❌ Rejeitar H₀")
                        else:
                            st.success("✅ Não rejeitar H₀")
                    
                    # Interpretação
                    st.markdown("**Interpretação:**")
                    if p_value < 0.05:
                        st.write(f"A média da amostra ({data_test.mean():.4f}) é significativamente diferente de {mu0} (p < 0.05)")
                    else:
                        st.write(f"Não há evidência suficiente de que a média seja diferente de {mu0} (p ≥ 0.05)")
        
        elif test_type == "Teste t (2 amostras)":
            st.markdown("#### 📊 Teste t para Duas Amostras")
            
            # Seleção de variáveis
            col1, col2 = st.columns(2)
            with col1:
                var1 = st.selectbox("Variável 1:", numeric_columns, key=f"ttest2_var1_{project_id}")
            with col2:
                var2_options = [col for col in numeric_columns if col != var1]
                if var2_options:
                    var2 = st.selectbox("Variável 2:", var2_options, key=f"ttest2_var2_{project_id}")
                    
                    if st.button("🧪 Executar Teste t (2 amostras)", key=f"run_ttest2_{project_id}"):
                        data1 = df[var1].dropna()
                        data2 = df[var2].dropna()
                        
                        if len(data1) > 0 and len(data2) > 0:
                            t_stat, p_value = stats.ttest_ind(data1, data2)
                            
                            col_a, col_b, col_c = st.columns(3)
                            
                            with col_a:
                                st.metric("Estatística t", f"{t_stat:.4f}")
                            
                            with col_b:
                                st.metric("p-valor", f"{p_value:.4f}")
                            
                            with col_c:
                                if p_value < 0.05:
                                    st.error("❌ Diferença significativa")
                                else:
                                    st.success("✅ Sem diferença significativa")
                            
                            # Estatísticas descritivas
                            st.markdown("**Estatísticas Descritivas:**")
                            
                            comp_data = {
                                'Variável': [var1, var2],
                                'Média': [data1.mean(), data2.mean()],
                                'Desvio Padrão': [data1.std(), data2.std()],
                                'N': [len(data1), len(data2)]
                            }
                            
                            st.dataframe(pd.DataFrame(comp_data), use_container_width=True)
        
        elif test_type == "ANOVA":
            st.markdown("#### 📊 Análise de Variância (ANOVA)")
            
            # Verificar se há variáveis categóricas
            categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
            
            if categorical_columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    response_var = st.selectbox("Variável Resposta:", numeric_columns, key=f"anova_response_{project_id}")
                
                with col2:
                    factor_var = st.selectbox("Fator (Categórica):", categorical_columns, key=f"anova_factor_{project_id}")
                
                if st.button("🧪 Executar ANOVA", key=f"run_anova_{project_id}"):
                    # Preparar dados para ANOVA
                    groups = []
                    group_names = []
                    
                    for group_name in df[factor_var].unique():
                        if pd.notna(group_name):
                            group_data = df[df[factor_var] == group_name][response_var].dropna()
                            if len(group_data) > 0:
                                groups.append(group_data)
                                group_names.append(str(group_name))
                    
                    if len(groups) >= 2:
                        try:
                            f_stat, p_value = stats.f_oneway(*groups)
                            
                            col_a, col_b, col_c = st.columns(3)
                            
                            with col_a:
                                st.metric("Estatística F", f"{f_stat:.4f}")
                            
                            with col_b:
                                st.metric("p-valor", f"{p_value:.4f}")
                            
                            with col_c:
                                if p_value < 0.05:
                                    st.error("❌ Diferença significativa")
                                else:
                                    st.success("✅ Sem diferença significativa")
                            
                            # Estatísticas por grupo
                            st.markdown("**Estatísticas por Grupo:**")
                            
                            group_stats = []
                            for i, group in enumerate(groups):
                                group_stats.append({
                                    'Grupo': group_names[i],
                                    'N': len(group),
                                    'Média': group.mean(),
                                    'Desvio Padrão': group.std()
                                })
                            
                            st.dataframe(pd.DataFrame(group_stats), use_container_width=True)
                            
                            # Box plot por grupo
                            fig = px.box(df, x=factor_var, y=response_var, 
                                       title=f"Box Plot: {response_var} por {factor_var}")
                            st.plotly_chart(fig, use_container_width=True)
                            
                        except Exception as e:
                            st.error(f"❌ Erro na ANOVA: {str(e)}")
                    else:
                        st.error("❌ Necessário pelo menos 2 grupos com dados")
            else:
                st.warning("⚠️ Nenhuma variável categórica encontrada para ANOVA")
    
    # Salvar análise
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Salvar Análise", key=f"save_stat_analysis_{project_id}"):
            analysis_data = {
                'analysis_date': datetime.now().isoformat(),
                'variables_analyzed': numeric_columns,
                'total_observations': len(df),
                'analysis_completed': True
            }
            
            _save_tool_data(project_id, 'statistical_analysis', analysis_data, False)
            st.success("💾 Análise salva!")
    
    with col2:
        if st.button("✅ Finalizar Análise Estatística", key=f"complete_stat_analysis_{project_id}"):
            analysis_data = {
                'analysis_date': datetime.now().isoformat(),
                'variables_analyzed': numeric_columns,
                'total_observations': len(df),
                'analysis_completed': True
            }
            
            _save_tool_data(project_id, 'statistical_analysis', analysis_data, True)
            st.success("✅ Análise estatística finalizada!")
            st.balloons()


def show_root_cause_analysis(project_data: Dict):
    """Análise de Causa Raiz"""
    
    project_id = project_data.get('id')
    
    st.markdown("## 🔍 Análise de Causa Raiz")
    st.markdown("Identifique as causas raiz dos problemas usando ferramentas estruturadas.")
    
    # Inicializar dados
    rca_key = f"root_cause_{project_id}"
    if rca_key not in st.session_state:
        existing_data = project_data.get('analyze', {}).get('root_cause_analysis', {}).get('data', {})
        st.session_state[rca_key] = existing_data if existing_data else {
            'problem_statement': '',
            'why_analysis': [],
            'fishbone_categories': {},
            'pareto_data': []
        }
    
    rca_data = st.session_state[rca_key]
    
    # Status
    is_completed = project_data.get('analyze', {}).get('root_cause_analysis', {}).get('completed', False)
    if is_completed:
        st.success("✅ Análise de causa raiz finalizada")
    else:
        st.info("⏳ Análise em desenvolvimento")
    
    # Tabs para diferentes ferramentas
    tab1, tab2, tab3, tab4 = st.tabs(["🤔 5 Porquês", "🐟 Ishikawa", "📊 Pareto", "🌳 Árvore de Falhas"])
    
    with tab1:
        st.markdown("### 🤔 Análise dos 5 Porquês")
        
        # Declaração do problema
        problem_statement = st.text_area(
            "Declaração do Problema",
            value=rca_data.get('problem_statement', ''),
            placeholder="Descreva claramente o problema que está sendo analisado...",
            height=80,
            key=f"problem_statement_{project_id}"
        )
        
        # Análise dos 5 Porquês
        st.markdown("#### 🔍 Sequência dos Porquês")
        
        if 'why_analysis' not in rca_data:
            rca_data['why_analysis'] = []
        
        # Mostrar porquês existentes
        for i, why_item in enumerate(rca_data['why_analysis']):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                why_text = st.text_input(
                    f"Por que {i+1}:",
                    value=why_item.get('why', ''),
                    key=f"why_{i}_{project_id}"
                )
                
                answer_text = st.text_input(
                    f"Resposta {i+1}:",
                    value=why_item.get('answer', ''),
                    key=f"answer_{i}_{project_id}"
                )
                
                # Atualizar dados
                rca_data['why_analysis'][i] = {
                    'why': why_text,
                    'answer': answer_text
                }
            
            with col2:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"remove_why_{i}_{project_id}"):
                    rca_data['why_analysis'].pop(i)
                    st.session_state[rca_key] = rca_data
                    st.rerun()
        
        # Adicionar novo porquê
        if len(rca_data['why_analysis']) < 5:
            if st.button(f"➕ Adicionar Por que {len(rca_data['why_analysis']) + 1}", key=f"add_why_{project_id}"):
                rca_data['why_analysis'].append({
                    'why': f"Por que {len(rca_data['why_analysis']) + 1}?",
                    'answer': ''
                })
                st.session_state[rca_key] = rca_data
                st.rerun()
        
        # Causa raiz identificada
        if rca_data['why_analysis']:
            st.markdown("#### 🎯 Causa Raiz Identificada")
            
            root_cause = st.text_area(
                "Causa Raiz Principal",
                value=rca_data.get('root_cause', ''),
                placeholder="Com base na análise dos porquês, qual é a causa raiz principal?",
                height=80,
                key=f"root_cause_{project_id}"
            )
            
            rca_data['root_cause'] = root_cause
    
    with tab2:
        st.markdown("### 🐟 Diagrama de Ishikawa (Espinha de Peixe)")
        
        # Categorias principais (6M)
        categories = {
            'Método': 'Processos, procedimentos, instruções',
            'Máquina': 'Equipamentos, ferramentas, tecnologia',
            'Material': 'Matéria-prima, insumos, componentes',
            'Mão de obra': 'Pessoas, habilidades, treinamento',
            'Medição': 'Instrumentos, calibração, sistema de medição',
            'Meio ambiente': 'Condições ambientais, layout, organização'
        }
        
        if 'fishbone_categories' not in rca_data:
            rca_data['fishbone_categories'] = {}
        
        st.markdown("#### 📋 Causas por Categoria (6M)")
        
        for category, description in categories.items():
            with st.expander(f"**{category}** - {description}"):
                
                if category not in rca_data['fishbone_categories']:
                    rca_data['fishbone_categories'][category] = []
                
                # Mostrar causas existentes
                for i, cause in enumerate(rca_data['fishbone_categories'][category]):
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        cause_text = st.text_input(
                            f"Causa {i+1}:",
                            value=cause,
                            key=f"cause_{category}_{i}_{project_id}"
                        )
                        
                        # Atualizar causa
                        rca_data['fishbone_categories'][category][i] = cause_text
                    
                    with col2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🗑️", key=f"remove_cause_{category}_{i}_{project_id}"):
                            rca_data['fishbone_categories'][category].pop(i)
                            st.session_state[rca_key] = rca_data
                            st.rerun()
                
                # Adicionar nova causa
                new_cause = st.text_input(
                    "Nova causa:",
                    key=f"new_cause_{category}_{project_id}",
                    placeholder=f"Digite uma possível causa relacionada a {category}..."
                )
                
                if st.button(f"➕ Adicionar em {category}", key=f"add_cause_{category}_{project_id}"):
                    if new_cause.strip():
                        rca_data['fishbone_categories'][category].append(new_cause.strip())
                        st.session_state[rca_key] = rca_data
                        st.rerun()
        
        # Visualização simplificada do diagrama
        st.markdown("#### 📊 Resumo das Causas Identificadas")
        
        total_causes = sum(len(causes) for causes in rca_data['fishbone_categories'].values())
        
        if total_causes > 0:
            # Criar gráfico de barras com causas por categoria
            category_counts = {cat: len(causes) for cat, causes in rca_data['fishbone_categories'].items() if len(causes) > 0}
            
            if category_counts:
                fig = px.bar(
                    x=list(category_counts.keys()),
                    y=list(category_counts.values()),
                    title="Número de Causas por Categoria",
                    labels={'x': 'Categorias', 'y': 'Número de Causas'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.info(f"📊 Total de causas identificadas: {total_causes}")
    
    with tab3:
        st.markdown("### 📊 Análise de Pareto")
        
        st.markdown("Identifique as causas mais importantes (80/20).")
        
        if 'pareto_data' not in rca_data:
            rca_data['pareto_data'] = []
        
        # Adicionar dados de Pareto
        st.markdown("#### ➕ Adicionar Dados para Pareto")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            pareto_cause = st.text_input("Causa/Problema", key=f"pareto_cause_{project_id}")
        
        with col2:
            pareto_frequency = st.number_input("Frequência", min_value=0, key=f"pareto_freq_{project_id}")
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Adicionar", key=f"add_pareto_{project_id}"):
                if pareto_cause.strip() and pareto_frequency > 0:
                    rca_data['pareto_data'].append({
                        'cause': pareto_cause.strip(),
                        'frequency': pareto_frequency
                    })
                    st.session_state[rca_key] = rca_data
                    st.rerun()
        
        # Mostrar dados existentes
        if rca_data['pareto_data']:
            st.markdown("#### 📋 Dados Coletados")
            
            # Tabela editável
            for i, item in enumerate(rca_data['pareto_data']):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    item['cause'] = st.text_input(
                        f"Causa {i+1}:",
                        value=item['cause'],
                        key=f"edit_cause_{i}_{project_id}"
                    )
                
                with col2:
                    item['frequency'] = st.number_input(
                        f"Freq. {i+1}:",
                        value=item['frequency'],
                        min_value=0,
                        key=f"edit_freq_{i}_{project_id}"
                    )
                
                with col3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"remove_pareto_{i}_{project_id}"):
                        rca_data['pareto_data'].pop(i)
                        st.session_state[rca_key] = rca_data
                        st.rerun()
            
            # Gráfico de Pareto
            if len(rca_data['pareto_data']) > 1:
                st.markdown("#### 📊 Gráfico de Pareto")
                
                # Preparar dados
                pareto_df = pd.DataFrame(rca_data['pareto_data'])
                pareto_df = pareto_df.sort_values('frequency', ascending=False)
                pareto_df['cumulative_freq'] = pareto_df['frequency'].cumsum()
                pareto_df['cumulative_percent'] = (pareto_df['cumulative_freq'] / pareto_df['frequency'].sum()) * 100
                
                # Criar gráfico
                fig = go.Figure()
                
                # Barras
                fig.add_trace(go.Bar(
                    x=pareto_df['cause'],
                    y=pareto_df['frequency'],
                    name='Frequência',
                    yaxis='y',
                    marker_color='lightblue'
                ))
                
                # Linha cumulativa
                fig.add_trace(go.Scatter(
                    x=pareto_df['cause'],
                    y=pareto_df['cumulative_percent'],
                    mode='lines+markers',
                    name='% Cumulativo',
                    yaxis='y2',
                    line=dict(color='red', width=2)
                ))
                
                # Linha 80%
                fig.add_hline(y=80, line_dash="dash", line_color="orange", 
                             annotation_text="80%", yref='y2')
                
                fig.update_layout(
                    title="Análise de Pareto",
                    xaxis_title="Causas",
                    yaxis=dict(title="Frequência", side="left"),
                    yaxis2=dict(title="% Cumulativo", side="right", overlaying="y", range=[0, 100]),
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Identificar causas vitais (80%)
                vital_causes = pareto_df[pareto_df['cumulative_percent'] <= 80]['cause'].tolist()
                if vital_causes:
                    st.success(f"🎯 **Causas Vitais (80%):** {', '.join(vital_causes)}")
    
    with tab4:
        st.markdown("### 🌳 Árvore de Falhas (Fault Tree)")
        
        st.info("🚧 **Ferramenta em Desenvolvimento**")
        
        st.markdown("""
        A Árvore de Falhas é uma ferramenta de análise dedutiva que:
        
        - **Parte do problema principal** (evento topo)
        - **Identifica eventos contribuintes** usando portas lógicas (E, OU)
        - **Mapeia relações de causa e efeito** de forma hierárquica
        - **Calcula probabilidades** de falha (quando aplicável)
        
        **Será implementada em versões futuras com:**
        - Interface gráfica interativa
        - Cálculos de probabilidade
        - Análise de criticidade
        """)
    
    # Atualizar dados no session_state
    rca_data['problem_statement'] = problem_statement
    st.session_state[rca_key] = rca_data
    
    # Botões de ação
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Salvar Análise", key=f"save_rca_{project_id}"):
            _save_tool_data(project_id, 'root_cause_analysis', rca_data, False)
            st.success("💾 Análise de causa raiz salva!")
    
    with col2:
        if st.button("✅ Finalizar Análise de Causa Raiz", key=f"complete_rca_{project_id}"):
            # Validação básica
            if problem_statement.strip() and (rca_data['why_analysis'] or any(rca_data['fishbone_categories'].values())):
                _save_tool_data(project_id, 'root_cause_analysis', rca_data, True)
                st.success("✅ Análise de causa raiz finalizada!")
                st.balloons()
            else:
                st.error("❌ Complete pelo menos a declaração do problema e uma ferramenta de análise")


def show_hypothesis_testing(project_data: Dict):
    """Teste de Hipóteses"""
    
    project_id = project_data.get('id')
    
    st.markdown("## 🧪 Teste de Hipóteses")
    st.markdown("Teste hipóteses sobre as causas identificadas usando métodos estatísticos.")
    
    # Verificar se há dados
    if f'uploaded_data_{project_id}' not in st.session_state:
        st.warning("⚠️ Primeiro faça upload dos dados na fase Measure")
        return
    
    df = st.session_state[f'uploaded_data_{project_id}']
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
    
    # Status
    is_completed = project_data.get('analyze', {}).get('hypothesis_testing', {}).get('completed', False)
    if is_completed:
        st.success("✅ Teste de hipóteses finalizado")
    else:
        st.info("⏳ Teste em desenvolvimento")
    
    # Inicializar dados
    hypothesis_key = f"hypothesis_{project_id}"
    if hypothesis_key not in st.session_state:
        existing_data = project_data.get('analyze', {}).get('hypothesis_testing', {}).get('data', {})
        st.session_state[hypothesis_key] = existing_data if existing_data else {'tests_performed': []}
    
    hypothesis_data = st.session_state[hypothesis_key]
    
    # Formulação de hipóteses
    st.markdown("### 📝 Formulação de Hipóteses")
    
    col1, col2 = st.columns(2)
    
    with col1:
        h0 = st.text_area(
            "Hipótese Nula (H₀)",
            value=hypothesis_data.get('h0', ''),
            placeholder="Ex: A média do processo é igual a 50",
            height=80,
            key=f"h0_{project_id}"
        )
    
    with col2:
        h1 = st.text_area(
            "Hipótese Alternativa (H₁)",
            value=hypothesis_data.get('h1', ''),
            placeholder="Ex: A média do processo é diferente de 50",
            height=80,
            key=f"h1_{project_id}"
        )
    
    # Nível de significância
    alpha = st.selectbox(
        "Nível de Significância (α)",
        [0.01, 0.05, 0.10],
        index=1,
        key=f"alpha_{project_id}"
    )
    
    # Tipos de teste disponíveis
    st.markdown("### 🧪 Executar Testes")
    
    test_type = st.selectbox(
        "Selecione o tipo de teste:",
        [
            "Teste t para uma amostra",
            "Teste t para duas amostras independentes",
            "Teste t para amostras pareadas",
            "Teste de proporção",
            "Teste Qui-quadrado",
            "ANOVA de um fator"
        ],
        key=f"hypothesis_test_type_{project_id}"
    )
    
    # Interface específica para cada tipo de teste
    if test_type == "Teste t para uma amostra":
        st.markdown("#### 📊 Teste t para Uma Amostra")
        
        col1, col2 = st.columns(2)
        
        with col1:
            test_variable = st.selectbox("Variável a testar:", numeric_columns, key=f"t1_var_{project_id}")
        
        with col2:
            mu0 = st.number_input("Valor de referência (μ₀):", value=0.0, key=f"t1_mu0_{project_id}")
        
        if st.button("🧪 Executar Teste t", key=f"run_t1_{project_id}"):
            data_test = df[test_variable].dropna()
            
            if len(data_test) > 0:
                # Executar teste
                t_stat, p_value = stats.ttest_1samp(data_test, mu0)
                
                # Resultados
                col_a, col_b, col_c, col_d = st.columns(4)
                
                with col_a:
                    st.metric("Estatística t", f"{t_stat:.4f}")
                
                with col_b:
                    st.metric("p-valor", f"{p_value:.4f}")
                
                with col_c:
                    st.metric("Média da Amostra", f"{data_test.mean():.4f}")
                
                with col_d:
                    if p_value < alpha:
                        st.error("❌ Rejeitar H₀")
                        conclusion = "Rejeitar H₀"
                    else:
                        st.success("✅ Não rejeitar H₀")
                        conclusion = "Não rejeitar H₀"
                
                # Interpretação detalhada
                st.markdown("#### 📋 Interpretação dos Resultados")
                
                st.write(f"**Hipótese Nula:** {h0 if h0 else 'Não definida'}")
                st.write(f"**Hipótese Alternativa:** {h1 if h1 else 'Não definida'}")
                st.write(f"**Nível de Significância:** {alpha}")
                st.write(f"**Estatística do Teste:** t = {t_stat:.4f}")
                st.write(f"**p-valor:** {p_value:.4f}")
                st.write(f"**Conclusão:** {conclusion}")
                
                if p_value < alpha:
                    st.write(f"Como p-valor ({p_value:.4f}) < α ({alpha}), rejeitamos H₀ ao nível de {alpha*100}% de significância.")
                else:
                    st.write(f"Como p-valor ({p_value:.4f}) ≥ α ({alpha}), não rejeitamos H₀ ao nível de {alpha*100}% de significância.")
                
                # Salvar resultado do teste
                test_result = {
                    'test_type': test_type,
                    'variable': test_variable,
                    'mu0': mu0,
                    'test_statistic': t_stat,
                    'p_value': p_value,
                    'alpha': alpha,
                    'conclusion': conclusion,
                    'sample_mean': data_test.mean(),
                    'sample_size': len(data_test),
                    'timestamp': datetime.now().isoformat()
                }
                
                hypothesis_data['tests_performed'].append(test_result)
                st.session_state[hypothesis_key] = hypothesis_data
    
    elif test_type == "Teste t para duas amostras independentes":
        st.markdown("#### 📊 Teste t para Duas Amostras Independentes")
        
        # Duas opções: duas variáveis numéricas ou uma variável numérica por grupo
        approach = st.radio(
            "Abordagem:",
            ["Duas variáveis numéricas", "Uma variável numérica por grupos"],
            key=f"t2_approach_{project_id}"
        )
        
        if approach == "Duas variáveis numéricas":
            col1, col2 = st.columns(2)
            
            with col1:
                var1 = st.selectbox("Variável 1:", numeric_columns, key=f"t2_var1_{project_id}")
            
            with col2:
                var2_options = [col for col in numeric_columns if col != var1]
                if var2_options:
                    var2 = st.selectbox("Variável 2:", var2_options, key=f"t2_var2_{project_id}")
                    
                    if st.button("🧪 Executar Teste t (2 amostras)", key=f"run_t2_{project_id}"):
                        data1 = df[var1].dropna()
                        data2 = df[var2].dropna()
                        
                        if len(data1) > 0 and len(data2) > 0:
                            # Teste de Levene para igualdade de variâncias
                            levene_stat, levene_p = stats.levene(data1, data2)
                            equal_var = levene_p > 0.05
                            
                            # Teste t
                            t_stat, p_value = stats.ttest_ind(data1, data2, equal_var=equal_var)
                            
                            # Resultados
                            col_a, col_b, col_c, col_d = st.columns(4)
                            
                            with col_a:
                                st.metric("Estatística t", f"{t_stat:.4f}")
                            
                            with col_b:
                                st.metric("p-valor", f"{p_value:.4f}")
                            
                            with col_c:
                                st.metric("Teste de Levene", f"p = {levene_p:.4f}")
                            
                            with col_d:
                                if p_value < alpha:
                                    st.error("❌ Diferença significativa")
                                    conclusion = "Diferença significativa"
                                else:
                                    st.success("✅ Sem diferença significativa")
                                    conclusion = "Sem diferença significativa"
                            
                            # Estatísticas descritivas
                            st.markdown("#### 📊 Estatísticas Descritivas")
                            
                            stats_comp = pd.DataFrame({
                                'Variável': [var1, var2],
                                'N': [len(data1), len(data2)],
                                'Média': [data1.mean(), data2.mean()],
                                'Desvio Padrão': [data1.std(), data2.std()],
                                'Erro Padrão': [data1.sem(), data2.sem()]
                            })
                            
                            st.dataframe(stats_comp, use_container_width=True)
                            
                            # Box plot comparativo
                            fig = go.Figure()
                            fig.add_trace(go.Box(y=data1, name=var1))
                            fig.add_trace(go.Box(y=data2, name=var2))
                            fig.update_layout(title=f"Comparação: {var1} vs {var2}", height=400)
                            st.plotly_chart(fig, use_container_width=True)
        
        else:  # Uma variável por grupos
            if categorical_columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    response_var = st.selectbox("Variável Resposta:", numeric_columns, key=f"t2_response_{project_id}")
                
                with col2:
                    group_var = st.selectbox("Variável de Grupo:", categorical_columns, key=f"t2_group_{project_id}")
                
                # Selecionar dois grupos específicos
                unique_groups = df[group_var].unique()
                if len(unique_groups) >= 2:
                    selected_groups = st.multiselect(
                        "Selecione 2 grupos para comparar:",
                        unique_groups,
                        max_selections=2,
                        key=f"t2_selected_groups_{project_id}"
                    )
                    
                    if len(selected_groups) == 2:
                        if st.button("🧪 Executar Teste t (por grupos)", key=f"run_t2_groups_{project_id}"):
                            group1_data = df[df[group_var] == selected_groups[0]][response_var].dropna()
                            group2_data = df[df[group_var] == selected_groups[1]][response_var].dropna()
                            
                            if len(group1_data) > 0 and len(group2_data) > 0:
                                # Teste t
                                t_stat, p_value = stats.ttest_ind(group1_data, group2_data)
                                
                                # Resultados similares ao caso anterior...
                                col_a, col_b, col_c = st.columns(3)
                                
                                with col_a:
                                    st.metric("Estatística t", f"{t_stat:.4f}")
                                
                                with col_b:
                                    st.metric("p-valor", f"{p_value:.4f}")
                                
                                with col_c:
                                    if p_value < alpha:
                                        st.error("❌ Diferença significativa")
                                    else:
                                        st.success("✅ Sem diferença significativa")
            else:
                st.warning("⚠️ Nenhuma variável categórica encontrada")
    
    # Histórico de testes realizados
    if hypothesis_data.get('tests_performed'):
        st.markdown("### 📋 Histórico de Testes Realizados")
        
        tests_df = pd.DataFrame(hypothesis_data['tests_performed'])
        
        # Mostrar apenas colunas relevantes
        display_columns = ['test_type', 'p_value', 'alpha', 'conclusion', 'timestamp']
        available_columns = [col for col in display_columns if col in tests_df.columns]
        
        if available_columns:
            st.dataframe(tests_df[available_columns], use_container_width=True)
    
    # Atualizar dados
    hypothesis_data.update({
        'h0': h0,
        'h1': h1,
        'alpha': alpha
    })
    st.session_state[hypothesis_key] = hypothesis_data
    
    # Botões de ação
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Salvar Testes", key=f"save_hypothesis_{project_id}"):
            _save_tool_data(project_id, 'hypothesis_testing', hypothesis_data, False)
            st.success("💾 Testes de hipóteses salvos!")
    
    with col2:
        if st.button("✅ Finalizar Teste de Hipóteses", key=f"complete_hypothesis_{project_id}"):
            if hypothesis_data.get('tests_performed') and h0.strip() and h1.strip():
                _save_tool_data(project_id, 'hypothesis_testing', hypothesis_data, True)
                st.success("✅ Teste de hipóteses finalizado!")
                st.balloons()
            else:
                st.error("❌ Defina as hipóteses e execute pelo menos um teste")


def show_process_analysis(project_data: Dict):
    """Análise do Processo"""
    
    project_id = project_data.get('id')
    
    st.markdown("## ⚙️ Análise do Processo")
    st.markdown("Analise o processo atual para identificar gargalos e oportunidades de melhoria.")
    
    # Inicializar dados
    process_key = f"process_analysis_{project_id}"
    if process_key not in st.session_state:
        existing_data = project_data.get('analyze', {}).get('process_analysis', {}).get('data', {})
        st.session_state[process_key] = existing_data if existing_data else {
            'process_steps': [],
            'bottlenecks': [],
            'cycle_time_analysis': {},
            'value_stream_data': []
        }
    
    process_data = st.session_state[process_key]
    
    # Status
    is_completed = project_data.get('analyze', {}).get('process_analysis', {}).get('completed', False)
    if is_completed:
        st.success("✅ Análise do processo finalizada")
    else:
        st.info("⏳ Análise em desenvolvimento")
    
    # Tabs para diferentes análises
    tab1, tab2, tab3, tab4 = st.tabs(["🔄 Fluxo do Processo", "⏱️ Tempo de Ciclo", "🚧 Gargalos", "📊 Value Stream"])
    
    with tab1:
        st.markdown("### 🔄 Mapeamento do Fluxo do Processo")
        
        # Adicionar etapas do processo
        st.markdown("#### ➕ Etapas do Processo")
        
        if 'process_steps' not in process_data:
            process_data['process_steps'] = []
        
        # Adicionar nova etapa
        with st.expander("Adicionar Nova Etapa"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                step_name = st.text_input("Nome da Etapa", key=f"step_name_{project_id}")
                step_type = st.selectbox("Tipo", ["Operação", "Inspeção", "Transporte", "Espera", "Estoque"], key=f"step_type_{project_id}")
            
            with col2:
                step_time = st.number_input("Tempo (min)", min_value=0.0, key=f"step_time_{project_id}")
                step_resources = st.text_input("Recursos Necessários", key=f"step_resources_{project_id}")
            
            with col3:
                step_value = st.selectbox("Agrega Valor?", ["Sim", "Não", "Necessário"], key=f"step_value_{project_id}")
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("➕ Adicionar Etapa", key=f"add_step_{project_id}"):
                    if step_name.strip():
                        process_data['process_steps'].append({
                            'name': step_name.strip(),
                            'type': step_type,
                            'time': step_time,
                            'resources': step_resources,
                            'value_add': step_value,
                            'order': len(process_data['process_steps']) + 1
                        })
                        st.session_state[process_key] = process_data
                        st.rerun()
        
        # Mostrar etapas existentes
        if process_data['process_steps']:
            st.markdown("#### 📋 Etapas Mapeadas")
            
            for i, step in enumerate(process_data['process_steps']):
                with st.expander(f"**{i+1}. {step['name']}** ({step['type']}) - {step['time']} min"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Tipo:** {step['type']}")
                        st.write(f"**Tempo:** {step['time']} minutos")
                    
                    with col2:
                        st.write(f"**Recursos:** {step['resources']}")
                        st.write(f"**Agrega Valor:** {step['value_add']}")
                    
                    with col3:
                        if st.button("🗑️ Remover", key=f"remove_step_{i}_{project_id}"):
                            process_data['process_steps'].pop(i)
                            st.session_state[process_key] = process_data
                            st.rerun()
            
            # Resumo do processo
            st.markdown("#### 📊 Resumo do Processo")
            
            total_time = sum(step['time'] for step in process_data['process_steps'])
            value_add_time = sum(step['time'] for step in process_data['process_steps'] if step['value_add'] == 'Sim')
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Etapas", len(process_data['process_steps']))
            
            with col2:
                st.metric("Tempo Total", f"{total_time:.1f} min")
            
            with col3:
                st.metric("Tempo que Agrega Valor", f"{value_add_time:.1f} min")
            
            with col4:
                efficiency = (value_add_time / total_time * 100) if total_time > 0 else 0
                st.metric("Eficiência do Processo", f"{efficiency:.1f}%")
            
            # Gráfico do fluxo
            if len(process_data['process_steps']) > 1:
                step_names = [f"{i+1}. {step['name']}" for i, step in enumerate(process_data['process_steps'])]
                step_times = [step['time'] for step in process_data['process_steps']]
                
                fig = px.bar(x=step_names, y=step_times, title="Tempo por Etapa do Processo")
                fig.update_xaxes(title="Etapas")
                fig.update_yaxes(title="Tempo (min)")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### ⏱️ Análise de Tempo de Ciclo")
        
        # Verificar se há dados de tempo carregados
        if f'uploaded_data_{project_id}' in st.session_state:
            df = st.session_state[f'uploaded_data_{project_id}']
            time_columns = [col for col in df.select_dtypes(include=[np.number]).columns if 'time' in col.lower() or 'tempo' in col.lower()]
            
            if time_columns:
                selected_time_col = st.selectbox("Selecione coluna de tempo:", time_columns, key=f"time_col_{project_id}")
                
                if selected_time_col:
                    time_data = df[selected_time_col].dropna()
                    
                    if len(time_data) > 0:
                        # Estatísticas de tempo
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Tempo Médio", f"{time_data.mean():.2f}")
                        
                        with col2:
                            st.metric("Mediana", f"{time_data.median():.2f}")
                        
                        with col3:
                            st.metric("Desvio Padrão", f"{time_data.std():.2f}")
                        
                        with col4:
                            cv = (time_data.std() / time_data.mean()) * 100 if time_data.mean() != 0 else 0
                            st.metric("Coef. Variação", f"{cv:.1f}%")
                        
                        # Gráficos de tempo
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            # Histograma
                            fig_hist = px.histogram(x=time_data, nbins=30, title="Distribuição dos Tempos de Ciclo")
                            st.plotly_chart(fig_hist, use_container_width=True)
                        
                        with col_b:
                            # Gráfico de controle
                            fig_control = px.line(x=range(len(time_data)), y=time_data, title="Gráfico de Controle - Tempos")
                            
                            # Adicionar limites de controle
                            mean_time = time_data.mean()
                            std_time = time_data.std()
                            
                            fig_control.add_hline(y=mean_time, line_dash="solid", line_color="green", annotation_text="Média")
                            fig_control.add_hline(y=mean_time + 3*std_time, line_dash="dash", line_color="red", annotation_text="UCL")
                            fig_control.add_hline(y=mean_time - 3*std_time, line_dash="dash", line_color="red", annotation_text="LCL")
                            
                            st.plotly_chart(fig_control, use_container_width=True)
            else:
                st.info("💡 Nenhuma coluna de tempo encontrada nos dados")
        else:
            st.warning("⚠️ Carregue dados na fase Measure para análise de tempo de ciclo")
    
    with tab3:
        st.markdown("### 🚧 Identificação de Gargalos")
        
        if 'bottlenecks' not in process_data:
            process_data['bottlenecks'] = []
        
        # Adicionar gargalo
        st.markdown("#### ➕ Identificar Gargalos")
        
        with st.expander("Adicionar Gargalo"):
            col1, col2 = st.columns(2)
            
            with col1:
                bottleneck_name = st.text_input("Nome do Gargalo", key=f"bottleneck_name_{project_id}")
                bottleneck_location = st.text_input("Localização", key=f"bottleneck_location_{project_id}")
            
            with col2:
                bottleneck_impact = st.selectbox("Impacto", ["Alto", "Médio", "Baixo"], key=f"bottleneck_impact_{project_id}")
                bottleneck_frequency = st.selectbox("Frequência", ["Sempre", "Frequente", "Ocasional", "Raro"], key=f"bottleneck_freq_{project_id}")
            
            bottleneck_description = st.text_area("Descrição do Gargalo", key=f"bottleneck_desc_{project_id}")
            
            if st.button("➕ Adicionar Gargalo", key=f"add_bottleneck_{project_id}"):
                if bottleneck_name.strip():
                    process_data['bottlenecks'].append({
                        'name': bottleneck_name.strip(),
                        'location': bottleneck_location,
                        'impact': bottleneck_impact,
                        'frequency': bottleneck_frequency,
                        'description': bottleneck_description
                    })
                    st.session_state[process_key] = process_data
                    st.rerun()
        
        # Mostrar gargalos identificados
        if process_data['bottlenecks']:
            st.markdown("#### 🚧 Gargalos Identificados")
            
            for i, bottleneck in enumerate(process_data['bottlenecks']):
                with st.expander(f"**{bottleneck['name']}** - {bottleneck['impact']} Impacto"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Localização:** {bottleneck['location']}")
                        st.write(f"**Impacto:** {bottleneck['impact']}")
                    
                    with col2:
                        st.write(f"**Frequência:** {bottleneck['frequency']}")
                        st.write(f"**Descrição:** {bottleneck['description']}")
                    
                    with col3:
                        if st.button("🗑️ Remover", key=f"remove_bottleneck_{i}_{project_id}"):
                            process_data['bottlenecks'].pop(i)
                            st.session_state[process_key] = process_data
                            st.rerun()
            
            # Matriz de priorização de gargalos
            if len(process_data['bottlenecks']) > 1:
                st.markdown("#### 📊 Matriz de Priorização")
                
                impact_map = {"Alto": 3, "Médio": 2, "Baixo": 1}
                freq_map = {"Sempre": 4, "Frequente": 3, "Ocasional": 2, "Raro": 1}
                
                bottleneck_names = [b['name'] for b in process_data['bottlenecks']]
                impact_scores = [impact_map[b['impact']] for b in process_data['bottlenecks']]
                freq_scores = [freq_map[b['frequency']] for b in process_data['bottlenecks']]
                
                fig = px.scatter(x=freq_scores, y=impact_scores, text=bottleneck_names,
                               labels={'x': 'Frequência', 'y': 'Impacto'},
                               title="Matriz de Priorização de Gargalos")
                
                fig.update_traces(textposition="top center", marker=dict(size=12))
                fig.update_xaxes(range=[0.5, 4.5], tickvals=[1, 2, 3, 4], ticktext=['Raro', 'Ocasional', 'Frequente', 'Sempre'])
                fig.update_yaxes(range=[0.5, 3.5], tickvals=[1, 2, 3], ticktext=['Baixo', 'Médio', 'Alto'])
                
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown("### 📊 Value Stream Mapping")
        
        st.info("🚧 **Value Stream Mapping Simplificado**")
        
        # Análise de valor agregado baseado nas etapas do processo
        if process_data.get('process_steps'):
            st.markdown("#### 📈 Análise de Valor Agregado")
            
            # Categorizar etapas
            value_add_steps = [s for s in process_data['process_steps'] if s['value_add'] == 'Sim']
            necessary_steps = [s for s in process_data['process_steps'] if s['value_add'] == 'Necessário']
            waste_steps = [s for s in process_data['process_steps'] if s['value_add'] == 'Não']
            
            # Métricas de valor
            col1, col2, col3 = st.columns(3)
            
            with col1:
                va_time = sum(s['time'] for s in value_add_steps)
                st.metric("Tempo que Agrega Valor", f"{va_time:.1f} min")
                st.write(f"**Etapas:** {len(value_add_steps)}")
            
            with col2:
                nva_time = sum(s['time'] for s in necessary_steps)
                st.metric("Tempo Necessário (NVA)", f"{nva_time:.1f} min")
                st.write(f"**Etapas:** {len(necessary_steps)}")
            
            with col3:
                waste_time = sum(s['time'] for s in waste_steps)
                st.metric("Desperdício", f"{waste_time:.1f} min")
                st.write(f"**Etapas:** {len(waste_steps)}")
            
            # Gráfico de pizza
            if va_time + nva_time + waste_time > 0:
                labels = ['Agrega Valor', 'Necessário', 'Desperdício']
                values = [va_time, nva_time, waste_time]
                colors = ['green', 'yellow', 'red']
                
                fig = px.pie(values=values, names=labels, title="Distribuição do Tempo por Tipo de Atividade")
                fig.update_traces(marker=dict(colors=colors))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 Primeiro mapeie as etapas do processo na aba 'Fluxo do Processo'")
    
    # Botões de ação
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Salvar Análise", key=f"save_process_analysis_{project_id}"):
            _save_tool_data(project_id, 'process_analysis', process_data, False)
            st.success("💾 Análise do processo salva!")
    
    with col2:
        if st.button("✅ Finalizar Análise do Processo", key=f"complete_process_analysis_{project_id}"):
            if process_data.get('process_steps') or process_data.get('bottlenecks'):
                _save_tool_data(project_id, 'process_analysis', process_data, True)
                st.success("✅ Análise do processo finalizada!")
                st.balloons()
            else:
                st.error("❌ Mapeie pelo menos as etapas do processo ou identifique gargalos")


def _save_tool_data(project_id: str, tool_name: str, data: dict, completed: bool = False):
    """Função auxiliar para salvar dados das ferramentas"""
    try:
        project_manager = ProjectManager()
        
        update_data = {
            f'analyze.{tool_name}.data': data,
            f'analyze.{tool_name}.completed': completed,
            f'analyze.{tool_name}.updated_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        success = project_manager.update_project(project_id, update_data)
        
        if success and 'current_project' in st.session_state:
            # Atualizar session_state
            if 'analyze' not in st.session_state.current_project:
                st.session_state.current_project['analyze'] = {}
            if tool_name not in st.session_state.current_project['analyze']:
                st.session_state.current_project['analyze'][tool_name] = {}
            
            st.session_state.current_project['analyze'][tool_name]['data'] = data
            st.session_state.current_project['analyze'][tool_name]['completed'] = completed
            st.session_state.current_project['analyze'][tool_name]['updated_at'] = datetime.now().isoformat()
        
        return success
        
    except Exception as e:
        st.error(f"❌ Erro ao salvar: {str(e)}")
        return False


def show_analyze_tools(project_data: Dict):
    """Função principal para mostrar as ferramentas da fase Analyze"""
    
    if not project_data:
        st.error("❌ Projeto não encontrado")
        return
    
    project_id = project_data.get('id')
    
    # Menu de ferramentas
    st.markdown("### 🔧 Ferramentas da Fase Analyze")
    
    tool_options = {
        "statistical_analysis": "📊 Análise Estatística",
        "root_cause_analysis": "🔍 Análise de Causa Raiz",
        "hypothesis_testing": "🧪 Teste de Hipóteses",
        "process_analysis": "⚙️ Análise do Processo"
    }
    
    # Verificar status das ferramentas
    analyze_data = project_data.get('analyze', {})
    
    # Selectbox para navegação
    tool_names_with_status = []
    tool_keys = list(tool_options.keys())
    
    for key, name in tool_options.items():
        tool_data = analyze_data.get(key, {})
        is_completed = tool_data.get('completed', False) if isinstance(tool_data, dict) else False
        status_icon = "✅" if is_completed else "⏳"
        tool_names_with_status.append(f"{status_icon} {name}")
    
    selected_index = st.selectbox(
        "Selecione uma ferramenta:",
        range(len(tool_names_with_status)),
        format_func=lambda x: tool_names_with_status[x],
        key=f"analyze_tool_selector_{project_id}"
    )
    
    selected_tool = tool_keys[selected_index]
    
    st.divider()
    
    # Mostrar ferramenta selecionada
    if selected_tool == "statistical_analysis":
        show_statistical_analysis(project_data)
    elif selected_tool == "root_cause_analysis":
        show_root_cause_analysis(project_data)
    elif selected_tool == "hypothesis_testing":
        show_hypothesis_testing(project_data)
    elif selected_tool == "process_analysis":
        show_process_analysis(project_data)
    
    # Progresso geral da fase Analyze
    st.divider()
    st.markdown("### 📊 Progresso da Fase Analyze")
    
    # Recarregar dados atualizados
    if 'current_project' in st.session_state:
        updated_analyze_data = st.session_state.current_project.get('analyze', {})
    else:
        updated_analyze_data = analyze_data
    
    total_tools = len(tool_options)
    completed_tools = 0
    
    # Status das ferramentas
    st.markdown("#### 📋 Status das Ferramentas:")
    cols = st.columns(len(tool_options))
    
    for i, (key, name) in enumerate(tool_options.items()):
        tool_data = updated_analyze_data.get(key, {})
        is_completed = tool_data.get('completed', False) if isinstance(tool_data, dict) else False
        
        if is_completed:
            completed_tools += 1
        
        with cols[i]:
            if is_completed:
                st.success(f"✅ {name.split(' ', 1)[1]}")
            else:
                st.info(f"⏳ {name.split(' ', 1)[1]}")
    
    progress = (completed_tools / total_tools) * 100
    
    # Barra de progresso
    col_prog1, col_prog2 = st.columns([3, 1])
    
    with col_prog1:
        st.progress(progress / 100)
        st.caption(f"{completed_tools}/{total_tools} ferramentas concluídas ({progress:.1f}%)")
    
    with col_prog2:
        if progress == 100:
            st.success("🎉 Completo!")
        else:
            st.info(f"⏳ {progress:.0f}%")
    
    # Conclusão da fase
    if progress == 100:
        st.success("🎉 **Parabéns! Fase Analyze concluída com sucesso!**")
        st.info("✨ Você pode avançar para a fase **Improve** usando a navegação das fases.")
        
        # Resumo das principais descobertas
        st.markdown("### 🎯 Principais Descobertas da Análise")
        
        discoveries = []
        
        # Verificar se há análises concluídas
        if updated_analyze_data.get('root_cause_analysis', {}).get('completed'):
            rca_data = updated_analyze_data['root_cause_analysis'].get('data', {})
            if rca_data.get('root_cause'):
                discoveries.append(f"🔍 **Causa Raiz:** {rca_data['root_cause']}")
        
        if updated_analyze_data.get('statistical_analysis', {}).get('completed'):
            discoveries.append("📊 **Análise Estatística:** Padrões e tendências identificados nos dados")
        
        if updated_analyze_data.get('hypothesis_testing', {}).get('completed'):
            discoveries.append("🧪 **Hipóteses:** Causas validadas estatisticamente")
        
        if updated_analyze_data.get('process_analysis', {}).get('completed'):
            discoveries.append("⚙️ **Processo:** Gargalos e oportunidades de melhoria mapeados")
        
        if discoveries:
            for discovery in discoveries:
                st.write(discovery)
        else:
            st.info("Complete as ferramentas para ver um resumo das descobertas")
    
    # Debug (opcional)
    if st.checkbox("🔍 Debug - Mostrar dados Analyze", key=f"debug_analyze_{project_id}"):
        st.json(updated_analyze_data)
