# parkapp - Smart Parking Management System

A production-grade, full-stack vehicle parking management application designed to demonstrate advanced Python, Flask, and system architecture concepts. This application handles user management, parking spot reservations, automated reporting, and payment integration.

## Default Credentials

**Admin Account:**
- Email: `admin@parkapp.com`
- Password: `admin123`

**Test User Account:**
- Email: `user@parkapp.com`
- Password: `user123`

## System Overview

The application is built using a modern, scalable architecture splitting responsibilities across different services and layers:

-   **Backend:** Python Flask
-   **Database:** SQLAlchemy (ORM) with SQLite (Dev) / PostgreSQL (Prod ready)
-   **Task Queue:** Celery + Redis
-   **Caching:** Redis
-   **Frontend:** Vue.js
-   **API:** RESTful API with Swagger Documentation (Flask-RESTX)
-   **Containerization:** Docker & Docker Compose

##  Key Features & Advanced Concepts

### 1. Advanced Architecture
-   **Modular Design:** Uses Flask Blueprints (in `controllers/`) to separate logic for Admin, User, Authorization, and Checks.
-   **Service Layer Pattern:** Business logic is decoupled from routes.
-   **Factory Pattern:** Application factory pattern (`create_app`) used for better testing and configuration management.

### 2. Security & Authentication
-   **Role-Based Access Control (RBAC):** Implemented using `Flask-Security-Too`. Supports distinct roles (Admin, User) with granular permissions.
-   **JWT Authentication:** Secure API access using `Flask-JWT-Extended`.
-   **Data Protection:** Password hashing and salting integration.

### 3. Asynchronous Task Processing
-   **Celery Workers:** specific heavy tasks are offloaded to background workers to ensure the UI remains responsive.
    -   *CSV Exports:* Users can request their booking history, which is generated asynchronously and emailed.
    -   *PDF Generation:* Monthly activity reports are generated using `ReportLab` and sent via background tasks.
-   **Scheduled Jobs:** (e.g., Monthly Activity Reports) using Celery Beat/APScheduler.

### 4. Performance & Caching
-   **Redis Caching:** Critical endpoints and data queries are cached using `Flask-Caching` and Redis to minimize database hits and latency.

### 5. API First Design
-   **Swagger/OpenAPI:** Integrated with `Flask-RESTX` to provide auto-generated, interactive API documentation.
-   **REST Standards:** Adheres to RESTful principles for resource management.

### 6. Code Quality & Tooling
-   **Dependency Management:** standard `requirements.txt` and `pyproject.toml`.
-   **Unit Testing:** Comprehensive test suite included.

##  Docker Support

The easiest way to run the entire stack (Backend + Frontend + Worker + Redis) is using Docker Compose.

1.  **Build and Run:**
    ```bash
    docker-compose up --build
    ```

2.  **Access:**
    -   Frontend: [http://localhost:8080](http://localhost:8080)
    -   Backend API: [http://localhost:5000](http://localhost:5000)

##  Getting Started (Manual)

### Prerequisites
-   Python 3.12+
-   Redis Server (running)
-   `uv` (recommended) or `pip`

### Installation

1.  **Clone the repository**
2.  **Install Dependencies using `uv`:**
    ```bash
    uv sync
    ```
    Or using standard pip:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Setup:**
    Create a `.env` file in the root directory:
    ```env
    SECRET_KEY=your_secret_key
    CELERY_BROKER_URL=redis://localhost:6379/1
    CELERY_RESULT_BACKEND=redis://localhost:6379/2
    CACHE_REDIS_URL=redis://localhost:6379/0
    MAIL_SERVER=smtp.example.com
    MAIL_PORT=587
    MAIL_USERNAME=your_email
    MAIL_PASSWORD=your_password
    ```
    
### Running the Application

1.  **Start Redis Server** (in a separate terminal)
2.  **Start Celery Worker:**
    ```bash
    celery -A celery_worker.celery worker --loglevel=info
    ```
3.  **Start Application Server:**
    
    You can run the application using **Uvicorn** (ASGI) managed by **Gunicorn** (Process Manager).
    
    *   **Development (Uvicorn directly with hot reload):**
        ```bash
        uv run python asgi.py
        # OR
        uv run uvicorn asgi:asgi_app --reload --port 5000
        ```
    
    *   **Production (Linux/Mac - Gunicorn + Uvicorn Workers):**
        ```bash
        uv run gunicorn -c gunicorn_config.py asgi:asgi_app
        ```

    *   **Production (Windows - Uvicorn):**
        ```bash
        uv run uvicorn asgi:asgi_app --port 5000 --workers 4
        ```

4.  **Frontend Setup:**
    Open a new terminal, navigate to `frontend/`, and start the Vue development server:
    ```bash
    cd frontend
    npm install
    npm run serve
    ```
    Access the application at `http://localhost:8080`.

##  Quickstart

To get the full stack up and running immediately:

1.  **Backend:**
    ```bash
    uv sync
    # Make sure Redis is running
    
    # Windows:
    uv run uvicorn asgi:asgi_app --port 5000
    
    # Linux/Mac:
    # uv run gunicorn -c gunicorn_config.py asgi:asgi_app
    ```

2.  **Worker:**
    ```bash
    uv run celery -A celery_worker.celery worker --loglevel=info
    ```

3.  **Frontend:**
    ```bash
    cd frontend
    npm install
    npm run serve
    ```

4.  **Browser:**
    *   **App URL:** [http://localhost:8080](http://localhost:8080)
    *   **API Docs:** [http://localhost:5000/api/docs](http://localhost:5000/api/docs)
    *   **Admin Login:** `admin@parkapp.com` / `admin123`
    *   **User Login:** `user@parkapp.com` / `user123`

## Running Tests

This project uses `pytest`. Run all tests using `uv`:

```bash
uv run pytest
```

##  API Documentation


Once the application is running, access the interactive API docs at:
`http://localhost:5000/api/docs` (or similar path depending on config).
