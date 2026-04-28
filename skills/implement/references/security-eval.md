# Security Eval

LLM-based review of auth and middleware code changes. Run by the orchestrator (you) on the diff — not a separate agent. Standard tier only.

## When to Run

- New or modified auth endpoints (login, signup, reset, session management)
- Changes to middleware, proxy, or route guards
- New permission checks or role gating
- Token generation or validation code
- Any code handling passwords, secrets, or PII

Do NOT run for: CRUD endpoints, UI components, config changes, documentation.

## How to Run

1. Get the diff for auth-relevant files:
   ```bash
   git diff main -- '**/auth/**' '**/middleware*' '**/proxy*' '**/session*' '**/guard*'
   ```

2. Review the diff against this checklist. For each item, emit PASS or FAIL:

### Checklist

| # | Check | What to look for |
|---|-------|-----------------|
| S1 | Session validation | Every protected endpoint checks session/token before acting |
| S2 | No information leaks | Error messages don't reveal whether an email exists, account status, or internal state. Generic errors for auth failures. |
| S3 | Parameterized queries | No string concatenation in SQL. All queries use parameterized bindings. |
| S4 | Password handling | Hashed with argon2id (not bcrypt/md5). Min length enforced. No plaintext logging. |
| S5 | Cookie security | httpOnly, secure (in prod), sameSite=lax or strict, scoped path |
| S6 | Rate limiting | Auth endpoints (login, reset, signup) have rate limits |
| S7 | CSRF protection | State-changing endpoints validate origin or use CSRF tokens |
| S8 | Token expiry | Auth tokens have explicit expiration. Signup tokens != reset tokens in TTL. |
| S9 | Session invalidation | Password change/reset invalidates all existing sessions |
| S10 | Public path exposure | Only intentionally public paths bypass auth. Check PUBLIC_PATHS array. |

## Output Format

```
Security eval — {files reviewed}
S1 PASS: all protected routes call requireUser()
S2 FAIL: login returns "account not activated" for unset passwords — leaks email existence
S3 PASS: all queries use drizzle ORM (parameterized)
...
Result: 1 FAIL (S2) — low severity, info leak on invite-only portal. Track as PIC or fix now.
```

## Severity Guide

- **Block deploy:** S1 (missing auth), S3 (SQL injection), S4 (plaintext passwords)
- **Fix before next phase:** S5 (cookie flags), S9 (session invalidation), S10 (public path leak)
- **Track as PIC:** S2 (minor info leak), S6 (missing rate limit on low-traffic endpoint), S7 (CSRF on read-only)
