# Design Document

## Overview

This design addresses critical production readiness issues in the microservices architecture by implementing missing Docker configurations, removing security vulnerabilities, standardizing environment variable usage, and ensuring consistent patterns across all services.

## Architecture

### Current State Analysis

The microservices application has:
- ✅ 7 services: API Gateway, Auth, Product, Cart, Order, Delivery, Notification
- ✅ Separate databases per service
- ✅ Inter-service communication patterns
- ❌ Missing Dockerfiles for 5 services
- ❌ Hardcoded credentials in multiple locations
- ❌ Inconsistent environment variable usage

### Target Architecture

```mermaid
graph TB
    subgraph "Docker Environment"
        subgraph "Infrastructure"
            DB1[Auth DB]
            DB2[Product DB] 
            DB3[Cart DB]
            DB4[Order DB]
            DB5[Delivery DB]
            REDIS[Redis]
            MEILI[Meilisearch]
        end
        
        subgraph "Services (All Dockerized)"
            GW[API Gateway:8000]
            AUTH[Auth Service:8001]
            PROD[Product Service:8002]
            CART[Cart Service:8003]
            ORDER[Order Service:8004]
            DEL[Delivery Service:8005]
            NOTIF[Notification Service:8006]
        end
    end
    
    subgraph "Configuration"
        ENV[.env file]
        TEMPLATE[.env.template]
    end
    
    ENV --> GW
    ENV --> AUTH
    ENV --> PROD
    ENV --> CART
    ENV --> ORDER
    ENV --> DEL
    ENV --> NOTIF
```

## Components and Interfaces

### 1. Docker Configuration Standardization

**Missing Dockerfiles Creation:**
- `cart-service/Dockerfile`
- `order-service/Dockerfile` 
- `delivery-service/Dockerfile`
- `notification-service/Dockerfile`
- `product-service/Dockerfile`

**Standard Dockerfile Pattern:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
EXPOSE 800X
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "800X"]
```

### 2. Security Configuration Management

**Environment Variable Standardization:**

| Service | Current Issue | Fix |
|---------|---------------|-----|
| API Gateway | Hardcoded admin key `admin123` | Use `ADMIN_API_KEY` env var |
| JWT Auth | Default secret `super-secret-jwt-key` | Use `JWT_SECRET_KEY` from env |
| Docker Compose | Hardcoded DB passwords | Use env vars with secure defaults |
| Start Scripts | Hardcoded credentials | Remove development shortcuts |

**Configuration Loading Pattern:**
```python
from pydantic import BaseSettings
from typing import Optional

class ServiceSettings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    admin_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### 3. Health Check Enhancement

**Comprehensive Health Checks:**
```python
@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "service": "service-name",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": await check_database(),
            "redis": await check_redis(),
            "external_services": await check_external_deps()
        }
    }
    
    if any(not check for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status
```

### 4. Environment Configuration Alignment

**Docker Compose Environment Variables:**
```yaml
environment:
  - DATABASE_URL=${AUTH_DB_URL:-postgresql+asyncpg://auth_user:${AUTH_DB_PASSWORD}@auth-db:5432/auth_db}
  - JWT_SECRET_KEY=${JWT_SECRET_KEY}
  - ADMIN_API_KEY=${ADMIN_API_KEY}
```

**Updated .env.template:**
```bash
# Service-specific database URLs
AUTH_DB_PASSWORD=your_secure_auth_password
PRODUCT_DB_PASSWORD=your_secure_product_password
# ... other passwords

# Security
JWT_SECRET_KEY=your_jwt_secret_key_minimum_32_characters
ADMIN_API_KEY=your_secure_admin_api_key

# External services (existing)
SUPABASE_URL=your_supabase_url
FCM_SERVER_KEY=your_fcm_server_key
```

## Data Models

### Configuration Models

**Base Settings Class:**
```python
class BaseServiceSettings(BaseSettings):
    """Base settings for all microservices"""
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"
    cors_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

**Service-Specific Settings:**
```python
class AuthServiceSettings(BaseServiceSettings):
    jwt_secret_key: str
    firebase_project_id: str
    google_client_id: str
    google_client_secret: str

class APIGatewaySettings(BaseServiceSettings):
    admin_api_key: str
    auth_service_url: str = "http://auth-service:8001"
    # ... other service URLs
```

## Error Handling

### Configuration Validation

**Startup Validation:**
```python
async def validate_configuration():
    """Validate required configuration on startup"""
    required_vars = ["DATABASE_URL", "JWT_SECRET_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        raise RuntimeError(f"Configuration error: Missing {missing_vars}")
```

**Database Connection Validation:**
```python
async def validate_database_connection():
    """Ensure database is accessible on startup"""
    try:
        async with database.get_session() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Database connection validated")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise RuntimeError("Database connection validation failed")
```

### Graceful Degradation

**Service Communication Error Handling:**
```python
async def call_service_with_fallback(url: str, fallback_response: dict):
    """Call external service with fallback on failure"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.warning(f"Service call failed: {e}, using fallback")
        return fallback_response
```

## Testing Strategy

### Configuration Testing

**Environment Variable Testing:**
```python
def test_missing_required_env_vars():
    """Test that missing env vars cause startup failure"""
    with pytest.raises(RuntimeError, match="Missing required environment variables"):
        settings = ServiceSettings()

def test_secure_defaults():
    """Test that no hardcoded credentials exist"""
    # Scan codebase for hardcoded secrets
    assert not has_hardcoded_credentials()
```

**Docker Build Testing:**
```python
def test_docker_builds():
    """Test that all services build successfully"""
    services = ["auth-service", "product-service", "cart-service", 
                "order-service", "delivery-service", "notification-service"]
    
    for service in services:
        result = subprocess.run(
            ["docker", "build", "-t", f"test-{service}", f"./{service}"],
            capture_output=True
        )
        assert result.returncode == 0, f"{service} Docker build failed"
```

### Health Check Testing

**Health Endpoint Testing:**
```python
async def test_health_checks():
    """Test health endpoints return proper status"""
    services = ["8001", "8002", "8003", "8004", "8005", "8006"]
    
    for port in services:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:{port}/health")
            assert response.status_code in [200, 503]
            health_data = response.json()
            assert "status" in health_data
            assert "checks" in health_data
```

### Integration Testing

**Docker Compose Integration:**
```python
def test_docker_compose_startup():
    """Test that docker-compose up starts all services"""
    result = subprocess.run(
        ["docker-compose", "up", "-d", "--build"],
        capture_output=True,
        cwd="microservices"
    )
    assert result.returncode == 0
    
    # Wait for services to be healthy
    time.sleep(30)
    
    # Check all services are running
    result = subprocess.run(["docker-compose", "ps"], capture_output=True)
    assert "Up" in result.stdout.decode()
```

## Implementation Phases

### Phase 1: Docker Configuration
1. Create missing Dockerfiles using standardized template
2. Update docker-compose.yml to use environment variables
3. Test Docker builds for all services

### Phase 2: Security Hardening
1. Remove hardcoded credentials from all files
2. Update configuration classes to require env vars
3. Add startup validation for required configuration

### Phase 3: Environment Standardization
1. Align .env.template with docker-compose.yml
2. Update all services to use consistent env var names
3. Add configuration validation and error handling

### Phase 4: Health Check Enhancement
1. Implement comprehensive health checks
2. Add database and external service connectivity checks
3. Update Docker health check configurations

### Phase 5: Testing and Validation
1. Add configuration and Docker build tests
2. Implement integration tests for full stack
3. Validate security improvements with automated scans