#!/usr/bin/env python3
"""Fix all microservices startup issues"""
import subprocess
import sys
import os

def install_dependencies():
    """Install missing dependencies for all services"""
    services = [
        "auth-service",
        "product-service", 
        "cart-service",
        "order-service",
        "delivery-service",
        "notification-service",
        "api-gateway"
    ]
    
    for service in services:
        if os.path.exists(service):
            print(f"Installing dependencies for {service}...")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", f"{service}/requirements.txt"
                ], check=True, cwd=".")
                print(f"✅ {service} dependencies installed")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {service} dependencies")

def start_individual_services():
    """Start services individually to avoid connection issues"""
    services = [
        ("Auth Service", 8001, "auth-service"),
        ("Product Service", 8002, "product-service"),
        ("Cart Service", 8003, "cart-service"),
        ("Order Service", 8004, "order-service"),
        ("Delivery Service", 8005, "delivery-service"),
        ("Notification Service", 8006, "notification-service"),
        ("API Gateway", 8000, "api-gateway"),
    ]
    
    print("🔧 Starting services individually...")
    
    for service_name, port, directory in services:
        if os.path.exists(directory):
            print(f"\n🚀 Start {service_name} manually:")
            print(f"cd {directory}")
            print(f"uvicorn app.main:app --host 0.0.0.0 --port {port} --reload")
        else:
            print(f"⚠️  {service_name} directory not found: {directory}")

if __name__ == "__main__":
    print("🔧 Fixing microservices...")
    install_dependencies()
    print("\n" + "="*50)
    start_individual_services()
    print("\n✅ Run each service in separate terminals!")