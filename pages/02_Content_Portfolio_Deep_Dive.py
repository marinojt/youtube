# pages/02_Product_Portfolio_Analysis.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide", page_title="Product Portfolio Analysis")

# --- Helper functions for this page ---
@st.cache_data
def calculate_new_performance_scores(df):
    """
    Calculates the four performance scores using vectorized, percentile-normalized logic.
    Returns the scored DataFrame and the calculated percentile benchmarks.
    """
    if df.empty:
        return pd.DataFrame(), {}
        
    df_processed = df.copy()

    # --- Constants and Error Handling ---
    epsilon = 1e-9 
    df_processed['duration_minutes'] = df_processed['duration_seconds'] / 60

    # --- Vectorized Calculations ---
    # 1. View Score
    p95_views = df_processed['view_count'].quantile(0.95)
    if p95_views > 0:
        log_views = np.log10(df_processed['view_count'] + 1)
        log_p95_views = np.log10(p95_views + 1)
        df_processed['view_score'] = (log_views / log_p95_views).clip(upper=1) * 100
    else:
        df_processed['view_score'] = 0

    # 2. Engagement Quality Score
    df_processed['weighted_engagement'] = ((df_processed['like_count'] * 1.0 + df_processed['comment_count'] * 2.0) / 
                           (df_processed['view_count'] + epsilon))
    p95_engagement = df_processed['weighted_engagement'].quantile(0.95)
    if p95_engagement > 0:
        df_processed['engagement_quality_score'] = (df_processed['weighted_engagement'] / p95_engagement).clip(upper=1) * 100
    else:
        df_processed['engagement_quality_score'] = 0

    # 3. Social Amplification Score
    df_processed['comment_density'] = df_processed['comment_count'] / ((df_processed['view_count'] / 1000) + epsilon)
    p95_comment_density = comment_density.quantile(0.95)
    if p95_comment_density > 0:
        df_processed['social_amplification_score'] = (comment_density / p95_comment_density).clip(upper=1) * 100
    else:
        df_processed['social_amplification_score'] = 0

    # 4. Content Efficiency Score - CRITICALLY CORRECTED LOGIC
    efficiency = df_processed['view_count'] / (df_processed['duration_minutes'] + epsilon)
    p95_efficiency = efficiency.quantile(0.95)
    if p95_efficiency > 0:
        df_processed['content_efficiency_score'] = (np.log10(efficiency + 1) / np.log10(p95_efficiency + 1)).clip(upper=1) * 100
    else:
        df_processed['content_efficiency_score'] = 0
    
    benchmarks = {
        'p95_views': p95_views, 'p95_engagement': p95_engagement, 
        'p95_comment_density': p95_comment_density, 'p95_efficiency': p95_efficiency
    }
    
    return df_processed, benchmarks

# --- Main Page Logic ---
if 'target_channel_data' not in st.session_state:
    st.error("Data not loaded. Please return to the main page to load the analysis file.")
