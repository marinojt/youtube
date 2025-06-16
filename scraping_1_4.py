import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from datetime import datetime, timedelta
import statistics
import re
from collections import Counter

# API Setup - MUST be at the top
def setup_youtube_api():
    """Initialize YouTube API client"""
    API_KEY = 'AIzaSyDQDu7_yw-7P3xuaMp1F0qWOnn_iWCCRNc'
    if not API_KEY:
        raise ValueError("Please set YOUTUBE_API_KEY environment variable")
    
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    return youtube

def get_channel_playlists(channel_data, performance_data=None):
    """
    Step 1.4: Get channel playlists and organization analysis for BI insights
    
    Args:
        channel_data: Output from step 1.1 (contains channel_id)
        performance_data: Optional output from step 1.3 (for enhanced metrics)
        
    Returns:
        dict: Complete playlists data with organization and performance analysis
    """
    youtube = setup_youtube_api()
    
    channel_id = channel_data['channel_id']
    all_playlists = []
    next_page_token = None
    api_calls_made = 0
    
    try:
        print(f"🔍 Collecting playlists for channel: {channel_id}")
        
        # Get all playlists from the channel
        while True:
            playlists_request = youtube.playlists().list(
                part='snippet,contentDetails,status',
                channelId=channel_id,
                maxResults=50,
                pageToken=next_page_token
            )
            
            playlists_response = playlists_request.execute()
            api_calls_made += 1
            
            # Process each playlist
            for playlist_item in playlists_response['items']:
                playlist_data = {
                    # Playlist Identity
                    'playlist_id': playlist_item['id'],
                    'title': playlist_item['snippet']['title'],
                    'description': playlist_item['snippet']['description'],
                    'published_at': playlist_item['snippet']['publishedAt'],
                    'channel_id': playlist_item['snippet']['channelId'],
                    'channel_title': playlist_item['snippet']['channelTitle'],
                    
                    # Playlist Metadata
                    'privacy_status': playlist_item['status']['privacyStatus'],
                    'item_count': playlist_item['contentDetails']['itemCount'],
                    'default_language': playlist_item['snippet'].get('defaultLanguage', ''),
                    
                    # Thumbnails
                    'thumbnail_default': playlist_item['snippet']['thumbnails'].get('default', {}).get('url', ''),
                    'thumbnail_medium': playlist_item['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                    'thumbnail_high': playlist_item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                    'thumbnail_standard': playlist_item['snippet']['thumbnails'].get('standard', {}).get('url', ''),
                    'thumbnail_maxres': playlist_item['snippet']['thumbnails'].get('maxres', {}).get('url', ''),
                    
                    # Analysis Metadata
                    'playlist_age_days': calculate_playlist_age(playlist_item['snippet']['publishedAt']),
                    'is_main_uploads': playlist_item['id'] == channel_data.get('uploads_playlist_id', ''),
                    'title_length': len(playlist_item['snippet']['title']),
                    'description_length': len(playlist_item['snippet']['description']),
                    
                    # Performance Metrics (will be calculated)
                    'video_ids': [],
                    'total_playlist_views': 0,
                    'avg_views_per_video': 0,
                    'playlist_engagement_rate': 0,
                    'series_completion_estimate': 0,
                    'monetization_potential': 'Unknown',
                    'content_theme': 'Unknown',
                    'seasonal_pattern': 'Unknown',
                    
                    # Organization Analysis
                    'playlist_type': classify_playlist_type(playlist_item['snippet']['title']),
                    'content_strategy': 'Unknown',
                }
                
                all_playlists.append(playlist_data)
            
            # Check for more pages
            next_page_token = playlists_response.get('nextPageToken')
            if not next_page_token:
                break
            
            print(f"📄 Collected {len(all_playlists)} playlists so far...")
        
        print(f"✅ Found {len(all_playlists)} playlists!")
        
        # Get detailed playlist items and calculate performance metrics
        print("🔍 Analyzing playlist contents and performance...")
        enhanced_playlists = []
        
        for playlist in all_playlists:
            if playlist['item_count'] > 0:  # Only analyze playlists with content
                enhanced_playlist = get_playlist_details(playlist, performance_data)
                enhanced_playlists.append(enhanced_playlist)
                api_calls_made += enhanced_playlist.get('api_calls_used', 0)
            else:
                enhanced_playlists.append(playlist)
        
        # Calculate channel-level playlist analytics
        organization_analytics = calculate_organization_analytics(enhanced_playlists, channel_data)
        
        # Create final data structure
        playlists_data = {
            'playlists': enhanced_playlists,
            'metadata': {
                'channel_id': channel_id,
                'channel_title': channel_data['channel_title'],
                'total_playlists': len(enhanced_playlists),
                'public_playlists': len([p for p in enhanced_playlists if p['privacy_status'] == 'public']),
                'step_1_4_api_calls': api_calls_made,
                'analysis_date': datetime.now().isoformat(),
            },
            'organization_analytics': organization_analytics
        }
        
        print(f"✅ Playlist analysis complete!")
        print(f"💰 Step 1.4 API cost: {api_calls_made} units")
        print(f"📊 Analyzed {len(enhanced_playlists)} playlists")
        
        return playlists_data
        
    except HttpError as e:
        raise Exception(f"YouTube API error: {e}")
    except Exception as e:
        raise Exception(f"Error collecting playlists data: {e}")

def get_playlist_details(playlist_data, performance_data=None):
    """Get detailed playlist items and calculate performance metrics"""
    youtube = setup_youtube_api()
    
    playlist_id = playlist_data['playlist_id']
    video_ids = []
    playlist_videos = []
    next_page_token = None
    api_calls_used = 0
    
    try:
        # Get all videos in the playlist
        while True:
            playlist_items_request = youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            
            playlist_items_response = playlist_items_request.execute()
            api_calls_used += 1
            
            for item in playlist_items_response['items']:
                video_id = item['contentDetails']['videoId']
                video_ids.append(video_id)
                
                video_info = {
                    'video_id': video_id,
                    'title': item['snippet']['title'],
                    'position': item['snippet']['position'],
                    'published_at': item['snippet'].get('publishedAt', ''),
                }
                playlist_videos.append(video_info)
            
            next_page_token = playlist_items_response.get('nextPageToken')
            if not next_page_token:
                break
        
        playlist_data['video_ids'] = video_ids
        playlist_data['playlist_videos'] = sorted(playlist_videos, key=lambda x: x['position'])
        playlist_data['api_calls_used'] = api_calls_used
        
        if performance_data and performance_data.get('videos'):
            playlist_data.update(calculate_playlist_performance_metrics(
                playlist_data, performance_data['videos']
            ))
        
        playlist_data.update(analyze_playlist_content_themes(playlist_data))
        
        return playlist_data
        
    except HttpError as e:
        print(f"⚠️ Error getting playlist details for {playlist_id}: {e}")
        playlist_data['api_calls_used'] = api_calls_used
        return playlist_data

def calculate_playlist_performance_metrics(playlist_data, all_videos_performance):
    """Calculate comprehensive playlist performance metrics"""
    video_ids = playlist_data['video_ids']
    playlist_videos_data = []
    
    performance_lookup = {v['video_id']: v for v in all_videos_performance if 'video_id' in v}
    
    for video_id in video_ids:
        if video_id in performance_lookup:
            playlist_videos_data.append(performance_lookup[video_id])
    
    if not playlist_videos_data:
        return {}
    
    total_views = sum(v.get('view_count', 0) for v in playlist_videos_data)
    total_likes = sum(v.get('like_count', 0) for v in playlist_videos_data)
    total_comments = sum(v.get('comment_count', 0) for v in playlist_videos_data)
    total_revenue = sum(v.get('estimated_revenue', 0) for v in playlist_videos_data)
    
    avg_views = total_views / len(playlist_videos_data) if playlist_videos_data else 0
    
    playlist_engagement_rate = (total_likes + total_comments) / max(total_views, 1)
    completion_estimate = estimate_series_completion_rate(playlist_videos_data)
    
    return {
        'total_playlist_views': total_views,
        'avg_views_per_video': round(avg_views, 0),
        'playlist_engagement_rate': round(playlist_engagement_rate, 6),
        'series_completion_estimate': round(completion_estimate, 3),
        'total_playlist_revenue': round(total_revenue, 2),
        'playlist_performance_score': round(calculate_playlist_performance_score(avg_views, playlist_engagement_rate, len(playlist_videos_data), completion_estimate), 2),
        'playlist_videos_analyzed': len(playlist_videos_data),
        'monetization_potential': classify_monetization_potential(total_revenue, len(playlist_videos_data)),
        'viewership_consistency': calculate_viewership_consistency(playlist_videos_data)
    }

def estimate_series_completion_rate(playlist_videos_data):
    """Estimate what percentage of viewers complete the playlist series"""
    if len(playlist_videos_data) < 2: return 1.0
    
    sorted_videos = sorted(playlist_videos_data, key=lambda x: x.get('position', 0))
    view_counts = [v.get('view_count', 0) for v in sorted_videos]
    
    if not view_counts or view_counts[0] == 0: return 0.0
    
    first_video_views = view_counts[0]
    last_video_views = view_counts[-1]
    
    completion_rate = last_video_views / first_video_views
    length_adjustment = max(0.3, 1 - (len(playlist_videos_data) - 1) * 0.05)
    
    return min(completion_rate * length_adjustment, 1.0)

def calculate_playlist_performance_score(avg_views, engagement_rate, video_count, completion_rate):
    """Calculate overall playlist performance score (0-100)"""
    views_score = min(avg_views / 10000, 1) * 30
    engagement_score = min(engagement_rate * 1000, 1) * 25
    completion_score = completion_rate * 25
    length_bonus = min(video_count / 10, 1) * 20
    return min(views_score + engagement_score + completion_score + length_bonus, 100)

def classify_monetization_potential(total_revenue, video_count):
    """Classify monetization potential of a playlist."""
    if video_count == 0: return 'None'
    avg_revenue = total_revenue / video_count
    if avg_revenue >= 50: return 'High'
    elif avg_revenue >= 10: return 'Medium'
    else: return 'Low'

def calculate_viewership_consistency(playlist_videos_data):
    """Calculate how consistent viewership is across playlist videos."""
    if len(playlist_videos_data) < 2: return 1.0
    view_counts = [v.get('view_count', 0) for v in playlist_videos_data]
    if not view_counts or max(view_counts) == 0: return 0.0
    mean_views = statistics.mean(view_counts)
    if mean_views == 0: return 0.0
    std_dev = statistics.stdev(view_counts) if len(view_counts) > 1 else 0
    return round(max(0, 1 - (std_dev / mean_views)), 3)

def analyze_playlist_content_themes(playlist_data):
    """Analyze content themes and patterns in a playlist."""
    title = playlist_data['title'].lower()
    description = playlist_data['description'].lower()
    
    return {
        'content_theme': classify_content_theme(title, description),
        'seasonal_pattern': detect_seasonal_pattern(playlist_data),
        'content_strategy': classify_content_strategy(playlist_data),
        'theme_keywords': extract_theme_keywords(title + ' ' + description),
    }

def classify_content_theme(title, description):
    """Classify the main content theme of a playlist."""
    text = (title + ' ' + description).lower()
    themes = {
        'Business & Finance': ['business', 'entrepreneur', 'startup', 'money', 'finance', 'investment', 'trading', 'forex'],
        'Education & Tutorial': ['tutorial', 'how to', 'learn', 'guide', 'course', 'training', 'tips', 'beginners'],
        'Lifestyle & Vlog': ['vlog', 'daily', 'life', 'lifestyle', 'routine', 'personal'],
        'Tech & Reviews': ['tech', 'review', 'gadget', 'software', 'unboxing'],
        'Entertainment': ['funny', 'comedy', 'reaction', 'challenge', 'music']
    }
    theme_scores = {theme: sum(1 for keyword in keywords if keyword in text) for theme, keywords in themes.items()}
    max_score = max(theme_scores.values())
    if max_score > 0:
        return max(theme_scores, key=theme_scores.get)
    return 'General'

def detect_seasonal_pattern(playlist_data):
    """Detect if a playlist has seasonal patterns."""
    if any(kw in playlist_data['title'].lower() for kw in ['summer', 'winter', 'spring', 'fall', 'holiday', 'christmas']):
        return 'Seasonal'
    return 'Year-round'

def classify_content_strategy(playlist_data):
    """Classify the content strategy behind a playlist."""
    count = playlist_data['item_count']
    title = playlist_data['title'].lower()
    if count >= 10: return 'Content Series'
    if count >= 5: return 'Mini-Series'
    if any(kw in title for kw in ['best of', 'compilation', 'highlights']): return 'Compilation'
    if any(kw in title for kw in ['tutorial', 'guide']): return 'Educational Series'
    return 'Curated Collection'

def extract_theme_keywords(text):
    """Extract key theme words from playlist title and description."""
    stop_words = {'the', 'and', 'for', 'of', 'in', 'to', 'a', 'is', 'with', 'on', 'that', 'by'}
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered_words = [word for word in words if word not in stop_words]
    return [word for word, count in Counter(filtered_words).most_common(5)]

def calculate_playlist_age(published_at):
    """Calculate playlist age in days."""
    try:
        published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        return (datetime.now(published_date.tzinfo) - published_date).days
    except:
        return 0

def classify_playlist_type(title):
    """Classify playlist by type based on title."""
    title_lower = title.lower()
    if 'uploads' in title_lower: return 'Main Uploads'
    if any(kw in title_lower for kw in ['series', 'season']): return 'Episodic Series'
    if any(kw in title_lower for kw in ['tutorial', 'how to']): return 'Tutorials'
    if any(kw in title_lower for kw in ['compilation', 'highlights']): return 'Compilation'
    return 'Thematic Collection'

def calculate_organization_analytics(playlists, channel_data):
    """Calculate channel-level organization and playlist analytics."""
    if not playlists: return {}
    content_playlists = [p for p in playlists if p['item_count'] > 0 and not p['is_main_uploads']]
    if not content_playlists: return {'total_playlists': len(playlists), 'content_playlists': 0}
    
    performance_scores = [p.get('playlist_performance_score', 0) for p in content_playlists if p.get('playlist_performance_score', 0) > 0]
    
    return {
        'total_playlists': len(playlists),
        'content_playlists': len(content_playlists),
        'avg_videos_per_playlist': round(statistics.mean([p['item_count'] for p in content_playlists])),
        'playlist_type_distribution': dict(Counter(p['playlist_type'] for p in content_playlists)),
        'content_theme_distribution': dict(Counter(p['content_theme'] for p in content_playlists)),
        'total_playlist_views': sum(p.get('total_playlist_views', 0) for p in content_playlists),
        'total_playlist_revenue': round(sum(p.get('total_playlist_revenue', 0) for p in content_playlists), 2),
        'avg_playlist_performance_score': round(statistics.mean(performance_scores), 2) if performance_scores else 0,
        'top_performing_playlists': sorted(
            [p for p in content_playlists if p.get('playlist_performance_score')], 
            key=lambda x: x.get('playlist_performance_score', 0), 
            reverse=True
        )[:3],
    }

def save_playlists_data(playlists_data, filename=None):
    """Save complete playlists analysis to a JSON file."""
    if not filename:
        channel_title = playlists_data['metadata']['channel_title'].replace(' ', '_')
        filename = f"{channel_title}_playlists_organization_analysis.json"
    
    with open(filename, 'w') as f:
        json.dump(playlists_data, f, indent=2, default=str)
    
    print(f"💾 Complete playlists analysis saved to {filename}")


if __name__ == "__main__":
    print("🔄 Running Standalone Test for Step 1.4: Playlists & Organization Analysis...")
    
    # To run this test, we must first get data from Step 1.1
    # This makes the test more realistic and demonstrates the data dependency.
    import scraping_1_1 as s11
    
    # --- CONFIGURATION for Standalone Test ---
    TEST_CHANNEL_URL = "https://www.youtube.com/@TheTradingChannel"
    
    try:
        print(f"--- (Test) Getting channel data for {TEST_CHANNEL_URL} using scraping-1.1 ---")
        channel_data = s11.get_enhanced_channel_statistics(TEST_CHANNEL_URL)
        
        # We don't have video performance data in this standalone test, so we pass None.
        # This correctly tests the basic playlist functionality.
        print(f"\n--- (Test) Running playlist analysis for {channel_data['channel_title']} ---")
        playlists_data = get_channel_playlists(channel_data, performance_data=None)
        
        # Save the standalone analysis
        if playlists_data:
            save_playlists_data(playlists_data)
        
        print("\n✅ Standalone playlist analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during standalone test: {e}")