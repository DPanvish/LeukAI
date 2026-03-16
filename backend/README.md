# LeukAI Backend

This directory contains the FastAPI backend for the LeukAI platform.

## Structure

- **`app/`**: The main application module.
  - **`api/`**: Contains the API endpoint routers for different functionalities (authentication, prediction, patients).
  - **`core/`**: Core application logic, including database connection, configuration, and security functions (password hashing, JWT creation).
  - **`models/`**: Pydantic schemas for request and response validation.
  - **`services/`**: Business logic, primarily the machine learning service (`ml_service.py`) which handles model loading and inference.
  - **`utils/`**: Utility functions, such as image processing helpers.
- **`ml_models/`**: The default directory where trained models are stored and loaded from.
- **`.env`**: (Required, not committed) Stores environment variables, such as the `SECRET_KEY` for JWTs and the `MONGODB_URL`.
- **`Dockerfile`**: Defines the Docker image for building and running the backend service.
- **`requirements.txt`**: A list of Python dependencies for the backend.

## Key Dependencies

The main dependencies are listed in `requirements.txt`. Here are some of the key packages:

- **`fastapi`**: The main web framework.
- **`uvicorn`**: The ASGI server to run the application.
- **`motor`**: Asynchronous Python driver for MongoDB.
- **`torch` & `torchvision`**: The core machine learning framework.
- **`opencv-python-headless`**: For image processing.
- **`python-jose` & `bcrypt`**: For JWT-based authentication.
- **`pydantic`**: For data validation.

## Running Independently

While it's recommended to use the top-level `docker-compose.yml` to run the entire application, you can run the backend service on its own for development or testing.

1.  **Set up a Virtual Environment:**
    It's highly recommended to use a Python virtual environment.
    ```bash
    # Create the virtual environment
    python -m venv venv
    
    # Activate it
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Environment Variables:**
    Create a `.env` file in this directory with the required variables.
    ```
    SECRET_KEY=your_super_secret_key
    MONGODB_URL=mongodb://localhost:27017 
    ```
    You'll need a running MongoDB instance at the URL you provide.

4.  **Run the Development Server:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The `--reload` flag automatically restarts the server when you make changes to the code.

5.  **Access the API:**
    - **API URL:** `http://localhost:8000`
    - **Interactive Docs (Swagger UI):** `http://localhost:8000/docs`
