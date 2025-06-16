# pages/03_Competitive_Intelligence.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Competitive Intelligence")

if 'target_channel_data' not in st.session_state:
    st.error("Data not loaded. Please go to the main page to load the analysis file.")
else:
    target_data = st.session_state.target_channel_data
    competitor_overview = st.session_state.competitor_overview
    all_deep_dives = st.session_state.all_deep_dives

    st.title("Competitive Intelligence Dashboard")
    st.markdown("*Enterprise View: External Market & Competitor Benchmarking*")
    st.markdown("---")

    st.header("Competitive Landscape Overview")
    if competitor_overview.get('competitors'):
        comp_df = pd.DataFrame(competitor_overview['competitors'])
        display_cols = ['channel_title', 'subscriber_count', 'total_views', 'video_count', 'average_views_per_video', 'relevance_score']
        display_cols = [col for col in display_cols if col in comp_df.columns]
        
        st.dataframe(comp_df[display_cols].style.format({
            'subscriber_count': '{:,.0f}', 'total_views': '{:,.0f}', 'video_count': '{:,.0f}',
            'average_views_per_video': '{:,.0f}', 'relevance_score': '{:.1f}'
        }))
    else:
        st.info("No competitor data to display.")

    st.markdown("---")
    st.header("Content Strategy Comparison")
    
    comparison_data = []
    channels_to_compare = [target_data] + competitor_overview.get('competitors', [])
    for channel in channels_to_compare:
        channel_id = channel.get('channel_id')
        if channel_id and channel_id in all_deep_dives and all_deep_dives[channel_id].get('video_analysis', {}).get('videos'):
            df = pd.DataFrame(all_deep_dives[channel_id]['video_analysis']['videos'])
            if not df.empty:
                avg_duration = df['duration_seconds'].mean()
                shorts_ratio = (df['is_short'].sum() / len(df)) * 100 if len(df) > 0 else 0
                comparison_data.append({'Channel': channel['channel_title'], 'Avg. Video Duration (sec)': avg_duration, 'Shorts Ratio (%)': shorts_ratio})

    if comparison_data:
        comp_df = pd.DataFrame(comparison_data)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.bar(comp_df, x='Channel', y='Avg. Video Duration (sec)', title="Avg. Video Duration by Channel", text_auto=True), use_container_width=True)
        with col2:
            st.plotly_chart(px.bar(comp_df, x='Channel', y='Shorts Ratio (%)', title="Shorts vs. Long-form Strategy", text_auto='.2f'), use_container_width=True)
    else:
        st.info("Run deep-dive analysis on competitors to enable this comparison.")