else:
    base_df = st.session_state.videos_df.copy()
    
    # --- Sidebar Filters ---
    st.sidebar.header("Portfolio Filters")
    if 'content_category' in base_df.columns:
        all_categories = ['All'] + sorted(base_df['content_category'].unique().tolist())
        selected_category = st.sidebar.selectbox("Filter by Product Line", all_categories)
    else:
        selected_category = 'All'

    if 'days_since_upload' in base_df.columns:
        base_df['months_since_upload'] = base_df['days_since_upload'] / 30.44
        min_age, max_age = 0, int(base_df['months_since_upload'].max()) if not base_df.empty else 0
        selected_age_range = st.sidebar.slider("Filter by Asset Age (Months)", min_age, max_age, (min_age, max_age))
    else:
        selected_age_range = (0, 0)

    # --- Filtering Logic ---
    filtered_df = base_df.copy()
    if 'months_since_upload' in filtered_df.columns and selected_age_range != (0,0):
        filtered_df = filtered_df[
            (filtered_df['months_since_upload'] >= selected_age_range[0]) &
            (filtered_df['months_since_upload'] <= selected_age_range[1])
        ]
    if selected_category != 'All' and 'content_category' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['content_category'] == selected_category]

    df, benchmarks = calculate_new_performance_scores(filtered_df)

    st.title("Product Portfolio Analysis: Performance Breakdown")
    
    if df.empty:
        st.warning("No assets match the current filter criteria.")
    else:
        # --- MODIFICATION: Restored Gauge Chart Summary ---
        st.markdown("---")
        st.header("Portfolio Health Summary")
        
        avg_view_score = df['view_score'].mean()
        avg_eng_score = df['engagement_quality_score'].mean()
        avg_social_score = df['social_amplification_score'].mean()
        avg_efficiency_score = df['content_efficiency_score'].mean()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_view_score, number={'suffix': "%"}, title={'text': "Avg. Market Reach"}, domain={'x': [0, 1], 'y': [0, 1]}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#1f77b4"}}))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_eng_score, number={'suffix': "%"}, title={'text': "Avg. Audience Satisfaction"}, domain={'x': [0, 1], 'y': [0, 1]}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#ff7f0e"}}))
            st.plotly_chart(fig, use_container_width=True)
        with col3:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_social_score, number={'suffix': "%"}, title={'text': "Avg. Social Amplification"}, domain={'x': [0, 1], 'y': [0, 1]}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#2ca02c"}}))
            st.plotly_chart(fig, use_container_width=True)
        with col4:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_efficiency_score, number={'suffix': "%"}, title={'text': "Avg. Performance Efficiency"}, domain={'x': [0, 1], 'y': [0, 1]}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#d62728"}}))
            st.plotly_chart(fig, use_container_width=True)

        # --- MODIFICATION: Strategic Insights Layout Changed ---
        st.markdown("---")
        st.header("Strategic Insights")
        st.subheader("Performance Trends Over Time")
        monthly_trends = df.groupby(df['months_since_upload'].round())[['view_score', 'engagement_quality_score', 'social_amplification_score', 'content_efficiency_score']].mean().reset_index()
        monthly_trends_melted = monthly_trends.melt(id_vars='months_since_upload', var_name='Metric', value_name='Average Score')
        fig_trend = px.line(monthly_trends_melted, x='months_since_upload', y='Average Score', color='Metric', title="Monthly Average Performance Score Trends")
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # --- Actionable Insights Panel ---
        st.markdown("---")
        st.header("Actionable Insights: Outlier Identification")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("⚠️ Underperformers (High Reach, Low Satisfaction)")
            underperformers = df[(df['view_score'] > 75) & (df['engagement_quality_score'] < 50)].sort_values('engagement_quality_score')
            st.dataframe(underperformers[['title', 'view_score', 'engagement_quality_score']].style.format({'view_score': '{:.1f}', 'engagement_quality_score': '{:.1f}'}), use_container_width=True)
        with col2:
            st.subheader("⭐ Overperformers (Low Reach, High Satisfaction)")
            overperformers = df[(df['view_score'] < 50) & (df['engagement_quality_score'] > 75)].sort_values('engagement_quality_score', ascending=False)
            st.dataframe(overperformers[['title', 'view_score', 'engagement_quality_score']].style.format({'view_score': '{:.1f}', 'engagement_quality_score': '{:.1f}'}), use_container_width=True)

        # --- Visualizations in Tabs---
        st.markdown("---")
        st.header("Performance Component Deep Dive")
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Market Reach", "Audience Satisfaction", "Discussion Generation", "Performance Efficiency", "Score Relationships"])
        
        with tab1:
            st.info(f"Measures market penetration. 95th Percentile Benchmark: **{benchmarks.get('p95_views', 0):,.0f} views**.")
            fig_view = px.scatter(df, x='months_since_upload', y='view_score', size='view_count', color='content_category', hover_name='title', title="Asset Market Reach vs. Age")
            st.plotly_chart(fig_view, use_container_width=True)

        with tab2:
            st.info(f"Measures audience resonance. 95th Percentile Benchmark: **{benchmarks.get('p95_engagement', 0):.3f} weighted engagement rate**.")
            fig_eng = px.scatter(df, x='view_score', y='engagement_quality_score', color='content_category', trendline='ols', hover_name='title', title="Audience Satisfaction vs. Market Reach")
            st.plotly_chart(fig_eng, use_container_width=True)

        with tab3:
            st.info(f"Measures ability to spark conversation. 95th Percentile Benchmark: **{benchmarks.get('p95_comment_density', 0):.2f} comments per 1k views**.")
            top_20_social = df.nlargest(20, 'social_amplification_score')
            fig_social_bar = px.bar(top_20_social, x='social_amplification_score', y='title', orientation='h', title="Top 20 Assets by Discussion Generation", text='social_amplification_score')
            fig_social_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            st.plotly_chart(fig_social_bar, use_container_width=True)

        with tab4:
            st.info(f"Measures views generated per minute of content. 95th Percentile Benchmark: **{benchmarks.get('p95_efficiency', 0):,.1f} views/minute**.")
            max_duration = df['duration_minutes'].max() if not df.empty else 30
            duration_bins = [0, 2, 5, 10, 20, max(30, max_duration + 1)]
            duration_labels = ['0-2 min', '2-5 min', '5-10 min', '10-20 min', '20+ min']
            df['duration_bucket'] = pd.cut(df['duration_minutes'], bins=duration_bins, labels=duration_labels, right=False)
            efficiency_grouped = df.groupby('duration_bucket', observed=True).agg(avg_efficiency_score=('content_efficiency_score', 'mean'), video_count=('title', 'count')).reset_index()
            fig_efficiency = px.bar(efficiency_grouped, x='duration_bucket', y='avg_efficiency_score', text='video_count', title="Average Performance Efficiency & Volume by Asset Duration")
            fig_efficiency.update_traces(texttemplate='<b>%{text} assets</b>', textposition='outside')
            st.plotly_chart(fig_efficiency, use_container_width=True)
            
        with tab5:
            st.info("Reveals strategic patterns by showing how the performance scores relate to each other.")
            corr_df = df[['view_score', 'engagement_quality_score', 'social_amplification_score', 'content_efficiency_score']].corr()
            fig_corr = px.imshow(corr_df, text_auto=True, aspect="auto", title="Performance Score Correlation Matrix", color_continuous_scale='RdBu_r', range_color=[-1,1])
            st.plotly_chart(fig_corr, use_container_width=True)
