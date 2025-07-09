# CMMS (Computerized Maintenance Management System)

This project is a web-based CMMS application built with Django (backend) and React (frontend), containerized with Docker.

## Project Structure

```
cmms/
├── backend/
│   ├── cmms_api/         # Django project directory
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── assets/           # Django app for Asset Management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── corrective_maintenance/ # Django app for Corrective Maintenance
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── preventive_maintenance/ # Django app for Preventive Maintenance
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── manage.py         # Django management script
│   ├── Dockerfile        # Backend Dockerfile
│   └── requirements.txt  # Backend Python dependencies
├── frontend/
│   ├── app/              # React application root
│   │   ├── public/
│   │   │   └── index.html
│   │   ├── src/
│   │   │   ├── App.css
│   │   │   ├── App.tsx
│   │   │   ├── index.css
│   │   │   └── index.tsx
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── tailwind.config.js
│   │   └── postcss.config.js
│   └── Dockerfile        # Frontend Dockerfile (parent of 'app/')
└── docker-compose.yml    # Docker Compose configuration
```

## Prerequisites

*   Docker
*   Docker Compose

## Setup and Running

1.  **Environment Variables:**
    *   The backend uses environment variables for configuration (e.g., `DJANGO_SECRET_KEY`, database credentials). These can be set in a `.env` file in the `cmms/` root directory, which `docker-compose.yml` will automatically pick up if not overridden.
    *   Example `.env` file:
        ```env
        # Django Backend
        DJANGO_SECRET_KEY=your_very_secret_django_key_here_!change_me!
        DJANGO_DEBUG=True
        DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend,frontend # Add frontend hostname if needed for CORS

        # PostgreSQL Database
        DB_NAME=cmms_db
        DB_USER=cmms_user
        DB_PASSWORD=supersecretpassword
        DB_HOST=db
        DB_PORT=5432
        # DB_PORT_HOST=5432 # Optional: Host port for DB if you need direct access

        # React Frontend (if it needs env vars passed during build or runtime)
        # Example: REACT_APP_API_BASE_URL=http://localhost:8000/api
        # Note: REACT_APP_API_BASE_URL is already set in docker-compose.yml for development
        ```

2.  **Build and Run Containers:**
    Navigate to the root `cmms/` directory where `docker-compose.yml` is located.
    Run the following command:
    ```bash
    docker-compose up --build
    ```
    This command will:
    *   Build the Docker images for the `backend` and `frontend` services if they don't exist or if their Dockerfiles/contexts have changed.
    *   Start the `db` (PostgreSQL), `backend` (Django), and `frontend` (React/Nginx) services.
    *   The backend service will automatically run `makemigrations` (for all apps) and `migrate` on startup. If you add new apps or make model changes, this should handle it. If you need to create migrations for a specific app, you can do it manually (see Development Notes).

