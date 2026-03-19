# Project Rules

## Build & Test
Commands are defined in `.harness-config`. Run `cat .harness-config` to see current settings.

## Conventions
- Read AGENTS.md for operational guide
- Read IMPLEMENTATION_PLAN.md for current task state
- Read progress.txt for recent session context
- Read CLARITY_LOG.md for resolved ambiguities from Socratic phase

## Rules
- ONE task per session. Pick the highest-priority TODO from IMPLEMENTATION_PLAN.md
- Search before assuming something isn't implemented
- Write tests alongside implementation. Target: 70% test code
- Capture the WHY in commit messages, not just the what
- Keep AGENTS.md under 60 lines. State goes in IMPLEMENTATION_PLAN.md
- Implement completely. No placeholders, no stubs, no TODOs in code
- If unrelated tests fail, fix them in this session

## Stack-Specific Rules
- Java 1.8 — no var, no records, no text blocks, no switch expressions
- Spring Framework 4.3.4 — NOT Spring Boot. All configuration is explicit Java/XML config
- MyBatis 3.2.2 — SQL in XML mapper files only, no annotation-based mapping
- javax.validation — NOT jakarta.validation
- JUnit 4 — @Test from org.junit, NOT org.junit.jupiter
- Tests use H2 in-memory DB (test profile), NOT PostgreSQL

## Backpressure
All must pass before committing:
1. `mvn compile` succeeds
2. `mvn test` — all tests pass
3. No `@Ignore` or `@Disabled` tests unless documented in IMPLEMENTATION_PLAN.md
