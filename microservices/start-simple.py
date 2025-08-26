#!/usr/bin/env python3
"""Start microservices with proper error handling"""
import subprocess
import sys
import time
import os

def start_service_safe(service_name, port, directory):
    """Start a service with error handling"""
    print(f"🚀 Starting {service_name} on port {port}...")
    
    if not os.path.exists(directory):
        print(f"❌ Directory not found: {directory}")
        return None
    
    try:
        env = os.environ.copy()
        env['PORT'] = str(port)
        env['DATABASE_URL'] = 'postgresql+asyncpg://postgres:password123@localhost:5432/blinkit_db'
        env['REDIS_URL'] = 'redis://localhost:6379/0'
        env['JWT_SECRET_KEY'] = 'super-secret-jwt-key'
        
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ], cwd=directory, env=env, 
           stdout=subprocess.PIPE, 
           stderr=subprocess.PIPE)
        
        time.sleep(2)  # Wait to check if it started
        
        if process.poll() is None:
            print(f"✅ {service_name} started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ {service_name} failed to start:")
            print(f"Error: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start {service_name}: {str(e)}")
        return None

def main():
    """Start all services with error handling"""
    print("🏗️  Starting Blinkit Clone Microservices (Safe Mode)...")
    
    services = [
        ("Notification Service", 8006, "notification-service"),  # Start simple ones first
        ("Auth Service", 8001, "auth-service"),
        ("Product Service", 8002, "product-service"),
        ("Cart Service", 8003, "cart-service"),
        ("Order Service", 8004, "order-service"),
        ("Delivery Service", 8005, "delivery-service"),
        ("API Gateway", 8000, "api-gateway"),
    ]
    
    processes = []
    
    for service_name, port, directory in services:
        process = start_service_safe(service_name, port, directory)
        if process:
            processes.append((service_name, process))
        time.sleep(3)  # Wait between starts
    
    if processes:
        print(f"\n✅ {len(processes)} services started successfully!")
        print("\n📡 Service URLs:")
        service_ports = {
            "Auth Service": 8001,
            "Product Service": 8002,
            "Cart Service": 8003,
            "Order Service": 8004,
            "Delivery Service": 8005,
            "Notification Service": 8006,
            "API Gateway": 8000
        }
        
        for service_name, _ in processes:
            port = service_ports.get(service_name, 8000)
            print(f"   {service_name}: http://localhost:{port}")
        
        print("\n🌐 API Gateway: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop all services...")
        
        try:
            # Wait for all processes
            for service_name, process in processes:
                process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping all services...")
            for service_name, process in processes:
                print(f"   Stopping {service_name}...")
                process.terminate()
            print("✅ All services stopped!")
    else:
        print("❌ No services started successfully!")

if __name__ == "__main__":
    main()