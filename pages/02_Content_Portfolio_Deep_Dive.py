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
    ESTIMATED_RETENTION_RATE = 0.4
    epsilon = 1e-9 

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
    weighted_engagement = ((df_processed['like_count'] * 1.0 + df_processed['comment_count'] * 2.0) / 
                           (df_processed['view_count'] + epsilon))
    p95_engagement = weighted_engagement.quantile(0.95)
    if p95_engagement > 0:
        df_processed['engagement_quality_score'] = (weighted_engagement / p95_engagement).clip(upper=1) * 100
    else:
        df_processed['engagement_quality_score'] = 0

    # 3. Social Amplification Score
    comment_density = df_processed['comment_count'] / ((df_processed['view_count'] / 1000) + epsilon)
    p95_comment_density = comment_density.quantile(0.95)
    if p95_comment_density > 0:
        df_processed['social_amplification_score'] = (comment_density / p95_comment_density).clip(upper=1) * 100
    else:
        df_processed['social_amplification_score'] = 0

    # 4. Content Efficiency Score - FIX APPLIED
    df_processed['duration_minutes'] = df_processed['duration_seconds'] / 60
    # The new calculation correctly measures efficiency as estimated watch time generated per minute of content
    estimated_watch_minutes = df_processed['view_count'] * df_processed['duration_minutes'] * ESTIMATED_RETENTION_RATE
    efficiency = estimated_watch_minutes / (df_processed['duration_minutes'] + epsilon)
    p95_efficiency = efficiency.quantile(0.95)
    if p95_efficiency > 0:
        df_processed['content_efficiency_score'] = (np.log10(efficiency + 1) / np.log10(p95_efficiency + 1)).clip(upper=1) * 100
    else:
        df_processed['content_efficiency_score'] = 0
    
    benchmarks = {
        'p95_views': p95_views,
        'p95_engagement': p95_engagement,
        'p95_comment_density': p95_comment_density,
        'p95_efficiency': p95_efficiency
    }
    
    return df_processed, benchmarks

# --- Main Page Logic ---
if 'target_channel_data' not in st.session_state:
    st.error("Data not loaded. Please return to the main page to load the analysis file.")
