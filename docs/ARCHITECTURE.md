# Blinkit Clone - System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile App    │    │   Web App       │    │   Admin Panel   │
│  (React Native)│    │   (React)       │    │   (React)       │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      FastAPI Server       │
                    │    (Python 3.10+)        │
                    └─────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                       │                        │
┌───────▼────────┐    ┌─────────▼─────────┐    ┌─────────▼─────────┐
│   PostgreSQL   │    │      Redis        │    │   Meilisearch     │
│   (Database)   │    │     (Cache)       │    │    (Search)       │
└────────────────┘    └───────────────────┘    └───────────────────┘
```

## 🔧 Technology Stack

### **Backend Core**
- **FastAPI**: Modern, fast web framework for building APIs
- **Python 3.10+**: Programming language
- **Uvicorn**: ASGI server for production
- **Pydantic**: Data validation and serialization

### **Database Layer**
- **PostgreSQL**: Primary database for structured data
- **SQLAlchemy 2.0**: ORM with async support
- **Asyncpg**: Async PostgreSQL driver
- **Alembic**: Database migration tool

### **Caching & Queue**
- **Redis**: Caching and session storage
- **Celery**: Distributed task queue for background jobs

### **Authentication & External Services**
- **Firebase Authentication**: Phone OTP and Google OAuth
- **Firebase Cloud Messaging (FCM)**: Push notifications
- **Supabase Realtime**: Real-time location tracking

### **Search & Storage**
- **Meilisearch**: Full-text search engine
- **Cloudflare R2**: Object storage (S3-compatible)

### **Monitoring & Logging**
- **Loguru**: Structured logging
- **Health checks**: Built-in monitoring endpoints

## 📊 Data Flow Architecture

### **User Authentication Flow**
```
Mobile App → Firebase Auth → FastAPI → PostgreSQL
     ↓
Firebase ID Token → Verify → Create/Get User → JWT Session
```

### **Order Processing Flow**
```
1. Add to Cart → Redis Cache + PostgreSQL
2. Create Order → PostgreSQL + Celery Task
3. Assign Delivery → Update Order + Notify Partner
4. Track Delivery → Supabase Realtime + GPS Updates
5. Complete Order → Update Status + Send Notifications
```

### **Real-time Location Flow**
```
Delivery App → FastAPI → Supabase → WebSocket → Customer App
                    ↓
              PostgreSQL (Backup)
```

## 🗂️ Project Structure

```
blinkit_clone/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config/                 # Configuration management
│   │   ├── settings.py         # Environment variables
│   │   └── database.py         # Database connection
│   ├── routes/                 # API route handlers
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── products.py        # Product management
│   │   ├── cart.py            # Shopping cart
│   │   ├── orders.py          # Order management
│   │   ├── delivery.py        # Delivery partner APIs
│   │   ├── notifications.py   # Push notifications
│   │   └── admin.py           # Admin dashboard
│   ├── models/                # SQLAlchemy database models
│   │   ├── user.py           # User model
│   │   ├── product.py        # Product & Category models
│   │   ├── cart.py           # Cart & CartItem models
│   │   ├── order.py          # Order & OrderItem models
│   │   └── delivery.py       # Delivery partner models
│   ├── schemas/               # Pydantic validation schemas
│   │   ├── user.py           # User request/response schemas
│   │   ├── product.py        # Product schemas
│   │   ├── cart.py           # Cart schemas
│   │   ├── order.py          # Order schemas
│   │   └── delivery.py       # Delivery schemas
│   ├── services/              # Business logic layer
│   │   ├── auth_service.py   # Authentication logic
│   │   ├── cart_service.py   # Cart management
│   │   ├── order_service.py  # Order processing
│   │   └── notification_service.py # Notifications
│   ├── firebase/              # Firebase integration
│   │   ├── config.py         # Firebase initialization
│   │   └── auth.py           # Token verification
│   ├── supabase/              # Supabase integration
│   │   └── client.py         # Realtime client
│   ├── celery_tasks/          # Background tasks
│   │   ├── __init__.py       # Celery app configuration
│   │   └── tasks.py          # Task definitions
│   ├── utils/                 # Utility functions
│   │   ├── location.py       # GPS calculations
│   │   └── logger.py         # Logging setup
│   └── static/                # Static files
├── migrations/                # Database migrations
├── docs/                      # Documentation
├── docker-compose.yml         # Container orchestration
├── Dockerfile                 # Container definition
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables
```

## 🔄 Request Lifecycle

### **1. Request Reception**
```python
# FastAPI receives HTTP request
@router.post("/orders/create")
async def create_order(request: OrderCreate, user_id: int = Depends(get_current_user_id))
```

### **2. Authentication**
```python
# Firebase token verification
async def get_current_user_id(firebase_token: str, db: AsyncSession = Depends(get_db)):
    user = await AuthService.create_or_get_user(db, firebase_token)
    return user.id
