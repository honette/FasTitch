from pathlib import Path

from fastitch.naming import example_name, next_dest_path, normalize_suffix


def test_example_name_default() -> None:
    assert example_name("photo.jpg") == "photo_stitched.jpg"
    assert example_name("photo.png", suffix="_stitched", subfolder="out", ext=".jpg") == (
        "out/photo_stitched.jpg"
    )


def test_empty_suffix_falls_back() -> None:
    assert normalize_suffix("  ") == "_stitched"
    assert example_name("photo.jpg", suffix="") == "photo_stitched.jpg"


def test_next_default_and_collision(tmp_path: Path) -> None:
    source = tmp_path / "cat.jpg"
    source.write_bytes(b"x")
    dest = next_dest_path(source, ext=".jpg")
    assert dest.name == "cat_stitched.jpg"
    dest.write_bytes(b"x")
    dest2 = next_dest_path(source, ext=".jpg")
    assert dest2.name == "cat_stitched_2.jpg"
    dest2.write_bytes(b"x")
    dest3 = next_dest_path(source, ext=".jpg")
    assert dest3.name == "cat_stitched_3.jpg"


def test_never_overwrites_source(tmp_path: Path) -> None:
    source = tmp_path / "shot_stitched.jpg"
    source.write_bytes(b"x")
    dest = next_dest_path(source, suffix="_stitched", ext=".jpg")
    assert dest != source
    assert dest.name == "shot_stitched_stitched.jpg"


def test_subfolder_created(tmp_path: Path) -> None:
    source = tmp_path / "a.webp"
    source.write_bytes(b"x")
    dest = next_dest_path(source, subfolder="join", ext=".jpg")
    assert dest == tmp_path / "join" / "a_stitched.jpg"
    assert dest.parent.is_dir()
