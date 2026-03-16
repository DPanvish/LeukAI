# LeukAI Frontend

This directory contains the React frontend for the LeukAI platform, built using Vite.

## Structure

- **`src/`**: The main source code directory.
  - **`components/`**: Reusable React components used across the application, such as the main `Layout.jsx` and other UI elements.
  - **`context/`**: React Context providers. Currently includes `AuthContext.jsx` for managing user authentication state globally.
  - **`pages/`**: Top-level components that correspond to the application's pages/routes (e.g., `Dashboard.jsx`, `Login.jsx`, `Upload.jsx`).
  - **`services/`**: Modules for communicating with the backend API. `api.js` contains a pre-configured Axios instance for making requests.
  - **`utils/`**: Helper functions and utilities.
  - **`App.jsx`**: The root component that sets up the application's routing using `react-router-dom`.
  - **`main.jsx`**: The entry point of the React application.
- **`public/`**: Static assets that are copied directly to the build output.
- **`index.html`**: The main HTML template for the single-page application.
- **`package.json`**: Defines the project's dependencies and scripts.
- **`vite.config.js`**: Configuration file for the Vite build tool.
- **`tailwind.config.js`**: Configuration for the Tailwind CSS framework.
- **`Dockerfile`**: Defines the Docker image for building and serving the frontend.

## Key Dependencies

The main dependencies are listed in `package.json`. Here are some of the key packages:

- **`react` & `react-dom`**: The core library for building the user interface.
- **`vite`**: The build tool and development server.
- **`react-router-dom`**: For client-side routing.
- **`axios`**: For making HTTP requests to the backend API.
- **`tailwindcss`**: A utility-first CSS framework for styling.
- **`framer-motion`**: For animations.
- **`recharts`**: For creating charts and graphs.
- **`react-dropzone`**: For the file upload component.

## Running Independently

While it's recommended to use the top-level `docker-compose.yml`, you can run the frontend development server on its own.

1.  **Install Node.js and npm:**
    Make sure you have Node.js (v16 or higher) and npm installed. You can download them from [nodejs.org](https://nodejs.org/).

2.  **Install Dependencies:**
    Navigate to this directory in your terminal and run:
    ```bash
    npm install
    ```

3.  **Run the Development Server:**
    ```bash
    npm run dev
    ```
    This will start the Vite development server, usually on `http://localhost:5173`. The server supports Hot Module Replacement (HMR) for a fast development experience.

4.  **Connect to the Backend:**
    The frontend will try to connect to the backend API at the URL specified in `src/services/api.js` (by default, `http://localhost:8000`). Ensure the backend service is running and accessible at that address.

## Building for Production

To create a production-ready build of the frontend:

```bash
npm run build
```

This will generate a `dist` directory containing the optimized and bundled static assets. These files can then be served by any static file server (like Nginx, Vercel, or AWS S3).
