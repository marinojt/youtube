import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from datetime import datetime, timedelta
import statistics
import re
from collections import Counter
import time

# API Setup - MUST be at the top
def setup_youtube_api():
    """Initialize YouTube API client"""
    API_KEY = 'AIzaSyDQDu7_yw-7P3xuaMp1F0qWOnn_iWCCRNc'
    if not API_KEY:
        raise ValueError("Please set YOUTUBE_API_KEY environment variable")
    
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    return youtube

def analyze_competitors(channel_data, performance_data=None, max_competitors=10):
    """
    Step 1.5: Complete competitor intelligence analysis
    
    Args:
        channel_data: Output from step 1.1 (main channel data)
        performance_data: Optional output from step 1.3 (for enhanced comparison)
        max_competitors: Maximum number of competitors to analyze
        
    Returns:
        dict: Complete competitive analysis with benchmarking and insights
    """
    print(f"🔍 Step 1.5: Starting competitor intelligence analysis...")
    print(f"🎯 Target Channel: {channel_data['channel_title']}")
    
    # Step 1: Find similar channels
    print("🔎 Finding similar channels...")
    competitors = find_similar_channels(
        channel_data, 
        max_competitors=max_competitors
    )
    
    if not competitors:
        print("❌ No competitors found")
        return create_empty_competitive_analysis(channel_data)
    
    print(f"✅ Found {len(competitors)} potential competitors")
    
    # Step 2: Collect competitor data
    print("📊 Collecting competitor channel data...")
    competitor_profiles = collect_competitor_data(competitors)
    
    # Step 3: Benchmark performance
    print("📈 Performing competitive benchmarking...")
    competitive_analysis = benchmark_performance(
        target_channel=channel_data,
        competitors=competitor_profiles,
        target_performance=performance_data
    )
    
    # Step 4: Generate insights
    print("💡 Generating competitive insights...")
    competitive_insights = generate_competitive_insights(
        channel_data, 
        competitor_profiles, 
        competitive_analysis
    )
    
    # Compile final results
    results = {
        'target_channel': {
            'channel_id': channel_data['channel_id'],
            'channel_title': channel_data['channel_title'],
            'subscriber_count': channel_data.get('subscriber_count', 0),
            'total_views': channel_data.get('total_views', 0),
            'video_count': channel_data.get('video_count', 0)
        },
        'competitors': competitor_profiles,
        'competitive_analysis': competitive_analysis,
        'competitive_insights': competitive_insights,
        'metadata': {
            'analysis_date': datetime.now().isoformat(),
            'competitors_analyzed': len(competitor_profiles),
            'api_calls_used': competitive_analysis.get('total_api_calls', 0),
            'analysis_scope': 'Full Competitive Intelligence'
        }
    }
    
    print(f"✅ Competitive analysis complete!")
    print(f"📊 Analyzed {len(competitor_profiles)} competitors")
    print(f"💰 API calls used: {results['metadata'].get('api_calls_used', 0)}")
    
    return results

def find_similar_channels(channel_data, max_competitors=10):
    """Find similar channels using search and filtering"""
    youtube = setup_youtube_api()
    
    search_terms = extract_channel_keywords(channel_data)
    
    competitors = []
    api_calls_made = 0
    unique_channel_ids = {channel_data['channel_id']}
    
    try:
        for search_term in search_terms[:3]:  # Use top 3 most relevant search terms
            print(f"🔍 Searching for channels similar to: '{search_term}'")
            
            search_response = youtube.search().list(
                q=search_term,
                part='snippet',
                type='channel',
                maxResults=25,
                order='relevance'
            ).execute()
            api_calls_made += 1
            
            for item in search_response['items']:
                channel_id = item['snippet']['channelId']
                
                if channel_id not in unique_channel_ids:
                    unique_channel_ids.add(channel_id)
                    competitor_candidate = {
                        'channel_id': channel_id,
                        'channel_title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'published_at': item['snippet']['publishedAt'],
                    }
                    competitors.append(competitor_candidate)
            
            time.sleep(0.1) # Be respectful to the API
        
        filtered_competitors = filter_and_rank_competitors(competitors, channel_data, max_competitors)
        
        print(f"📊 Filtered to {len(filtered_competitors)} relevant competitors")
        return filtered_competitors
        
    except HttpError as e:
        print(f"❌ Error searching for competitors: {e}")
        return []

