"""
LeukAI v2 — Improved Training Pipeline
========================================
Key improvements over v1:
  1. Class-weighted loss to handle Benign imbalance
  2. Full fine-tuning (unfreeze all layers with differential LR)
  3. Stronger augmentation (especially for minority class)
  4. Cosine annealing LR schedule
  5. Label smoothing to reduce overconfidence
  6. Longer training with early stopping
  7. Test-time augmentation (TTA) for final evaluation
"""

import os
import argparse
import json
import time
import numpy as np
from datetime import datetime
from collections import Counter

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
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

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ── Data Transforms (stronger augmentation) ──────────────────
train_transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomCrop(224),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.5),
    transforms.RandomRotation(30),
    transforms.RandomAffine(
        degrees=0,
        translate=(0.1, 0.1),
        scale=(0.85, 1.15),
        shear=10,
    ),
    transforms.ColorJitter(
        brightness=0.3,
        contrast=0.3,
        saturation=0.2,
        hue=0.05,
    ),
    transforms.RandomGrayscale(p=0.05),
    transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.2, scale=(0.02, 0.15)),
])

test_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# TTA transforms for more robust final evaluation
tta_transforms = [
    test_transform,
    transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=1.0),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]),
    transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]),
]


def build_model(num_classes=4):
    """
    Build AlexNet with differential fine-tuning:
      - All layers trainable (no freezing)
      - Improved classifier with BatchNorm
    """
    model = models.alexnet(weights=models.AlexNet_Weights.DEFAULT)
    print("[INFO] Loaded ImageNet-pretrained AlexNet (all layers trainable)")

    # Improved classifier with BatchNorm for stability
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

    # Initialize classifier weights properly
    for m in model.classifier.modules():
        if isinstance(m, nn.Linear):
            nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.BatchNorm1d):
            nn.init.constant_(m.weight, 1)
            nn.init.constant_(m.bias, 0)

    return model.to(DEVICE)


def get_class_weights(dataset):
    """Compute inverse-frequency class weights for balanced loss."""
    labels = [s[1] for s in dataset.samples]
    counter = Counter(labels)
    total = len(labels)
    num_classes = len(counter)
    weights = []
    for i in range(num_classes):
        w = total / (num_classes * counter[i])
        weights.append(w)
    return torch.FloatTensor(weights).to(DEVICE)


def get_balanced_sampler(dataset):
    """Create a WeightedRandomSampler to oversample minority classes."""
    labels = [s[1] for s in dataset.samples]
    counter = Counter(labels)
    class_weights = {cls: len(labels) / count for cls, count in counter.items()}
    sample_weights = [class_weights[label] for label in labels]
    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(labels),
        replacement=True,
    )
    return sampler


def train_one_epoch(model, loader, criterion, optimizer, epoch, total_epochs):
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

        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
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

    return running_loss / total, 100.0 * correct / total


@torch.no_grad()
def evaluate(model, loader):
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


@torch.no_grad()
def evaluate_tta(model, dataset, num_augments=3):
    """Test-Time Augmentation: average predictions across multiple augmented views."""
    model.eval()
    all_preds = []
    all_labels = []

    for idx in range(len(dataset)):
        img_path, label = dataset.samples[idx]
        from PIL import Image
        img = Image.open(img_path).convert('RGB')

        # Collect predictions from each TTA transform
        logits_sum = None
        for tfm in tta_transforms[:num_augments]:
            tensor = tfm(img).unsqueeze(0).to(DEVICE)
            logits = model(tensor)
            if logits_sum is None:
                logits_sum = logits
            else:
                logits_sum += logits

        pred = logits_sum.argmax(dim=1).item()
        all_preds.append(pred)
        all_labels.append(label)

        if (idx + 1) % 200 == 0:
            print(f"  TTA progress: {idx+1}/{len(dataset)}")

    accuracy = 100.0 * accuracy_score(all_labels, all_preds)
    return accuracy, np.array(all_preds), np.array(all_labels)


