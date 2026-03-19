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
- Package: com.example.shop (config, domain, mapper, service, controller, dto, exception)
- Spring 4.3.4 Java @Configuration (no XML, no Boot)
- MyBatis XML mappers in src/main/resources/mapper/
- Schema: schema.sql + data.sql in src/main/resources/
- Static pages: src/main/webapp/static/ (HTML/CSS/JS)
- Tests: H2 in-memory, JUnit 4, MockMvc for controllers
- Security: HTTP Basic, BCrypt, stateless, CSRF disabled
- SELECT FOR UPDATE on product stock during order creation

## Patterns to Follow
- Single source of truth: no adapters, no migrations
- Test-first: write test → implement → verify
- Atomic commits: one logical change per commit

## Anti-Patterns
- Don't duplicate utilities — check shared code first
- Don't modify test assertions to make tests pass
- Don't leave console.log/print debugging statements