def extract_channel_keywords(channel_data):
    """Extract relevant keywords from channel data for competitor search"""
    title = channel_data.get('channel_title', '')
    description = channel_data.get('description', '')
    combined_text = (title + ' ' + description).lower()
    
    stop_words = {'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'channel', 'youtube', 'subscribe', 'like', 'video'}
    words = re.findall(r'\b[a-zA-Z]{3,}\b', combined_text)
    filtered_words = [word for word in words if word not in stop_words]
    
    word_counts = Counter(filtered_words)
    top_words = [word for word, count in word_counts.most_common(5)]
    
    return top_words

def filter_and_rank_competitors(competitors, target_channel_data, max_competitors):
    """Filter and rank competitors based on a relevance score."""
    scored_competitors = []
    for competitor in competitors:
        score = calculate_competitor_relevance_score(competitor, target_channel_data)
        competitor['relevance_score'] = score
        scored_competitors.append(competitor)
    
    scored_competitors.sort(key=lambda x: x['relevance_score'], reverse=True)
    return scored_competitors[:max_competitors]

def calculate_competitor_relevance_score(competitor, target_channel):
    """Calculate how relevant a competitor is to the target channel."""
    score = 0
    target_title_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', target_channel.get('channel_title', '').lower()))
    comp_title_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', competitor.get('channel_title', '').lower()))
    
    if target_title_words and comp_title_words:
        title_similarity = len(target_title_words.intersection(comp_title_words)) / len(target_title_words.union(comp_title_words))
        score += title_similarity * 50

    target_desc_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', target_channel.get('description', '').lower()))
    comp_desc_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', competitor.get('description', '').lower()))

    if target_desc_words and comp_desc_words:
        desc_similarity = len(target_desc_words.intersection(comp_desc_words)) / len(target_desc_words.union(comp_desc_words))
        score += desc_similarity * 30
    
    score += 20 # Base score for being found
    return score

def collect_competitor_data(competitors):
    """Collect detailed data for each competitor channel."""
    competitor_profiles = []
    for competitor in competitors:
        try:
            print(f"📊 Analyzing competitor profile: {competitor['channel_title']}")
            # Using a simplified version of get_enhanced_channel_statistics to avoid circular dependencies
            # and to focus on competitor-relevant data.
            comp_data = get_basic_channel_stats(competitor['channel_id'])
            if comp_data:
                comp_data['relevance_score'] = competitor.get('relevance_score', 0)
                competitor_profiles.append(comp_data)
            time.sleep(0.1)
        except Exception as e:
            print(f"⚠️ Unexpected error for {competitor['channel_title']}: {e}")
            continue
    return competitor_profiles

def get_basic_channel_stats(channel_id):
    """A lightweight version of 1.1's main function for competitor analysis."""
    youtube = setup_youtube_api()
    try:
        response = youtube.channels().list(
            part='snippet,statistics,contentDetails',
            id=channel_id
        ).execute()
        if not response['items']: return None
        
        data = response['items'][0]
        stats = data.get('statistics', {})
        total_views = int(stats.get('viewCount', 0))
        video_count = int(stats.get('videoCount', 1))

        return {
            'channel_id': data['id'],
            'channel_title': data['snippet']['title'],
            'custom_url': data['snippet'].get('customUrl', ''),
            'description': data['snippet']['description'],
            'published_at': data['snippet']['publishedAt'],
            'country': data['snippet'].get('country', 'Unknown'),
            'subscriber_count': int(stats.get('subscriberCount', 0)),
            'total_views': total_views,
            'video_count': video_count,
            'uploads_playlist_id': data.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads'),
            'channel_age_days': calculate_channel_age_days(data['snippet']['publishedAt']),
            'average_views_per_video': total_views / max(video_count, 1),
        }
    except HttpError as e:
        print(f"⚠️ API Error fetching basic stats for {channel_id}: {e}")
        return None

def calculate_channel_age_days(published_at):
    if not published_at: return 0
    try:
        published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        return (datetime.now(published_date.tzinfo) - published_date).days
    except:
        return 0

def benchmark_performance(target_channel, competitors, target_performance=None):
    """Perform comprehensive competitive benchmarking."""
    if not competitors: return {'error': 'No competitors to benchmark against'}
    
    all_channels = [target_channel] + competitors
    sub_counts = [c.get('subscriber_count', 0) for c in all_channels]
    view_counts = [c.get('total_views', 0) for c in all_channels]
    avg_view_counts = [c.get('average_views_per_video', 0) for c in all_channels]

    target_subs = target_channel.get('subscriber_count', 0)
    target_views = target_channel.get('total_views', 0)

    return {
        'subscriber_ranking': calculate_ranking(target_subs, [c['subscriber_count'] for c in competitors]),
        'subscriber_percentile': calculate_percentile(target_subs, sub_counts),
        'views_percentile': calculate_percentile(target_views, view_counts),
        'market_statistics': {
            'median_subscribers': statistics.median(sub_counts),
            'avg_subscribers': round(statistics.mean(sub_counts)),
            'median_avg_views_per_video': round(statistics.median(avg_view_counts)),
        },
        'performance_gaps': {
            'subscriber_gap_to_leader': max(sub_counts) - target_subs,
            'views_gap_to_leader': max(view_counts) - target_views,
        },
        'top_competitors_by_subs': sorted(competitors, key=lambda x: x.get('subscriber_count', 0), reverse=True)[:3],
    }

def calculate_ranking(target_value, competitor_values):
    return sorted([target_value] + competitor_values, reverse=True).index(target_value) + 1

def calculate_percentile(target_value, all_values):
    if not all_values: return 50
    return round((sorted(all_values).index(target_value) / len(all_values)) * 100, 1)

def generate_competitive_insights(target_channel, competitors, competitive_analysis):
    """Generate strategic insights from the competitive analysis."""
    if not competitors or 'market_statistics' not in competitive_analysis:
        return {'error': 'Insufficient data for insights.'}
        
    market_stats = competitive_analysis['market_statistics']
    target_subs = target_channel.get('subscriber_count', 0)
    median_subs = market_stats.get('median_subscribers', 0)
    
    position = "Above Median" if target_subs > median_subs else "Below Median"
    
    return {
        'market_position_summary': f"Channel is {position} in its competitive set with {target_subs:,} subscribers vs a median of {median_subs:,}.",
        'strategic_recommendations': [f"Focus on strategies to close the {median_subs - target_subs:,} subscriber gap to the market median."] if target_subs < median_subs else ["Leverage market leader position to expand into new content areas."],
    }

def create_empty_competitive_analysis(channel_data):
    """Create an empty analysis structure when no competitors are found."""
    return {
        'target_channel': { 'channel_id': channel_data['channel_id'], 'channel_title': channel_data['channel_title']},
        'competitors': [], 'competitive_analysis': {'error': 'No competitors found'},
        'competitive_insights': {'error': 'Insufficient data for analysis'}, 'metadata': {}
    }

def save_competitive_analysis(analysis_data, filename=None):
    """Save competitive analysis to a JSON file."""
    if not filename:
        channel_title = analysis_data['target_channel']['channel_title'].replace(' ', '_')
        filename = f"{channel_title}_competitive_intelligence_analysis.json"
    
    with open(filename, 'w') as f:
        json.dump(analysis_data, f, indent=2, default=str)
    
    print(f"💾 Competitive analysis saved to {filename}")


if __name__ == "__main__":
    print("🔄 Running Standalone Test for Step 1.5: Competitor Analysis...")

    # To run this test, we must first get data from Step 1.1 for a target channel.
    import scraping_1_1 as s11

    # --- CONFIGURATION for Standalone Test ---
    TEST_CHANNEL_URL = "https://www.youtube.com/@mkbhd" # Let's use a different one for testing

    try:
        print(f"--- (Test) Getting base channel data for {TEST_CHANNEL_URL} using scraping-1.1 ---")
        target_channel_data = s11.get_enhanced_channel_statistics(TEST_CHANNEL_URL)
        
        print(f"\n--- (Test) Running competitor analysis for {target_channel_data['channel_title']} ---")
        # In a standalone test, we won't have the deep performance data, so we pass None.
        competitive_analysis = analyze_competitors(
            target_channel_data, 
            performance_data=None, 
            max_competitors=5
        )
        
        # Save the standalone analysis
        if competitive_analysis:
            save_competitive_analysis(competitive_analysis)
        
        print("\n✅ Standalone competitor analysis complete!")

    except Exception as e:
        print(f"❌ Error during standalone test: {e}")