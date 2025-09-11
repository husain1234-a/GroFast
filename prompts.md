Update the provided microservices codebase to achieve complete functional parity, security, and robustness with the fully implemented monolithic application. The current microservices contain placeholder implementations, critical security flaws, and missing integrations. Use the monolithic code as the definitive blueprint for business logic and data models.

1. auth-service: Fix Critical Security Flaw (Firebase Token Verification)
The current implementation is a severe security vulnerability. The /internal/verify-token endpoint does not verify the Firebase token; it blindly trusts it.

Required Fix: Implement proper Firebase token verification using the firebase_admin SDK.
Install firebase_admin in the auth-service dependencies.
Initialize the SDK in app/main.py using the credentials from settings.firebase_credentials_path.
In the /internal/verify-token endpoint handler, replace the current logic with firebase_admin.auth.verify_id_token(token).
Use the decoded token's uid to look up the user in the auth-service's database and return the user information.
If the token is invalid or expired, catch the exception and return a 401 Unauthorized error.
2. delivery-service: Implement Real-time Tracking & Notifications
The core endpoints exist, but two critical integrations from the monolith are missing.

Required Fix 1: Sync Location to Supabase
In the POST /location endpoint handler, after updating the delivery partner's location in the service's database, call the SupabaseClient.create_delivery_location() method to sync the latitude and longitude to Supabase. This enables real-time tracking for users.
Required Fix 2: Send Delivery Notifications
In the PUT /status and POST /location endpoint handlers, when the status changes to "out_for_delivery" or similar, use the ResilientHttpClient to call the notification-service and send a notification to the user. This replicates the NotificationService.notify_order_status_change logic from the monolith.
3. product-service: Implement Admin Restock Endpoint
The monolith has a dedicated PUT /inventory/{product_id}/restock endpoint for administrators to add stock.

Required Fix: Implement a dedicated POST /admin/products/{product_id}/restock endpoint.
Authentication: This endpoint must be protected by the verify_admin dependency.
Logic: It should accept a quantity_to_add: int parameter. The service must fetch the current product, add the new quantity to the existing stock_quantity, and save the result. This atomic operation prevents race conditions.
4. notification-service: Implement Core Notification Logic
The service contains only placeholder methods.

Required Fix: Implement the following methods using the monolith's NotificationService as a reference:
_send_fcm_notification: Use httpx to send a POST request to the FCM API.
_send_email_notification: Use httpx to send a POST request to the resend API.
_send_in_app_notification: Persist the notification to the database.
notify_order_status_change: Orchestrate the sending of push, email, and in-app notifications based on the order status.
5. cart-service: Implement Complete Business Logic
The CartService lacks core functionality.

Required Fix: Implement the following methods:
get_cart: Fetch from DB, create if not exists, and sync with Redis.
add_item: Validate product (call product-service), check stock, validate quantity, update totals, and persist.
remove_item: Remove an item and update persistence layers.
clear_cart: Empty the cart after an order is placed.
6. order-service: Implement Service Orchestration
The service only handles local order creation.

Required Fix: After successfully creating an order:
Use the ResilientHttpClient to call the cart-service and clear the user's cart (DELETE /cart/clear).
Use the ResilientHttpClient to call the notification-service and send an "order_created" notification.
7. shared Module: Implement Persistent Audit Logging
The AuditService only logs to files.

Required Fix:
Define an AuditLog SQLAlchemy model in shared/models/audit.py.
Update the AuditService.record_event method to create and commit an AuditLog entry to the database.
8. Create the admin-service
The entire service is missing.

Required Fix: Create a new admin-service that replicates the functionality in the monolith's app/routes/admin.py. It should:
Provide endpoints for user, product, order, and inventory management.
Aggregate data by calling other microservices (Auth, Product, Order) using the ResilientHttpClient.
Be protected by an admin API key.
9. General Principles
Leverage Shared Code: Use the ResilientHttpClient, custom_logging, and error_handler modules consistently.
Configuration: Use the BaseSettings and ServiceConfig classes for all configuration.
Docker: Add the new admin-service to docker-compose.yml with its database, environment variables, and health checks.
Data Models: Ensure all microservice database models (Product, Order, etc.) are identical to their monolith counterparts.
Please generate the complete, updated code for all services to ensure they are fully functional, secure, and equivalent to the monolithic application.



## prompt-2 
The provided microservices codebase has several critical issues that break functional parity with the monolithic application and introduce security and architectural flaws. Please fix the following problems:

Issue 1: The enhanced_order_service.py File is a Severe Anti-Pattern
Problem: The file order-service/app/services/enhanced_order_service.py is a major problem. It contains a complete duplicate of the OrderService logic, which already exists in order-service/app/services/order_service.py. This violates the DRY principle and creates maintenance nightmares.
Critical Flaws:
Code Duplication: The business logic for create_order, get_order, etc., is duplicated.
Hardcoded Dummy Data: The get_order_fallback function contains hardcoded, dummy order data (e.g., "id": "unknown", "total": 0.0). This is unacceptable for a production service and pollutes the business logic layer.
Misplaced Resilience Logic: The GracefulServiceCall context manager, which implements the circuit breaker, is incorrectly placed inside the service. Resilience patterns belong in the client layer (e.g., ResilientHttpClient) or the API Gateway, not in the service being called.
Required Fix:
Delete the file enhanced_order_service.py immediately.
Ensure all order logic resides solely in order_service.py.
Move any fallback logic to the api-gateway, where it belongs.
Issue 2: The admin-service is Calling Non-Existent Endpoints
Problem: The admin-service attempts to aggregate data by calling endpoints that do not exist in the target services, which will cause 404 Not Found errors and break the admin dashboard.
Specific Incorrect Calls:
delivery-service: The admin-service calls /internal/stats, but this endpoint does not exist in the delivery-service code.
product-service: The admin-service calls /admin/products, but this admin-specific endpoint does not exist. The product-service only has standard /products endpoints.
order-service: The admin-service calls /admin/orders, but this endpoint does not exist. The order-service has /orders but not an admin-specific version.
Required Fix:
Implement the Missing Endpoints:
Add a GET /internal/stats endpoint in the delivery-service to return aggregate data (e.g., count of active partners).
Add a GET /admin/products endpoint in the product-service (protected by admin auth) to list all products for admin use.
Add a GET /admin/orders endpoint in the order-service (protected by admin auth) to list all orders for admin use.
OR, Update the admin-service: If admin-specific endpoints are not desired, update the admin-service to call the existing, non-admin endpoints (e.g., GET /products, GET /orders) and aggregate the data itself.
Issue 3: Presence of Dummy Data in Configuration
Problem: The docker-compose.yml file contains a hardcoded, dummy API key for Meilisearch:
environment:
  MEILI_MASTER_KEY: dummy-master-key-123
Risk: This is a security vulnerability. A hardcoded, well-known key in a configuration file can lead to unauthorized access to the search index.
Required Fix:
Replace dummy-master-key-123 with a strong, randomly generated master key.
Store this key in a secure environment variable or a secrets manager, not in the docker-compose.yml file. The file should reference an environment variable (e.g., ${MEILI_MASTER_KEY}).
General Principles for the Fixes
Remove Redundancy: Eliminate all duplicated code and ensure a single source of truth for business logic.
Separation of Concerns: Keep resilience and fallback logic in the API Gateway or client layer, not in core business services.
Security: Never use hardcoded secrets in configuration files.
Consistency: Ensure service-to-service communication contracts (URLs, endpoints) are accurate and functional.
Please generate the corrected code, focusing on deleting the enhanced_order_service.py file, implementing the missing admin endpoints, and securing the Meilisearch configuration.