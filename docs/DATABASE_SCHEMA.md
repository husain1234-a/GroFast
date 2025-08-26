# Blinkit Clone - Database Schema Documentation

## 📊 Database Overview

The Blinkit Clone uses **PostgreSQL** as the primary database with **SQLAlchemy 2.0** as the ORM. The schema is designed for a q-commerce platform supporting users, products, orders, and delivery management.

---

## 🗂️ Entity Relationship Diagram

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Users    │    │ Categories  │    │  Products   │
│             │    │             │    │             │
│ id (PK)     │    │ id (PK)     │    │ id (PK)     │
│ firebase_uid│    │ name        │    │ name        │
│ phone       │    │ image_url   │    │ price       │
│ email       │    │ is_active   │    │ category_id │
│ name        │    │ created_at  │    │ stock_qty   │
│ address     │    └─────────────┘    │ is_active   │
│ latitude    │           │           │ created_at  │
│ longitude   │           │           └─────────────┘
│ fcm_token   │           │                  │
│ is_active   │           └──────────────────┘
│ created_at  │
└─────────────┘
       │
       │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Carts    │    │ Cart Items  │    │   Orders    │
│             │    │             │    │             │
│ id (PK)     │    │ id (PK)     │    │ id (PK)     │
│ user_id (FK)│────│ cart_id (FK)│    │ user_id (FK)│
│ created_at  │    │ product_id  │    │ delivery_id │
│ updated_at  │    │ quantity    │    │ total_amount│
└─────────────┘    │ created_at  │    │ status      │
                   └─────────────┘    │ address     │
                                      │ latitude    │
                                      │ longitude   │
                                      │ created_at  │
                                      └─────────────┘
                                             │
                                             │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Order Items  │    │ Delivery    │    │ Delivery    │
│             │    │ Partners    │    │ Locations   │
│ id (PK)     │    │             │    │             │
│ order_id(FK)│────│ id (PK)     │    │ id (PK)     │
│ product_id  │    │ firebase_uid│    │ partner_id  │
│ quantity    │    │ name        │    │ order_id    │
│ price       │    │ phone       │    │ latitude    │
│ created_at  │    │ status      │    │ longitude   │
└─────────────┘    │ latitude    │    │ timestamp   │
                   │ longitude   │    └─────────────┘
                   │ is_active   │
                   │ created_at  │
                   └─────────────┘
```

---

## 📋 Table Definitions

### **Users Table**
Stores customer and user information with Firebase integration.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE,
    email VARCHAR(255) UNIQUE,
    name VARCHAR(100),
    fcm_token TEXT,
    address TEXT,
    latitude VARCHAR(20),
    longitude VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_users_firebase_uid ON users(firebase_uid);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_email ON users(email);
```

**Fields:**
- `id`: Primary key, auto-increment
- `firebase_uid`: Unique Firebase user identifier
- `phone`: User's phone number (for OTP login)
- `email`: User's email address
- `name`: User's display name
- `fcm_token`: Firebase Cloud Messaging token for push notifications
- `address`: Delivery address
- `latitude/longitude`: GPS coordinates for delivery
- `is_active`: Account status flag
- `created_at/updated_at`: Timestamps

### **Categories Table**
Product categories for organizing the catalog.

```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_categories_active ON categories(is_active);
```

**Fields:**
- `id`: Primary key
- `name`: Category name (e.g., "Fruits & Vegetables")
- `image_url`: Category display image
- `is_active`: Visibility flag
- `created_at`: Creation timestamp

### **Products Table**
Product catalog with pricing and inventory.

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    mrp DECIMAL(10,2),
    category_id INTEGER REFERENCES categories(id),
    image_url VARCHAR(500),
    stock_quantity INTEGER DEFAULT 0,
    unit VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_price ON products(price);
