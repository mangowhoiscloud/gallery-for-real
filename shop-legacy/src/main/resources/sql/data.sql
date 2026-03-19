-- Seed data for shop-legacy
-- Admin account: admin@example.com / admin1234
-- BCrypt hash (cost 10) of "admin1234"
INSERT INTO members (email, password, name, role)
VALUES (
    'admin@example.com',
    '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy',
    'Admin',
    'ADMIN'
);
