# pages/03_Market_and_Competitive_Landscape.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Competitive Landscape")

if 'target_channel_data' not in st.session_state:
    st.error("Data not loaded. Please return to the main page to load the analysis file.")
else:
    target_data = st.session_state.target_channel_data
    competitor_overview = st.session_state.competitor_overview
    all_deep_dives = st.session_state.all_deep_dives

    st.title("Market and Competitive Landscape")
    st.markdown("This report provides external market research, benchmarking this business unit against key competitors on performance metrics and go-to-market strategy.")
    st.markdown("---")

    st.header("Competitor Performance Benchmarking")
    if competitor_overview.get('competitors'):
        comp_df = pd.DataFrame(competitor_overview.get('competitors', []))
        
        # Check if columns exist before trying to rename them
        rename_map = {
            'channel_title': 'Competitor Brand', 
            'subscriber_count': 'Customer Base', 
            'total_views': 'Total Engagements',
            'video_count': 'Total Assets',
            'average_views_per_video': 'Avg Engagements per Asset'
        }
        
        # Only rename columns that are actually present in the DataFrame
        comp_df.rename(columns={k: v for k, v in rename_map.items() if k in comp_df.columns}, inplace=True)
        
        # Define display columns based on the new names
        display_cols = ['Competitor Brand', 'Customer Base', 'Total Engagements', 'Total Assets', 'Avg Engagements per Asset', 'relevance_score']
        
        # Filter for only columns that actually exist in the dataframe to prevent errors
        display_cols_exist = [col for col in display_cols if col in comp_df.columns]
        
        st.dataframe(comp_df[display_cols_exist].style.format({
            'Customer Base': '{:,.0f}', 
            'Total Engagements': '{:,.0f}', 
            'Total Assets': '{:,.0f}',
            'Avg Engagements per Asset': '{:,.0f}', 
            'relevance_score': '{:.1f}'
        }))
    else:
        st.info("No competitor data to display.")

    st.markdown("---")
    st.header("Go-to-Market Strategy Comparison")
    
    comparison_data = []
    channels_to_compare = [target_data] + competitor_overview.get('competitors', [])
    
    for channel in channels_to_compare:
        channel_id = channel.get('channel_id')
        if channel_id and channel_id in all_deep_dives and all_deep_dives.get(channel_id, {}).get('video_analysis', {}).get('videos'):
            df = pd.DataFrame(all_deep_dives[channel_id]['video_analysis']['videos'])
            if not df.empty:
                avg_duration = df['duration_seconds'].mean()
                shorts_ratio = (df['is_short'].sum() / len(df)) * 100 if len(df) > 0 else 0
                comparison_data.append({
                    'Brand': channel.get('channel_title', 'Unknown'), 
                    'Avg. Asset Complexity (sec)': avg_duration, 
                    'Short-Form Asset Ratio (%)': shorts_ratio
                })

    if comparison_data:
        comp_df = pd.DataFrame(comparison_data)
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(comp_df, x='Brand', y='Avg. Asset Complexity (sec)', title="Avg. Asset Complexity by Brand", text_auto=True)
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(comp_df, x='Brand', y='Short-Form Asset Ratio (%)', title="Short-Form vs. Long-Form Strategy", text_auto='.2f')
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Deep-dive analysis must be run on competitors to enable this comparison.")