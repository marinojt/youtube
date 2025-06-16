# pages/02_Content_Portfolio_Deep_Dive.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Content Portfolio")

if 'target_channel_data' not in st.session_state:
    st.error("Data not loaded. Please go to the main page to load the analysis file.")
else:
    channel_data = st.session_state.target_channel_data
    videos_df = st.session_state.videos_df

    st.title(f"Content Portfolio Deep Dive: {channel_data.get('channel_title', '')}")
    st.markdown("*Enterprise View: Product Portfolio Optimization (BCG Matrix)*")
    st.markdown("---")

    if videos_df.empty:
        st.warning("No video data available for this channel.")
    else:
        st.header("Content Strategy Matrix")
        st.info("Analyze your video library by performance vs. engagement. Bubble size represents video length.")

        if 'view_count' in videos_df.columns and 'engagement_rate' in videos_df.columns:
            videos_df_plottable = videos_df[videos_df['view_count'] > 0].copy()
            if not videos_df_plottable.empty:
                median_views = videos_df_plottable['view_count'].median()
                median_engagement = videos_df_plottable['engagement_rate'].median()

                fig = px.scatter(
                    videos_df_plottable, x="view_count", y="engagement_rate", size="duration_seconds",
                    color="content_category", hover_name="title", log_x=True,
                    labels={"view_count": "Video Views (Log Scale)", "engagement_rate": "Engagement Rate (%)"},
                    title="Portfolio View: Views vs. Engagement"
                )
                fig.add_vline(x=median_views, line_width=2, line_dash="dash", line_color="grey", annotation_text="Median Views")
                fig.add_hline(y=median_engagement, line_width=2, line_dash="dash", line_color="grey", annotation_text="Median Engagement")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No videos with views available to plot.")
        else:
            st.warning("Required columns ('view_count', 'engagement_rate') not found in video data.")