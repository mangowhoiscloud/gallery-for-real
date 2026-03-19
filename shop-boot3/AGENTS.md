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
- 4 domain entities: Member, Product, Cart/CartItem, Order/OrderItem
- MyBatis XML mappers (not annotations) in src/main/resources/mapper/
- HTTP Basic Auth (stateless, no JWT) via Spring Security 6.x
- ProblemDetail (RFC 7807) for all error responses
- H2 in-memory DB for tests, PostgreSQL for production
- Java records for all DTOs
- 7 parallel build groups, 14 total items

## Patterns to Follow
- Single source of truth: no adapters, no migrations
- Test-first: write test → implement → verify
- Atomic commits: one logical change per commit

## Anti-Patterns
- Don't duplicate utilities — check shared code first
- Don't modify test assertions to make tests pass
- Don't leave console.log/print debugging statements
