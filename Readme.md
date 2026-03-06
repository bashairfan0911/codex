# ApprovIQ

ApprovIQ is a lightweight **3-tier web application** for student leave approvals in educational institutions.

## 3-Tier Architecture

1. **Presentation Tier** (`static/`)
   - Browser UI for students and approvers.
   - Pages and assets: `index.html`, `styles.css`, `app.js`.

2. **Application Tier** (`app/main.py`, `app/service.py`)
   - HTTP API layer for submitting requests and taking decisions.
   - Business rules enforce strict sequence:
     `Advisor -> HOD -> Principal`.

3. **Data Tier** (`app/repository.py`, SQLite DB)
   - Persistent storage for leave requests and approval decisions.
   - Database file auto-created at `data/approviq.db`.

## Features

- Submit student leave requests.
- Role-based stepwise approvals (Advisor, HOD, Principal).
- Rejection can happen at any stage and finalizes the request.
- Live status tracking with decision history.
- Simple dashboard-style UI.

## Run Locally

```bash
python -m app.main
```

Open: [http://localhost:8000](http://localhost:8000)

## API Endpoints

- `GET /api/requests` - list all requests with decision history.
- `POST /api/requests` - submit a new leave request.
- `POST /api/requests/{id}/decision` - approve/reject by role.

Example decision payload:

```json
{
  "role": "advisor",
  "action": "approve",
  "comment": "Eligible"
}
```
