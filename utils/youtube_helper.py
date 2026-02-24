import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_top_videos(topic):
    search_url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": topic + " tutorial",
        "type": "video",
        "order": "viewCount",
        "maxResults": 3,
        "key": API_KEY
    }

    response = requests.get(search_url, params=params)
    data = response.json()

    videos = []

    for item in data.get("items", []):
        video = {
            "title": item["snippet"]["title"],
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
            "video_id": item["id"]["videoId"],
            "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        }
        videos.append(video)

    return videos