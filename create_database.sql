-- GroFast Database Schema
-- Run this in PostgreSQL to create all required tables

-- Create database (run this first as superuser)
CREATE DATABASE grofast_db;

-- Connect to grofast_db and run the following:

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    firebase_uid VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    name VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    fcm_token VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    discount_percentage DECIMAL(5, 2) DEFAULT 0,
    stock_quantity INTEGER DEFAULT 0,
    unit VARCHAR(50) NOT NULL,
    image_url VARCHAR(500),
    category_id INTEGER REFERENCES categories (id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Carts table
CREATE TABLE IF NOT EXISTS carts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users (id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id)
);

-- Cart items table
CREATE TABLE IF NOT EXISTS cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER REFERENCES carts (id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products (id),
    quantity INTEGER NOT NULL DEFAULT 1,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (cart_id, product_id)
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users (id),
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2) NOT NULL,
    delivery_address TEXT NOT NULL,
    delivery_time_slot VARCHAR(100),
    payment_method VARCHAR(50) DEFAULT 'cash_on_delivery',
    notes TEXT,
    delivery_partner_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders (id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products (id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Delivery partners table
CREATE TABLE IF NOT EXISTS delivery_partners (
    id SERIAL PRIMARY KEY,
    firebase_uid VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'available',
    current_latitude VARCHAR(20),
    current_longitude VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Delivery locations table (for real-time tracking)
CREATE TABLE IF NOT EXISTS delivery_locations (
    id SERIAL PRIMARY KEY,
    delivery_partner_id INTEGER REFERENCES delivery_partners (id),
    order_id INTEGER REFERENCES orders (id),
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key for delivery partner in orders
ALTER TABLE orders
ADD CONSTRAINT fk_orders_delivery_partner FOREIGN KEY (delivery_partner_id) REFERENCES delivery_partners (id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category_id);

CREATE INDEX IF NOT EXISTS idx_products_active ON products (is_active);

CREATE INDEX IF NOT EXISTS idx_cart_items_cart ON cart_items (cart_id);

CREATE INDEX IF NOT EXISTS idx_cart_items_product ON cart_items (product_id);

CREATE INDEX IF NOT EXISTS idx_orders_user ON orders (user_id);

CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);

CREATE INDEX IF NOT EXISTS idx_orders_delivery_partner ON orders (delivery_partner_id);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items (order_id);

CREATE INDEX IF NOT EXISTS idx_delivery_locations_partner ON delivery_locations (delivery_partner_id);

CREATE INDEX IF NOT EXISTS idx_delivery_locations_order ON delivery_locations (order_id);

CREATE INDEX IF NOT EXISTS idx_users_firebase_uid ON users (firebase_uid);

CREATE INDEX IF NOT EXISTS idx_delivery_partners_firebase_uid ON delivery_partners (firebase_uid);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_carts_updated_at BEFORE UPDATE ON carts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cart_items_updated_at BEFORE UPDATE ON cart_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_delivery_partners_updated_at BEFORE UPDATE ON delivery_partners FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default data
INSERT INTO
    categories (name, description, image_url)
VALUES (
        'Fruits & Vegetables',
        'Fresh fruits and vegetables',
        'https://grofast-assets.your-domain.com/categories/fruits.jpg'
    ),
    (
        'Dairy & Bakery',
        'Milk, bread, and bakery items',
        'https://grofast-assets.your-domain.com/categories/dairy.jpg'
    ),
    (
        'Snacks & Beverages',
        'Chips, drinks, and snacks',
        'https://grofast-assets.your-domain.com/categories/snacks.jpg'
    ),
    (
        'Personal Care',
        'Health and beauty products',
        'https://grofast-assets.your-domain.com/categories/personal.jpg'
    ),
    (
        'Household Items',
        'Cleaning and home essentials',
        'https://grofast-assets.your-domain.com/categories/household.jpg'
    )
ON CONFLICT (name) DO NOTHING;

-- Alter existing users table to minimal structure
-- Run these commands in your PostgreSQL database

-- Drop columns we don't need (Firebase Auth handles these)
ALTER TABLE users DROP COLUMN IF EXISTS email;

ALTER TABLE users DROP COLUMN IF EXISTS name;

ALTER TABLE users DROP COLUMN IF EXISTS phone;

-- Rename address to default_address for clarity
ALTER TABLE users RENAME COLUMN address TO default_address;

-- Add comment to clarify purpose
COMMENT ON TABLE users IS 'Minimal user business data - Firebase Auth handles authentication';

COMMENT ON COLUMN users.firebase_uid IS 'Links to Firebase Auth user';

COMMENT ON COLUMN users.fcm_token IS 'For push notifications';

COMMENT ON COLUMN users.default_address IS 'Default delivery address for quick checkout';