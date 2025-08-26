# Blinkit Clone - Deployment Guide

## 🚀 Free Hosting Options

This guide covers deploying your Blinkit clone to free hosting platforms with zero cost.

---

## 🌐 Render.com Deployment (Recommended)

### Prerequisites
- GitHub account with your code
- Render.com account (free)

### Step 1: Prepare Repository
```bash
# Ensure these files are in your repo root:
# - Dockerfile
# - requirements.txt
# - render.yaml (create this)
```

### Step 2: Create render.yaml
```yaml
# render.yaml
services:
  - type: web
    name: blinkit-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: blinkit-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: blinkit-redis
          property: connectionString
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: false

  - type: redis
    name: blinkit-redis
    ipAllowList: []

databases:
  - name: blinkit-db
    databaseName: blinkit_db
    user: postgres
```

### Step 3: Deploy to Render
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically deploy based on render.yaml

### Step 4: Configure Environment Variables
In Render dashboard, add these environment variables:
```env
FIREBASE_PROJECT_ID=your-project-id
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
FCM_SERVER_KEY=your-fcm-key
CORS_ORIGINS=["https://your-frontend-domain.com"]
```

### Step 5: Run Database Migration
```bash
# In Render shell or locally with production DATABASE_URL
alembic upgrade head
python init_data.py
```

---

## ✈️ Fly.io Deployment

### Step 1: Install Fly CLI
```bash
# macOS
brew install flyctl

# Windows
iwr https://fly.io/install.ps1 -useb | iex

# Linux
curl -L https://fly.io/install.sh | sh
```

### Step 2: Login and Initialize
```bash
fly auth login
fly launch
```

### Step 3: Configure fly.toml
```toml
# fly.toml
app = "blinkit-clone"
primary_region = "ord"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"
  DEBUG = "false"

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"
```

### Step 4: Add PostgreSQL
```bash
fly postgres create --name blinkit-db
fly postgres attach --app blinkit-clone blinkit-db
```

### Step 5: Add Redis
```bash
fly redis create --name blinkit-redis
fly redis attach --app blinkit-clone blinkit-redis
```

### Step 6: Set Environment Variables
```bash
fly secrets set FIREBASE_PROJECT_ID=your-project-id
fly secrets set SUPABASE_URL=your-supabase-url
fly secrets set SUPABASE_KEY=your-supabase-key
fly secrets set JWT_SECRET_KEY=your-secret-key
```

### Step 7: Deploy
```bash
fly deploy
```

---

## 🚂 Railway.app Deployment

### Step 1: Connect Repository
1. Go to [Railway](https://railway.app/)
2. Click "Deploy from GitHub"
3. Select your repository

### Step 2: Add Services
```bash
# Railway will auto-detect your app
# Add PostgreSQL service
# Add Redis service
```

### Step 3: Configure Environment Variables
In Railway dashboard:
```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
FIREBASE_PROJECT_ID=your-project-id
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
JWT_SECRET_KEY=your-secret-key
DEBUG=false
PORT=8000
```

### Step 4: Configure Build
```json
// package.json (create if needed)
{
  "scripts": {
    "build": "pip install -r requirements.txt",
    "start": "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

---

## 🐳 Docker Production Setup

### Optimized Dockerfile
```dockerfile
# Dockerfile.prod
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Production Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  celery:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: celery -A app.celery_tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

## 🔧 Environment Configuration

### Production Environment Variables
```env
# Production .env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0

# Security
JWT_SECRET_KEY=super-secure-random-key-256-bits
DEBUG=false

# CORS (your actual domains)
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]

# External Services
FIREBASE_PROJECT_ID=your-prod-project
FIREBASE_CREDENTIALS_PATH=/app/firebase-prod-credentials.json
SUPABASE_URL=https://your-prod-project.supabase.co
SUPABASE_KEY=your-prod-anon-key

# Storage
R2_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your-prod-access-key
R2_SECRET_ACCESS_KEY=your-prod-secret-key
R2_BUCKET_NAME=blinkit-prod-assets

# Notifications
FCM_SERVER_KEY=your-prod-fcm-key
RESEND_API_KEY=your-prod-resend-key

# Search
MEILISEARCH_URL=https://your-meilisearch-instance.com
MEILISEARCH_MASTER_KEY=your-prod-master-key
```

---

## 📊 Production Monitoring

### Health Checks
```python
# Add to main.py
@app.get("/health")
async def health_check():
    # Check database
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # Check Redis
    try:
        redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy",
        "service": "Blinkit Clone",
        "database": db_status,
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Logging Configuration
```python
# Production logging
import logging
from loguru import logger

# Configure for production
logger.remove()
logger.add(
    "logs/app.log",
    rotation="100 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    serialize=True  # JSON format for log aggregation
)

# Add structured logging
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}"
)
```

---

## 🔐 Security Checklist

### Pre-Deployment Security
- [ ] Change all default passwords
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Validate all inputs
- [ ] Use secure headers
- [ ] Enable database SSL
- [ ] Rotate API keys regularly

### Production Security Headers
```python
# Add to main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Force HTTPS in production
if not settings.debug:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## 📈 Performance Optimization

### Database Optimization
```python
# Connection pooling
engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300
)
```

### Caching Strategy
```python
# Redis caching
@lru_cache(maxsize=100)
async def get_categories():
    # Cache categories for 1 hour
    pass

# Application-level caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def calculate_distance(lat1, lon1, lat2, lon2):
    # Cache distance calculations
    pass
```

### API Optimization
```python
# Pagination
@router.get("/products")
async def get_products(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    # Implement pagination
    pass

# Database query optimization
async def get_products_optimized(db: AsyncSession):
    return await db.execute(
        select(Product)
        .options(selectinload(Product.category))  # Eager loading
        .where(Product.is_active == True)
        .limit(50)
    )
```

---

## 🚨 Troubleshooting Production Issues

### Common Production Problems

#### 1. High Memory Usage
```bash
# Monitor memory
docker stats

# Solution: Limit worker processes
uvicorn app.main:app --workers 2 --max-requests 1000
```

#### 2. Database Connection Pool Exhausted
```python
# Increase pool size
engine = create_async_engine(
    DATABASE_URL,
    pool_size=50,
    max_overflow=10
)
```

#### 3. Slow API Responses
```bash
# Add database indexes
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
```

#### 4. Background Task Failures
```bash
# Monitor Celery
celery -A app.celery_tasks inspect active
celery -A app.celery_tasks inspect stats

# Restart workers
celery -A app.celery_tasks control shutdown
celery -A app.celery_tasks worker --loglevel=info
```

### Monitoring Commands
```bash
# Check application health
curl https://your-domain.com/health

# Monitor logs
tail -f logs/app.log

# Database performance
SELECT * FROM pg_stat_activity WHERE state = 'active';

# Redis info
redis-cli info memory
```

Your Blinkit clone is now ready for production deployment! 🚀

Choose the platform that best fits your needs:
- **Render.com**: Easiest setup, good free tier
- **Fly.io**: More control, global deployment
- **Railway.app**: Simple interface, good for beginners
- **Docker**: Maximum control, any cloud provider