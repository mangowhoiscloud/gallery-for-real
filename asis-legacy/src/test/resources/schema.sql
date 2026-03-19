-- H2-compatible DDL for employees table (test profile)
-- Uses BIGINT AUTO_INCREMENT instead of PostgreSQL BIGSERIAL
DROP TABLE IF EXISTS employees;
CREATE TABLE employees (
    id          BIGINT         AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)   NOT NULL,
    email       VARCHAR(255)   NOT NULL UNIQUE,
    department  VARCHAR(50)    NOT NULL,
    salary      DECIMAL(19,2)  NOT NULL CHECK (salary >= 0),
    hire_date   DATE           NOT NULL,
    created_at  TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);
