# Faculty Consultation and Scheduling System: Development Plan

Web-Based Faculty Consultation and Scheduling System (SA01) · 2026-10-11

## Scope

The system lets faculty publish consultation hours and lets students book those slots online. It also records each session and produces simple reports. We use our school as the case study.

**In scope (first version)**

- Accounts and roles for students, faculty, and an admin or department head
- Faculty availability setup, shown in a weekly calendar
- Student booking, cancelling, and rescheduling
- Faculty accept or decline, and session notes after each consultation
- Consultation categories, reminders, and basic reports

**Out of scope (unless the school asks)**

- Class scheduling and room booking
- Payments, grades, or any link to the enrollment system
- A mobile app (the web pages should work on a phone browser)

These lists are our starting assumption. Update them after the interviews, using the requirements tracker in the questionnaire.

## Tech stack

Django renders the pages itself, so the project needs no separate frontend app.

| Part | Choice | Used for |
| --- | --- | --- |
| Language and framework | Python with Django | Models, views, templates, login, admin panel |
| Database | PostgreSQL | Users, schedules, bookings, session records |
| Interactivity | htmx | Loading slots, booking, and status updates without full page reloads |
| Styling | Tailwind CSS with DaisyUI, using a custom ICCT theme | Layout, buttons, tables, modals, forms in the school's look |
| Calendar | FullCalendar | Weekly availability view for faculty and slot view for students |
| Reminders | Email through SMTP, with Django-Q or a scheduled command | Booking reminders and no-show checks |
| PDF reports | WeasyPrint or ReportLab | Printable consultation reports |
| Hosting | Render or similar for the demo, or the school server | Running the system |

FullCalendar is a JavaScript library. Django sends it the availability and booking data as JSON from a small endpoint, and htmx handles the forms around it.

**Theme:** the system uses the ICCT theme, so it looks like an official school system. Set the ICCT colors, logo, and font once as a custom DaisyUI theme in the Tailwind config, and every page and component picks them up. Get the official logo and color codes from the school (the registrar, the marketing office, or the school website) instead of guessing them, and include the logo in the header, the login page, and the PDF reports.

## Users and roles

There are three roles, so access control stays simple.

| Role | Can do | Cannot do |
| --- | --- | --- |
| Student | View faculty availability, book, cancel, or reschedule; see own history and advice given | See other students' records or edit faculty schedules |
| Faculty | Set availability, accept or decline requests, mark attendance, write session notes, view own reports | See other faculty's notes or change system rules |
| Admin or department head | Manage accounts, categories, and rules; view all schedules; run department reports | Edit the content of a faculty member's private session notes (to be confirmed) |

Who can see session notes is a privacy decision, so confirm it with the dean (questionnaire Part D, question 14).

## Modules and features

Must-haves cover the main problem: students cannot easily find when a teacher is free or book a time. Nice-to-haves come after the must-haves work.

| Module | Must have | Nice to have |
| --- | --- | --- |
| Accounts | Login, logout, roles, password reset | Import faculty and student lists from a spreadsheet |
| Availability | Faculty add weekly consultation hours and see them in FullCalendar | Block times that clash with class schedules automatically |
| Booking | Student picks faculty, date, slot, and category; cancel or reschedule | Group booking for capstone teams |
| Approval and status | Faculty accept or decline; statuses shown to both sides | Auto-approve for certain categories |
| Session records | Mark attended or no-show; short notes and outcome | Student sees advice given in their history |
| Notifications | Email reminder before the session | SMS or Messenger reminders |
| Reports | Sessions per faculty, per category, and per period; PDF export | Dashboard with charts |
| Admin | Manage users, categories, and basic rules | Audit log of changes |

Final priorities should come from the interviews and surveys, not from this table.

## Data model

These are the starting entities for the ERD. Field names will change after we see the school's real forms.

| Entity | Key fields | Relationships |
| --- | --- | --- |
| User | id, name, school email, role, password, active | One user is either a student or a faculty member (or admin) |
| Student | user, student number, program, year level, section | Makes many bookings |
| Faculty | user, employee ID, department | Has many availability slots and handles many bookings |
| Department | id, name | Has many faculty and students |
| Category | id, name, default length in minutes, is private | Used by many bookings |
| Availability | faculty, day of week or date, start time, end time, mode, location or link | Belongs to one faculty member |
| Booking | student, faculty, category, date, start time, end time, mode, status, reason | Has at most one session record |
| Session record | booking, attended or no-show, notes, outcome, recorded at | Belongs to one booking |
| Notification | user, booking, type, sent at | Belongs to a user and a booking |

If group booking is added later, a Booking would link to several students through a separate group-members table.