def plot_training_curves(history, save_path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.plot(history['train_loss'], label='Train Loss', color='#3381ff', linewidth=2)
    ax1.plot(history['val_loss'], label='Val Loss', color='#d946ef', linewidth=2)
    ax1.set_title('Loss Curves (v2)', fontweight='bold')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(history['train_acc'], label='Train Acc', color='#3381ff', linewidth=2)
    ax2.plot(history['val_acc'], label='Val Acc', color='#d946ef', linewidth=2)
    ax2.set_title('Accuracy Curves (v2)', fontweight='bold')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Training curves saved to {save_path}")


def plot_confusion_matrix(cm, class_names, save_path):
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
    ax.set_title('Confusion Matrix (v2)', fontweight='bold', fontsize=14)
    plt.colorbar(im)

    tick_marks = np.arange(len(class_names))
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(class_names, rotation=45, ha='right', fontsize=9)
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(class_names, fontsize=9)

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
    parser = argparse.ArgumentParser(description='Train AlexNet v2')
    parser.add_argument('--data_dir', type=str, required=True)
    parser.add_argument('--epochs', type=int, default=40)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=0.0005)
    parser.add_argument('--output_dir', type=str, default='./backend/ml_models')
    parser.add_argument('--patience', type=int, default=10,
                        help='Early stopping patience')
    args = parser.parse_args()

    print("=" * 60)
    print("  LeukAI v2 - Improved Training Pipeline")
    print("=" * 60)
    print(f"  Device:     {DEVICE}")
    print(f"  Dataset:    {args.data_dir}")
    print(f"  Epochs:     {args.epochs}")
    print(f"  Batch Size: {args.batch_size}")
    print(f"  LR:         {args.lr}")
    print(f"  Patience:   {args.patience}")
    print("=" * 60)
    print()
    print("  IMPROVEMENTS in v2:")
    print("  [1] Class-weighted loss (handles Benign imbalance)")
    print("  [2] Full fine-tuning (all layers, differential LR)")
    print("  [3] Stronger augmentation + RandomErasing")
    print("  [4] Cosine annealing LR schedule")
    print("  [5] Label smoothing (0.1)")
    print("  [6] BatchNorm in classifier")
    print("  [7] Oversampling minority classes")
    print("  [8] Gradient clipping")
    print("  [9] Test-Time Augmentation (TTA)")
    print("=" * 60)

    # ── Load Data ────────────────────────────────────────
    train_dir = os.path.join(args.data_dir, 'train')
    test_dir = os.path.join(args.data_dir, 'test')

    if not os.path.exists(train_dir) or not os.path.exists(test_dir):
        print("[ERROR] Dataset not found!")
        return

    train_dataset = datasets.ImageFolder(train_dir, transform=train_transform)
    test_dataset = datasets.ImageFolder(test_dir, transform=test_transform)

    print(f"\n[DATA] Training samples: {len(train_dataset)}")
    print(f"[DATA] Test samples:     {len(test_dataset)}")
    print(f"[DATA] Classes:          {train_dataset.classes}")

    # Class distribution
    train_labels = [s[1] for s in train_dataset.samples]
    for cls_idx, cls_name in enumerate(train_dataset.classes):
        count = train_labels.count(cls_idx)
        print(f"       {cls_name}: {count} images")

    # Class weights for loss
    class_weights = get_class_weights(train_dataset)
    print(f"\n[BALANCE] Class weights: {class_weights.cpu().numpy()}")

    # Balanced sampler for oversampling
    sampler = get_balanced_sampler(train_dataset)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size,
                              sampler=sampler, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size,
                             shuffle=False, num_workers=0)

    # ── Build Model ──────────────────────────────────────
    model = build_model(num_classes=len(train_dataset.classes))

    total_params = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n[MODEL] Total params:     {total_params:,}")
    print(f"[MODEL] Trainable params: {trainable:,}")

    # ── Optimizer with differential LR ───────────────────
    # Features get a lower LR, classifier gets the full LR
    param_groups = [
        {'params': model.features.parameters(), 'lr': args.lr * 0.1},
        {'params': model.classifier.parameters(), 'lr': args.lr},
    ]
    optimizer = optim.AdamW(param_groups, weight_decay=1e-3)

    # Label-smoothing + class-weighted loss
    criterion = nn.CrossEntropyLoss(
        weight=class_weights,
        label_smoothing=0.1,
    )

    # Cosine annealing
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.epochs, eta_min=1e-6)

    # ── Training Loop ────────────────────────────────────
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    best_val_acc = 0.0
    patience_counter = 0
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

        feat_lr = optimizer.param_groups[0]['lr']
        cls_lr = optimizer.param_groups[1]['lr']
        print(f"\nEpoch {epoch+1}/{args.epochs} | "
              f"Train: {train_loss:.4f} / {train_acc:.2f}% | "
              f"Val: {val_loss:.4f} / {val_acc:.2f}% | "
              f"LR: feat={feat_lr:.7f} cls={cls_lr:.6f}")

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            save_path = os.path.join(args.output_dir, 'alexnet_leukemia.pt')
            torch.save(model.state_dict(), save_path)
            print(f"  >> New best model saved! ({val_acc:.2f}%)")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"\n  [STOP] Early stopping at epoch {epoch+1} "
                      f"(no improvement for {args.patience} epochs)")
                break

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  Training Complete! ({elapsed/60:.1f} minutes)")
    print(f"  Best Validation Accuracy: {best_val_acc:.2f}%")
    print(f"{'='*60}")

    # ── Final Evaluation ─────────────────────────────────
    print("\n[EVAL] Loading best model for final evaluation...")
    best_path = os.path.join(args.output_dir, 'alexnet_leukemia.pt')
    model.load_state_dict(torch.load(best_path, map_location=DEVICE))

    # Standard evaluation
    val_loss, val_acc, preds, labels = evaluate(model, test_loader)
    actual_names = train_dataset.classes

    print(f"\n{'='*60}")
    print(f"  STANDARD EVALUATION")
    print(f"{'='*60}")
    print(f"\n  Overall Accuracy: {val_acc:.2f}%")
    print(classification_report(labels, preds, target_names=actual_names, digits=4))

    # Test-Time Augmentation evaluation
    print(f"\n{'='*60}")
    print(f"  TEST-TIME AUGMENTATION (TTA)")
    print(f"{'='*60}")
    tta_acc, tta_preds, tta_labels = evaluate_tta(model, test_dataset)
    print(f"\n  TTA Accuracy: {tta_acc:.2f}%")
    print(classification_report(tta_labels, tta_preds,
                                target_names=actual_names, digits=4))

    # Use TTA results for final metrics
    final_preds = tta_preds
    final_labels = tta_labels
    final_acc = tta_acc

    precision, recall, f1, support = precision_recall_fscore_support(
        final_labels, final_preds, average=None)

    print(f"\n  Per-Class Metrics (TTA):")
    print(f"  {'Class':<20} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}")
    print(f"  {'-'*60}")
    for i, name in enumerate(actual_names):
        print(f"  {name:<20} {precision[i]*100:>9.2f}% {recall[i]*100:>9.2f}% "
              f"{f1[i]*100:>9.2f}%")

    mac_p, mac_r, mac_f1, _ = precision_recall_fscore_support(
        final_labels, final_preds, average='macro')
    wt_p, wt_r, wt_f1, _ = precision_recall_fscore_support(
        final_labels, final_preds, average='weighted')
    print(f"\n  {'Macro Avg':<20} {mac_p*100:>9.2f}% {mac_r*100:>9.2f}% {mac_f1*100:>9.2f}%")
    print(f"  {'Weighted Avg':<20} {wt_p*100:>9.2f}% {wt_r*100:>9.2f}% {wt_f1*100:>9.2f}%")

    cm = confusion_matrix(final_labels, final_preds)
    print(f"\n  Confusion Matrix:")
    print(cm)

    # ── Save Artifacts ───────────────────────────────────
    plot_training_curves(history,
                         os.path.join(args.output_dir, 'training_curves.png'))
    plot_confusion_matrix(cm, actual_names,
                          os.path.join(args.output_dir, 'confusion_matrix.png'))

    metrics = {
        'version': 'v2',
        'timestamp': datetime.now().isoformat(),
        'epochs_trained': epoch + 1,
        'max_epochs': args.epochs,
        'best_val_accuracy': round(best_val_acc / 100, 4),
        'standard_accuracy': round(val_acc / 100, 4),
        'tta_accuracy': round(final_acc / 100, 4),
        'final_accuracy': round(final_acc / 100, 4),
        'training_time_minutes': round(elapsed / 60, 2),
        'device': str(DEVICE),
        'class_names': actual_names,
        'improvements': [
            'class_weighted_loss',
            'full_finetuning',
            'differential_lr',
            'cosine_annealing',
            'label_smoothing_0.1',
            'batchnorm_classifier',
            'oversampling',
            'stronger_augmentation',
            'gradient_clipping',
            'tta_evaluation',
        ],
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
    print(f"\nRestart the backend to load the improved model!")


if __name__ == '__main__':
    main()
