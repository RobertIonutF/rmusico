from alternative_extractor import AlternativeExtractor
from youtube_helper import get_troubleshooting_tips
from web_server import update_bot_status, bot_status
from ffmpeg_utils import ffmpeg_manager


def test_extract_video_id():
    url_variants = [
        "https://www.youtube.com/watch?v=abc123",
        "https://youtu.be/abc123",
        "https://www.youtube.com/embed/abc123",
        "https://www.youtube.com/v/abc123",
    ]
    for url in url_variants:
        assert AlternativeExtractor._extract_video_id(url) == "abc123"
    assert AlternativeExtractor._extract_video_id("https://example.com") is None


def test_get_troubleshooting_tips():
    tips = get_troubleshooting_tips()
    assert any("voice channel" in t for t in tips)


def test_update_bot_status():
    update_bot_status(connected=True, guilds=2)
    assert bot_status["connected"] is True
    assert bot_status["guilds"] == 2


def test_ffmpeg_options():
    opts = ffmpeg_manager.get_optimal_ffmpeg_options()
    assert "pcm" in opts and "opus" in opts
    assert "before_options" in opts["pcm"]
