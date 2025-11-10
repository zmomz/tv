# Execution Engine

This is a fully automated trading execution engine with an integrated web UI.

## Running the Application

To run the application, you will need Docker and Docker Compose installed.

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd execution-engine
    ```

2.  **Create a `.env` file:**
    Create a `.env` file in the `backend` directory with the necessary environment variables. You can use `backend/.env.example` as a template.

3.  **Run with Docker Compose:**
    ```bash
    docker-compose up --build
    ```

4.  **Access the application:**
    *   **Frontend:** [http://localhost:3000](http://localhost:3000)
    *   **Backend API:** [http://localhost:8000](http://localhost:8000)

## Setup

Refer to `plan.md` for detailed setup and development instructions.
