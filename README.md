# ICCT Faculty Consultation and Scheduling System (SA01)

A web-based consultation scheduling and academic advising management system designed for **ICCT Colleges Foundation, Inc.**

Built with **Python 3.12+**, **Django 5.x/6.x**, **Tailwind CSS & DaisyUI** (custom official ICCT school theme), **htmx**, **FullCalendar**, and **ReportLab**.

---

## Key Features & Modular Architecture

The application is structured into 8 modular Django apps:

1. **`accounts`**: Custom User model (`STUDENT`, `FACULTY`, `ADMIN`), secure session auth, and student registration.
2. **`directory`**: Departments (`CCS`, `CBA`, `CAS`, `COE`), Faculty directory search with department filters, and consultation categories.
3. **`availability`**: Faculty weekly consultation hours manager and interactive JSON feed for FullCalendar.
4. **`bookings`**: Atomic slot reservations preventing double bookings (`transaction.atomic()` + `select_for_update()`), active booking limit enforcement (max 2 active bookings per student), and htmx slot picker.
5. **`records`**: Post-session documentation with attendance tracking (`Attended` / `No-Show`), student-facing advice & deliverables, and confidential faculty private notes.
6. **`notifications`**: System notifications and email alerts on requests, approvals, declines, cancellations, and session advice.
7. **`reports`**: Filterable reporting dashboard with PDF consultation export generated via ReportLab with official ICCT branding.
8. **`core`**: Role-based landing dashboards (Student, Faculty, Admin), official ICCT theme styling, and base layouts.

---

## Getting Started

### 1. Environment & Dependencies

Activate the project virtual environment:
```powershell
.\.venv\Scripts\Activate.ps1
```

Or run directly using the `.venv` Python:
```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

### 2. Database & Migrations

By default, the system uses SQLite for seamless local execution with zero configuration. For production with PostgreSQL, simply set the `DATABASE_URL` environment variable:
```powershell
$env:DATABASE_URL = "postgres://user:password@localhost:5432/icct_consult_db"
.\.venv\Scripts\python.exe manage.py migrate
```

To run migrations:
```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

### 3. Demo Accounts & Seed Data

A management command is included to populate initial departments, faculty, categories, consultation hours, and demonstration bookings:
```powershell
.\.venv\Scripts\python.exe manage.py seed_data
```

#### Pre-configured Test Accounts:

| Role | Username / ID | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin / Dean** | `admin` | `admin123` | Department chair oversight & Django Admin access |
| **Faculty (CCS)** | `prof_turing` | `faculty123` | Prof. Alan Turing (Room 302 / Online) |
| **Faculty (CCS)** | `prof_lovelace`| `faculty123` | Prof. Ada Lovelace (Room 405 / Hybrid) |
| **Student** | `student_juan` | `student123` | Student ID `2026-00101` (BSIT-3A) |
| **Student** | `student_maria`| `student123` | Student ID `2026-00102` (BSCS-4A) |

### 4. Running the Development Server

Start the local server at `http://127.0.0.1:8000`:
```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

### 5. Running the Test Suite

Execute the automated test suite verifying slot conflict prevention, active booking limits, state machine transitions, and PDF generation:
```powershell
.\.venv\Scripts\python.exe manage.py test
```