else:
    base_df = st.session_state.videos_df
    
    # --- Sidebar Filters ---
    st.sidebar.header("Portfolio Filters")
    all_categories = ['All'] + sorted(base_df['content_category'].unique().tolist())
    selected_category = st.sidebar.selectbox("Filter by Product Line", all_categories)

    base_df['months_since_upload'] = base_df['days_since_upload'] / 30.44
    min_age = int(base_df['months_since_upload'].min())
    max_age = int(base_df['months_since_upload'].max())
    selected_age_range = st.sidebar.slider("Filter by Asset Age (Months)", min_age, max_age, (min_age, max_age))

    # --- Filtering Logic ---
    filtered_df = base_df[
        (base_df['months_since_upload'] >= selected_age_range[0]) &
        (base_df['months_since_upload'] <= selected_age_range[1])
    ]
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['content_category'] == selected_category]

    df, benchmarks = calculate_new_performance_scores(filtered_df)

    st.title("Product Portfolio Analysis: Performance Breakdown")
    
    if df.empty:
        st.warning("No assets match the current filter criteria.")
    else:
        # --- NEW: Multi-Dimensional Portfolio View ---
        st.header("Multi-Dimensional Portfolio View")
        st.info("A complete overview of the asset portfolio. X-axis is market reach, Y-axis is audience satisfaction, bubble size represents discussion volume, and color represents efficiency.")
        fig_portfolio = px.scatter(
            df, x='view_score', y='engagement_quality_score',
            size='social_amplification_score', color='content_efficiency_score',
            hover_name='title', title="Complete Portfolio Performance Matrix",
            labels={
                'view_score': 'Market Reach Score',
                'engagement_quality_score': 'Audience Satisfaction Score',
                'social_amplification_score': 'Discussion Volume Score',
                'content_efficiency_score': 'Performance Efficiency Score'
            },
            color_continuous_scale=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig_portfolio, use_container_width=True)

        # --- NEW: Actionable Insights Panel ---
        st.markdown("---")
        st.header("Actionable Insights: Outlier Identification")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("⚠️ Underperformers")
            st.caption("High reach, low satisfaction. These assets attracted an audience but failed to resonate, representing an optimization opportunity.")
            underperformers = df[(df['view_score'] > 75) & (df['engagement_quality_score'] < 50)].sort_values('engagement_quality_score', ascending=True)
            st.dataframe(underperformers[['title', 'view_score', 'engagement_quality_score']], use_container_width=True)
        with col2:
            st.subheader("⭐ Overperformers")
            st.caption("High satisfaction despite lower reach. These assets are 'hidden gems' that resonate deeply with a niche audience.")
            overperformers = df[(df['view_score'] < 50) & (df['engagement_quality_score'] > 75)].sort_values('engagement_quality_score', ascending=False)
            st.dataframe(overperformers[['title', 'view_score', 'engagement_quality_score']], use_container_width=True)

        # --- Visualizations ---
        st.markdown("---")
        st.header("Performance Deep Dive")
        tab1, tab2, tab3, tab4 = st.tabs(["Market Reach", "Audience Satisfaction", "Discussion Generation", "Performance Efficiency"])
        
        with tab1:
            st.info(f"Measures an asset's ability to penetrate the market. 95th Percentile Benchmark: **{benchmarks.get('p95_views', 0):,.0f} views**.")
            # FIX: Removed log_y=True
            fig_view = px.scatter(
                df, x='months_since_upload', y='view_score',
                size='view_count', color='content_category', hover_name='title',
                title="Asset Market Reach vs. Age",
                labels={'months_since_upload': 'Asset Age (Months)', 'view_score': 'Market Reach Score', 'content_category': 'Product Line'}
            )
            st.plotly_chart(fig_view, use_container_width=True)

        with tab2:
            st.info(f"Measures how deeply an asset resonates. 95th Percentile Benchmark: **{benchmarks.get('p95_engagement', 0):.3f} weighted engagement rate**.")
            fig_eng = px.scatter(
                df, x='view_score', y='engagement_quality_score',
                color='content_category', trendline='ols', 
                hover_name='title', title="Audience Satisfaction vs. Market Reach"
            )
            st.plotly_chart(fig_eng, use_container_width=True)

        with tab3:
            st.info(f"Measures an asset's ability to spark conversation. 95th Percentile Benchmark: **{benchmarks.get('p95_comment_density', 0):.2f} comments per 1k views**.")
            corr_df = df[['view_score', 'engagement_quality_score', 'social_amplification_score', 'content_efficiency_score']].corr()
            fig_corr = px.imshow(corr_df, text_auto=True, aspect="auto", title="Performance Score Correlation Matrix")
            st.plotly_chart(fig_corr, use_container_width=True)

        with tab4:
            st.info("Reveals the optimal asset complexity (duration), guiding future production strategy.")
            max_duration = df['duration_minutes'].max() if not df.empty else 30
            duration_bins = [0, 2, 5, 10, 20, max(30, max_duration + 1)]
            duration_labels = ['0-2 min', '2-5 min', '5-10 min', '10-20 min', '20+ min']
            df['duration_bucket'] = pd.cut(df['duration_minutes'], bins=duration_bins, labels=duration_labels, right=False)
            
            # Group by bucket to get both mean score and count
            efficiency_grouped = df.groupby('duration_bucket', observed=False).agg(
                avg_efficiency_score=('content_efficiency_score', 'mean'),
                video_count=('title', 'count')
            ).reset_index()

            fig_efficiency = px.bar(
                efficiency_grouped, x='duration_bucket', y='avg_efficiency_score',
                text='video_count', # TWEAK: Display video count on bars
                title="Average Performance Efficiency & Volume by Asset Duration",
                labels={'duration_bucket': 'Asset Duration Bucket', 'avg_efficiency_score': 'Average Efficiency Score'}
            )
            fig_efficiency.update_traces(texttemplate='<b>%{text} assets</b>', textposition='outside')
            st.plotly_chart(fig_efficiency, use_container_width=True)
