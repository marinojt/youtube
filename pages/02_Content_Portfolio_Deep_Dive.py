# pages/02_Product_Portfolio_Analysis.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Product Portfolio Analysis")

def format_number(num):
    """Formats a number for display in tables."""
    if pd.isna(num):
        return "N/A"
    return f"{num:,.0f}"

if 'target_channel_data' not in st.session_state:
    st.error("Data not loaded. Please return to the main page to load the analysis file.")
else:
    channel_data = st.session_state.target_channel_data
    videos_df = st.session_state.videos_df.copy() # Use a copy to avoid modifying session state

    st.title("Product Portfolio Deep Dive")
    st.markdown("This report deconstructs the overall 'Asset Health Index' into its four core components. Each section analyzes the entire product portfolio against a specific performance dimension, identifying top performers and areas for strategic improvement.")
    st.markdown("---")

    if videos_df.empty:
        st.warning("No product asset data available for this business unit.")
    else:
        # --- 1. Market Reach Analysis (View Score) ---
        st.header("1. Market Reach Analysis (View Score)")
        st.info("This measures raw popularity and market penetration. The benchmark for a maximum score is **50,000 engagements** per asset.")
        
        col1, col2 = st.columns([1.5, 1]) # Give more space to the chart
        with col1:
            fig = px.histogram(videos_df, x="view_count", log_x=True, title="Distribution of Asset Engagements")
            fig.update_layout(xaxis_title="Engagements (Views) on a Logarithmic Scale", yaxis_title="Number of Assets")
            fig.add_vline(x=50000, line_width=2, line_dash="dash", line_color="red", annotation_text="Benchmark (50k)")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("Top 5 Assets by Reach")
            top_reach = videos_df.nlargest(5, 'view_count')[['title', 'view_count']]
            top_reach['view_count'] = top_reach['view_count'].apply(format_number)
            st.dataframe(top_reach, use_container_width=True)

            st.subheader("Top 5 Improvement Opportunities")
            bottom_reach = videos_df.nsmallest(5, 'view_count')[['title', 'view_count']]
            bottom_reach['view_count'] = bottom_reach['view_count'].apply(format_number)
            st.dataframe(bottom_reach, use_container_width=True)

        st.markdown("---")

        # --- 2. Audience Satisfaction Analysis (Engagement Score) ---
        st.header("2. Audience Satisfaction Analysis (Engagement Score)")
        st.info("This measures how well the audience responds to an asset. The benchmark for a maximum score is a **4% engagement rate** (likes + comments / views).")

        col1, col2 = st.columns([1.5, 1])
        with col1:
            # Filter out videos with 0 views for a meaningful engagement rate distribution
            engagement_df = videos_df[videos_df['view_count'] > 100].copy()
            fig = px.histogram(engagement_df, x="engagement_rate", title="Distribution of Audience Satisfaction Scores")
            fig.update_layout(xaxis_title="Engagement Rate (Satisfaction Score)", yaxis_title="Number of Assets")
            fig.add_vline(x=0.04, line_width=2, line_dash="dash", line_color="red", annotation_text="Benchmark (4%)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Top 5 Assets by Satisfaction")
            top_eng = engagement_df.nlargest(5, 'engagement_rate')[['title', 'engagement_rate']]
            top_eng['engagement_rate'] = (top_eng['engagement_rate'] * 100).map('{:.2f}%'.format)
            st.dataframe(top_eng, use_container_width=True)

            st.subheader("Top 5 Improvement Opportunities")
            bottom_eng = engagement_df.nsmallest(5, 'engagement_rate')[['title', 'engagement_rate']]
            bottom_eng['engagement_rate'] = (bottom_eng['engagement_rate'] * 100).map('{:.2f}%'.format)
            st.dataframe(bottom_eng, use_container_width=True)
            
        st.markdown("---")

        # --- 3. Social Proof Analysis (Social Score) ---
        videos_df['total_interactions'] = videos_df['like_count'] + videos_df['comment_count']
        st.header("3. Social Proof Analysis (Social Score)")
        st.info("This measures the total volume of social interaction an asset generates. The benchmark for a maximum score is **1,000 total interactions** (likes + comments).")

        col1, col2 = st.columns([1.5, 1])
        with col1:
            fig = px.histogram(videos_df, x="total_interactions", log_x=True, title="Distribution of Social Proof Volume")
            fig.update_layout(xaxis_title="Total Interactions (Logarithmic Scale)", yaxis_title="Number of Assets")
            fig.add_vline(x=1000, line_width=2, line_dash="dash", line_color="red", annotation_text="Benchmark (1k)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Top 5 Assets by Social Proof")
            top_social = videos_df.nlargest(5, 'total_interactions')[['title', 'total_interactions']]
            top_social['total_interactions'] = top_social['total_interactions'].apply(format_number)
            st.dataframe(top_social, use_container_width=True)

            st.subheader("Top 5 Improvement Opportunities")
            bottom_social = videos_df.nsmallest(5, 'total_interactions')[['title', 'total_interactions']]
            bottom_social['total_interactions'] = bottom_social['total_interactions'].apply(format_number)
            st.dataframe(bottom_social, use_container_width=True)
            
        st.markdown("---")
        
        # --- 4. Performance Efficiency Analysis (Velocity Score) ---
        # Handle potential division by zero for videos with 0 duration
        videos_df['duration_minutes'] = videos_df['duration_seconds'] / 60
        videos_df['views_per_minute'] = videos_df.apply(
            lambda row: row['view_count'] / row['duration_minutes'] if row['duration_minutes'] > 0 else 0,
            axis=1
        )
        st.header("4. Performance Efficiency Analysis (Velocity Score)")
        st.info("This measures how efficiently an asset generates engagement relative to its complexity (duration). The benchmark for a maximum score is **1,000 views per minute**.")

        col1, col2 = st.columns([1.5, 1])
        with col1:
            velocity_df = videos_df[videos_df['views_per_minute'] > 0].copy()
            fig = px.histogram(velocity_df, x="views_per_minute", log_x=True, title="Distribution of Asset Performance Efficiency")
            fig.update_layout(xaxis_title="Views per Minute (Logarithmic Scale)", yaxis_title="Number of Assets")
            fig.add_vline(x=1000, line_width=2, line_dash="dash", line_color="red", annotation_text="Benchmark (1k)")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Top 5 Most Efficient Assets")
            top_velo = videos_df.nlargest(5, 'views_per_minute')[['title', 'views_per_minute']]
            top_velo['views_per_minute'] = top_velo['views_per_minute'].apply(format_number)
            st.dataframe(top_velo, use_container_width=True)
            
            st.subheader("Top 5 Improvement Opportunities")
            bottom_velo = videos_df[videos_df['views_per_minute'] > 0].nsmallest(5, 'views_per_minute')[['title', 'views_per_minute']]
            bottom_velo['views_per_minute'] = bottom_velo['views_per_minute'].apply(format_number)
            st.dataframe(bottom_velo, use_container_width=True)