```

**Fields:**
- `id`: Primary key
- `name`: Product name
- `description`: Product description
- `price`: Selling price
- `mrp`: Maximum retail price
- `category_id`: Foreign key to categories
- `image_url`: Product image
- `stock_quantity`: Available inventory
- `unit`: Unit of measurement (kg, piece, liter)
- `is_active`: Product availability
- `created_at/updated_at`: Timestamps

### **Carts Table**
Shopping carts for users.

```sql
CREATE TABLE carts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_carts_user ON carts(user_id);
```

**Fields:**
- `id`: Primary key
- `user_id`: Foreign key to users
- `created_at/updated_at`: Timestamps

### **Cart Items Table**
Items within shopping carts.

```sql
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER REFERENCES carts(id) NOT NULL,
    product_id INTEGER REFERENCES products(id) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_cart_product UNIQUE(cart_id, product_id)
);

-- Indexes
CREATE INDEX idx_cart_items_cart ON cart_items(cart_id);
CREATE INDEX idx_cart_items_product ON cart_items(product_id);
```

**Fields:**
- `id`: Primary key
- `cart_id`: Foreign key to carts
- `product_id`: Foreign key to products
- `quantity`: Number of items
- `created_at/updated_at`: Timestamps
- **Constraint**: Unique cart-product combination

### **Orders Table**
Customer orders with delivery information.

```sql
CREATE TYPE order_status AS ENUM (
    'pending',
    'confirmed', 
    'preparing',
    'out_for_delivery',
    'delivered',
    'cancelled'
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    delivery_partner_id INTEGER REFERENCES delivery_partners(id),
    total_amount DECIMAL(10,2) NOT NULL,
    delivery_fee DECIMAL(10,2) DEFAULT 0,
    status order_status DEFAULT 'pending',
    delivery_address TEXT NOT NULL,
    delivery_latitude VARCHAR(20),
    delivery_longitude VARCHAR(20),
    estimated_delivery_time TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_delivery_partner ON orders(delivery_partner_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
```

**Fields:**
- `id`: Primary key
- `user_id`: Foreign key to users
- `delivery_partner_id`: Foreign key to delivery partners
- `total_amount`: Order total
- `delivery_fee`: Delivery charges
- `status`: Order status enum
- `delivery_address`: Delivery location
- `delivery_latitude/longitude`: GPS coordinates
- `estimated_delivery_time`: Expected delivery
- `delivered_at`: Actual delivery time
- `created_at/updated_at`: Timestamps

### **Order Items Table**
Items within orders with pricing snapshot.

```sql
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) NOT NULL,
    product_id INTEGER REFERENCES products(id) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
```

**Fields:**
- `id`: Primary key
- `order_id`: Foreign key to orders
- `product_id`: Foreign key to products
- `quantity`: Number of items ordered
- `price`: Price at time of order (historical pricing)
- `created_at`: Timestamp

### **Delivery Partners Table**
Delivery personnel information.

```sql
CREATE TYPE delivery_status AS ENUM (
    'available',
    'busy', 
    'offline'
);

CREATE TABLE delivery_partners (
    id SERIAL PRIMARY KEY,
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(255),
    fcm_token VARCHAR(500),
    status delivery_status DEFAULT 'offline',
    current_latitude VARCHAR(20),
    current_longitude VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_delivery_partners_firebase_uid ON delivery_partners(firebase_uid);
CREATE INDEX idx_delivery_partners_status ON delivery_partners(status);
CREATE INDEX idx_delivery_partners_phone ON delivery_partners(phone);
```

**Fields:**
- `id`: Primary key
- `firebase_uid`: Firebase authentication ID
- `name`: Partner's name
- `phone`: Contact number
- `email`: Email address
- `fcm_token`: Push notification token
- `status`: Availability status
- `current_latitude/longitude`: Current GPS location
- `is_active`: Account status
- `created_at/updated_at`: Timestamps

### **Delivery Locations Table**
Real-time location tracking for deliveries.

```sql
CREATE TABLE delivery_locations (
    id SERIAL PRIMARY KEY,
    delivery_partner_id INTEGER REFERENCES delivery_partners(id) NOT NULL,
    order_id INTEGER REFERENCES orders(id),
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_delivery_locations_partner ON delivery_locations(delivery_partner_id);
CREATE INDEX idx_delivery_locations_order ON delivery_locations(order_id);
CREATE INDEX idx_delivery_locations_timestamp ON delivery_locations(timestamp);
```

**Fields:**
- `id`: Primary key
- `delivery_partner_id`: Foreign key to delivery partners
- `order_id`: Associated order (optional)
- `latitude/longitude`: GPS coordinates (high precision)
- `timestamp`: Location update time

---

## 🔗 Relationships

### **One-to-Many Relationships**
- **Users → Carts**: One user can have one active cart
- **Users → Orders**: One user can have multiple orders
- **Categories → Products**: One category contains multiple products
- **Carts → Cart Items**: One cart contains multiple items
- **Orders → Order Items**: One order contains multiple items
- **Delivery Partners → Orders**: One partner can handle multiple orders
- **Delivery Partners → Delivery Locations**: One partner has multiple location updates

### **Many-to-One Relationships**
- **Products → Categories**: Many products belong to one category
- **Cart Items → Products**: Many cart items reference one product
- **Order Items → Products**: Many order items reference one product
- **Orders → Delivery Partners**: Many orders can be assigned to one partner

### **Foreign Key Constraints**
```sql
-- User relationships
ALTER TABLE carts ADD CONSTRAINT fk_carts_user 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE orders ADD CONSTRAINT fk_orders_user 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Product relationships
ALTER TABLE products ADD CONSTRAINT fk_products_category 
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL;

ALTER TABLE cart_items ADD CONSTRAINT fk_cart_items_product 
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;

ALTER TABLE order_items ADD CONSTRAINT fk_order_items_product 
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT;

-- Cart relationships
ALTER TABLE cart_items ADD CONSTRAINT fk_cart_items_cart 
    FOREIGN KEY (cart_id) REFERENCES carts(id) ON DELETE CASCADE;

-- Order relationships
ALTER TABLE order_items ADD CONSTRAINT fk_order_items_order 
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;

ALTER TABLE orders ADD CONSTRAINT fk_orders_delivery_partner 
    FOREIGN KEY (delivery_partner_id) REFERENCES delivery_partners(id) ON DELETE SET NULL;

-- Delivery relationships
ALTER TABLE delivery_locations ADD CONSTRAINT fk_delivery_locations_partner 
    FOREIGN KEY (delivery_partner_id) REFERENCES delivery_partners(id) ON DELETE CASCADE;

ALTER TABLE delivery_locations ADD CONSTRAINT fk_delivery_locations_order 
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL;
```

---

## 📊 Sample Data

### **Categories**
```sql
INSERT INTO categories (name, image_url) VALUES
('Fruits & Vegetables', 'https://example.com/fruits.jpg'),
('Dairy & Bakery', 'https://example.com/dairy.jpg'),
('Snacks & Beverages', 'https://example.com/snacks.jpg'),
('Personal Care', 'https://example.com/care.jpg'),
('Household Items', 'https://example.com/household.jpg');
```

### **Products**
```sql
INSERT INTO products (name, description, price, mrp, category_id, stock_quantity, unit) VALUES
('Fresh Bananas', 'Fresh yellow bananas', 40.00, 50.00, 1, 100, 'dozen'),
('Red Apples', 'Crispy red apples', 120.00, 150.00, 1, 50, 'kg'),
('Milk (1L)', 'Fresh cow milk', 60.00, 65.00, 2, 80, 'liter'),
('Bread', 'White bread loaf', 25.00, 30.00, 2, 40, 'piece'),
('Coca Cola', 'Cold drink 500ml', 40.00, 45.00, 3, 100, 'piece');
```

### **Users**
```sql
INSERT INTO users (firebase_uid, phone, email, name, address) VALUES
('firebase_uid_1', '+919876543210', 'john@example.com', 'John Doe', '123 Main St, Delhi'),
('firebase_uid_2', '+919876543211', 'jane@example.com', 'Jane Smith', '456 Oak Ave, Mumbai');
```

### **Delivery Partners**
```sql
INSERT INTO delivery_partners (firebase_uid, name, phone, email, status) VALUES
('delivery_uid_1', 'Rahul Kumar', '+919876543220', 'rahul@delivery.com', 'available'),
('delivery_uid_2', 'Amit Singh', '+919876543221', 'amit@delivery.com', 'available');
```

---

## 🔍 Common Queries

### **Product Queries**
```sql
-- Get products by category
SELECT p.*, c.name as category_name 
FROM products p 
JOIN categories c ON p.category_id = c.id 
WHERE c.id = 1 AND p.is_active = true;

-- Search products
SELECT * FROM products 
WHERE name ILIKE '%banana%' AND is_active = true 
ORDER BY name;

-- Get low stock products
SELECT * FROM products 
WHERE stock_quantity < 10 AND is_active = true 
ORDER BY stock_quantity;
```

### **Order Queries**
```sql
-- Get user's recent orders
SELECT o.*, COUNT(oi.id) as item_count
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
WHERE o.user_id = 1
GROUP BY o.id
ORDER BY o.created_at DESC
LIMIT 10;

-- Get orders by status
SELECT o.*, u.name as user_name, dp.name as delivery_partner_name
FROM orders o
JOIN users u ON o.user_id = u.id
LEFT JOIN delivery_partners dp ON o.delivery_partner_id = dp.id
WHERE o.status = 'out_for_delivery';

-- Daily order statistics
SELECT 
    DATE(created_at) as order_date,
    COUNT(*) as total_orders,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_order_value
FROM orders 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY order_date DESC;
```

### **Cart Queries**
```sql
-- Get user's cart with items
SELECT 
    c.id as cart_id,
    ci.quantity,
    p.name as product_name,
    p.price,
    (ci.quantity * p.price) as item_total
FROM carts c
JOIN cart_items ci ON c.id = ci.cart_id
JOIN products p ON ci.product_id = p.id
WHERE c.user_id = 1;

-- Cart summary
SELECT 
    c.user_id,
    COUNT(ci.id) as total_items,
    SUM(ci.quantity * p.price) as cart_total
FROM carts c
JOIN cart_items ci ON c.id = ci.cart_id
JOIN products p ON ci.product_id = p.id
WHERE c.user_id = 1
GROUP BY c.user_id;
```

### **Delivery Queries**
```sql
-- Get available delivery partners
SELECT * FROM delivery_partners 
WHERE status = 'available' AND is_active = true;

-- Get delivery partner's current orders
SELECT o.*, u.name as customer_name, u.phone as customer_phone
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.delivery_partner_id = 1 
AND o.status IN ('preparing', 'out_for_delivery');

-- Get recent location updates
SELECT 
    dl.*,
    dp.name as partner_name,
    o.id as order_id
FROM delivery_locations dl
JOIN delivery_partners dp ON dl.delivery_partner_id = dp.id
LEFT JOIN orders o ON dl.order_id = o.id
WHERE dl.timestamp >= NOW() - INTERVAL '1 hour'
ORDER BY dl.timestamp DESC;
```

---

## 🔧 Database Maintenance

### **Performance Optimization**
```sql
-- Analyze table statistics
ANALYZE users;
ANALYZE products;
ANALYZE orders;

-- Vacuum tables to reclaim space
VACUUM ANALYZE products;
VACUUM ANALYZE orders;

-- Reindex for better performance
REINDEX INDEX idx_products_category;
REINDEX INDEX idx_orders_user_status;
```

### **Backup Strategy**
```bash
# Daily backup
pg_dump -h localhost -U postgres -d blinkit_db > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h localhost -U postgres -d blinkit_db < backup_20240101.sql
```

### **Monitoring Queries**
```sql
-- Check database size
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

---

## 🚀 Migration Scripts

### **Initial Migration**
```python
# migrations/versions/001_initial_migration.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('firebase_uid', sa.String(128), nullable=False),
        sa.Column('phone', sa.String(15), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('fcm_token', sa.Text(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('latitude', sa.String(20), nullable=True),
        sa.Column('longitude', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_firebase_uid', 'users', ['firebase_uid'], unique=True)
    
    # Create other tables...

def downgrade():
    op.drop_table('users')
    # Drop other tables...
```

This comprehensive database schema provides a solid foundation for the Blinkit Clone q-commerce platform, supporting all core features while maintaining data integrity and performance.