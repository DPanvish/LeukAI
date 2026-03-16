# Frontend Documentation (LeukAI)

This document provides a detailed breakdown of the frontend React application's structure and the purpose of each file.

## Directory Structure

```
frontend/
├───src/
│   ├───components/
│   │   ├───Layout.jsx
│   │   └───UIComponents.jsx
│   ├───context/
│   │   └───AuthContext.jsx
│   ├───pages/
│   │   ├───Dashboard.jsx
│   │   ├───DiagnosticViewer.jsx
│   │   ├───History.jsx
│   │   ├───Login.jsx
│   │   └───Upload.jsx
│   ├───services/
│   │   └───api.js
│   ├───utils/
│   │   └───helpers.js
│   ├───App.jsx
│   ├───index.css
│   └───main.jsx
├───.gitignore
├───Dockerfile
├───index.html
├───package.json
└───README.md
```

---

## `src/` - The Application Source Code

This directory contains the main source code for the React application.

### `src/main.jsx`

This is the main entry point for the React application.

-   **Responsibilities:**
    -   Renders the root `App` component into the DOM.
    -   Wraps the application in a `BrowserRouter` to enable client-side routing.
    -   Wraps the application in the `AuthProvider` to provide authentication context to all components.

### `src/App.jsx`

This is the root component of the application.

-   **Responsibilities:**
    -   Sets up the main routing structure using `react-router-dom`.
    -   Defines the public (`/login`) and protected routes.
    -   Uses a `ProtectedRoute` component to ensure that only authenticated users can access the main application.
    -   Wraps the protected routes in the `Layout` component, providing a consistent UI shell.
    -   Uses `framer-motion`'s `AnimatePresence` to add animations to page transitions.

### `src/components/` - Reusable UI Components

This directory contains reusable components that are used across multiple pages.

-   **`components/Layout.jsx`**:
    -   **Functionality:** This is the main UI shell for the authenticated part of the application.
    -   It includes the responsive sidebar for navigation, a header for mobile view, and the main content area where the different pages are rendered (via `<Outlet />`).
    -   It also contains the user card with the logout button.

-   **`components/UIComponents.jsx`**:
    -   **Functionality:** This file likely contains smaller, generic UI components that are used throughout the application, such as custom buttons, cards, loaders, or modal dialogs. This helps to maintain a consistent look and feel.

### `src/context/` - Global State Management

-   **`context/AuthContext.jsx`**:
    -   **Functionality:** This React Context provider is responsible for managing the global authentication state.
    -   It provides the `user` object, the `isAuthenticated` flag, and functions like `login` and `logout` to all components that are descendants of it.
    -   It typically interacts with `localStorage` or `sessionStorage` to persist the authentication token between sessions.

### `src/pages/` - Application Pages

This directory contains the top-level components for each page (or route) in the application.

-   **`pages/Login.jsx`**: The login page with a form for users to enter their credentials.
-   **`pages/Dashboard.jsx`**: The main landing page after login. It displays key statistics and recent activity, fetched from the `/api/patients/stats` endpoint.
-   **`pages/Upload.jsx`**: Contains the file upload component (`react-dropzone`) for submitting new blood cell images for analysis. It sends the data to the `/api/predict/upload` endpoint.
-   **`pages/History.jsx`**: Displays a searchable and paginated table or list of all past predictions, fetched from the `/api/patients/history` endpoint.
-   **`pages/DiagnosticViewer.jsx`**: A detailed view for a single prediction. It's accessed via a route like `/diagnostic/:id`. It fetches the data for a specific record from `/api/patients/{record_id}` and displays the image, heatmap, and all associated details.

### `src/services/` - API Communication

-   **`services/api.js`**:
    -   **Functionality:** This file centralizes the API communication logic.
    -   It exports a pre-configured `axios` instance.
    -   This instance has its `baseURL` set to the backend's address (`http://localhost:8000`).
    -   It often includes an interceptor to automatically add the JWT `Authorization` header to all outgoing requests, simplifying API calls from the components.

### `src/utils/` - Helper Functions

-   **`utils/helpers.js`**:
    -   **Functionality:** Contains miscellaneous helper functions that can be used anywhere in the application. This might include functions for formatting dates, calculating values, or other small, reusable pieces of logic.

---

## Root Directory Files

-   **`.gitignore`**: Specifies which files and directories should be ignored by Git (e.g., `node_modules`, `dist`, `.env`).
-   **`Dockerfile`**: The instructions for building a production-ready Docker image for the frontend. It typically involves a multi-stage build: one stage to install dependencies and build the static assets, and a final, lightweight stage (e.g., using `nginx`) to serve those assets.
-   **`index.html`**: The HTML shell for the single-page application.
-   **`package.json`**: Lists the project's dependencies, dev dependencies, and scripts (`dev`, `build`, `preview`).
-   **`README.md`**: The main documentation file for the frontend, providing an overview and setup instructions.
-   **`vite.config.js`**: The configuration file for Vite, the frontend build tool.
-   **`tailwind.config.js` & `postcss.config.js`**: Configuration files for the Tailwind CSS framework.