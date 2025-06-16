# pages/04_Advanced_Analytics_Preview.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide", page_title="Advanced Analytics")

st.title("Advanced Analytics (Phase 2 Preview)")
st.warning(
    """
    **DEMONSTRATION ONLY:** The analytics on this page use **simulated data**. 
    They showcase the powerful, high-value insights that become possible with authenticated access to a channel's private YouTube Analytics data. 
    This is the 'Phase 2' of the analysis.
    """
)
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Viewer-to-Subscriber Funnel")
    st.markdown("*Enterprise View: Customer Acquisition Funnel*")
    funnel_data = {'stage': ['Impressions', 'Views (from Impressions)', 'High-Retention Views', 'Subscribers Gained'],'value': [2_500_000, 200_000, 75_000, 1_500]}
    fig = go.Figure(go.Funnel(y=funnel_data['stage'], x=funnel_data['value'], textposition="inside", textinfo="value+percent initial"))
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Top Reasons for Unsubscribing")
    st.markdown("*Enterprise View: Root Cause Analysis for Churn*")
    churn_reasons_data = {'Reason': ['Content became repetitive', 'Not interested in new topics', 'Too many sponsored videos', 'Upload schedule inconsistent'], 'Count': [125, 88, 62, 45]}
    churn_df = pd.DataFrame(churn_reasons_data)
    fig = px.bar(churn_df, x='Count', y='Reason', orientation='h', title="Simulated Monthly Churn Drivers")
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

col3, col4 = st.columns(2)
with col3:
    st.subheader("New Subscriber Retention Over Time")
    st.markdown("*Enterprise View: Customer Cohort Analysis*")
    cohort_data = {'Join Month': ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024'],'Day 1': [100.0, 100.0, 100.0, 100.0],'Day 7': [85.2, 88.1, 86.5, None],'Day 30': [62.5, 65.3, None, None],'Day 90': [41.3, None, None, None]}
    cohort_df = pd.DataFrame(cohort_data).set_index('Join Month')
    fig = px.imshow(cohort_df, text_auto=".1f", aspect="auto", color_continuous_scale='Greens', title="Subscriber Retention by Cohort (%)")
    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.subheader("Video Performance Velocity")
    st.markdown("*Enterprise View: Product Time-to-Peak Analysis*")
    np.random.seed(42)
    peak_times = np.random.gamma(2.5, 1.5, 100).clip(1, 30)
    fig = px.histogram(x=peak_times, nbins=15, title="Distribution of Days to Reach Peak Views", labels={'x': 'Days Since Upload'})
    fig.update_layout(yaxis_title="Number of Videos")
    st.plotly_chart(fig, use_container_width=True)