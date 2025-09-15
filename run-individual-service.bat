@echo off
if "%1"=="" (
    echo Usage: run-individual-service.bat [service-name]
    echo.
    echo Available services:
    echo   gateway
    echo   auth
    echo   product
    echo   cart
    echo   order
    echo   delivery
    echo   notification
    echo   admin
    echo.
    echo Example: run-individual-service.bat gateway
    pause
    exit /b 1
)

cd /d "c:\Users\husain.burhanpurwala\Downloads\blinkit_clone"
call .venv\Scripts\activate.bat

if "%1"=="gateway" (
    cd microservices\api-gateway
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else if "%1"=="auth" (
    cd microservices\auth-service
    uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
) else if "%1"=="product" (
    cd microservices\product-service
    uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
) else if "%1"=="cart" (
    cd microservices\cart-service
    uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
) else if "%1"=="order" (
    cd microservices\order-service
    uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
) else if "%1"=="delivery" (
    cd microservices\delivery-service
    uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
) else if "%1"=="notification" (
    cd microservices\notification-service
    uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
) else if "%1"=="admin" (
    cd microservices\admin-service
    uvicorn app.main:app --host 0.0.0.0 --port 8007 --reload
) else (
    echo Invalid service name: %1
    echo Available services: gateway, auth, product, cart, order, delivery, notification, admin
    pause
    exit /b 1
)