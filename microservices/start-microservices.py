#!/usr/bin/env python3
"""Start all microservices for development"""
import subprocess
import sys
import time
import os

def start_service(service_name, port, directory):
    """Start a microservice"""
    print(f"🚀 Starting {service_name} on port {port}...")
    
    env = os.environ.copy()
    env['PORT'] = str(port)
    
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload"
    ], cwd=directory, env=env)
    
    return process

def main():
    """Start all microservices"""
    print("🏗️  Starting GroFast Microservices...")
    
    services = [
        ("Auth Service", 8001, "auth-service"),
        ("Product Service", 8002, "product-service"),
        ("Cart Service", 8003, "cart-service"),
        ("Order Service", 8004, "order-service"),
        ("Delivery Service", 8005, "delivery-service"),
        ("Notification Service", 8006, "notification-service"),
        ("API Gateway", 8000, "api-gateway"),
    ]
    
    processes = []
    
    try:
        for service_name, port, directory in services:
            if os.path.exists(directory):
                process = start_service(service_name, port, directory)
                processes.append((service_name, process))
                time.sleep(2)  # Wait between starts
            else:
                print(f"⚠️  {service_name} directory not found: {directory}")
        
        print("\n✅ All services started!")
        print("\n📡 Service URLs:")
        for service_name, port, _ in services:
            print(f"   {service_name}: http://localhost:{port}")
        
        print("\n🌐 API Gateway: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop all services...")
        
        # Wait for all processes
        for service_name, process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for service_name, process in processes:
            print(f"   Stopping {service_name}...")
            process.terminate()
        
        print("✅ All services stopped!")

if __name__ == "__main__":
    main()