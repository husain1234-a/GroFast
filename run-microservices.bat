@echo off
echo Starting all microservices...

cd /d "c:\Users\husain.burhanpurwala\Downloads\blinkit_clone"

REM Start each microservice in a new terminal window
start "API Gateway" cmd /k "call .venv\Scripts\activate.bat && cd microservices\api-gateway && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

start "Auth Service" cmd /k "call .venv\Scripts\activate.bat && cd microservices\auth-service && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

start "Product Service" cmd /k "call .venv\Scripts\activate.bat && cd microservices\product-service && uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload"

start "Cart Service" cmd /k "call .venv\Scripts\activate.bat && cd microservices\cart-service && uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload"

start "Order Service" cmd /k "call .venv\Scripts\activate.bat && cd microservices\order-service && uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload"

start "Delivery Service" cmd /k "call .venv\Scripts\activate.bat && cd microservices\delivery-service && uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload"

start "Notification Service" cmd /k "call .venv\Scripts\activate.bat && cd microservices\notification-service && uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload"

start "Admin Service" cmd /k "call .venv\Scripts\activate.bat && cd microservices\admin-service && uvicorn app.main:app --host 0.0.0.0 --port 8007 --reload"

echo All microservices started!
echo.
echo Service URLs:
echo API Gateway:         http://localhost:8000
echo Auth Service:         http://localhost:8001
echo Product Service:      http://localhost:8002
echo Cart Service:         http://localhost:8003
echo Order Service:        http://localhost:8004
echo Delivery Service:     http://localhost:8005
echo Notification Service: http://localhost:8006
echo Admin Service:        http://localhost:8007
echo.
pause