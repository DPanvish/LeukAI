# Backend Documentation (LeukAI)

This document provides a detailed breakdown of the backend application's structure and the purpose of each file.

## Directory Structure

```
backend/
├───app/
│   ├───api/
│   │   ├───auth.py
│   │   ├───patients.py
│   │   └───predict.py
│   ├───core/
│   │   ├───config.py
│   │   ├───database.py
│   │   └───security.py
│   ├───models/
│   │   └───schemas.py
│   ├───services/
│   │   └───ml_service.py
│   ├───utils/
│   │   └───image_processing.py
│   ├───main.py
│   └───__init__.py
├───ml_models/
├───.env
├───Dockerfile
├───README.md
└───requirements.txt
```

---

## `app/` - The Core Application

This directory contains the main FastAPI application logic, organized into modules.

### `app/main.py`

This is the main entry point of the FastAPI application.

-   **Responsibilities:**
    -   Initializes the FastAPI app instance.
    -   Manages the application's startup and shutdown events using a `lifespan` manager.
        -   **On Startup:** Connects to MongoDB and loads the machine learning model into memory.
        -   **On Shutdown:** Closes the MongoDB connection.
    -   Configures CORS (Cross-Origin Resource Sharing) middleware to allow requests from the frontend.
    -   Includes the API routers from the `app/api/` directory.
    -   Defines the root (`/`) and health check (`/health`) endpoints.

### `app/api/` - API Endpoints

This module contains the different API routers, separating the endpoints by their functionality.

-   **`api/auth.py`**:
    -   **Endpoint:** `POST /api/auth/login`
    -   **Functionality:** Handles user authentication. It takes a username and password, verifies them against the database, and returns a JWT access token if the credentials are valid.

-   **`api/patients.py`**:
    -   **Endpoints:**
        -   `GET /api/patients/history`: Fetches a paginated and searchable list of all past predictions.
        -   `GET /api/patients/stats`: Retrieves aggregate statistics for the dashboard (e.g., total scans, benign/malignant counts).
        -   `GET /api/patients/{record_id}`: Fetches a single prediction record by its unique ID.
    -   **Protection:** All endpoints in this router require a valid JWT token for access.

-   **`api/predict.py`**:
    -   **Endpoint:** `POST /api/predict/upload`
    -   **Functionality:** This is the core prediction endpoint. It accepts a multipart/form-data request containing an image and patient details.
        1.  Validates the uploaded image file.
        2.  Calls the `ml_service` to perform inference and generate a Grad-CAM heatmap.
        3.  Saves the complete record (image, patient data, prediction, heatmap) to the MongoDB database.
        4.  Returns the prediction results and heatmap to the client.

### `app/core/` - Core Logic & Configuration

This module contains the central application logic that is shared across different parts of the backend.

-   **`core/config.py`**:
    -   **Functionality:** Defines the application's configuration using Pydantic's `BaseSettings`. It loads settings from environment variables (defined in the `.env` file), providing a single source of truth for configuration values like the app name, secret key, allowed file types, etc.

-   **`core/database.py`**:
    -   **Functionality:** Manages the connection to the MongoDB database.
    -   `connect_to_mongo()`: Establishes the connection using the `motor` async driver.
    -   `close_mongo_connection()`: Closes the database connection gracefully.
    -   `get_database()`: A utility function to get the database instance.
    -   It also contains logic to create a default `admin` user on the first run if no users exist in the database.

-   **`core/security.py`**:
    -   **Functionality:** Handles all security-related operations.
    -   `verify_password()`: Compares a plain-text password with a hashed one using `bcrypt`.
    -   `get_password_hash()`: Hashes a plain-text password.
    -   `create_access_token()`: Creates a JWT token.
    -   `get_current_user()`: A FastAPI dependency that decodes a JWT token from the request headers and verifies the user's identity.

### `app/models/` - Pydantic Schemas

-   **`models/schemas.py`**:
    -   **Functionality:** Defines the Pydantic models (schemas) that are used for data validation, serialization, and documentation.
    -   **Examples:** `LoginRequest` (for the login endpoint), `TokenResponse` (for the login response), and other models for patient data and prediction results.

### `app/services/` - Business Logic

-   **`services/ml_service.py`**:
    -   **Functionality:** This is the heart of the machine learning inference logic.
    -   `load_model()`: Loads the trained PyTorch model from disk. It cleverly handles different model versions (v1, v2, v3) and falls back to a "demo mode" if no trained model is found.
    -   `_generate_gradcam()`: Generates the Grad-CAM heatmap for model interpretability.
    -   `run_inference()`: The main public function that takes an image, runs prediction and Grad-CAM generation, and returns all the results.

### `app/utils/` - Utility Functions

-   **`utils/image_processing.py`**:
    -   **Functionality:** Provides helper functions for image manipulation.
    -   `validate_image()`: Checks file extension and size.
    -   `bytes_to_pil()`, `pil_to_base64()`, `numpy_to_base64()`: Functions for converting between different image formats (bytes, PIL Image, base64).

---

## Root Directory Files

-   **`ml_models/`**: This directory is the designated location for storing the trained model files (e.g., `alexnet_leukemia.pt`) and any resulting artifacts like `metrics.json`.
-   **`.env`**: This file (which is not committed to version control) stores sensitive configuration and environment variables.
-   **`Dockerfile`**: The instructions for building the backend Docker image. It handles installing dependencies and setting up the runtime environment.
-   **`README.md`**: The main documentation file for the backend, providing an overview and setup instructions.
-   **`requirements.txt`**: The list of all Python packages that the backend depends on.
