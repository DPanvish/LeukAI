"""Test Grad-CAM with retain_grad() approach"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torchvision import models

model = models.alexnet(weights=None)
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
    nn.Linear(1024, 4),
)
model.load_state_dict(torch.load('backend/ml_models/alexnet_leukemia.pt', map_location='cpu'))
model.eval()
print("[OK] Model loaded")

# Step 1: Classification (no_grad)
x_img = torch.randn(1, 3, 224, 224)
with torch.no_grad():
    logits = model(x_img)
probs = F.softmax(logits, dim=1).squeeze().cpu().numpy()
pred_idx = int(np.argmax(probs))
print(f"[OK] pred_idx={pred_idx}")

# Step 2: Grad-CAM with retain_grad
activations = {}
target_layer = model.features[10]

def forward_hook(module, inp, out):
    out.retain_grad()
    activations['output'] = out

fh = target_layer.register_forward_hook(forward_hook)

model.zero_grad()
grad_input = torch.randn(1, 3, 224, 224)
grad_input.requires_grad_(True)
output = model(grad_input)
target = output[0, pred_idx]
target.backward()
fh.remove()

has_act = 'output' in activations
has_grad = has_act and activations['output'].grad is not None

print(f"activations captured: {has_act}")
print(f"gradients captured: {has_grad}")

if has_act and has_grad:
    act = activations['output'].detach()
    grad = activations['output'].grad.detach()
    weights = grad.mean(dim=(2, 3), keepdim=True)
    cam = (weights * act).sum(dim=1, keepdim=True)
    cam = F.relu(cam).squeeze().numpy()
    print(f"cam min={cam.min():.6f}, max={cam.max():.6f}")
    if cam.max() - cam.min() > 1e-8:
        print("SUCCESS: Grad-CAM produces varied heatmap!")
    else:
        print("FAIL: cam is flat")
else:
    print("FAIL: no gradient data")
