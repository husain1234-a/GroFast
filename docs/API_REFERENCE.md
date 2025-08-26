# Blinkit Clone - API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

Most endpoints require Firebase authentication. Include the Firebase ID token in requests.

---

## 🔐 Authentication Endpoints

### Verify OTP

**POST** `/auth/verify-otp`

Verify Firebase OTP and create/get user.

**Request Body:**

```json
{
  "firebase_id_token": "string"
}
```

**Response:**

```json
{
  "id": 1,
  "firebase_uid": "firebase_user_id",
  "phone": "+1234567890",
  "email": "user@example.com",
  "name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Google Login

**POST** `/auth/google-login`

Login with Google OAuth token.

**Request Body:**

```json
{
  "google_id_token": "string"
}
```

**Response:** Same as OTP verification

### Get Current User

**GET** `/auth/me?firebase_token=TOKEN`

Get current user information.

### Update User Profile

**PUT** `/auth/me?firebase_token=TOKEN`

**Request Body:**

```json
{
  "name": "Updated Name",
  "address": "New Address",
  "latitude": "28.6139",
  "longitude": "77.2090"
}
```

---

## 🛍️ Product Endpoints

### Get Categories

**GET** `/products/categories`

Get all active product categories.

**Response:**

```json
[
  {
    "id": 1,
    "name": "Fruits & Vegetables",
    "image_url": "https://example.com/image.jpg",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Get Products

**GET** `/products`

**Query Parameters:**

- `category_id` (optional): Filter by category
- `search` (optional): Search products by name
- `limit` (optional, default: 50): Number of products
- `offset` (optional, default: 0): Pagination offset

**Response:**

```json
[
  {
    "id": 1,
    "name": "Fresh Bananas",
    "description": "Fresh yellow bananas",
    "price": 40.0,
    "mrp": 50.0,
    "category_id": 1,
    "image_url": "https://example.com/banana.jpg",
    "stock_quantity": 100,
    "unit": "dozen",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "category": {
      "id": 1,
      "name": "Fruits & Vegetables"
    }
  }
]
```

### Get Product Details

**GET** `/products/{product_id}`

Get detailed information about a specific product.

---

## 🛒 Cart Endpoints

### Get Cart

**GET** `/cart?firebase_token=TOKEN`

Get user's current cart with items and totals.

**Response:**

```json
{
  "id": 1,
  "user_id": 1,
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "quantity": 2,
      "product": {
        "id": 1,
        "name": "Fresh Bananas",
        "price": 40.0
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total_amount": 80.0,
  "total_items": 2,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Add to Cart

**POST** `/cart/add?firebase_token=TOKEN`

**Request Body:**

```json
{
  "product_id": 1,
  "quantity": 2
}
```

### Remove from Cart

**POST** `/cart/remove?firebase_token=TOKEN`

**Request Body:**

```json
{
  "product_id": 1
}
```

### Clear Cart

**DELETE** `/cart/clear?firebase_token=TOKEN`

Remove all items from cart.

---

## 📦 Order Endpoints

### Create Order

**POST** `/orders/create?firebase_token=TOKEN`

Create order from current cart items.

**Request Body:**

```json
{
  "delivery_address": "123 Main St, City, State",
  "delivery_latitude": "28.6139",
  "delivery_longitude": "77.2090"
}
```

**Response:**

```json
{
  "id": 1,
  "user_id": 1,
  "total_amount": 100.0,
  "delivery_fee": 20.0,
  "status": "pending",
  "delivery_address": "123 Main St",
  "estimated_delivery_time": "2024-01-01T01:00:00Z",
  "created_at": "2024-01-01T00:30:00Z",
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "quantity": 2,
      "price": 40.0,
      "product": {
        "name": "Fresh Bananas"
      }
    }
  ]
}
```

### Get User Orders

**GET** `/orders/my-orders?firebase_token=TOKEN`

**Query Parameters:**

- `limit` (optional, default: 20)
- `offset` (optional, default: 0)

### Get Order Details

**GET** `/orders/{order_id}?firebase_token=TOKEN`

### Update Order Status

**PUT** `/orders/{order_id}/status`

**Request Body:**

```json
{
  "status": "confirmed"
}
```

**Order Status Values:**

- `pending`
- `confirmed`
- `preparing`
- `out_for_delivery`
- `delivered`
- `cancelled`

---

## 🚚 Delivery Partner Endpoints

### Get Delivery Partner Info

**GET** `/delivery/me?firebase_token=TOKEN`

### Update Delivery Status

**PUT** `/delivery/status?firebase_token=TOKEN`

**Request Body:**

```json
{
  "status": "available"
}
```

**Status Values:** `available`, `busy`, `offline`

### Update Location

**POST** `/delivery/location?firebase_token=TOKEN`

**Request Body:**

```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "order_id": 1
}
```

### Assign Order

**POST** `/delivery/assign/{order_id}`

**Request Body:**

```json
{
  "partner_id": 1
}
```

### Get Assigned Orders

**GET** `/delivery/orders?firebase_token=TOKEN`

---

## 🔔 Notification Endpoints

### Send FCM Notification

**POST** `/notifications/fcm`

**Request Body:**

```json
{
  "fcm_tokens": ["token1", "token2"],
  "title": "Order Update",
  "body": "Your order is ready!",
  "data": {
    "order_id": "123",
    "type": "order_update"
  }
}
```

---

## 👨‍💼 Admin Endpoints

### Get Dashboard Stats

**GET** `/admin/stats?admin_key=admin123`

**Response:**

```json
{
  "total_users": 150,
  "total_orders": 500,
  "total_revenue": 25000.0,
  "orders_by_status": {
    "pending": 10,
    "confirmed": 5,
    "delivered": 480,
    "cancelled": 5
  }
}
```

### Get All Products

**GET** `/admin/products?admin_key=admin123`

### Create Product

**POST** `/admin/products?admin_key=admin123`

**Request Body:**

```json
{
  "name": "New Product",
  "description": "Product description",
  "price": 99.99,
  "mrp": 120.0,
  "category_id": 1,
  "stock_quantity": 50,
  "unit": "piece"
}
```

### Get All Orders

**GET** `/admin/orders?admin_key=admin123`

**Query Parameters:**

- `status` (optional): Filter by order status
- `limit` (optional, default: 50)
- `offset` (optional, default: 0)

---

## 🏥 Health Check

### Health Status

**GET** `/health`

**Response:**

```json
{
  "status": "healthy",
  "service": "Blinkit Clone"
}
```

---

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message description"
}
```

**Common HTTP Status Codes:**

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error
