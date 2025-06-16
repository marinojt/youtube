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
    This function is cached to avoid recalculating on every interaction.
    """
    # Create a copy to avoid modifying the original session state DataFrame
    df_processed = df.copy()

    # --- Handle edge cases and prepare base metrics ---
    df_processed['duration_minutes'] = df_processed['duration_seconds'] / 60
    # Add a small epsilon to avoid division by zero
    epsilon = 1e-9 
    
    # --- 1. View Score Calculation ---
    p95_views = df_processed['view_count'].quantile(0.95)
    df_processed['view_score'] = df_processed.apply(
        lambda row: min(np.log10(row['view_count'] + 1) / np.log10(p95_views + 1), 1) * 30 if p95_views > 0 else 0,
        axis=1
    )

    # --- 2. Engagement Quality Score Calculation ---
    df_processed['weighted_engagement'] = (
        (df_processed['like_count'] * 1.0 + df_processed['comment_count'] * 2.0) / (df_processed['view_count'] + epsilon)
    )
    p95_engagement = df_processed['weighted_engagement'].quantile(0.95)
    df_processed['engagement_quality_score'] = df_processed.apply(
        lambda row: min(row['weighted_engagement'] / p95_engagement, 1) * 25 if p95_engagement > 0 else 0,
        axis=1
    )

    # --- 3. Social Amplification Score Calculation ---
    df_processed['comment_density'] = (
        df_processed['comment_count'] / ((df_processed['view_count'] / 1000) + epsilon)
    )
    p95_comment_density = df_processed['comment_density'].quantile(0.95)
    df_processed['social_amplification_score'] = df_processed.apply(
        lambda row: min(row['comment_density'] / p95_comment_density, 1) * 20 if p95_comment_density > 0 else 0,
        axis=1
    )

    # --- 4. Content Efficiency Score Calculation ---
    df_processed['efficiency'] = df_processed['view_count'] * 0.4 # Per user's formula
    p95_efficiency = df_processed['efficiency'].quantile(0.95)
    df_processed['content_efficiency_score'] = df_processed.apply(
        lambda row: (np.log10(row['efficiency'] + 1) / np.log10(p95_efficiency + 1)) * 25 if p95_efficiency > 0 else 0,
        axis=1
    )
    
    # --- Final Composite Score ---
    df_processed['overall_performance_score'] = (
        df_processed['view_score'] + 
        df_processed['engagement_quality_score'] + 
        df_processed['social_amplification_score'] + 
        df_processed['content_efficiency_score']
    )
    
    return df_processed

# --- Main Page Logic ---
if 'target_channel_data' not in st.session_state:
    st.error("Data not loaded. Please return to the main page to load the analysis file.")
else:
    # Load base data and calculate the new scores
    df = calculate_new_performance_scores(st.session_state.videos_df)

    st.title("Product Portfolio Analysis: Performance Breakdown")
    st.markdown("This report deconstructs asset performance using a custom, percentile-based indexing system. Each asset is scored across four key business dimensions: Market Reach, Audience Satisfaction, Social Amplification, and Performance Efficiency.")
    
    # --- Summary Panel with Gauge Charts ---
    st.markdown("---")
    st.header("Portfolio Health Summary")
    
    avg_view_score = df['view_score'].mean()
    avg_eng_score = df['engagement_quality_score'].mean()
    avg_social_score = df['social_amplification_score'].mean()
    avg_efficiency_score = df['content_efficiency_score'].mean()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_view_score, title={'text': "Avg. Market Reach"}, domain={'x': [0, 1], 'y': [0, 1]}, gauge={'axis': {'range': [0, 30]}}))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_eng_score, title={'text': "Avg. Audience Satisfaction"}, domain={'x': [0, 1], 'y': [0, 1]}, gauge={'axis': {'range': [0, 25]}}))
        st.plotly_chart(fig, use_container_width=True)
    with col3:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_social_score, title={'text': "Avg. Social Amplification"}, domain={'x': [0, 1], 'y': [0, 1]}, gauge={'axis': {'range': [0, 20]}}))
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_efficiency_score, title={'text': "Avg. Performance Efficiency"}, domain={'x': [0, 1], 'y': [0, 1]}, gauge={'axis': {'range': [0, 25]}}))
        st.plotly_chart(fig, use_container_width=True)

    # --- 1. View Score - Market Reach ---
    st.markdown("---")
    st.header("1. Market Reach (View Score)")
    st.info("This score measures an asset's ability to penetrate the market. It uses logarithmic scaling benchmarked against the portfolio's 95th percentile for views, rewarding viral content without being overly skewed by outliers.")
    
    fig_view = px.scatter(
        df,
        x='days_since_upload',
        y='view_score',
        size='view_count',
        color='content_category',
        hover_name='title',
        title="Asset Market Reach vs. Age",
        labels={
            'days_since_upload': 'Asset Age (Days)',
            'view_score': 'Market Reach Score (0-30)',
            'content_category': 'Product Line',
            'view_count': 'Total Engagements'
        }
    )
    st.plotly_chart(fig_view, use_container_width=True)

    # --- 2. Engagement Quality Score - Audience Satisfaction ---
    st.markdown("---")
    st.header("2. Audience Satisfaction (Engagement Quality Score)")
    st.info("This score measures how deeply an asset resonates with its audience, using a weighted formula (comments are twice as valuable as likes). It is normalized against the portfolio's 95th percentile for engagement.")

    df['performance_tier'] = pd.cut(
        df['view_score'], 
        bins=3, 
        labels=['Low Reach', 'Medium Reach', 'High Reach']
    )
    fig_eng = px.scatter(
        df,
        x='view_score',
        y='engagement_quality_score',
        color='performance_tier',
        trendline='ols',
        hover_name='title',
        title="Audience Satisfaction vs. Market Reach",
        labels={
            'view_score': 'Market Reach Score (0-30)',
            'engagement_quality_score': 'Audience Satisfaction Score (0-25)',
            'performance_tier': 'Reach Tier'
        }
    )
    st.plotly_chart(fig_eng, use_container_width=True)

    # --- 3. Social Amplification Score - Discussion Generation ---
    st.markdown("---")
    st.header("3. Discussion Generation (Social Amplification Score)")
    st.info("This score measures an asset's ability to spark conversation, focusing on comment density (comments per 1,000 views). It highlights assets that are true conversation starters.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        top_20_social = df.nlargest(20, 'social_amplification_score').sort_values('social_amplification_score', ascending=True)
        fig_social_bar = px.bar(
            top_20_social,
            x='social_amplification_score',
            y='title',
            orientation='h',
            title="Top 20 Assets by Discussion Generation",
            labels={'social_amplification_score': 'Social Amplification Score (0-20)', 'title': 'Asset Title'}
        )
        st.plotly_chart(fig_social_bar, use_container_width=True)
    with col2:
        fig_social_hist = px.histogram(
            df,
            x='social_amplification_score',
            title="Distribution of Social Amplification Scores",
            labels={'social_amplification_score': 'Score (0-20)'}
        )
        st.plotly_chart(fig_social_hist, use_container_width=True)
        
    # --- 4. Content Efficiency Score - Performance Efficiency ---
    st.markdown("---")
    st.header("4. Performance Efficiency (Content Efficiency Score)")
    st.info("This score reveals the optimal asset complexity (duration). It helps identify which content lengths are the most efficient at generating engagement, guiding future production strategy.")

    # Create duration buckets for the heatmap
    max_duration = df['duration_minutes'].max()
    duration_bins = [0, 2, 5, 10, 20, max(30, max_duration)]
    duration_labels = ['0-2 min', '2-5 min', '5-10 min', '10-20 min', '20+ min']
    df['duration_bucket'] = pd.cut(df['duration_minutes'], bins=duration_bins, labels=duration_labels, right=False)

    # Create the heatmap data
    heatmap_data = df.groupby('duration_bucket')['content_efficiency_score'].mean().reset_index()
    
    fig_efficiency = px.bar(
        heatmap_data,
        x='duration_bucket',
        y='content_efficiency_score',
        color='content_efficiency_score',
        color_continuous_scale='viridis',
        title="Average Performance Efficiency by Asset Duration",
        labels={
            'duration_bucket': 'Asset Duration Bucket',
            'content_efficiency_score': 'Average Efficiency Score (0-25)'
        }
    )
    st.plotly_chart(fig_efficiency, use_container_width=True)
    st.caption("This chart replaces the proposed heatmap with a more direct and readable bar chart showing the average efficiency for each duration bucket, directly answering the question of which length is most effective.")
