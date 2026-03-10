"""
LeukAI — AlexNet Training & Evaluation Pipeline
=================================================
Trains an AlexNet model on a Peripheral Blood Smear (PBS) dataset
for leukemia classification with 4 classes:
    0: Benign
    1: Early Pre-B ALL
    2: Pre-B ALL
    3: Pro-B ALL

Dataset Structure Expected:
    dataset/
    ├── train/
    │   ├── Benign/
    │   ├── Early Pre-B ALL/
    │   ├── Pre-B ALL/
    │   └── Pro-B ALL/
    └── test/
        ├── Benign/
        ├── Early Pre-B ALL/
        ├── Pre-B ALL/
        └── Pro-B ALL/

Usage:
    python train_model.py --data_dir ./dataset --epochs 25 --batch_size 32
"""

import os
import argparse
import json
import time
import numpy as np
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# ── Configuration ────────────────────────────────────────────
CLASS_NAMES = ["Benign", "Early Pre-B", "Pre-B", "Pro-B"]
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ── Data Transforms ──────────────────────────────────────────
train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.3),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
    transforms.RandomAffine(degrees=0, translate=(0.05, 0.05)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

test_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


def build_model(num_classes=4, pretrained=True):
    """Build AlexNet with a custom classifier for leukemia classes."""
    if pretrained:
        model = models.alexnet(weights=models.AlexNet_Weights.DEFAULT)
        print("[INFO] Loaded ImageNet-pretrained AlexNet")
    else:
        model = models.alexnet(weights=None)
        print("[INFO] AlexNet initialized from scratch")

    # Freeze early feature layers for transfer learning
    for param in model.features[:8].parameters():
        param.requires_grad = False

    # Replace classifier
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

    return model.to(DEVICE)


def train_one_epoch(model, loader, criterion, optimizer, epoch, total_epochs):
    """Train for one epoch and return average loss + accuracy."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (images, labels) in enumerate(loader):
        images, labels = images.to(DEVICE), labels.to(DEVICE)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

        if (batch_idx + 1) % 20 == 0:
            print(f"  Epoch [{epoch+1}/{total_epochs}] "
                  f"Batch [{batch_idx+1}/{len(loader)}] "
                  f"Loss: {loss.item():.4f} "
                  f"Acc: {100.*correct/total:.2f}%")

    avg_loss = running_loss / total
    accuracy = 100.0 * correct / total
    return avg_loss, accuracy


@torch.no_grad()
def evaluate(model, loader):
    """Evaluate model and return loss, accuracy, all predictions and labels."""
    model.eval()
    criterion = nn.CrossEntropyLoss()
    running_loss = 0.0
    all_preds = []
    all_labels = []

    for images, labels in loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    avg_loss = running_loss / len(all_labels)
    accuracy = 100.0 * accuracy_score(all_labels, all_preds)
    return avg_loss, accuracy, np.array(all_preds), np.array(all_labels)


def plot_training_curves(history, save_path):
    """Save training/validation loss and accuracy curves."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(history['train_loss'], label='Train Loss', color='#3381ff')
    ax1.plot(history['val_loss'], label='Val Loss', color='#d946ef')
    ax1.set_title('Loss Curves', fontweight='bold')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(history['train_acc'], label='Train Acc', color='#3381ff')
    ax2.plot(history['val_acc'], label='Val Acc', color='#d946ef')
    ax2.set_title('Accuracy Curves', fontweight='bold')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Training curves saved to {save_path}")


def plot_confusion_matrix(cm, class_names, save_path):
    """Save a confusion matrix heatmap."""
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
    ax.set_title('Confusion Matrix', fontweight='bold', fontsize=14)
    plt.colorbar(im)

    tick_marks = np.arange(len(class_names))
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(class_names, rotation=45, ha='right', fontsize=9)
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(class_names, fontsize=9)

    # Add text annotations
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f'{cm[i, j]}',
                    ha='center', va='center',
                    color='white' if cm[i, j] > thresh else 'black',
                    fontsize=12, fontweight='bold')

    ax.set_ylabel('True Label', fontweight='bold')
    ax.set_xlabel('Predicted Label', fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Confusion matrix saved to {save_path}")


def main():
    parser = argparse.ArgumentParser(description='Train AlexNet for Leukemia Detection')
    parser.add_argument('--data_dir', type=str, required=True,
                        help='Path to dataset root (must have train/ and test/ subdirs)')
    parser.add_argument('--epochs', type=int, default=25)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=0.001)
    parser.add_argument('--output_dir', type=str, default='./backend/ml_models')
    parser.add_argument('--pretrained', action='store_true', default=True)
    args = parser.parse_args()

    print("=" * 60)
    print("  LeukAI - AlexNet Training Pipeline")
    print("=" * 60)
    print(f"  Device:     {DEVICE}")
    print(f"  Dataset:    {args.data_dir}")
    print(f"  Epochs:     {args.epochs}")
    print(f"  Batch Size: {args.batch_size}")
    print(f"  LR:         {args.lr}")
    print(f"  Output:     {args.output_dir}")
    print("=" * 60)

    # ── Load Data ────────────────────────────────────────
    train_dir = os.path.join(args.data_dir, 'train')
    test_dir = os.path.join(args.data_dir, 'test')

    if not os.path.exists(train_dir) or not os.path.exists(test_dir):
        print(f"\n[ERROR] Dataset not found!")
        print(f"Expected structure:")
        print(f"  {args.data_dir}/")
        print(f"  ├── train/")
        print(f"  │   ├── Benign/")
        print(f"  │   ├── Early Pre-B ALL/")
        print(f"  │   ├── Pre-B ALL/")
        print(f"  │   └── Pro-B ALL/")
        print(f"  └── test/")
        print(f"      ├── Benign/")
        print(f"      ├── Early Pre-B ALL/")
        print(f"      ├── Pre-B ALL/")
        print(f"      └── Pro-B ALL/")
        return

    train_dataset = datasets.ImageFolder(train_dir, transform=train_transform)
    test_dataset = datasets.ImageFolder(test_dir, transform=test_transform)

    print(f"\n[DATA] Training samples: {len(train_dataset)}")
    print(f"[DATA] Test samples:     {len(test_dataset)}")
    print(f"[DATA] Classes:          {train_dataset.classes}")
    print(f"[DATA] Class mapping:    {train_dataset.class_to_idx}")

    # Class distribution
    train_labels = [s[1] for s in train_dataset.samples]
    for cls_idx, cls_name in enumerate(train_dataset.classes):
        count = train_labels.count(cls_idx)
        print(f"       {cls_name}: {count} images")

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size,
                              shuffle=True, num_workers=2, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size,
                             shuffle=False, num_workers=2, pin_memory=True)

    # ── Build Model ──────────────────────────────────────
    model = build_model(num_classes=len(train_dataset.classes),
                        pretrained=args.pretrained)

    total_params = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n[MODEL] Total params:     {total_params:,}")
    print(f"[MODEL] Trainable params: {trainable:,}")

    # ── Training Setup ───────────────────────────────────
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()),
                           lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)

    # ── Training Loop ────────────────────────────────────
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    best_val_acc = 0.0
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Starting Training...")
    print(f"{'='*60}\n")
    start_time = time.time()

    for epoch in range(args.epochs):
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, epoch, args.epochs)
        val_loss, val_acc, _, _ = evaluate(model, test_loader)
        scheduler.step()

        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)

        lr = optimizer.param_groups[0]['lr']
        print(f"\nEpoch {epoch+1}/{args.epochs} | "
              f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
              f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | "
              f"LR: {lr:.6f}")

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            save_path = os.path.join(args.output_dir, 'alexnet_leukemia.pt')
            torch.save(model.state_dict(), save_path)
            print(f"  >> New best model saved! ({val_acc:.2f}%)")

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  Training Complete! ({elapsed/60:.1f} minutes)")
    print(f"  Best Validation Accuracy: {best_val_acc:.2f}%")
    print(f"{'='*60}")

    # ── Final Evaluation ─────────────────────────────────
    print("\n[EVAL] Loading best model for final evaluation...")
    best_path = os.path.join(args.output_dir, 'alexnet_leukemia.pt')
    model.load_state_dict(torch.load(best_path, map_location=DEVICE))

    val_loss, val_acc, preds, labels = evaluate(model, test_loader)

    # Use the actual class names from the dataset
    actual_names = train_dataset.classes

    print(f"\n{'='*60}")
    print(f"  FINAL MODEL EVALUATION")
    print(f"{'='*60}")
    print(f"\n  Overall Accuracy: {val_acc:.2f}%")
    print(f"\n  Classification Report:")
    print(classification_report(labels, preds, target_names=actual_names, digits=4))

    # Per-class metrics
    precision, recall, f1, support = precision_recall_fscore_support(
        labels, preds, average=None)
    print(f"\n  Per-Class Metrics:")
    print(f"  {'Class':<20} {'Precision':>10} {'Recall':>10} {'F1-Score':>10} {'Support':>10}")
    print(f"  {'-'*60}")
    for i, name in enumerate(actual_names):
        print(f"  {name:<20} {precision[i]:>10.4f} {recall[i]:>10.4f} "
              f"{f1[i]:>10.4f} {int(support[i]):>10}")

    # Macro & Weighted averages
    mac_p, mac_r, mac_f1, _ = precision_recall_fscore_support(
        labels, preds, average='macro')
    wt_p, wt_r, wt_f1, _ = precision_recall_fscore_support(
        labels, preds, average='weighted')
    print(f"\n  {'Macro Avg':<20} {mac_p:>10.4f} {mac_r:>10.4f} {mac_f1:>10.4f}")
    print(f"  {'Weighted Avg':<20} {wt_p:>10.4f} {wt_r:>10.4f} {wt_f1:>10.4f}")

    # Confusion matrix
    cm = confusion_matrix(labels, preds)
    print(f"\n  Confusion Matrix:")
    print(cm)

    # ── Save Artifacts ───────────────────────────────────
    plot_training_curves(history,
                         os.path.join(args.output_dir, 'training_curves.png'))
    plot_confusion_matrix(cm, actual_names,
                          os.path.join(args.output_dir, 'confusion_matrix.png'))

    # Save metrics JSON
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'epochs': args.epochs,
        'best_val_accuracy': round(best_val_acc, 4),
        'final_accuracy': round(val_acc, 4),
        'training_time_minutes': round(elapsed / 60, 2),
        'device': str(DEVICE),
        'class_names': actual_names,
        'per_class_precision': {n: round(float(p), 4) for n, p in zip(actual_names, precision)},
        'per_class_recall': {n: round(float(r), 4) for n, r in zip(actual_names, recall)},
        'per_class_f1': {n: round(float(f), 4) for n, f in zip(actual_names, f1)},
        'macro_f1': round(float(mac_f1), 4),
        'weighted_f1': round(float(wt_f1), 4),
        'confusion_matrix': cm.tolist(),
    }
    metrics_path = os.path.join(args.output_dir, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\n[OK] Metrics saved to {metrics_path}")
    print(f"[OK] Model saved to {best_path}")
    print(f"\nRestart the backend to load the trained model automatically!")


if __name__ == '__main__':
    main()
