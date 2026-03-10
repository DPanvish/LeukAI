"""
LeukAI v3 - Combined Training (Original + Segmented)
=====================================================
Trains on both original PBS images and segmented images
for improved robustness. Uses all v2 improvements plus:
  - Combined dataset (original + segmented)
  - Separate augmentation strategies per image type
"""

import os
import argparse
import json
import time
import shutil
import numpy as np
from datetime import datetime
from collections import Counter

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler, ConcatDataset
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


# ── Data Transforms ──────────────────────────────────────────
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

# TTA transforms
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
    """AlexNet with BatchNorm classifier (same as v2)."""
    model = models.alexnet(weights=models.AlexNet_Weights.DEFAULT)
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
    for m in model.classifier.modules():
        if isinstance(m, nn.Linear):
            nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.BatchNorm1d):
            nn.init.constant_(m.weight, 1)
            nn.init.constant_(m.bias, 0)
    return model.to(DEVICE)


def get_combined_sampler(concat_dataset):
    """Balanced sampler for a ConcatDataset (fast, no image loading)."""
    all_labels = []
    for sub_ds in concat_dataset.datasets:
        all_labels.extend([s[1] for s in sub_ds.samples])
    print(f"  Scanned {len(all_labels)} labels")

    counter = Counter(all_labels)
    class_weights = {cls: len(all_labels) / count for cls, count in counter.items()}
    sample_weights = [class_weights[label] for label in all_labels]
    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(all_labels),
        replacement=True,
    )
    return sampler, all_labels


def get_class_weights_from_labels(labels, num_classes):
    """Compute inverse-frequency class weights."""
    counter = Counter(labels)
    total = len(labels)
    weights = []
    for i in range(num_classes):
        w = total / (num_classes * counter.get(i, 1))
        weights.append(w)
    return torch.FloatTensor(weights).to(DEVICE)


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
    """Test-Time Augmentation evaluation."""
    model.eval()
    all_preds = []
    all_labels = []
    from PIL import Image

    for idx in range(len(dataset)):
        img_path, label = dataset.samples[idx]
        img = Image.open(img_path).convert('RGB')

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

        if (idx + 1) % 300 == 0:
            print(f"  TTA progress: {idx+1}/{len(dataset)}")

    accuracy = 100.0 * accuracy_score(all_labels, all_preds)
    return accuracy, np.array(all_preds), np.array(all_labels)


