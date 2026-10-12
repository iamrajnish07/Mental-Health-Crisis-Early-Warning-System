# Mental Health Crisis Early Warning System for Campuses

A privacy-conscious university student wellbeing platform combining voluntary daily wellbeing check-ins, personal baseline tracking, machine learning risk indicators, human-in-the-loop counsellor review workflows, and privacy-preserving administrative analytics.

> **Ethical Notice:** This application **does not** provide medical or psychiatric diagnoses, nor does it automatically label students with mental health conditions. Risk signals serve strictly as supportive flags to facilitate human counsellor check-ins.

---

## 1. System Architecture & Workflow

```text
              STUDENT
                 │
                 ▼
        Registration / Login
                 │
                 ▼
          Consent Management (Granular scopes & withdrawal)
                 │
                 ▼
       Wellbeing Check-in Form (Sleep, Activity, Mood, Social)
                 │
                 ▼
          FastAPI Backend
                 │
                 ▼
       Feature Engineering & Baseline Deviations (Sleep & Activity Shifts)
                 │
                 ▼
      Scikit-Learn ML Model (Random Forest & Logistic Regression)
                 │
                 ▼
       Wellbeing Support Indicator
                 │
        ┌────────┴────────┐
        ▼                 ▼
   Student View      Counsellor Queue (ALT-XXXX)
 (Trends & Tips)          │
                          ▼
                     Human Review & Case Notes
                          │
                          ▼
                 Aggregate Analytics (k-anonymity suppression)
```

---

## 2. Technology Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy
- **Database:** SQLite (development) / PostgreSQL (production ready)
- **Machine Learning:** Scikit-learn (RandomForestClassifier, LogisticRegression), Pandas, NumPy
- **Frontend:** Jinja2 Templates, HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Chart.js
- **Authentication & Security:** Bcrypt password hashing, HMAC-SHA256 signed session cookies, Role-Based Access Control (RBAC), Audit Logging
- **Testing:** Pytest, HTTPX

---

## 3. Project Structure

```text
├── app/
│   ├── config.py              # Application settings and environment paths
│   ├── database.py            # SQLAlchemy engine, session maker, Base
│   ├── main.py                # FastAPI app initialization and route mounts
│   ├── models/                # Database entities
│   │   ├── user.py            # User credentials, roles, pseudonymous refs
│   │   ├── consent.py         # Granular consent tracking and timestamps
│   │   ├── checkin.py         # Daily check-ins and personal baselines
│   │   ├── assessment.py      # ML indicators, deviations, reason codes
│   │   └── alert.py           # Counsellor case queue, follow-up notes, audit logs
│   ├── schemas/               # Pydantic validation schemas
│   ├── routers/               # Role-based endpoints
│   │   ├── auth.py            # Login, registration, session management
│   │   ├── students.py        # Student dashboard, checkin submission, data deletion
│   │   ├── consent.py         # Consent management and withdrawal
│   │   ├── counsellors.py     # Counsellor triage queue and case notes
│   │   ├── admin.py           # Administrator analytics and user oversight
│   │   └── api.py             # Health check, model metadata, JSON endpoints
│   ├── services/              # Business logic layer
│   │   ├── checkin_service.py # Check-in processing and baseline updates
│   │   ├── alert_service.py   # Counsellor queue triage and case management
│   │   └── analytics_service.py # Privacy-preserving aggregate metrics
│   └── security/              # Auth & RBAC
│       ├── authentication.py  # Bcrypt and HMAC session cookies
│       ├── authorization.py   # Role guards (require_student, require_counsellor, etc.)
│       └── audit.py           # Compliance audit logging
├── ml/
│   ├── preprocessing.py       # Imputation and standard scaling
│   ├── feature_engineering.py # Baseline calculations and deviation offsets
│   ├── train_model.py         # Training pipeline on synthetic data
│   ├── predict.py             # Risk scoring, safeguards, and explainable reason codes
│   └── saved_models/          # Exported joblib model and evaluation metadata
├── templates/                 # Jinja2 frontend views
│   ├── base.html              # Responsive navigation, hotlines, footer
│   ├── login.html             # Login form with one-click demo presets
│   ├── register.html          # Student registration form
│   ├── student_dashboard.html # Charts, trends, ML status, campus resources
│   ├── checkin.html           # 60-second interactive daily check-in
│   ├── consent.html           # Granular privacy settings and withdrawal
│   ├── counsellor_dashboard.html # Triage queue with status/priority filters
│   ├── alert_detail.html      # Individual case review, timeline, and actions
│   └── admin_dashboard.html   # k-anonymity suppressed aggregate analytics
├── static/
│   └── css/style.css          # Design system stylesheet
├── scripts/
│   └── seed_demo_data.py      # Demo accounts and synthetic check-in history
├── tests/                     # Automated test suite (16 tests)
├── requirements.txt
├── .env.example
├── run.py                     # Server launcher
└── README.md
```

---

## 4. Setup and Installation

### 1. Prerequisites
- Python 3.10+ installed

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Seed Demo Accounts & Synthetic Data
```bash
python scripts/seed_demo_data.py
```

### 4. Run the Application
```bash
python run.py
```
Open your browser at **http://127.0.0.1:8000**

---

## 5. Demo Accounts

For quick presentation and evaluation, pre-seeded accounts are available (with one-click auto-fill buttons on the login page):

| Role | Email | Password | Pseudonymous Ref |
|---|---|---|---|
| **Student** | `student@campus.edu` | `StudentPass123!` | `STU-1001` |
| **Counsellor** | `counsellor@campus.edu` | `CounsellorPass123!` | `CNS-2001` |
| **Administrator** | `admin@campus.edu` | `AdminPass123!` | `ADM-3001` |

---

## 6. Running Tests

Run the full automated pytest suite:
```bash
python -m pytest tests/ -v
```

All 16 tests validate:
- System health checks
- Secure login and cookie sessions
- Student registration and baseline initialization
- Daily check-in submissions and baseline updates
- Self-service data deletion workflows
- Consent recording and withdrawal
- Role-based route authorization guards
- Machine learning feature engineering and safety safeguards

---

## 7. College Project Demonstration Script

Follow this sequence for your presentation:
1. **Student Login & Consent:** Sign in as `student@campus.edu`. Show the granular consent screen explaining student agency and the non-diagnostic notice.
2. **Personal Baseline & Trends:** View the student dashboard. Show the 7-day sleep and activity charts generated from the student's personal baseline.
3. **Daily Check-in:** Submit today's check-in via `/student/checkin`. Demonstrate adjusting sleep/activity and optional mood inputs.
4. **Counsellor Review Queue:** Log out and log in as `counsellor@campus.edu`. Show the review queue, pseudonymous student references (`STU-1002`), reason codes, and record a follow-up action.
5. **Administrator Privacy-Preserving Analytics:** Log in as `admin@campus.edu`. Show university-level aggregate charts with small-group ($k \ge 5$) suppression protecting student identities, and review model training metadata (ROC-AUC, PR-AUC).
6. **Security & Authorization Check:** Attempt accessing `/counsellor/dashboard` while logged in as a student to demonstrate the backend 403 Forbidden enforcement.
