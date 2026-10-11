# Faculty Consultation and Scheduling System (SA01) - Agent Guidelines & Installed Plugins

## Project Context
This project implements the **Web-Based Faculty Consultation and Scheduling System** as planned in `faculty-consultation-system-plan.md`.

- **Framework**: Python 3.12+ with Django 5.x (modular apps: `accounts`, `directory`, `availability`, `bookings`, `records`, `notifications`, `reports`, `core`)
- **Database**: PostgreSQL (relational model, constraints, indexes, transactional concurrency)
- **Frontend & UI**: Tailwind CSS with DaisyUI (custom ICCT theme), htmx (seamless slot loading and booking updates), FullCalendar (interactive weekly availability)
- **Background Tasks & Reminders**: SMTP email reminders via Django-Q or scheduled commands
- **Reporting**: WeasyPrint / ReportLab PDF consultation reports

---

## Installed Plugins & Skill Packs

The following plugins and skills have been installed into `.agents/plugins` and `.agents/skills` from `wshobson/agents` and `sickn33/agentic-awesome-skills`:

### 1. Backend & Django Architecture
* **`agentic-bundle-python-pro`** (`sickn33`):
  - `django-pro`: Django 5.x architecture, model design, query optimization, CBVs, custom user models, admin customization.
  - `django-access-review`: IDOR and access control verification (ensuring students cannot view other students' records and private session notes remain confidential).
  - `django-perf-review`: ORM query auditing, prefetch/select_related optimization for FullCalendar and slot generation.
  - `python-pro` & `python-testing-patterns`: Clean code patterns, pytest-django guidelines.
* **`python-development`** (`wshobson`):
  - `python-background-jobs`: Task scheduling patterns for booking reminders and no-show checks.
  - `python-project-structure`: Multi-app layout guidance matching the 8-app modular architecture.
  - `python-error-handling` & `python-code-style`: Exception hierarchies and robust failure recovery.

### 2. Database & Data Modeling (PostgreSQL)
* **`database-design`** (`wshobson`):
  - `postgresql-table-design`: Table modeling, constraints, foreign keys, and indexes for User, Student, Faculty, Availability, Booking, and Session records.
* **`database-migrations`** (`wshobson`):
  - Database migration best practices, data migrations, and schema validation.
* **`postgres-best-practices`** (`sickn33`):
  - Concurrency & locking strategies (preventing race conditions when two students attempt to book the same pending slot).

### 3. Frontend, UI Design & Interactivity
* **`agentic-bundle-web-wizard`** (`sickn33`):
  - `tailwind-patterns`: Modern Tailwind CSS architecture, custom design token setup for the school's ICCT theme.
  - `frontend-design` & `form-cro`: Clean UX for multi-step consultation booking and status confirmation.
  - `accessibility-compliance-accessibility-audit`: WCAG accessibility for forms and calendars.
* **`ui-design`** (`wshobson`):
  - `design-system-patterns` & `responsive-design`: Responsive UI layouts compatible with both desktop and mobile browser viewports.

### 4. PDF Reporting & Documents
* **`agentic-bundle-documents-presentations`** (`sickn33`):
  - `pdf-official`: Python-based PDF generation workflows for consultation summaries, attendance reports, and department exports.

### 5. Authentication, Quality Assurance & Security
* **`developer-essentials`** (`wshobson`):
  - `auth-implementation-patterns`: Multi-role RBAC (Student, Faculty, Admin), session security.
  - `code-review-excellence` & `sql-optimization-patterns`: Best practices for PRs and queries.
* **`agentic-bundle-qa-testing`** (`sickn33`):
  - `test-driven-development` & `e2e-testing-patterns`: Comprehensive unit tests for slot conflicts, status transitions, and role boundaries.
* **`documentation-generation`** (`wshobson`):
  - `architecture-decision-records`: Tracking key architectural decisions (ERD, DFD, API contracts).

---

## Architectural Rules for Agents Working on this Codebase

1. **Separation of Concerns**:
   - Booking slot conflict checks, status transitions, and business logic belong in model methods or service files (`bookings/services.py`), never inside templates.
2. **Access Control & Privacy**:
   - Never expose consultation session notes or student consultation history across different students or unauthorized faculty.
   - All booking queries must be filtered by the authenticated user's role and ownership.
3. **Atomic Slot Reservation**:
   - Booking slot state changes (Pending, Confirmed, Cancelled) must use database transactions (`transaction.atomic()`) and `select_for_update()` to prevent double bookings.
4. **Theme Consistency**:
   - Use Tailwind CSS and DaisyUI theme variables configured for the ICCT theme across all views and components.
