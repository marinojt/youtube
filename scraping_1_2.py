import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from datetime import datetime
import isodate  # For parsing YouTube duration format
import statistics

# API Setup - MUST be at the top
def setup_youtube_api():
    """Initialize YouTube API client"""
    API_KEY = 'AIzaSyDQDu7_yw-7P3xuaMp1F0qWOnn_iWCCRNc'
    if not API_KEY:
        raise ValueError("Please set YOUTUBE_API_KEY environment variable")
    
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    return youtube

def get_all_videos(channel_data):
    """
    Step 1.2 (Part 1): Get the list of all video uploads from a channel.
    This function collects the basic video metadata.
    """
    youtube = setup_youtube_api()
    
    uploads_playlist_id = channel_data['uploads_playlist_id']
    all_videos = []
    next_page_token = None
    api_calls_made = 0
    
    try:
        print(f"🔍 Collecting all video IDs from playlist: {uploads_playlist_id}")
        
        while True:
            playlist_request = youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            playlist_response = playlist_request.execute()
            api_calls_made += 1
            
            for item in playlist_response['items']:
                video_data = {
                    'video_id': item['contentDetails']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'position': item['snippet']['position'],
                    'channel_id': item['snippet']['channelId'],
                    'channel_title': item['snippet']['channelTitle'],
                    'thumbnail_high_url': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                    'upload_date': item['snippet']['publishedAt'][:10],
                    'days_since_upload': calculate_days_since_upload(item['snippet']['publishedAt']),
                }
                all_videos.append(video_data)
            
            next_page_token = playlist_response.get('nextPageToken')
            if not next_page_token:
                break
            
            print(f"📄 Collected {len(all_videos)} video IDs so far...")
        
        all_videos.sort(key=lambda x: x['published_at'], reverse=True)
        
        collection_metadata = {
            'total_videos_collected': len(all_videos),
            'list_api_calls': api_calls_made,
            'collection_date': datetime.now().isoformat(),
            'channel_id': channel_data['channel_id'],
            'channel_title': channel_data['channel_title'],
            'country': channel_data.get('country', 'US') # Pass country for CPM
        }
        
        print(f"✅ Successfully collected {len(all_videos)} video IDs.")
        return {'videos': all_videos, 'metadata': collection_metadata}
        
    except HttpError as e:
        raise Exception(f"YouTube API error: {e}")
    except Exception as e:
        raise Exception(f"Error collecting videos data: {e}")

def get_and_process_video_details(videos_data):
    """
    Step 1.2 (Part 2): Get enhanced details for all videos and calculate BI metrics.
    This function takes the list of videos and enriches it with stats, topics, and all calculations.
    """
    youtube = setup_youtube_api()
    
    videos = videos_data['videos']
    video_ids = [video['video_id'] for video in videos]
    country = videos_data['metadata'].get('country', 'US')
    
    print(f"📊 Getting enhanced details for {len(video_ids)} videos...")
    
    all_video_details = {}
    api_calls_made = 0
    
    try:
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            print(f"📈 Processing batch {i//50 + 1}...")
            
            details_response = youtube.videos().list(
                part='contentDetails,snippet,statistics,status,topicDetails',
                id=','.join(batch_ids)
            ).execute()
            api_calls_made += 1
            
            for item in details_response['items']:
                duration_seconds = parse_duration_to_seconds(item['contentDetails']['duration'])
                
                # The big BI calculation step
                bi_metrics = calculate_complete_bi_metrics(item, duration_seconds, country)
                
                # Combine raw API data with calculated metrics
                details = {
                    'video_id': item['id'],
                    'category_id': item['snippet']['categoryId'],
                    'tags': item['snippet'].get('tags', []),
                    'live_broadcast_content': item['snippet']['liveBroadcastContent'],
                    'duration': item['contentDetails']['duration'],
                    'duration_seconds': duration_seconds,
                    'definition': item['contentDetails'].get('definition', 'sd'),
                    'has_captions': item['contentDetails'].get('caption', 'false') == 'true',
                    'licensed_content': item['contentDetails'].get('licensedContent', False),
                    'privacy_status': item['status']['privacyStatus'],
                    'made_for_kids': item['status'].get('madeForKids', False),
                    'topic_categories': item.get('topicDetails', {}).get('topicCategories', []),
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'like_count': int(item['statistics'].get('likeCount', 0)),
                    'comment_count': int(item['statistics'].get('commentCount', 0)),
                    **bi_metrics  # Merge all calculated BI metrics
                }
                all_video_details[item['id']] = details
        
        # Merge the new details back into the original video list
        enhanced_videos = []
        for video in videos:
            if video['video_id'] in all_video_details:
                enhanced_video = {**video, **all_video_details[video['video_id']]}
                enhanced_videos.append(enhanced_video)
        
        videos_data['videos'] = enhanced_videos
        videos_data['metadata']['details_api_calls'] = api_calls_made
        videos_data['metadata']['total_api_calls'] = videos_data['metadata']['list_api_calls'] + api_calls_made
        videos_data['metadata']['performance_data_collected'] = len(enhanced_videos)
        
        # Add channel-level analytics summary
        videos_data['channel_analytics'] = calculate_comprehensive_channel_analytics(enhanced_videos)
        
        print(f"✅ Complete! Enriched {len(enhanced_videos)} videos with full BI metrics.")
        return videos_data
        
    except HttpError as e:
        raise Exception(f"YouTube API error: {e}")
    except Exception as e:
        raise Exception(f"Error collecting performance data: {e}")

