import os
import json
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

API_KEY = os.getenv("YOUTUBE_API_KEY")
SEARCH_QUERIES = ["AI news", "artificial intelligence research", "LLM news"]
MIN_SUBSCRIBERS = 10_000
MAX_INACTIVITY_DAYS = 30
MAX_CHANNELS = 15

OUTPUT_PATH = Path(__file__).parent.parent.parent / "data" / "channels.json"


def search_channels(query: str) -> list[str]:
    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/search",
        params={
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": 10,
            "key": API_KEY,
        },
    )
    resp.raise_for_status()
    return [item["snippet"]["channelId"] for item in resp.json().get("items", [])]


def get_channel_details(channel_ids: list[str]) -> list[dict]:
    if not channel_ids:
        return []
    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={
            "part": "snippet,statistics",
            "id": ",".join(channel_ids),
            "key": API_KEY,
        },
    )
    resp.raise_for_status()
    return resp.json().get("items", [])


def has_recent_upload(channel_id: str) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_INACTIVITY_DAYS)
    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/search",
        params={
            "part": "snippet",
            "channelId": channel_id,
            "order": "date",
            "maxResults": 1,
            "type": "video",
            "key": API_KEY,
        },
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if not items:
        return False
    published_at = datetime.fromisoformat(
        items[0]["snippet"]["publishedAt"].replace("Z", "+00:00")
    )
    return published_at >= cutoff


def discover_channels() -> list[dict]:
    if not API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY is not set")

    candidate_ids = set()
    for query in SEARCH_QUERIES:
        candidate_ids.update(search_channels(query))

    details = get_channel_details(list(candidate_ids))

    qualified = []
    for channel in details:
        sub_count = int(channel["statistics"].get("subscriberCount", 0))
        if sub_count < MIN_SUBSCRIBERS:
            continue
        channel_id = channel["id"]
        if not has_recent_upload(channel_id):
            continue
        qualified.append({
            "channel_id": channel_id,
            "title": channel["snippet"]["title"],
            "subscriber_count": sub_count,
        })

    qualified.sort(key=lambda c: c["subscriber_count"], reverse=True)
    return qualified[:MAX_CHANNELS]


def main():
    channels = discover_channels()
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(channels, indent=2))
    print(f"Discovered {len(channels)} channels, written to {OUTPUT_PATH}")
    for c in channels:
        print(f"  - {c['title']} ({c['subscriber_count']:,} subs)")


if __name__ == "__main__":
    main()