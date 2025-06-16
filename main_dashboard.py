# main_dashboard.py

import streamlit as st
import pandas as pd
import json

# --- Page Configuration (set this on the main page) ---
st.set_page_config(
    page_title="Digital Media BI Platform",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Data Loading Function ---
@st.cache_data(ttl=3600)
def load_data(filepath='full_analysis_report.json'):
    """Loads the main analysis JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"🚨 Analysis report file not found at '{filepath}'.")
        st.warning("Please run the full data pipeline and ensure the output file is in the correct location.")
        return None

# --- Main App Logic ---
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = load_data()

if st.session_state.analysis_data:
    data = st.session_state.analysis_data

    # Extract key data chunks and store them in session_state
    target_id = data.get('target_channel_id')
    if target_id and target_id in data.get('channel_deep_dives', {}):
        st.session_state.target_deep_dive = data['channel_deep_dives'][target_id]
        st.session_state.target_channel_data = st.session_state.target_deep_dive.get('channel_data', {})
        st.session_state.target_video_analysis = st.session_state.target_deep_dive.get('video_analysis', {})
        st.session_state.videos_df = pd.DataFrame(st.session_state.target_video_analysis.get('videos', []))
        st.session_state.competitor_overview = data.get('competitor_overview', {})
        st.session_state.all_deep_dives = data.get('channel_deep_dives', {})

        # --- Sidebar (common to all pages) ---
        target_channel_data = st.session_state.target_channel_data
        st.sidebar.info(f"**Business Unit Analyzed:**\n\n{target_channel_data.get('channel_title', 'N/A')}")
        st.sidebar.markdown(f"**Customer Base:** {target_channel_data.get('subscriber_count', 0):,}")
        st.sidebar.markdown(f"**Total Engagements:** {target_channel_data.get('total_views', 0):,}")
        st.sidebar.markdown("---")
        st.sidebar.success("Reports 1-3 are based on live market data.")
        st.sidebar.warning("Report 4 (Phase 2) demonstrates advanced analytics using a simulated dataset.")

# --- Landing Page Content ---
st.title("Digital Media Business Intelligence Platform")
st.markdown("Welcome. This platform provides a strategic analysis of a digital media business unit, its product portfolio, and its position within the competitive landscape.")
st.info("Please select a report from the sidebar to begin.")