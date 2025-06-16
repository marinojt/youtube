# pages/02_Product_Portfolio_Analysis.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Product Portfolio Analysis")

if 'target_channel_data' not in st.session_state:
    st.error("Data not loaded. Please return to the main page to load the analysis file.")
else:
    channel_data = st.session_state.target_channel_data
    videos_df = st.session_state.videos_df

    st.title("Product Portfolio Analysis")
    st.markdown("This report uses a BCG-style growth-share matrix to segment the business unit's digital assets, identifying high-potential products and areas for optimization.")
    st.markdown("---")

    if videos_df.empty:
        st.warning("No product asset data available for this business unit.")
    else:
        st.header("Product Performance vs. Satisfaction Matrix")
        st.info("Asset performance is measured by total engagements (market penetration), and satisfaction is measured by a blended engagement score. Bubble size represents asset complexity (duration).")

        if 'view_count' in videos_df.columns and 'engagement_rate' in videos_df.columns:
            videos_df_plottable = videos_df[videos_df['view_count'] > 0].copy()
            if not videos_df_plottable.empty:
                median_views = videos_df_plottable['view_count'].median()
                median_engagement = videos_df_plottable['engagement_rate'].median()

                fig = px.scatter(
                    videos_df_plottable, x="view_count", y="engagement_rate", size="duration_seconds",
                    color="content_category", hover_name="title", log_x=True,
                    labels={
                        "view_count": "Product Engagements (Market Penetration)", 
                        "engagement_rate": "Customer Satisfaction Score (%)",
                        "content_category": "Product Line"
                        },
                    title="Asset Portfolio: Performance vs. Satisfaction"
                )
                fig.add_vline(x=median_views, line_width=2, line_dash="dash", line_color="grey", annotation_text="Median Performance")
                fig.add_hline(y=median_engagement, line_width=2, line_dash="dash", line_color="grey", annotation_text="Median Satisfaction")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No assets with performance data are available to plot.")
        else:
            st.warning("Required performance or satisfaction data not found in the dataset.")