## Booking flow and statuses

A booking moves through a few statuses. This is the main flow for your DFD and flowchart.

1. Faculty add their consultation hours.
2. The student opens a faculty member's calendar and picks an open slot.
3. The student chooses a category and writes a short reason, then submits. Status: **Pending**.
4. The faculty member accepts or declines. Status: **Confirmed** or **Declined**.
5. Both sides get an email, and a reminder goes out before the session.
6. The student or faculty can cancel or reschedule before the deadline. Status: **Cancelled** or back to **Pending**.
7. After the session, the faculty member marks it **Completed** or **No-show** and adds notes.

| Status | Moves to | Who triggers it |
| --- | --- | --- |
| Pending | Confirmed, Declined, Cancelled | Faculty accept or decline; student cancels |
| Confirmed | Completed, No-show, Cancelled | Faculty after the session; either side cancels |
| Declined | (end) | Faculty |
| Cancelled | (end) | Student or faculty |
| Completed | (end) | Faculty |
| No-show | (end) | Faculty |

A slot is held as soon as a booking is Pending, so two students cannot take the same slot. If the school wants auto-approval, step 4 is skipped.

## Business rules to confirm

The numbers below are placeholders. Replace each one with what the school actually says.

| Rule | Placeholder | Ask whom |
| --- | --- | --- |
| Session length | 30 minutes, longer for capstone | Dean, faculty |
| Bookings per student | Up to 2 active bookings at a time | Dean |
| How far ahead a student can book | Up to 2 weeks | Faculty |
| Cancellation deadline | At least 2 hours before the session | Dean, faculty |
| No-show handling | Recorded and shown in reports, no penalty | Dean |
| Approval | Faculty approve each request | Faculty |
| Who a student can book | Any faculty, or only the subject teacher or adviser | Dean |
| Who sees session notes | Faculty only, plus the student for advice given | Dean, IT |
| Record retention | Keep for the school year | IT, registrar |

## Django project structure

A Django project is split into apps, so each module stays separate and each groupmate can own one.

| App | Contains |
| --- | --- |
| accounts | User model, roles, login, password reset, profile pages |
| directory | Department, Faculty, Student, and Category |
| availability | Faculty consultation hours and the JSON endpoint for FullCalendar |
| bookings | Booking model, status rules, student and faculty booking pages |
| records | Session records, attendance, notes |
| notifications | Emails and scheduled reminders |
| reports | Report pages and PDF export |
| core | Base templates, Tailwind setup, shared helpers |

Status changes and slot-conflict checks belong in the bookings app (in model methods or a service file), not in the templates, so the rules stay in one place.

## Build phases

The phases are in order, and each one ends with something we can show. We have no deadline yet, so add dates once the instructor gives them.

1. **Fact-finding:** interviews, student survey, and document review using the questionnaire. Done when the requirements tracker is filled and the scope is confirmed.
2. **Analysis and design:** requirements list, DFD, flowchart, ERD, and screen mockups. Done when the instructor approves the design.
3. **Setup:** Django project, PostgreSQL, Tailwind and DaisyUI with the ICCT theme, base layout, and login with roles. Done when each role can log in and sees its own home page.
4. **Availability and calendar:** faculty set hours, and FullCalendar shows them. Done when a faculty member can add and edit a week of consultation hours.
5. **Booking:** student booking, status changes, and slot-conflict checks with htmx. Done when a student can book and a faculty member can accept or decline.
6. **Records and notifications:** session notes, attendance, and email reminders. Done when a full consultation can go from request to completed record.
7. **Reports and admin:** reports with PDF export, plus category and user management. Done when the department head can run a report.
8. **Testing and documentation:** test cases, a trial with real users, fixes, and the user guide. Done when the test results are documented.

## Risks and open questions

**Risks**

- **Low adoption:** faculty or students keep using chat and walk-ins. Involve faculty early and keep the booking steps short.
- **Scope grows:** class scheduling or room booking creeps in. Keep to the scope section unless the instructor agrees.
- **Privacy of records:** session notes may contain sensitive information. Limit access by role and confirm the rules with the school.
- **Team skills:** the group is new to Django. Pick one small app first and learn from it.
- **Email delivery:** reminders may fail or land in spam. Test with the school email early.

**Open questions**

- [ ] Does SA01 need a working system, or only analysis and design?
- [ ] What are the consultation categories at our school, and do they have different rules?
- [ ] Can faculty and student accounts use the school email?
- [ ] Where will the system be hosted if it is used after the project?
- [ ] What is the deadline for each phase?
- [ ] Where do we get the official ICCT logo, colors, and font, and are we allowed to use them in the system?
