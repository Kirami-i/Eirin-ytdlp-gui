from eirin.core.formats import (
    BEST_SELECTOR,
    build_format_rows,
    human_bytes,
    human_duration,
    human_speed,
    parse_rate,
)


def test_human_bytes():
    assert human_bytes(None) == "—"
    assert human_bytes(0) == "—"
    assert human_bytes(512) == "512 B"
    assert human_bytes(1536) == "1.5 KiB"
    assert human_bytes(5 * 1024**2) == "5.0 MiB"


def test_human_duration():
    assert human_duration(None) == "—"
    assert human_duration(0) == "0:00"
    assert human_duration(65) == "1:05"
    assert human_duration(3725) == "1:02:05"


def test_human_speed():
    assert human_speed(None) == "—"
    assert human_speed(1024) == "1.0 KiB/s"


def test_parse_rate():
    assert parse_rate("") is None
    assert parse_rate("5M") == 5 * 1024**2
    assert parse_rate("500k") == 500 * 1024
    assert parse_rate("1.5G") == int(1.5 * 1024**3)
    assert parse_rate("abc") is None


def test_build_format_rows_presets_only():
    rows = build_format_rows(None)
    assert rows[0].selector == BEST_SELECTOR
    assert rows[0].is_preset
    assert rows[-1].audio_only


def test_build_format_rows_sorted_and_filtered():
    info = {
        "formats": [
            {
                "format_id": "140",
                "ext": "m4a",
                "vcodec": "none",
                "acodec": "mp4a.40.2",
                "abr": 129,
                "filesize": 2_000_000,
            },
            {
                "format_id": "137",
                "ext": "mp4",
                "vcodec": "avc1.640028",
                "acodec": "none",
                "height": 1080,
                "fps": 30,
                "filesize": 50_000_000,
            },
            {
                "format_id": "18",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "mp4a",
                "height": 360,
                "fps": 30,
                "filesize": 10_000_000,
            },
            {"format_id": "sb0", "ext": "mhtml", "vcodec": "none", "acodec": "none"},
        ]
    }
    rows = build_format_rows(info)
    formats = [row for row in rows if not row.is_preset]
    assert [row.format_id for row in formats] == ["137", "18", "140"]
    assert formats[0].selector == "137+ba/b"
    assert formats[0].audio_only is False
    assert formats[1].selector == "18"
    assert formats[2].audio_only is True
    assert formats[2].size == "1.9 MiB"
