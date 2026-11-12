from eirin.config import Settings


def test_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(output_dir=str(tmp_path), retries=3, audio_format="m4a")
    settings.save(path)

    loaded = Settings.load(path)
    assert loaded.output_dir == str(tmp_path)
    assert loaded.retries == 3
    assert loaded.audio_format == "m4a"


def test_missing_file_uses_defaults(tmp_path):
    loaded = Settings.load(tmp_path / "missing.json")
    assert loaded.retries == 10
    assert loaded.concurrent_downloads == 2


def test_broken_json_uses_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")
    assert Settings.load(path).audio_format == "mp3"


def test_unknown_keys_are_ignored(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"retries": 4, "unknown_option": true}', encoding="utf-8")
    loaded = Settings.load(path)
    assert loaded.retries == 4
