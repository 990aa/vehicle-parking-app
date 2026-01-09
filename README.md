# Vehicle Parking Management System

A production-grade, full-stack vehicle parking management application designed to demonstrate advanced Python, Flask, and system architecture concepts. This application handles user management, parking spot reservations, automated reporting, and payment integration.

##  System Overview

The application is built using a modern, scalable architecture splitting responsibilities across different services and layers:

-   **Backend:** Python Flask
-   **Database:** SQLAlchemy (ORM) with SQLite (Dev) / PostgreSQL (Prod ready)
-   **Task Queue:** Celery + Redis
-   **Caching:** Redis
-   **Frontend:** Vue.js + Jinja2 Templates
-   **API:** RESTful API with Swagger Documentation (Flask-RESTX)

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

##  Project Structure

```
vehicle-parking-app/
├── app.py                  # Application entry point & factory
├── celery_worker.py        # Celery worker process entry
├── extensions.py           # extensions initialization
├── controllers/            # Route handlers (Blueprints)
├── models/                 # Database models (SQLAlchemy)
├── jobs.py                 # Background task definitions
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS, JS, Images
├── frontend/               # Vue.js frontend source
└── tests/                  # Unit and Integration tests
```

##  Getting Started

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

4.  **Initialize Database:**
    (The application likely auto-initializes or requires a flask command, e.g., `flask db upgrade` if migrations are used, or runs setup on start).

### Running the Application

1.  **Start Redis Server** (in a separate terminal)
2.  **Start Celery Worker:**
    ```bash
    celery -A celery_worker.celery worker --loglevel=info
    ```
3.  **Start Flask App:**
    ```bash
    flask run
    # OR
    python app.py
    ```

##  Running Tests

This project uses `pytest`. Run all tests using `uv`:

```bash
uv run pytest
```

##  API Documentation

Once the application is running, access the interactive API docs at:
`http://localhost:5000/api/docs` (or similar path depending on config).
