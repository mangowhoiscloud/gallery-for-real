-- Shop Legacy Schema
-- Compatible with PostgreSQL (prod) and H2 PostgreSQL mode (test)

CREATE TABLE IF NOT EXISTS members (
    id          BIGSERIAL PRIMARY KEY,
    email       VARCHAR(100)  NOT NULL UNIQUE,
    password    VARCHAR(255)  NOT NULL,
    name        VARCHAR(50)   NOT NULL,
    phone       VARCHAR(20),
    address     VARCHAR(200),
    role        VARCHAR(10)   NOT NULL DEFAULT 'USER'
                    CHECK (role IN ('USER', 'ADMIN')),
    created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id             BIGSERIAL PRIMARY KEY,
    name           VARCHAR(100)   NOT NULL,
    description    TEXT,
    price          DECIMAL(10,2)  NOT NULL CHECK (price >= 0),
    stock_quantity INT            NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    category       VARCHAR(50),
    image_url      VARCHAR(255),
    status         VARCHAR(10)    NOT NULL DEFAULT 'ACTIVE'
                       CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS carts (
    id         BIGSERIAL PRIMARY KEY,
    member_id  BIGINT     NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    created_at TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (member_id)
);

CREATE TABLE IF NOT EXISTS cart_items (
    id         BIGSERIAL PRIMARY KEY,
    cart_id    BIGINT     NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    product_id BIGINT     NOT NULL REFERENCES products(id),
    quantity   INT        NOT NULL CHECK (quantity > 0),
    created_at TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (cart_id, product_id)
);

CREATE TABLE IF NOT EXISTS orders (
    id               BIGSERIAL PRIMARY KEY,
    member_id        BIGINT         NOT NULL REFERENCES members(id),
    total_amount     DECIMAL(12,2)  NOT NULL,
    status           VARCHAR(15)    NOT NULL DEFAULT 'PENDING'
                         CHECK (status IN ('PENDING','CONFIRMED','SHIPPED','DELIVERED','CANCELLED')),
    shipping_address VARCHAR(300)   NOT NULL,
    created_at       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id           BIGSERIAL PRIMARY KEY,
    order_id     BIGINT         NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id   BIGINT         REFERENCES products(id),
    product_name VARCHAR(100)   NOT NULL,
    quantity     INT            NOT NULL CHECK (quantity > 0),
    unit_price   DECIMAL(10,2)  NOT NULL
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_products_status    ON products(status);
CREATE INDEX IF NOT EXISTS idx_products_category  ON products(category);
CREATE INDEX IF NOT EXISTS idx_orders_member_id   ON orders(member_id);
CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders(status);
CREATE INDEX IF NOT EXISTS idx_cart_items_cart_id ON cart_items(cart_id);
