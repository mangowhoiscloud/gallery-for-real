# Operational Guide

## How to Run
```bash
# Build
mvn compile

# Run tests
mvn test

# Lint
mvn checkstyle:check 2>/dev/null || true

# Typecheck
mvn compile
```

## Project Type
java-maven (package manager: mvn)

## Architecture Decisions
- Employee is a mutable class (MyBatis useGeneratedKeys needs id mutation); DTOs are records
- Timestamps managed at service layer, not DB defaults
- MyBatis: 7 annotated methods (simple CRUD) + 2 XML methods (search with dynamic SQL)
- HTTP Basic Auth, stateless, CSRF disabled, role hierarchy ADMIN > USER
- ProblemDetail (RFC 7807) for all error responses
- H2 with MODE=PostgreSQL for tests; SQL-standard DDL for cross-DB compat

## Patterns to Follow
- Single source of truth: no adapters, no migrations
- Test-first: write test → implement → verify
- Atomic commits: one logical change per commit

## Anti-Patterns
- Don't duplicate utilities — check shared code first
- Don't modify test assertions to make tests pass
- Don't leave console.log/print debugging statements
