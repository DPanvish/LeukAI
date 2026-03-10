"""
Image preprocessing utilities using OpenCV and PIL.
Handles validation, resizing, normalization for the AlexNet model.
"""

import io
import base64
import numpy as np
import cv2
from PIL import Image
from typing import Tuple

from app.core.config import settings


def validate_image(file_bytes: bytes, filename: str) -> bool:
    """Validate image file size and extension."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        return False
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE:
        return False
    return True


def bytes_to_pil(file_bytes: bytes) -> Image.Image:
    """Convert raw bytes to a PIL Image."""
    return Image.open(io.BytesIO(file_bytes)).convert("RGB")


def pil_to_base64(img: Image.Image, fmt: str = "PNG") -> str:
    """Convert a PIL Image to a base64-encoded string."""
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def numpy_to_base64(arr: np.ndarray) -> str:
    """Convert a NumPy array (BGR or RGB) to base64 PNG string."""
    if arr.dtype != np.uint8:
        arr = (arr * 255).astype(np.uint8)
    if len(arr.shape) == 3 and arr.shape[2] == 3:
        arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    _, buf = cv2.imencode(".png", arr)
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def preprocess_for_alexnet(
    img: Image.Image, size: Tuple[int, int] = (227, 227)
) -> np.ndarray:
    """
    Resize and normalize an image for AlexNet inference.
    Returns a NumPy array (C, H, W) with ImageNet normalization.
    """
    img = img.resize(size, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    arr = (arr - mean) / std
    arr = arr.transpose(2, 0, 1)  # H,W,C → C,H,W
    return arr
