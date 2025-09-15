# PowerShell script to run microservices in VS Code integrated terminals
Write-Host "Starting all microservices in VS Code terminals..." -ForegroundColor Green

$services = @(
    @{Name="Auth Service"; Port=8001; Path="microservices/auth-service"},
    @{Name="Product Service"; Port=8002; Path="microservices/product-service"},
    @{Name="Cart Service"; Port=8003; Path="microservices/cart-service"},
    @{Name="Order Service"; Port=8004; Path="microservices/order-service"},
    @{Name="Delivery Service"; Port=8005; Path="microservices/delivery-service"},
    @{Name="Notification Service"; Port=8006; Path="microservices/notification-service"},
    @{Name="Admin Service"; Port=8007; Path="microservices/admin-service"}
)

foreach ($service in $services) {
    Write-Host "Starting $($service.Name) on port $($service.Port)..." -ForegroundColor Yellow
    
    # Create new terminal for each service
    code --command workbench.action.terminal.new
    Start-Sleep -Seconds 1
    
    # Send commands to the terminal
    $command = "cd $($service.Path) && uvicorn app.main:app --host 0.0.0.0 --port $($service.Port) --reload"
    code --command workbench.action.terminal.sendSequence --args $command
}

Write-Host "`nAll microservices started!" -ForegroundColor Green
Write-Host "Check the terminal tabs in VS Code for each service." -ForegroundColor Cyan