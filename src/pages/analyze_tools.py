import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from src.utils.project_manager import ProjectManager
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


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
    """Classe para análise estatística com funcionalidades avançadas"""
    
    def __init__(self, manager: AnalyzePhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
    
    def show(self):
        """Interface principal da análise estatística"""
        st.markdown("## 📊 Análise Estatística")
        st.markdown("Realize análises estatísticas avançadas para identificar padrões, tendências e insights nos dados do projeto.")
        
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
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Análise Exploratória", 
            "🔗 Correlações", 
            "📊 Distribuições", 
            "🧪 Testes Estatísticos",
            "📋 Relatório"
        ])
        
        with tab1:
            self._show_exploratory_analysis(df, numeric_columns)
        
        with tab2:
            self._show_correlation_analysis(df, numeric_columns)
        
        with tab3:
            self._show_distribution_analysis(df, numeric_columns)
        
        with tab4:
            self._show_statistical_tests(df, numeric_columns)
        
        with tab5:
            self._show_analysis_report(df, numeric_columns)
        
        # Botões de ação
        self._show_action_buttons()
    
    def _show_exploratory_analysis(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Análise exploratória dos dados"""
        st.markdown("### 📈 Análise Exploratória de Dados")
        
        # Seleção de variável
        selected_var = st.selectbox(
            "Selecione a variável para análise:",
            numeric_columns,
            key=f"eda_var_{self.project_id}"
        )
        
        if selected_var:
            data_series = df[selected_var].dropna()
            
            if len(data_series) == 0:
                st.warning("⚠️ Nenhum dado válido encontrado para esta variável")
                return
            
            # Layout com métricas e gráficos
            col1, col2 = st.columns([1, 2])
            
            with col1:
                self._show_descriptive_stats(data_series, selected_var)
            
            with col2:
                self._show_trend_analysis(data_series, selected_var)
            
            # Análise de outliers
            self._show_outlier_analysis(data_series, selected_var)
    
    def _show_descriptive_stats(self, data: pd.Series, var_name: str):
        """Mostra estatísticas descritivas"""
        st.markdown("#### 📊 Estatísticas Descritivas")
        
        try:
            stats_data = {
                'Média': data.mean(),
                'Mediana': data.median(),
                'Moda': data.mode().iloc[0] if not data.mode().empty else 'N/A',
                'Desvio Padrão': data.std(),
                'Variância': data.var(),
                'Mínimo': data.min(),
                'Máximo': data.max(),
                'Amplitude': data.max() - data.min(),
                'Q1 (25%)': data.quantile(0.25),
                'Q3 (75%)': data.quantile(0.75),
                'IQR': data.quantile(0.75) - data.quantile(0.25),
                'Assimetria': stats.skew(data),
                'Curtose': stats.kurtosis(data),
                'Coef. Variação': (data.std() / data.mean() * 100) if data.mean() != 0 else 0
            }
            
            # Mostrar métricas principais
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric("Média", f"{stats_data['Média']:.3f}")
                st.metric("Mediana", f"{stats_data['Mediana']:.3f}")
                st.metric("Desvio Padrão", f"{stats_data['Desvio Padrão']:.3f}")
                st.metric("Mínimo", f"{stats_data['Mínimo']:.3f}")
            
            with col_b:
                st.metric("Máximo", f"{stats_data['Máximo']:.3f}")
                st.metric("Amplitude", f"{stats_data['Amplitude']:.3f}")
                st.metric("Coef. Variação", f"{stats_data['Coef. Variação']:.1f}%")
                st.metric("Assimetria", f"{stats_data['Assimetria']:.3f}")
            
            # Interpretações
            st.markdown("**💡 Interpretações:**")
            
            # Assimetria
            skew_val = stats_data['Assimetria']
            if abs(skew_val) < 0.5:
                st.info("📊 Distribuição aproximadamente simétrica")
            elif skew_val > 0.5:
                st.warning("📊 Distribuição assimétrica à direita (cauda longa à direita)")
            else:
                st.warning("📊 Distribuição assimétrica à esquerda (cauda longa à esquerda)")
            
            # Variabilidade
            cv = stats_data['Coef. Variação']
            if cv < 15:
                st.success("📊 Baixa variabilidade (CV < 15%)")
            elif cv < 30:
                st.info("📊 Variabilidade moderada (15% ≤ CV < 30%)")
            else:
                st.error("📊 Alta variabilidade (CV ≥ 30%)")
                
        except Exception as e:
            st.error(f"❌ Erro no cálculo das estatísticas: {str(e)}")
    
    def _show_trend_analysis(self, data: pd.Series, var_name: str):
        """Análise de tendências temporais"""
        st.markdown("#### 📈 Análise de Tendências")
        
        # Gráfico de série temporal
        fig = go.Figure()
        
        # Dados originais
        fig.add_trace(go.Scatter(
            x=list(range(len(data))),
            y=data.values,
            mode='lines+markers',
            name='Dados',
            line=dict(color='blue', width=1),
            marker=dict(size=4)
        ))
        
        # Linha de tendência
        x_vals = np.array(range(len(data)))
        z = np.polyfit(x_vals, data.values, 1)
        p = np.poly1d(z)
        
        fig.add_trace(go.Scatter(
            x=list(range(len(data))),
            y=p(x_vals),
            mode='lines',
            name='Tendência',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        # Média móvel (se houver dados suficientes)
        if len(data) >= 7:
            window = min(7, len(data) // 3)
            moving_avg = data.rolling(window=window, center=True).mean()
            
            fig.add_trace(go.Scatter(
                x=list(range(len(data))),
                y=moving_avg.values,
                mode='lines',
                name=f'Média Móvel ({window})',
                line=dict(color='green', width=2)
            ))
        
        fig.update_layout(
            title=f"Análise Temporal - {var_name}",
            xaxis_title="Observação",
            yaxis_title=var_name,
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas de tendência
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            slope = z[0]
            st.metric("Inclinação", f"{slope:.6f}")
        
        with col_b:
            # Teste de Mann-Kendall para tendência
            try:
                from scipy.stats import kendalltau
                tau, p_value = kendalltau(range(len(data)), data)
                st.metric("Kendall Tau", f"{tau:.4f}")
                
                if p_value < 0.05:
                    trend_text = "Tendência significativa" if abs(tau) > 0.1 else "Tendência fraca"
                    st.info(f"📊 {trend_text}")
                else:
                    st.info("📊 Sem tendência significativa")
            except:
                st.metric("Kendall Tau", "N/A")
        
        with col_c:
            # Autocorrelação lag-1
            if len(data) > 1:
                autocorr = data.autocorr(lag=1)
                st.metric("Autocorrelação", f"{autocorr:.4f}" if not pd.isna(autocorr) else "N/A")
    
    def _show_outlier_analysis(self, data: pd.Series, var_name: str):
        """Análise de outliers"""
        st.markdown("#### 🎯 Análise de Outliers")
        
        # Calcular outliers usando IQR
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = data[(data < lower_bound) | (data > upper_bound)]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Box plot
            fig_box = px.box(y=data, title=f"Box Plot - {var_name}")
            fig_box.update_layout(height=300)
            st.plotly_chart(fig_box, use_container_width=True)
        
        with col2:
            # Informações sobre outliers
            st.markdown("**🔍 Detecção de Outliers (Método IQR):**")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric("Total de Outliers", len(outliers))
                st.metric("% de Outliers", f"{len(outliers)/len(data)*100:.1f}%")
            
            with col_b:
                st.metric("Limite Inferior", f"{lower_bound:.3f}")
                st.metric("Limite Superior", f"{upper_bound:.3f}")
            
            if len(outliers) > 0:
                st.markdown("**⚠️ Valores Outliers Identificados:**")
                outlier_df = pd.DataFrame({
                    'Posição': outliers.index,
                    'Valor': outliers.values
                })
                st.dataframe(outlier_df.head(10), use_container_width=True)
                
                if len(outliers) > 10:
                    st.info(f"... e mais {len(outliers) - 10} outliers")
            else:
                st.success("✅ Nenhum outlier detectado pelo método IQR")
    
    def _show_correlation_analysis(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Análise de correlações"""
        st.markdown("### 🔗 Análise de Correlações")
        
        if len(numeric_columns) < 2:
            st.warning("⚠️ Necessário pelo menos 2 variáveis numéricas para análise de correlação")
            return
        
        # Matriz de correlação
        corr_matrix = df[numeric_columns].corr()
        
        # Heatmap da matriz de correlação
        fig = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            title="Matriz de Correlação",
            color_continuous_scale='RdBu_r',
            zmin=-1,
            zmax=1
        )
        
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Análise de correlações significativas
        self._show_significant_correlations(corr_matrix, numeric_columns)
        
        # Análise detalhada de pares específicos
        self._show_detailed_correlation_analysis(df, numeric_columns)
    
    def _show_significant_correlations(self, corr_matrix: pd.DataFrame, numeric_columns: List[str]):
        """Mostra correlações mais significativas"""
        st.markdown("#### 🎯 Correlações Mais Significativas")
        
        # Encontrar correlações fortes
        strong_correlations = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                
                if not pd.isna(corr_value):
                    abs_corr = abs(corr_value)
                    
                    if abs_corr > 0.3:  # Correlações moderadas ou fortes
                        strength = "Muito Forte" if abs_corr > 0.8 else "Forte" if abs_corr > 0.6 else "Moderada"
                        direction = "Positiva" if corr_value > 0 else "Negativa"
                        
                        strong_correlations.append({
                            'Variável 1': corr_matrix.columns[i],
                            'Variável 2': corr_matrix.columns[j],
                            'Correlação': corr_value,
                            'Força': strength,
                            'Direção': direction,
                            'Abs. Correlação': abs_corr
                        })
        
        if strong_correlations:
            df_corr = pd.DataFrame(strong_correlations)
            df_corr = df_corr.sort_values('Abs. Correlação', ascending=False)
            
            # Remover coluna auxiliar
            df_corr = df_corr.drop('Abs. Correlação', axis=1)
            
            st.dataframe(df_corr, use_container_width=True)
            
            # Insights automáticos
            st.markdown("**💡 Insights Automáticos:**")
            
            strongest = df_corr.iloc[0]
            st.info(f"🔗 **Correlação mais forte:** {strongest['Variável 1']} e {strongest['Variável 2']} "
                   f"({strongest['Correlação']:.3f} - {strongest['Força']} {strongest['Direção']})")
            
            positive_corrs = df_corr[df_corr['Direção'] == 'Positiva']
            negative_corrs = df_corr[df_corr['Direção'] == 'Negativa']
            
            if len(positive_corrs) > 0:
                st.success(f"📈 {len(positive_corrs)} correlação(ões) positiva(s) identificada(s)")
            
            if len(negative_corrs) > 0:
                st.warning(f"📉 {len(negative_corrs)} correlação(ões) negativa(s) identificada(s)")
        else:
            st.info("📊 Nenhuma correlação significativa encontrada (|r| > 0.3)")
    
    def _show_detailed_correlation_analysis(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Análise detalhada de correlações específicas"""
        st.markdown("#### 🔍 Análise Detalhada de Correlações")
        
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
        """Analisa correlação específica entre duas variáveis"""
        # Dados limpos
        clean_data = df[[x_var, y_var]].dropna()
        
        if len(clean_data) == 0:
            st.warning("⚠️ Nenhum par de dados válido encontrado")
            return
        
        x_data = clean_data[x_var]
        y_data = clean_data[y_var]
        
        # Scatter plot com linha de tendência
        fig = px.scatter(
            clean_data, 
            x=x_var, 
            y=y_var,
            trendline="ols",
            title=f"Correlação: {x_var} vs {y_var}"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas da correlação
        try:
            # Correlação de Pearson
            pearson_r, pearson_p = stats.pearsonr(x_data, y_data)
            
            # Correlação de Spearman (não-paramétrica)
            spearman_r, spearman_p = stats.spearmanr(x_data, y_data)
            
            # Coeficiente de determinação
            r_squared = pearson_r ** 2
            
            # Mostrar estatísticas
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                st.metric("Pearson (r)", f"{pearson_r:.4f}")
                if pearson_p < 0.05:
                    st.success("Significativo")
                else:
                    st.info("Não significativo")
            
            with col_b:
                st.metric("Spearman (ρ)", f"{spearman_r:.4f}")
                if spearman_p < 0.05:
                    st.success("Significativo")
                else:
                    st.info("Não significativo")
            
            with col_c:
                st.metric("R² (Determinação)", f"{r_squared:.4f}")
                st.caption(f"{r_squared*100:.1f}% da variância explicada")
            
            with col_d:
                # Interpretação da força
                abs_r = abs(pearson_r)
                if abs_r > 0.8:
                    strength_color = "success"
                    strength_text = "Muito Forte"
                elif abs_r > 0.6:
                    strength_color = "warning"
                    strength_text = "Forte"
                elif abs_r > 0.3:
                    strength_color = "info"
                    strength_text = "Moderada"
                else:
                    strength_color = "error"
                    strength_text = "Fraca"
                
                getattr(st, strength_color)(f"🔗 {strength_text}")
            
            # Interpretação detalhada
            st.markdown("**📋 Interpretação:**")
            
            direction = "positiva" if pearson_r > 0 else "negativa"
            significance = "significativa" if pearson_p < 0.05 else "não significativa"
            
            st.write(f"Existe uma correlação {direction} {strength_text.lower()} e "
                    f"{significance} entre {x_var} e {y_var} (r = {pearson_r:.3f}, p = {pearson_p:.3f}).")
            
            if r_squared > 0.5:
                st.info(f"💡 {x_var} explica {r_squared*100:.1f}% da variabilidade em {y_var}")
            
        except Exception as e:
            st.error(f"❌ Erro no cálculo da correlação: {str(e)}")
    
    def _show_distribution_analysis(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Análise de distribuições"""
        st.markdown("### 📊 Análise de Distribuições")
        
        # Seleção de variável
        dist_var = st.selectbox(
            "Selecione a variável para análise de distribuição:",
            numeric_columns,
            key=f"dist_var_{self.project_id}"
        )
        
        if dist_var:
            data_col = df[dist_var].dropna()
            
            if len(data_col) == 0:
                st.warning("⚠️ Nenhum dado válido encontrado")
                return
            
            # Layout com gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                self._show_histogram_analysis(data_col, dist_var)
            
            with col2:
                self._show_normality_plots(data_col, dist_var)
            
            # Testes de normalidade
            self._show_normality_tests(data_col, dist_var)
            
            # Ajuste de distribuições
            self._show_distribution_fitting(data_col, dist_var)
    
    def _show_histogram_analysis(self, data: pd.Series, var_name: str):
        """Mostra análise de histograma"""
        # Histograma interativo
        fig = px.histogram(
            x=data,
            nbins=min(50, max(10, int(np.sqrt(len(data))))),
            title=f"Distribuição - {var_name}",
            marginal="box"
        )
        
        # Adicionar linha da média
        fig.add_vline(x=data.mean(), line_dash="dash", line_color="red", 
                     annotation_text="Média")
        
        # Adicionar linha da mediana
        fig.add_vline(x=data.median(), line_dash="dash", line_color="green", 
                     annotation_text="Mediana")
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_normality_plots(self, data: pd.Series, var_name: str):
        """Mostra gráficos para avaliação de normalidade"""
        try:
            # Q-Q Plot
            from scipy.stats import probplot
            
            fig = go.Figure()
            
            # Calcular Q-Q plot
            (osm, osr), (slope, intercept, r) = probplot(data, dist="norm", plot=None)
            
            # Pontos dos dados
            fig.add_scatter(
                x=osm, 
                y=osr, 
                mode='markers', 
                name='Dados Observados',
                marker=dict(color='blue', size=6)
            )
            
            # Linha teórica
            fig.add_scatter(
                x=osm, 
                y=slope * osm + intercept,
                mode='lines', 
                name='Linha Teórica Normal',
                line=dict(color='red', width=2)
            )
            
            fig.update_layout(
                title=f"Q-Q Plot Normal - {var_name}",
                xaxis_title="Quantis Teóricos",
                yaxis_title="Quantis da Amostra",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Interpretação do Q-Q plot
            if r > 0.95:
                st.success("✅ Dados seguem aproximadamente distribuição normal")
            elif r > 0.90:
                st.warning("⚠️ Desvios moderados da normalidade")
            else:
                st.error("❌ Desvios significativos da normalidade")
                
        except Exception as e:
            st.error(f"❌ Erro na geração do Q-Q plot: {str(e)}")
            
            # Box plot alternativo
            fig_box = px.box(y=data, title=f"Box Plot - {var_name}")
            fig_box.update_layout(height=400)
            st.plotly_chart(fig_box, use_container_width=True)
    
    def _show_normality_tests(self, data: pd.Series, var_name: str):
        """Testes estatísticos de normalidade"""
        st.markdown("#### 🧪 Testes de Normalidade")
        
        tests_results = []
        
        try:
            # Shapiro-Wilk (para n < 5000)
            if len(data) < 5000:
                shapiro_stat, shapiro_p = stats.shapiro(data)
                tests_results.append({
                    'Teste': 'Shapiro-Wilk',
                    'Estatística': f"{shapiro_stat:.6f}",
                    'p-valor': f"{shapiro_p:.6f}",
                    'Resultado': 'Normal' if shapiro_p > 0.05 else 'Não Normal'
                })
            
            # Kolmogorov-Smirnov
            ks_stat, ks_p = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
            tests_results.append({
                'Teste': 'Kolmogorov-Smirnov',
                'Estatística': f"{ks_stat:.6f}",
                'p-valor': f"{ks_p:.6f}",
                'Resultado': 'Normal' if ks_p > 0.05 else 'Não Normal'
            })
            
            # D'Agostino-Pearson
            try:
                dp_stat, dp_p = stats.normaltest(data)
                tests_results.append({
                    'Teste': "D'Agostino-Pearson",
                    'Estatística': f"{dp_stat:.6f}",
                    'p-valor': f"{dp_p:.6f}",
                    'Resultado': 'Normal' if dp_p > 0.05 else 'Não Normal'
                })
            except:
                pass
            
            # Anderson-Darling
            try:
                ad_stat, ad_crit, ad_sig = stats.anderson(data, dist='norm')
                # Usar nível de 5%
                critical_5 = ad_crit[2]  # 5% level
                tests_results.append({
                    'Teste': 'Anderson-Darling',
                    'Estatística': f"{ad_stat:.6f}",
                    'Valor Crítico (5%)': f"{critical_5:.6f}",
                    'Resultado': 'Normal' if ad_stat < critical_5 else 'Não Normal'
                })
            except:
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
            
        except Exception as e:
            st.error(f"❌ Erro nos testes de normalidade: {str(e)}")
    
    def _show_distribution_fitting(self, data: pd.Series, var_name: str):
        """Ajuste de distribuições estatísticas"""
        st.markdown("#### 📈 Ajuste de Distribuições")
        
        # Lista de distribuições para testar
        distributions_to_test = [
            ('Normal', stats.norm),
            ('Log-Normal', stats.lognorm),
            ('Exponencial', stats.expon),
            ('Gamma', stats.gamma),
            ('Beta', stats.beta),
            ('Weibull', stats.weibull_min)
        ]
        
        fitting_results = []
        
        for dist_name, dist_func in distributions_to_test:
            try:
                # Ajustar distribuição
                if dist_name == 'Normal':
                    params = dist_func.fit(data)
                    ks_stat, p_value = stats.kstest(data, dist_func.cdf, args=params)
                elif dist_name == 'Exponencial':
                    # Para exponencial, usar apenas dados positivos
                    if data.min() > 0:
                        params = dist_func.fit(data, floc=0)
                        ks_stat, p_value = stats.kstest(data, dist_func.cdf, args=params)
                    else:
                        continue
                else:
                    # Para outras distribuições, verificar se os dados são adequados
                    if data.min() >= 0:  # Dados não-negativos
                        params = dist_func.fit(data)
                        ks_stat, p_value = stats.kstest(data, dist_func.cdf, args=params)
                    else:
                        continue
                
                # Calcular AIC (critério de informação)
                log_likelihood = np.sum(dist_func.logpdf(data, *params))
                aic = 2 * len(params) - 2 * log_likelihood
                
                fitting_results.append({
                    'Distribuição': dist_name,
                    'KS Estatística': f"{ks_stat:.6f}",
                    'p-valor KS': f"{p_value:.6f}",
                    'AIC': f"{aic:.2f}",
                    'Qualidade': 'Boa' if p_value > 0.05 else 'Ruim'
                })
                
            except Exception as e:
                continue
        
        if fitting_results:
            df_fitting = pd.DataFrame(fitting_results)
            df_fitting = df_fitting.sort_values('p-valor KS', ascending=False)
            
            st.dataframe(df_fitting, use_container_width=True)
            
            # Melhor ajuste
            best_fit = df_fitting.iloc[0]
            st.info(f"🏆 **Melhor ajuste:** {best_fit['Distribuição']} "
                   f"(p-valor KS = {best_fit['p-valor KS']})")
            
            # Recomendações
            good_fits = df_fitting[df_fitting['Qualidade'] == 'Boa']
            if len(good_fits) > 0:
                st.success(f"✅ {len(good_fits)} distribuição(ões) com bom ajuste encontrada(s)")
            else:
                st.warning("⚠️ Nenhuma distribuição padrão se ajusta bem aos dados")
        else:
            st.info("📊 Não foi possível ajustar distribuições aos dados")
    
    def _show_statistical_tests(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Interface para testes estatísticos"""
        st.markdown("### 🧪 Testes Estatísticos")
        
        test_type = st.selectbox(
            "Selecione o tipo de teste:",
            [
                "Teste t (1 amostra)",
                "Teste t (2 amostras independentes)",
                "Teste t (amostras pareadas)",
                "ANOVA (1 fator)",
                "Teste de Proporções",
                "Teste Qui-quadrado",
                "Teste de Mann-Whitney U",
                "Teste de Wilcoxon"
            ],
            key=f"stat_test_type_{self.project_id}"
        )
        
        # Interface específica para cada teste
        if test_type == "Teste t (1 amostra)":
            self._show_one_sample_ttest(df, numeric_columns)
        elif test_type == "Teste t (2 amostras independentes)":
            self._show_two_sample_ttest(df, numeric_columns)
        elif test_type == "Teste t (amostras pareadas)":
            self._show_paired_ttest(df, numeric_columns)
        elif test_type == "ANOVA (1 fator)":
            self._show_anova_test(df, numeric_columns)
        elif test_type == "Teste de Mann-Whitney U":
            self._show_mannwhitney_test(df, numeric_columns)
        elif test_type == "Teste de Wilcoxon":
            self._show_wilcoxon_test(df, numeric_columns)
        else:
            st.info(f"🚧 {test_type} será implementado em breve")
    
    def _show_one_sample_ttest(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Teste t para uma amostra"""
        st.markdown("#### 📊 Teste t para Uma Amostra")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            test_var = st.selectbox("Variável:", numeric_columns, key=f"t1_var_{self.project_id}")
        
        with col2:
            mu0 = st.number_input("Valor de referência (μ₀):", value=0.0, key=f"t1_mu0_{self.project_id}")
        
        with col3:
            alpha = st.selectbox("Nível de significância:", [0.01, 0.05, 0.10], index=1, key=f"t1_alpha_{self.project_id}")
        
        # Hipóteses
        st.markdown("**Hipóteses:**")
        col_h1, col_h2 = st.columns(2)
        
        with col_h1:
            st.write(f"**H₀:** μ = {mu0}")
        with col_h2:
            st.write(f"**H₁:** μ ≠ {mu0}")
        
        if st.button("🧪 Executar Teste t", key=f"run_t1_{self.project_id}"):
            data_test = df[test_var].dropna()
            
            if len(data_test) == 0:
                st.error("❌ Nenhum dado válido encontrado")
                return
            
            # Executar teste
            t_stat, p_value = stats.ttest_1samp(data_test, mu0)
            
            # Graus de liberdade
            df_test = len(data_test) - 1
            
            # Valor crítico
            t_critical = stats.t.ppf(1 - alpha/2, df_test)
            
            # Resultados
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                st.metric("Estatística t", f"{t_stat:.4f}")
            
            with col_b:
                st.metric("p-valor", f"{p_value:.6f}")
            
            with col_c:
                st.metric("Valor crítico", f"±{t_critical:.4f}")
            
            with col_d:
                if p_value < alpha:
                    st.error("❌ Rejeitar H₀")
                    conclusion = "Rejeitar H₀"
                else:
                    st.success("✅ Não rejeitar H₀")
                    conclusion = "Não rejeitar H₀"
            
            # Interpretação detalhada
            st.markdown("#### 📋 Interpretação dos Resultados")
            
            sample_mean = data_test.mean()
            sample_std = data_test.std()
            sample_size = len(data_test)
            
            st.write(f"**Amostra:** n = {sample_size}, x̄ = {sample_mean:.4f}, s = {sample_std:.4f}")
            st.write(f"**Teste:** t = {t_stat:.4f}, gl = {df_test}, p = {p_value:.6f}")
            st.write(f"**Conclusão:** {conclusion} ao nível α = {alpha}")
            
            if p_value < alpha:
                direction = "maior" if sample_mean > mu0 else "menor"
                st.write(f"A média da amostra ({sample_mean:.4f}) é significativamente "
                        f"{direction} que {mu0} (p < {alpha}).")
            else:
                st.write(f"Não há evidência suficiente para concluir que a média "
                        f"seja diferente de {mu0} (p ≥ {alpha}).")
            
            # Intervalo de confiança
            margin_error = t_critical * (sample_std / np.sqrt(sample_size))
            ci_lower = sample_mean - margin_error
            ci_upper = sample_mean + margin_error
            
            st.write(f"**Intervalo de confiança ({(1-alpha)*100:.0f}%):** "
                    f"[{ci_lower:.4f}, {ci_upper:.4f}]")
    
    def _show_two_sample_ttest(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Teste t para duas amostras independentes"""
        st.markdown("#### 📊 Teste t para Duas Amostras Independentes")
        
        # Opções de análise
        approach = st.radio(
            "Abordagem:",
            ["Duas variáveis numéricas", "Uma variável por grupos"],
            key=f"t2_approach_{self.project_id}"
        )
        
        if approach == "Duas variáveis numéricas":
            self._show_two_variables_ttest(df, numeric_columns)
        else:
            self._show_grouped_ttest(df, numeric_columns)
    
    def _show_two_variables_ttest(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Teste t entre duas variáveis numéricas"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            var1 = st.selectbox("Variável 1:", numeric_columns, key=f"t2_var1_{self.project_id}")
        
        with col2:
            var2_options = [col for col in numeric_columns if col != var1]
            if not var2_options:
                st.error("❌ Necessário pelo menos 2 variáveis numéricas")
                return
            
            var2 = st.selectbox("Variável 2:", var2_options, key=f"t2_var2_{self.project_id}")
        
        with col3:
            alpha = st.selectbox("Nível de significância:", [0.01, 0.05, 0.10], index=1, key=f"t2_alpha_{self.project_id}")
        
        if st.button("🧪 Executar Teste t (2 amostras)", key=f"run_t2_{self.project_id}"):
            data1 = df[var1].dropna()
            data2 = df[var2].dropna()
            
            if len(data1) == 0 or len(data2) == 0:
                st.error("❌ Dados insuficientes em uma ou ambas as variáveis")
                return
            
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
                st.metric("p-valor", f"{p_value:.6f}")
            
            with col_c:
                st.metric("Levene p-valor", f"{levene_p:.6f}")
                if equal_var:
                    st.success("Variâncias iguais")
                else:
                    st.warning("Variâncias diferentes")
            
            with col_d:
                if p_value < alpha:
                    st.error("❌ Diferença significativa")
                else:
                    st.success("✅ Sem diferença significativa")
            
            # Estatísticas descritivas
            self._show_two_sample_descriptives(data1, data2, var1, var2)
            
            # Visualização
            self._show_two_sample_visualization(data1, data2, var1, var2)
    
    def _show_grouped_ttest(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Teste t por grupos"""
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        if not categorical_columns:
            st.warning("⚠️ Nenhuma variável categórica encontrada")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            response_var = st.selectbox("Variável Resposta:", numeric_columns, key=f"t2_response_{self.project_id}")
        
        with col2:
            group_var = st.selectbox("Variável de Grupo:", categorical_columns, key=f"t2_group_{self.project_id}")
        
        with col3:
            alpha = st.selectbox("Nível de significância:", [0.01, 0.05, 0.10], index=1, key=f"t2_group_alpha_{self.project_id}")
        
        # Selecionar grupos específicos
        unique_groups = df[group_var].dropna().unique()
        
        if len(unique_groups) < 2:
            st.error("❌ Necessário pelo menos 2 grupos")
            return
        
        selected_groups = st.multiselect(
            "Selecione exatamente 2 grupos para comparar:",
            unique_groups,
            max_selections=2,
            key=f"t2_selected_groups_{self.project_id}"
        )
        
        if len(selected_groups) == 2:
            if st.button("🧪 Executar Teste t (por grupos)", key=f"run_t2_groups_{self.project_id}"):
                group1_data = df[df[group_var] == selected_groups[0]][response_var].dropna()
                group2_data = df[df[group_var] == selected_groups[1]][response_var].dropna()
                
                if len(group1_data) == 0 or len(group2_data) == 0:
                    st.error("❌ Dados insuficientes em um ou ambos os grupos")
                    return
                
                # Executar teste
                t_stat, p_value = stats.ttest_ind(group1_data, group2_data)
                
                # Mostrar resultados
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.metric("Estatística t", f"{t_stat:.4f}")
                
                with col_b:
                    st.metric("p-valor", f"{p_value:.6f}")
                
                with col_c:
                    if p_value < alpha:
                        st.error("❌ Diferença significativa")
                    else:
                        st.success("✅ Sem diferença significativa")
                
                # Estatísticas por grupo
                self._show_group_comparison_results(
                    group1_data, group2_data, 
                    selected_groups[0], selected_groups[1], 
                    response_var
                )
        elif len(selected_groups) == 1:
            st.info("💡 Selecione mais um grupo para comparação")
        elif len(selected_groups) > 2:
            st.warning("⚠️ Selecione exatamente 2 grupos")
    
    def _show_two_sample_descriptives(self, data1: pd.Series, data2: pd.Series, var1: str, var2: str):
        """Estatísticas descritivas para duas amostras"""
        st.markdown("#### 📊 Estatísticas Descritivas")
        
        stats_comparison = pd.DataFrame({
            'Estatística': ['N', 'Média', 'Mediana', 'Desvio Padrão', 'Erro Padrão', 'Mínimo', 'Máximo'],
            var1: [
                len(data1),
                data1.mean(),
                data1.median(),
                data1.std(),
                data1.sem(),
                data1.min(),
                data1.max()
            ],
            var2: [
                len(data2),
                data2.mean(),
                data2.median(),
                data2.std(),
                data2.sem(),
                data2.min(),
                data2.max()
            ]
        })
        
        # Formatar números
        for col in [var1, var2]:
            stats_comparison[col] = stats_comparison[col].apply(
                lambda x: f"{int(x)}" if x == int(x) else f"{x:.4f}"
            )
        
        st.dataframe(stats_comparison, use_container_width=True)
    
    def _show_two_sample_visualization(self, data1: pd.Series, data2: pd.Series, var1: str, var2: str):
        """Visualização para comparação de duas amostras"""
        # Box plot comparativo
        fig = go.Figure()
        
        fig.add_trace(go.Box(y=data1, name=var1, boxpoints='outliers'))
        fig.add_trace(go.Box(y=data2, name=var2, boxpoints='outliers'))
        
        fig.update_layout(
            title=f"Comparação: {var1} vs {var2}",
            yaxis_title="Valores",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_group_comparison_results(self, group1_data: pd.Series, group2_data: pd.Series, 
                                     group1_name: str, group2_name: str, response_var: str):
        """Resultados da comparação entre grupos"""
        st.markdown("#### 📊 Comparação entre Grupos")
        
        # Estatísticas por grupo
        comparison_stats = pd.DataFrame({
            'Grupo': [group1_name, group2_name],
            'N': [len(group1_data), len(group2_data)],
            'Média': [group1_data.mean(), group2_data.mean()],
            'Mediana': [group1_data.median(), group2_data.median()],
            'Desvio Padrão': [group1_data.std(), group2_data.std()],
            'Erro Padrão': [group1_data.sem(), group2_data.sem()]
        })
        
        st.dataframe(comparison_stats, use_container_width=True)
        
        # Box plot por grupo
        combined_data = pd.DataFrame({
            response_var: pd.concat([group1_data, group2_data]),
            'Grupo': [group1_name] * len(group1_data) + [group2_name] * len(group2_data)
        })
        
        fig = px.box(combined_data, x='Grupo', y=response_var, 
                    title=f"Distribuição de {response_var} por Grupo")
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_anova_test(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Teste ANOVA de um fator"""
        st.markdown("#### 📊 ANOVA (Análise de Variância)")
        
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        if not categorical_columns:
            st.warning("⚠️ Nenhuma variável categórica encontrada")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            response_var = st.selectbox("Variável Resposta:", numeric_columns, key=f"anova_response_{self.project_id}")
        
        with col2:
            factor_var = st.selectbox("Fator (Categórica):", categorical_columns, key=f"anova_factor_{self.project_id}")
        
        with col3:
            alpha = st.selectbox("Nível de significância:", [0.01, 0.05, 0.10], index=1, key=f"anova_alpha_{self.project_id}")
        
        if st.button("🧪 Executar ANOVA", key=f"run_anova_{self.project_id}"):
            # Preparar dados
            groups = []
            group_names = []
            
            for group_name in df[factor_var].dropna().unique():
                group_data = df[df[factor_var] == group_name][response_var].dropna()
                if len(group_data) > 0:
                    groups.append(group_data)
                    group_names.append(str(group_name))
            
            if len(groups) < 2:
                st.error("❌ Necessário pelo menos 2 grupos com dados")
                return
            
            try:
                # ANOVA
                f_stat, p_value = stats.f_oneway(*groups)
                
                # Graus de liberdade
                df_between = len(groups) - 1
                df_within = sum(len(group) for group in groups) - len(groups)
                
                # Resultados principais
                col_a, col_b, col_c, col_d = st.columns(4)
                
                with col_a:
                    st.metric("Estatística F", f"{f_stat:.4f}")
                
                with col_b:
                    st.metric("p-valor", f"{p_value:.6f}")
                
                with col_c:
                    st.metric("GL Entre", df_between)
                    st.metric("GL Dentro", df_within)
                
                with col_d:
                    if p_value < alpha:
                        st.error("❌ Diferença significativa")
                        conclusion = "Pelo menos um grupo difere"
                    else:
                        st.success("✅ Sem diferença significativa")
                        conclusion = "Grupos não diferem"
                
                # Estatísticas por grupo
                st.markdown("#### 📊 Estatísticas por Grupo")
                
                group_stats = []
                for i, group in enumerate(groups):
                    group_stats.append({
                        'Grupo': group_names[i],
                        'N': len(group),
                        'Média': group.mean(),
                        'Desvio Padrão': group.std(),
                        'Erro Padrão': group.sem()
                    })
                
                group_df = pd.DataFrame(group_stats)
                st.dataframe(group_df, use_container_width=True)
                
                # Visualização
                combined_anova_data = pd.DataFrame({
                    response_var: pd.concat(groups),
                    factor_var: [name for i, name in enumerate(group_names) for _ in range(len(groups[i]))]
                })
                
                col_viz1, col_viz2 = st.columns(2)
                
                with col_viz1:
                    # Box plot
                    fig_box = px.box(combined_anova_data, x=factor_var, y=response_var,
                                    title=f"Box Plot: {response_var} por {factor_var}")
                    st.plotly_chart(fig_box, use_container_width=True)
                
                with col_viz2:
                    # Gráfico de médias
                    fig_means = px.bar(group_df, x='Grupo', y='Média',
                                      error_y='Erro Padrão',
                                      title=f"Médias por Grupo")
                    st.plotly_chart(fig_means, use_container_width=True)
                
                # Interpretação
                st.markdown("#### 📋 Interpretação")
                st.write(f"**Conclusão:** {conclusion} (F = {f_stat:.4f}, p = {p_value:.6f})")
                
                if p_value < alpha:
                    st.info("💡 Como há diferença significativa, considere realizar testes post-hoc "
                           "para identificar quais grupos diferem entre si.")
                
            except Exception as e:
                st.error(f"❌ Erro na execução da ANOVA: {str(e)}")
    
    def _show_mannwhitney_test(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Teste de Mann-Whitney U (não-paramétrico)"""
        st.markdown("#### 📊 Teste de Mann-Whitney U")
        st.info("💡 Alternativa não-paramétrica ao teste t para duas amostras independentes")
        
        # Similar ao teste t de duas amostras, mas usando Mann-Whitney
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        if not categorical_columns:
            st.warning("⚠️ Nenhuma variável categórica encontrada")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            response_var = st.selectbox("Variável Resposta:", numeric_columns, key=f"mw_response_{self.project_id}")
        
        with col2:
            group_var = st.selectbox("Variável de Grupo:", categorical_columns, key=f"mw_group_{self.project_id}")
        
        with col3:
            alpha = st.selectbox("Nível de significância:", [0.01, 0.05, 0.10], index=1, key=f"mw_alpha_{self.project_id}")
        
        # Selecionar grupos
        unique_groups = df[group_var].dropna().unique()
        
        if len(unique_groups) < 2:
            st.error("❌ Necessário pelo menos 2 grupos")
            return
        
        selected_groups = st.multiselect(
            "Selecione exatamente 2 grupos:",
            unique_groups,
            max_selections=2,
            key=f"mw_selected_groups_{self.project_id}"
        )
        
        if len(selected_groups) == 2:
            if st.button("🧪 Executar Mann-Whitney U", key=f"run_mw_{self.project_id}"):
                group1_data = df[df[group_var] == selected_groups[0]][response_var].dropna()
                group2_data = df[df[group_var] == selected_groups[1]][response_var].dropna()
                
                if len(group1_data) == 0 or len(group2_data) == 0:
                    st.error("❌ Dados insuficientes")
                    return
                
                try:
                    # Teste de Mann-Whitney U
                    u_stat, p_value = stats.mannwhitneyu(group1_data, group2_data, alternative='two-sided')
                    
                    # Resultados
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.metric("Estatística U", f"{u_stat:.0f}")
                    
                    with col_b:
                        st.metric("p-valor", f"{p_value:.6f}")
                    
                    with col_c:
                        if p_value < alpha:
                            st.error("❌ Diferença significativa")
                        else:
                            st.success("✅ Sem diferença significativa")
                    
                    # Estatísticas de postos
                    st.markdown("#### 📊 Análise de Postos")
                    
                    # Calcular postos médios
                    combined = pd.concat([group1_data, group2_data])
                    ranks = stats.rankdata(combined)
                    
                    group1_ranks = ranks[:len(group1_data)]
                    group2_ranks = ranks[len(group1_data):]
                    
                    rank_stats = pd.DataFrame({
                        'Grupo': [selected_groups[0], selected_groups[1]],
                        'N': [len(group1_data), len(group2_data)],
                        'Posto Médio': [np.mean(group1_ranks), np.mean(group2_ranks)],
                        'Soma dos Postos': [np.sum(group1_ranks), np.sum(group2_ranks)]
                    })
                    
                    st.dataframe(rank_stats, use_container_width=True)
                    
                    # Interpretação
                    st.markdown("#### 📋 Interpretação")
                    
                    higher_group = selected_groups[0] if np.mean(group1_ranks) > np.mean(group2_ranks) else selected_groups[1]
                    
                    if p_value < alpha:
                        st.write(f"Há diferença significativa entre os grupos (p = {p_value:.6f}). "
                                f"O grupo '{higher_group}' tende a ter valores mais altos.")
                    else:
                        st.write(f"Não há diferença significativa entre os grupos (p = {p_value:.6f}).")
                    
                except Exception as e:
                    st.error(f"❌ Erro no teste: {str(e)}")
    
    def _show_wilcoxon_test(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Teste de Wilcoxon (amostras pareadas)"""
        st.markdown("#### 📊 Teste de Wilcoxon (Amostras Pareadas)")
        st.info("💡 Alternativa não-paramétrica ao teste t pareado")
        
        if len(numeric_columns) < 2:
            st.warning("⚠️ Necessário pelo menos 2 variáveis numéricas")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            var1 = st.selectbox("Variável 1 (Antes):", numeric_columns, key=f"wilcoxon_var1_{self.project_id}")
        
        with col2:
            var2_options = [col for col in numeric_columns if col != var1]
            var2 = st.selectbox("Variável 2 (Depois):", var2_options, key=f"wilcoxon_var2_{self.project_id}")
        
        with col3:
            alpha = st.selectbox("Nível de significância:", [0.01, 0.05, 0.10], index=1, key=f"wilcoxon_alpha_{self.project_id}")
        
        if st.button("🧪 Executar Wilcoxon", key=f"run_wilcoxon_{self.project_id}"):
            # Dados pareados (apenas observações completas)
            paired_data = df[[var1, var2]].dropna()
            
            if len(paired_data) == 0:
                st.error("❌ Nenhum par de dados válido encontrado")
                return
            
            data1 = paired_data[var1]
            data2 = paired_data[var2]
            
            try:
                # Teste de Wilcoxon
                w_stat, p_value = stats.wilcoxon(data1, data2)
                
                # Resultados
                col_a, col_b, col_c, col_d = st.columns(4)
                
                with col_a:
                    st.metric("Estatística W", f"{w_stat:.0f}")
                
                with col_b:
                    st.metric("p-valor", f"{p_value:.6f}")
                
                with col_c:
                    st.metric("N Pares", len(paired_data))
                
                with col_d:
                    if p_value < alpha:
                        st.error("❌ Diferença significativa")
                    else:
                        st.success("✅ Sem diferença significativa")
                
                # Análise das diferenças
                differences = data2 - data1
                
                st.markdown("#### 📊 Análise das Diferenças")
                
                diff_stats = pd.DataFrame({
                    'Estatística': ['Mediana das Diferenças', 'Diferenças Positivas', 'Diferenças Negativas', 'Diferenças Zero'],
                    'Valor': [
                        differences.median(),
                        sum(differences > 0),
                        sum(differences < 0),
                        sum(differences == 0)
                    ]
                })
                
                st.dataframe(diff_stats, use_container_width=True)
                
                # Gráfico das diferenças
                fig = px.histogram(x=differences, title=f"Distribuição das Diferenças ({var2} - {var1})")
                fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Zero")
                fig.add_vline(x=differences.median(), line_dash="dash", line_color="green", annotation_text="Mediana")
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Interpretação
                st.markdown("#### 📋 Interpretação")
                
                if p_value < alpha:
                    direction = "aumentaram" if differences.median() > 0 else "diminuíram"
                    st.write(f"Há evidência significativa de que os valores {direction} "
                            f"de {var1} para {var2} (p = {p_value:.6f}).")
                else:
                    st.write(f"Não há evidência significativa de mudança entre {var1} e {var2} "
                            f"(p = {p_value:.6f}).")
                
            except Exception as e:
                st.error(f"❌ Erro no teste: {str(e)}")
    
    def _show_analysis_report(self, df: pd.DataFrame, numeric_columns: List[str]):
        """Relatório resumido das análises"""
        st.markdown("### 📋 Relatório de Análise Estatística")
        
        # Resumo dos dados
        st.markdown("#### 📊 Resumo dos Dados")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Observações", len(df))
        
        with col2:
            st.metric("Variáveis Numéricas", len(numeric_columns))
        
        with col3:
            missing_data = df[numeric_columns].isnull().sum().sum()
            st.metric("Dados Faltantes", missing_data)
        
        with col4:
            complete_cases = len(df.dropna(subset=numeric_columns))
            st.metric("Casos Completos", complete_cases)
        
        # Resumo estatístico geral
        if numeric_columns:
            st.markdown("#### 📈 Resumo Estatístico Geral")
            
            summary_stats = df[numeric_columns].describe()
            st.dataframe(summary_stats, use_container_width=True)
            
            # Insights automáticos
            st.markdown("#### 💡 Insights Automáticos")
            
            insights = []
            
            for col in numeric_columns[:3]:  # Limitar a 3 variáveis principais
                data = df[col].dropna()
                
                if len(data) > 0:
                    # Variabilidade
                    cv = (data.std() / data.mean()) * 100 if data.mean() != 0 else 0
                    
                    if cv > 50:
                        insights.append(f"🔍 **{col}**: Alta variabilidade (CV = {cv:.1f}%)")
                    elif cv < 10:
                        insights.append(f"✅ **{col}**: Baixa variabilidade (CV = {cv:.1f}%)")
                    
                    # Assimetria
                    skewness = stats.skew(data)
                    if abs(skewness) > 1:
                        direction = "direita" if skewness > 0 else "esquerda"
                        insights.append(f"⚖️ **{col}**: Distribuição assimétrica à {direction}")
                    
                    # Outliers
                    Q1, Q3 = data.quantile([0.25, 0.75])
                    IQR = Q3 - Q1
                    outliers = data[(data < Q1 - 1.5*IQR) | (data > Q3 + 1.5*IQR)]
                    
                    if len(outliers) > len(data) * 0.05:  # Mais de 5% outliers
                        insights.append(f"⚠️ **{col}**: {len(outliers)} outliers detectados ({len(outliers)/len(data)*100:.1f}%)")
            
            if insights:
                for insight in insights:
                    st.write(insight)
            else:
                st.info("📊 Dados aparentam estar dentro dos padrões normais")
            
            # Recomendações
            st.markdown("#### 🎯 Recomendações para Próximas Etapas")
            
            recommendations = [
                "🔍 **Análise de Causa Raiz**: Use os insights estatísticos para focar nas variáveis mais críticas",
                "🧪 **Teste de Hipóteses**: Formule hipóteses baseadas nos padrões identificados",
                "📈 **Análise de Correlações**: Explore as relações entre variáveis para identificar fatores de influência",
                "⚙️ **Análise de Processo**: Investigue as etapas que podem estar causando alta variabilidade"
            ]
            
            for rec in recommendations:
                st.write(rec)
    
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


class RootCauseAnalysis:
    """Classe para análise de causa raiz com ferramentas avançadas"""
    
    def __init__(self, manager: AnalyzePhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.data = manager.initialize_session_data('root_cause_analysis', {
            'problem_statement': '',
            'why_analysis': [],
            'fishbone_categories': {},
            'pareto_data': [],
            'fault_tree_data': {}
        })
    
    def show(self):
        """Interface principal da análise de causa raiz"""
        st.markdown("## 🔍 Análise de Causa Raiz")
        st.markdown("Identifique e analise as causas raiz dos problemas usando ferramentas estruturadas e metodologias comprovadas.")
        
        # Status da ferramenta
        self._show_status()
        
        # Interface principal
        self._show_analysis_tabs()
    
    def _show_status(self):
        """Mostra status da ferramenta"""
        if self.manager.is_tool_completed('root_cause_analysis'):
            st.success("✅ **Análise de causa raiz concluída**")
        else:
            st.info("⏳ **Análise em desenvolvimento**")
    
    def _show_analysis_tabs(self):
        """Interface com abas para diferentes ferramentas"""
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📝 Definição do Problema",
            "🤔 5 Porquês", 
            "🐟 Ishikawa", 
            "📊 Pareto",
            "📋 Relatório"
        ])
        
        with tab1:
            self._show_problem_definition()
        
        with tab2:
            self._show_five_whys()
        
        with tab3:
            self._show_fishbone_diagram()
        
        with tab4:
            self._show_pareto_analysis()
        
        with tab5:
            self._show_rca_report()
        
        # Botões de ação
        self._show_action_buttons()
    
    def _show_problem_definition(self):
        """Definição clara do problema"""
        st.markdown("### 📝 Definição do Problema")
        st.markdown("Uma definição clara e específica do problema é fundamental para uma análise eficaz.")
        
        # Declaração do problema
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
        
        # Framework 5W2H para estruturar o problema
        st.markdown("#### 🎯 Framework 5W2H para Estruturação")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**What (O quê?)**")
            what = st.text_input(
                "O que exatamente está acontecendo?",
                value=self.data.get('5w2h', {}).get('what', ''),
                key=f"what_{self.project_id}"
            )
            
            st.markdown("**Where (Onde?)**")
            where = st.text_input(
                "Onde o problema ocorre?",
                value=self.data.get('5w2h', {}).get('where', ''),
                key=f"where_{self.project_id}"
            )
            
            st.markdown("**When (Quando?)**")
            when = st.text_input(
                "Quando o problema acontece?",
                value=self.data.get('5w2h', {}).get('when', ''),
                key=f"when_{self.project_id}"
            )
            
            st.markdown("**Who (Quem?)**")
            who = st.text_input(
                "Quem está envolvido/afetado?",
                value=self.data.get('5w2h', {}).get('who', ''),
                key=f"who_{self.project_id}"
            )
        
        with col2:
            st.markdown("**Why (Por quê?)**")
            why = st.text_input(
                "Por que é importante resolver?",
                value=self.data.get('5w2h', {}).get('why', ''),
                key=f"why_{self.project_id}"
            )
            
            st.markdown("**How (Como?)**")
            how = st.text_input(
                "Como o problema se manifesta?",
                value=self.data.get('5w2h', {}).get('how', ''),
                key=f"how_{self.project_id}"
            )
            
            st.markdown("**How Much (Quanto?)**")
            how_much = st.text_input(
                "Qual o impacto quantitativo?",
                value=self.data.get('5w2h', {}).get('how_much', ''),
                key=f"how_much_{self.project_id}"
            )
        
        # Salvar dados 5W2H
        if '5w2h' not in self.data:
            self.data['5w2h'] = {}
        
        self.data['5w2h'].update({
            'what': what,
            'where': where,
            'when': when,
            'who': who,
            'why': why,
            'how': how,
            'how_much': how_much
        })
        
        # Validação da definição
        if problem_statement.strip():
            filled_fields = sum(1 for field in [what, where, when, who, why, how, how_much] if field.strip())
            
            col_val1, col_val2 = st.columns(2)
            
            with col_val1:
                st.metric("Campos Preenchidos", f"{filled_fields}/7")
            
            with col_val2:
                if filled_fields >= 5:
                    st.success("✅ Definição bem estruturada")
                elif filled_fields >= 3:
                    st.warning("⚠️ Definição parcial")
                else:
                    st.error("❌ Definição incompleta")
        
        # Dicas para uma boa definição
        with st.expander("💡 Dicas para uma Definição Eficaz"):
            st.markdown("""
            **✅ Características de uma boa definição de problema:**
            
            - **Específica**: Evite termos vagos como "às vezes" ou "frequentemente"
            - **Mensurável**: Inclua números, percentuais, frequências
            - **Observável**: Descreva comportamentos ou resultados observáveis
            - **Temporal**: Indique quando o problema começou ou com que frequência ocorre
            - **Impacto claro**: Explique as consequências do problema
            
            **❌ Evite:**
            - Linguagem subjetiva ("ruim", "péssimo")
            - Assumir causas na descrição do problema
            - Definições muito amplas ou muito específicas
            """)
    
    def _show_five_whys(self):
        """Análise dos 5 Porquês"""
        st.markdown("### 🤔 Análise dos 5 Porquês")
        st.markdown("Técnica iterativa que explora as relações de causa e efeito subjacentes a um problema.")
        
        if not self.data.get('problem_statement', '').strip():
            st.warning("⚠️ Primeiro defina o problema na aba 'Definição do Problema'")
            return
        
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
                        'answer': '',
                        'evidence': '',
                        'confidence': 'Média'
                    })
                    st.rerun()
        
        # Análise da causa raiz identificada
        if len(self.data['why_analysis']) > 0:
            self._show_root_cause_summary()
    
    def _show_why_item(self, index: int, why_item: Dict):
        """Mostra um item da análise dos porquês"""
        with st.container():
            st.markdown(f"**Por que {index + 1}:**")
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Pergunta (editável)
                question = st.text_input(
                    f"Pergunta {index + 1}:",
                    value=why_item.get('question', f"Por que {index + 1}?"),
                    key=f"why_question_{index}_{self.project_id}"
                )
                
                # Resposta
                answer = st.text_area(
                    f"Resposta {index + 1}:",
                    value=why_item.get('answer', ''),
                    placeholder="Descreva a causa identificada...",
                    height=80,
                    key=f"why_answer_{index}_{self.project_id}"
                )
                
                # Evidência
                evidence = st.text_input(
                    f"Evidência {index + 1}:",
                    value=why_item.get('evidence', ''),
                    placeholder="Que evidências suportam esta causa?",
                    key=f"why_evidence_{index}_{self.project_id}"
                )
                
                # Nível de confiança
                confidence = st.selectbox(
                    f"Confiança {index + 1}:",
                    ["Baixa", "Média", "Alta"],
                    index=["Baixa", "Média", "Alta"].index(why_item.get('confidence', 'Média')),
                    key=f"why_confidence_{index}_{self.project_id}"
                )
                
                # Atualizar dados
                self.data['why_analysis'][index] = {
                    'question': question,
                    'answer': answer,
                    'evidence': evidence,
                    'confidence': confidence
                }
            
            with col2:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"remove_why_{index}_{self.project_id}"):
                    self.data['why_analysis'].pop(index)
                    st.rerun()
            
            st.divider()
    
    def _show_root_cause_summary(self):
        """Resumo da análise de causa raiz"""
        st.markdown("#### 🎯 Causa Raiz Identificada")
        
        # Última resposta como causa raiz potencial
        if self.data['why_analysis']:
            last_why = self.data['why_analysis'][-1]
            
            if last_why.get('answer', '').strip():
                st.success(f"**Possível Causa Raiz:** {last_why['answer']}")
                
                # Avaliação da qualidade da análise
                filled_items = sum(1 for item in self.data['why_analysis'] 
                                 if item.get('answer', '').strip())
                
                high_confidence = sum(1 for item in self.data['why_analysis'] 
                                    if item.get('confidence') == 'Alta')
                
                col_qual1, col_qual2, col_qual3 = st.columns(3)
                
                with col_qual1:
                    st.metric("Porquês Respondidos", filled_items)
                
                with col_qual2:
                    st.metric("Alta Confiança", high_confidence)
                
                with col_qual3:
                    quality_score = (filled_items * 0.6 + high_confidence * 0.4) / 5 * 100
                    st.metric("Qualidade da Análise", f"{quality_score:.0f}%")
                
                # Recomendações
                if quality_score >= 80:
                    st.success("✅ Análise robusta - prossiga para validação")
                elif quality_score >= 60:
                    st.warning("⚠️ Análise adequada - considere mais evidências")
                else:
                    st.error("❌ Análise incompleta - adicione mais detalhes")
        
        # Campo para causa raiz final
        root_cause = st.text_area(
            "**Declaração Final da Causa Raiz**",
            value=self.data.get('root_cause_final', ''),
            placeholder="Com base na análise dos porquês, qual é a causa raiz principal?",
            height=100,
            key=f"root_cause_final_{self.project_id}"
        )
        
        self.data['root_cause_final'] = root_cause
    
    def _show_fishbone_diagram(self):
        """Diagrama de Ishikawa (Espinha de Peixe)"""
        st.markdown("### 🐟 Diagrama de Ishikawa (Espinha de Peixe)")
        st.markdown("Ferramenta visual para identificar causas potenciais organizadas por categorias.")
        
        # Seletor de método (6M, 4P, etc.)
        method = st.selectbox(
            "Método de Categorização:",
            ["6M (Manufatura)", "4P (Serviços)", "4S (Serviços)", "Personalizado"],
            key=f"fishbone_method_{self.project_id}"
        )
        
        # Definir categorias baseado no método
        if method == "6M (Manufatura)":
            categories = {
                'Método': 'Processos, procedimentos, instruções de trabalho',
                'Máquina': 'Equipamentos, ferramentas, tecnologia, software',
                'Material': 'Matéria-prima, insumos, componentes, qualidade',
                'Mão de obra': 'Pessoas, habilidades, treinamento, experiência',
                'Medição': 'Instrumentos, calibração, sistema de medição',
                'Meio ambiente': 'Condições ambientais, layout, organização, cultura'
            }
        elif method == "4P (Serviços)":
            categories = {
                'Políticas': 'Regras, diretrizes, procedimentos organizacionais',
                'Procedimentos': 'Processos, métodos, fluxos de trabalho',
                'Pessoas': 'Recursos humanos, competências, treinamento',
                'Planta/Local': 'Instalações, equipamentos, ambiente físico'
            }
        elif method == "4S (Serviços)":
            categories = {
                'Surroundings': 'Ambiente físico, condições de trabalho',
                'Suppliers': 'Fornecedores, parceiros, terceirizados',
                'Systems': 'Sistemas, processos, tecnologia',
                'Skills': 'Habilidades, competências, conhecimento'
            }
        else:  # Personalizado
            categories = self.data.get('custom_categories', {
                'Categoria 1': 'Descrição da categoria 1',
                'Categoria 2': 'Descrição da categoria 2',
                'Categoria 3': 'Descrição da categoria 3'
            })
        
        # Interface para categorias personalizadas
        if method == "Personalizado":
            self._show_custom_categories()
            categories = self.data.get('custom_categories', categories)
        
        # Inicializar estrutura de dados
        if 'fishbone_categories' not in self.data:
            self.data['fishbone_categories'] = {}
        
        # Interface para cada categoria
        st.markdown("#### 📋 Causas por Categoria")
        
        total_causes = 0
        
        for category, description in categories.items():
            with st.expander(f"**{category}** - {description}"):
                
                if category not in self.data['fishbone_categories']:
                    self.data['fishbone_categories'][category] = []
                
                # Mostrar causas existentes
                for i, cause in enumerate(self.data['fishbone_categories'][category]):
                    self._show_fishbone_cause(category, i, cause)
                
                # Adicionar nova causa
                self._show_add_cause_interface(category)
                
                total_causes += len(self.data['fishbone_categories'][category])
        
        # Resumo e visualização
        if total_causes > 0:
            self._show_fishbone_summary(categories, total_causes)
    
    def _show_custom_categories(self):
        """Interface para definir categorias personalizadas"""
        st.markdown("#### ⚙️ Definir Categorias Personalizadas")
        
        if 'custom_categories' not in self.data:
            self.data['custom_categories'] = {}
        
        # Adicionar nova categoria
        with st.expander("Adicionar Nova Categoria"):
            col1, col2, col3 = st.columns([2, 3, 1])
            
            with col1:
                new_cat_name = st.text_input("Nome da Categoria", key=f"new_cat_name_{self.project_id}")
            
            with col2:
                new_cat_desc = st.text_input("Descrição", key=f"new_cat_desc_{self.project_id}")
            
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Adicionar", key=f"add_category_{self.project_id}"):
                    if new_cat_name.strip():
                        self.data['custom_categories'][new_cat_name.strip()] = new_cat_desc.strip()
                        st.rerun()
        
        # Mostrar categorias existentes
        if self.data['custom_categories']:
            st.markdown("**Categorias Definidas:**")
            
            for i, (cat_name, cat_desc) in enumerate(self.data['custom_categories'].items()):
                col1, col2, col3 = st.columns([2, 3, 1])
                
                with col1:
                    new_name = st.text_input(f"Nome {i+1}:", value=cat_name, key=f"edit_cat_name_{i}_{self.project_id}")
                
                with col2:
                    new_desc = st.text_input(f"Descrição {i+1}:", value=cat_desc, key=f"edit_cat_desc_{i}_{self.project_id}")
                
                with col3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"remove_category_{i}_{self.project_id}"):
                        del self.data['custom_categories'][cat_name]
                        st.rerun()
                
                # Atualizar se mudou
                if new_name != cat_name or new_desc != cat_desc:
                    if new_name.strip():
                        # Remover antiga e adicionar nova
                        del self.data['custom_categories'][cat_name]
                        self.data['custom_categories'][new_name.strip()] = new_desc.strip()
    
    def _show_fishbone_cause(self, category: str, index: int, cause: Dict):
        """Mostra uma causa do diagrama de Ishikawa"""
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            cause_text = st.text_input(
                f"Causa {index + 1}:",
                value=cause.get('cause', ''),
                key=f"fishbone_cause_{category}_{index}_{self.project_id}"
            )
        
        with col2:
            priority = st.selectbox(
                f"Prioridade {index + 1}:",
                ["Baixa", "Média", "Alta"],
                index=["Baixa", "Média", "Alta"].index(cause.get('priority', 'Média')),
                key=f"fishbone_priority_{category}_{index}_{self.project_id}"
            )
        
        with col3:
            evidence = st.text_input(
                f"Evidência {index + 1}:",
                value=cause.get('evidence', ''),
                placeholder="Evidência...",
                key=f"fishbone_evidence_{category}_{index}_{self.project_id}"
            )
        
        with col4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"remove_fishbone_{category}_{index}_{self.project_id}"):
                self.data['fishbone_categories'][category].pop(index)
                st.rerun()
        
        # Atualizar dados
        self.data['fishbone_categories'][category][index] = {
            'cause': cause_text,
            'priority': priority,
            'evidence': evidence
        }
    
    def _show_add_cause_interface(self, category: str):
        """Interface para adicionar nova causa"""
        new_cause = st.text_input(
            "Nova causa:",
            key=f"new_cause_{category}_{self.project_id}",
            placeholder=f"Digite uma possível causa relacionada a {category}..."
        )
        
        if st.button(f"➕ Adicionar em {category}", key=f"add_cause_{category}_{self.project_id}"):
            if new_cause.strip():
                self.data['fishbone_categories'][category].append({
                    'cause': new_cause.strip(),
                    'priority': 'Média',
                    'evidence': ''
                })
                st.rerun()
    
    def _show_fishbone_summary(self, categories: Dict, total_causes: int):
        """Resumo do diagrama de Ishikawa"""
        st.markdown("#### 📊 Resumo do Diagrama de Ishikawa")
        
        # Métricas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Causas", total_causes)
        
        with col2:
            high_priority = sum(
                sum(1 for cause in causes if cause.get('priority') == 'Alta')
                for causes in self.data['fishbone_categories'].values()
            )
            st.metric("Alta Prioridade", high_priority)
        
        with col3:
            with_evidence = sum(
                sum(1 for cause in causes if cause.get('evidence', '').strip())
                for causes in self.data['fishbone_categories'].values()
            )
            st.metric("Com Evidência", with_evidence)
        
        with col4:
            categories_used = sum(1 for causes in self.data['fishbone_categories'].values() if len(causes) > 0)
            st.metric("Categorias Usadas", f"{categories_used}/{len(categories)}")
        
        # Gráfico de distribuição por categoria
        if total_causes > 0:
            category_counts = {
                cat: len(self.data['fishbone_categories'].get(cat, []))
                for cat in categories.keys()
            }
            
            # Filtrar categorias com causas
            category_counts = {k: v for k, v in category_counts.items() if v > 0}
            
            if category_counts:
                fig = px.bar(
                    x=list(category_counts.keys()),
                    y=list(category_counts.values()),
                    title="Distribuição de Causas por Categoria",
                    labels={'x': 'Categorias', 'y': 'Número de Causas'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Lista de causas prioritárias
        priority_causes = []
        for category, causes in self.data['fishbone_categories'].items():
            for cause in causes:
                if cause.get('priority') == 'Alta' and cause.get('cause', '').strip():
                    priority_causes.append({
                        'Categoria': category,
                        'Causa': cause['cause'],
                        'Evidência': cause.get('evidence', 'Não informada')
                    })
        
        if priority_causes:
            st.markdown("#### 🎯 Causas de Alta Prioridade")
            df_priority = pd.DataFrame(priority_causes)
            st.dataframe(df_priority, use_container_width=True)
    
    def _show_pareto_analysis(self):
        """Análise de Pareto para priorização de causas"""
        st.markdown("### 📊 Análise de Pareto")
        st.markdown("Identifique as causas mais importantes seguindo o princípio 80/20.")
        
        # Inicializar dados de Pareto
        if 'pareto_data' not in self.data:
            self.data['pareto_data'] = []
        
        # Interface para adicionar dados
        self._show_pareto_data_entry()
        
        # Mostrar dados existentes e análise
        if self.data['pareto_data']:
            self._show_pareto_table()
            self._show_pareto_chart()
            self._show_pareto_insights()
    
    def _show_pareto_data_entry(self):
        """Interface para entrada de dados do Pareto"""
        st.markdown("#### ➕ Adicionar Dados para Análise")
        
        with st.expander("Adicionar Nova Causa/Problema"):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                pareto_cause = st.text_input(
                    "Causa/Problema:",
                    key=f"pareto_cause_{self.project_id}",
                    placeholder="Descreva a causa ou problema..."
                )
            
            with col2:
                pareto_frequency = st.number_input(
                    "Frequência/Ocorrências:",
                    min_value=0,
                    value=0,
                    key=f"pareto_freq_{self.project_id}"
                )
            
            with col3:
                pareto_impact = st.selectbox(
                    "Nível de Impacto:",
                    ["Baixo", "Médio", "Alto"],
                    key=f"pareto_impact_{self.project_id}"
                )
            
            with col4:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Adicionar", key=f"add_pareto_{self.project_id}"):
                    if pareto_cause.strip() and pareto_frequency > 0:
                        # Calcular peso baseado no impacto
                        impact_weights = {"Baixo": 1, "Médio": 2, "Alto": 3}
                        weighted_value = pareto_frequency * impact_weights[pareto_impact]
                        
                        self.data['pareto_data'].append({
                            'cause': pareto_cause.strip(),
                            'frequency': pareto_frequency,
                            'impact': pareto_impact,
                            'weighted_value': weighted_value
                        })
                        st.rerun()
        
        # Importar causas do Fishbone
        if self.data.get('fishbone_categories'):
            st.markdown("#### 📥 Importar do Diagrama de Ishikawa")
            
            if st.button("📥 Importar Causas de Alta Prioridade", key=f"import_fishbone_{self.project_id}"):
                imported_count = 0
                
                for category, causes in self.data['fishbone_categories'].items():
                    for cause in causes:
                        if cause.get('priority') == 'Alta' and cause.get('cause', '').strip():
                            # Verificar se já existe
                            existing = any(
                                item['cause'] == cause['cause']
                                for item in self.data['pareto_data']
                            )
                            
                            if not existing:
                                self.data['pareto_data'].append({
                                    'cause': cause['cause'],
                                    'frequency': 1,  # Valor padrão
                                    'impact': 'Alto',
                                    'weighted_value': 3
                                })
                                imported_count += 1
                
                if imported_count > 0:
                    st.success(f"✅ {imported_count} causa(s) importada(s) do Ishikawa")
                    st.rerun()
                else:
                    st.info("💡 Nenhuma causa nova para importar")
    
    def _show_pareto_table(self):
        """Tabela editável dos dados de Pareto"""
        st.markdown("#### 📋 Dados Coletados")
        
        for i, item in enumerate(self.data['pareto_data']):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                item['cause'] = st.text_input(
                    f"Causa {i+1}:",
                    value=item['cause'],
                    key=f"edit_pareto_cause_{i}_{self.project_id}"
                )
            
            with col2:
                item['frequency'] = st.number_input(
                    f"Freq. {i+1}:",
                    value=item['frequency'],
                    min_value=0,
                    key=f"edit_pareto_freq_{i}_{self.project_id}"
                )
            
            with col3:
                item['impact'] = st.selectbox(
                    f"Impacto {i+1}:",
                    ["Baixo", "Médio", "Alto"],
                    index=["Baixo", "Médio", "Alto"].index(item['impact']),
                    key=f"edit_pareto_impact_{i}_{self.project_id}"
                )
            
            with col4:
                # Recalcular valor ponderado
                impact_weights = {"Baixo": 1, "Médio": 2, "Alto": 3}
                item['weighted_value'] = item['frequency'] * impact_weights[item['impact']]
                st.metric(f"Peso {i+1}:", f"{item['weighted_value']}")
            
            with col5:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"remove_pareto_{i}_{self.project_id}"):
                    self.data['pareto_data'].pop(i)
                    st.rerun()
    
    def _show_pareto_chart(self):
        """Gráfico de Pareto"""
        if len(self.data['pareto_data']) < 2:
            st.info("💡 Adicione pelo menos 2 itens para gerar o gráfico de Pareto")
            return
        
        st.markdown("#### 📊 Gráfico de Pareto")
        
        # Preparar dados
        pareto_df = pd.DataFrame(self.data['pareto_data'])
        pareto_df = pareto_df.sort_values('weighted_value', ascending=False)
        
        # Calcular percentuais cumulativos
        pareto_df['cumulative_value'] = pareto_df['weighted_value'].cumsum()
        pareto_df['cumulative_percent'] = (pareto_df['cumulative_value'] / pareto_df['weighted_value'].sum()) * 100
        
        # Criar gráfico
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Barras (valores ponderados)
        fig.add_trace(
            go.Bar(
                x=pareto_df['cause'],
                y=pareto_df['weighted_value'],
                name='Valor Ponderado',
                marker_color='lightblue'
            ),
            secondary_y=False
        )
        
        # Linha cumulativa
        fig.add_trace(
            go.Scatter(
                x=pareto_df['cause'],
                y=pareto_df['cumulative_percent'],
                mode='lines+markers',
                name='% Cumulativo',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ),
            secondary_y=True
        )
        
        # Linha 80%
        fig.add_hline(
            y=80, 
            line_dash="dash", 
            line_color="orange",
            annotation_text="80%",
            secondary_y=True
        )
        
        # Layout
        fig.update_xaxes(title_text="Causas")
        fig.update_yaxes(title_text="Valor Ponderado (Frequência × Impacto)", secondary_y=False)
        fig.update_yaxes(title_text="Percentual Cumulativo (%)", secondary_y=True, range=[0, 100])
        
        fig.update_layout(
            title="Análise de Pareto - Priorização de Causas",
            height=500,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Salvar dados processados para insights
        self.data['pareto_analysis'] = {
            'sorted_data': pareto_df.to_dict('records'),
            'total_value': pareto_df['weighted_value'].sum()
        }
    
    def _show_pareto_insights(self):
        """Insights da análise de Pareto"""
        st.markdown("#### 💡 Insights da Análise de Pareto")
        
        if 'pareto_analysis' not in self.data:
            return
        
        sorted_data = self.data['pareto_analysis']['sorted_data']
        
        # Identificar causas vitais (80%)
        vital_causes = []
        for item in sorted_data:
            if item['cumulative_percent'] <= 80:
                vital_causes.append(item['cause'])
        
        if not vital_causes:
            vital_causes = [sorted_data[0]['cause']]  # Pelo menos a primeira
        
        # Mostrar resultados
        col1, col2 = st.columns(2)
        
        with col1:
            st.success(f"🎯 **Causas Vitais ({len(vital_causes)} de {len(sorted_data)}):**")
            for cause in vital_causes:
                st.write(f"• {cause}")
        
        with col2:
            # Estatísticas
            vital_value = sum(item['weighted_value'] for item in sorted_data if item['cause'] in vital_causes)
            total_value = self.data['pareto_analysis']['total_value']
            vital_percent = (vital_value / total_value) * 100
            
            st.metric("Impacto das Causas Vitais", f"{vital_percent:.1f}%")
            st.metric("Proporção de Causas", f"{len(vital_causes)}/{len(sorted_data)}")
        
        # Recomendações
        st.markdown("#### 🎯 Recomendações Estratégicas")
        
        recommendations = [
            f"🔥 **Foque nas {len(vital_causes)} causas vitais** que representam {vital_percent:.1f}% do impacto total",
            "📊 **Implemente monitoramento** específico para as causas de maior impacto",
            "⚡ **Priorize recursos** para resolver as causas vitais identificadas",
            "🔄 **Reavalie periodicamente** a análise conforme novas informações"
        ]
        
        for rec in recommendations:
            st.write(rec)
    
    def _show_rca_report(self):
        """Relatório consolidado da análise de causa raiz"""
        st.markdown("### 📋 Relatório de Análise de Causa Raiz")
        
        # Resumo executivo
        st.markdown("#### 📊 Resumo Executivo")
        
        # Verificar completude das análises
        problem_defined = bool(self.data.get('problem_statement', '').strip())
        why_analysis_done = len(self.data.get('why_analysis', [])) > 0
        fishbone_done = any(len(causes) > 0 for causes in self.data.get('fishbone_categories', {}).values())
        pareto_done = len(self.data.get('pareto_data', [])) > 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if problem_defined:
                st.success("✅ Problema Definido")
            else:
                st.error("❌ Problema Não Definido")
        
        with col2:
            if why_analysis_done:
                st.success("✅ 5 Porquês Realizado")
            else:
                st.error("❌ 5 Porquês Pendente")
        
        with col3:
            if fishbone_done:
                st.success("✅ Ishikawa Completo")
            else:
                st.error("❌ Ishikawa Pendente")
        
        with col4:
            if pareto_done:
                st.success("✅ Pareto Realizado")
            else:
                st.error("❌ Pareto Pendente")
        
        # Problema identificado
        if problem_defined:
            st.markdown("#### 🎯 Problema Identificado")
            st.info(self.data['problem_statement'])
        
        # Causa raiz principal
        if self.data.get('root_cause_final', '').strip():
            st.markdown("#### 🔍 Causa Raiz Principal")
            st.success(self.data['root_cause_final'])
        
        # Causas vitais do Pareto
        if pareto_done and 'pareto_analysis' in self.data:
            st.markdown("#### 📊 Causas Prioritárias (Pareto)")
            
            sorted_data = self.data['pareto_analysis']['sorted_data']
            vital_causes = [item for item in sorted_data if item['cumulative_percent'] <= 80]
            
            if not vital_causes:
                vital_causes = [sorted_data[0]]  # Pelo menos a primeira
            
            for i, cause in enumerate(vital_causes, 1):
                st.write(f"**{i}.** {cause['cause']} "
                        f"(Peso: {cause['weighted_value']}, "
                        f"Impacto: {cause['impact']})")
        
        # Resumo das ferramentas utilizadas
        st.markdown("#### 🛠️ Ferramentas Utilizadas")
        
        tools_summary = []
        
        if why_analysis_done:
            why_count = len([item for item in self.data['why_analysis'] if item.get('answer', '').strip()])
            tools_summary.append(f"**5 Porquês:** {why_count} níveis analisados")
        
        if fishbone_done:
            total_fishbone_causes = sum(len(causes) for causes in self.data['fishbone_categories'].values())
            categories_used = sum(1 for causes in self.data['fishbone_categories'].values() if len(causes) > 0)
            tools_summary.append(f"**Ishikawa:** {total_fishbone_causes} causas em {categories_used} categorias")
        
        if pareto_done:
            pareto_items = len(self.data['pareto_data'])
            tools_summary.append(f"**Pareto:** {pareto_items} causas analisadas e priorizadas")
        
        for tool in tools_summary:
            st.write(f"• {tool}")
        
        # Próximos passos recomendados
        st.markdown("#### 🚀 Próximos Passos Recomendados")
        
        next_steps = [
            "🧪 **Validar as causas raiz** através de testes de hipóteses",
            "📊 **Coletar dados adicionais** para confirmar as causas identificadas",
            "💡 **Desenvolver soluções** focadas nas causas vitais do Pareto",
            "📈 **Planejar implementação** das melhorias na fase Improve",
            "📋 **Definir métricas** para monitorar a eficácia das soluções"
        ]
        
        for step in next_steps:
            st.write(step)
        
        # Exportar dados (simulado)
        if st.button("📄 Gerar Relatório Detalhado", key=f"export_rca_{self.project_id}"):
            # Aqui você poderia implementar exportação para PDF ou Word
            st.success("📄 Relatório gerado com sucesso!")
            st.info("💡 Funcionalidade de exportação será implementada em versões futuras")
    
    def _show_action_buttons(self):
        """Botões de ação para salvar e finalizar"""
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
                has_analysis = (len(self.data.get('why_analysis', [])) > 0 or 
                               any(len(causes) > 0 for causes in self.data.get('fishbone_categories', {}).values()) or
                               len(self.data.get('pareto_data', [])) > 0)
                
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
                        missing.append("pelo menos uma ferramenta de análise")
                    
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
    st.markdown("Analise os dados coletados para identificar as causas raiz dos problemas e validar hipóteses.")
    
    # Opções de ferramentas
    tool_options = {
        "statistical_analysis": ("📊", "Análise Estatística"),
        "root_cause_analysis": ("🔍", "Análise de Causa Raiz"),
        "hypothesis_testing": ("🧪", "Teste de Hipóteses"),
        "process_analysis": ("⚙️", "Análise do Processo")
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
        root_cause_analysis = RootCauseAnalysis(manager)
        root_cause_analysis.show()
    
    elif selected_tool == "hypothesis_testing":
        hypothesis_testing = HypothesisTestingTool(manager)
        hypothesis_testing.show()
    
    elif selected_tool == "process_analysis":
        process_analysis = ProcessAnalysisTool(manager)
        process_analysis.show()
    
    # Progresso geral da fase Analyze
    st.divider()
    _show_analyze_progress(manager, tool_options, analyze_data)


class HypothesisTestingTool:
    """Classe para teste de hipóteses com interface melhorada"""
    
    def __init__(self, manager: AnalyzePhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.data = manager.initialize_session_data('hypothesis_testing', {
            'hypotheses': [],
            'tests_performed': []
        })
    
    def show(self):
        """Interface principal do teste de hipóteses"""
        st.markdown("## 🧪 Teste de Hipóteses")
        st.markdown("Valide estatisticamente as hipóteses sobre as causas identificadas na análise de causa raiz.")
        
        # Verificar dados disponíveis
        df = self.manager.get_uploaded_data()
        if df is None:
            self._show_no_data_warning()
            return
        
        # Status da ferramenta
        self._show_status()
        
        # Interface principal
        tab1, tab2, tab3 = st.tabs([
            "📝 Formulação de Hipóteses",
            "🧪 Execução de Testes",
            "📊 Resultados e Conclusões"
        ])
        
        with tab1:
            self._show_hypothesis_formulation()
        
        with tab2:
            self._show_hypothesis_testing(df)
        
        with tab3:
            self._show_results_summary()
        
        # Botões de ação
        self._show_action_buttons()
    
    def _show_no_data_warning(self):
        """Aviso quando não há dados"""
        st.warning("⚠️ **Dados não encontrados**")
        st.info("Carregue os dados na fase **Measure** para realizar testes de hipóteses.")
        
        if st.button("📊 Ir para Measure", key=f"goto_measure_hyp_{self.project_id}"):
            st.session_state['navigate_to'] = 'measure'
            st.rerun()
    
    def _show_status(self):
        """Status da ferramenta"""
        if self.manager.is_tool_completed('hypothesis_testing'):
            st.success("✅ **Teste de hipóteses concluído**")
        else:
            st.info("⏳ **Teste em desenvolvimento**")
    
    def _show_hypothesis_formulation(self):
        """Formulação de hipóteses"""
        st.markdown("### 📝 Formulação de Hipóteses")
        st.markdown("Defina hipóteses claras baseadas nas causas identificadas na análise de causa raiz.")
        
        # Adicionar nova hipótese
        with st.expander("➕ Adicionar Nova Hipótese"):
            col1, col2 = st.columns(2)
            
            with col1:
                h0 = st.text_area(
                    "Hipótese Nula (H₀):",
                    placeholder="Ex: A média do processo é igual a 50",
                    height=80,
                    key=f"new_h0_{self.project_id}"
                )
            
            with col2:
                h1 = st.text_area(
                    "Hipótese Alternativa (H₁):",
                    placeholder="Ex: A média do processo é diferente de 50",
                    height=80,
                    key=f"new_h1_{self.project_id}"
                )
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                alpha = st.selectbox(
                    "Nível de Significância (α):",
                    [0.01, 0.05, 0.10],
                    index=1,
                    key=f"new_alpha_{self.project_id}"
                )
            
            with col4:
                test_type = st.selectbox(
                    "Tipo de Teste:",
                    ["Teste t (1 amostra)", "Teste t (2 amostras)", "ANOVA", "Qui-quadrado", "Mann-Whitney"],
                    key=f"new_test_type_{self.project_id}"
                )
            
            with col5:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("➕ Adicionar Hipótese", key=f"add_hypothesis_{self.project_id}"):
                    if h0.strip() and h1.strip():
                        self.data['hypotheses'].append({
                            'id': len(self.data['hypotheses']) + 1,
                            'h0': h0.strip(),
                            'h1': h1.strip(),
                            'alpha': alpha,
                            'test_type': test_type,
                            'status': 'Não testada',
                            'created_at': datetime.now().isoformat()
                        })
                        st.rerun()
        
        # Mostrar hipóteses existentes
        if self.data['hypotheses']:
            st.markdown("#### 📋 Hipóteses Definidas")
            
            for i, hypothesis in enumerate(self.data['hypotheses']):
                with st.expander(f"**Hipótese {hypothesis['id']}** - {hypothesis['status']}"):
                    self._show_hypothesis_item(i, hypothesis)
    
    def _show_hypothesis_item(self, index: int, hypothesis: Dict):
        """Mostra item individual de hipótese"""
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            h0_edit = st.text_area(
                "H₀:",
                value=hypothesis['h0'],
                height=60,
                key=f"edit_h0_{index}_{self.project_id}"
            )
            
            h1_edit = st.text_area(
                "H₁:",
                value=hypothesis['h1'],
                height=60,
                key=f"edit_h1_{index}_{self.project_id}"
            )
        
        with col2:
            alpha_edit = st.selectbox(
                "α:",
                [0.01, 0.05, 0.10],
                index=[0.01, 0.05, 0.10].index(hypothesis['alpha']),
                key=f"edit_alpha_{index}_{self.project_id}"
            )
            
            test_type_edit = st.selectbox(
                "Tipo de Teste:",
                ["Teste t (1 amostra)", "Teste t (2 amostras)", "ANOVA", "Qui-quadrado", "Mann-Whitney"],
                index=["Teste t (1 amostra)", "Teste t (2 amostras)", "ANOVA", "Qui-quadrado", "Mann-Whitney"].index(hypothesis['test_type']),
                key=f"edit_test_type_{index}_{self.project_id}"
            )
            
            # Status
            status_color = {
                'Não testada': 'info',
                'Testada': 'success',
                'Rejeitada': 'error',
                'Não rejeitada': 'success'
            }
            
            status = hypothesis.get('status', 'Não testada')
            getattr(st, status_color.get(status, 'info'))(f"**Status:** {status}")
        
        with col3:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("🗑️ Remover", key=f"remove_hypothesis_{index}_{self.project_id}"):
                self.data['hypotheses'].pop(index)
                st.rerun()
        
        # Atualizar dados
        self.data['hypotheses'][index].update({
            'h0': h0_edit,
            'h1': h1_edit,
            'alpha': alpha_edit,
            'test_type': test_type_edit
        })
    
    def _show_hypothesis_testing(self, df: pd.DataFrame):
        """Interface para execução de testes"""
        st.markdown("### 🧪 Execução de Testes")
        
        if not self.data['hypotheses']:
            st.info("💡 Primeiro defina as hipóteses na aba anterior")
            return
        
        # Seletor de hipótese para testar
        hypothesis_options = [
            f"Hipótese {h['id']}: {h['h0'][:50]}..." if len(h['h0']) > 50 else f"Hipótese {h['id']}: {h['h0']}"
            for h in self.data['hypotheses']
        ]
        
        selected_hyp_idx = st.selectbox(
            "Selecione a hipótese para testar:",
            range(len(hypothesis_options)),
            format_func=lambda x: hypothesis_options[x],
            key=f"select_hypothesis_{self.project_id}"
        )
        
        selected_hypothesis = self.data['hypotheses'][selected_hyp_idx]
        
        # Mostrar detalhes da hipótese selecionada
        st.markdown("#### 📋 Hipótese Selecionada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**H₀:** {selected_hypothesis['h0']}")
        
        with col2:
            st.info(f"**H₁:** {selected_hypothesis['h1']}")
        
        # Interface específica baseada no tipo de teste
        test_type = selected_hypothesis['test_type']
        
        if test_type == "Teste t (1 amostra)":
            self._execute_one_sample_ttest(df, selected_hypothesis, selected_hyp_idx)
        elif test_type == "Teste t (2 amostras)":
            self._execute_two_sample_ttest(df, selected_hypothesis, selected_hyp_idx)
        elif test_type == "ANOVA":
            self._execute_anova_test(df, selected_hypothesis, selected_hyp_idx)
        elif test_type == "Mann-Whitney":
            self._execute_mannwhitney_test(df, selected_hypothesis, selected_hyp_idx)
        else:
            st.info(f"🚧 {test_type} será implementado em breve")
    
    def _execute_one_sample_ttest(self, df: pd.DataFrame, hypothesis: Dict, hyp_index: int):
        """Executa teste t para uma amostra"""
        st.markdown("#### 📊 Configuração do Teste t (1 amostra)")
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_columns:
            st.error("❌ Nenhuma coluna numérica encontrada")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            test_variable = st.selectbox(
                "Variável a testar:",
                numeric_columns,
                key=f"t1_var_{hyp_index}_{self.project_id}"
            )
        
        with col2:
            mu0 = st.number_input(
                "Valor de referência (μ₀):",
                value=0.0,
                key=f"t1_mu0_{hyp_index}_{self.project_id}"
            )
        
        if st.button(f"🧪 Executar Teste", key=f"run_t1_{hyp_index}_{self.project_id}"):
            data_test = df[test_variable].dropna()
            
            if len(data_test) == 0:
                st.error("❌ Nenhum dado válido encontrado")
                return
            
            try:
                # Executar teste
                t_stat, p_value = stats.ttest_1samp(data_test, mu0)
                
                # Salvar resultado
                test_result = {
                    'hypothesis_id': hypothesis['id'],
                    'test_type': 'Teste t (1 amostra)',
                    'variable': test_variable,
                    'mu0': mu0,
                    'sample_size': len(data_test),
                    'sample_mean': data_test.mean(),
                    'sample_std': data_test.std(),
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'alpha': hypothesis['alpha'],
                    'conclusion': 'Rejeitar H₀' if p_value < hypothesis['alpha'] else 'Não rejeitar H₀',
                    'executed_at': datetime.now().isoformat()
                }
                
                self.data['tests_performed'].append(test_result)
                
                # Atualizar status da hipótese
                self.data['hypotheses'][hyp_index]['status'] = 'Testada'
                
                # Mostrar resultados
                self._show_test_results(test_result)
                
            except Exception as e:
                st.error(f"❌ Erro na execução do teste: {str(e)}")
    
    def _execute_two_sample_ttest(self, df: pd.DataFrame, hypothesis: Dict, hyp_index: int):
        """Executa teste t para duas amostras"""
        st.markdown("#### 📊 Configuração do Teste t (2 amostras)")
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        if not numeric_columns:
            st.error("❌ Nenhuma coluna numérica encontrada")
            return
        
        # Escolher abordagem
        approach = st.radio(
            "Abordagem:",
            ["Duas variáveis numéricas", "Uma variável por grupos"],
            key=f"t2_approach_{hyp_index}_{self.project_id}"
        )
        
        if approach == "Duas variáveis numéricas":
            col1, col2 = st.columns(2)
            
            with col1:
                var1 = st.selectbox(
                    "Variável 1:",
                    numeric_columns,
                    key=f"t2_var1_{hyp_index}_{self.project_id}"
                )
            
            with col2:
                var2_options = [col for col in numeric_columns if col != var1]
                if var2_options:
                    var2 = st.selectbox(
                        "Variável 2:",
                        var2_options,
                        key=f"t2_var2_{hyp_index}_{self.project_id}"
                    )
                    
                    if st.button(f"🧪 Executar Teste", key=f"run_t2_{hyp_index}_{self.project_id}"):
                        self._run_two_var_ttest(df, var1, var2, hypothesis, hyp_index)
        
        else:  # Por grupos
            if not categorical_columns:
                st.warning("⚠️ Nenhuma variável categórica encontrada")
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                response_var = st.selectbox(
                    "Variável Resposta:",
                    numeric_columns,
                    key=f"t2_response_{hyp_index}_{self.project_id}"
                )
            
            with col2:
                group_var = st.selectbox(
                    "Variável de Grupo:",
                    categorical_columns,
                    key=f"t2_group_{hyp_index}_{self.project_id}"
                )
            
            # Selecionar grupos
            unique_groups = df[group_var].dropna().unique()
            selected_groups = st.multiselect(
                "Selecione 2 grupos:",
                unique_groups,
                max_selections=2,
                key=f"t2_groups_{hyp_index}_{self.project_id}"
            )
            
            if len(selected_groups) == 2:
                if st.button(f"🧪 Executar Teste", key=f"run_t2_groups_{hyp_index}_{self.project_id}"):
                    self._run_grouped_ttest(df, response_var, group_var, selected_groups, hypothesis, hyp_index)
    
    def _run_two_var_ttest(self, df: pd.DataFrame, var1: str, var2: str, hypothesis: Dict, hyp_index: int):
        """Executa teste t entre duas variáveis"""
        data1 = df[var1].dropna()
        data2 = df[var2].dropna()
        
        if len(data1) == 0 or len(data2) == 0:
            st.error("❌ Dados insuficientes")
            return
        
        try:
            # Teste de Levene para igualdade de variâncias
            levene_stat, levene_p = stats.levene(data1, data2)
            equal_var = levene_p > 0.05
            
            # Teste t
            t_stat, p_value = stats.ttest_ind(data1, data2, equal_var=equal_var)
            
            # Salvar resultado
            test_result = {
                'hypothesis_id': hypothesis['id'],
                'test_type': 'Teste t (2 amostras)',
                'variables': [var1, var2],
                'sample_sizes': [len(data1), len(data2)],
                'sample_means': [data1.mean(), data2.mean()],
                'sample_stds': [data1.std(), data2.std()],
                'levene_p': levene_p,
                'equal_variances': equal_var,
                't_statistic': t_stat,
                'p_value': p_value,
                'alpha': hypothesis['alpha'],
                'conclusion': 'Rejeitar H₀' if p_value < hypothesis['alpha'] else 'Não rejeitar H₀',
                'executed_at': datetime.now().isoformat()
            }
            
            self.data['tests_performed'].append(test_result)
            self.data['hypotheses'][hyp_index]['status'] = 'Testada'
            
            self._show_test_results(test_result)
            
        except Exception as e:
            st.error(f"❌ Erro no teste: {str(e)}")
    
    def _run_grouped_ttest(self, df: pd.DataFrame, response_var: str, group_var: str, 
                          selected_groups: List[str], hypothesis: Dict, hyp_index: int):
        """Executa teste t por grupos"""
        group1_data = df[df[group_var] == selected_groups[0]][response_var].dropna()
        group2_data = df[df[group_var] == selected_groups[1]][response_var].dropna()
        
        if len(group1_data) == 0 or len(group2_data) == 0:
            st.error("❌ Dados insuficientes nos grupos")
            return
        
        try:
            t_stat, p_value = stats.ttest_ind(group1_data, group2_data)
            
            test_result = {
                'hypothesis_id': hypothesis['id'],
                'test_type': 'Teste t (grupos)',
                'response_variable': response_var,
                'group_variable': group_var,
                'groups': selected_groups,
                'sample_sizes': [len(group1_data), len(group2_data)],
                'sample_means': [group1_data.mean(), group2_data.mean()],
                'sample_stds': [group1_data.std(), group2_data.std()],
                't_statistic': t_stat,
                'p_value': p_value,
                'alpha': hypothesis['alpha'],
                'conclusion': 'Rejeitar H₀' if p_value < hypothesis['alpha'] else 'Não rejeitar H₀',
                'executed_at': datetime.now().isoformat()
            }
            
            self.data['tests_performed'].append(test_result)
            self.data['hypotheses'][hyp_index]['status'] = 'Testada'
            
            self._show_test_results(test_result)
            
        except Exception as e:
            st.error(f"❌ Erro no teste: {str(e)}")
    
    def _execute_anova_test(self, df: pd.DataFrame, hypothesis: Dict, hyp_index: int):
        """Executa teste ANOVA"""
        st.markdown("#### 📊 Configuração da ANOVA")
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        if not categorical_columns:
            st.warning("⚠️ Necessário variável categórica para ANOVA")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            response_var = st.selectbox(
                "Variável Resposta:",
                numeric_columns,
                key=f"anova_response_{hyp_index}_{self.project_id}"
            )
        
        with col2:
            factor_var = st.selectbox(
                "Fator (Categórica):",
                categorical_columns,
                key=f"anova_factor_{hyp_index}_{self.project_id}"
            )
        
        if st.button(f"🧪 Executar ANOVA", key=f"run_anova_{hyp_index}_{self.project_id}"):
            try:
                # Preparar grupos
                groups = []
                group_names = []
                
                for group_name in df[factor_var].dropna().unique():
                    group_data = df[df[factor_var] == group_name][response_var].dropna()
                    if len(group_data) > 0:
                        groups.append(group_data)
                        group_names.append(str(group_name))
                
                if len(groups) < 2:
                    st.error("❌ Necessário pelo menos 2 grupos")
                    return
                
                # ANOVA
                f_stat, p_value = stats.f_oneway(*groups)
                
                test_result = {
                    'hypothesis_id': hypothesis['id'],
                    'test_type': 'ANOVA',
                    'response_variable': response_var,
                    'factor_variable': factor_var,
                    'groups': group_names,
                    'group_sizes': [len(group) for group in groups],
                    'group_means': [group.mean() for group in groups],
                    'f_statistic': f_stat,
                    'p_value': p_value,
                    'alpha': hypothesis['alpha'],
                    'conclusion': 'Rejeitar H₀' if p_value < hypothesis['alpha'] else 'Não rejeitar H₀',
                    'executed_at': datetime.now().isoformat()
                }
                
                self.data['tests_performed'].append(test_result)
                self.data['hypotheses'][hyp_index]['status'] = 'Testada'
                
                self._show_test_results(test_result)
                
            except Exception as e:
                st.error(f"❌ Erro na ANOVA: {str(e)}")
    
    def _execute_mannwhitney_test(self, df: pd.DataFrame, hypothesis: Dict, hyp_index: int):
        """Executa teste de Mann-Whitney U"""
        st.markdown("#### 📊 Configuração do Mann-Whitney U")
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        if not categorical_columns:
            st.warning("⚠️ Necessário variável categórica")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            response_var = st.selectbox(
                "Variável Resposta:",
                numeric_columns,
                key=f"mw_response_{hyp_index}_{self.project_id}"
            )
        
        with col2:
            group_var = st.selectbox(
                "Variável de Grupo:",
                categorical_columns,
                key=f"mw_group_{hyp_index}_{self.project_id}"
            )
        
        # Selecionar grupos
        unique_groups = df[group_var].dropna().unique()
        selected_groups = st.multiselect(
            "Selecione 2 grupos:",
            unique_groups,
            max_selections=2,
            key=f"mw_groups_{hyp_index}_{self.project_id}"
        )
        
        if len(selected_groups) == 2:
            if st.button(f"🧪 Executar Mann-Whitney", key=f"run_mw_{hyp_index}_{self.project_id}"):
                try:
                    group1_data = df[df[group_var] == selected_groups[0]][response_var].dropna()
                    group2_data = df[df[group_var] == selected_groups[1]][response_var].dropna()
                    
                    if len(group1_data) == 0 or len(group2_data) == 0:
                        st.error("❌ Dados insuficientes")
                        return
                    
                    # Mann-Whitney U
                    u_stat, p_value = stats.mannwhitneyu(group1_data, group2_data, alternative='two-sided')
                    
                    test_result = {
                        'hypothesis_id': hypothesis['id'],
                        'test_type': 'Mann-Whitney U',
                        'response_variable': response_var,
                        'group_variable': group_var,
                        'groups': selected_groups,
                        'sample_sizes': [len(group1_data), len(group2_data)],
                        'medians': [group1_data.median(), group2_data.median()],
                        'u_statistic': u_stat,
                        'p_value': p_value,
                        'alpha': hypothesis['alpha'],
                        'conclusion': 'Rejeitar H₀' if p_value < hypothesis['alpha'] else 'Não rejeitar H₀',
                        'executed_at': datetime.now().isoformat()
                    }
                    
                    self.data['tests_performed'].append(test_result)
                    self.data['hypotheses'][hyp_index]['status'] = 'Testada'
                    
                    self._show_test_results(test_result)
                    
                except Exception as e:
                    st.error(f"❌ Erro no teste: {str(e)}")
    
    def _show_test_results(self, result: Dict):
        """Mostra resultados do teste"""
        st.markdown("#### 📊 Resultados do Teste")
        
        # Métricas principais
        if result['test_type'] == 'Teste t (1 amostra)':
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Estatística t", f"{result['t_statistic']:.4f}")
            
            with col2:
                st.metric("p-valor", f"{result['p_value']:.6f}")
            
            with col3:
                st.metric("Média da Amostra", f"{result['sample_mean']:.4f}")
            
            with col4:
                if result['p_value'] < result['alpha']:
                    st.error("❌ Rejeitar H₀")
                else:
                    st.success("✅ Não rejeitar H₀")
        
        elif 'ANOVA' in result['test_type']:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Estatística F", f"{result['f_statistic']:.4f}")
            
            with col2:
                st.metric("p-valor", f"{result['p_value']:.6f}")
            
            with col3:
                if result['p_value'] < result['alpha']:
                    st.error("❌ Diferença significativa")
                else:
                    st.success("✅ Sem diferença significativa")
        
        # Interpretação
        st.markdown("**📋 Interpretação:**")
        
        if result['p_value'] < result['alpha']:
            st.write(f"Com p-valor = {result['p_value']:.6f} < α = {result['alpha']}, "
                    f"rejeitamos H₀ ao nível de {result['alpha']*100}% de significância.")
        else:
            st.write(f"Com p-valor = {result['p_value']:.6f} ≥ α = {result['alpha']}, "
                    f"não rejeitamos H₀ ao nível de {result['alpha']*100}% de significância.")
        
        st.success("✅ Teste executado e resultado salvo!")
    
    def _show_results_summary(self):
        """Resumo de todos os resultados"""
        st.markdown("### 📊 Resultados e Conclusões")
        
        if not self.data['tests_performed']:
            st.info("💡 Nenhum teste executado ainda")
            return
        
        # Resumo geral
        st.markdown("#### 📈 Resumo Geral")
        
        total_tests = len(self.data['tests_performed'])
        rejected_h0 = sum(1 for test in self.data['tests_performed'] if test['conclusion'] == 'Rejeitar H₀')
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Testes", total_tests)
        
        with col2:
            st.metric("H₀ Rejeitadas", rejected_h0)
        
        with col3:
            st.metric("H₀ Não Rejeitadas", total_tests - rejected_h0)
        
        # Tabela de resultados
        st.markdown("#### 📋 Detalhes dos Testes")
        
        results_summary = []
        for test in self.data['tests_performed']:
            results_summary.append({
                'Hipótese': f"H{test['hypothesis_id']}",
                'Tipo de Teste': test['test_type'],
                'p-valor': f"{test['p_value']:.6f}",
                'α': test['alpha'],
                'Conclusão': test['conclusion'],
                'Data': test['executed_at'][:10]
            })
        
        df_results = pd.DataFrame(results_summary)
        st.dataframe(df_results, use_container_width=True)
        
        # Insights e recomendações
        st.markdown("#### 💡 Insights e Recomendações")
        
        insights = []
        
        if rejected_h0 > 0:
            insights.append(f"🔍 **{rejected_h0} hipótese(s) rejeitada(s)** - Evidência estatística encontrada")
        
        if total_tests - rejected_h0 > 0:
            insights.append(f"✅ **{total_tests - rejected_h0} hipótese(s) não rejeitada(s)** - Sem evidência suficiente")
        
        # Análise por tipo de teste
        test_types = {}
        for test in self.data['tests_performed']:
            test_type = test['test_type']
            if test_type not in test_types:
                test_types[test_type] = {'total': 0, 'rejected': 0}
            test_types[test_type]['total'] += 1
            if test['conclusion'] == 'Rejeitar H₀':
                test_types[test_type]['rejected'] += 1
        
        for test_type, counts in test_types.items():
            rejection_rate = (counts['rejected'] / counts['total']) * 100
            insights.append(f"📊 **{test_type}**: {counts['rejected']}/{counts['total']} rejeitadas ({rejection_rate:.1f}%)")
        
        for insight in insights:
            st.write(insight)
        
        # Próximos passos
        st.markdown("#### 🚀 Próximos Passos")
        
        next_steps = [
            "📊 **Revisar hipóteses rejeitadas** - Investigar as causas validadas estatisticamente",
            "🔍 **Analisar hipóteses não rejeitadas** - Considerar coleta de mais dados ou reformulação",
            "💡 **Desenvolver soluções** baseadas nas evidências encontradas",
            "📈 **Planejar implementação** das melhorias na fase Improve",
            "📋 **Documentar aprendizados** para futuras análises"
        ]
        
        for step in next_steps:
            st.write(step)
    
    def _show_action_buttons(self):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Testes", key=f"save_hypothesis_{self.project_id}"):
                success = self.manager.save_tool_data('hypothesis_testing', self.data, False)
                if success:
                    st.success("💾 Testes de hipóteses salvos!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("✅ Finalizar Teste de Hipóteses", key=f"complete_hypothesis_{self.project_id}"):
                if self.data['hypotheses'] and self.data['tests_performed']:
                    success = self.manager.save_tool_data('hypothesis_testing', self.data, True)
                    if success:
                        st.success("✅ Teste de hipóteses finalizado!")
                        st.balloons()
                    else:
                        st.error("❌ Erro ao finalizar")
                else:
                    st.error("❌ Defina hipóteses e execute pelo menos um teste")


class ProcessAnalysisTool:
    """Classe para análise do processo com ferramentas avançadas"""
    
    def __init__(self, manager: AnalyzePhaseManager):
        self.manager = manager
        self.project_id = manager.project_id
        self.data = manager.initialize_session_data('process_analysis', {
            'process_steps': [],
            'bottlenecks': [],
            'cycle_time_analysis': {},
            'value_stream_data': [],
            'waste_analysis': {}
        })
    
    def show(self):
        """Interface principal da análise de processo"""
        st.markdown("## ⚙️ Análise do Processo")
        st.markdown("Analise o processo atual para identificar gargalos, desperdícios e oportunidades de melhoria.")
        
        # Status da ferramenta
        self._show_status()
        
        # Interface principal
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔄 Mapeamento do Processo",
            "⏱️ Análise de Tempo",
            "🚧 Gargalos",
            "🗑️ Análise de Desperdícios",
            "📊 Relatório"
        ])
        
        with tab1:
            self._show_process_mapping()
        
        with tab2:
            self._show_time_analysis()
        
        with tab3:
            self._show_bottleneck_analysis()
        
        with tab4:
            self._show_waste_analysis()
        
        with tab5:
            self._show_process_report()
        
        # Botões de ação
        self._show_action_buttons()
    
    def _show_status(self):
        """Status da ferramenta"""
        if self.manager.is_tool_completed('process_analysis'):
            st.success("✅ **Análise do processo concluída**")
        else:
            st.info("⏳ **Análise em desenvolvimento**")
    
    def _show_process_mapping(self):
        """Mapeamento do fluxo do processo"""
        st.markdown("### 🔄 Mapeamento do Fluxo do Processo")
        st.markdown("Mapeie todas as etapas do processo para identificar oportunidades de melhoria.")
        
        # Adicionar nova etapa
        with st.expander("➕ Adicionar Nova Etapa"):
            self._show_add_step_interface()
        
        # Mostrar etapas existentes
        if self.data['process_steps']:
            self._show_existing_steps()
            self._show_process_summary()
            self._show_process_visualization()
    
    def _show_add_step_interface(self):
        """Interface para adicionar nova etapa"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            step_name = st.text_input(
                "Nome da Etapa:",
                key=f"step_name_{self.project_id}",
                placeholder="Ex: Inspeção de qualidade"
            )
            
            step_type = st.selectbox(
                "Tipo de Atividade:",
                ["Operação", "Inspeção", "Transporte", "Espera", "Estoque", "Retrabalho"],
                key=f"step_type_{self.project_id}"
            )
        
        with col2:
            step_time = st.number_input(
                "Tempo (minutos):",
                min_value=0.0,
                value=0.0,
                step=0.1,
                key=f"step_time_{self.project_id}"
            )
            
            step_resources = st.text_input(
                "Recursos Necessários:",
                key=f"step_resources_{self.project_id}",
                placeholder="Ex: 1 operador, equipamento X"
            )
        
        with col3:
            step_value = st.selectbox(
                "Agrega Valor?",
                ["Sim", "Não", "Necessário"],
                key=f"step_value_{self.project_id}",
                help="Sim: Agrega valor ao cliente | Não: Desperdício | Necessário: Não agrega valor mas é obrigatório"
            )
            
            step_cost = st.number_input(
                "Custo Estimado (R$):",
                min_value=0.0,
                value=0.0,
                key=f"step_cost_{self.project_id}"
            )
        
        # Campos adicionais
        step_description = st.text_area(
            "Descrição Detalhada:",
            key=f"step_description_{self.project_id}",
            placeholder="Descreva o que acontece nesta etapa..."
        )
        
        col4, col5 = st.columns(2)
        
        with col4:
            step_problems = st.text_area(
                "Problemas Identificados:",
                key=f"step_problems_{self.project_id}",
                placeholder="Quais problemas ocorrem nesta etapa?"
            )
        
        with col5:
            step_frequency = st.selectbox(
                "Frequência de Problemas:",
                ["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"],
                key=f"step_frequency_{self.project_id}"
            )
        
        if st.button("➕ Adicionar Etapa", key=f"add_step_{self.project_id}"):
            if step_name.strip():
                new_step = {
                    'id': len(self.data['process_steps']) + 1,
                    'name': step_name.strip(),
                    'type': step_type,
                    'time': step_time,
                    'cost': step_cost,
                    'resources': step_resources,
                    'value_add': step_value,
                    'description': step_description,
                    'problems': step_problems,
                    'problem_frequency': step_frequency,
                    'order': len(self.data['process_steps']) + 1
                }
                
                self.data['process_steps'].append(new_step)
                st.success(f"✅ Etapa '{step_name}' adicionada!")
                st.rerun()
            else:
                st.error("❌ Nome da etapa é obrigatório")
    
    def _show_existing_steps(self):
        """Mostra etapas existentes"""
        st.markdown("#### 📋 Etapas Mapeadas")
        
        for i, step in enumerate(self.data['process_steps']):
            # Determinar cor baseada no tipo de atividade
            type_colors = {
                'Operação': 'success',
                'Inspeção': 'info',
                'Transporte': 'warning',
                'Espera': 'error',
                'Estoque': 'error',
                'Retrabalho': 'error'
            }
            
            color = type_colors.get(step['type'], 'info')
            
            with st.expander(f"**{step['order']}. {step['name']}** ({step['type']}) - {step['time']} min"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Tipo:** {step['type']}")
                    st.write(f"**Tempo:** {step['time']} minutos")
                    st.write(f"**Custo:** R$ {step['cost']:.2f}")
                    st.write(f"**Agrega Valor:** {step['value_add']}")
                
                with col2:
                    st.write(f"**Recursos:** {step['resources']}")
                    if step['description']:
                        st.write(f"**Descrição:** {step['description']}")
                    if step['problems']:
                        st.write(f"**Problemas:** {step['problems']}")
                        st.write(f"**Frequência:** {step['problem_frequency']}")
                
                with col3:
                    # Botões de ação
                    if st.button("📝 Editar", key=f"edit_step_{i}_{self.project_id}"):
                        st.info("💡 Funcionalidade de edição será implementada")
                    
                    if st.button("🗑️ Remover", key=f"remove_step_{i}_{self.project_id}"):
                        self.data['process_steps'].pop(i)
                        # Reordenar
                        for j, remaining_step in enumerate(self.data['process_steps']):
                            remaining_step['order'] = j + 1
                        st.rerun()
                    
                    if st.button("⬆️ Subir", key=f"move_up_{i}_{self.project_id}"):
                        if i > 0:
                            self.data['process_steps'][i], self.data['process_steps'][i-1] = \
                                self.data['process_steps'][i-1], self.data['process_steps'][i]
                            # Atualizar ordem
                            for j, step_item in enumerate(self.data['process_steps']):
                                step_item['order'] = j + 1
                            st.rerun()
                    
                    if st.button("⬇️ Descer", key=f"move_down_{i}_{self.project_id}"):
                        if i < len(self.data['process_steps']) - 1:
                            self.data['process_steps'][i], self.data['process_steps'][i+1] = \
                                self.data['process_steps'][i+1], self.data['process_steps'][i]
                            # Atualizar ordem
                            for j, step_item in enumerate(self.data['process_steps']):
                                step_item['order'] = j + 1
                            st.rerun()
    
    def _show_process_summary(self):
        """Resumo do processo mapeado"""
        st.markdown("#### 📊 Resumo do Processo")
        
        # Calcular métricas
        total_time = sum(step['time'] for step in self.data['process_steps'])
        total_cost = sum(step['cost'] for step in self.data['process_steps'])
        
        value_add_time = sum(step['time'] for step in self.data['process_steps'] if step['value_add'] == 'Sim')
        necessary_time = sum(step['time'] for step in self.data['process_steps'] if step['value_add'] == 'Necessário')
        waste_time = sum(step['time'] for step in self.data['process_steps'] if step['value_add'] == 'Não')
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Etapas", len(self.data['process_steps']))
        
        with col2:
            st.metric("Tempo Total", f"{total_time:.1f} min")
        
        with col3:
            st.metric("Custo Total", f"R$ {total_cost:.2f}")
        
        with col4:
            efficiency = (value_add_time / total_time * 100) if total_time > 0 else 0
            st.metric("Eficiência (VA)", f"{efficiency:.1f}%")
        
        # Análise de valor agregado
        st.markdown("#### 💎 Análise de Valor Agregado")
        
        col5, col6, col7 = st.columns(3)
        
        with col5:
            st.metric("Tempo que Agrega Valor", f"{value_add_time:.1f} min")
            va_steps = sum(1 for step in self.data['process_steps'] if step['value_add'] == 'Sim')
            st.caption(f"{va_steps} etapas")
        
        with col6:
            st.metric("Tempo Necessário", f"{necessary_time:.1f} min")
            nec_steps = sum(1 for step in self.data['process_steps'] if step['value_add'] == 'Necessário')
            st.caption(f"{nec_steps} etapas")
        
        with col7:
            st.metric("Desperdício", f"{waste_time:.1f} min")
            waste_steps = sum(1 for step in self.data['process_steps'] if step['value_add'] == 'Não')
            st.caption(f"{waste_steps} etapas")
        
        # Análise por tipo de atividade
        type_analysis = {}
        for step in self.data['process_steps']:
            step_type = step['type']
            if step_type not in type_analysis:
                type_analysis[step_type] = {'count': 0, 'time': 0, 'cost': 0}
            
            type_analysis[step_type]['count'] += 1
            type_analysis[step_type]['time'] += step['time']
            type_analysis[step_type]['cost'] += step['cost']
        
        if type_analysis:
            st.markdown("#### 📊 Análise por Tipo de Atividade")
            
            type_df = pd.DataFrame([
                {
                    'Tipo': tipo,
                    'Quantidade': dados['count'],
                    'Tempo Total (min)': dados['time'],
                    'Custo Total (R$)': dados['cost'],
                    '% do Tempo': f"{(dados['time']/total_time*100):.1f}%" if total_time > 0 else "0%"
                }
                for tipo, dados in type_analysis.items()
            ])
            
            st.dataframe(type_df, use_container_width=True)
    
    def _show_process_visualization(self):
        """Visualizações do processo"""
        st.markdown("#### 📈 Visualizações do Processo")
        
        # Gráfico de tempo por etapa
        col1, col2 = st.columns(2)
        
        with col1:
            step_names = [f"{step['order']}. {step['name'][:20]}..." if len(step['name']) > 20 
                         else f"{step['order']}. {step['name']}" for step in self.data['process_steps']]
            step_times = [step['time'] for step in self.data['process_steps']]
            
            fig_time = px.bar(
                x=step_names,
                y=step_times,
                title="Tempo por Etapa do Processo",
                labels={'x': 'Etapas', 'y': 'Tempo (min)'}
            )
            fig_time.update_xaxes(tickangle=45)
            fig_time.update_layout(height=400)
            st.plotly_chart(fig_time, use_container_width=True)
        
        with col2:
            # Gráfico de pizza - valor agregado
            if self.data['process_steps']:
                value_add_time = sum(step['time'] for step in self.data['process_steps'] if step['value_add'] == 'Sim')
                necessary_time = sum(step['time'] for step in self.data['process_steps'] if step['value_add'] == 'Necessário')
                waste_time = sum(step['time'] for step in self.data['process_steps'] if step['value_add'] == 'Não')
                
                if value_add_time + necessary_time + waste_time > 0:
                    fig_pie = px.pie(
                        values=[value_add_time, necessary_time, waste_time],
                        names=['Agrega Valor', 'Necessário', 'Desperdício'],
                        title="Distribuição do Tempo por Tipo",
                        color_discrete_sequence=['green', 'yellow', 'red']
                    )
                    fig_pie.update_layout(height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)
    
    def _show_time_analysis(self):
        """Análise detalhada de tempos"""
        st.markdown("### ⏱️ Análise de Tempo de Ciclo")
        
        # Verificar se há dados de tempo nos dados carregados
        df = self.manager.get_uploaded_data()
        
        if df is not None:
            self._show_data_time_analysis(df)
        
        # Análise baseada no processo mapeado
        if self.data['process_steps']:
            self._show_mapped_process_time_analysis()
    
    def _show_data_time_analysis(self, df: pd.DataFrame):
        """Análise de tempo baseada nos dados carregados"""
        st.markdown("#### 📊 Análise de Dados de Tempo")
        
        # Procurar colunas de tempo
        time_columns = [col for col in df.select_dtypes(include=[np.number]).columns 
                       if any(keyword in col.lower() for keyword in ['time', 'tempo', 'cycle', 'ciclo', 'duration', 'duracao'])]
        
        if not time_columns:
            st.info("💡 Nenhuma coluna de tempo identificada nos dados")
            return
        
        selected_time_col = st.selectbox(
            "Selecione a coluna de tempo para análise:",
            time_columns,
            key=f"time_col_analysis_{self.project_id}"
        )
        
        if selected_time_col:
            time_data = df[selected_time_col].dropna()
            
            if len(time_data) == 0:
                st.warning("⚠️ Nenhum dado de tempo válido encontrado")
                return
            
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
                fig_hist = px.histogram(
                    x=time_data,
                    nbins=30,
                    title=f"Distribuição dos Tempos - {selected_time_col}"
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col_b:
                # Gráfico de controle
                fig_control = px.line(
                    x=range(len(time_data)),
                    y=time_data,
                    title=f"Gráfico de Controle - {selected_time_col}"
                )
                
                # Limites de controle
                mean_time = time_data.mean()
                std_time = time_data.std()
                
                fig_control.add_hline(y=mean_time, line_dash="solid", line_color="green", annotation_text="Média")
                fig_control.add_hline(y=mean_time + 3*std_time, line_dash="dash", line_color="red", annotation_text="UCL")
                fig_control.add_hline(y=mean_time - 3*std_time, line_dash="dash", line_color="red", annotation_text="LCL")
                
                st.plotly_chart(fig_control, use_container_width=True)
            
            # Análise de estabilidade
            st.markdown("#### 📊 Análise de Estabilidade do Processo")
            
            # Pontos fora de controle
            ucl = mean_time + 3 * std_time
            lcl = max(0, mean_time - 3 * std_time)  # Tempo não pode ser negativo
            
            out_of_control = time_data[(time_data > ucl) | (time_data < lcl)]
            
            col_stab1, col_stab2, col_stab3 = st.columns(3)
            
            with col_stab1:
                st.metric("Pontos Fora de Controle", len(out_of_control))
            
            with col_stab2:
                stability_pct = (1 - len(out_of_control) / len(time_data)) * 100
                st.metric("Estabilidade", f"{stability_pct:.1f}%")
            
            with col_stab3:
                if cv < 15:
                    st.success("Baixa Variabilidade")
                elif cv < 30:
                    st.warning("Variabilidade Moderada")
                else:
                    st.error("Alta Variabilidade")
    
    def _show_mapped_process_time_analysis(self):
        """Análise de tempo do processo mapeado"""
        st.markdown("#### ⚙️ Análise do Processo Mapeado")
        
        # Análise de gargalos por tempo
        sorted_steps = sorted(self.data['process_steps'], key=lambda x: x['time'], reverse=True)
        
        st.markdown("**🔍 Etapas com Maior Tempo (Top 5):**")
        
        for i, step in enumerate(sorted_steps[:5], 1):
            total_time = sum(s['time'] for s in self.data['process_steps'])
            percentage = (step['time'] / total_time * 100) if total_time > 0 else 0
            
            col_step1, col_step2, col_step3 = st.columns([2, 1, 1])
            
            with col_step1:
                st.write(f"**{i}. {step['name']}**")
            
            with col_step2:
                st.write(f"{step['time']:.1f} min")
            
            with col_step3:
                st.write(f"{percentage:.1f}%")
        
        # Análise de tempo cumulativo
        cumulative_times = []
        cumulative_sum = 0
        
        for step in self.data['process_steps']:
            cumulative_sum += step['time']
            cumulative_times.append(cumulative_sum)
        
        if len(cumulative_times) > 1:
            fig_cumulative = go.Figure()
            
            fig_cumulative.add_trace(go.Scatter(
                x=[f"{step['order']}. {step['name'][:15]}..." if len(step['name']) > 15 
                   else f"{step['order']}. {step['name']}" for step in self.data['process_steps']],
                y=cumulative_times,
                mode='lines+markers',
                name='Tempo Cumulativo'
            ))
            
            fig_cumulative.update_layout(
                title="Tempo Cumulativo do Processo",
                xaxis_title="Etapas",
                yaxis_title="Tempo Cumulativo (min)",
                height=400
            )
            
            fig_cumulative.update_xaxes(tickangle=45)
            
            st.plotly_chart(fig_cumulative, use_container_width=True)
    
    def _show_bottleneck_analysis(self):
        """Análise de gargalos"""
        st.markdown("### 🚧 Análise de Gargalos")
        st.markdown("Identifique e analise os gargalos que limitam a capacidade do processo.")
        
        # Identificação automática de gargalos baseada no processo mapeado
        if self.data['process_steps']:
            self._show_automatic_bottleneck_detection()
        
        # Interface para adicionar gargalos manualmente
        self._show_manual_bottleneck_entry()
        
        # Análise de gargalos identificados
        if self.data.get('bottlenecks'):
            self._show_bottleneck_analysis_results()
    
    def _show_automatic_bottleneck_detection(self):
        """Detecção automática de gargalos"""
        st.markdown("#### 🔍 Detecção Automática de Gargalos")
        
        # Analisar etapas com maior tempo
        sorted_by_time = sorted(self.data['process_steps'], key=lambda x: x['time'], reverse=True)
        total_time = sum(step['time'] for step in self.data['process_steps'])
        
        # Critérios para identificar gargalos
        potential_bottlenecks = []
        
        for step in sorted_by_time:
            time_percentage = (step['time'] / total_time * 100) if total_time > 0 else 0
            
            # Critérios: tempo > 20% do total OU problemas frequentes OU não agrega valor
            is_bottleneck = (
                time_percentage > 20 or
                step.get('problem_frequency') in ['Frequentemente', 'Sempre'] or
                (step['value_add'] == 'Não' and step['time'] > 0)
            )
            
            if is_bottleneck:
                potential_bottlenecks.append({
                    'step': step,
                    'time_percentage': time_percentage,
                    'reasons': []
                })
                
                # Identificar razões
                if time_percentage > 20:
                    potential_bottlenecks[-1]['reasons'].append(f"Alto tempo ({time_percentage:.1f}% do total)")
                
                if step.get('problem_frequency') in ['Frequentemente', 'Sempre']:
                    potential_bottlenecks[-1]['reasons'].append(f"Problemas {step['problem_frequency'].lower()}")
                
                if step['value_add'] == 'Não':
                    potential_bottlenecks[-1]['reasons'].append("Não agrega valor (desperdício)")
        
        if potential_bottlenecks:
            st.success(f"🔍 {len(potential_bottlenecks)} gargalo(s) potencial(is) detectado(s)")
            
            for i, bottleneck in enumerate(potential_bottlenecks, 1):
                step = bottleneck['step']
                reasons = bottleneck['reasons']
                
                with st.expander(f"**Gargalo {i}: {step['name']}** - {step['time']} min"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Tempo:** {step['time']} min ({bottleneck['time_percentage']:.1f}% do total)")
                        st.write(f"**Tipo:** {step['type']}")
                        st.write(f"**Agrega Valor:** {step['value_add']}")
                    
                    with col2:
                        st.write("**Razões para ser gargalo:**")
                        for reason in reasons:
                            st.write(f"• {reason}")
                        
                        if step.get('problems'):
                            st.write(f"**Problemas:** {step['problems']}")
                    
                    # Botão para adicionar aos gargalos manuais
                    if st.button(f"➕ Adicionar aos Gargalos", key=f"add_auto_bottleneck_{i}_{self.project_id}"):
                        # Verificar se já existe
                        existing = any(
                            b.get('name') == step['name'] for b in self.data.get('bottlenecks', [])
                        )
                        
                        if not existing:
                            if 'bottlenecks' not in self.data:
                                self.data['bottlenecks'] = []
                            
                            self.data['bottlenecks'].append({
                                'name': step['name'],
                                'location': f"Etapa {step['order']}",
                                'impact': 'Alto' if bottleneck['time_percentage'] > 30 else 'Médio',
                                'frequency': step.get('problem_frequency', 'Às vezes'),
                                'description': f"Gargalo detectado automaticamente. {'; '.join(reasons)}",
                                'time': step['time'],
                                'type': 'Automático'
                            })
                            
                            st.success("✅ Gargalo adicionado!")
                            st.rerun()
                        else:
                            st.info("💡 Este gargalo já foi adicionado")
        else:
            st.info("✅ Nenhum gargalo crítico detectado automaticamente")
    
    def _show_manual_bottleneck_entry(self):
        """Interface para adicionar gargalos manualmente"""
        st.markdown("#### ➕ Adicionar Gargalos Manualmente")
        
        with st.expander("Adicionar Novo Gargalo"):
            col1, col2 = st.columns(2)
            
            with col1:
                bottleneck_name = st.text_input(
                    "Nome do Gargalo:",
                    key=f"bottleneck_name_{self.project_id}",
                    placeholder="Ex: Aprovação gerencial"
                )
                
                bottleneck_location = st.text_input(
                    "Localização/Etapa:",
                    key=f"bottleneck_location_{self.project_id}",
                    placeholder="Ex: Entre etapas 3 e 4"
                )
            
            with col2:
                bottleneck_impact = st.selectbox(
                    "Nível de Impacto:",
                    ["Alto", "Médio", "Baixo"],
                    key=f"bottleneck_impact_{self.project_id}"
                )
                
                bottleneck_frequency = st.selectbox(
                    "Frequência:",
                    ["Sempre", "Frequentemente", "Às vezes", "Raramente"],
                    key=f"bottleneck_frequency_{self.project_id}"
                )
            
            bottleneck_description = st.text_area(
                "Descrição Detalhada:",
                key=f"bottleneck_description_{self.project_id}",
                placeholder="Descreva o gargalo, suas causas e impactos..."
            )
            
            col3, col4 = st.columns(2)
            
            with col3:
                bottleneck_time = st.number_input(
                    "Tempo de Atraso (min):",
                    min_value=0.0,
                    value=0.0,
                    key=f"bottleneck_time_{self.project_id}"
                )
            
            with col4:
                bottleneck_cost = st.number_input(
                    "Custo do Impacto (R$):",
                    min_value=0.0,
                    value=0.0,
                    key=f"bottleneck_cost_{self.project_id}"
                )
            
            if st.button("➕ Adicionar Gargalo", key=f"add_manual_bottleneck_{self.project_id}"):
                if bottleneck_name.strip():
                    if 'bottlenecks' not in self.data:
                        self.data['bottlenecks'] = []
                    
                    self.data['bottlenecks'].append({
                        'name': bottleneck_name.strip(),
                        'location': bottleneck_location,
                        'impact': bottleneck_impact,
                        'frequency': bottleneck_frequency,
                        'description': bottleneck_description,
                        'time': bottleneck_time,
                        'cost': bottleneck_cost,
                        'type': 'Manual'
                    })
                    
                    st.success(f"✅ Gargalo '{bottleneck_name}' adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Nome do gargalo é obrigatório")
    
    def _show_bottleneck_analysis_results(self):
        """Análise dos gargalos identificados"""
        st.markdown("#### 📊 Análise dos Gargalos Identificados")
        
        # Lista de gargalos
        for i, bottleneck in enumerate(self.data['bottlenecks']):
            with st.expander(f"**{bottleneck['name']}** - {bottleneck['impact']} Impacto"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Localização:** {bottleneck['location']}")
                    st.write(f"**Impacto:** {bottleneck['impact']}")
                    st.write(f"**Frequência:** {bottleneck['frequency']}")
                    st.write(f"**Tipo:** {bottleneck.get('type', 'Manual')}")
                
                with col2:
                    if bottleneck.get('time', 0) > 0:
                        st.write(f"**Tempo de Atraso:** {bottleneck['time']} min")
                    if bottleneck.get('cost', 0) > 0:
                        st.write(f"**Custo do Impacto:** R$ {bottleneck['cost']:.2f}")
                    if bottleneck['description']:
                        st.write(f"**Descrição:** {bottleneck['description']}")
                
                with col3:
                    if st.button("🗑️ Remover", key=f"remove_bottleneck_{i}_{self.project_id}"):
                        self.data['bottlenecks'].pop(i)
                        st.rerun()
        
        # Matriz de priorização
        if len(self.data['bottlenecks']) > 1:
            self._show_bottleneck_prioritization()
    
    def _show_bottleneck_prioritization(self):
        """Matriz de priorização de gargalos"""
        st.markdown("#### 🎯 Matriz de Priorização de Gargalos")
        
        # Mapear valores para scores
        impact_map = {"Alto": 3, "Médio": 2, "Baixo": 1}
        freq_map = {"Sempre": 4, "Frequentemente": 3, "Às vezes": 2, "Raramente": 1}
        
        bottleneck_names = [b['name'] for b in self.data['bottlenecks']]
        impact_scores = [impact_map[b['impact']] for b in self.data['bottlenecks']]
        freq_scores = [freq_map[b['frequency']] for b in self.data['bottlenecks']]
        
        # Gráfico de dispersão
        fig_matrix = px.scatter(
            x=freq_scores,
            y=impact_scores,
            text=bottleneck_names,
            labels={'x': 'Frequência', 'y': 'Impacto'},
            title="Matriz de Priorização de Gargalos"
        )
        
        fig_matrix.update_traces(textposition="top center", marker=dict(size=15))
        fig_matrix.update_xaxes(
            range=[0.5, 4.5],
            tickvals=[1, 2, 3, 4],
            ticktext=['Raramente', 'Às vezes', 'Frequentemente', 'Sempre']
        )
        fig_matrix.update_yaxes(
            range=[0.5, 3.5],
            tickvals=[1, 2, 3],
            ticktext=['Baixo', 'Médio', 'Alto']
        )
        
        # Adicionar linhas de referência
        fig_matrix.add_hline(y=2.5, line_dash="dash", line_color="orange", opacity=0.5)
        fig_matrix.add_vline(x=2.5, line_dash="dash", line_color="orange", opacity=0.5)
        
        fig_matrix.update_layout(height=500)
        st.plotly_chart(fig_matrix, use_container_width=True)
        
        # Classificação por prioridade
        priority_bottlenecks = []
        
        for i, bottleneck in enumerate(self.data['bottlenecks']):
            priority_score = impact_scores[i] * freq_scores[i]
            
            if impact_scores[i] >= 3 and freq_scores[i] >= 3:
                priority = "Crítica"
            elif impact_scores[i] >= 2 and freq_scores[i] >= 2:
                priority = "Alta"
            elif impact_scores[i] >= 2 or freq_scores[i] >= 2:
                priority = "Média"
            else:
                priority = "Baixa"
            
            priority_bottlenecks.append({
                'Nome': bottleneck['name'],
                'Impacto': bottleneck['impact'],
                'Frequência': bottleneck['frequency'],
                'Score': priority_score,
                'Prioridade': priority
            })
        
        # Ordenar por score
        priority_bottlenecks.sort(key=lambda x: x['Score'], reverse=True)
        
        st.markdown("#### 📋 Classificação por Prioridade")
        
        priority_df = pd.DataFrame(priority_bottlenecks)
        
        # Colorir por prioridade
        def color_priority(val):
            if val == 'Crítica':
                return 'background-color: #ffcccc'
            elif val == 'Alta':
                return 'background-color: #ffe6cc'
            elif val == 'Média':
                return 'background-color: #ffffcc'
            else:
                return 'background-color: #e6ffe6'
        
        styled_df = priority_df.style.applymap(color_priority, subset=['Prioridade'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Recomendações
        critical_count = sum(1 for b in priority_bottlenecks if b['Prioridade'] == 'Crítica')
        high_count = sum(1 for b in priority_bottlenecks if b['Prioridade'] == 'Alta')
        
        st.markdown("#### 🎯 Recomendações")
        
        if critical_count > 0:
            st.error(f"🚨 **{critical_count} gargalo(s) crítico(s)** - Ação imediata necessária")
        
        if high_count > 0:
            st.warning(f"⚠️ **{high_count} gargalo(s) de alta prioridade** - Planejar ações prioritárias")
        
        recommendations = [
            "🎯 **Foque nos gargalos críticos e de alta prioridade**",
            "📊 **Monitore os gargalos regularmente** para detectar mudanças",
            "💡 **Desenvolva soluções específicas** para cada gargalo identificado",
            "⚡ **Implemente melhorias rápidas** nos gargalos de maior impacto"
        ]
        
        for rec in recommendations:
            st.write(rec)
    
    def _show_waste_analysis(self):
        """Análise de desperdícios (8 Wastes do Lean)"""
        st.markdown("### 🗑️ Análise de Desperdícios")
        st.markdown("Identifique e categorize os desperdícios usando os 8 tipos do Lean Manufacturing.")
        
        # Os 8 desperdícios do Lean
        waste_types = {
            'Transporte': 'Movimentação desnecessária de materiais ou informações',
            'Estoque': 'Excesso de materiais, informações ou trabalho em processo',
            'Movimento': 'Movimentação desnecessária de pessoas',
            'Espera': 'Tempo perdido aguardando algo',
            'Superprodução': 'Produzir mais do que o necessário',
            'Superprocessamento': 'Processos mais complexos que o necessário',
            'Defeitos': 'Erros que requerem retrabalho ou correção',
            'Talento': 'Subutilização das habilidades e conhecimentos das pessoas'
        }
        
        # Inicializar dados de desperdício
        if 'waste_analysis' not in self.data:
            self.data['waste_analysis'] = {}
        
        # Interface para cada tipo de desperdício
        st.markdown("#### 🔍 Identificação de Desperdícios por Categoria")
        
        total_waste_time = 0
        total_waste_cost = 0
        
        for waste_type, description in waste_types.items():
            with st.expander(f"**{waste_type}** - {description}"):
                self._show_waste_category_analysis(waste_type, description)
                
                # Somar desperdícios identificados
                if waste_type in self.data['waste_analysis']:
                    for waste_item in self.data['waste_analysis'][waste_type]:
                        total_waste_time += waste_item.get('time_impact', 0)
                        total_waste_cost += waste_item.get('cost_impact', 0)
        
        # Resumo geral dos desperdícios
        if total_waste_time > 0 or total_waste_cost > 0:
            self._show_waste_summary(total_waste_time, total_waste_cost)
    
    def _show_waste_category_analysis(self, waste_type: str, description: str):
        """Análise de uma categoria específica de desperdício"""
        if waste_type not in self.data['waste_analysis']:
            self.data['waste_analysis'][waste_type] = []
        
        # Adicionar novo desperdício nesta categoria
        st.markdown(f"**Adicionar {waste_type}:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            waste_name = st.text_input(
                "Nome/Descrição:",
                key=f"waste_name_{waste_type}_{self.project_id}",
                placeholder=f"Descreva o {waste_type.lower()} identificado..."
            )
            
            waste_location = st.text_input(
                "Localização:",
                key=f"waste_location_{waste_type}_{self.project_id}",
                placeholder="Onde ocorre este desperdício?"
            )
        
        with col2:
            waste_frequency = st.selectbox(
                "Frequência:",
                ["Sempre", "Frequentemente", "Às vezes", "Raramente"],
                key=f"waste_frequency_{waste_type}_{self.project_id}"
            )
            
            waste_severity = st.selectbox(
                "Severidade:",
                ["Alta", "Média", "Baixa"],
                key=f"waste_severity_{waste_type}_{self.project_id}"
            )
        
        col3, col4 = st.columns(2)
        
        with col3:
            time_impact = st.number_input(
                "Impacto em Tempo (min/dia):",
                min_value=0.0,
                value=0.0,
                key=f"waste_time_{waste_type}_{self.project_id}"
            )
        
        with col4:
            cost_impact = st.number_input(
                "Impacto em Custo (R$/dia):",
                min_value=0.0,
                value=0.0,
                key=f"waste_cost_{waste_type}_{self.project_id}"
            )
        
        waste_cause = st.text_area(
            "Causa Raiz:",
            key=f"waste_cause_{waste_type}_{self.project_id}",
            placeholder="Qual a causa deste desperdício?"
        )
        
        if st.button(f"➕ Adicionar {waste_type}", key=f"add_waste_{waste_type}_{self.project_id}"):
            if waste_name.strip():
                self.data['waste_analysis'][waste_type].append({
                    'name': waste_name.strip(),
                    'location': waste_location,
                    'frequency': waste_frequency,
                    'severity': waste_severity,
                    'time_impact': time_impact,
                    'cost_impact': cost_impact,
                    'cause': waste_cause,
                    'identified_at': datetime.now().isoformat()
                })
                
                st.success(f"✅ {waste_type} '{waste_name}' adicionado!")
                st.rerun()
        
        # Mostrar desperdícios existentes nesta categoria
        if self.data['waste_analysis'][waste_type]:
            st.markdown(f"**{waste_type}s Identificados:**")
            
            for i, waste_item in enumerate(self.data['waste_analysis'][waste_type]):
                col_w1, col_w2, col_w3 = st.columns([3, 2, 1])
                
                with col_w1:
                    st.write(f"**{waste_item['name']}**")
                    if waste_item['location']:
                        st.write(f"*Local:* {waste_item['location']}")
                    if waste_item['cause']:
                        st.write(f"*Causa:* {waste_item['cause']}")
                
                with col_w2:
                    st.write(f"*Frequência:* {waste_item['frequency']}")
                    st.write(f"*Severidade:* {waste_item['severity']}")
                    if waste_item['time_impact'] > 0:
                        st.write(f"*Tempo:* {waste_item['time_impact']} min/dia")
                    if waste_item['cost_impact'] > 0:
                        st.write(f"*Custo:* R$ {waste_item['cost_impact']:.2f}/dia")
                
                with col_w3:
                    if st.button("🗑️", key=f"remove_waste_{waste_type}_{i}_{self.project_id}"):
                        self.data['waste_analysis'][waste_type].pop(i)
                        st.rerun()
                
                st.divider()
    
    def _show_waste_summary(self, total_time: float, total_cost: float):
        """Resumo geral dos desperdícios"""
        st.markdown("#### 📊 Resumo dos Desperdícios Identificados")
        
        # Métricas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        total_wastes = sum(len(wastes) for wastes in self.data['waste_analysis'].values())
        categories_with_waste = sum(1 for wastes in self.data['waste_analysis'].values() if len(wastes) > 0)
        
        with col1:
            st.metric("Total de Desperdícios", total_wastes)
        
        with col2:
            st.metric("Categorias Afetadas", f"{categories_with_waste}/8")
        
        with col3:
            st.metric("Impacto Tempo/Dia", f"{total_time:.1f} min")
        
        with col4:
            st.metric("Impacto Custo/Dia", f"R$ {total_cost:.2f}")
        
        # Análise por categoria
        category_analysis = []
        
        for waste_type, wastes in self.data['waste_analysis'].items():
            if wastes:
                category_time = sum(w.get('time_impact', 0) for w in wastes)
                category_cost = sum(w.get('cost_impact', 0) for w in wastes)
                high_severity = sum(1 for w in wastes if w.get('severity') == 'Alta')
                
                category_analysis.append({
                    'Categoria': waste_type,
                    'Quantidade': len(wastes),
                    'Tempo/Dia (min)': category_time,
                    'Custo/Dia (R$)': category_cost,
                    'Alta Severidade': high_severity
                })
        
        if category_analysis:
            st.markdown("#### 📋 Análise por Categoria")
            
            category_df = pd.DataFrame(category_analysis)
            category_df = category_df.sort_values('Custo/Dia (R$)', ascending=False)
            
            st.dataframe(category_df, use_container_width=True)
            
            # Gráfico de desperdícios por categoria
            if len(category_analysis) > 1:
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    fig_waste_qty = px.bar(
                        category_df,
                        x='Categoria',
                        y='Quantidade',
                        title="Quantidade de Desperdícios por Categoria"
                    )
                    fig_waste_qty.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_waste_qty, use_container_width=True)
                
                with col_chart2:
                    fig_waste_cost = px.bar(
                        category_df,
                        x='Categoria',
                        y='Custo/Dia (R$)',
                        title="Impacto em Custo por Categoria"
                    )
                    fig_waste_cost.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_waste_cost, use_container_width=True)
        
        # Projeções anuais
        if total_time > 0 or total_cost > 0:
            st.markdown("#### 📈 Projeções de Impacto")
            
            # Assumindo 250 dias úteis por ano
            annual_time_hours = (total_time * 250) / 60
            annual_cost = total_cost * 250
            
            col_proj1, col_proj2 = st.columns(2)
            
            with col_proj1:
                st.metric("Tempo Perdido/Ano", f"{annual_time_hours:.0f} horas")
            
            with col_proj2:
                st.metric("Custo Anual", f"R$ {annual_cost:,.2f}")
            
            # Potencial de economia
            if annual_cost > 0:
                potential_savings = annual_cost * 0.8  # Assumindo 80% de redução possível
                st.success(f"💰 **Potencial de economia anual:** R$ {potential_savings:,.2f} (80% de redução)")
    
    def _show_process_report(self):
        """Relatório consolidado da análise de processo"""
        st.markdown("### 📊 Relatório de Análise do Processo")
        
        # Resumo executivo
        st.markdown("#### 📈 Resumo Executivo")
        
        # Verificar completude
        process_mapped = len(self.data.get('process_steps', [])) > 0
        bottlenecks_identified = len(self.data.get('bottlenecks', [])) > 0
        waste_identified = any(len(wastes) > 0 for wastes in self.data.get('waste_analysis', {}).values())
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if process_mapped:
                st.success("✅ Processo Mapeado")
                st.caption(f"{len(self.data['process_steps'])} etapas")
            else:
                st.error("❌ Processo Não Mapeado")
        
        with col2:
            if bottlenecks_identified:
                st.success("✅ Gargalos Identificados")
                st.caption(f"{len(self.data['bottlenecks'])} gargalos")
            else:
                st.error("❌ Gargalos Não Identificados")
        
        with col3:
            if waste_identified:
                st.success("✅ Desperdícios Analisados")
                total_wastes = sum(len(wastes) for wastes in self.data['waste_analysis'].values())
                st.caption(f"{total_wastes} desperdícios")
            else:
                st.error("❌ Desperdícios Não Analisados")
        
        # Métricas do processo
        if process_mapped:
            st.markdown("#### 📊 Métricas do Processo")
            
            total_time = sum(step['time'] for step in self.data['process_steps'])
            total_cost = sum(step['cost'] for step in self.data['process_steps'])
            value_add_time = sum(step['time'] for step in self.data['process_steps'] if step['value_add'] == 'Sim')
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                st.metric("Tempo Total", f"{total_time:.1f} min")
            
            with col_m2:
                st.metric("Custo Total", f"R$ {total_cost:.2f}")
            
            with col_m3:
                efficiency = (value_add_time / total_time * 100) if total_time > 0 else 0
                st.metric("Eficiência", f"{efficiency:.1f}%")
            
            with col_m4:
                st.metric("Etapas", len(self.data['process_steps']))
        
        # Principais descobertas
        st.markdown("#### 🔍 Principais Descobertas")
        
        discoveries = []
        
        if process_mapped:
            # Etapa mais demorada
            longest_step = max(self.data['process_steps'], key=lambda x: x['time'])
            discoveries.append(f"⏱️ **Etapa mais demorada:** {longest_step['name']} ({longest_step['time']} min)")
            
            # Etapas que não agregam valor
            non_value_steps = [step for step in self.data['process_steps'] if step['value_add'] == 'Não']
            if non_value_steps:
                non_value_time = sum(step['time'] for step in non_value_steps)
                discoveries.append(f"🗑️ **Desperdício identificado:** {len(non_value_steps)} etapas não agregam valor ({non_value_time:.1f} min)")
        
        if bottlenecks_identified:
            critical_bottlenecks = [b for b in self.data['bottlenecks'] if b['impact'] == 'Alto']
            if critical_bottlenecks:
                discoveries.append(f"🚧 **Gargalos críticos:** {len(critical_bottlenecks)} identificados")
        
        if waste_identified:
            total_waste_cost = sum(
                sum(w.get('cost_impact', 0) for w in wastes)
                for wastes in self.data['waste_analysis'].values()
            )
            if total_waste_cost > 0:
                annual_waste_cost = total_waste_cost * 250
                discoveries.append(f"💰 **Custo de desperdícios:** R$ {annual_waste_cost:,.2f}/ano")
        
        if discoveries:
            for discovery in discoveries:
                st.write(discovery)
        else:
            st.info("Complete as análises para ver as principais descobertas")
        
        # Recomendações prioritárias
        st.markdown("#### 🎯 Recomendações Prioritárias")
        
        recommendations = []
        
        if process_mapped and bottlenecks_identified:
            recommendations.append("🚧 **Eliminar gargalos críticos** identificados na análise")
        
        if process_mapped:
            efficiency = (value_add_time / total_time * 100) if total_time > 0 else 0
            if efficiency < 50:
                recommendations.append("⚡ **Melhorar eficiência** - menos de 50% das atividades agregam valor")
        
        if waste_identified:
            recommendations.append("🗑️ **Implementar melhorias Lean** para eliminar desperdícios identificados")
        
        recommendations.extend([
            "📊 **Monitorar métricas** de tempo de ciclo e qualidade",
            "👥 **Envolver a equipe** no desenvolvimento de soluções",
            "🔄 **Implementar melhorias incrementais** usando metodologia PDCA"
        ])
        
        for rec in recommendations:
            st.write(rec)
        
        # Próximos passos
        st.markdown("#### 🚀 Próximos Passos")
        
        next_steps = [
            "💡 **Fase Improve:** Desenvolver soluções para os problemas identificados",
            "📈 **Definir metas:** Estabelecer objetivos quantitativos de melhoria",
            "🎯 **Priorizar ações:** Focar nos gargalos e desperdícios de maior impacto",
            "📋 **Plano de ação:** Criar cronograma detalhado de implementação",
            "📊 **Métricas de controle:** Definir indicadores para monitorar melhorias"
        ]
        
        for step in next_steps:
            st.write(step)
    
    def _show_action_buttons(self):
        """Botões de ação"""
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Salvar Análise", key=f"save_process_analysis_{self.project_id}"):
                success = self.manager.save_tool_data('process_analysis', self.data, False)
                if success:
                    st.success("💾 Análise do processo salva!")
                else:
                    st.error("❌ Erro ao salvar")
        
        with col2:
            if st.button("✅ Finalizar Análise do Processo", key=f"complete_process_analysis_{self.project_id}"):
                # Validação
                has_analysis = (
                    len(self.data.get('process_steps', [])) > 0 or
                    len(self.data.get('bottlenecks', [])) > 0 or
                    any(len(wastes) > 0 for wastes in self.data.get('waste_analysis', {}).values())
                )
                
                if has_analysis:
                    success = self.manager.save_tool_data('process_analysis', self.data, True)
                    if success:
                        st.success("✅ Análise do processo finalizada!")
                        st.balloons()
                    else:
                        st.error("❌ Erro ao finalizar")
                else:
                    st.error("❌ Complete pelo menos uma análise (processo, gargalos ou desperdícios)")


def _show_analyze_progress(manager: AnalyzePhaseManager, tool_options: Dict, analyze_data: Dict):
    """Mostra progresso geral da fase Analyze"""
    st.markdown("### 📊 Progresso da Fase Analyze")
    
    # Recarregar dados atualizados
    if 'current_project' in st.session_state:
        updated_analyze_data = st.session_state.current_project.get('analyze', {})
    else:
        updated_analyze_data = analyze_data
    
    total_tools = len(tool_options)
    completed_tools = 0
    
    # Status das ferramentas
    st.markdown("#### 📋 Status das Ferramentas")
    
    cols = st.columns(len(tool_options))
    
    for i, (key, (icon, name)) in enumerate(tool_options.items()):
        is_completed = manager.is_tool_completed(key)
        
        if is_completed:
            completed_tools += 1
        
        with cols[i]:
            if is_completed:
                st.success(f"✅ {name}")
            else:
                st.info(f"⏳ {name}")
    
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
        
        # Resumo das principais descobertas
        st.markdown("### 🎯 Principais Descobertas da Análise")
        
        discoveries = []
        
        # Verificar descobertas de cada ferramenta
        if manager.is_tool_completed('root_cause_analysis'):
            rca_data = updated_analyze_data.get('root_cause_analysis', {}).get('data', {})
            if rca_data.get('root_cause_final'):
                discoveries.append(f"🔍 **Causa Raiz:** {rca_data['root_cause_final']}")
        
        if manager.is_tool_completed('statistical_analysis'):
            discoveries.append("📊 **Análise Estatística:** Padrões e tendências identificados nos dados")
        
        if manager.is_tool_completed('hypothesis_testing'):
            hyp_data = updated_analyze_data.get('hypothesis_testing', {}).get('data', {})
            tests_performed = len(hyp_data.get('tests_performed', []))
            if tests_performed > 0:
                discoveries.append(f"🧪 **Hipóteses:** {tests_performed} teste(s) estatístico(s) executado(s)")
        
        if manager.is_tool_completed('process_analysis'):
            proc_data = updated_analyze_data.get('process_analysis', {}).get('data', {})
            process_steps = len(proc_data.get('process_steps', []))
            bottlenecks = len(proc_data.get('bottlenecks', []))
            if process_steps > 0 or bottlenecks > 0:
                discoveries.append(f"⚙️ **Processo:** {process_steps} etapas mapeadas, {bottlenecks} gargalo(s) identificado(s)")
        
        if discoveries:
            for discovery in discoveries:
                st.write(discovery)
        else:
            st.info("Complete as ferramentas para ver um resumo das descobertas")
        
        # Preparação para próxima fase
        st.markdown("### 🚀 Preparação para a Fase Improve")
        
        preparation_items = [
            "💡 **Priorize as causas raiz** identificadas para desenvolvimento de soluções",
            "📊 **Use as evidências estatísticas** para fundamentar as melhorias",
            "🎯 **Foque nos gargalos críticos** para máximo impacto",
            "📈 **Defina metas quantitativas** baseadas na análise realizada"
        ]
        
        for item in preparation_items:
            st.write(item)
    
    # Debug opcional
    with st.expander("🔍 Debug - Dados da Fase Analyze"):
        st.json(updated_analyze_data)
    
    











    
