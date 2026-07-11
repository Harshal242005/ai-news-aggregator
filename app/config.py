import json
from pathlib import Path

_DISCOVERED_CHANNELS_PATH = Path(__file__).parent.parent / "data" / "channels.json"

MANUAL_YOUTUBE_CHANNELS = [
    # "UCn8ujwUInbJkBhffxqAPBVQ", # Dave Ebbelaar
    "UCawZsQWqfGSbCI5yjkdVkTA",  # Matthew Berman
]


def _load_discovered_channels() -> list[str]:
    if not _DISCOVERED_CHANNELS_PATH.exists():
        return []
    data = json.loads(_DISCOVERED_CHANNELS_PATH.read_text())
    return [c["channel_id"] for c in data]


YOUTUBE_CHANNELS = list(dict.fromkeys(MANUAL_YOUTUBE_CHANNELS + _load_discovered_channels()))