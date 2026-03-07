"""Tests for shared quality parsing."""

from threep_commons.quality import parse_quality


def test_parse_quality() -> None:
    assert parse_quality("Movie.2160p.REMUX.x265.DV.mkv") == "2160p REMUX HEVC DV"
    assert parse_quality("Show.1080p.WEB-DL.H264.mkv") == "1080p WEB-DL x264"
