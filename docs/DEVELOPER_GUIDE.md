# Blinkit Clone - Developer Guide

## 🚀 Welcome Developers!

This guide will help you understand, contribute to, and extend the Blinkit Clone codebase.

---

## 🏗️ Architecture Overview

### **Tech Stack**
- **Backend**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Cache**: Redis for sessions and caching
- **Queue**: Celery for background tasks
- **Auth**: Firebase Authentication
- **Real-time**: Supabase for live location tracking
- **Search**: Meilisearch for product search
- **Storage**: Cloudflare R2 for file storage

### **Design Patterns**
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic separation
- **Dependency Injection**: FastAPI's dependency system
- **Event-Driven**: Celery tasks for async operations
- **RESTful API**: Standard HTTP methods and status codes

---

## 📁 Code Structure

### **Directory Layout**
```
app/
├── main.py                 # FastAPI application entry
├── config/                 # Configuration management
├── routes/                 # API endpoint handlers
├── models/                 # Database models (SQLAlchemy)
├── schemas/                # Request/response models (Pydantic)
├── services/               # Business logic layer
├── firebase/               # Firebase integration
├── supabase/               # Supabase integration
├── celery_tasks/           # Background tasks
├── utils/                  # Utility functions
└── static/                 # Static files
```

### **Layer Responsibilities**

#### **Routes Layer** (`app/routes/`)
- Handle HTTP requests/responses
- Input validation via Pydantic
- Authentication and authorization
- Call service layer for business logic

```python
@router.post("/orders/create", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    order = await OrderService.create_order(db, user_id, order_data)
    return OrderResponse.model_validate(order)
```

#### **Services Layer** (`app/services/`)
- Business logic implementation
- Data transformation
- External service integration
- Transaction management

```python
class OrderService:
    @staticmethod
    async def create_order(db: AsyncSession, user_id: int, order_data: OrderCreate) -> Order:
        # Business logic here
        async with db.begin():
            order = Order(...)
            db.add(order)
            await db.flush()
            # More business logic
            return order
```

#### **Models Layer** (`app/models/`)
- Database schema definition
- Relationships between entities
- Database constraints

```python
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    
    items = relationship("OrderItem", back_populates="order")
```

#### **Schemas Layer** (`app/schemas/`)
- API request/response validation
- Data serialization/deserialization
- Type safety

```python
class OrderCreate(BaseModel):
    delivery_address: str
    delivery_latitude: Optional[str] = None
    delivery_longitude: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    status: OrderStatus
    total_amount: float
    items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True
```

---

## 🔧 Development Workflow

### **Setting Up Development Environment**

#### 1. **Clone and Setup**
```bash
git clone <repository-url>
cd blinkit_clone
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-minimal.txt
```

#### 2. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

#### 3. **Start Services**
```bash
# Start databases
docker-compose up -d postgres redis meilisearch

# Run migrations
alembic upgrade head

# Initialize sample data
python init_data.py
```

#### 4. **Run Application**
```bash
# Terminal 1: FastAPI server
python run_dev.py

# Terminal 2: Celery worker
celery -A app.celery_tasks worker --loglevel=info
```

### **Development Tools**

#### **Code Quality**
```bash
# Install development dependencies
pip install black isort flake8 mypy pytest

# Format code
black app/
isort app/

# Lint code
flake8 app/
mypy app/

# Run tests
pytest
```

#### **Database Management**
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

---

## 🧪 Testing

### **Test Structure**
```
tests/
├── conftest.py             # Test configuration
├── test_auth.py            # Authentication tests
├── test_products.py        # Product API tests
├── test_cart.py            # Cart functionality tests
├── test_orders.py          # Order processing tests
└── test_delivery.py        # Delivery partner tests
```

### **Writing Tests**

#### **API Tests**
```python
# tests/test_products.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_products():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/products")
    assert response.status_code == 200
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_create_product():
    product_data = {
        "name": "Test Product",
        "price": 99.99,
        "category_id": 1,
        "stock_quantity": 10
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/admin/products?admin_key=admin123", json=product_data)
    assert response.status_code == 201
```

