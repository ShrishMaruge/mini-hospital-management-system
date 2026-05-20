# Debugging Notes

---

## 1. OAuth PKCE Error

### Error

```text
Google OAuth Error: (invalid_grant) Missing code verifier
```

### Root Cause

OAuth PKCE verifier was not persisted between connect and callback requests.

### Fix

Stored:

```python
flow.code_verifier
```

inside Django session.

---

## 2. MultipleObjectsReturned Error

### Error

```text
get() returned more than one User
```

### Root Cause

Using:

```python
User.objects.get(role="doctor")
```

when multiple doctor users existed.

### Fix

Query users using unique fields such as email or username.

---

## 3. Missing Calendar Events

### Problem

Appointments confirmed but no Google Calendar events created.

### Root Cause

Booking model lacked event ID storage.

### Fix

Added:

```python
doctor_calendar_event_id
patient_calendar_event_id
```

to Booking model.

---

## 4. Google Calendar Token Handling

### Problem

Google credentials not being stored correctly.

### Fix

Implemented:
- access token storage
- refresh token storage
- token expiry tracking
- automatic token refresh

---

## 5. Race Condition Risk

### Problem

Potential simultaneous booking issue.

### Fix

Discussed backend atomic booking strategy and slot locking validation.

---

## 6. PostgreSQL Reset

### Purpose

Needed clean database for end-to-end testing.

### Method Used

```sql
TRUNCATE TABLE table_name RESTART IDENTITY CASCADE;
```

Successfully reset all HMS application tables.