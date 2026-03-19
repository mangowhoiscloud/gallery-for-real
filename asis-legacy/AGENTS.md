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
- Spring 4.3.4 (NOT Boot) — all config is explicit Java @Configuration classes
- MyBatis 3.2.2 — SQL in XML mapper files only, no annotation mapping
- Java 1.8 — no var, records, text blocks, or switch expressions
- JUnit 4 + Mockito — NOT JUnit 5
- javax.validation — NOT jakarta.validation
- H2 in PostgreSQL mode for tests, real PostgreSQL for production
- Stateless HTTP Basic Auth with in-memory users
- Custom exceptions (NotFoundException, DuplicateEmailException, BadRequestException)
- GlobalExceptionHandler returns ErrorResponse JSON for all error cases

## Patterns to Follow
- Single source of truth: no adapters, no migrations
- Test-first: write test → implement → verify
- Atomic commits: one logical change per commit

## Anti-Patterns
- Don't duplicate utilities — check shared code first
- Don't modify test assertions to make tests pass
- Don't leave console.log/print debugging statements