# --- BI METRIC CALCULATION FUNCTIONS (from scraping-1.3.py) ---

def calculate_complete_bi_metrics(item, duration_seconds, country):
    """Calculate COMPLETE business intelligence metrics for a single video item from the API."""
    stats = item.get('statistics', {})
    views = int(stats.get('viewCount', 0))
    likes = int(stats.get('likeCount', 0))
    comments = int(stats.get('commentCount', 0))
    tags = item['snippet'].get('tags', [])
    
    # Avoid division by zero
    safe_views = max(views, 1)
    duration_minutes = max(duration_seconds / 60, 0.1)
    
    days_since_upload = calculate_days_since_upload(item['snippet']['publishedAt'])
    
    estimated_cpm = estimate_advanced_cpm(
        item['snippet']['categoryId'], country, duration_seconds
    )
    engagement_rate = (likes + comments) / safe_views

    return {
        # Core Ratios
        'engagement_rate': engagement_rate,
        'like_ratio': likes / safe_views,
        'comment_ratio': comments / safe_views,
        
        # Performance Velocity
        'views_per_day': views / max(days_since_upload, 1),
        
        # Content Analysis
        'title_length': len(item['snippet'].get('title', '')),
        'description_length': len(item['snippet'].get('description', '')),
        'tags_count': len(tags),
        'is_hd': item['contentDetails'].get('definition', 'sd') == 'hd',
        'content_category': get_category_name(item['snippet']['categoryId']),
        
        # Timing Analysis
        'upload_day_of_week': get_upload_day_of_week(item['snippet']['publishedAt']),
        'upload_hour': get_upload_hour(item['snippet']['publishedAt']),
        
        # Duration Analysis
        'duration_category': categorize_duration(duration_seconds),
        'views_per_minute': views / duration_minutes,
        
        # Revenue Estimation
        'estimated_cpm': estimated_cpm,
        'estimated_revenue': (views / 1000) * estimated_cpm,
        
        # Advanced Scores
        'performance_score': calculate_advanced_performance_score(views, likes, comments, engagement_rate, duration_seconds),
        'content_efficiency_score': calculate_content_efficiency_score(views, duration_minutes, likes, comments),
        'engagement_quality_score': calculate_engagement_quality_score(likes, comments, safe_views),
        'monetization_potential_score': calculate_monetization_potential(views, engagement_rate, duration_seconds, estimated_cpm),
        
        # Platform-specific Metrics
        'is_short': duration_seconds <= 60,
        'is_long_form': duration_seconds >= 600,
    }

def estimate_advanced_cpm(category_id, country='US', duration_seconds=0):
    """Advanced CPM estimation based on multiple factors."""
    base_cpm_rates = {
        '22': 3.50, '27': 8.50, '26': 4.00, '24': 2.50, '25': 6.00,
        '28': 9.00, '19': 5.50, '20': 2.20, '10': 1.80, '29': 12.00 # Finance
    }
    base_cpm = base_cpm_rates.get(category_id, 3.00)
    
    if duration_seconds >= 480: base_cpm *= 1.5 # 8+ mins for mid-rolls
    elif duration_seconds <= 60: base_cpm *= 0.15 # Shorts CPM
    
    country_multipliers = {'US': 1.0, 'CA': 0.9, 'GB': 0.95, 'AU': 0.9, 'DE': 0.85}
    base_cpm *= country_multipliers.get(country, 0.5)
    
    return round(base_cpm, 2)