#### **Service Tests**
```python
# tests/test_services.py
import pytest
from app.services.cart_service import CartService
from app.models.user import User
from app.models.product import Product

@pytest.mark.asyncio
async def test_add_to_cart(db_session):
    user = User(firebase_uid="test_uid", name="Test User")
    product = Product(name="Test Product", price=10.0, category_id=1)
    
    db_session.add_all([user, product])
    await db_session.commit()
    
    cart = await CartService.add_to_cart(db_session, user.id, product.id, 2)
    assert cart.total_items == 2
    assert cart.total_amount == 20.0
```

### **Test Configuration**
```python
# conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.config.database import Base

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
```

---

## 🔌 Adding New Features

### **1. Adding a New API Endpoint**

#### Step 1: Define Schema
```python
# app/schemas/reviews.py
class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### Step 2: Create Model
```python
# app/models/review.py
class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    product = relationship("Product")
    user = relationship("User")
```

#### Step 3: Create Service
```python
# app/services/review_service.py
class ReviewService:
    @staticmethod
    async def create_review(db: AsyncSession, user_id: int, review_data: ReviewCreate) -> Review:
        review = Review(
            user_id=user_id,
            **review_data.model_dump()
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review
```

#### Step 4: Create Route
```python
# app/routes/reviews.py
@router.post("/reviews", response_model=ReviewResponse)
async def create_review(
    review_data: ReviewCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    review = await ReviewService.create_review(db, user_id, review_data)
    return ReviewResponse.model_validate(review)
```

#### Step 5: Register Route
```python
# app/main.py
from .routes import reviews

app.include_router(reviews.router)
```

### **2. Adding Background Tasks**

```python
# app/celery_tasks/tasks.py
@celery_app.task
def send_review_notification(product_id: int, rating: int):
    """Notify product owner of new review"""
    # Implementation here
    pass

# In your route
@router.post("/reviews")
async def create_review(...):
    review = await ReviewService.create_review(...)
    
    # Trigger background task
    send_review_notification.delay(review.product_id, review.rating)
    
    return review
```

### **3. Adding Real-time Features**

```python
# app/supabase/client.py
async def broadcast_review_update(self, product_id: int, avg_rating: float):
    """Broadcast review updates to subscribers"""
    try:
        data = {
            "product_id": product_id,
            "avg_rating": avg_rating,
            "timestamp": datetime.utcnow().isoformat()
        }
        result = self.client.table('product_updates').insert(data).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        logger.error(f"Error broadcasting review update: {e}")
        return {}
```

---

## 🔒 Security Best Practices

### **Authentication & Authorization**

#### **Firebase Token Verification**
```python
async def verify_firebase_token(id_token: str) -> dict:
    try:
        decoded_token = auth.verify_id_token(id_token)
        return {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name')
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
```

#### **Role-Based Access Control**
```python
from enum import Enum

class UserRole(Enum):
    CUSTOMER = "customer"
    DELIVERY_PARTNER = "delivery_partner"
    ADMIN = "admin"

async def require_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Usage
@router.get("/admin/stats")
async def get_admin_stats(admin: User = Depends(require_role(UserRole.ADMIN))):
    pass
```

### **Input Validation**

#### **Pydantic Validators**
```python
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0, le=10000)
    category_id: int = Field(..., gt=0)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return round(v, 2)
```

#### **SQL Injection Prevention**
```python
# Good: Using SQLAlchemy ORM
result = await db.execute(
    select(Product).where(Product.name.ilike(f"%{search_term}%"))
)

# Bad: Raw SQL with string formatting
# query = f"SELECT * FROM products WHERE name LIKE '%{search_term}%'"
```

### **Rate Limiting**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/auth/verify-otp")
@limiter.limit("5/minute")
async def verify_otp(request: Request, ...):
    pass
```

---

## 📊 Performance Optimization

### **Database Optimization**

#### **Query Optimization**
```python
# Bad: N+1 queries
orders = await db.execute(select(Order))
for order in orders:
    items = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))

# Good: Eager loading
orders = await db.execute(
    select(Order).options(selectinload(Order.items))
)
```

#### **Indexing**
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
```

#### **Connection Pooling**
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300
)
```

### **Caching Strategies**

#### **Redis Caching**
```python
import redis
from functools import wraps

redis_client = redis.from_url(settings.redis_url)

def cache_result(expiration: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(expiration=600)  # Cache for 10 minutes
async def get_popular_products():
    # Expensive database query
    pass
```

#### **Application-Level Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Expensive calculation
    pass
```

### **Async Best Practices**

#### **Proper Async Usage**
```python
# Good: Concurrent execution
async def get_order_details(order_id: int):
    order_task = asyncio.create_task(get_order(order_id))
    items_task = asyncio.create_task(get_order_items(order_id))
    user_task = asyncio.create_task(get_user(order.user_id))
    
    order, items, user = await asyncio.gather(order_task, items_task, user_task)
    return OrderDetails(order=order, items=items, user=user)

# Bad: Sequential execution
async def get_order_details_slow(order_id: int):
    order = await get_order(order_id)
    items = await get_order_items(order_id)
    user = await get_user(order.user_id)
    return OrderDetails(order=order, items=items, user=user)
```

---

## 🐛 Debugging & Troubleshooting

### **Logging Best Practices**

#### **Structured Logging**
```python
from loguru import logger

# Good: Structured logging
logger.info("Order created", 
    order_id=order.id, 
    user_id=user.id, 
    amount=order.total_amount,
    items_count=len(order.items)
)

# Bad: String formatting
logger.info(f"Order {order.id} created for user {user.id} with amount {order.total_amount}")
```

#### **Error Handling**
```python
async def create_order(db: AsyncSession, user_id: int, order_data: OrderCreate):
    try:
        # Business logic
        order = Order(...)
        db.add(order)
        await db.commit()
        
        logger.info("Order created successfully", order_id=order.id)
        return order
        
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Database error creating order", 
            user_id=user_id, 
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to create order")
    
    except Exception as e:
        await db.rollback()
        logger.error("Unexpected error creating order", 
            user_id=user_id, 
            error=str(e),
            exc_info=True
        )
        raise
```

### **Common Issues & Solutions**

#### **Database Connection Issues**
```python
# Add connection health check
@app.on_event("startup")
async def startup_event():
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Failed to connect to database", error=str(e))
        raise
```

#### **Memory Leaks**
```python
# Always close database sessions
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Use context managers for external connections
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

---

## 🚀 Deployment & CI/CD

### **GitHub Actions Workflow**
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
    
    - name: Run tests
      run: pytest
    
    - name: Run linting
      run: |
        flake8 app/
        black --check app/
        isort --check-only app/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      run: |
        # Deployment commands here
        echo "Deploying to production..."
```

### **Docker Multi-stage Build**
```dockerfile
# Dockerfile.prod
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.10-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📚 Contributing Guidelines

### **Code Style**
- Use **Black** for code formatting
- Use **isort** for import sorting
- Follow **PEP 8** naming conventions
- Write **docstrings** for all functions and classes
- Use **type hints** wherever possible

### **Git Workflow**
1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** Pull Request

### **Pull Request Guidelines**
- **Clear title** and description
- **Link related issues**
- **Add tests** for new features
- **Update documentation**
- **Ensure CI passes**

### **Code Review Checklist**
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Error handling is appropriate

---

## 📖 Additional Resources

### **Documentation**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Celery Documentation](https://docs.celeryproject.org/)

### **Tools & Libraries**
- **IDE**: VS Code with Python extension
- **Database**: PostgreSQL, pgAdmin
- **API Testing**: Postman, Insomnia
- **Monitoring**: Sentry, DataDog
- **Deployment**: Docker, Kubernetes

### **Community**
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Discord/Slack**: Real-time community chat
- **Stack Overflow**: Technical questions

---

Happy coding! 🚀 Let's build an amazing q-commerce platform together!