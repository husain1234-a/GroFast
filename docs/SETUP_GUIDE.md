# Blinkit Clone - Complete Setup Guide

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.10+
- Git
- Docker & Docker Compose (optional but recommended)

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd blinkit_clone
cp .env.example .env
```

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install packages
pip install -r requirements-minimal.txt
```

### 3. Start Services
```bash
# Option A: Docker (Recommended)
docker-compose up -d postgres redis meilisearch

# Option B: Local installation (see detailed setup below)
```

### 4. Run Application
```bash
# Start FastAPI server
python run_dev.py

# In another terminal, start background tasks
celery -A app.celery_tasks worker --loglevel=info
```

### 5. Test Installation
- Visit: http://localhost:8000/docs
- Test: http://localhost:8000/health

---

## 🔧 Detailed Setup Instructions

### Step 1: Environment Setup

#### Python Environment
```bash
# Check Python version
python --version  # Should be 3.10+

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

#### Install Dependencies
```bash
# Install all dependencies
pip install -r requirements-minimal.txt

# Or install specific packages if issues occur:
pip install fastapi uvicorn sqlalchemy[asyncio] asyncpg alembic redis celery pydantic pydantic-settings firebase-admin httpx supabase meilisearch python-multipart python-jose[cryptography] passlib[bcrypt] loguru boto3 python-dotenv
```

### Step 2: Database Setup

#### Option A: Docker (Recommended)
```bash
# Start PostgreSQL, Redis, and Meilisearch
docker-compose up -d postgres redis meilisearch

# Check services are running
docker-compose ps
```

#### Option B: Local Installation

**PostgreSQL:**
```bash
# Install PostgreSQL (varies by OS)
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# macOS (with Homebrew):
brew install postgresql

# Windows: Download from postgresql.org

# Create database
sudo -u postgres createdb blinkit_db
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'password123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE blinkit_db TO postgres;"
```

**Redis:**
```bash
# Ubuntu/Debian:
sudo apt-get install redis-server

# macOS:
brew install redis

# Windows: Download from redis.io or use WSL

# Start Redis
redis-server
```

**Meilisearch:**
```bash
# Download and install Meilisearch
curl -L https://install.meilisearch.com | sh

# Start Meilisearch
./meilisearch --master-key="dummy-master-key-123"
```

### Step 3: Environment Configuration

#### Edit .env File
```bash
# Copy example environment file
cp .env.example .env

# Edit with your preferred editor
nano .env  # or code .env or vim .env
```

#### Required Configuration
```env
# Database (update if using different credentials)
DATABASE_URL=postgresql+asyncpg://postgres:password123@localhost:5432/blinkit_db

# Redis (default should work)
REDIS_URL=redis://localhost:6379/0

# Meilisearch (default should work)
MEILISEARCH_URL=http://localhost:7700
MEILISEARCH_MASTER_KEY=dummy-master-key-123

# JWT Secret (change for production)
JWT_SECRET_KEY=your-super-secret-jwt-key-for-development

# App Settings
DEBUG=True
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### Step 4: Database Migration

```bash
# Initialize Alembic (if not already done)
alembic init migrations

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### Step 5: Initialize Sample Data

```bash
# Run the data initialization script
python init_data.py
```

This will create:
- Sample product categories
- Sample products
- Sample delivery partners

### Step 6: Firebase Setup (Optional)

#### Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create new project
3. Enable Authentication
4. Enable Phone and Google sign-in methods

#### Download Credentials
1. Go to Project Settings → Service Accounts
2. Generate new private key
3. Save as `firebase-credentials.json` in project root

#### Update .env
```env
FIREBASE_PROJECT_ID=your-actual-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
```

### Step 7: Supabase Setup (Optional)

#### Create Supabase Project
1. Go to [Supabase](https://supabase.com/)
2. Create new project
3. Go to Settings → API
4. Copy URL and anon key

#### Create Realtime Table
```sql
-- Run in Supabase SQL Editor
CREATE TABLE delivery_locations (
  id SERIAL PRIMARY KEY,
  delivery_partner_id INTEGER NOT NULL,
  order_id INTEGER,
  latitude FLOAT NOT NULL,
  longitude FLOAT NOT NULL,
  timestamp TIMESTAMP DEFAULT NOW()
);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE delivery_locations;
```

#### Update .env
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

---

## 🏃‍♂️ Running the Application

### Development Mode
```bash
# Terminal 1: Start FastAPI server
python run_dev.py