3.  **Accessing the Application:**
    *   **Backend API:** Base URL `http://localhost:8000/api/`
        *   Asset Management: `http://localhost:8000/api/assets/`
        *   Preventive Maintenance:
            *   Maintenance Plans: `http://localhost:8000/api/pm/maintenance-plans/`
            *   PM Tasks: `http://localhost:8000/api/pm/pm-tasks/`
            *   PM Checklist Items: `http://localhost:8000/api/pm/pm-checklist-items/`
            *   PM SOPs: `http://localhost:8000/api/pm/pm-sops/`
        *   Corrective Maintenance:
            *   Breakdown Reports: `http://localhost:8000/api/cm/breakdown-reports/`
            *   Fault Categories: `http://localhost:8000/api/cm/fault-categories/`
            *   Root Causes: `http://localhost:8000/api/cm/root-causes/`
        *   Admin panel: `http://localhost:8000/admin/` (You'll need to create a superuser first)
    *   **Frontend UI:** `http://localhost:3000/`

4.  **Creating a Django Superuser (for admin panel access):**
    Once the containers are running, open another terminal and execute:
    ```bash
    docker-compose exec backend python manage.py createsuperuser
    ```
    Follow the prompts to create an admin user.

## Development Notes

*   **Backend:** The backend code is mounted as a volume into the `backend` container. Django's development server will typically auto-reload on code changes.
*   **Frontend:** The frontend code (inside `frontend/app`) is also mounted.
    *   The provided `frontend/Dockerfile` builds the React app and serves it with Nginx. For development with hot-reloading, you would typically modify the `frontend/Dockerfile` to use `CMD ["npm", "start"]` and ensure `react-scripts start` is running. The current `docker-compose.yml` attempts to configure environment variables that are often used with `react-scripts start` (like `CHOKIDAR_USEPOLLING`).
    *   If you modify the frontend Dockerfile to use `npm start`, ensure the `ports` in `docker-compose.yml` for the frontend service map to the port used by `react-scripts start` (usually 3000), e.g., `"3000:3000"`. The current Nginx setup in the Dockerfile serves on port 80 in the container, which is mapped to 3000 on the host.

*   **Database Migrations:**
    *   To make new migrations after changing models (replace `app_name` with the specific app like `assets` or `preventive_maintenance` if you only want to target one):
        ```bash
        docker-compose exec backend python manage.py makemigrations [app_name]
        ```
    *   To apply migrations (usually handled on startup by the `command` in `docker-compose.yml`, but can be run manually):
        ```bash
        docker-compose exec backend python manage.py migrate
        ```

## Stopping the Application

*   To stop the containers:
    ```bash
    docker-compose down
    ```
*   To stop and remove volumes (including database data):
    ```bash
    docker-compose down -v
    ```

---

## ERD (Entity-Relationship Diagram) - Asset Model (Initial)

```
+---------------------+
| Asset               |
+---------------------+
| uuid (PK)           |  UUIDField, default=uuid.uuid4, editable=False
| name                |  CharField(255)
| tag                 |  CharField(100), unique, blank, null
| model               |  CharField(255), blank, null
| serial_number       |  CharField(255), unique, blank, null
| location            |  CharField(255), blank, null
| criticality         |  CharField(50), blank, null (e.g., "High", "Medium", "Low")
| installation_date   |  DateField, blank, null
| created_at          |  DateTimeField, auto_now_add=True
| updated_at          |  DateTimeField, auto_now=True
+---------------------+

+-----------------------------------+
| MaintenancePlan                   |
+-----------------------------------+
| uuid (PK)                         | UUIDField
| asset (FK)                        | -> Asset.uuid
| name                              | CharField(255)
| description                       | TextField, blank, null
| schedule_type                     | CharField(10) (TIME, USAGE, CONDITION)
| interval_days                     | PositiveIntegerField, blank, null (for TIME)
| usage_metric                      | CharField(100), blank, null (for USAGE)
| usage_threshold                   | FloatField, blank, null (for USAGE)
| condition_threshold_description   | TextField, blank, null (for CONDITION)
| is_active                         | BooleanField, default=True
| created_at                        | DateTimeField, auto_now_add=True
| updated_at                        | DateTimeField, auto_now=True
+-----------------------------------+
      |
      |1..* (Asset can have multiple plans)
      V
+---------------------+
| Asset               | (defined previously)
+---------------------+


+-----------------------------------+
| PMTask                            |
+-----------------------------------+
| uuid (PK)                         | UUIDField
| maintenance_plan (FK)             | -> MaintenancePlan.uuid
| description                       | TextField
| estimated_duration_hours          | DecimalField(5,2), blank, null
| assigned_to_role                  | CharField(100), blank, null
| sequence_order                    | PositiveIntegerField, default=0
| created_at                        | DateTimeField, auto_now_add=True
| updated_at                        | DateTimeField, auto_now=True
+-----------------------------------+
      |
      |1..* (Plan can have multiple tasks)
      V
+-----------------------------------+
| MaintenancePlan                   | (defined above)
+-----------------------------------+


+-----------------------------------+
| PMChecklistItem                   |
+-----------------------------------+
| uuid (PK)                         | UUIDField
| pm_task (FK)                      | -> PMTask.uuid
| item_description                  | CharField(500)
| is_mandatory                      | BooleanField, default=True
| expected_result                   | CharField(255), blank, null
| sequence_order                    | PositiveIntegerField, default=0
| created_at                        | DateTimeField, auto_now_add=True
| updated_at                        | DateTimeField, auto_now=True
+-----------------------------------+
      |
      |1..* (Task can have multiple checklist items)
      V
+-----------------------------------+
| PMTask                            | (defined above)
+-----------------------------------+


+-----------------------------------+
| PreventiveMaintenanceSOP          |
+-----------------------------------+
| uuid (PK)                         | UUIDField
| maintenance_plan (FK, optional)   | -> MaintenancePlan.uuid
| pm_task (FK, optional)            | -> PMTask.uuid
| title                             | CharField(255)
| document                          | FileField
| version                           | CharField(50), blank, null
| upload_date                       | DateField, auto_now_add=True
| description                       | TextField, blank, null
| created_at                        | DateTimeField, auto_now_add=True
| updated_at                        | DateTimeField, auto_now=True
+-----------------------------------+
 (Can be linked to MaintenancePlan, PMTask, or both)


+-----------------------------------+
| FaultCategory                     |
+-----------------------------------+
| uuid (PK)                         | UUIDField
| name                              | CharField(100), unique
| description                       | TextField, blank, null
| created_at                        | DateTimeField, auto_now_add=True
| updated_at                        | DateTimeField, auto_now=True
+-----------------------------------+


+-----------------------------------+
| RootCause                         |
+-----------------------------------+
| uuid (PK)                         | UUIDField
| name                              | CharField(255)
| description                       | TextField, blank, null
| category (FK, optional)           | -> FaultCategory.uuid
| created_at                        | DateTimeField, auto_now_add=True
| updated_at                        | DateTimeField, auto_now=True
+-----------------------------------+
      |
      |0..1 (RootCause can have one FaultCategory)
      V
+-----------------------------------+
| FaultCategory                     | (defined above)
+-----------------------------------+


+-----------------------------------+
| BreakdownReport                   |
+-----------------------------------+
| uuid (PK)                         | UUIDField
| asset (FK)                        | -> Asset.uuid
| reported_by (FK, optional)        | -> User.id (Django User model)
| report_time                       | DateTimeField, auto_now_add=True
| description_of_fault              | TextField
| severity                          | CharField(20) (LOW, MEDIUM, HIGH, CRITICAL)
| status                            | CharField(20) (REPORTED, INVESTIGATING, RESOLVED, etc.)
| downtime_started_at (optional)    | DateTimeField, blank, null
| downtime_ended_at (optional)      | DateTimeField, blank, null
| resolution_details (optional)     | TextField, blank, null
| root_cause_analysis (optional)    | TextField, blank, null
| identified_root_causes (M2M, opt) | -> RootCause.uuid
| created_at                        | DateTimeField, auto_now_add=True
| updated_at                        | DateTimeField, auto_now=True
+-----------------------------------+
      |
      |1..* (Asset can have multiple breakdown reports)
      V
+---------------------+
| Asset               | (defined previously)
+---------------------+
      |
      |0..* (BreakdownReport can have multiple RootCauses)
      V
+-----------------------------------+
| RootCause                         | (defined above)
+-----------------------------------+

```
*(More models and relationships will be added as other modules are developed.)*
