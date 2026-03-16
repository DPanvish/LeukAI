# Deep Learning Concepts & Model Architecture (LeukAI)

This document provides a deeper dive into the deep learning algorithms, concepts, and model architecture used in the LeukAI platform.

## 1. Core Model: AlexNet

The deep learning model at the heart of this project is **AlexNet**, one of the most influential convolutional neural network (CNN) architectures. While newer architectures exist, AlexNet provides a great balance of performance and computational efficiency for this task.

### Key Architectural Features:

-   **Convolutional Layers (Conv):** These are the primary building blocks. They apply a set of learnable filters to the input image to create feature maps. These filters are designed to detect low-level features like edges and textures in the early layers, and more complex patterns in the deeper layers.
-   **ReLU Activation Function:** After each convolutional layer, a Rectified Linear Unit (ReLU) activation function is applied. It replaces all negative pixel values in the feature map with zero, which helps the network learn non-linear relationships.
-   **Max-Pooling Layers:** These layers are used to down-sample the feature maps, reducing their spatial dimensions. This helps to make the learned features more robust to small translations and distortions in the input image.
-   **Fully-Connected (Linear) Layers:** After several convolutional and max-pooling layers, the high-level features are flattened and fed into a sequence of fully-connected layers. These layers perform the final classification based on the learned features.

### Our Modified AlexNet

We don't use the standard AlexNet directly. Instead, we modify it for our specific task:

1.  **Pretrained Model:** We start with an AlexNet model that has been pretrained on the **ImageNet** dataset, a massive dataset with over 14 million images across 1000 classes. This is the foundation of our transfer learning approach.
2.  **Custom Classifier:** We remove the final fully-connected layer (the "classifier") which was originally designed for 1000 ImageNet classes. We replace it with our own custom classifier, which is a new sequence of `Linear`, `ReLU`, `Dropout`, and `BatchNorm1d` layers, ending in a final `Linear` layer with 4 outputs, corresponding to our 4 leukemia classes.

---

## 2. Transfer Learning

**Transfer Learning** is a technique where a model developed for a task is reused as the starting point for a model on a second task.

-   **Why use it?** Training a deep neural network from scratch requires a very large amount of data. By using a model pretrained on ImageNet, we are leveraging the knowledge (i.e., the learned feature-detecting filters) that the model has already gained from a massive dataset. This allows us to achieve high accuracy with a much smaller dataset of blood cell images.

There are two main strategies for transfer learning, both of which are explored in our training scripts:

-   **Strategy A: Freeze the Feature Extractor (v1 script)**
    In this approach, we "freeze" the weights of all the convolutional layers. This means that their weights will not be updated during training. We only train the weights of our newly added custom classifier. This is a fast and safe approach when you have a very small dataset.

-   **Strategy B: Full Fine-Tuning (v2/v3 scripts)**
    In this more advanced approach, we allow all layers of the model to be trained, but we use a **differential learning rate**. The early convolutional layers (the "feature extractor") are trained with a very small learning rate, as they are already very good at detecting general features. The new classifier layers are trained with a larger learning rate, as they need to learn from scratch. This allows the entire network to adapt to the new dataset, often resulting in better performance.

---

## 3. Techniques for Robust Training

The `v2` and `v3` training scripts employ several modern techniques to improve the model's performance and robustness.

### Data Augmentation

Data augmentation artificially expands the training dataset by creating modified versions of the images. This helps the model to generalize better and not be overly sensitive to the specific orientation or lighting of the training images. We use:

-   **Geometric Augmentations:** `RandomHorizontalFlip`, `RandomVerticalFlip`, `RandomRotation`, `RandomCrop`, `RandomAffine` (translation and shear).
-   **Color Augmentations:** `ColorJitter` (adjusting brightness, contrast, and saturation).
-   **Other Augmentations:** `RandomGrayscale`, `GaussianBlur`, `RandomErasing` (which cuts out a random patch of the image, forcing the model to learn more holistic features).

### Handling Class Imbalance

In medical datasets, it's common for "normal" (benign) cases to be much more frequent than "diseased" (malignant) cases. This is a problem known as **class imbalance**. If not handled, the model can become biased towards predicting the majority class. We use two techniques to combat this:

-   **Class-Weighted Loss:** We assign a higher weight to the minority classes in the loss function. This means that the model is penalized more for making mistakes on the rare classes, forcing it to pay more attention to them.
-   **Balanced Sampler (`WeightedRandomSampler`):** This sampler ensures that each batch of training data contains a more balanced representation of all classes by oversampling images from the minority classes.

### Regularization

Regularization techniques are used to prevent **overfitting**, a scenario where the model performs very well on the training data but fails to generalize to new, unseen data.

-   **Dropout:** During training, `Dropout` layers randomly set a fraction of the neuron activations to zero. This forces the network to learn more robust features that are not dependent on any single neuron.
-   **Batch Normalization (`BatchNorm1d`):** This technique normalizes the inputs to a layer for each mini-batch. It helps to stabilize the training process, allows for higher learning rates, and acts as a regularizer.
-   **Label Smoothing:** This technique slightly alters the "hard" target labels (e.g., changing `[0, 1, 0, 0]` to something like `[0.025, 0.925, 0.025, 0.025]`). This discourages the model from becoming overly confident in its predictions and improves its ability to generalize.

### Learning Rate Scheduling

The learning rate is a hyperparameter that controls how much we are adjusting the weights of our network with respect to the loss gradient. A **learning rate scheduler** adjusts the learning rate during training.

-   **`StepLR` (v1):** Reduces the learning rate by a fixed factor every few epochs.
-   **`CosineAnnealingLR` (v2/v3):** Varies the learning rate following the curve of a cosine function. It starts high, gradually decreases to a minimum, and can be configured to "warm up" again. This often leads to better convergence than a simple step decay.

---

## 4. Model Interpretability: Grad-CAM

**Gradient-weighted Class Activation Mapping (Grad-CAM)** is a technique for making CNNs more interpretable. It produces a heatmap that highlights the regions of an input image that were most important for a particular prediction.

-   **How it works:** It uses the gradients of the target class score with respect to the feature maps of the final convolutional layer. These gradients are used to compute a weighted sum of the feature maps, resulting in a coarse heatmap of the "important" regions.
-   **Why it's important:** In a medical context, it's not enough for a model to be accurate; we also need to have some understanding of *why* it's making a particular decision. Grad-CAM provides a visual explanation, allowing a medical professional to see if the model is focusing on the relevant parts of the cell (e.g., the nucleus) or if it's being distracted by artifacts. This builds trust and can help to identify potential issues with the model.
