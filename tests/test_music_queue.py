import pytest
from music_queue import MusicQueue

class DummySong:
    def __init__(self, title):
        self.title = title

def test_queue_add_and_get_next():
    q = MusicQueue()
    s1 = DummySong("song1")
    s2 = DummySong("song2")
    q.add(s1)
    q.add(s2)
    assert q.size == 2
    assert not q.is_empty
    first = q.get_next()
    assert first is s1
    assert q.current is s1
    assert q.size == 1
    second = q.get_next()
    assert second is s2
    assert q.current is s2
    assert q.size == 0


def test_queue_loop_mode():
    q = MusicQueue()
    s1 = DummySong("song1")
    q.add(s1)
    q.get_next()
    q.loop_mode = True
    assert q.get_next() is s1


def test_queue_skip_and_clear():
    q = MusicQueue()
    s1 = DummySong("s1")
    s2 = DummySong("s2")
    q.add(s1)
    q.add(s2)
    q.get_next()  # play first
    skipped = q.skip()
    assert skipped is s2
    assert q.current is s2
    assert q.size == 0
    q.clear()
    assert q.is_empty


def test_queue_shuffle():
    q = MusicQueue()
    songs = [DummySong(str(i)) for i in range(5)]
    for song in songs:
        q.add(song)
    q.shuffle()
    assert set(s.title for s in q.queue) == set(str(i) for i in range(5))
