import matplotlib

matplotlib.use("Agg")

import plots  # noqa: E402


def test_bundled_thai_font_is_used():
    # Sarabun renders Thai marks correctly in matplotlib; macOS Thonburi does not (floating vowels).
    assert plots.setup_style() == "Sarabun"
    assert matplotlib.rcParams["font.family"] == ["Sarabun"]
