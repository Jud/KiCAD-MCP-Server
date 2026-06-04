"""SVG->PNG converter tests for get_board_2d_view rasterization (issue #209).

The added macOS Quick Look (qlmanage) step lets a Mac with no pymupdf/inkscape/
ImageMagick still rasterize instead of dropping to inline SVG. These cover that a
PNG comes back when any converter exists, and a graceful None when none do.
"""

import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from commands.board.view import _svg_to_png  # noqa: E402

_SVG = (
    '<?xml version="1.0"?>'
    '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
    '<rect width="64" height="64" fill="black"/>'
    '<circle cx="32" cy="32" r="20" fill="white"/>'
    "</svg>"
)

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _raise_not_found(*args, **kwargs):
    raise FileNotFoundError("no converter")


def test_svg_to_png_produces_png_when_a_converter_exists(tmp_path):
    if not any(shutil.which(t) for t in ("magick", "convert", "qlmanage", "inkscape")):
        pytest.skip("no SVG->PNG converter available on this host")
    svg = tmp_path / "in.svg"
    svg.write_text(_SVG)
    out = _svg_to_png(str(svg), 64, 64)
    assert out is not None
    assert out[:8] == _PNG_MAGIC


def test_svg_to_png_returns_none_when_no_converter_succeeds(tmp_path, monkeypatch):
    # Graceful None (the caller falls back to inline SVG) when every converter is
    # absent or fails. Stub the spawns and feed invalid SVG so the test is fast
    # and independent of which converters the host happens to have.
    import subprocess

    monkeypatch.setattr(subprocess, "run", _raise_not_found)
    bad = tmp_path / "in.svg"
    bad.write_text("not valid svg")  # also defeats pymupdf when it is installed
    assert _svg_to_png(str(bad), 64, 64) is None