def calculate_advanced_performance_score(views, likes, comments, engagement_rate, duration_seconds):
    """Calculate advanced performance score (0-100) with multiple factors."""
    view_score = min(views / 50000, 1) * 30
    engagement_score = min(engagement_rate * 25, 1) * 30 # Engagement rate of 4% gets full points
    social_score = min((likes + comments) / 1000, 1) * 20
    velocity_score = min((views / max(duration_seconds / 60, 1)) / 1000, 1) * 20
    return round(view_score + engagement_score + social_score + velocity_score, 2)

def calculate_content_efficiency_score(views, duration_minutes, likes, comments):
    """Calculate how efficiently content generates engagement per minute."""
    if duration_minutes <= 0.1: return 0
    views_per_min = views / duration_minutes
    engagement_per_min = (likes + comments) / duration_minutes
    return round(min((views_per_min / 1000) + (engagement_per_min / 10), 100), 2)

def calculate_engagement_quality_score(likes, comments, views):
    """Calculate quality of engagement (higher weight for comments)."""
    if views == 0: return 0
    weighted_engagement = ((comments * 3) + (likes * 1)) / views
    return round(min(weighted_engagement * 500, 100), 2)

def calculate_monetization_potential(views, engagement_rate, duration_seconds, estimated_cpm):
    """Calculate monetization potential score (0-100)."""
    revenue = (views / 1000) * estimated_cpm
    duration_factor = 1.5 if duration_seconds >= 480 else 1.0
    engagement_factor = min(engagement_rate * 50, 2.0)
    return round(min((revenue * duration_factor * engagement_factor) / 10, 100), 2)

# --- CHANNEL-LEVEL ANALYTICS (from scraping-1.3.py) ---

def calculate_comprehensive_channel_analytics(videos):
    """Calculate comprehensive channel-level analytics from all video performance data."""
    if not videos: return {}
    perf_videos = [v for v in videos if 'view_count' in v and v['view_count'] > 0]
    if not perf_videos: return {}

    views = [v['view_count'] for v in perf_videos]
    revenues = [v['estimated_revenue'] for v in perf_videos]
    scores = [v['performance_score'] for v in perf_videos]
    
    # Calculate monthly revenue estimate
    recent_videos = [v for v in perf_videos if v.get('days_since_upload', 999) <= 30]
    monthly_uploads = len(recent_videos)
    avg_rev_per_video = statistics.mean(revenues) if revenues else 0
    monthly_estimated_revenue = avg_rev_per_video * monthly_uploads

    return {
        'total_videos_analyzed': len(perf_videos),
        'total_views': sum(views),
        'total_estimated_revenue': sum(revenues),
        'avg_views_per_video': statistics.mean(views),
        'median_views_per_video': statistics.median(views),
        'avg_revenue_per_video': avg_rev_per_video,
        'monthly_estimated_revenue': monthly_estimated_revenue,
        'avg_performance_score': statistics.mean(scores),
        'top_10_performing_videos': get_top_performing_videos(perf_videos, 10, 'performance_score'),
        'top_10_earning_videos': get_top_performing_videos(perf_videos, 10, 'estimated_revenue'),
        'recent_performance_trend': analyze_recent_performance_trend(perf_videos),
    }

def get_top_performing_videos(videos, count, sort_key):
    """Get top performing videos by a specific metric."""
    sorted_videos = sorted(videos, key=lambda x: x.get(sort_key, 0), reverse=True)
    return [{
        'title': v['title'],
        'video_id': v['video_id'],
        'view_count': v['view_count'],
        'sort_metric_value': v.get(sort_key, 0)
    } for v in sorted_videos[:count]]

