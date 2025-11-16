import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

# Suprimir warnings
warnings.filterwarnings('ignore')

# Imports condicionais para evitar erros
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    st.warning("⚠️ Scipy não disponível. Algumas análises estatísticas estarão limitadas.")

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Import do ProjectManager com tratamento de erro
try:
    from src.utils.project_manager import ProjectManager
except ImportError:
    try:
        from src.core.project_manager import ProjectManager
    except ImportError:
        st.error("❌ Não foi possível importar ProjectManager")
        st.stop()


class AnalyzePhaseManager:
    """Gerenciador principal da fase Analyze com melhor organização e funcionalidades"""
    
    def __init__(self, project_data: Dict):
        self.project_data = project_data
        self.project_id = project_data.get('id')
        self.project_manager = ProjectManager()
    
    def initialize_session_data(self, tool_name: str, default_data: Dict = None) -> Dict:
        """Inicializa dados da sessão para uma ferramenta específica"""
        session_key = f"{tool_name}_{self.project_id}"
        
        if session_key not in st.session_state:
            existing_data = self.project_data.get('analyze', {}).get(tool_name, {}).get('data', {})
            st.session_state[session_key] = existing_data if existing_data else (default_data or {})
        
        return st.session_state[session_key]
    
    def save_tool_data(self, tool_name: str, data: Dict, completed: bool = False) -> bool:
        """Salva dados de uma ferramenta no Firebase"""
        try:
            update_data = {
                f'analyze.{tool_name}.data': data,
                f'analyze.{tool_name}.completed': completed,
                f'analyze.{tool_name}.updated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            success = self.project_manager.update_project(self.project_id, update_data)
            
            if success and 'current_project' in st.session_state:
                # Atualizar session_state local
                if 'analyze' not in st.session_state.current_project:
                    st.session_state.current_project['analyze'] = {}
                if tool_name not in st.session_state.current_project['analyze']:
                    st.session_state.current_project['analyze'][tool_name] = {}
                
                st.session_state.current_project['analyze'][tool_name]['data'] = data
                st.session_state.current_project['analyze'][tool_name]['completed'] = completed
                st.session_state.current_project['analyze'][tool_name]['updated_at'] = datetime.now().isoformat()
            
            return success
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar dados: {str(e)}")
            return False
    
    def get_uploaded_data(self) -> Optional[pd.DataFrame]:
        """Recupera dados carregados na fase Measure"""
        data_key = f'uploaded_data_{self.project_id}'
        return st.session_state.get(data_key)
    
    def is_tool_completed(self, tool_name: str) -> bool:
        """Verifica se uma ferramenta foi concluída"""
        return self.project_data.get('analyze', {}).get(tool_name, {}).get('completed', False)


class StatisticalAnalysis:
    """Classe para análise estatística com funcionalidades robustas"""
    
    def __init__(self, manager: AnalyzePhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
    
    def show(self):
        """Interface principal da análise estatística"""
        st.markdown("## 📊 Análise Estatística")
        st.markdown("Realize análises estatísticas para identificar padrões, tendências e insights nos dados do projeto.")
        
        # Verificar dependências
        if not SCIPY_AVAILABLE:
            st.error("❌ Scipy não está disponível. Instale com: pip install scipy")
            return
        
        # Verificar dados disponíveis
        df = self.manager.get_uploaded_data()
        if df is None:
            self._show_no_data_warning()
            return
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_columns:
            st.error("❌ Nenhuma coluna numérica encontrada nos dados")
            return
        
        # Status da ferramenta
        self._show_status()
        
        # Interface principal com tabs
        self._show_analysis_tabs(df, numeric_columns)
    
    def _show_no_data_warning(self):
        """Mostra aviso quando não há dados disponíveis"""
        st.warning("⚠️ **Dados não encontrados**")
        st.info("Primeiro faça upload dos dados na fase **Measure** para realizar análises estatísticas.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Ir para Measure", key=f"goto_measure_{self.project_id}"):
                st.session_state['navigate_to'] = 'measure'
                st.rerun()
        with col2:
            if st.button("🔄 Recarregar", key=f"reload_data_{self.project_id}"):
                st.rerun()
    
    def _show_status(self):
        """Mostra status da ferramenta"""
        if self.manager.is_tool_completed('statistical_analysis'):
            st.success("✅ **Análise estatística concluída**")
            st.info("💡 Você pode continuar explorando ou modificar as análises abaixo.")
        else:
            st.info("⏳ **Análise em desenvolvimento**")
    
    def _show_analysis_tabs(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Mostra as abas de análise"""
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Estatísticas Descritivas",
            "🔗 Análise de Correlação", 
            "📊 Distribuições",
            "📋 Relatório Completo"
        ])
        
        with tab1:
            self._show_descriptive_statistics(df, numeric_columns)
        
        with tab2:
            self._show_correlation_analysis(df, numeric_columns)
        
        with tab3:
            self._show_distribution_analysis(df, numeric_columns)
        
        with tab4:
            self._show_comprehensive_report(df, numeric_columns)
        
        # Botões de ação
        self._show_action_buttons()
    
    def _show_descriptive_statistics(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Estatísticas descritivas"""
        st.write("### 📊 Estatísticas Descritivas")
        
        # Seleção de colunas
        selected_columns = st.multiselect(
            "Selecione as colunas para análise:",
            numeric_columns,
            default=numeric_columns[:5] if len(numeric_columns) > 5 else numeric_columns,
            key=f"desc_stats_cols_{self.project_id}"
        )
        
        if not selected_columns:
            st.warning("Selecione pelo menos uma coluna.")
            return
        
        # Calcular estatísticas
        stats_df = df[selected_columns].describe()
        
        # Adicionar estatísticas extras
        try:
            extra_stats = pd.DataFrame({
                col: {
                    'variance': df[col].var(),
                    'skewness': df[col].skew() if len(df[col].dropna()) > 0 else 0,
                    'kurtosis': df[col].kurtosis() if len(df[col].dropna()) > 0 else 0,
                    'missing_count': df[col].isnull().sum(),
                    'missing_pct': (df[col].isnull().sum() / len(df)) * 100
                } for col in selected_columns
            }).T
            
            # Combinar estatísticas
            full_stats = pd.concat([stats_df.T, extra_stats], axis=1)
            
            # Mostrar tabela
            st.dataframe(
                full_stats.round(4),
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Erro ao calcular estatísticas extras: {str(e)}")
            st.dataframe(stats_df, use_container_width=True)
        
        # Visualizações
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                # Box plot
                fig_box = px.box(
                    df[selected_columns], 
                    title="Distribuição das Variáveis (Box Plot)"
                )
                fig_box.update_layout(height=400)
                st.plotly_chart(fig_box, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao criar box plot: {str(e)}")
        
        with col2:
            try:
                # Histograma para primeira coluna selecionada
                if selected_columns:
                    fig_hist = px.histogram(
                        df, 
                        x=selected_columns[0], 
                        title=f"Histograma - {selected_columns[0]}"
                    )
                    fig_hist.update_layout(height=400)
                    st.plotly_chart(fig_hist, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao criar histograma: {str(e)}")
    
    def _show_correlation_analysis(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Análise de correlação sem dependências externas"""
        st.write("### 🔗 Análise de Correlação")
        
        if len(numeric_columns) < 2:
            st.warning("⚠️ Necessário pelo menos 2 variáveis numéricas para análise de correlação")
            return
        
        # Seleção de colunas
        selected_columns = st.multiselect(
            "Selecione as colunas para análise de correlação:",
            numeric_columns,
            default=numeric_columns[:10] if len(numeric_columns) > 10 else numeric_columns,
            key=f"corr_cols_{self.project_id}"
        )
        
        if len(selected_columns) < 2:
            st.warning("Selecione pelo menos 2 colunas.")
            return
        
        try:
            # Calcular matriz de correlação
            corr_matrix = df[selected_columns].corr()
            
            # Heatmap de correlação
            fig_heatmap = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                title="Matriz de Correlação",
                color_continuous_scale="RdBu",
                range_color=[-1, 1]
            )
            fig_heatmap.update_layout(height=500)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Correlações mais fortes
            self._show_significant_correlations(corr_matrix, selected_columns)
            
            # Análise detalhada de pares específicos
            self._show_detailed_correlation_analysis(df, selected_columns)
            
        except Exception as e:
            st.error(f"Erro na análise de correlação: {str(e)}")
    
    def _show_significant_correlations(self, corr_matrix: pd.DataFrame, numeric_columns: List[str]):
        """Mostra correlações mais significativas"""
        st.write("#### 🎯 Correlações Mais Significativas")
        
        # Encontrar correlações fortes
        correlations = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                
                if not pd.isna(corr_value):
                    abs_corr = abs(corr_value)
                    
                    if abs_corr > 0.3:  # Correlações moderadas ou fortes
                        strength = self._classify_correlation_strength(abs_corr)
                        direction = "Positiva" if corr_value > 0 else "Negativa"
                        
                        correlations.append({
                            'Variável 1': corr_matrix.columns[i],
                            'Variável 2': corr_matrix.columns[j],
                            'Correlação': corr_value,
                            'Força': strength,
                            'Direção': direction
                        })
        
        if correlations:
            df_corr = pd.DataFrame(correlations)
            df_corr = df_corr.reindex(
                df_corr['Correlação'].abs().sort_values(ascending=False).index
            )
            
            st.dataframe(df_corr.round(4), use_container_width=True)
            
            # Insights automáticos
            if len(df_corr) > 0:
                strongest = df_corr.iloc[0]
                st.info(f"🔗 **Correlação mais forte:** {strongest['Variável 1']} e {strongest['Variável 2']} "
                       f"({strongest['Correlação']:.3f} - {strongest['Força']} {strongest['Direção']})")
        else:
            st.info("📊 Nenhuma correlação significativa encontrada (|r| > 0.3)")
    
    def _classify_correlation_strength(self, abs_corr: float) -> str:
        """Classifica a força da correlação"""
        if abs_corr >= 0.8:
            return "Muito Forte"
        elif abs_corr >= 0.6:
            return "Forte"
        elif abs_corr >= 0.4:
            return "Moderada"
        elif abs_corr >= 0.2:
            return "Fraca"
        else:
            return "Muito Fraca"
    
    def _show_detailed_correlation_analysis(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Análise detalhada de correlações específicas"""
        st.write("#### 🔍 Análise Detalhada de Correlações")
        
        col1, col2 = st.columns(2)
        
        with col1:
            x_var = st.selectbox("Variável X:", numeric_columns, key=f"corr_x_{self.project_id}")
        
        with col2:
            y_options = [col for col in numeric_columns if col != x_var]
            if y_options:
                y_var = st.selectbox("Variável Y:", y_options, key=f"corr_y_{self.project_id}")
                
                # Análise da correlação específica
                self._analyze_specific_correlation(df, x_var, y_var)
    
    def _analyze_specific_correlation(self, df: pd.DataFrame, x_var: str, y_var: str):
        """Analisa correlação específica entre duas variáveis sem trendline"""
        # Dados limpos
        clean_data = df[[x_var, y_var]].dropna()
        
        if len(clean_data) == 0:
            st.warning("⚠️ Nenhum par de dados válido encontrado")
            return
        
        x_data = clean_data[x_var]
        y_data = clean_data[y_var]
        
        try:
            # Scatter plot simples (sem trendline para evitar dependências)
            fig = px.scatter(
                clean_data, 
                x=x_var, 
                y=y_var,
                title=f"Correlação: {x_var} vs {y_var}"
            )
            
            # Adicionar linha de tendência manual usando numpy
            try:
                x_vals = x_data.values
                y_vals = y_data.values
                
                # Coeficientes da regressão linear
                slope, intercept = np.polyfit(x_vals, y_vals, 1)
                
                # Criar linha de tendência
                x_trend = np.linspace(x_vals.min(), x_vals.max(), 100)
                y_trend = slope * x_trend + intercept
                
                # Adicionar linha ao gráfico
                fig.add_trace(
                    go.Scatter(
                        x=x_trend,
                        y=y_trend,
                        mode='lines',
                        name='Linha de Tendência',
                        line=dict(color='red', width=2)
                    )
                )
            except Exception:
                pass  # Continuar sem linha de tendência se houver erro
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas da correlação
            try:
                correlation = x_data.corr(y_data)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Correlação de Pearson", f"{correlation:.4f}")
                
                with col2:
                    # R²
                    r_squared = correlation ** 2
                    st.metric("R² (Coef. Determinação)", f"{r_squared:.4f}")
                
                with col3:
                    # Força da correlação
                    strength = self._classify_correlation_strength(abs(correlation))
                    if abs(correlation) > 0.7:
                        st.success(f"🔗 {strength}")
                    elif abs(correlation) > 0.3:
                        st.warning(f"🔗 {strength}")
                    else:
                        st.info(f"🔗 {strength}")
                
                # Interpretação
                st.write("**📝 Interpretação:**")
                interpretation = self._interpret_correlation(correlation)
                st.info(interpretation)
                
            except Exception as e:
                st.error(f"Erro no cálculo da correlação: {str(e)}")
                
        except Exception as e:
            st.error(f"Erro na análise de correlação: {str(e)}")
    
    def _interpret_correlation(self, correlation: float) -> str:
        """Interpreta o valor da correlação"""
        abs_corr = abs(correlation)
        direction = "positiva" if correlation > 0 else "negativa"
        strength = self._classify_correlation_strength(abs_corr)
        
        interpretation = f"Correlação {direction} de força {strength.lower()} ({correlation:.4f}). "
        
        if abs_corr >= 0.7:
            interpretation += "Existe uma relação linear forte entre as variáveis."
        elif abs_corr >= 0.3:
            interpretation += "Existe uma relação linear moderada entre as variáveis."
        else:
            interpretation += "A relação linear entre as variáveis é fraca."
        
        return interpretation
    
    def _show_distribution_analysis(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Análise de distribuições"""
        st.write("### 📊 Análise de Distribuições")
        
        # Seleção de variável
        selected_var = st.selectbox(
            "Selecione a variável para análise:",
            numeric_columns,
            key=f"dist_var_{self.project_id}"
        )
        
        if not selected_var:
            return
        
        data = df[selected_var].dropna()
        
        if len(data) == 0:
            st.warning("Nenhum dado válido encontrado para a variável selecionada.")
            return
        
        try:
            # Layout em colunas
            col1, col2 = st.columns(2)
            
            with col1:
                # Histograma com curva normal
                fig_hist = px.histogram(
                    x=data,
                    nbins=30,
                    title=f"Distribuição de {selected_var}",
                    marginal="box"
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Q-Q Plot (se scipy disponível)
                if SCIPY_AVAILABLE:
                    try:
                        fig_qq = go.Figure()
                        
                        # Calcular Q-Q plot
                        from scipy.stats import probplot
                        (osm, osr), (slope, intercept, r) = probplot(data, dist="norm", plot=None)
                        
                        # Pontos observados
                        fig_qq.add_trace(go.Scatter(
                            x=osm, 
                            y=osr,
                            mode='markers',
                            name='Dados Observados',
                            marker=dict(color='blue', size=6)
                        ))
                        
                        # Linha teórica
                        fig_qq.add_trace(go.Scatter(
                            x=osm,
                            y=slope * osm + intercept,
                            mode='lines',
                            name='Linha Teórica (Normal)',
                            line=dict(color='red', width=2)
                        ))
                        
                        fig_qq.update_layout(
                            title=f"Q-Q Plot - {selected_var}",
                            xaxis_title="Quantis Teóricos",
                            yaxis_title="Quantis Observados",
                            height=400
                        )
                        
                        st.plotly_chart(fig_qq, use_container_width=True)
                        
                    except Exception as e:
                        st.warning(f"Erro ao gerar Q-Q plot: {str(e)}")
                        # Box plot alternativo
                        fig_box = px.box(y=data, title=f"Box Plot - {selected_var}")
                        fig_box.update_layout(height=400)
                        st.plotly_chart(fig_box, use_container_width=True)
                else:
                    # Box plot se scipy não estiver disponível
                    fig_box = px.box(y=data, title=f"Box Plot - {selected_var}")
                    fig_box.update_layout(height=400)
                    st.plotly_chart(fig_box, use_container_width=True)
            
            # Estatísticas da distribuição
            self._show_distribution_stats(data, selected_var)
            
        except Exception as e:
            st.error(f"Erro na análise de distribuição: {str(e)}")
    
    def _show_distribution_stats(self, data: pd.Series, var_name: str):
        """Mostra estatísticas da distribuição"""
        st.write("#### 📈 Estatísticas da Distribuição")
        
        try:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                skewness = data.skew()
                st.metric("Assimetria (Skewness)", f"{skewness:.4f}")
            
            with col2:
                kurtosis = data.kurtosis()
                st.metric("Curtose (Kurtosis)", f"{kurtosis:.4f}")
            
            with col3:
                cv = (data.std() / data.mean() * 100) if data.mean() != 0 else 0
                st.metric("Coef. Variação", f"{cv:.2f}%")
            
            with col4:
                amplitude = data.max() - data.min()
                st.metric("Amplitude", f"{amplitude:.4f}")
            
            # Testes de normalidade (se scipy disponível)
            if SCIPY_AVAILABLE:
                self._show_normality_tests(data, var_name)
        
        except Exception as e:
            st.error(f"Erro ao calcular estatísticas: {str(e)}")
    
    def _show_normality_tests(self, data: pd.Series, var_name: str):
        """Testes estatísticos de normalidade"""
        st.write("#### 🧪 Testes de Normalidade")
        
        try:
            tests_results = []
            
            # Shapiro-Wilk (para n < 5000)
            if len(data) < 5000:
                try:
                    shapiro_stat, shapiro_p = stats.shapiro(data)
                    tests_results.append({
                        'Teste': 'Shapiro-Wilk',
                        'Estatística': f"{shapiro_stat:.6f}",
                        'p-valor': f"{shapiro_p:.6f}",
                        'Resultado': 'Normal' if shapiro_p > 0.05 else 'Não Normal'
                    })
                except Exception:
                    pass
            
            # Kolmogorov-Smirnov
            try:
                ks_stat, ks_p = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
                tests_results.append({
                    'Teste': 'Kolmogorov-Smirnov',
                    'Estatística': f"{ks_stat:.6f}",
                    'p-valor': f"{ks_p:.6f}",
                    'Resultado': 'Normal' if ks_p > 0.05 else 'Não Normal'
                })
            except Exception:
                pass
            
            # Mostrar resultados
            if tests_results:
                df_tests = pd.DataFrame(tests_results)
                st.dataframe(df_tests, use_container_width=True)
                
                # Resumo dos resultados
                normal_count = sum(1 for result in tests_results if result['Resultado'] == 'Normal')
                total_tests = len(tests_results)
                
                if normal_count == total_tests:
                    st.success(f"✅ Todos os {total_tests} testes indicam normalidade")
                elif normal_count > total_tests / 2:
                    st.warning(f"⚠️ {normal_count}/{total_tests} testes indicam normalidade")
                else:
                    st.error(f"❌ Apenas {normal_count}/{total_tests} testes indicam normalidade")
            else:
                st.info("Não foi possível executar testes de normalidade")
        
        except Exception as e:
            st.error(f"Erro nos testes de normalidade: {str(e)}")
    
    def _show_comprehensive_report(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Relatório abrangente da análise"""
        st.write("### 📋 Relatório Completo da Análise Estatística")
        
        # Resumo geral dos dados
        st.write("#### 📊 Resumo Geral dos Dados")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Registros", len(df))
        
        with col2:
            st.metric("Colunas Numéricas", len(numeric_columns))
        
        with col3:
            total_missing = df[numeric_columns].isnull().sum().sum()
            st.metric("Valores Ausentes", total_missing)
        
        with col4:
            missing_pct = (total_missing / (len(df) * len(numeric_columns))) * 100
            st.metric("% Valores Ausentes", f"{missing_pct:.2f}%")
        
        # Estatísticas por variável
        st.write("#### 📈 Estatísticas Detalhadas por Variável")
        
        try:
            detailed_stats = []
            for col in numeric_columns[:10]:  # Limitar a 10 colunas
                data = df[col].dropna()
                
                if len(data) > 0:
                    stats_dict = {
                        'Variável': col,
                        'Contagem': len(data),
                        'Média': data.mean(),
                        'Mediana': data.median(),
                        'Desvio Padrão': data.std(),
                        'Mínimo': data.min(),
                        'Máximo': data.max(),
                        'Coef. Variação (%)': (data.std() / data.mean()) * 100 if data.mean() != 0 else np.nan
                    }
                    detailed_stats.append(stats_dict)
            
            if detailed_stats:
                detailed_df = pd.DataFrame(detailed_stats)
                st.dataframe(detailed_df.round(4), use_container_width=True)
        
        except Exception as e:
            st.error(f"Erro ao gerar estatísticas detalhadas: {str(e)}")
        
        # Recomendações
        st.write("#### 💡 Recomendações e Insights")
        recommendations = self._generate_recommendations(df, numeric_columns)
        
        for rec in recommendations:
            st.info(f"🔍 {rec}")
    
    def _generate_recommendations(self, df: pd.DataFrame, numeric_columns: List[str]) -> List[str]:
        """Gera recomendações baseadas na análise"""
        recommendations = []
        
        try:
            # Verificar valores ausentes
            missing_data = df[numeric_columns].isnull().sum()
            high_missing = missing_data[missing_data > len(df) * 0.1]  # Mais de 10%
            
            if not high_missing.empty:
                recommendations.append(
                    f"Variáveis com muitos valores ausentes detectadas: {', '.join(high_missing.index)}. "
                    "Considere estratégias de imputação ou remoção."
                )
            
            # Verificar variabilidade
            for col in numeric_columns[:3]:  # Verificar apenas primeiras 3 colunas
                data = df[col].dropna()
                if len(data) > 0:
                    cv = (data.std() / data.mean()) * 100 if data.mean() != 0 else 0
                    
                    if cv > 50:
                        recommendations.append(
                            f"Alta variabilidade em '{col}' (CV: {cv:.1f}%). "
                            "Investigue possíveis causas especiais."
                        )
            
            # Verificar correlações altas
            if len(numeric_columns) >= 2:
                try:
                    corr_matrix = df[numeric_columns[:5]].corr()  # Limitar a 5 colunas
                    high_corr_pairs = []
                    
                    for i in range(len(corr_matrix.columns)):
                        for j in range(i+1, len(corr_matrix.columns)):
                            corr_value = corr_matrix.iloc[i, j]
                            if not pd.isna(corr_value) and abs(corr_value) > 0.8:
                                high_corr_pairs.append(
                                    f"{corr_matrix.columns[i]} e {corr_matrix.columns[j]} ({corr_value:.3f})"
                                )
                    
                    if high_corr_pairs:
                        recommendations.append(
                            f"Correlações muito altas detectadas: {', '.join(high_corr_pairs)}. "
                            "Considere possível multicolinearidade."
                        )
                except Exception:
                    pass
            
            if not recommendations:
                recommendations.append(
                    "Os dados apresentam características estatísticas adequadas para análise. "
                    "Prossiga com as análises específicas do projeto."
                )
        
        except Exception as e:
            recommendations.append(f"Erro ao gerar recomendações: {str(e)}")
        
        return recommendations
    
    def _show_action_buttons(self):
        """Botões de ação para salvar e finalizar"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Análise", key=f"save_stat_analysis_{self.project_id}"):
                # Coletar dados da análise realizada
                analysis_data = {
                    'analysis_date': datetime.now().isoformat(),
                    'data_summary': {
                        'total_observations': len(self.manager.get_uploaded_data()) if self.manager.get_uploaded_data() is not None else 0,
                        'numeric_variables': len(self.manager.get_uploaded_data().select_dtypes(include=[np.number]).columns) if self.manager.get_uploaded_data() is not None else 0
                    },
                    'analysis_completed': True
                }
                
                success = self.manager.save_tool_data('statistical_analysis', analysis_data, False)
                if success:
                    st.success("💾 Análise estatística salva com sucesso!")
                else:
                    st.error("❌ Erro ao salvar análise")
        
        with col2:
            if st.button("✅ Finalizar Análise Estatística", key=f"complete_stat_analysis_{self.project_id}"):
                df = self.manager.get_uploaded_data()
                if df is not None:
                    analysis_data = {
                        'analysis_date': datetime.now().isoformat(),
                        'data_summary': {
                            'total_observations': len(df),
                            'numeric_variables': len(df.select_dtypes(include=[np.number]).columns),
                            'categorical_variables': len(df.select_dtypes(include=['object']).columns),
                            'missing_data_count': df.isnull().sum().sum()
                        },
                        'analysis_completed': True
                    }
                    
                    success = self.manager.save_tool_data('statistical_analysis', analysis_data, True)
                    if success:
                        st.success("✅ Análise estatística finalizada com sucesso!")
                        st.balloons()
                    else:
                        st.error("❌ Erro ao finalizar análise")
                else:
                    st.error("❌ Dados não encontrados. Carregue os dados primeiro.")


class SimpleRootCauseAnalysis:
    """Versão simplificada da análise de causa raiz"""
    
    def __init__(self, manager: AnalyzePhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.data = manager.initialize_session_data('root_cause_analysis', {
            'problem_statement': '',
            'why_analysis': [],
            'root_cause_final': ''
        })
    
    def show(self):
        """Interface principal da análise de causa raiz"""
        st.markdown("## 🔍 Análise de Causa Raiz")
        st.markdown("Identifique as causas raiz dos problemas usando a técnica dos 5 Porquês.")
        
        # Status da ferramenta
        self._show_status()
        
        # Definição do problema
        self._show_problem_definition()
        
        # 5 Porquês
        if self.data.get('problem_statement', '').strip():
            self._show_five_whys()
        
        # Botões de ação
        self._show_action_buttons()
    
    def _show_status(self):
        """Mostra status da ferramenta"""
        if self.manager.is_tool_completed('root_cause_analysis'):
            st.success("✅ **Análise de causa raiz concluída**")
        else:
            st.info("⏳ **Análise em desenvolvimento**")
    
    def _show_problem_definition(self):
        """Definição clara do problema"""
        st.markdown("### 📝 Definição do Problema")
        
        problem_statement = st.text_area(
            "**Declaração do Problema**",
            value=self.data.get('problem_statement', ''),
            placeholder="Descreva o problema de forma clara, específica e mensurável. "
                       "Inclua: O que está acontecendo? Onde? Quando? Com que frequência?",
            height=120,
            key=f"problem_statement_{self.project_id}",
            help="Seja específico: use dados quantitativos quando possível"
        )
        
        self.data['problem_statement'] = problem_statement
    
    def _show_five_whys(self):
        """Análise dos 5 Porquês"""
        st.markdown("### 🤔 Análise dos 5 Porquês")
        
        # Mostrar o problema definido
        st.info(f"**Problema:** {self.data['problem_statement']}")
        
        # Inicializar lista de porquês se não existir
        if 'why_analysis' not in self.data:
            self.data['why_analysis'] = []
        
        # Interface para os 5 porquês
        st.markdown("#### 🔍 Sequência de Análise")
        
        # Mostrar porquês existentes
        for i, why_item in enumerate(self.data['why_analysis']):
            self._show_why_item(i, why_item)
        
        # Botão para adicionar novo porquê
        if len(self.data['why_analysis']) < 5:
            col_add1, col_add2 = st.columns([3, 1])
            
            with col_add1:
                st.markdown(f"**Por que {len(self.data['why_analysis']) + 1}?**")
            
            with col_add2:
                if st.button(f"➕ Adicionar Por que {len(self.data['why_analysis']) + 1}", 
                            key=f"add_why_{self.project_id}"):
                    self.data['why_analysis'].append({
                        'question': f"Por que {len(self.data['why_analysis']) + 1}?",
                        'answer': ''
                    })
                    st.rerun()
        
        # Causa raiz final
        if len(self.data['why_analysis']) > 0:
            self._show_root_cause_summary()
    
    def _show_why_item(self, index: int, why_item: Dict):
        """Mostra um item da análise dos porquês"""
        with st.container():
            st.markdown(f"**Por que {index + 1}:**")
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Resposta
                answer = st.text_area(
                    f"Resposta {index + 1}:",
                    value=why_item.get('answer', ''),
                    placeholder="Descreva a causa identificada...",
                    height=80,
                    key=f"why_answer_{index}_{self.project_id}"
                )
                
                # Atualizar dados
                self.data['why_analysis'][index]['answer'] = answer
            
            with col2:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"remove_why_{index}_{self.project_id}"):
                    self.data['why_analysis'].pop(index)
                    st.rerun()
            
            st.divider()
    
    def _show_root_cause_summary(self):
        """Resumo da análise de causa raiz"""
        st.markdown("#### 🎯 Causa Raiz Identificada")
        
        # Campo para causa raiz final
        root_cause = st.text_area(
            "**Declaração Final da Causa Raiz**",
            value=self.data.get('root_cause_final', ''),
            placeholder="Com base na análise dos porquês, qual é a causa raiz principal?",
            height=100,
            key=f"root_cause_final_{self.project_id}"
        )
        
        self.data['root_cause_final'] = root_cause
    
    def _show_action_buttons(self):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Análise", key=f"save_rca_{self.project_id}"):
                success = self.manager.save_tool_data('root_cause_analysis', self.data, False)
                if success:
                    st.success("💾 Análise de causa raiz salva com sucesso!")
                else:
                    st.error("❌ Erro ao salvar análise")
        
        with col2:
            if st.button("✅ Finalizar Análise de Causa Raiz", key=f"complete_rca_{self.project_id}"):
                # Validação básica
                problem_defined = bool(self.data.get('problem_statement', '').strip())
                has_analysis = len(self.data.get('why_analysis', [])) > 0
                
                if problem_defined and has_analysis:
                    success = self.manager.save_tool_data('root_cause_analysis', self.data, True)
                    if success:
                        st.success("✅ Análise de causa raiz finalizada com sucesso!")
                        st.balloons()
                    else:
                        st.error("❌ Erro ao finalizar análise")
                else:
                    missing = []
                    if not problem_defined:
                        missing.append("definição do problema")
                    if not has_analysis:
                        missing.append("análise dos porquês")
                    
                    st.error(f"❌ Complete: {', '.join(missing)}")


# Função principal para mostrar a fase Analyze
def show_analyze_tools(project_data: Dict):
    """Função principal para mostrar as ferramentas da fase Analyze"""
    
    if not project_data:
        st.error("❌ Projeto não encontrado")
        return
    
    # Inicializar gerenciador
    manager = AnalyzePhaseManager(project_data)
    
    # Menu de ferramentas
    st.markdown("### 🔧 Ferramentas da Fase Analyze")
    st.markdown("Analise os dados coletados para identificar as causas raiz dos problemas.")
    
    # Opções de ferramentas (versão simplificada)
    tool_options = {
        "statistical_analysis": ("📊", "Análise Estatística"),
        "root_cause_analysis": ("🔍", "Análise de Causa Raiz")
    }
    
    # Verificar status das ferramentas
    analyze_data = project_data.get('analyze', {})
    
    # Criar lista de ferramentas com status
    tool_names_with_status = []
    tool_keys = list(tool_options.keys())
    
    for key, (icon, name) in tool_options.items():
        is_completed = manager.is_tool_completed(key)
        status_icon = "✅" if is_completed else "⏳"
        tool_names_with_status.append(f"{status_icon} {icon} {name}")
    
    # Seletor de ferramenta
    selected_index = st.selectbox(
        "Selecione uma ferramenta para usar:",
        range(len(tool_names_with_status)),
        format_func=lambda x: tool_names_with_status[x],
        key=f"analyze_tool_selector_{manager.project_id}",
        help="Escolha a ferramenta que deseja usar para análise"
    )
    
    selected_tool = tool_keys[selected_index]
    
    st.divider()
    
    # Mostrar ferramenta selecionada
    if selected_tool == "statistical_analysis":
        statistical_analysis = StatisticalAnalysis(manager)
        statistical_analysis.show()
    
    elif selected_tool == "root_cause_analysis":
        root_cause_analysis = SimpleRootCauseAnalysis(manager)
        root_cause_analysis.show()
    
    # Progresso geral da fase Analyze
    st.divider()
    _show_analyze_progress(manager, tool_options, analyze_data)


def _show_analyze_progress(manager: AnalyzePhaseManager, tool_options: Dict, analyze_data: Dict):
    """Mostra progresso geral da fase Analyze"""
    st.markdown("### 📊 Progresso da Fase Analyze")
    
    total_tools = len(tool_options)
    completed_tools = sum(1 for key in tool_options.keys() if manager.is_tool_completed(key))
    
    # Barra de progresso
    progress = (completed_tools / total_tools) * 100
    
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
