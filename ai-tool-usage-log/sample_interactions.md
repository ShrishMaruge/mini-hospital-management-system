# Sample AI Interactions

---

## Example 1 — OAuth Debugging

### Problem

Google OAuth callback produced:

```text
Google OAuth Error: (invalid_grant) Missing code verifier
```

### AI Suggestion

Store:

```python
flow.code_verifier
```

inside session during OAuth connect step and restore it during callback.

### Result

Google OAuth integration worked successfully.

---

## Example 2 — Google Calendar Sync

### Problem

Appointments were not appearing in Google Calendar.

### AI Suggestion

Add:
- access token handling
- refresh token support
- event creation helper
- attendee support

### Result

Calendar events successfully created for doctors and patients.

---

## Example 3 — Race Condition Prevention

### Problem

Two patients could potentially book the same slot simultaneously.

### AI Discussion

Compared:
- frontend validation
- backend transactional locking

### Final Decision

Backend validation with atomic booking approach.

### Result

Double booking prevention implemented successfully.

---

## Example 4 — PostgreSQL Cleanup

### Problem

Need to reset database for full testing.

### AI Suggestion

Use:

```sql
TRUNCATE TABLE ... RESTART IDENTITY CASCADE;
```

### Result

Database reset successfully for clean testing.