```

### **3. Validation**
```python
# Pydantic schema validation
class OrderCreate(BaseModel):
    delivery_address: str
    delivery_latitude: Optional[str] = None
    delivery_longitude: Optional[str] = None
```

### **4. Business Logic**
```python
# Service layer processing
order = await OrderService.create_order(db, user_id, order_data)
```

### **5. Database Operations**
```python
# SQLAlchemy async operations
async with AsyncSessionLocal() as db:
    result = await db.execute(select(Order).where(Order.id == order_id))
```

### **6. Background Tasks**
```python
# Celery task dispatch
send_order_notification.delay([user.fcm_token], order.id, "confirmed")
```

### **7. Response**
```python
# Pydantic response serialization
return OrderResponse.model_validate(order)
```

## 🔐 Security Architecture

### **Authentication Flow**
1. **Client**: Authenticates with Firebase (Phone OTP/Google OAuth)
2. **Firebase**: Returns ID token
3. **Client**: Sends ID token with API requests
4. **FastAPI**: Verifies token with Firebase Admin SDK
5. **FastAPI**: Creates/retrieves user from PostgreSQL

### **Authorization Layers**
- **Public**: Health check, product listing
- **Authenticated**: Cart, orders, user profile
- **Delivery Partner**: Delivery-specific endpoints
- **Admin**: Management endpoints with admin key

### **Security Measures**
- Rate limiting (100 requests/minute per IP)
- CORS protection
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- Environment-based secrets management

## 📈 Scalability Considerations

### **Database Scaling**
- **Read Replicas**: For product catalog queries
- **Connection Pooling**: SQLAlchemy async pool
- **Indexing**: Optimized queries for search and filtering

### **Caching Strategy**
- **Redis**: Session data, cart items, frequent queries
- **Application Cache**: Product categories, static data
- **CDN**: Static assets via Cloudflare

### **Background Processing**
- **Celery Workers**: Horizontal scaling for notifications
- **Task Queues**: Separate queues for different task types
- **Retry Logic**: Automatic retry for failed tasks

### **API Scaling**
- **Async FastAPI**: Non-blocking I/O operations
- **Load Balancing**: Multiple FastAPI instances
- **Container Orchestration**: Docker + Kubernetes ready

## 🔍 Monitoring & Observability

### **Logging Strategy**
```python
# Structured logging with Loguru
logger.info("Order created", order_id=order.id, user_id=user.id, amount=order.total_amount)
```

### **Health Checks**
- **Application**: `/health` endpoint
- **Database**: Connection status
- **Redis**: Cache availability
- **External Services**: Firebase, Supabase status

### **Metrics Collection**
- Request/response times
- Error rates by endpoint
- Database query performance
- Background task success rates

## 🚀 Deployment Architecture

### **Development Environment**
```bash
# Local development with Docker Compose
docker-compose up -d  # PostgreSQL, Redis, Meilisearch
python run_dev.py     # FastAPI with hot reload
celery -A app.celery_tasks worker  # Background tasks
```

### **Production Environment**
```bash
# Container-based deployment
docker build -t blinkit-api .
docker run -p 8000:8000 blinkit-api
```

### **Free Hosting Options**
- **Render.com**: Web service + PostgreSQL + Redis
- **Fly.io**: App hosting + Postgres add-on
- **Railway.app**: Full-stack deployment

### **Environment Configuration**
- **Development**: Local Docker containers
- **Staging**: Cloud services with test data
- **Production**: Managed services with monitoring

This architecture ensures scalability, maintainability, and cost-effectiveness while providing a robust foundation for a q-commerce platform.