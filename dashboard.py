import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="YouTube BI Suite",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Data Loading ---
@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_data(filepath='full_analysis_report.json'):
    """Loads the main analysis JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# --- Helper Functions for Charts ---
def format_kpi(num):
    """Formats a number into a compact KPI format (e.g., 1.2M, 5.3K)."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)

# --- Main App ---
def main():
    st.sidebar.title("BI Dashboard Navigation")
    page = st.sidebar.radio("Choose a Report", ["Executive Summary", "Competitive Intelligence", "Content Portfolio Deep Dive"])

    data = load_data()

    if data is None:
        st.error("🚨 Analysis report file ('full_analysis_report.json') not found.")
        st.warning("Please run `main.py` locally and upload the generated JSON file to your GitHub repository.")
        st.info("The dashboard will appear here once the data file is available.")
        return

    # --- Extracting Key Data Chunks for easier access ---
    target_id = data.get('target_channel_id')
    if not target_id or target_id not in data.get('channel_deep_dives', {}):
        st.error("Target channel data not found in the report. Please re-run the analysis.")
        return

    target_deep_dive = data['channel_deep_dives'][target_id]
    target_channel_data = target_deep_dive.get('channel_data', {})
    target_video_analysis = target_deep_dive.get('video_analysis', {})
    target_videos_df = pd.DataFrame(target_video_analysis.get('videos', []))
    competitor_overview = data.get('competitor_overview', {})

    st.sidebar.markdown("---")
    st.sidebar.info(f"**Analysis Target:**\n\n{target_channel_data.get('channel_title', 'N/A')}")
    st.sidebar.markdown(f"**Subscribers:** {format_kpi(target_channel_data.get('subscriber_count', 0))}")
    st.sidebar.markdown(f"**Total Views:** {format_kpi(target_channel_data.get('total_views', 0))}")
    st.sidebar.markdown("---")


    # --- Page Routing ---
    if page == "Executive Summary":
        render_executive_summary(target_channel_data, target_video_analysis, competitor_overview)
    elif page == "Competitive Intelligence":
        render_competitive_intelligence(target_channel_data, competitor_overview, data['channel_deep_dives'])
    elif page == "Content Portfolio Deep Dive":
        render_content_portfolio(target_channel_data, target_videos_df)

