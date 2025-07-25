import discord
from utils import format_duration, create_queue_embed, create_song_embed

class DummySong:
    def __init__(self, title, duration=60, uploader="test", thumbnail=None):
        self.title = title
        self.duration = duration
        self.uploader = uploader
        self.thumbnail = thumbnail

    def format_duration(self):
        return format_duration(self.duration)

class DummyQueue:
    def __init__(self):
        self.current = None
        self.queue = []
        self.loop_mode = False


def test_format_duration():
    assert format_duration(0) == "Unknown"
    assert format_duration(65) == "1:05"


def test_create_queue_embed_empty():
    q = DummyQueue()
    embed = create_queue_embed(q)
    assert embed.title == "🎵 Music Queue"
    assert embed.fields[0].name == "📝 Queue"


def test_create_queue_embed_with_songs():
    q = DummyQueue()
    q.current = DummySong("current")
    q.queue.append(DummySong("next"))
    q.loop_mode = True
    embed = create_queue_embed(q)
    field_names = [f.name for f in embed.fields]
    assert "🎵 Now Playing" in field_names
    assert "🔂 Loop Mode" in field_names
    assert any(name.startswith("📝 Up Next") for name in field_names)


def test_create_song_embed():
    song = DummySong("song", duration=70, uploader="me", thumbnail="http://x")
    embed = create_song_embed(song, title="Info")
    assert embed.title == "Info"
    assert embed.fields[0].name == "Duration"
    assert embed.fields[1].name == "Uploader"
