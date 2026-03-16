# LeukAI: AI-Powered Leukemia Detection Platform

LeukAI is a full-stack web application that uses a deep learning model to detect leukemia from blood cell images. It provides a modern, user-friendly interface for medical professionals to upload images, receive instant predictions, and manage patient diagnostic records.

![LeukAI Screenshot](https://i.imgur.com/YOUR_SCREENSHOT_URL.png)  <!-- Replace with a real screenshot -->

## Key Features

- **Secure User Authentication:** JWT-based login system for authorized access.
- **AI-Powered Predictions:** Upload blood cell images and receive a classification (Benign, Early Pre-B, Pre-B, or Pro-B ALL) with a confidence score.
- **Intelligent Visualization:** Grad-CAM heatmaps are generated to show which parts of the image the model focused on for its prediction, providing interpretability.
- **Patient & History Management:** Create patient profiles and view a searchable, paginated history of all diagnostic scans.
- **Data-Rich Dashboard:** Get a quick overview of system statistics, including total scans, benign/malignant counts, and a list of recent activity.
- **PDF Export:** (Future Feature) Export diagnostic reports, including images and predictions, to PDF.

## Technology Stack & Dependencies

The application is fully containerized with Docker, which is the recommended way to run it. However, you can also run the frontend and backend services locally for development.

### Core Technologies
| Component      | Technologies                                                                                             |
|----------------|----------------------------------------------------------------------------------------------------------|
| **Backend**    | FastAPI, Python, MongoDB (Motor), PyTorch, Torchvision, OpenCV, JWT (python-jose), Uvicorn                |
| **Frontend**   | React, Vite, React Router, Tailwind CSS, Framer Motion, Axios, Lucide Icons, Recharts                      |
| **Database**   | MongoDB                                                                                                  |
| **Deployment** | Docker, Docker Compose                                                                                   |

### Prerequisites for Local Development
- **Node.js** (v16 or higher) and **npm** for the frontend.
- **Python** (v3.9 or higher) and **pip** for the backend.
- A running **MongoDB** instance.

## Model Architecture

The core of LeukAI is a modified **AlexNet** convolutional neural network (CNN), pretrained on the ImageNet dataset and fine-tuned for leukemia classification.

- **Transfer Learning:** We use a pretrained AlexNet to leverage features learned from a massive dataset.
- **Custom Classifier:** The original 1000-class classifier is replaced with a custom one designed for our 4 leukemia classes.
- **Fine-Tuning:**
  - **v1:** Early convolutional layers are frozen, and only the classifier is trained.
  - **v2/v3:** All layers are fine-tuned using a *differential learning rate*—the pretrained feature layers learn slowly, while the new classifier layers learn faster.
- **Regularization:** The classifier includes `Dropout` and `BatchNorm1d` (in v2/v3) to prevent overfitting and improve stability.

## Training the Model

The repository includes several scripts for training and evaluating the model. Each version introduces significant improvements.

| Script              | Key Features & Improvements                                                                                                                                                                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `train_model.py`    | **v1:** Basic transfer learning pipeline with a frozen feature extractor and a simple learning rate schedule.                                                                                                                                                    |
| `train_model_v2.py` | **v2:** Introduces advanced techniques: <br> - **Class-weighted loss** & **oversampling** to handle data imbalance. <br> - **Full fine-tuning** with differential learning rates. <br> - **Stronger data augmentation** (RandomErasing, etc.). <br> - **Cosine Annealing** LR schedule & **Label Smoothing**. <br> - **Early Stopping** to prevent overfitting. <br> - **Test-Time Augmentation (TTA)** for more robust evaluation. |
| `train_model_v3.py` | **v3:** Builds on v2 by training on a **combined dataset** of original and segmented cell images. This aims to make the model more robust to background variations. Evaluates performance on both image types separately.                                              |

### Training Your Own Model
1.  **Get the Dataset:** The dataset is not included in this repository. You can download a suitable dataset, such as the one from [Kaggle](https://www.kaggle.com/datasets/mohammadamireshraghi/blood-cell-cancer-all-4class), and organize it into `train` and `test` directories as expected by the scripts.
2.  **Run the Training Script:**
    ```bash
    # It is recommended to use a Python virtual environment
    pip install -r backend/requirements.txt
    
    # Run the training script of your choice
    python train_model_v2.py --data_dir ./path/to/your/dataset --epochs 40 --patience 10
    ```
    This will save the trained model (`alexnet_leukemia.pt`) and other artifacts in the `backend/ml_models` directory.

## Getting Started

### Option 1: Running with Docker (Recommended)

This is the easiest way to get the entire application running.

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Leukemia
    ```
2.  **Create Backend Environment File:**
    The backend needs a `.env` file for secrets. Create a file at `backend/.env`.
    ```bash
    # For Linux/macOS
    echo "SECRET_KEY=$(openssl rand -hex 32)" > backend/.env
    
    # For Windows (PowerShell)
    "SECRET_KEY=$(openssl rand -hex 32)" | Out-File -FilePath backend/.env -Encoding utf8
    ```
    You should also add the database URL (though it defaults to the Docker service name):
    ```
    MONGODB_URL=mongodb://mongodb:27017
    ```

3.  **Build and Run with Docker Compose:**
    ```bash
    docker-compose up -d --build
    ```

### Option 2: Running Services Locally

If you prefer to run the services without Docker, you can run them locally. You will need to have a MongoDB instance running.

**1. Run the Backend:**
For detailed instructions, see the `backend/README.md` file.
```bash
# Navigate to the backend directory
cd backend

# Install dependencies (preferably in a virtual environment)
pip install -r requirements.txt

# Create the .env file as described above

# Run the development server
uvicorn app.main:app --reload
```

**2. Run the Frontend:**
For detailed instructions, see the `frontend/README.md` file.
```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

### Accessing the Application
- **Frontend:** `http://localhost:5173`
- **Backend API:** `http://localhost:8000`
- **API Docs (Swagger UI):** `http://localhost:8000/docs`

A default user `admin` with password `admin123` is created if the database is empty (see `backend/app/core/database.py`).

## API Documentation

The backend provides a RESTful API for all platform operations. For detailed, interactive documentation, visit the Swagger UI at `http://localhost:8000/docs` after starting the application.

### Key Endpoints
- `POST /api/auth/login`: Authenticate and receive a JWT token.
- `POST /api/predict/upload`: Upload an image for prediction. Requires a valid token.
- `GET /api/patients/history`: Get a paginated list of all past predictions. Requires a valid token.
- `GET /api/patients/stats`: Get dashboard statistics. Requires a valid token.
- `GET /api/patients/{record_id}`: Get details for a single prediction. Requires a valid token.

## Project Structure

```
e:\Leukemia\
├───backend/            # FastAPI Application
│   └───README.md       # Backend-specific instructions
├───frontend/           # React Application
│   └───README.md       # Frontend-specific instructions
├───dataset(original)/  # (Not in repo)
├───dataset(segmented)/ # (Not in repo)
├───train_model_v2.py   # Example training script
└───docker-compose.yml  # Docker service orchestration
```

## Deployment

While this project is set up for easy local development, here is a general guide for a production deployment:

1.  **Database:** Use a managed MongoDB service (like MongoDB Atlas) instead of a Docker container for reliability and scalability. Update the `MONGODB_URL` in the backend's environment variables.
2.  **Backend:** Deploy the backend container to a cloud service like AWS Fargate, Google Cloud Run, or a virtual machine. Ensure you manage your `.env` file securely (e.g., using secret management tools).
3.  **Frontend:**
    *   **Build:** Build the static frontend assets: `npm run build` in the `frontend` directory.
    *   **Serve:** Serve the static files from the `frontend/dist` directory using a web server like Nginx or a static hosting service (AWS S3/CloudFront, Vercel, Netlify). You will need to configure the web server to proxy API requests to the backend service.
4.  **CORS:** Update `CORS_ORIGINS` in the backend environment to include your production frontend URL.

---