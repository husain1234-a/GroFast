# GroFast - Q-Commerce Platform

Ultra-fast grocery delivery platform built with FastAPI, supporting 30-minute delivery with real-time tracking.

## 🚀 Features

- **User Authentication**: Firebase OTP-based login
- **Product Catalog**: Categories, search, inventory management
- **Shopping Cart**: Add/remove items, real-time totals
- **Order Management**: Create orders, track status, delivery time slots
- **Delivery Partner App**: Accept orders, real-time GPS tracking
- **Real-time Location**: Supabase-powered live tracking
- **Push Notifications**: FCM for order updates
- **Admin Dashboard**: Product/order management, analytics

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL + SQLAlchemy 2.0
- **Cache**: Redis
- **Queue**: Celery
- **Auth**: Firebase Authentication
- **Real-time**: Supabase Realtime
- **Search**: Meilisearch
- **Storage**: Cloudflare R2
- **Notifications**: FCM, Resend

## 📦 Installation

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- Firebase project
- Supabase project

### 1. Clone Repository
```bash
git clone <repository-url>
cd grofast
```

### 2. Environment Setup
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Firebase Setup
- Create Firebase project
- Enable Authentication (Phone)
- Download service account key as `firebase-credentials.json`

### 4. Supabase Setup
- Create Supabase project
- Create `delivery_locations` table:
```sql
CREATE TABLE delivery_locations (
  id SERIAL PRIMARY KEY,
  delivery_partner_id INTEGER NOT NULL,
  order_id INTEGER,
  latitude FLOAT NOT NULL,
  longitude FLOAT NOT NULL,
  timestamp TIMESTAMP DEFAULT NOW()
);
```
- Enable Realtime for the table

### 5. Run with Docker
```bash
docker-compose up -d
```

### 6. Database Migration
```bash
# Install dependencies locally for migration
pip install -r requirements.txt

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

## 🔧 Development Setup

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start services
docker-compose up postgres redis meilisearch -d

# Run FastAPI
uvicorn app.main:app --reload

# Run Celery worker
celery -A app.celery_tasks worker --loglevel=info
```

## 📡 API Endpoints

### Authentication
- `POST /auth/verify-otp` - Verify Firebase OTP
- `GET /auth/me` - Get current user
- `PUT /auth/me` - Update user profile

### Products
- `GET /products/categories` - List categories
- `GET /products` - List products (with search/filter)
- `GET /products/{id}` - Get product details

### Cart
- `GET /cart` - Get user cart
- `POST /cart/add` - Add item to cart
- `POST /cart/remove` - Remove item from cart

### Orders
- `POST /orders/create` - Create order from cart
- `GET /orders/my-orders` - Get user orders
- `GET /orders/{id}` - Get order details
- `PUT /orders/{id}/status` - Update order status

### Delivery
- `GET /delivery/me` - Get delivery partner info
- `PUT /delivery/status` - Update availability status
- `POST /delivery/location` - Update GPS location
- `GET /delivery/orders` - Get assigned orders

### Admin
- `GET /admin/stats` - Dashboard statistics
- `GET /admin/products` - Manage products
- `POST /admin/products` - Create product
- `GET /admin/orders` - View all orders

## 🚀 Deployment

### Free Hosting Options

#### 1. Render.com
```bash
# Connect GitHub repo
# Add environment variables
# Deploy automatically
```

#### 2. Fly.io
```bash
fly launch
fly deploy
```

#### 3. Railway.app
```bash
railway login
railway init
railway up
```

### Environment Variables
Set these in your hosting platform:
- `DATABASE_URL`
- `REDIS_URL`
- `FIREBASE_CREDENTIALS_PATH`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `FCM_SERVER_KEY`
- All other variables from `.env.example`

## 📱 Mobile App Integration

### React Native Setup
```javascript
// Firebase Auth
import auth from '@react-native-firebase/auth';

// Supabase Realtime
import { createClient } from '@supabase/supabase-js';
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// Real-time location tracking
supabase
  .channel('delivery_locations')
  .on('postgres_changes', 
    { event: 'INSERT', schema: 'public', table: 'delivery_locations' },
    (payload) => {
      // Update delivery location on map
    }
  )
  .subscribe();
```

## 🔐 Security Features

- Firebase ID token verification
- Rate limiting (100 req/min per IP)
- CORS protection
- Input validation with Pydantic
- Secure headers middleware
- Environment-based secrets

## 📊 Monitoring & Logging

- **Logging**: Loguru with file rotation
- **Error Tracking**: Sentry integration ready
- **Health Checks**: `/health` endpoint
- **Metrics**: Built-in request logging

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## 📈 Scaling Considerations

- **Database**: PostgreSQL read replicas
- **Cache**: Redis Cluster
- **Queue**: Celery with multiple workers
- **CDN**: Cloudflare for static assets
- **Load Balancer**: Nginx/HAProxy

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- Create GitHub issues for bugs
- Check documentation for setup help
- Join community discussions

---

**Built with ❤️ for ultra-fast grocery delivery**