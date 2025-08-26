# Blinkit Clone - Microservices Architecture

## 🏗️ Architecture Overview

The monolithic application has been transformed into a microservices architecture with the following services:

```
┌─────────────────┐
│   API Gateway   │ ← Single entry point (Port 8000)
│   (Port 8000)   │
└─────────┬───────┘
          │
    ┌─────┼─────┐
    │     │     │
┌───▼─┐ ┌─▼─┐ ┌─▼──┐
│Auth │ │Prod│ │Cart│ ... (Microservices)
│8001 │ │8002│ │8003│
└─────┘ └────┘ └────┘
```

## 🔧 Services

| Service | Port | Description |
|---------|------|-------------|
| **API Gateway** | 8000 | Single entry point, routing, rate limiting |
| **Auth Service** | 8001 | User authentication, Firebase integration |
| **Product Service** | 8002 | Product catalog, categories, search |
| **Cart Service** | 8003 | Shopping cart management |
| **Order Service** | 8004 | Order processing, lifecycle management |
| **Delivery Service** | 8005 | Delivery partner management, GPS tracking |
| **Notification Service** | 8006 | Push notifications, FCM integration |

## 🚀 Quick Start

### Option 1: Development Mode
```bash
# Start infrastructure
docker-compose up -d postgres redis meilisearch

# Start all microservices
python start-microservices.py
```

### Option 2: Docker Mode
```bash
# Start everything with Docker
docker-compose up --build
```

## 📡 API Gateway

All client requests go through the API Gateway at `http://localhost:8000`

**Features:**
- Request routing to appropriate microservices
- Rate limiting (100 req/min per IP)
- CORS handling
- Error handling
- Service discovery

**Endpoints:**
- `/auth/*` → Auth Service
- `/products/*` → Product Service  
- `/cart/*` → Cart Service
- `/orders/*` → Order Service
- `/delivery/*` → Delivery Service
- `/notifications/*` → Notification Service

## 🔐 Inter-Service Communication

Services communicate via HTTP APIs:

```python
# Example: Cart Service calling Product Service
async with httpx.AsyncClient() as client:
    response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
    product = response.json()
```

**Authentication Flow:**
1. Client → API Gateway (with Firebase token)
2. API Gateway → Auth Service (token verification)
3. Auth Service → Returns user info
4. API Gateway → Target Service (with user context)

## 📁 Directory Structure

```
microservices/
├── shared/                 # Common utilities
│   ├── config.py          # Shared configuration
│   ├── database.py        # Database manager
│   └── auth.py            # Auth client
├── api-gateway/           # API Gateway service
│   ├── app/
│   │   ├── main.py        # FastAPI app
│   │   ├── routes/        # Route handlers
│   │   └── middleware/    # Rate limiting, etc.
│   ├── Dockerfile
│   └── requirements.txt
├── auth-service/          # Authentication service
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/        # Auth endpoints
│   │   ├── models/        # User model
│   │   ├── schemas/       # Pydantic models
│   │   └── services/      # Business logic
│   ├── Dockerfile
│   └── requirements.txt
├── product-service/       # Product catalog service
├── cart-service/          # Shopping cart service
├── order-service/         # Order management service
├── delivery-service/      # Delivery tracking service
├── notification-service/  # Push notifications service
├── docker-compose.yml     # All services orchestration
└── start-microservices.py # Development startup script
```

## 🔧 Development

### Running Individual Services

```bash
# Auth Service
cd auth-service
uvicorn app.main:app --port 8001 --reload

# Product Service  
cd product-service
uvicorn app.main:app --port 8002 --reload

# API Gateway
cd api-gateway
uvicorn app.main:app --port 8000 --reload
```

### Adding New Service

1. Create service directory with same structure
2. Add to `docker-compose.yml`
3. Add routes to API Gateway
4. Update `start-microservices.py`

## 🧪 Testing

### Health Checks
```bash
# API Gateway
curl http://localhost:8000/health

# Individual services
curl http://localhost:8001/health  # Auth
curl http://localhost:8002/health  # Product
```

### API Testing
```bash
# Through API Gateway (recommended)
curl http://localhost:8000/products/categories

# Direct service call (for debugging)
curl http://localhost:8002/categories
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build and start all services
docker-compose up --build -d

# Scale specific services
docker-compose up --scale product-service=3
```

### Production Considerations
- **Load Balancer**: Nginx/HAProxy in front of API Gateway
- **Service Discovery**: Consul, Eureka, or Kubernetes
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or similar
- **Circuit Breakers**: Hystrix or similar
- **API Versioning**: `/v1/`, `/v2/` prefixes

## 🔍 Monitoring

### Service Health
Each service exposes `/health` endpoint

### Logs
```bash
# Docker logs
docker-compose logs -f api-gateway
docker-compose logs -f auth-service

# Development logs
tail -f auth-service/logs/app.log
```

## 🎯 Benefits of Microservices

✅ **Independent Scaling**: Scale services based on demand  
✅ **Technology Diversity**: Different tech stacks per service  
✅ **Fault Isolation**: One service failure doesn't bring down entire system  
✅ **Team Independence**: Teams can work on services independently  
✅ **Deployment Flexibility**: Deploy services independently  
✅ **Database Per Service**: Each service owns its data  

## 🚨 Challenges Addressed

❌ **Network Latency**: Minimized with efficient API design  
❌ **Data Consistency**: Eventual consistency patterns  
❌ **Service Discovery**: API Gateway handles routing  
❌ **Monitoring Complexity**: Centralized logging and health checks  
❌ **Testing Complexity**: Contract testing between services  

## 🔗 Service Dependencies

```
API Gateway
├── Auth Service (user verification)
├── Product Service (catalog)
├── Cart Service → Product Service (product info)
├── Order Service → Cart Service (cart items)
│                → Auth Service (user info)
│                → Notification Service (order updates)
├── Delivery Service → Order Service (order details)
│                   → Notification Service (delivery updates)
└── Notification Service (independent)
```

Your monolithic Blinkit Clone is now a fully functional microservices architecture! 🎉