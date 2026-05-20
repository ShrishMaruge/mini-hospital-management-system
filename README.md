# Mini Hospital Management System

A full-stack Hospital Management System built with Django and PostgreSQL, featuring role-based access control, race-condition-safe appointment booking, Google Calendar integration, and a decoupled serverless email notification service.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [System Architecture](#system-architecture)
- [Database Design](#database-design)
- [Booking Workflow](#booking-workflow)
- [Design Decisions](#design-decisions)
- [Security](#security)
- [API Integrations](#api-integrations)
- [Demo Credentials](#demo-credentials)
- [Limitations](#limitations)
- [AI Tool Usage](#ai-tool-usage)
- [Author](#author)

---

## Features

### Authentication

- Doctor and Patient signup and login with role-based access control
- OTP-based email verification on registration
- Secure password hashing via Django's built-in authentication system
- Session-based authentication with CSRF protection throughout

### Doctor Features

- Create, edit, and delete availability slots
- View incoming appointment requests from patients
- Accept or reject booking requests
- Manage appointment cancellations
- Google Calendar integration for automatic event creation on confirmation

### Patient Features

- Browse available doctors and their open time slots
- Book appointments from available slots
- Cancel existing appointments
- Google Calendar integration for automatic event sync on booking

### Booking System

- Prevents double booking with race-condition-safe slot locking
- Atomic backend validation ensures only one booking succeeds per slot
- Full booking status lifecycle tracking from pending through confirmed, rejected, or cancelled

### Serverless Email Service

- Fully decoupled email microservice running independently from the Django backend
- Local execution via serverless-offline for development
- Sends welcome emails on signup and booking confirmation emails on appointment acceptance

### Google Calendar Integration

- OAuth2-based secure Google account linking for both doctors and patients
- Automatic event creation in both the doctor's and the patient's calendars on confirmation
- Access and refresh token storage with automatic token refresh on expiry

---

## Tech Stack

| Technology | Role |
|---|---|
| Django | Backend Web Framework |
| PostgreSQL | Relational Database |
| Django ORM | Database Abstraction Layer |
| HTML and CSS | Frontend Templates |
| Google Calendar API | Calendar Event Management |
| OAuth2 with PKCE | Secure Google Authentication |
| Serverless Framework | Email Microservice |
| serverless-offline | Local Serverless Testing |
| Gmail SMTP | Email Delivery |

---

## Project Structure

```
Mini_Hospital_Management_System/
│
├── README.md
│
├── ai-tool-usage-log/
│   ├── chatgpt-thread-1.md
│   └── ...
│
├── hms/
│   ├── accounts/
│   ├── appointments/
│   ├── doctors/
│   ├── templates/
│   ├── static/
│   ├── utils/
│   ├── manage.py
│   └── ...
│
├── email-service/
│   ├── handler.py
│   ├── serverless.yml
│   ├── requirements.txt
│   └── ...
│
└── requirements.txt
```

---

## Setup and Installation

### Prerequisites

Make sure the following are installed on your system before proceeding.

- Python 3.11 or higher
- PostgreSQL
- Node.js
- Serverless Framework

---

### Step 1 — Clone the Repository

```bash
git clone <your-github-repo-link>
cd Mini_Hospital_Management_System
```

---

### Step 2 — PostgreSQL Setup

Open your PostgreSQL shell and create the database.

```sql
CREATE DATABASE hms_db;
```

---

### Step 3 — Configure Environment Variables

Create a `.env` file inside the `hms/` directory and add the following values.

```env
# Django
SECRET_KEY=your_secret_key
DEBUG=True

# Database
DB_NAME=hms_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_email_app_password

# Google OAuth2
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8001/google/callback/
```

---

### Step 4 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5 — Run Migrations and Start the Django Server

```bash
cd hms
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 8001
```

The application runs at `http://127.0.0.1:8001`

---

### Step 6 — Setup and Run the Email Microservice

```bash
npm install -g serverless

cd email-service
pip install -r requirements.txt
npm install
serverless offline
```

The email service runs locally at `http://localhost:3000`

---

### Step 7 — Google OAuth2 Setup

1. Go to the Google Cloud Console and create a new project
2. Enable the Google Calendar API
3. Configure the OAuth Consent Screen
4. Add `http://127.0.0.1:8001/google/callback/` as an authorized redirect URI
5. Generate your Client ID and Client Secret
6. Add both values to your `.env` file

---

## System Architecture

The system is composed of two independent services that communicate over HTTP.

**Django HMS Backend** handles all core application logic including authentication, slot management, appointment booking, Google Calendar integration, role-based access control, and all database operations.

**Serverless Email Microservice** is a fully decoupled service responsible solely for sending email notifications. The Django backend triggers it via HTTP requests, keeping email delivery concerns cleanly separated from core business logic.

---

## Database Design

### Core Tables

| Table | Description |
|---|---|
| accounts_user | Stores doctor and patient information, roles, OAuth tokens, and authentication details |
| doctors_availability | Stores doctor availability slots and their current booking state |
| appointments_booking | Stores booking records, appointment statuses, and Google Calendar event IDs |
| appointments_cancelledbooking | Audit log for all cancelled appointments |
| appointments_rejectedbooking | Audit log for all rejected appointment requests |

### Relationships

One doctor can have many availability slots, represented by a ForeignKey from availability to the user.

One slot can have only one booking, enforced by a OneToOneField between availability and booking. This makes duplicate bookings structurally impossible at the database schema level, independent of any application-layer logic.

---

## Booking Workflow

1. Doctor creates availability slots
2. Patient browses available slots
3. Patient submits a booking request
4. Backend validates slot availability atomically inside a database transaction
5. If the slot is free, the booking is created and the slot is immediately locked
6. If the slot is already taken, an error is returned and no booking is created
7. Doctor reviews the pending request and accepts or rejects it
8. On acceptance, Google Calendar events are created in both the doctor's and patient's calendars
9. Email notifications are triggered through the serverless email microservice

### Email Triggers

| Trigger | When It Fires |
|---|---|
| SIGNUP_WELCOME | User successfully completes registration |
| BOOKING_CONFIRMATION | Doctor accepts an appointment request |

---

## Design Decisions

### The Race Condition Problem

The primary engineering challenge in this system was preventing two patients from simultaneously booking the same appointment slot.

Consider this scenario: Patient A and Patient B both view the same open slot and click Book at nearly the same moment. Both requests arrive at the server within milliseconds of each other. Without proper handling, both could read the slot as available, both could pass the availability check, and both bookings could be written to the database. The result would be two confirmed bookings for the same slot.

Two approaches were evaluated to solve this.

---

### Option 1 — Frontend Validation Only

This approach disables already-booked slots in the UI and dynamically refreshes slot availability as changes occur.

**Advantages:** Simpler to implement with less backend complexity.

**Problems:** Frontend state can become stale between the time a user loads the page and the time they submit. Multiple users viewing the same page at the same time can all see the slot as available. Concurrent form submissions bypass the UI state entirely. Frontend validation is a user experience enhancement, not a data integrity mechanism.

This approach was rejected because it cannot guarantee correctness under concurrent access.

---

### Option 2 — Backend Transactional Validation (Chosen)

This approach validates slot availability inside an atomic database transaction. The slot is locked and the booking is committed as a single indivisible operation. Any concurrent request that reaches the same slot after the lock has been acquired receives an error response and no booking is created.

**Advantages:** Guarantees exactly one booking per slot regardless of traffic volume. The database remains the single source of truth. The system behaves correctly under any level of concurrent access and is production-ready.

This approach was chosen because appointment booking is a critical operation where data correctness is more important than implementation simplicity. Even if two patients submit booking requests for the same slot at exactly the same time, only one booking will succeed.

---

## Security

| Feature | Implementation |
|---|---|
| Password Storage | Django's built-in PBKDF2 password hashing |
| Session Security | Django session-based authentication |
| CSRF Protection | Django CSRF middleware on all forms |
| OAuth State Validation | State parameter verification on the OAuth callback |
| PKCE | Verifier and challenge flow for Google OAuth |
| Route Protection | Role-based decorators applied to all views |
| Slot Integrity | Future-slot validation and overlapping slot prevention |

---

## API Integrations

### Google Calendar API

Used to create calendar events for both the doctor and the patient when an appointment is confirmed. Authentication is handled via OAuth2 with PKCE. Access tokens and refresh tokens are stored in the database, and token refresh is handled automatically when tokens expire.

### Gmail SMTP

Used by the serverless email microservice to deliver welcome emails on user registration, booking confirmation emails when an appointment is accepted, and cancellation notification emails when an appointment is cancelled.

---

## Demo Credentials

Use these credentials to explore the system without registering a new account.

| Role | Username | Password |
|---|---|---|
| Doctor | doctor_demo | doctor123 |
| Patient | patient_demo | patient123 |

---

## Limitations

### Current Limitations

**Local development only.** The system runs entirely on localhost and has not been deployed to a production environment.

**Unencrypted OAuth token storage.** Google OAuth access and refresh tokens are stored as plaintext in the database. In a production system, tokens should be encrypted at rest and secrets should be managed through a dedicated secrets manager.

**No real-time updates.** The system does not use WebSockets or any push mechanism. Users must refresh the page manually to see updated booking states.

**Basic frontend.** The UI was built to demonstrate functionality rather than to deliver a polished user experience. Layout and visual design are minimal.

**Synchronous email delivery.** Emails are sent inline during the request cycle. In production, this should be moved to an asynchronous queue using Celery and RabbitMQ to avoid blocking and handle failures gracefully.



---

## AI Tool Usage

AI tools were used during development to assist with implementation decisions and debugging. All interaction logs are documented transparently in the `ai-tool-usage-log/` directory.

| Tool | Purpose |
|---|---|
| codex | Implementation guidance and debugging |
| ChatGPT | Code review and architecture discussion |

---

## Author

**Shrish Maruge**  
B.Tech CSE — Artificial Intelligence and Machine Learning