# pages/04_Phase_2_Advanced_Analytics.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide", page_title="Phase 2: Advanced Analytics")

st.title("Phase 2 Preview: Pipeline & Lifecycle Analytics")
st.warning(
    """
    **FOR DEMONSTRATION ONLY:** The analytics on this page use a **simulated dataset**.
    They showcase the high-value insights (e.g., lead funnels, churn analysis, cohort retention) that are possible with access to internal, private business data.
    """
)
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Lead Acquisition Funnel")
    funnel_data = {'stage': ['Market Impressions', 'Product Engagements (Leads)', 'Qualified Leads (High-Retention)', 'Converted Customers'],'value': [2_500_000, 200_000, 75_000, 1_500]}
    fig = go.Figure(go.Funnel(y=funnel_data['stage'], x=funnel_data['value'], textposition="inside", textinfo="value+percent initial"))
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Customer Churn: Root Cause Analysis")
    churn_reasons_data = {'Reason': ['Product-Market Fit Mismatch', 'Dissatisfaction with New Product Lines', 'High Ad/Sponsorship Frequency', 'Inconsistent Release Cadence'], 'Count': [125, 88, 62, 45]}
    churn_df = pd.DataFrame(churn_reasons_data)
    fig = px.bar(churn_df, x='Count', y='Reason', orientation='h', title="Simulated Monthly Churn Drivers")
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

col3, col4 = st.columns(2)
with col3:
    st.subheader("Customer Cohort Retention Analysis")
    cohort_data = {'Acquisition Cohort': ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024'],'Day 1': [100.0, 100.0, 100.0, 100.0],'Day 7': [85.2, 88.1, 86.5, None],'Day 30': [62.5, 65.3, None, None],'Day 90': [41.3, None, None, None]}
    cohort_df = pd.DataFrame(cohort_data).set_index('Acquisition Cohort')
    fig = px.imshow(cohort_df, text_auto=".1f", aspect="auto", color_continuous_scale='Greens', title="Customer Retention by Acquisition Month (%)")
    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.subheader("Product Adoption Velocity")
    st.markdown("*Time-to-Market Saturation Analysis*")
    np.random.seed(42)
    peak_times = np.random.gamma(2.5, 1.5, 100).clip(1, 30)
    fig = px.histogram(x=peak_times, nbins=15, title="Distribution of Days to Reach Peak Engagement", labels={'x': 'Days Since Product Release'})
    fig.update_layout(yaxis_title="Number of Products")
    st.plotly_chart(fig, use_container_width=True)