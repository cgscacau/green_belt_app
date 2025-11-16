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
                
                # Adicionar linha de tendência manual
                x_vals = np.array(range(len(data_series)))
                y_vals = data_series.values
                
                # Calcular regressão linear simples
                try:
                    slope, intercept = np.polyfit(x_vals, y_vals, 1)
                    trend_line = slope * x_vals + intercept
                    
                    fig.add_scatter(x=x_vals, y=trend_line, 
                                   mode='lines', name='Tendência', 
                                   line=dict(dash='dash', color='red'))
                except:
                    pass  # Se der erro, não adiciona a linha de tendência
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Estatísticas de tendência
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    try:
                        slope = np.polyfit(range(len(data_series)), data_series, 1)[0]
                        st.metric("Inclinação", f"{slope:.4f}")
                    except:
                        st.metric("Inclinação", "N/A")
                
                with col2:
                    # Teste de correlação com tempo (substituindo Mann-Kendall)
                    try:
                        correlation, p_value = stats.pearsonr(range(len(data_series)), data_series)
                        st.metric("Correlação Temporal", f"{correlation:.4f}")
                    except:
                        st.metric("Correlação Temporal", "N/A")
                
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
                    
                    # Scatter plot simples (sem trendline OLS)
                    fig = px.scatter(df, x=x_var, y=y_var, title=f"Correlação: {x_var} vs {y_var}")
                    
                    # Adicionar linha de tendência manual
                    try:
                        clean_df = df[[x_var, y_var]].dropna()
                        if len(clean_df) > 1:
                            slope, intercept = np.polyfit(clean_df[x_var], clean_df[y_var], 1)
                            x_range = np.linspace(clean_df[x_var].min(), clean_df[x_var].max(), 100)
                            y_trend = slope * x_range + intercept
                            
                            fig.add_scatter(x=x_range, y=y_trend, mode='lines', 
                                          name='Linha de Tendência', line=dict(color='red'))
                    except:
                        pass
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Estatísticas da correlação
                    try:
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
                    except:
                        st.error("❌ Erro no cálculo da correlação")
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
                    # Q-Q Plot simplificado ou Box plot
                    try:
                        # Tentar criar Q-Q plot simples
                        sorted_data = np.sort(data_col)
                        n = len(sorted_data)
                        theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, n))
                        
                        fig_qq = go.Figure()
                        fig_qq.add_scatter(x=theoretical_quantiles, y=sorted_data, 
                                         mode='markers', name='Dados')
                        
                        # Linha de referência
                        min_val = min(theoretical_quantiles.min(), sorted_data.min())
                        max_val = max(theoretical_quantiles.max(), sorted_data.max())
                        fig_qq.add_scatter(x=[min_val, max_val], y=[min_val, max_val], 
                                         mode='lines', name='Linha Teórica', 
                                         line=dict(color='red', dash='dash'))
                        
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
                    
                    # Teste simples de assimetria
                    skewness = stats.skew(data_col)
                    with col_c:
                        st.metric("Assimetria", f"{skewness:.4f}")
                        if abs(skewness) < 0.5:
                            st.success("✅ Simétrica")
                        elif abs(skewness) < 1:
                            st.warning("⚠️ Moderada")
                        else:
                            st.error("❌ Assimétrica")
                
                except Exception as e:
                    st.warning(f"⚠️ Erro nos testes: {str(e)}")
                
                # Estatísticas descritivas
                st.markdown("#### 📋 Estatísticas Descritivas")
                
                try:
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
                except Exception as e:
                    st.error(f"❌ Erro no cálculo das estatísticas: {str(e)}")
    
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
                try:
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
                    else:
                        st.error("❌ Não há dados válidos para o teste")
                except Exception as e:
                    st.error(f"❌ Erro no teste: {str(e)}")
        
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
                        try:
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
                            else:
                                st.error("❌ Dados insuficientes para o teste")
                        except Exception as e:
                            st.error(f"❌ Erro no teste: {str(e)}")
        
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
                    try:
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
                            
                        else:
                            st.error("❌ Necessário pelo menos 2 grupos com dados")
                    except Exception as e:
                        st.error(f"❌ Erro na ANOVA: {str(e)}")
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

# ... (resto das funções permanecem iguais)
