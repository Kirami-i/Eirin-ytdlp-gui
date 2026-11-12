from dataclasses import replace

from eirin.config import Settings
from eirin.core.options import (
    build_download_options,
    build_probe_options,
    thumbnail_embedding_supported,
)


def make_settings(**kwargs) -> Settings:
    return replace(Settings(), **kwargs)


def test_audio_only_options():
    options = build_download_options(make_settings(), selector="best", audio_only=True)
    assert options["format"] == "ba/b"
    postprocessors = options["postprocessors"]
    assert postprocessors[0]["key"] == "FFmpegExtractAudio"
    assert postprocessors[0]["preferredcodec"] == "mp3"


def test_remux_container():
    settings = make_settings(container="mp4", embed_thumbnail=False, embed_metadata=False)
    options = build_download_options(settings, selector="best")
    keys = [item["key"] for item in options["postprocessors"]]
    assert "FFmpegVideoRemuxer" in keys


def test_subtitles_and_sponsorblock():
    settings = make_settings(
        write_subs=True,
        subtitle_langs="ru, en",
        embed_subs=True,
        sponsorblock=True,
        embed_thumbnail=False,
        embed_metadata=False,
    )
    options = build_download_options(settings, selector="best")
    assert options["subtitleslangs"] == ["ru", "en"]
    keys = [item["key"] for item in options["postprocessors"]]
    assert "FFmpegEmbedSubtitle" in keys
    assert "SponsorBlock" in keys
    assert "ModifyChapters" in keys


def test_playlist_flag_and_output_path():
    settings = make_settings(playlist=True)
    options = build_download_options(settings, selector="best")
    assert options["noplaylist"] is False
    assert options["paths"]["home"] == settings.output_dir
    assert options["outtmpl"]["default"] == settings.filename_template


def test_rate_limit_and_proxy():
    settings = make_settings(rate_limit="2M", proxy="socks5://127.0.0.1:9050")
    options = build_download_options(settings, selector="best")
    assert options["ratelimit"] == 2 * 1024**2
    assert options["proxy"] == "socks5://127.0.0.1:9050"


def test_probe_options():
    options = build_probe_options(Settings())
    assert options["skip_download"] is True
    assert options["playlistend"] == 1
    assert options["remote_components"] == {"ejs:github"}


def test_remote_components_can_be_disabled():
    options = build_download_options(
        make_settings(allow_remote_components=False), selector="best"
    )
    assert "remote_components" not in options


def test_thumbnail_embedding_supported_audio():
    assert thumbnail_embedding_supported(make_settings(audio_format="mp3"), audio_only=True)
    assert thumbnail_embedding_supported(make_settings(audio_format="flac"), audio_only=True)
    assert not thumbnail_embedding_supported(make_settings(audio_format="wav"), audio_only=True)


def test_thumbnail_embedding_supported_video():
    assert thumbnail_embedding_supported(make_settings(container="mp4"), audio_only=False)
    assert thumbnail_embedding_supported(make_settings(container="mkv"), audio_only=False)
    assert not thumbnail_embedding_supported(make_settings(container="auto"), audio_only=False)
    assert not thumbnail_embedding_supported(make_settings(container="webm"), audio_only=False)


def test_wav_skips_thumbnail_embedding():
    settings = make_settings(audio_format="wav")
    options = build_download_options(settings, selector="ba/b", audio_only=True)
    keys = [item["key"] for item in options["postprocessors"]]
    assert "EmbedThumbnail" not in keys
    assert options["writethumbnail"] is False


def test_mp3_embeds_thumbnail():
    settings = make_settings(audio_format="mp3")
    options = build_download_options(settings, selector="ba/b", audio_only=True)
    keys = [item["key"] for item in options["postprocessors"]]
    assert "EmbedThumbnail" in keys
    assert options["writethumbnail"] is True
