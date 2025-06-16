# pages/01_Executive_Summary.py

import streamlit as st
import pandas as pd
import plotly.express as px

# Helper function can be defined here or imported from a utils.py
def format_kpi(num):
    if num is None: return 'N/A'
    if num >= 1_000_000: return f"{num / 1_000_000:.1f}M"
    if num >= 1_000: return f"{num / 1_000:.1f}K"
    return str(num)

st.set_page_config(layout="wide", page_title="Executive Summary")

# --- Check if data is loaded ---
if 'target_channel_data' not in st.session_state:
    st.error("Data not loaded. Please go to the main page to load the analysis file.")
else:
    # --- Load data from session state ---
    channel_data = st.session_state.target_channel_data
    video_analysis = st.session_state.target_video_analysis
    competitor_overview = st.session_state.competitor_overview

    # --- Page Content ---
    st.title(f"Executive Summary: {channel_data.get('channel_title', '')}")
    st.markdown("---")

    channel_analytics = video_analysis.get('channel_analytics', {})
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Est. Monthly Revenue", f"${channel_analytics.get('monthly_estimated_revenue', 0):,.0f}")
    col2.metric("Avg. Revenue per Video", f"${channel_analytics.get('avg_revenue_per_video', 0):.2f}")
    col3.metric("Avg. Performance Score", f"{channel_analytics.get('avg_performance_score', 0):.1f}/100")
    col4.metric("Content Velocity", f"{channel_data.get('content_velocity', 0):.2f} videos/day")
    
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Market Position (Subscriber Count)")
        st.markdown("*Enterprise View: Market Share Analysis*")
        market_stats = competitor_overview.get('competitive_analysis', {}).get('market_statistics', {})
        if market_stats:
            your_subs = channel_data.get('subscriber_count', 0)
            competitor_subs = [c.get('subscriber_count', 0) for c in competitor_overview.get('competitors', [])]
            market_leader_subs = max([your_subs] + competitor_subs) if your_subs or competitor_subs else 0
            
            fig = px.bar(y=['Your Channel', 'Market Average', 'Market Leader'], x=[your_subs, market_stats.get('avg_subscribers', 0), market_leader_subs],
                         orientation='h', labels={'x': 'Subscribers', 'y': ''}, text_auto=True)
            fig.update_traces(texttemplate='%{x:,.0f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Competitor data not available.")

    with col2:
        st.subheader("Revenue by Content Category")
        st.markdown("*Enterprise View: Product Line P&L*")
        if not video_analysis.get('videos', []):
            st.info("Video data not available.")
        else:
            df = pd.DataFrame(video_analysis['videos'])
            if 'estimated_revenue' in df.columns and 'content_category' in df.columns:
                revenue_by_cat = df.groupby('content_category')['estimated_revenue'].sum().sort_values(ascending=False)
                fig = px.bar(revenue_by_cat, x=revenue_by_cat.values, y=revenue_by_cat.index,
                             orientation='h', labels={'x': 'Total Estimated Revenue ($)', 'y': 'Category'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Revenue or category data missing.")