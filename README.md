# MiniIAM – Identity Lifecycle Simulator

A lightweight **Identity and Access Management (IAM)** simulator built with **FastAPI**, **PostgreSQL**, and deployed on **Google Cloud Run** with **Cloud SQL**.

MiniIAM demonstrates core IAM concepts including user provisioning/deprovisioning, role-based access control (RBAC), access request workflows, and audit logging.

---

## Features

- **User Registration & Authentication** – Secure signup/login with JWT tokens and bcrypt password hashing
- **Role-Based Access Control (RBAC)** – Three roles: `Admin`, `Manager`, `Employee` with enforced permissions
- **User Deprovisioning** – Admins can deactivate user accounts (identity lifecycle management)
- **Access Request Workflow** – Employees request access to resources; Managers/Admins approve
- **Department-Scoped Approvals** – Managers can only approve requests within their own department
- **Audit Logging** – All IAM actions are logged with timestamps and IP addresses
- **Access Review Report** – Admin-only endpoint to generate compliance-style user access reports

---

## Tech Stack

| Layer          | Technology                                  |
|----------------|---------------------------------------------|
| **Backend**    | Python 3.11+, FastAPI                       |
| **Database**   | PostgreSQL (Cloud SQL)                      |
| **ORM**        | SQLAlchemy                                  |
| **Auth**       | JWT (python-jose), bcrypt (passlib)         |
| **Hosting**    | Google Cloud Run                            |
| **Container**  | Docker                                      |
| **DB Hosting** | Google Cloud SQL (PostgreSQL)               |

---

## Project Structure

```
mini-iam/
├── app/
│   ├── __init__.py       # Package init
│   ├── main.py           # FastAPI app, routes, and endpoints
│   ├── auth.py           # JWT creation, password hashing, authentication
│   ├── database.py       # SQLAlchemy engine & session (Cloud SQL)
│   ├── models.py         # ORM models: User, AccessRequest, AuditLog
│   ├── audit.py          # Audit logging helper
│   ├── rbac.py           # Role-based access control dependency
│   └── schemas.py        # Pydantic schemas (extensible)
├── Dockerfile            # Container image definition
├── requirements.txt      # Python dependencies
├── .gitignore            # Git ignore rules
├── .env.example          # Example environment variables
└── README.md             # This file
```

---

## API Endpoints

| Method | Endpoint                     | Auth Required | Role Required | Description                          |
|--------|------------------------------|---------------|---------------|--------------------------------------|
| GET    | `/`                          | No            | —             | Health check                         |
| POST   | `/register`                  | No            | —             | Register a new user                  |
| POST   | `/login`                     | No            | —             | Login and receive JWT token          |
| POST   | `/users/{user_id}/deprovision` | Yes         | Admin         | Deactivate a user account            |
| POST   | `/access/request`            | Yes           | Any           | Submit an access request             |
| POST   | `/access/approve/{req_id}`   | Yes           | Admin/Manager | Approve a pending access request     |
| GET    | `/reports/access-review`     | Yes           | Admin         | Generate access review report        |

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database (local or Cloud SQL)
- Docker (for containerized deployment)
- Google Cloud SDK (for GCP deployment)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cyb3rcr4t0712/mini-iam.git
   cd mini-iam
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database password and secret key
   export DB_PASSWORD=your_db_password
   export SECRET_KEY=$(openssl rand -hex 32)
   ```

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

6. **Open the API docs:**
   Navigate to `http://localhost:8080/docs` for the interactive Swagger UI.

---

## Deployment (Google Cloud)

### 1. Build & Push Docker Image

```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT/mini-iam-repo/mini-iam-app
```

### 2. Deploy to Cloud Run

```bash
gcloud run deploy mini-iam-service \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT/mini-iam-repo/mini-iam-app \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --service-account=miniiam-sa@YOUR_PROJECT.iam.gserviceaccount.com \
  --add-cloudsql-instances=YOUR_PROJECT:us-central1:mini-iam-db \
  --set-env-vars 'DB_PASSWORD=YOUR_DB_PASSWORD,SECRET_KEY=YOUR_SECRET_KEY'
```

### 3. Set Cloud SQL User Password

```bash
gcloud sql users set-password miniiam_user \
  --instance=mini-iam-db \
  --password=YOUR_DB_PASSWORD
```

---

## Environment Variables

| Variable      | Description                        | Required |
|---------------|------------------------------------|----------|
| `DB_PASSWORD` | PostgreSQL database password       | Yes      |
| `SECRET_KEY`  | JWT signing secret (hex string)    | Yes      |

---

## Usage Examples

### Register a User
```bash
curl -X POST "https://YOUR_SERVICE_URL/register?username=alice&password=securepass&role=Employee&department=Engineering"
```

### Login
```bash
curl -X POST "https://YOUR_SERVICE_URL/login?username=alice&password=securepass"
```

### Request Access (with JWT token)
```bash
curl -X POST "https://YOUR_SERVICE_URL/access/request?resource=AWS%20Console&reason=Need%20for%20deployment" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Approve Access Request (Admin/Manager)
```bash
curl -X POST "https://YOUR_SERVICE_URL/access/approve/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Generate Access Review Report (Admin only)
```bash
curl -X GET "https://YOUR_SERVICE_URL/reports/access-review" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Security Notes

> ⚠️ **Important:** Never commit secrets to version control.

- Database passwords and secret keys are passed via environment variables
- Passwords are hashed using **bcrypt** before storage
- Authentication uses **JWT Bearer tokens** with 60-minute expiration
- Add your `.env` file to `.gitignore` to prevent accidental commits
- Use **Google Secret Manager** for production secret management

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for more details.

---
