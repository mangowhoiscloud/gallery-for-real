CREATE TABLE IF NOT EXISTS employees (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(100)  NOT NULL,
    email       VARCHAR(255)  NOT NULL,
    department  VARCHAR(50)   NOT NULL,
    salary      DECIMAL(10,2) NOT NULL,
    hire_date   DATE          NOT NULL,
    created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT employees_email_uq  UNIQUE (email),
    CONSTRAINT employees_salary_chk CHECK (salary >= 0)
);
