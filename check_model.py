import os, sys, json, torch, torch.nn as nn
from torchvision import models
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from app.core.config import settings

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_path = os.path.join('backend', settings.MODEL_PATH)
metrics_path = os.path.join('backend', 'ml_models', 'metrics.json')

print("LeukAI - Model Status Report")
print("-" * 40)
print("Device:", device)
print("Model path:", model_path)
print("Model exists:", os.path.exists(model_path))

if os.path.exists(model_path):
    size_mb = os.path.getsize(model_path) / (1024*1024)
    print("File size: %.1f MB" % size_mb)
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            m = json.load(f)
        print("Accuracy: %.2f%%" % (m['final_accuracy']*100))
        print("Macro F1: %.2f%%" % (m['macro_f1']*100))
        print("Weighted F1: %.2f%%" % (m['weighted_f1']*100))
    else:
        print("No metrics.json found")
else:
    print("")
    print("STATUS: DEMO MODE (no trained model)")
    print("")
    print("The model has NO real accuracy because")
    print("the classifier is randomly initialized.")
    print("Predictions are essentially random guesses.")
    print("")
    print("To get real accuracy, you need to train")
    print("the model on a leukemia PBS dataset.")
    print("")
    print("HOW TO TRAIN:")
    print("  1. Download a dataset (e.g. from Kaggle):")
    print("     kaggle.com/datasets/mohammadamireshraghi/blood-cell-cancer-all-4class")
    print("  2. Organize into train/test folders")
    print("  3. Run: python train_model.py --data_dir ./dataset --epochs 25")
    print("  4. Restart the backend server")
    print("")
    print("The trained model will auto-load and")
    print("provide real classification accuracy.")