def render_executive_summary(channel_data, video_analysis, competitor_overview):
    st.title(f" Executive Summary: {channel_data.get('channel_title', '')}")
    st.markdown("---")
    
    # 1. Top-Line KPIs
    st.header("Key Business Performance Indicators")
    channel_analytics = video_analysis.get('channel_analytics', {})
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg. Revenue per Video", f"${channel_analytics.get('avg_revenue_per_video', 0):.2f}")
    col2.metric("Est. Monthly Revenue", f"${channel_analytics.get('monthly_estimated_revenue', 0):,.0f}")
    col3.metric("Avg. Performance Score", f"{channel_analytics.get('avg_performance_score', 0):.1f}/100")
    col4.metric("Content Velocity", f"{channel_data.get('content_velocity', 0):.2f} videos/day")
    
    st.markdown("---")

    # 2. Market Position & Content Health
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Market Position vs. Competitors")
        market_stats = competitor_overview.get('competitive_analysis', {}).get('market_statistics', {})
        if market_stats:
            fig = px.bar(
                y=['Your Channel', 'Market Average', 'Market Leader'],
                x=[channel_data.get('subscriber_count', 0), market_stats.get('avg_subscribers', 0), max([c['subscriber_count'] for c in competitor_overview.get('competitors', [{'subscriber_count': 0}])])],
                orientation='h',
                labels={'x': 'Subscribers', 'y': ''},
                text_auto=True
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Competitor data not available for this chart.")

    with col2:
        st.subheader("Revenue by Content Category")
        if not target_video_analysis.get('videos', []):
            st.info("Video data not available for this chart.")
        else:
            df = pd.DataFrame(target_video_analysis['videos'])
            revenue_by_cat = df.groupby('content_category')['estimated_revenue'].sum().sort_values(ascending=False)
            fig = px.bar(
                revenue_by_cat,
                x=revenue_by_cat.values,
                y=revenue_by_cat.index,
                orientation='h',
                labels={'x': 'Total Estimated Revenue ($)', 'y': 'Category'},
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Executive Recommendation (LLM-Generated Placeholder)")
    st.info("📈 **Growth Opportunity:** Your 'Education' content significantly outperforms other categories in revenue per view. Recommend creating a dedicated series to capture this high-value audience. \n\n⚠️ **Competitive Threat:** Competitor 'Channel XYZ' is growing 25% faster month-over-month. Their focus on short-form 'How-To' videos appears to be a key driver.")

def render_competitive_intelligence(target_data, competitor_overview, all_deep_dives):
    st.title("Competitive Intelligence Dashboard")
    st.markdown("---")

    # 1. Competitive Landscape Overview Table
    st.header("Competitive Landscape Overview")
    if competitor_overview.get('competitors'):
        comp_df = pd.DataFrame(competitor_overview['competitors'])
        display_cols = ['channel_title', 'subscriber_count', 'total_views', 'video_count', 'average_views_per_video']
        st.dataframe(comp_df[display_cols].style.format({
            'subscriber_count': '{:,.0f}',
            'total_views': '{:,.0f}',
            'video_count': '{:,.0f}',
            'average_views_per_video': '{:,.0f}'
        }))
    else:
        st.info("No competitor data to display.")

    st.markdown("---")
    # 2. Content Strategy Comparison
    st.header("Content Strategy Comparison")
    
    # Data prep for comparison charts
    comparison_data = []
    channels_to_compare = [target_data] + competitor_overview.get('competitors', [])
    for channel in channels_to_compare:
        channel_id = channel['channel_id']
        if channel_id in all_deep_dives and all_deep_dives[channel_id].get('video_analysis'):
            df = pd.DataFrame(all_deep_dives[channel_id]['video_analysis']['videos'])
            if not df.empty:
                avg_duration = df['duration_seconds'].mean()
                shorts_ratio = (df['is_short'].sum() / len(df)) * 100
                comparison_data.append({
                    'Channel': channel['channel_title'],
                    'Avg. Video Duration (sec)': avg_duration,
                    'Shorts Ratio (%)': shorts_ratio
                })

    if comparison_data:
        comp_df = pd.DataFrame(comparison_data)
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(comp_df, x='Channel', y='Avg. Video Duration (sec)', title="Avg. Video Duration by Channel", text_auto=True)
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(comp_df, x='Channel', y='Shorts Ratio (%)', title="Shorts vs. Long-form Strategy", text_auto='.2f')
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Not enough deep-dive data for strategy comparison.")


def render_content_portfolio(channel_data, videos_df):
    st.title(f"Content Portfolio Deep Dive: {channel_data.get('channel_title', '')}")
    st.markdown("---")

    if videos_df.empty:
        st.warning("No video data available for this channel.")
        return

    # 1. The Content Strategy Matrix
    st.header("Content Strategy Matrix")
    st.info("Analyze your video library. Bubbles are sized by duration. Hover for details.")

    # Filter out videos with 0 views for better log scale plotting
    videos_df_plottable = videos_df[videos_df['view_count'] > 0].copy()

    fig = px.scatter(
        videos_df_plottable,
        x="view_count",
        y="engagement_rate",
        size="duration_seconds",
        color="content_category",
        hover_name="title",
        log_x=True,
        labels={
            "view_count": "Video Views (Log Scale)",
            "engagement_rate": "Engagement Rate (%)",
            "content_category": "Category"
        },
        title="Portfolio View: Views vs. Engagement"
    )
    fig.add_annotation(x=videos_df_plottable['view_count'].median(), y=videos_df_plottable['engagement_rate'].median(), text="Average Zone", showarrow=False, yshift=10)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    # 2. Playlist Performance
    st.header("Playlist Performance Analysis")
    
    # This part requires playlist data. We'll simulate it for now.
    # In a full app, you'd pull this from the JSON.
    st.info("This section would show a ranked table of playlist performance, including the unique 'Series Completion Estimate' metric.")
    playlist_sample_data = {
        "Playlist Title": ["Beginner's Guide to Trading", "Advanced Options Strategy", "Weekly Market Recap"],
        "Total Est. Revenue": [543.21, 1205.80, 153.40],
        "Series Completion Estimate (%)": [78.5, 23.1, 95.2]
    }
    playlist_df = pd.DataFrame(playlist_sample_data)
    st.dataframe(playlist_df)


if __name__ == '__main__':
    main()