# Terminal 2: Start Celery worker
celery -A app.celery_tasks worker --loglevel=info

# Terminal 3: Start Celery beat (for scheduled tasks)
celery -A app.celery_tasks beat --loglevel=info
```

### Production Mode
```bash
# Start with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or with Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Mode
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run specific services
docker-compose up -d postgres redis meilisearch
docker-compose up app
```

---

## 🧪 Testing the Setup

### Automated Tests
```bash
# Run API tests
python test_all_apis.py

# Run basic connectivity test
python test_api.py
```

### Manual Testing

#### 1. Health Check
```bash
curl http://localhost:8000/health
```
Expected: `{"status": "healthy", "service": "Blinkit Clone"}`

#### 2. API Documentation
Visit: http://localhost:8000/docs

#### 3. Test Endpoints
```bash
# Get categories
curl http://localhost:8000/products/categories

# Get products
curl http://localhost:8000/products

# Admin stats
curl "http://localhost:8000/admin/stats?admin_key=admin123"
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Error
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution:**
- Check PostgreSQL is running: `docker-compose ps` or `sudo service postgresql status`
- Verify DATABASE_URL in .env
- Check firewall settings

#### 2. Redis Connection Error
```
redis.exceptions.ConnectionError: Error connecting to Redis
```
**Solution:**
- Check Redis is running: `redis-cli ping`
- Verify REDIS_URL in .env
- Start Redis: `redis-server` or `docker-compose up -d redis`

#### 3. Import Errors
```
ModuleNotFoundError: No module named 'fastapi'
```
**Solution:**
- Activate virtual environment: `source .venv/bin/activate`
- Install dependencies: `pip install -r requirements-minimal.txt`

#### 4. Port Already in Use
```
OSError: [Errno 48] Address already in use
```
**Solution:**
- Kill process using port: `lsof -ti:8000 | xargs kill -9`
- Or use different port: `uvicorn app.main:app --port 8001`

#### 5. Firebase Credentials Error
```
ValueError: the greenlet library is required to use this function
```
**Solution:**
- Install greenlet: `pip install greenlet`
- Or use dummy credentials for development

### Performance Issues

#### Slow API Responses
1. Check database indexes
2. Monitor Redis cache hit rates
3. Review slow query logs
4. Consider connection pooling

#### High Memory Usage
1. Limit worker processes
2. Implement pagination
3. Use database query optimization
4. Monitor background tasks

---

## 📊 Monitoring Setup

### Application Logs
```bash
# View logs
tail -f logs/app.log

# Or with Docker
docker-compose logs -f app
```

### Database Monitoring
```bash
# PostgreSQL stats
docker-compose exec postgres psql -U postgres -d blinkit_db -c "SELECT * FROM pg_stat_activity;"

# Redis info
docker-compose exec redis redis-cli info
```

### Health Monitoring
Set up monitoring for:
- `/health` endpoint
- Database connectivity
- Redis availability
- Background task processing

---

## 🚀 Next Steps

After successful setup:

1. **Configure External Services**
   - Set up real Firebase project
   - Configure Supabase for real-time features
   - Set up Cloudflare R2 for file storage

2. **Customize Application**
   - Add your product categories
   - Configure delivery zones
   - Set up payment integration

3. **Deploy to Production**
   - Choose hosting platform (Render, Fly.io, Railway)
   - Set up CI/CD pipeline
   - Configure monitoring and alerts

4. **Build Frontend**
   - React Native mobile app
   - React web dashboard
   - Admin panel

Your Blinkit clone is now ready for development! 🎉