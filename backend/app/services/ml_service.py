"""
ML Inference Service — AlexNet classification + Grad-CAM heatmap generation.

If no trained model file is found, a demo mode is used that returns
simulated predictions so the full UI/UX pipeline can be tested.
"""

import os
import io
import base64
import numpy as np
import cv2
from PIL import Image
from typing import Tuple, Dict, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms

from app.core.config import settings
from app.utils.image_processing import pil_to_base64, numpy_to_base64

# ── Globals ──────────────────────────────────────────────────
_model: Optional[nn.Module] = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_demo_mode = False

# ImageNet-normalised transform (AlexNet expects 227×227, but torchvision
# AlexNet internally adapts from 224; we use 224 for compatibility).
_transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


# ── Model loading ────────────────────────────────────────────
def load_model():
    """Load the AlexNet model from disk or fall back to demo mode."""
    global _model, _demo_mode

    model_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        settings.MODEL_PATH,
    )

    if os.path.exists(model_path):
        print(f"[ML] Loading trained model from {model_path}")
        model = models.alexnet(weights=None)
        num_classes = len(settings.CLASS_NAMES)

        # Try v2 architecture first (with BatchNorm), fall back to v1
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.5),
            nn.Linear(256 * 6 * 6, 4096),
            nn.BatchNorm1d(4096),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.4),
            nn.Linear(4096, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.3),
            nn.Linear(1024, num_classes),
        )
        try:
            model.load_state_dict(torch.load(model_path, map_location=_device))
            print("[ML] Loaded v2 model (BatchNorm)")
        except RuntimeError:
            # Fallback to v1 architecture (without BatchNorm)
            print("[ML] v2 mismatch, trying v1 architecture...")
            model.classifier = nn.Sequential(
                nn.Dropout(p=0.5),
                nn.Linear(256 * 6 * 6, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(p=0.5),
                nn.Linear(4096, 1024),
                nn.ReLU(inplace=True),
                nn.Dropout(p=0.3),
                nn.Linear(1024, num_classes),
            )
            model.load_state_dict(torch.load(model_path, map_location=_device))
            print("[ML] Loaded v1 model")
        model.to(_device)
        model.eval()
        _model = model
        _demo_mode = False
    else:
        print("[WARN] Trained model not found -- running in DEMO mode")
        model = models.alexnet(weights=models.AlexNet_Weights.DEFAULT)
        num_classes = len(settings.CLASS_NAMES)
        model.classifier[6] = nn.Linear(4096, num_classes)
        model.to(_device)
        model.eval()
        _model = model
        _demo_mode = True

    print(f"[OK] Model ready on {_device}  (demo={_demo_mode})")


# ── Grad-CAM ─────────────────────────────────────────────────
def _generate_gradcam(model, input_tensor, class_idx):
    """
    Generate a Grad-CAM heatmap for the given input and class.
    
    Uses retain_grad() on activations to capture gradients, avoiding
    both module backward hooks (conflict with inplace ReLU) and
    tensor hooks on clones (disconnected from computation graph).
    """
    activations = {}

    # AlexNet features[10] is the last Conv2d (conv5)
    target_layer = model.features[10]

    def forward_hook(module, inp, out):
        # Don't detach — keep in computation graph
        # Use retain_grad so we can read .grad after backward
        out.retain_grad()
        activations['output'] = out

    fh = target_layer.register_forward_hook(forward_hook)

    try:
        model.zero_grad()
        output = model(input_tensor)
        target = output[0, class_idx]
        target.backward()

        if 'output' not in activations or activations['output'].grad is None:
            print("[WARN] Grad-CAM: no gradient on activations")
            return np.zeros((224, 224), dtype=np.float32)

        act = activations['output'].detach()
        grad = activations['output'].grad.detach()

        # GAP over spatial dims to get channel importance weights
        weights = grad.mean(dim=(2, 3), keepdim=True)
        cam = (weights * act).sum(dim=1, keepdim=True)
        cam = F.relu(cam)
        cam = cam.squeeze().cpu().numpy()

        # Normalize to [0, 1]
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max - cam_min > 1e-8:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            print(f"[WARN] Grad-CAM: flat cam (min={cam_min:.6f}, max={cam_max:.6f})")
            cam = np.zeros_like(cam)

        cam = cv2.resize(cam, (224, 224))
        return cam

    finally:
        fh.remove()


# ── Public API ───────────────────────────────────────────────
def run_inference(pil_image: Image.Image) -> Dict:
    """
    Run classification + Grad-CAM on a PIL image.

    Returns
    -------
    dict with keys:
        classification  – predicted class name
        confidence      – float 0-1
        all_probabilities – {class_name: float}
        heatmap_base64  – base64-encoded heatmap overlay PNG
        image_base64    – base64-encoded original image PNG
    """
    if _model is None:
        load_model()

    # Prepare tensor for classification (no gradients needed)
    input_tensor = _transform(pil_image).unsqueeze(0).to(_device)

    with torch.no_grad():
        logits = _model(input_tensor)
    probs = F.softmax(logits, dim=1).squeeze().cpu().numpy()

    pred_idx = int(np.argmax(probs))
    classification = settings.CLASS_NAMES[pred_idx]
    confidence = float(probs[pred_idx])
    all_probs = {
        name: round(float(p), 4)
        for name, p in zip(settings.CLASS_NAMES, probs)
    }

    # Grad-CAM — needs a FRESH tensor with gradients enabled
    try:
        grad_input = _transform(pil_image).unsqueeze(0).to(_device)
        grad_input.requires_grad_(True)
        cam = _generate_gradcam(_model, grad_input, pred_idx)
    except Exception as e:
        print(f"[WARN] Grad-CAM failed: {e}, using fallback heatmap")
        import traceback
        traceback.print_exc()
        cam = np.zeros((224, 224), dtype=np.float32)

    # Build overlay
    orig_resized = pil_image.resize((224, 224), Image.LANCZOS)
    orig_np = np.array(orig_resized, dtype=np.float32) / 255.0

    heatmap_color = cv2.applyColorMap(
        (cam * 255).astype(np.uint8), cv2.COLORMAP_JET
    )
    heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB).astype(
        np.float32
    ) / 255.0

    overlay = 0.55 * orig_np + 0.45 * heatmap_color
    overlay = np.clip(overlay, 0, 1)

    return {
        "classification": classification,
        "confidence": confidence,
        "all_probabilities": all_probs,
        "heatmap_base64": numpy_to_base64(overlay),
        "image_base64": pil_to_base64(orig_resized),
    }

