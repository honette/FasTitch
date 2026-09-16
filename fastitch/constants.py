APP_NAME = "FasTitch"
ORG_NAME = "FasTitch"

RATIO_W = 16
RATIO_H = 9

IMAGE_EXTS = {
    ".jpg",
    ".jpeg",
    ".jfif",
    ".png",
    ".gif",
    ".bmp",
    ".dib",
    ".webp",
    ".tif",
    ".tiff",
    ".ico",
    ".tga",
    ".ppm",
    ".pgm",
    ".pbm",
    ".heic",
    ".heif",
}

OPEN_FILTER = (
    "Images ("
    "*.jpg *.jpeg *.jfif *.png *.gif *.bmp *.webp *.tif *.tiff "
    "*.ico *.tga *.heic *.heif"
    ");;All files (*.*)"
)

OUTPUT_FORMATS = [
    ("JPEG", "jpeg"),
    ("PNG", "png"),
    ("WebP", "webp"),
]

DEFAULT_SUFFIX = "_stitched"
DEFAULT_FORMAT = "jpeg"
DEFAULT_JPEG_QUALITY = 92