def analyze_recent_performance_trend(videos):
    """Analyze recent performance trend vs. older videos."""
    recent = [v for v in videos if v.get('days_since_upload', 999) <= 90]
    older = [v for v in videos if v.get('days_since_upload', 0) > 90]
    if not recent or not older: return 'insufficient_data'
    
    recent_avg_views = statistics.mean([v['view_count'] for v in recent])
    older_avg_views = statistics.mean([v['view_count'] for v in older])
    
    if recent_avg_views > older_avg_views * 1.2: return 'improving'
    elif recent_avg_views < older_avg_views * 0.8: return 'declining'
    else: return 'stable'

# --- HELPER FUNCTIONS ---

def parse_youtube_date(date_string):
    return datetime.fromisoformat(date_string.replace('Z', '+00:00'))

def calculate_days_since_upload(published_at):
    published_date = parse_youtube_date(published_at)
    return max(1, (datetime.now(published_date.tzinfo) - published_date).days)

def parse_duration_to_seconds(duration):
    try:
        return int(isodate.parse_duration(duration).total_seconds())
    except:
        return 0

def get_category_name(category_id):
    categories = {'1': 'Film & Animation','2': 'Autos & Vehicles','10': 'Music','15': 'Pets & Animals','17': 'Sports','19': 'Travel & Events','20': 'Gaming','22': 'People & Blogs','23': 'Comedy','24': 'Entertainment','25': 'News & Politics','26': 'Howto & Style','27': 'Education','28': 'Science & Technology','29': 'Nonprofits & Activism'}
    return categories.get(category_id, f'Category {category_id}')

def get_upload_day_of_week(published_at):
    return parse_youtube_date(published_at).strftime('%A')

def get_upload_hour(published_at):
    return parse_youtube_date(published_at).hour

def categorize_duration(duration_seconds):
    if duration_seconds <= 60: return 'Short'
    elif duration_seconds <= 300: return 'Short Form'
    elif duration_seconds <= 1200: return 'Medium Form'
    else: return 'Long Form'

# --- MAIN ORCHESTRATOR & SAVING ---

def get_all_videos_with_full_analysis(channel_data):
    """Single, ultimate function to get all videos with full analysis."""
    print(f"📹 Starting full video analysis for: {channel_data['channel_title']}")
    videos_data = get_all_videos(channel_data)
    if not videos_data['videos']:
        print("❌ No videos found for this channel.")
        return None
    
    full_videos_data = get_and_process_video_details(videos_data)
    return full_videos_data

def save_full_video_analysis(analysis_data, filename=None):
    """Saves the complete video analysis to a JSON file."""
    if not filename:
        channel_title = analysis_data['metadata']['channel_title'].replace(' ', '_')
        filename = f"{channel_title}_video_portfolio_analysis.json"
    
    with open(filename, 'w') as f:
        # Use a custom default function to handle datetime objects if any remain
        json.dump(analysis_data, f, indent=2, default=str)
    
    print(f"💾 Full video analysis saved to {filename}")
    return filename

# --- EXAMPLE USAGE ---

if __name__ == "__main__":
    # Sample channel data, assuming step 1.1 has been run
    sample_channel_data = {
        'channel_id': 'UCSDclSDfDZLCTfxbt64IotQ',
        'channel_title': 'Tanner Planes',
        'uploads_playlist_id': 'UUSDclSDfDZLCTfxbt64IotQ',
        'country': 'US' # Important for CPM estimation
    }
    
    print("🔄 Running COMPLETE Video Portfolio Analysis...")
    try:
        # This one function now does everything
        full_analysis = get_all_videos_with_full_analysis(sample_channel_data)
        
        if full_analysis:
            saved_file = save_full_video_analysis(full_analysis)
            
            # Print a high-level summary from the new channel_analytics key
            print("\n🎯 FINAL ANALYSIS SUMMARY:")
            analytics = full_analysis['channel_analytics']
            metadata = full_analysis['metadata']
            
            print(f"Channel: {metadata['channel_title']}")
            print(f"API Cost: {metadata['total_api_calls']} units")
            print(f"Total Videos Analyzed: {analytics['total_videos_analyzed']:,}")
            print(f"Total Views: {analytics['total_views']:,}")
            print(f"Total Estimated Revenue: ${analytics['total_estimated_revenue']:,.2f}")
            print(f"Est. Monthly Revenue: ${analytics['monthly_estimated_revenue']:,.2f}")
            print(f"Average Performance Score: {analytics['avg_performance_score']:.1f}/100")
            print(f"Performance Trend: {analytics['recent_performance_trend']}")
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")