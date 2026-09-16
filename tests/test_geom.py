import pytest

from fastitch.geom import (
    MSG_FIRST_TOO_WIDE,
    MSG_TOO_NARROW,
    StitchError,
    center_crop_box,
    is_wider_than_16_9,
    max_width_for_height,
    plan_stitch,
    scaled_width,
)


def test_is_wider_than_16_9() -> None:
    assert not is_wider_than_16_9(1600, 900)
    assert not is_wider_than_16_9(800, 900)
    assert is_wider_than_16_9(1601, 900)
    assert is_wider_than_16_9(2000, 900)


def test_max_width_for_height() -> None:
    assert max_width_for_height(900) == 1600
    assert max_width_for_height(901) == 1601


def test_scaled_width_identity_and_round() -> None:
    assert scaled_width(200, 100, 100) == 200
    assert scaled_width(200, 100, 50) == 100
    assert scaled_width(100, 50, 100) == 200


def test_center_crop_even_and_odd() -> None:
    assert center_crop_box(100, 40, 80) == (10, 0, 90, 40)
    assert center_crop_box(101, 40, 80) == (10, 0, 90, 40)


def test_no_trim_keeps_unequal_widths() -> None:
    plan = plan_stitch([(40, 100), (80, 100)])
    assert not plan.trimmed
    assert plan.height == 100
    assert plan.panel_widths == (40, 80)
    assert plan.output_width == 120


def test_trim_makes_equal_widths() -> None:
    plan = plan_stitch([(100, 100), (200, 100), (150, 100)])
    assert plan.trimmed
    slot = max_width_for_height(100) // 3
    assert slot == 59
    assert plan.panel_widths == (59, 59, 59)
    assert plan.output_width == 177
    assert not is_wider_than_16_9(plan.output_width, plan.height)


def test_two_squares_center_crop() -> None:
    plan = plan_stitch([(100, 100), (100, 100)])
    assert plan.trimmed
    slot = max_width_for_height(100) // 2
    assert slot == 88
    assert plan.panels[0].crop == (6, 0, 94, 100)
    assert plan.output_width == 176
    assert plan.divider_xs == (88,)


def test_exact_16_9_pair_trims_to_half() -> None:
    plan = plan_stitch([(160, 90), (160, 90)])
    assert plan.trimmed
    assert plan.output_width == 160
    assert plan.panel_widths == (80, 80)


def test_single_image_under_limit() -> None:
    plan = plan_stitch([(800, 900)])
    assert not plan.trimmed
    assert plan.output_width == 800
    assert plan.panel_widths == (800,)


def test_first_too_wide() -> None:
    with pytest.raises(StitchError, match="16:9"):
        plan_stitch([(2000, 900)])
    with pytest.raises(StitchError, match="16:9"):
        plan_stitch([(200, 100), (50, 100)])


def test_too_narrow_for_equal_slot() -> None:
    with pytest.raises(StitchError, match="narrow"):
        plan_stitch([(160, 90), (10, 90)])


def test_empty_and_invalid() -> None:
    with pytest.raises(StitchError):
        plan_stitch([])
    with pytest.raises(StitchError):
        plan_stitch([(0, 10)])


def test_scale_other_images_to_first_height() -> None:
    plan = plan_stitch([(20, 40), (80, 80)])
    assert plan.height == 40
    assert plan.panels[0].scaled_width == 20
    assert plan.panels[1].scaled_width == 40
    assert not plan.trimmed
    assert plan.output_width == 60


def test_error_messages_are_stable() -> None:
    assert "16:9" in MSG_FIRST_TOO_WIDE
    assert "narrow" in MSG_TOO_NARROW
