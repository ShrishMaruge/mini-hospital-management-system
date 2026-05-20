# ChatGPT / AI Assistance Report

## AI Tool Used

- ChatGPT (OpenAI)

---

## Purpose of AI Usage

AI assistance was used during the development of the Mini Hospital Management System (HMS) to accelerate debugging, improve architecture decisions, refine frontend components, and assist in documentation.

The final implementation, testing, integration, and verification were completed manually by the developer.

---

# What AI Was Used For

## 1. Google OAuth2 & Calendar Integration

AI assistance helped with:

- Implementing Google OAuth2 login flow
- Debugging OAuth state mismatch errors
- Fixing PKCE `Missing code verifier` issue
- Saving Google access and refresh tokens
- Handling OAuth callback validation
- Creating Google Calendar events
- Supporting both doctor and patient calendars
- Google Calendar attendee invitation flow

---

## 2. Backend Development

AI assistance was used for:

- Django model improvements
- Booking workflow implementation
- Slot creation validation
- Preventing overlapping appointments
- Atomic booking discussions
- Race condition handling strategies
- PostgreSQL debugging and cleanup
- Migration troubleshooting

---

## 3. Frontend Improvements

AI assistance helped improve:

- Doctor dashboard UI
- Patient dashboard UI
- Appointment table rendering
- Google Calendar connection indicators
- Form validation UX
- Responsive HTML improvements

---

## 4. Documentation

AI assistance was used for:

- README structure
- Setup instructions
- Architecture explanation
- Design decision documentation
- AI usage documentation

---

# Problems AI Helped Solve

## OAuth PKCE Error

Issue:
`Google OAuth Error: (invalid_grant) Missing code verifier`

Solution:
AI suggested storing `flow.code_verifier` inside session and restoring it during callback.

Result:
Google OAuth2 integration started working correctly.

---

## MultipleObjectsReturned Error

Issue:
`get() returned more than one User`

Solution:
AI suggested replacing:

```python
User.objects.get(role="doctor")
```

with a filtered query using a unique field.

---

## Missing Calendar Event IDs

Issue:
Booking model lacked calendar event tracking.

Solution:
AI suggested adding:

- `doctor_calendar_event_id`
- `patient_calendar_event_id`

inside Booking model.

Result:
Google Calendar synchronization became trackable.

---

## Google Calendar Event Sync

Issue:
Confirmed appointments were not appearing in Google Calendar.

Solution:
AI assisted in implementing:
- Google Calendar API integration
- Event creation logic
- Token refresh handling

Result:
Events successfully appeared in calendars.

---

## Race Condition Handling

Issue:
Potential double booking problem.

Solution Discussed:
- Frontend-only validation
- Backend transactional validation

Final Decision:
Backend validation with atomic booking logic.

Reason:
Prevents simultaneous slot booking conflicts.

---

# What Was Manually Verified

The following were manually tested and verified:

- Doctor registration flow
- Patient registration flow
- OTP verification
- Login/logout system
- Slot creation
- Slot editing
- Slot deletion
- Appointment booking
- Appointment confirmation
- Appointment rejection
- Appointment cancellation
- Email notifications
- Google OAuth flow
- Google Calendar synchronization
- PostgreSQL database operations
- Race condition prevention logic
- Dashboard rendering
- Responsive frontend behavior

---

# Important Note

AI-generated suggestions were reviewed, modified, tested, and integrated manually.

The developer fully understood and verified the final implementation before submission.