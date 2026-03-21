# Shop — Spring Boot 3 Shopping Mall

A REST API + frontend shopping mall built with Spring Boot 3, MyBatis, and Spring Security.

## Prerequisites

- Java 21
- PostgreSQL 12+ (or use the embedded H2 profile for quick demo)

## Quick Start

### Option A: With PostgreSQL

1. Create a database:
   ```sql
   CREATE DATABASE shopdb;
   CREATE USER shop WITH PASSWORD 'shop';
   GRANT ALL PRIVILEGES ON DATABASE shopdb TO shop;
   ```

2. Run the application:
   ```bash
   ./mvnw spring-boot:run
   ```

   Tables are created automatically on first run via `schema.sql`.

### Option B: Without PostgreSQL (H2 in-memory)

```bash
./mvnw spring-boot:run -Dspring-boot.run.profiles=test
```

This uses H2 in-memory — data resets on restart.

## Access

- Frontend: http://localhost:8080
- API Base: http://localhost:8080/api

### Default Admin Account

- Email: `admin@shop.com`
- Password: `admin1234`

## Build & Test

```bash
./mvnw compile        # Compile
./mvnw test           # Run all tests (106 tests, H2 in-memory)
./mvnw package        # Build executable JAR
java -jar target/shop-1.0.0-SNAPSHOT.jar
```

## Tech Stack

- Java 21, Spring Boot 3.3.7
- Spring Security 6 (HTTP Basic Auth, stateless)
- MyBatis 3.0.4 (XML mappers)
- PostgreSQL (production) / H2 (test)
- Static HTML + vanilla JS frontend
