import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np # Needed for simulating data

# --- Page Configuration ---
st.set_page_config(
    page_title="YouTube BI Suite (Phase 1)",
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
    if num is None: return 'N/A'
    if num >= 1_000_000: return f"{num / 1_000_000:.1f}M"
    if num >= 1_000: return f"{num / 1_000:.1f}K"
    return str(num)

# --- Main App ---
def main():
    st.sidebar.title("BI Dashboard Navigation")
    page = st.sidebar.radio(
        "Choose a Report", 
        ["Executive Summary", "Content Portfolio Deep Dive", "Competitive Intelligence", "Advanced Analytics (Phase 2 Preview)"]
    )

    data = load_data()

    if data is None:
        st.error("🚨 Analysis report file ('full_analysis_report.json') not found.")
        st.warning("Please run the full data pipeline and ensure the output file is available.")
        return

    # --- Extracting Key Data Chunks ---
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
    st.sidebar.success("Pages 1-3 are powered by real, publicly scraped data.")
    st.sidebar.warning("Page 4 demonstrates advanced concepts using simulated data.")

    # --- Page Routing ---
    if page == "Executive Summary":
        render_executive_summary(target_channel_data, target_video_analysis, competitor_overview)
    elif page == "Content Portfolio Deep Dive":
        render_content_portfolio(target_channel_data, target_videos_df)
    elif page == "Competitive Intelligence":
        render_competitive_intelligence(target_channel_data, competitor_overview, data['channel_deep_dives'])
    elif page == "Advanced Analytics (Phase 2 Preview)":
        render_advanced_analytics()

def render_executive_summary(channel_data, video_analysis, competitor_overview):
    st.title(f"Executive Summary: {channel_data.get('channel_title', '')}")
    st.markdown("---")
    
    channel_analytics = video_analysis.get('channel_analytics', {})
    
    # KPIs are now cleaned to only show metrics derivable from the public data pipeline
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Est. Monthly Revenue", f"${channel_analytics.get('monthly_estimated_revenue', 0):,.0f}", help="Estimated from recent video performance and upload frequency.")
    col2.metric("Avg. Revenue per Video", f"${channel_analytics.get('avg_revenue_per_video', 0):.2f}", help="A proxy for 'Unit Profitability'.")
    col3.metric("Avg. Performance Score", f"{channel_analytics.get('avg_performance_score', 0):.1f}/100", help="A blended score of views, engagement, and velocity.")
    col4.metric("Content Velocity", f"{channel_data.get('content_velocity', 0):.2f} videos/day", help="A proxy for 'Production Cadence'.")
    
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
            
            fig = px.bar(
                y=['Your Channel', 'Market Average', 'Market Leader'],
                x=[your_subs, market_stats.get('avg_subscribers', 0), market_leader_subs],
                orientation='h', labels={'x': 'Subscribers', 'y': ''}, text_auto=True
            )
            fig.update_traces(texttemplate='%{x:,.0f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Competitor data not available.")

    with col2:
        st.subheader("Revenue by Content Category")
        st.markdown("*Enterprise View: Product Line P&L*")
        if not target_video_analysis.get('videos', []):
            st.info("Video data not available.")
        else:
            df = pd.DataFrame(target_video_analysis['videos'])
            if 'estimated_revenue' in df.columns and 'content_category' in df.columns:
                revenue_by_cat = df.groupby('content_category')['estimated_revenue'].sum().sort_values(ascending=False)
                fig = px.bar(
                    revenue_by_cat, x=revenue_by_cat.values, y=revenue_by_cat.index,
                    orientation='h', labels={'x': 'Total Estimated Revenue ($)', 'y': 'Category'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Revenue or category data missing.")
    st.markdown("---")
    st.subheader("Executive Recommendation (LLM-Generated Placeholder)")
    st.info("📈 **Growth Opportunity:** Your 'Education' content significantly outperforms other categories in revenue per view. Recommend creating a dedicated series to capture this high-value audience. \n\n⚠️ **Competitive Threat:** Competitor 'Channel XYZ' is growing 25% faster month-over-month. Their focus on short-form 'How-To' videos appears to be a key driver.")

def render_content_portfolio(channel_data, videos_df):
    st.title(f"Content Portfolio Deep Dive: {channel_data.get('channel_title', '')}")
    st.markdown("*Enterprise View: Product Portfolio Optimization (BCG Matrix)*")
    st.markdown("---")

    if videos_df.empty:
        st.warning("No video data available for this channel.")
        return

    st.header("Content Strategy Matrix")
    st.info("Analyze your video library by performance vs. engagement. Bubble size represents video length. Hover for details.")

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

def render_competitive_intelligence(target_data, competitor_overview, all_deep_dives):
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
                comparison_data.append({
                    'Channel': channel['channel_title'],
                    'Avg. Video Duration (sec)': avg_duration,
                    'Shorts Ratio (%)': shorts_ratio
                })

    if comparison_data:
        comp_df = pd.DataFrame(comparison_data)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.bar(comp_df, x='Channel', y='Avg. Video Duration (sec)', title="Avg. Video Duration by Channel", text_auto=True), use_container_width=True)
        with col2:
            st.plotly_chart(px.bar(comp_df, x='Channel', y='Shorts Ratio (%)', title="Shorts vs. Long-form Strategy", text_auto='.2f'), use_container_width=True)
    else:
        st.info("Run deep-dive analysis on competitors to enable this comparison.")

def render_advanced_analytics():
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
        # Simulating a sales/marketing funnel
        funnel_data = {'stage': ['Impressions', 'Views (from Impressions)', 'High-Retention Views', 'Subscribers Gained'],'value': [2_500_000, 200_000, 75_000, 1_500]}
        fig = go.Figure(go.Funnel(y=funnel_data['stage'], x=funnel_data['value'], textposition="inside", textinfo="value+percent initial"))
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top Reasons for Unsubscribing")
        st.markdown("*Enterprise View: Root Cause Analysis for Churn*")
        # Simulating HR "Reasons for Leaving"
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
        # Simulating a user cohort retention table
        cohort_data = {'Join Month': ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024'],'Day 1': [100.0, 100.0, 100.0, 100.0],'Day 7': [85.2, 88.1, 86.5, None],'Day 30': [62.5, 65.3, None, None],'Day 90': [41.3, None, None, None]}
        cohort_df = pd.DataFrame(cohort_data).set_index('Join Month')
        fig = px.imshow(cohort_df, text_auto=".1f", aspect="auto", color_continuous_scale='Greens', title="Subscriber Retention by Cohort (%)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col4:
        st.subheader("Video Performance Velocity")
        st.markdown("*Enterprise View: Product Time-to-Peak Analysis*")
        # Simulating how long it takes for videos to reach 90% of their first-month views
        np.random.seed(42)
        peak_times = np.random.gamma(2.5, 1.5, 100).clip(1, 30)
        fig = px.histogram(x=peak_times, nbins=15, title="Distribution of Days to Reach Peak Views", labels={'x': 'Days Since Upload'})
        fig.update_layout(yaxis_title="Number of Videos")
        st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()