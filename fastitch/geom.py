from __future__ import annotations

from dataclasses import dataclass

from fastitch.constants import RATIO_H, RATIO_W

MSG_EMPTY = "No images."
MSG_INVALID = "Image has invalid size."
MSG_FIRST_TOO_WIDE = "The first image is wider than 16:9. Choose a different first image."
MSG_TOO_NARROW = "One or more images are too narrow to fit 16:9 as equal-width panels."


class StitchError(ValueError):
    pass


@dataclass(frozen=True)
class Panel:
    scaled_width: int
    crop: tuple[int, int, int, int]


@dataclass(frozen=True)
class StitchPlan:
    height: int
    panels: tuple[Panel, ...]
    output_width: int
    trimmed: bool

    @property
    def panel_widths(self) -> tuple[int, ...]:
        return tuple(panel.crop[2] - panel.crop[0] for panel in self.panels)

    @property
    def divider_xs(self) -> tuple[int, ...]:
        xs: list[int] = []
        x = 0
        for width in self.panel_widths[:-1]:
            x += width
            xs.append(x)
        return tuple(xs)


def is_wider_than_16_9(width: int, height: int) -> bool:
    if width <= 0 or height <= 0:
        return True
    return width * RATIO_H > height * RATIO_W


def max_width_for_height(height: int) -> int:
    if height <= 0:
        return 0
    return (height * RATIO_W) // RATIO_H


def scaled_width(width: int, height: int, target_height: int) -> int:
    if width <= 0 or height <= 0 or target_height <= 0:
        return 1
    if height == target_height:
        return width
    return max(1, round(width * target_height / height))


def center_crop_box(width: int, height: int, target_width: int) -> tuple[int, int, int, int]:
    target_width = max(1, min(width, target_width))
    extra = width - target_width
    left = extra // 2
    return (left, 0, left + target_width, height)


def plan_stitch(sizes: list[tuple[int, int]]) -> StitchPlan:
    if not sizes:
        raise StitchError(MSG_EMPTY)
    width0, height0 = sizes[0]
    if width0 <= 0 or height0 <= 0:
        raise StitchError(MSG_INVALID)
    if is_wider_than_16_9(width0, height0):
        raise StitchError(MSG_FIRST_TOO_WIDE)

    height = height0
    scaled_widths: list[int] = []
    for width, src_height in sizes:
        if width <= 0 or src_height <= 0:
            raise StitchError(MSG_INVALID)
        scaled_widths.append(scaled_width(width, src_height, height))

    total = sum(scaled_widths)
    if not is_wider_than_16_9(total, height):
        panels = tuple(
            Panel(sw, (0, 0, sw, height)) for sw in scaled_widths
        )
        return StitchPlan(height, panels, total, False)

    count = len(scaled_widths)
    slot = max_width_for_height(height) // count
    if slot < 1:
        raise StitchError(MSG_TOO_NARROW)
    for sw in scaled_widths:
        if sw < slot:
            raise StitchError(MSG_TOO_NARROW)

    panels = tuple(Panel(sw, center_crop_box(sw, height, slot)) for sw in scaled_widths)
    return StitchPlan(height, panels, slot * count, True)
