## Vehicle Parking App
This project is a multi-user Vehicle Parking App for managing 4 wheeler parking lots and reservations.

### Prerequisites

- Python 3.x
- Git

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/99daha/parking_app_24F2002963.git
    cd parking_app_24F2002963
    ```

2.  **Create a Virtual Environment:**

    ```bash
    python -m venv .venv
    ```

3.  **Activate the Virtual Environment:**

    **On Windows:**

    ```bash
    .venv\Scripts\activate
    ```

    **On macOS/Linux:**

    ```bash
    source .venv/bin/activate
    ```

4.  **Install Requirements:**

    ```bash
    pip install -r requirements.txt
    ```

5.  **Create a .env file:**

    Create a `.env` file in the root directory of the project and add the following line:

    ```
    SECRET_KEY='secret_key'
    ```
    Replace `'secret_key'` with a strong, unique secret key.

6.  **Run the Application:**

    ```bash
    python app.py
    ```

7.  **Access the Application:**

    Open any web browser and enter to the address:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)