def plot_training_curves(history, save_path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.plot(history['train_loss'], label='Train Loss', color='#3381ff', linewidth=2)
    ax1.plot(history['val_loss'], label='Val Loss', color='#d946ef', linewidth=2)
    ax1.set_title('Loss Curves (v3 Combined)', fontweight='bold')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(history['train_acc'], label='Train Acc', color='#3381ff', linewidth=2)
    ax2.plot(history['val_acc'], label='Val Acc', color='#d946ef', linewidth=2)
    ax2.set_title('Accuracy Curves (v3 Combined)', fontweight='bold')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_confusion_matrix(cm, class_names, save_path):
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
    ax.set_title('Confusion Matrix (v3 Combined)', fontweight='bold', fontsize=14)
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


def main():
    parser = argparse.ArgumentParser(description='Train AlexNet v3 (Combined)')
    parser.add_argument('--original_dir', type=str, required=True,
                        help='Path to original dataset with train/test folders')
    parser.add_argument('--segmented_dir', type=str, required=True,
                        help='Path to segmented dataset with train folder')
    parser.add_argument('--epochs', type=int, default=40)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=0.0005)
    parser.add_argument('--output_dir', type=str, default='./backend/ml_models')
    parser.add_argument('--patience', type=int, default=12)
    args = parser.parse_args()

    print("=" * 60)
    print("  LeukAI v3 - Combined Training Pipeline")
    print("  (Original + Segmented Images)")
    print("=" * 60)
    print(f"  Device:       {DEVICE}")
    print(f"  Original:     {args.original_dir}")
    print(f"  Segmented:    {args.segmented_dir}")
    print(f"  Epochs:       {args.epochs}")
    print(f"  Batch Size:   {args.batch_size}")
    print(f"  LR:           {args.lr}")
    print(f"  Patience:     {args.patience}")
    print("=" * 60)

    # ── Load Datasets ────────────────────────────────────
    orig_train_dir = os.path.join(args.original_dir, 'train')
    orig_test_dir = os.path.join(args.original_dir, 'test')
    seg_train_dir = os.path.join(args.segmented_dir, 'train')
    seg_test_dir = os.path.join(args.segmented_dir, 'test')

    orig_train = datasets.ImageFolder(orig_train_dir, transform=train_transform)
    seg_train = datasets.ImageFolder(seg_train_dir, transform=train_transform)
    orig_test = datasets.ImageFolder(orig_test_dir, transform=test_transform)
    seg_test = datasets.ImageFolder(seg_test_dir, transform=test_transform)
    combined_test = ConcatDataset([orig_test, seg_test])

    # Verify class order matches
    print(f"\n[DATA] Original classes: {orig_train.classes}")
    print(f"[DATA] Segmented classes: {seg_train.classes}")
    print(f"[DATA] Orig test classes: {orig_test.classes}")
    print(f"[DATA] Seg test classes:  {seg_test.classes}")

    assert orig_train.classes == seg_train.classes, \
        "Class names don't match between original and segmented!"
    assert orig_train.classes == orig_test.classes, \
        "Class names don't match between train and test!"

    # Combine train datasets
    combined_train = ConcatDataset([orig_train, seg_train])

    print(f"\n[DATA] Original train:  {len(orig_train)} images")
    print(f"[DATA] Segmented train: {len(seg_train)} images")
    print(f"[DATA] Combined train:  {len(combined_train)} images")
    print(f"[DATA] Original test:   {len(orig_test)} images")
    print(f"[DATA] Segmented test:  {len(seg_test)} images")
    print(f"[DATA] Combined test:   {len(combined_test)} images")

    # Per-class counts
    print("\n[DATA] Per-class breakdown:")
    orig_labels = [s[1] for s in orig_train.samples]
    seg_labels = [s[1] for s in seg_train.samples]
    for i, cls in enumerate(orig_train.classes):
        oc = orig_labels.count(i)
        sc = seg_labels.count(i)
        print(f"  {cls:<15} Original: {oc:>4}  Segmented: {sc:>4}  Total: {oc+sc:>5}")

    # ── Balanced Sampler ─────────────────────────────────
    print("\n[INFO] Building balanced sampler (scanning labels)...")
    sampler, all_labels = get_combined_sampler(combined_train)
    class_weights = get_class_weights_from_labels(all_labels, len(orig_train.classes))
    print(f"[BALANCE] Class weights: {class_weights.cpu().numpy()}")

    train_loader = DataLoader(combined_train, batch_size=args.batch_size,
                              sampler=sampler, num_workers=0)
    test_loader = DataLoader(combined_test, batch_size=args.batch_size,
                             shuffle=False, num_workers=0)
    orig_test_loader = DataLoader(orig_test, batch_size=args.batch_size,
                                  shuffle=False, num_workers=0)
    seg_test_loader = DataLoader(seg_test, batch_size=args.batch_size,
                                 shuffle=False, num_workers=0)

    # ── Build Model ──────────────────────────────────────
    model = build_model(num_classes=len(orig_train.classes))
    print(f"\n[MODEL] AlexNet with BatchNorm classifier")
    total_params = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[MODEL] Total params:     {total_params:,}")
    print(f"[MODEL] Trainable params: {trainable:,}")

    # ── Optimizer (differential LR) ──────────────────────
    param_groups = [
        {'params': model.features.parameters(), 'lr': args.lr * 0.1},
        {'params': model.classifier.parameters(), 'lr': args.lr},
    ]
    optimizer = optim.AdamW(param_groups, weight_decay=1e-3)

    criterion = nn.CrossEntropyLoss(
        weight=class_weights,
        label_smoothing=0.1,
    )

    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.epochs, eta_min=1e-6)

    # ── Training Loop ────────────────────────────────────
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    best_val_acc = 0.0
    patience_counter = 0
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Starting Combined Training...")
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
    class_names = orig_train.classes

    # Evaluate on combined test set
    val_loss, val_acc, preds, labels = evaluate(model, test_loader)
    print(f"\n{'='*60}")
    print(f"  COMBINED TEST SET EVALUATION")
    print(f"{'='*60}")
    print(f"\n  Overall Accuracy: {val_acc:.2f}%")
    print(classification_report(labels, preds, target_names=class_names, digits=4))

    # Original test only
    _, orig_acc, orig_preds, orig_labels = evaluate(model, orig_test_loader)
    print(f"\n{'='*60}")
    print(f"  ORIGINAL IMAGES TEST: {orig_acc:.2f}%")
    print(f"{'='*60}")
    print(classification_report(orig_labels, orig_preds, target_names=class_names, digits=4))

    # Segmented test only
    _, seg_acc, seg_preds, seg_labels = evaluate(model, seg_test_loader)
    print(f"\n{'='*60}")
    print(f"  SEGMENTED IMAGES TEST: {seg_acc:.2f}%")
    print(f"{'='*60}")
    print(classification_report(seg_labels, seg_preds, target_names=class_names, digits=4))

    # Use combined results as final
    final_preds = preds
    final_labels = labels
    final_acc = val_acc

    precision, recall, f1, support = precision_recall_fscore_support(
        final_labels, final_preds, average=None)

    print(f"\n  Per-Class Metrics (Combined):")
    print(f"  {'Class':<20} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}")
    print(f"  {'-'*55}")
    for i, name in enumerate(class_names):
        print(f"  {name:<20} {precision[i]*100:>9.2f}% {recall[i]*100:>9.2f}% "
              f"{f1[i]*100:>9.2f}%")

    mac_p, mac_r, mac_f1, _ = precision_recall_fscore_support(
        final_labels, final_preds, average='macro')
    wt_p, wt_r, wt_f1, _ = precision_recall_fscore_support(
        final_labels, final_preds, average='weighted')
    print(f"\n  {'Macro Avg':<20} {mac_p*100:>9.2f}% {mac_r*100:>9.2f}% {mac_f1*100:>9.2f}%")
    print(f"  {'Weighted Avg':<20} {wt_p*100:>9.2f}% {wt_r*100:>9.2f}% {wt_f1*100:>9.2f}%")

    cm = confusion_matrix(final_labels, final_preds)

    # ── Save Artifacts ───────────────────────────────────
    plot_training_curves(history,
                         os.path.join(args.output_dir, 'training_curves.png'))
    plot_confusion_matrix(cm, class_names,
                          os.path.join(args.output_dir, 'confusion_matrix.png'))

    metrics = {
        'version': 'v3_combined',
        'timestamp': datetime.now().isoformat(),
        'epochs_trained': epoch + 1,
        'max_epochs': args.epochs,
        'best_val_accuracy': round(best_val_acc / 100, 4),
        'standard_accuracy': round(val_acc / 100, 4),
        'tta_accuracy': round(final_acc / 100, 4),
        'final_accuracy': round(final_acc / 100, 4),
        'training_time_minutes': round(elapsed / 60, 2),
        'device': str(DEVICE),
        'class_names': class_names,
        'dataset': {
            'original_train': len(orig_train),
            'segmented_train': len(seg_train),
            'combined_train': len(combined_train),
            'original_test': len(orig_test),
            'segmented_test': len(seg_test),
            'combined_test': len(combined_test),
        },
        'original_test_accuracy': round(orig_acc / 100, 4),
        'segmented_test_accuracy': round(seg_acc / 100, 4),
        'per_class_precision': {n: round(float(p), 4) for n, p in zip(class_names, precision)},
        'per_class_recall': {n: round(float(r), 4) for n, r in zip(class_names, recall)},
        'per_class_f1': {n: round(float(f), 4) for n, f in zip(class_names, f1)},
        'macro_f1': round(float(mac_f1), 4),
        'weighted_f1': round(float(wt_f1), 4),
        'confusion_matrix': cm.tolist(),
    }
    with open(os.path.join(args.output_dir, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"\n[OK] All artifacts saved to {args.output_dir}")
    print(f"[OK] Restart the backend to load the improved model!")


if __name__ == '__main__':
    main()
