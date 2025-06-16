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
    Calculates the four new performance scores based on percentile-normalized logic.
    Each score is now on a 0-100 scale for consistency.
    """
    if df.empty:
        return pd.DataFrame()
        
    df_processed = df.copy()

    # --- Handle edge cases and prepare base metrics ---
    df_processed['duration_minutes'] = df_processed['duration_seconds'] / 60
    epsilon = 1e-9 
    
    # --- 1. View Score Calculation (out of 100) ---
    p95_views = df_processed['view_count'].quantile(0.95)
    df_processed['view_score'] = df_processed.apply(
        lambda row: min(np.log10(row['view_count'] + 1) / np.log10(p95_views + 1), 1) * 100 if p95_views > 0 else 0,
        axis=1
    )

    # --- 2. Engagement Quality Score Calculation (out of 100) ---
    df_processed['weighted_engagement'] = (
        (df_processed['like_count'] * 1.0 + df_processed['comment_count'] * 2.0) / (df_processed['view_count'] + epsilon)
    )
    p95_engagement = df_processed['weighted_engagement'].quantile(0.95)
    df_processed['engagement_quality_score'] = df_processed.apply(
        lambda row: min(row['weighted_engagement'] / p95_engagement, 1) * 100 if p95_engagement > 0 else 0,
        axis=1
    )

    # --- 3. Social Amplification Score Calculation (out of 100) ---
    df_processed['comment_density'] = (
        df_processed['comment_count'] / ((df_processed['view_count'] / 1000) + epsilon)
    )
    p95_comment_density = df_processed['comment_density'].quantile(0.95)
    df_processed['social_amplification_score'] = df_processed.apply(
        lambda row: min(row['comment_density'] / p95_comment_density, 1) * 100 if p95_comment_density > 0 else 0,
        axis=1
    )

    # --- 4. Content Efficiency Score Calculation (out of 100) ---
    df_processed['efficiency'] = df_processed['view_count'] * 0.4
    p95_efficiency = df_processed['efficiency'].quantile(0.95)
    df_processed['content_efficiency_score'] = df_processed.apply(
        lambda row: (np.log10(row['efficiency'] + 1) / np.log10(p95_efficiency + 1)) * 100 if p95_efficiency > 0 else 0,
        axis=1
    )
    
    return df_processed

# --- Main Page Logic ---
if 'target_channel_data' not in st.session_state:
    st.error("Data not loaded. Please return to the main page to load the analysis file.")
else:
    df = calculate_new_performance_scores(st.session_state.videos_df)

    st.title("Product Portfolio Analysis: Performance Breakdown")
    st.markdown("This report deconstructs asset performance using a custom, percentile-based indexing system. Each asset is scored across four key business dimensions: Market Reach, Audience Satisfaction, Social Amplification, and Performance Efficiency.")
    
    if df.empty:
        st.warning("No video data available to calculate performance scores.")
    else:
        # --- Summary Panel with Gauge Charts ---
        st.markdown("---")
        st.header("Portfolio Health Summary")
        
        avg_view_score = df['view_score'].mean()
        avg_eng_score = df['engagement_quality_score'].mean()
        avg_social_score = df['social_amplification_score'].mean()
        avg_efficiency_score = df['content_efficiency_score'].mean()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_view_score, title={'text': "Avg. Market Reach"}, domain={'x': [0, 1], 'y': [0, 1]}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#1f77b4"}}))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_eng_score, title={'text': "Avg. Audience Satisfaction"}, domain={'x': [0, 1], 'y': [0, 1]}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#ff7f0e"}}))
            st.plotly_chart(fig, use_container_width=True)
        with col3:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_social_score, title={'text': "Avg. Social Amplification"}, domain={'x': [0, 1], 'y': [0, 1]}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#2ca02c"}}))
            st.plotly_chart(fig, use_container_width=True)
        with col4:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_efficiency_score, title={'text': "Avg. Performance Efficiency"}, domain={'x': [0, 1], 'y': [0, 1]}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#d62728"}}))
            st.plotly_chart(fig, use_container_width=True)

        # --- Visualizations ---
        st.markdown("---")
        st.header("1. Market Reach (View Score)")
        st.info("Measures an asset's ability to penetrate the market, benchmarked against the portfolio's top performers.")
        
        df['months_since_upload'] = df['days_since_upload'] / 30.44 # Average days in a month
        fig_view = px.scatter(
            df, x='months_since_upload', y='view_score',
            size='view_count', color='content_category', hover_name='title',
            log_y=True, # TWEAK: Use a logarithmic scale for the Y-axis to increase resolution at the top end.
            title="Asset Market Reach vs. Age",
            labels={
                'months_since_upload': 'Asset Age (Months)',
                'view_score': 'Market Reach Score (Log Scale)',
                'content_category': 'Product Line',
                'view_count': 'Total Engagements'
            }
        )
        st.plotly_chart(fig_view, use_container_width=True)

        st.markdown("---")
        st.header("2. Audience Satisfaction (Engagement Quality Score)")
        st.info("Measures how deeply an asset resonates with its audience, using a weighted formula where comments are valued more than likes.")

        df['performance_tier'] = pd.cut(df['view_score'], bins=3, labels=['Low Reach', 'Medium Reach', 'High Reach'])
        fig_eng = px.scatter(
            df, x='view_score', y='engagement_quality_score',
            color='performance_tier', trendline='ols', trendline_color_override='rgba(128,128,128,0.5)', # TWEAK: Make trendline semi-transparent grey
            hover_name='title',
            title="Audience Satisfaction vs. Market Reach",
            labels={'view_score': 'Market Reach Score (0-100)', 'engagement_quality_score': 'Audience Satisfaction Score (0-100)', 'performance_tier': 'Reach Tier'}
        )
        # TWEAK: Customize the trendline to be dashed and lighter
        fig_eng.data[1].line.dash = 'dash'
        st.plotly_chart(fig_eng, use_container_width=True)

        st.markdown("---")
        st.header("3. Discussion Generation (Social Amplification Score)")
        st.info("Measures an asset's ability to spark conversation, focusing on comment density (comments per 1,000 views).")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            # TWEAK: Ensure it shows exactly 20 assets.
            top_20_social = df.nlargest(20, 'social_amplification_score').sort_values('social_amplification_score', ascending=True)
            fig_social_bar = px.bar(
                top_20_social, x='social_amplification_score', y='title',
                orientation='h', title="Top 20 Assets by Discussion Generation",
                labels={'social_amplification_score': 'Social Amplification Score (0-100)', 'title': 'Asset Title'}
            )
            st.plotly_chart(fig_social_bar, use_container_width=True)
        with col2:
            fig_social_hist = px.histogram(
                df, x='social_amplification_score',
                title="Distribution of Social Amplification Scores",
                labels={'social_amplification_score': 'Score (0-100)', 'count': 'Number of Assets'} # TWEAK: Changed y-axis label
            )
            # TWEAK: Explicitly set the y-axis title
            fig_social_hist.update_layout(yaxis_title="Number of Assets")
            st.plotly_chart(fig_social_hist, use_container_width=True)
            
        st.markdown("---")
        st.header("4. Performance Efficiency (Content Efficiency Score)")
        st.info("Reveals the optimal asset complexity (duration), guiding future production strategy.")

        max_duration = df['duration_minutes'].max() if not df.empty else 30
        duration_bins = [0, 2, 5, 10, 20, max(30, max_duration)]
        duration_labels = ['0-2 min', '2-5 min', '5-10 min', '10-20 min', '20+ min']
        df['duration_bucket'] = pd.cut(df['duration_minutes'], bins=duration_bins, labels=duration_labels, right=False)
        
        # Use observed=True to only show buckets with data
        heatmap_data = df.groupby('duration_bucket', observed=True)['content_efficiency_score'].mean().reset_index()
        
        fig_efficiency = px.bar(
            heatmap_data, x='duration_bucket', y='content_efficiency_score',
            color='content_efficiency_score', color_continuous_scale='viridis',
            title="Average Performance Efficiency by Asset Duration",
            labels={'duration_bucket': 'Asset Duration Bucket', 'content_efficiency_score': 'Average Efficiency Score (0-100)'}
        )
        st.plotly_chart(fig_efficiency, use_container_width=True)
        st.caption("Note: Duration buckets with no corresponding assets are intentionally not displayed. The absence of a bar for a specific duration (e.g., '2-5 min') is an insight, indicating that no products of that length exist in the current portfolio.")
