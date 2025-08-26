#!/usr/bin/env python3
"""Quick setup script for Blinkit Clone"""
import os
import subprocess
import sys

def run_command(command, description):
    """Run shell command with description"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Blinkit Clone...")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("📝 Creating .env file from template...")
        subprocess.run('copy .env.example .env', shell=True)
        print("⚠️  Please edit .env file with your credentials before continuing")
        return
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    print("✅ Logs directory created")
    
    # Install dependencies
    if not run_command('pip install -r requirements.txt', 'Installing Python dependencies'):
        return
    
    # Start Docker services
    if not run_command('docker-compose up -d postgres redis meilisearch', 'Starting Docker services'):
        print("⚠️  Make sure Docker is running and try again")
        return
    
    # Wait for services
    print("⏳ Waiting for services to start...")
    import time
    time.sleep(10)
    
    # Run migrations
    if not run_command('alembic revision --autogenerate -m "Initial migration"', 'Creating database migration'):
        return
    
    if not run_command('alembic upgrade head', 'Applying database migration'):
        return
    
    # Initialize sample data
    if not run_command('python init_data.py', 'Initializing sample data'):
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your Firebase, Supabase, and other credentials")
    print("2. Run: python run_dev.py (for development)")
    print("3. Run: celery -A app.celery_tasks worker --loglevel=info (in another terminal)")
    print("4. Visit: http://localhost:8000/docs for API documentation")
    print("\n🔗 Useful URLs:")
    print("- API Docs: http://localhost:8000/docs")
    print("- Health Check: http://localhost:8000/health")
    print("- Meilisearch: http://localhost:7700")

if __name__ == "__main__":
    main()