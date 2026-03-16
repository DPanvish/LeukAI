# Deep Learning Models & Scripts Documentation (LeukAI)

This document provides a detailed overview of the machine learning scripts and the overall workflow for training, evaluating, and using the deep learning models in the LeukAI platform.

## Overview

The core of the LeukAI platform is a deep learning model that classifies blood cell images into four categories of leukemia. The scripts in the root directory provide all the necessary tools to train a new model from scratch, evaluate its performance, and test its functionality.

## Training Scripts

There are three versions of the training script, each representing an evolution in the training methodology. All scripts use a modified **AlexNet** architecture with a custom classifier, leveraging transfer learning from a model pretrained on ImageNet.

### `train_model.py` (v1)

This is the baseline training script.

-   **Architecture:** AlexNet.
-   **Methodology:**
    -   **Transfer Learning:** Uses a pretrained AlexNet model.
    -   **Frozen Layers:** Freezes the early convolutional layers (`features`) and only trains the custom classifier. This is a fast but less flexible approach.
    -   **Data Augmentation:** Applies basic augmentations like flips and rotations.
    -   **Optimizer:** Adam.
    -   **Scheduler:** `StepLR` (reduces the learning rate at fixed intervals).
-   **When to use:** Good for a quick baseline or if you have a very small dataset and want to avoid overfitting the feature layers.

### `train_model_v2.py` (v2)

This script introduces several advanced techniques for improved performance and robustness. It is the **recommended script for most use cases**.

-   **Key Improvements:**
    -   **Full Fine-Tuning:** Unfreezes all layers and uses a **differential learning rate**. The pretrained feature layers are trained with a small learning rate, while the new classifier layers are trained with a larger one.
    -   **Class Imbalance Handling:**
        -   **Weighted Loss:** Uses a class-weighted `CrossEntropyLoss` to give more importance to minority classes during training.
        -   **Balanced Sampler:** Uses a `WeightedRandomSampler` to oversample images from minority classes in each batch.
    -   **Stronger Augmentation:** Employs a wider range of augmentations, including `RandomErasing` and `ColorJitter`, to create a more robust model.
    -   **Advanced Scheduling:** Uses a `CosineAnnealingLR` scheduler for a smoother learning rate decay.
    -   **Regularization:**
        -   **Label Smoothing:** Helps to prevent the model from becoming overconfident.
        -   **Gradient Clipping:** Stabilizes training by preventing exploding gradients.
        -   **BatchNorm:** Adds `BatchNorm1d` layers to the classifier for more stable training.
    -   **Early Stopping:** Monitors validation accuracy and stops training if it doesn't improve for a set number of epochs (`patience`).
    -   **Test-Time Augmentation (TTA):** For the final evaluation, it averages predictions over multiple augmented versions of each test image, providing a more reliable accuracy metric.

### `train_model_v3.py` (v3)

This script builds on v2 by training on a combined dataset of original and segmented images.

-   **Key Feature:**
    -   **Combined Dataset:** Takes two dataset paths (`--original_dir` and `--segmented_dir`) and trains on a `ConcatDataset` of both. The goal is to make the model learn features that are independent of the image background, improving its ability to generalize.
-   **Evaluation:** After training, it evaluates the model's performance on the original test set, the segmented test set, and the combined test set, providing a more detailed performance breakdown.
-   **When to use:** Use this if you have segmented versions of your images and want to train the most robust model possible.

## Evaluation & Testing Scripts

These scripts are used to check the status of the trained model and test its functionality.

### `check_model.py`

-   **Purpose:** Provides a quick status report of the currently installed model in `backend/ml_models/`.
-   **Functionality:**
    -   Checks if the model file exists.
    -   Prints the model's file size.
    -   If `metrics.json` is present, it prints key performance metrics like accuracy and F1-score.
    -   If no model is found, it prints instructions on how to train one, informing the user that the backend is in "demo mode".

### `test_api.py`

-   **Purpose:** An integration test for the backend's prediction API.
-   **Functionality:**
    -   Logs in to the API to get an auth token.
    -   Selects a few images from each class in the test dataset.
    -   Sends each image to the `/api/predict/upload` endpoint.
    -   Compares the predicted class with the true class and calculates the overall accuracy of the live API.

### `test_gradcam.py` & `test_gradcam_debug.py`

-   **Purpose:** To test and debug the Grad-CAM functionality.
-   **Functionality:**
    -   Sends a test image to the prediction endpoint.
    -   Receives the Grad-CAM heatmap (as a base64 string).
    -   Decodes the heatmap and saves it as `test_heatmap.png`.
    -   Analyzes the pixel values of the heatmap to ensure it has sufficient variation, confirming that the Grad-CAM algorithm is working correctly and not just returning a flat or empty image.

## ML Workflow

1.  **Data Preparation:**
    -   Obtain a dataset of blood cell images.
    -   Structure it into `train` and `test` directories, with subdirectories for each class (e.g., `Benign`, `Pro-B`).

2.  **Training:**
    -   Choose a training script (v2 is recommended).
    -   Run the script, providing the path to your dataset.
    -   The script will train the model, save the best-performing version (`alexnet_leukemia.pt`) to `backend/ml_models/`, and generate performance artifacts (`metrics.json`, `training_curves.png`, `confusion_matrix.png`).

3.  **Deployment:**
    -   When the backend server starts, the `ml_service` will automatically load the `alexnet_leukemia.pt` file.
    -   If no model is found, it will run in a fully functional demo mode.

4.  **Evaluation:**
    -   Run `check_model.py` to get a quick report on the loaded model.
    -   Run `test_api.py` to perform a live integration test against the running API.
    -   Run `test_gradcam.py` to verify the model interpretability feature.
