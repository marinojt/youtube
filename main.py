import json
import pandas as pd
from datetime import datetime
import os

# Import your custom scraping modules
# The 'sXX' alias is used for brevity and clarity
import scraping_1_1 as s11
import scraping_1_2 as s12
import scraping_1_4 as s14
import scraping_1_5 as s15

def save_to_json(data, filename):
    """Saves dictionary data to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, default=str)
        print(f"✅ Successfully saved JSON report to: {filename}")
    except Exception as e:
        print(f"❌ Error saving JSON file: {e}")

def create_and_save_video_csv(report_data, filename):
    """Creates a flattened CSV of all videos from the analysis for easy use in BI tools."""
    print("-> Creating flattened CSV for all videos...")
    all_videos_flat = []
    
    # Check if the deep dive data exists
    if 'channel_deep_dives' not in report_data:
        print("⚠️ No deep-dive data available to create CSV.")
        return

    # Loop through each analyzed channel's deep dive data
    for channel_id, deep_dive in report_data['channel_deep_dives'].items():
        if deep_dive.get('video_analysis') and deep_dive['video_analysis'].get('videos'):
            videos = deep_dive['video_analysis']['videos']
            for video in videos:
                # Select and flatten key metrics for the CSV
                flat_video_data = {
                    'channel_id': video.get('channel_id'),
                    'channel_title': video.get('channel_title'),
                    'video_id': video.get('video_id'),
                    'video_title': video.get('title'),
                    'published_at': video.get('published_at'),
                    'view_count': video.get('view_count', 0),
                    'like_count': video.get('like_count', 0),
                    'comment_count': video.get('comment_count', 0),
                    'duration_seconds': video.get('duration_seconds', 0),
                    'estimated_revenue': video.get('estimated_revenue', 0.0),
                    'performance_score': video.get('performance_score', 0.0),
                    'engagement_rate': video.get('engagement_rate', 0.0),
                    'content_category': video.get('content_category', 'Unknown'),
                    'is_short': video.get('is_short', False)
                }
                all_videos_flat.append(flat_video_data)

    if not all_videos_flat:
        print("⚠️ No video data found to populate CSV.")
        return

    try:
        df = pd.DataFrame(all_videos_flat)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ Successfully saved CSV report to: {filename}")
    except Exception as e:
        print(f"❌ Error saving CSV file: {e}")


def run_full_bi_analysis(target_url, max_competitors=3):
    """
    Orchestrates the entire BI analysis workflow for a target channel and its competitors.
    
    Args:
        target_url (str): The URL of the YouTube channel to analyze.
        max_competitors (int): The number of top competitors to include in the deep-dive.
    """
    print(f"🚀 STARTING FULL BI ANALYSIS FOR: {target_url} 🚀")
    
    # Initialize the main report structure
    full_analysis_report = {
        'metadata': {
            'analysis_start_time': datetime.now().isoformat(),
            'target_url': target_url,
            'max_competitors_analyzed': max_competitors
        },
        'target_channel_id': None,
        'competitor_overview': None,
        'channel_deep_dives': {} # This will store the detailed analysis for each channel
    }

    try:
        # --- Step 1: Analyze the Target Channel (1.1) ---
        print("\n--- Step 1 of 4: Analyzing Target Channel Base Data ---")
        target_channel_data = s11.get_enhanced_channel_statistics(target_url)
        full_analysis_report['target_channel_id'] = target_channel_data['channel_id']
        print(f"✅ Target: {target_channel_data['channel_title']}")

        # --- Step 2: Find Competitors (1.5) ---
        print("\n--- Step 2 of 4: Identifying Competitor Landscape ---")
        # Note: 1.5 does a full benchmark, we'll store that and extract the competitor list
        competitor_analysis_result = s15.analyze_competitors(target_channel_data, max_competitors=max_competitors)
        full_analysis_report['competitor_overview'] = competitor_analysis_result
        competitors = competitor_analysis_result.get('competitors', [])
        print(f"✅ Found {len(competitors)} relevant competitors.")

        # --- Step 3 & 4: Deep Dive on Target and Competitors ---
        print("\n--- Step 3 of 4: Performing Deep-Dive Analysis ---")
        channels_to_analyze = [target_channel_data] + competitors
        
        for i, channel in enumerate(channels_to_analyze):
            is_target = (i == 0)
            log_prefix = "(Target)" if is_target else "(Competitor)"
            print(f"\n Diving into Channel {i+1}/{len(channels_to_analyze)}: {channel['channel_title']} {log_prefix}")
            
            channel_id = channel['channel_id']
            deep_dive_data = {
                'channel_data': channel,
                'video_analysis': None,
                'playlist_analysis': None
            }

            try:
                # Run Video Analysis (1.2, which now includes 1.3's logic)
                print("  -> Fetching and analyzing video portfolio...")
                video_analysis = s12.get_all_videos_with_full_analysis(channel)
                deep_dive_data['video_analysis'] = video_analysis

                # Run Playlist Analysis (1.4)
                print("  -> Fetching and analyzing playlist structure...")
                # Pass the rich video_analysis data to get performance metrics for playlists
                playlist_analysis = s14.get_channel_playlists(channel, video_analysis)
                deep_dive_data['playlist_analysis'] = playlist_analysis
                
            except Exception as e:
                print(f"❌ ERROR during deep-dive for {channel['channel_title']}: {e}")
            
            # Add the completed deep-dive to our main report
            full_analysis_report['channel_deep_dives'][channel_id] = deep_dive_data

        # --- Final Step: Save the Consolidated Report ---
        print("\n--- Step 4 of 4: Consolidating and Saving Reports ---")
        
        # Create a timestamped folder for the reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_folder = f"BI_Report_{target_channel_data['channel_title'].replace(' ', '_')}_{timestamp}"
        os.makedirs(report_folder, exist_ok=True)
        print(f"📂 Reports will be saved in: {report_folder}")

        # Define file paths
        json_filename = os.path.join(report_folder, "full_analysis_report.json")
        csv_filename = os.path.join(report_folder, "video_portfolio_data.csv")
        
        # Save the structured JSON
        save_to_json(full_analysis_report, json_filename)
        
        # Save the flattened CSV
        create_and_save_video_csv(full_analysis_report, csv_filename)

        full_analysis_report['metadata']['analysis_end_time'] = datetime.now().isoformat()
        print("\n🎉 BI ANALYSIS COMPLETE! 🎉")
        return full_analysis_report

    except Exception as e:
        print(f"\n\n❌ A critical error occurred during the analysis: {e}")
        return None


# ==============================================================================
#  MAIN EXECUTION BLOCK
# ==============================================================================
if __name__ == "__main__":
    # --- CONFIGURATION ---
    # Set the URL of the channel you want to analyze
    TARGET_CHANNEL_URL = "https://www.youtube.com/@TheTradingChannel"
    # Set how many of their top competitors you also want to deep-dive into
    MAX_COMPETITORS_TO_ANALYZE = 2 # Set to 0 to only analyze the target channel

    # --- RUN ANALYSIS ---
    run_full_bi_analysis(TARGET_CHANNEL_URL, MAX_COMPETITORS_TO_ANALYZE)